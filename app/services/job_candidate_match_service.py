"""
人岗匹配服务
处理职位与简历的AI匹配逻辑
"""
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select

from app.models.job import Job
from app.models.resume import Resume
from app.models.ai_match_result import AIMatchResult
from app.services.base_service import BaseService
from app.services.job_service import JobService
from app.services.resume_service import ResumeService
from app.ai.llm_caller import get_llm_caller
import structlog

logger = structlog.get_logger(__name__)


class JobCandidateMatchService(BaseService):
    """人岗匹配服务类"""

    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.job_service = JobService(db)
        self.resume_service = ResumeService(db)
        self.llm_caller = get_llm_caller()

    async def match_job_candidate(
        self,
        job_id: UUID,
        resume_id: UUID,
        tenant_id: UUID,
        user_id: Optional[UUID] = None,
        max_retries: int = 3
    ) -> Optional[AIMatchResult]:
        """
        执行人岗匹配

        Args:
            job_id: 职位ID
            resume_id: 简历ID
            tenant_id: 租户ID
            user_id: 用户ID
            max_retries: 最大重试次数

        Returns:
            匹配结果对象，失败返回None
        """
        # 获取职位和简历信息
        job = await self.job_service.get_by_id(Job, job_id, tenant_id)
        resume = await self.resume_service.get_by_id(Resume, resume_id, tenant_id)

        if not job or not resume:
            logger.error(
                "job_or_resume_not_found",
                job_id=job_id,
                resume_id=resume_id,
                tenant_id=tenant_id
            )
            return None

        # 选择匹配策略
        match_strategy = await self._select_match_strategy(job)
        logger.info(
            "match_strategy_selected",
            job_id=job_id,
            resume_id=resume_id,
            strategy=match_strategy
        )

        # 准备职位和简历描述
        job_description = self._prepare_job_description(job)
        resume_description = await self._prepare_resume_description(resume_id, tenant_id)

        # 执行AI匹配（带重试）
        match_result = None
        for attempt in range(max_retries):
            try:
                match_result = await self._execute_ai_match(
                    match_strategy=match_strategy,
                    job_description=job_description,
                    resume_description=resume_description
                )
                print(match_result)
                break  # 成功则跳出重试循环
            except Exception as e:
                logger.warning(
                    "ai_match_attempt_failed",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    job_id=job_id,
                    resume_id=resume_id,
                    error=str(e)
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)  # 重试前等待1秒
                else:
                    logger.error(
                        "ai_match_failed_after_retries",
                        job_id=job_id,
                        resume_id=resume_id,
                        max_retries=max_retries
                    )
                    return None

        # 保存匹配结果
        ai_match_result = await self._save_match_result(
            job_id=job_id,
            resume_id=resume_id,
            tenant_id=tenant_id,
            user_id=user_id,
            match_result=match_result,
            strategy=match_strategy
        )

        # 更新简历表
        await self._update_resume_match_info(
            resume_id=resume_id,
            tenant_id=tenant_id,
            is_match=ai_match_result.is_match,
            match_conclusion=ai_match_result.reason
        )

        return ai_match_result

    async def _select_match_strategy(self, job: Job) -> str:
        """
        选择匹配策略

        Args:
            job: 职位对象

        Returns:
            匹配策略名称
        """
        # 首先尝试通过category判断
        category = job.category or ""
        category_lower = category.lower()

        # 销售类关键词
        sales_keywords = ["销售", "sale", "商务", "业务", "客户经理", "客户代表"]
        # 技术类关键词
        tech_keywords = ["开发", "工程师", "技术", "程序", "软件", "前端", "后端", "算法", "数据", "dev", "engineer", "developer"]

        # 判断是否为销售类
        is_sales = any(keyword in category_lower for keyword in sales_keywords)
        # 判断是否为技术类
        is_tech = any(keyword in category_lower for keyword in tech_keywords)

        if is_sales:
            return "job_candidate_match.job_candidate_match_for_sales"
        elif is_tech:
            return "job_candidate_match.job_candidate_match_for_strong_skills"
        else:
            # 如果category无法确定，使用大模型判断
            return await self._determine_job_type_with_llm(job)

    async def _determine_job_type_with_llm(self, job: Job) -> str:
        """
        使用大模型判断职位类型

        Args:
            job: 职位对象

        Returns:
            匹配策略名称
        """
        job_info = f"""
        职位名称: {job.title}
        职位类别: {job.category}
        职位描述: {job.description}
        职位要求: {job.requirements}
        """

        template_vars = {"jobInfo": job_info}
        
        try:
            # 使用简单的分类prompt
            result = await self.llm_caller.call_with_prompt(
                prompt=f"""
                请根据以下职位信息，判断这个职位更偏向于"销售类"还是"技术类"？
                只回答"销售类"或"技术类"，不要其他内容。

                职位信息：
                {job_info}
                """,
                parse_json=False
            )
            
            job_type = result.strip()
            
            if "销售" in job_type:
                return "job_candidate_match.job_candidate_match_for_sales"
            else:
                return "job_candidate_match.job_candidate_match_for_strong_skills"
                
        except Exception as e:
            logger.error(
                "failed_to_determine_job_type_with_llm",
                job_id=job.id,
                error=str(e)
            )
            # 默认使用技术类匹配
            return "job_candidate_match.job_candidate_match_for_strong_skills"

    def _prepare_job_description(self, job: Job) -> str:
        """
        准备职位描述

        Args:
            job: 职位对象

        Returns:
            格式化的职位描述字符串
        """
        description = f"""
        职位名称: {job.title}
        职位类型: {job.type or ''}
        
        职位描述:
        {job.description or ''}
        
        职位要求:
        {job.requirements or ''}
        """
        return description.strip()

    async def _prepare_resume_description(self, resume_id: UUID, tenant_id: UUID) -> str:
        """
        准备简历描述

        Args:
            resume_id: 简历ID
            tenant_id: 租户ID

        Returns:
            格式化的简历描述字符串
        """
        # 使用resume_service中的get_resume_full_details方法获取完整简历信息
        resume_details = await self.resume_service.get_resume_full_details(resume_id, tenant_id)
        if not resume_details:
            return ""

        resume = resume_details["resume"]
        work_experiences = resume_details["work_experiences"]
        project_experiences = resume_details["project_experiences"]
        education_histories = resume_details["education_histories"]

        # 构建工作经历描述
        work_desc = ""
        for exp in work_experiences:
            work_desc += f"""
            职位: {exp.position}
            时间: {exp.start_date} - {exp.end_date}
            工作描述: {exp.description or ''}
            """

        # 构建项目经历描述
        project_desc = ""
        for proj in project_experiences:
            project_desc += f"""
            项目名称: {proj.project_name}
            角色: {proj.role or ''}
            时间: {proj.start_date} - {proj.end_date}
            技术栈: {proj.technologies or ''}
            项目描述: {proj.description or ''}
            """

        # 构建教育背景描述
        education_desc = ""
        for edu in education_histories:
            education_desc += f"""
            学校: {edu.school}
            学历: {edu.degree or ''}
            专业: {edu.major or ''}
            时间: {edu.start_date} - {edu.end_date}
            """

        # 组合完整简历描述
        resume_description = f"""
        工作经验年限: {resume.experience_years or ''}
        学历水平: {resume.education_level or ''}
        技能列表: {resume.skills or ''}
        
        工作经历:
        {work_desc}
        
        项目经历:
        {project_desc}
        
        教育背景:
        {education_desc}
        """
        
        return resume_description.strip()

    async def _execute_ai_match(
        self,
        match_strategy: str,
        job_description: str,
        resume_description: str
    ) -> Dict[str, Any]:
        """
        执行AI匹配

        Args:
            match_strategy: 匹配策略
            job_description: 职位描述
            resume_description: 简历描述

        Returns:
            AI匹配结果
        """
        template_vars = {
            "jobDescription": job_description,
            "resumeDesc": resume_description
        }

        # 对于技术类匹配，需要特殊处理返回结果，因为模板输出不是标准JSON
        if "job_candidate_match_for_strong_skills" in match_strategy:
            result = await self.llm_caller.call_with_scene(
                scene_name=match_strategy,
                template_vars=template_vars,
                parse_json=False  # 不解析为JSON，因为模板输出不是标准JSON格式
            )
            
            # 手动解析返回结果
            content = result
            
            # 尝试从内容中提取判断结果和判断依据
            is_match = False
            reason = ""
            
            # 查找"判断结果"字段
            if '"判断结果"' in content and '"是"' in content:
                is_match = True
            
            # 查找"判断依据"字段
            if '"判断依据"' in content:
                # 提取判断依据内容
                start_idx = content.find('"判断依据"') + len('"判断依据"')
                # 查找下一个引号或行尾
                end_idx = content.find('"', start_idx)
                if end_idx == -1:
                    end_idx = len(content)
                
                # 跳过可能的冒号和空格
                while start_idx < end_idx and (content[start_idx] == ':' or content[start_idx] == ' '):
                    start_idx += 1
                
                reason = content[start_idx:end_idx].strip()
            
            return {
                "判断结果": "是" if is_match else "否",
                "判断依据": reason
            }
        else:
            # 销售类匹配，使用标准JSON解析
            return await self.llm_caller.call_with_scene(
                scene_name=match_strategy,
                template_vars=template_vars,
                parse_json=True
            )

    async def _save_match_result(
        self,
        job_id: UUID,
        resume_id: UUID,
        tenant_id: UUID,
        user_id: Optional[UUID],
        match_result: Dict[str, Any],
        strategy: str
    ) -> AIMatchResult:
        """
        保存匹配结果

        Args:
            job_id: 职位ID
            resume_id: 简历ID
            tenant_id: 租户ID
            user_id: 用户ID
            match_result: AI匹配结果
            strategy: 匹配策略

        Returns:
            保存的匹配结果对象
        """
        # 在保存新匹配结果前，先将当前有效的匹配结果置为失效状态
        await self._invalidate_previous_match_results(job_id, resume_id, tenant_id)
        
        # 根据不同策略解析结果
        if "job_candidate_match_for_sales" in strategy:
            # 销售类匹配结果格式: {"分析过程": "", "判断结果": "[是/否]"}
            is_match = match_result.get("判断结果", "否") == "是"
            reason = match_result.get("分析过程", "")
            match_score = 100 if is_match else 0
        else:
            # 技术类匹配结果格式: {"判断结果": "是/否", "判断依据": "xxx"}
            is_match = match_result.get("判断结果", "否") == "是"
            reason = match_result.get("判断依据", "")
            match_score = 100 if is_match else 0

        # 创建匹配结果记录
        match_data = {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "resume_id": resume_id,
            "job_id": job_id,
            "is_match": is_match,
            "match_score": match_score,
            "reason": reason,
            "strengths": "",  # 当前prompt未返回此字段
            "weaknesses": "",  # 当前prompt未返回此字段
            "recommendation": reason,  # 当前prompt未返回此字段
            "status": "valid",  # 新创建的匹配结果默认为有效状态
            "analyzed_at": datetime.utcnow()
        }
        print(match_data)

        return await self.create(AIMatchResult, match_data)
    
    async def _invalidate_previous_match_results(
        self,
        job_id: UUID,
        resume_id: UUID,
        tenant_id: UUID
    ) -> None:
        """
        将当前有效的匹配结果置为失效状态

        Args:
            job_id: 职位ID
            resume_id: 简历ID
            tenant_id: 租户ID
        """
        from sqlalchemy import update
        
        # 使用批量更新操作，将所有有效的匹配结果置为失效状态
        stmt = update(AIMatchResult).where(
            and_(
                AIMatchResult.job_id == job_id,
                AIMatchResult.resume_id == resume_id,
                AIMatchResult.tenant_id == tenant_id,
                AIMatchResult.status == "valid"
            )
        ).values(status="invalid")
        
        await self.db.execute(stmt)
        # 不需要显式提交，因为 BaseService 的 create 方法会处理事务

    async def _update_resume_match_info(
        self,
        resume_id: UUID,
        tenant_id: UUID,
        is_match: bool,
        match_conclusion: str
    ) -> None:
        """
        更新简历的匹配信息

        Args:
            resume_id: 简历ID
            tenant_id: 租户ID
            is_match: 是否匹配
            match_conclusion: 匹配结论
        """
        await self.resume_service.update(
            Resume,
            resume_id,
            {
                "is_match": is_match,
                "match_conclusion": match_conclusion
            },
            tenant_id
        )
