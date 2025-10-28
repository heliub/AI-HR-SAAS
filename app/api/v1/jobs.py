"""
Job endpoints
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, get_current_user
from app.schemas.job import (
    JobCreate, JobUpdate, JobStatusUpdate, JobResponse,
    JobAIGenerateRequest, JobAIGenerateResponse
)
from app.schemas.base import APIResponse, PaginatedResponse
from app.services.job_service import JobService
from app.models.user import User
from app.models.job import Job
from app.models.job_channel import JobChannel

router = APIRouter()


@router.get("", response_model=APIResponse)
async def get_jobs(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    company: Optional[str] = None,
    category: Optional[str] = None,
    workplaceType: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取职位列表 - 优化版本，使用JOIN查询解决N+1问题"""
    job_service = JobService(db)

    skip = (page - 1) * pageSize
    # 判断是否为管理员
    is_admin = current_user.role == "admin"

    # 使用优化的查询方法一次性获取职位和渠道信息
    result = await job_service.search_jobs_with_channels(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        keyword=search,
        status=status,
        company=company,
        category=category,
        workplace_type=workplaceType,
        skip=skip,
        limit=pageSize,
        is_admin=is_admin
    )

    jobs = result["jobs"]
    job_channels_map = result["job_channels"]

    # 获取总数
    total = await job_service.count_jobs(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        filters={
            "status": status,
            "company": company,
            "category": category,
            "workplace_type": workplaceType
        } if status or company or category or workplaceType else None,
        is_admin=is_admin
    )

    # 构建响应数据，使用预查询的渠道信息
    job_responses_with_channels = []
    for job in jobs:
        # 从预查询的映射中获取渠道信息
        channel_ids = job_channels_map.get(job.id, [])

        # 更新响应数据，包含渠道信息
        job_response_data = job.__dict__.copy()
        job_response_data["channels"] = channel_ids
        job_response = JobResponse.model_validate(job_response_data)
        job_responses_with_channels.append(job_response)

    paginated_data = PaginatedResponse(
        total=total,
        page=page,
        pageSize=pageSize,
        list=job_responses_with_channels
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

    # 检查职位是否存在
    job = await job_service.get_by_id(Job, job_id, current_user.tenant_id)
    if not job or job.tenant_id != current_user.tenant_id:
        return APIResponse(
            code=404,
            message="职位不存在"
        )

    # 获取关联的渠道
    channel_query = select(JobChannel).where(
        JobChannel.tenant_id == current_user.tenant_id,
        JobChannel.job_id == job_id
    )
    channel_result = await db.execute(channel_query)
    job_channels = channel_result.scalars().all()
    channel_ids = [channel.channel_id for channel in job_channels]

    # 更新响应数据，包含渠道信息
    job_response_data = job.__dict__.copy()
    job_response_data["channels"] = channel_ids
    job_response = JobResponse.model_validate(job_response_data)

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
    job_service = JobService(db)

    # 分离渠道数据和其他字段
    channel_ids = job_data.channels
    create_data = job_data.model_dump(exclude_unset=True, exclude={"channels"}, by_alias=True)

    # 设置创建者信息
    create_data.update({
        "created_by": current_user.id,
        "tenant_id": current_user.tenant_id,
        "user_id": current_user.id
    })

    # 创建职位
    job = await job_service.create(Job, create_data)

    # 如果提供了渠道ID，创建职位-渠道关联
    if channel_ids:
        for channel_id in channel_ids:
            channel_association = {
                "tenant_id": current_user.tenant_id,
                "job_id": job.id,
                "channel_id": channel_id
            }
            await job_service.create(JobChannel, channel_association)

        # 更新响应数据，包含渠道信息
        job_response_data = job.__dict__.copy()
        job_response_data["channels"] = channel_ids
        job_response = JobResponse.model_validate(job_response_data)
    else:
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
    job_service = JobService(db)

    # 检查职位是否存在
    job = await job_service.get_by_id(Job, job_id, current_user.tenant_id)
    if not job or job.tenant_id != current_user.tenant_id:
        return APIResponse(
            code=404,
            message="职位不存在"
        )

    # 检查权限：只有职位创建者或管理员可以修改
    is_admin = current_user.role == "admin"
    if not is_admin and job.user_id != current_user.id:
        return APIResponse(
            code=403,
            message="权限不足，只能修改自己创建的职位"
        )

    # 分离渠道数据和其他字段
    channel_ids = job_data.channels
    update_data = job_data.model_dump(exclude_unset=True, exclude={"salary", "channels"}, by_alias=True)

    # 更新职位，更新时间会在服务层自动处理
    job = await job_service.update(
        model=Job,
        record_id=job_id,
        data=update_data,
        tenant_id=current_user.tenant_id
    )

    # 如果提供了渠道ID，更新职位-渠道关联
    if channel_ids is not None:
        # 先删除现有的关联
        existing_channel_query = select(JobChannel).where(
            JobChannel.tenant_id == current_user.tenant_id,
            JobChannel.job_id == job_id
        )
        existing_channel_result = await db.execute(existing_channel_query)
        existing_channels = existing_channel_result.scalars().all()

        for existing_channel in existing_channels:
            await db.delete(existing_channel)

        if existing_channels:
            await db.commit()

        # 创建新的关联
        for channel_id in channel_ids:
            channel_association = {
                "tenant_id": current_user.tenant_id,
                "job_id": job_id,
                "channel_id": channel_id
            }
            await job_service.create(JobChannel, channel_association)

        # 更新响应数据，包含渠道信息
        job_response_data = job.__dict__.copy()
        job_response_data["channels"] = channel_ids
        job_response = JobResponse.model_validate(job_response_data)
    else:
        # 如果没有提供渠道ID，查询现有渠道
        existing_channel_query = select(JobChannel).where(
            JobChannel.tenant_id == current_user.tenant_id,
            JobChannel.job_id == job_id
        )
        existing_channel_result = await db.execute(existing_channel_query)
        existing_channels = existing_channel_result.scalars().all()
        existing_channel_ids = [channel.channel_id for channel in existing_channels]

        job_response_data = job.__dict__.copy()
        job_response_data["channels"] = existing_channel_ids
        job_response = JobResponse.model_validate(job_response_data)

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
    job_service = JobService(db)

    # 检查职位是否存在
    job = await job_service.get_by_id(Job, job_id, current_user.tenant_id)
    if not job or job.tenant_id != current_user.tenant_id:
        return APIResponse(
            code=404,
            message="职位不存在"
        )

    # 检查权限：只有职位创建者或管理员可以删除
    is_admin = current_user.role == "admin"
    if not is_admin and job.user_id != current_user.id:
        return APIResponse(
            code=403,
            message="权限不足，只能删除自己创建的职位"
        )
    
    # 更新职位状态为删除（软删除）
    await job_service.update_job_status(
        job_id=job_id,
        tenant_id=current_user.tenant_id,
        status="deleted"
    )

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
    job_service = JobService(db)
    
    # 检查职位是否存在
    job = await job_service.get_by_id(Job, job_id, current_user.tenant_id)
    if not job or job.tenant_id != current_user.tenant_id or job.user_id != current_user.id:
        return APIResponse(
            code=404,
            message="职位不存在"
        )
    
    job = await job_service.update_job_status(
        job_id=job_id,
        tenant_id=current_user.tenant_id,
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
    job_service = JobService(db)
    
    # 检查职位是否存在
    job = await job_service.get_by_id(Job, job_id, current_user.tenant_id)
    if not job or job.tenant_id != current_user.tenant_id or job.user_id != current_user.id:
        return APIResponse(
            code=404,
            message="职位不存在"
        )
    
    new_job = await job_service.duplicate_job(
        job_id=job_id,
        tenant_id=current_user.tenant_id,
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
):
    """AI智能生成职位描述，根据输入参数生成完整的职位信息"""
    try:
        # 智能生成职位信息，使用更多输入参数
        generated_data = _generate_job_description(
            job_title=request_data.title,
            job_type=request_data.type,
            workplace_type=request_data.workplaceType,
            pay_currency=request_data.payCurrency,
            location=request_data.location
        )

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


def _generate_job_description(job_title: str, job_type: str, workplace_type: Optional[str] = None, pay_currency: Optional[str] = None, location: Optional[str] = None) -> dict:
    """
    根据职位标题、类型、工作场所、薪资货币、地点等参数生成详细职位信息
    """
    # 基于职位标题的智能生成逻辑
    tech_jobs = ["前端", "后端", "全栈", "移动端", "算法", "数据", "测试", "运维", "架构师"]
    product_jobs = ["产品", "设计", "运营", "市场", "销售"]
    hr_jobs = ["人力资源", "HR", "招聘", "培训", "薪酬"]

    job_title_lower = job_title.lower()

    # 基于职位类型调整生成策略，job_type参数用于未来扩展
    if job_type == "intern" or job_type == "part-time":
        # 实习生和兼职的生成逻辑可以在这里扩展
        pass
    if any(tech in job_title_lower for tech in tech_jobs):
        return _generate_tech_job_desc(job_title, workplace_type, pay_currency, location)
    elif any(job in job_title_lower for job in product_jobs):
        return _generate_product_job_desc(job_title, workplace_type, pay_currency, location)
    elif any(hr_job in job_title_lower for hr_job in hr_jobs):
        return _generate_hr_job_desc(job_title, workplace_type, pay_currency, location)
    else:
        return _generate_general_job_desc(job_title, workplace_type, pay_currency, location)


def _generate_tech_job_desc(title: str, workplace_type: Optional[str] = None, pay_currency: Optional[str] = None, location: Optional[str] = None) -> dict:
    """生成技术类职位描述"""
    return {
        "company": None,
        "location": location or "北京/上海/深圳",
        "workplace_type": workplace_type or "Hybrid",
        "min_salary": 20000,
        "max_salary": 45000,
        "pay_type": "Monthly",
        "pay_currency": pay_currency or "CNY",
        "pay_shown_on_ad": True,
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
        "requirements": f"3年以上相关开发经验，有大型项目经验者优先；熟练掌握相关技术栈和开发工具；具备良好的编程习惯和代码规范意识；有较强的学习能力和技术热情",
        "category": "Software Development",
        "recruitment_invitation": f"我们正在寻找优秀的{title}加入我们的技术团队！你将有机会参与创新项目，与技术大牛一起成长，享受有竞争力的薪酬福利和良好的职业发展空间。",
        "education": "本科及以上"
    }


def _generate_product_job_desc(title: str, workplace_type: Optional[str] = None, pay_currency: Optional[str] = None, location: Optional[str] = None) -> dict:
    """生成产品类职位描述"""
    return {
        "company": None,
        "location": location or "北京/上海",
        "workplace_type": workplace_type or "Hybrid",
        "min_salary": 15000,
        "max_salary": 35000,
        "pay_type": "Monthly",
        "pay_currency": pay_currency or "CNY",
        "pay_shown_on_ad": True,
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
        "requirements": f"2年以上相关工作经验，有成功产品案例者优先；具备良好的市场洞察力和用户需求分析能力；优秀的沟通协调能力和团队合作精神；熟练使用产品设计和管理工具",
        "category": "Product Management",
        "recruitment_invitation": f"如果你对产品有热情，对用户体验有执着，加入我们的产品团队！你将有机会参与产品全生命周期管理，创造用户喜爱的产品。",
        "education": "本科及以上"
    }


def _generate_hr_job_desc(title: str, workplace_type: Optional[str] = None, pay_currency: Optional[str] = None, location: Optional[str] = None) -> dict:
    """生成HR类职位描述"""
    return {
        "company": None,
        "location": location or "北京",
        "workplace_type": workplace_type or "On-site",
        "min_salary": 12000,
        "max_salary": 25000,
        "pay_type": "Monthly",
        "pay_currency": pay_currency or "CNY",
        "pay_shown_on_ad": True,
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
        "requirements": f"2年以上HR相关工作经验，熟悉人力资源管理流程；具备良好的沟通能力和亲和力；熟悉劳动法律法规，具备风险防范意识；工作细致认真，有较强的责任心和执行力",
        "category": "Human Resources",
        "recruitment_invitation": f"我们期待热爱HR工作、有服务意识的你加入！在这里，你将有机会参与人力资源体系建设，助力公司和员工共同成长。",
        "education": "本科及以上"
    }


def _generate_general_job_desc(title: str, workplace_type: Optional[str] = None, pay_currency: Optional[str] = None, location: Optional[str] = None) -> dict:
    """生成通用职位描述"""
    return {
        "company": None,
        "location": location or "北京",
        "workplace_type": workplace_type or "On-site",
        "min_salary": 10000,
        "max_salary": 20000,
        "pay_type": "Monthly",
        "pay_currency": pay_currency or "CNY",
        "pay_shown_on_ad": False,
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
        "requirements": f"1年以上相关工作经验；具备良好的职业素养和工作态度；有较强的学习能力和适应能力；注重团队合作，积极主动",
        "category": "General Business",
        "recruitment_invitation": f"我们正在寻找合适的{title}加入我们的团队！如果你渴望在专业领域发展，愿意接受挑战，这里将是你施展才华的舞台。",
        "education": "大专及以上"
    }
