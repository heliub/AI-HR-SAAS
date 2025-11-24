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

        # 解析匹配结果
        parsed_match_result = self._parse_match_result(match_result, match_strategy)

        # 更新简历表
        # 只有当 is_match 不为 None 时才更新简历匹配信息
        is_match = parsed_match_result["is_match"]
        if is_match is not None:
             # 保存匹配结果
            ai_match_result = await self._save_match_result(
                job_id=job_id,
                resume_id=resume_id,
                tenant_id=tenant_id,
                user_id=user_id,
                match_result=parsed_match_result
            )
            await self._update_resume_match_info(
                resume_id=resume_id,
                tenant_id=tenant_id,
                is_match=is_match,
                match_conclusion=parsed_match_result["reason"]
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

        return "job_candidate_match.job_candidate_match_common"
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
            # 如果category无法确定，使用通用匹配策略
            return "job_candidate_match.job_candidate_match_common"

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
    ) -> str:
        """
        执行AI匹配

        Args:
            match_strategy: 匹配策略
            job_description: 职位描述
            resume_description: 简历描述

        Returns:
            AI匹配结果（原始返回结果，字符串）
        """
        template_vars = {
            "jobDescription": job_description,
            "resumeDesc": resume_description
        }

        # 统一不进行JSON解析，直接返回原始结果
        result = await self.llm_caller.call_with_scene(
            scene_name=match_strategy,
            template_vars=template_vars
        )
        
        # 直接返回原始结果，不做任何处理
        return result

    def _parse_match_result(self, match_result, match_strategy: str) -> Dict[str, Any]:
        """
        解析匹配结果

        Args:
            match_result: AI匹配结果（可能是字符串或字典）
            match_strategy: 匹配策略

        Returns:
            解析后的匹配结果字典，包含is_match和reason字段
        """
        # 根据不同策略调用相应的解析方法
        if "job_candidate_match_for_strong_skills" in match_strategy:
            return self._parse_tech_match_result(match_result)
        elif "job_candidate_match_for_sales" in match_strategy:
            return self._parse_sales_match_result(match_result)
        elif "job_candidate_match_common" in match_strategy:
            return self._parse_common_match_result(match_result)
        else:
            # 未知策略，返回空结果
            return {
                "is_match": None,
                "reason": None,
                "error": "未知匹配策略"
            }
    
    def _parse_tech_match_result(self, match_result) -> Dict[str, Any]:
        """
        解析技术类匹配结果
        
        Args:
            match_result: AI匹配结果（可能是字符串或字典）
            
        Returns:
            包含以下字段的字典：
            - is_match: 是否匹配（True/False/None）
            - reason: 判断依据（字符串）
            - error: 解析错误信息（如果有）或 None
        """
        try:
            # 处理字典类型的输入
            if isinstance(match_result, dict):
                # 从字典中提取判断结果和判断依据
                is_match = None
                reason = None
                
                # 尝试获取判断结果
                if "判断结果" in match_result:
                    result_value = match_result["判断结果"]
                    if isinstance(result_value, str):
                        is_match = result_value == "是"
                    elif isinstance(result_value, bool):
                        is_match = result_value
                
                # 尝试获取判断依据
                if "判断依据" in match_result:
                    reason = match_result["判断依据"]
                    if not isinstance(reason, str):
                        reason = str(reason)
                
                return {
                    "is_match": is_match,
                    "reason": reason,
                    "error": None
                }
            
            # 处理字符串类型的输入
            if not match_result or not match_result.strip():
                return {
                    "is_match": None,
                    "reason": None,
                    "error": "模型返回结果为空"
                }
            
            # 获取原始内容
            content = match_result
            
            # 技术类匹配结果解析
            # 输出格式: "判断结果":"是/否","判断依据":"xxx"
            # 使用正则表达式提取判断结果和判断依据
            import re
            
            # 提取判断结果
            result_match = re.search(r'"判断结果"\s*:\s*"([^"]*)"', content)
            if result_match:
                result_value = result_match.group(1).strip()
                is_match = result_value == "是"
            else:
                # 如果没有找到标准格式，返回None
                return {
                    "is_match": None,
                    "reason": None,
                    "error": "未找到判断结果字段"
                }
            
            # 提取判断依据
            reason_match = re.search(r'"判断依据"\s*:\s*"([^"]*)"', content)
            if reason_match:
                reason = reason_match.group(1).strip()
            else:
                # 如果没有找到判断依据，仍然返回匹配结果，但reason为None
                reason = None
            
            return {
                "is_match": is_match,
                "reason": reason,
                "error": None
            }
        except Exception as e:
            return {
                "is_match": None,
                "reason": None,
                "error": f"解析技术类匹配结果失败: {str(e)}"
            }
    
    def _parse_sales_match_result(self, match_result) -> Dict[str, Any]:
        """
        解析销售类匹配结果
        
        Args:
            match_result: AI匹配结果（可能是字符串或字典）
            
        Returns:
            包含以下字段的字典：
            - is_match: 是否匹配（True/False/None）
            - reason: 判断依据（字符串）
            - error: 解析错误信息（如果有）或 None
        """
        try:
            # 处理字典类型的输入
            if isinstance(match_result, dict):
                # 从字典中提取判断结果和分析过程
                is_match = None
                reason = None
                
                # 尝试获取判断结果
                if "判断结果" in match_result:
                    result_value = match_result["判断结果"]
                    if isinstance(result_value, str):
                        is_match = "是" in result_value
                    elif isinstance(result_value, bool):
                        is_match = result_value
                
                # 尝试获取分析过程
                if "分析过程" in match_result:
                    reason = match_result["分析过程"]
                    if not isinstance(reason, str):
                        reason = str(reason)
                
                return {
                    "is_match": is_match,
                    "reason": reason,
                    "error": None
                }
            
            # 处理字符串类型的输入
            if not match_result or not match_result.strip():
                return {
                    "is_match": None,
                    "reason": None,
                    "error": "模型返回结果为空"
                }
            
            # 获取原始内容
            content = match_result
            
            # 销售类匹配结果解析
            # 输出格式: {"分析过程": "", "判断结果": "[是/否]"}
            # 尝试解析JSON格式
            try:
                # 移除markdown代码块标记
                json_content = content
                if "```json" in content:
                    json_content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_content = content.split("```")[1].split("```")[0].strip()
                
                # 尝试解析JSON
                import json
                parsed_result = json.loads(json_content)
                
                # 获取判断结果和分析过程
                result = parsed_result.get("判断结果", None)
                if result is not None:
                    is_match = "是" in result
                else:
                    return {
                        "is_match": None,
                        "reason": None,
                        "error": "未找到判断结果字段"
                    }
                    
                reason = parsed_result.get("分析过程", None)
                
                return {
                    "is_match": is_match,
                    "reason": reason,
                    "error": None
                }
            except (json.JSONDecodeError, Exception):
                # 如果解析失败，尝试从原始内容中查找判断结果
                import re
                result_match = re.search(r'"判断结果"\s*:\s*"([^"]*)"', content)
                if result_match:
                    result_value = result_match.group(1).strip()
                    is_match = result_value == "是"
                else:
                    return {
                        "is_match": None,
                        "reason": None,
                        "error": "未找到判断结果字段"
                    }
                
                # 尝试查找分析过程
                process_match = re.search(r'"分析过程"\s*:\s*"([^"]*)"', content)
                if process_match:
                    reason = process_match.group(1).strip()
                else:
                    reason = None
                
                return {
                    "is_match": is_match,
                    "reason": reason,
                    "error": None
                }
        except Exception as e:
            return {
                "is_match": None,
                "reason": None,
                "error": f"解析销售类匹配结果失败: {str(e)}"
            }
    
    def _parse_common_match_result(self, match_result) -> Dict[str, Any]:
        """
        解析通用匹配结果
        
        Args:
            match_result: AI匹配结果（可能是字符串或字典）
            
        Returns:
            包含以下字段的字典：
            - is_match: 是否匹配（True/False/None）
            - reason: 判断依据（字符串）
            - error: 解析错误信息（如果有）或 None
        """
        try:
            # 处理字典类型的输入
            if isinstance(match_result, dict):
                # 从字典中提取过滤结果和总体说明
                is_match = None
                reason = None
                
                # 尝试获取过滤结果
                if "过滤结果" in match_result:
                    result_value = match_result["过滤结果"]
                    if isinstance(result_value, str):
                        is_match = result_value == "匹配"
                    elif isinstance(result_value, bool):
                        is_match = result_value
                
                # 尝试获取总体说明
                if "总体说明" in match_result:
                    reason = match_result["总体说明"]
                    if not isinstance(reason, str):
                        reason = str(reason)
                
                return {
                    "is_match": is_match,
                    "reason": reason,
                    "error": None
                }
            
            # 处理字符串类型的输入
            if not match_result or not match_result.strip():
                return {
                    "is_match": None,
                    "reason": None,
                    "error": "模型返回结果为空"
                }
            
            # 获取原始内容
            content = match_result
            
            # 通用匹配结果解析
            # 输出格式: JSON格式，包含过滤结果和总体说明等字段
            # 尝试解析JSON格式
            try:
                # 移除markdown代码块标记
                json_content = content
                if "```json" in content:
                    json_content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_content = content.split("```")[1].split("```")[0].strip()
                
                # 尝试解析JSON
                import json
                parsed_result = json.loads(json_content)
                
                # 获取过滤结果和总体说明
                filter_result = parsed_result.get("过滤结果", None)
                if filter_result is not None:
                    is_match = filter_result == "匹配"
                else:
                    return {
                        "is_match": None,
                        "reason": None,
                        "error": "未找到过滤结果字段"
                    }
                    
                reason = parsed_result.get("总体说明", None)
                
                return {
                    "is_match": is_match,
                    "reason": reason,
                    "error": None
                }
            except (json.JSONDecodeError, Exception):
                # 如果解析失败，尝试从原始内容中查找过滤结果
                import re
                result_match = re.search(r'"过滤结果"\s*:\s*"([^"]*)"', content)
                if result_match:
                    result_value = result_match.group(1).strip()
                    is_match = result_value == "匹配"
                else:
                    return {
                        "is_match": None,
                        "reason": None,
                        "error": "未找到过滤结果字段"
                    }
                
                # 尝试查找总体说明
                reason_match = re.search(r'"总体说明"\s*:\s*"([^"]*)"', content)
                if reason_match:
                    reason = reason_match.group(1).strip()
                else:
                    reason = None
                
                return {
                    "is_match": is_match,
                    "reason": reason,
                    "error": None
                }
        except Exception as e:
            return {
                "is_match": None,
                "reason": None,
                "error": f"解析通用匹配结果失败: {str(e)}"
            }

    async def _save_match_result(
        self,
        job_id: UUID,
        resume_id: UUID,
        tenant_id: UUID,
        user_id: Optional[UUID],
        match_result: Dict[str, Any]
    ) -> AIMatchResult:
        """
        保存匹配结果

        Args:
            job_id: 职位ID
            resume_id: 简历ID
            tenant_id: 租户ID
            user_id: 用户ID
            match_result: AI匹配结果

        Returns:
            保存的匹配结果对象
        """
        # 在保存新匹配结果前，先将当前有效的匹配结果置为失效状态
        await self._invalidate_previous_match_results(job_id, resume_id, tenant_id)
        
        # 根据解析结果设置匹配信息
        is_match = match_result.get("is_match")
        reason = match_result.get("reason", "")
        
        # 如果 is_match 为 None，说明无法确定匹配结果，不设置分数
        if is_match is None:
            match_score = 0
        else:
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
