"""
Job endpoints
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.schemas.job import (
    JobCreate, JobUpdate, JobStatusUpdate, JobResponse,
    JobAIGenerateRequest, JobAIGenerateResponse
)
from app.schemas.base import APIResponse, PaginatedResponse
from app.services.job_service import JobService
from app.models.user import User
from app.models.job import Job

router = APIRouter()


@router.get("", response_model=APIResponse)
async def get_jobs(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    department: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取职位列表"""
    job_service = JobService(db)

    skip = (page - 1) * pageSize
    jobs = await job_service.search_jobs(
        tenant_id=current_user.tenant_id,
        keyword=search,
        status=status,
        department=department,
        skip=skip,
        limit=pageSize
    )

    # 获取总数
    total = await job_service.count(Job, current_user.tenant_id, {
        "status": status,
        "department": department
    } if status or department else None)

    job_responses = [JobResponse.model_validate(job) for job in jobs]

    paginated_data = PaginatedResponse(
        total=total,
        page=page,
        pageSize=pageSize,
        list=job_responses
    )

    return APIResponse(
        code=200,
        message="成功",
        data=paginated_data.model_dump()
    )


@router.get("/{job_id}", response_model=APIResponse)
async def get_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取职位详情"""
    job_service = JobService(db)
    
    # 使用新的服务方法获取职位详情
    job_data = await job_service.get_job_with_details(job_id, current_user.tenant_id)

    if not job_data:
        return APIResponse(
            code=404,
            message="职位不存在"
        )

    job_response = JobResponse.model_validate(job_data["job"])

    return APIResponse(
        code=200,
        message="成功",
        data=job_response.model_dump()
    )


@router.post("", response_model=APIResponse)
async def create_job(
    job_data: JobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建职位"""
    job_service = JobService()
    
    job = await job_service.create_job(
        db=db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        created_by=current_user.id,
        **job_data.model_dump(exclude_unset=True)
    )
    
    job_response = JobResponse.model_validate(job)
    
    return APIResponse(
        code=200,
        message="职位创建成功",
        data=job_response.model_dump()
    )


@router.put("/{job_id}", response_model=APIResponse)
async def update_job(
    job_id: UUID,
    job_data: JobUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新职位"""
    job_service = JobService()
    
    # 检查职位是否存在
    job = await job_service.get_by_id(Job, job_id, current_user.tenant_id)
    if not job or job.tenant_id != current_user.tenant_id or job.user_id != current_user.id:
        return APIResponse(
            code=404,
            message="职位不存在"
        )
    
    job = await job_service.update_job(
        db=db,
        job_id=job_id,
        **job_data.model_dump(exclude_unset=True)
    )
    
    job_response = JobResponse.model_validate(job)
    
    return APIResponse(
        code=200,
        message="职位更新成功",
        data=job_response.model_dump()
    )


@router.delete("/{job_id}", response_model=APIResponse)
async def delete_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除职位"""
    job_service = JobService()
    
    # 检查职位是否存在
    job = await job_service.get_by_id(Job, job_id, current_user.tenant_id)
    if not job or job.tenant_id != current_user.tenant_id or job.user_id != current_user.id:
        return APIResponse(
            code=404,
            message="职位不存在"
        )
    
    await job_service.delete(db, job_id)
    
    return APIResponse(
        code=200,
        message="职位删除成功"
    )


@router.patch("/{job_id}/status", response_model=APIResponse)
async def update_job_status(
    job_id: UUID,
    status_data: JobStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新职位状态"""
    job_service = JobService()
    
    # 检查职位是否存在
    job = await job_service.get_by_id(Job, job_id, current_user.tenant_id)
    if not job or job.tenant_id != current_user.tenant_id or job.user_id != current_user.id:
        return APIResponse(
            code=404,
            message="职位不存在"
        )
    
    job = await job_service.update_job(
        db=db,
        job_id=job_id,
        status=status_data.status
    )
    
    return APIResponse(
        code=200,
        message="状态更新成功"
    )


@router.post("/{job_id}/duplicate", response_model=APIResponse)
async def duplicate_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """复制职位"""
    job_service = JobService()
    
    # 检查职位是否存在
    job = await job_service.get_by_id(Job, job_id, current_user.tenant_id)
    if not job or job.tenant_id != current_user.tenant_id or job.user_id != current_user.id:
        return APIResponse(
            code=404,
            message="职位不存在"
        )
    
    new_job = await job_service.duplicate_job(
        db=db,
        job_id=job_id,
        user_id=current_user.id,
        created_by=current_user.id
    )
    
    job_response = JobResponse.model_validate(new_job)
    
    return APIResponse(
        code=200,
        message="职位复制成功",
        data=job_response.model_dump()
    )


@router.post("/ai-generate", response_model=APIResponse)
async def ai_generate_job(
    request_data: JobAIGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI生成职位描述"""
    try:
        # 智能生成职位信息
        generated_data = _generate_job_description(request_data.title, request_data.description)

        response_data = JobAIGenerateResponse(**generated_data)

        return APIResponse(
            code=200,
            message="生成成功",
            data=response_data.model_dump(by_alias=True)
        )
    except Exception as e:
        return APIResponse(
            code=500,
            message=f"生成失败: {str(e)}"
        )


def _generate_job_description(job_title: str, brief_desc: str) -> dict:
    """
    根据职位标题和简要描述生成详细职位信息
    """
    # 基于职位标题的智能生成逻辑
    tech_jobs = ["前端", "后端", "全栈", "移动端", "算法", "数据", "测试", "运维", "架构师"]
    product_jobs = ["产品", "设计", "运营", "市场", "销售"]
    hr_jobs = ["人力资源", "HR", "招聘", "培训", "薪酬"]

    job_title_lower = job_title.lower()

    if any(tech in job_title_lower for tech in tech_jobs):
        return _generate_tech_job_desc(job_title, brief_desc)
    elif any(job in job_title_lower for job in product_jobs):
        return _generate_product_job_desc(job_title, brief_desc)
    elif any(hr_job in job_title_lower for hr_job in hr_jobs):
        return _generate_hr_job_desc(job_title, brief_desc)
    else:
        return _generate_general_job_desc(job_title, brief_desc)


def _generate_tech_job_desc(title: str, brief_desc: str) -> dict:
    """生成技术类职位描述"""
    return {
        "department": "技术部",
        "location": "北京/上海/深圳",
        "min_salary": 20000,
        "max_salary": 45000,
        "description": f"""职位描述：
1. 负责公司{title}相关的开发工作，参与产品需求分析和技术方案设计
2. 编写高质量、可维护的代码，完成核心功能模块开发
3. 参与代码审查，确保代码质量和团队技术水平提升
4. 解决开发过程中的技术难题，优化系统性能
5. 与产品、设计、测试团队密切配合，确保项目按时高质量交付

任职要求：
• 3年以上相关开发经验，有大型项目经验者优先
• 熟练掌握相关技术栈和开发工具
• 具备良好的编程习惯和代码规范意识
• 有较强的学习能力和技术热情""",
        "recruitment_invitation": f"我们正在寻找优秀的{title}加入我们的技术团队！你将有机会参与创新项目，与技术大牛一起成长，享受有竞争力的薪酬福利和良好的职业发展空间。",
        "education": "本科及以上",
        "min_age": 22,
        "max_age": 45
    }


def _generate_product_job_desc(title: str, brief_desc: str) -> dict:
    """生成产品类职位描述"""
    return {
        "department": "产品部",
        "location": "北京/上海",
        "min_salary": 15000,
        "max_salary": 35000,
        "description": f"""职位描述：
1. 负责公司{title}相关工作，参与产品规划和需求调研
2. 进行市场分析和竞品研究，为产品决策提供数据支持
3. 与技术、设计团队协作，推动产品功能实现和优化
4. 跟踪产品数据表现，持续改进产品用户体验
5. 参与产品推广和用户反馈收集，制定产品迭代计划

任职要求：
• 2年以上相关工作经验，有成功产品案例者优先
• 具备良好的市场洞察力和用户需求分析能力
• 优秀的沟通协调能力和团队合作精神
• 熟练使用产品设计和管理工具""",
        "recruitment_invitation": f"如果你对产品有热情，对用户体验有执着，加入我们的产品团队！你将有机会参与产品全生命周期管理，创造用户喜爱的产品。",
        "education": "本科及以上",
        "min_age": 23,
        "max_age": 40
    }


def _generate_hr_job_desc(title: str, brief_desc: str) -> dict:
    """生成HR类职位描述"""
    return {
        "department": "人力资源部",
        "location": "北京",
        "min_salary": 12000,
        "max_salary": 25000,
        "description": f"""职位描述：
1. 负责{title}相关工作，协助制定和完善人力资源管理制度
2. 参与招聘流程优化和人才选拔，确保人才质量
3. 协助员工培训发展计划的制定和实施
4. 参与薪酬福利管理和绩效考核工作
5. 处理员工关系问题，营造良好的工作氛围

任职要求：
• 2年以上HR相关工作经验，熟悉人力资源管理流程
• 具备良好的沟通能力和亲和力
• 熟悉劳动法律法规，具备风险防范意识
• 工作细致认真，有较强的责任心和执行力""",
        "recruitment_invitation": f"我们期待热爱HR工作、有服务意识的你加入！在这里，你将有机会参与人力资源体系建设，助力公司和员工共同成长。",
        "education": "本科及以上",
        "min_age": 24,
        "max_age": 40
    }


def _generate_general_job_desc(title: str, brief_desc: str) -> dict:
    """生成通用职位描述"""
    return {
        "department": "综合管理部",
        "location": "北京",
        "min_salary": 10000,
        "max_salary": 20000,
        "description": f"""职位描述：
1. 负责{title}相关工作，协助部门完成各项业务指标
2. 根据工作要求和标准，高效完成分配的任务
3. 与团队成员密切配合，确保工作质量和进度
4. 及时反馈工作进展和遇到的问题
5. 不断学习提升，为团队发展贡献力量

任职要求：
• 1年以上相关工作经验
• 具备良好的职业素养和工作态度
• 有较强的学习能力和适应能力
• 注重团队合作，积极主动""",
        "recruitment_invitation": f"我们正在寻找合适的{title}加入我们的团队！如果你渴望在专业领域发展，愿意接受挑战，这里将是你施展才华的舞台。",
        "education": "大专及以上",
        "min_age": 20,
        "max_age": 45
    }
