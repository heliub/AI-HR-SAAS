"""
Resume endpoints
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.api.deps import get_db, get_current_user
from app.schemas.resume import (
    ResumeCreate, ResumeUpdate, ResumeStatusUpdate,
    ResumeResponse, ResumeDetailResponse, AIMatchRequest, SendEmailRequest
)
from app.schemas.base import APIResponse, PaginatedResponse
from app.services.resume_service import ResumeService
from app.models.user import User
from app.models.resume import Resume

router = APIRouter()


@router.get("", response_model=APIResponse)
async def get_resumes(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    jobId: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取简历列表"""
    resume_service = ResumeService(db)

    skip = (page - 1) * pageSize
    # 判断是否为管理员
    is_admin = current_user.role == "admin"

    # 为管理员查看所有租户数据，HR查看自己的数据
    if is_admin:
        # 管理员可以查看所有租户的简历
        resumes = await resume_service.search_resumes_without_tenant_filter(
            user_id=current_user.id if not is_admin else None,
            keyword=search,
            status=status,
            job_id=jobId,
            skip=skip,
            limit=pageSize,
            is_admin=is_admin
        )
    else:
        # HR只能查看自己租户的简历
        resumes = await resume_service.search_resumes(
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            keyword=search,
            status=status,
            job_id=jobId,
            skip=skip,
            limit=pageSize,
            is_admin=is_admin
        )

    # 获取总数
    if is_admin:
        # 管理员统计所有简历数量
        total = await resume_service.count_without_tenant_filter(
            Resume,
            user_id=current_user.id if not is_admin else None,
            filters={
                "status": status,
                "job_id": jobId
            } if status or jobId else None,
            is_admin=is_admin
        )
    else:
        # HR统计自己租户的简历数量
        total = await resume_service.count(
            Resume,
            current_user.tenant_id,
            current_user.id,
            {
                "status": status,
                "job_id": jobId
            } if status or jobId else None,
            is_admin=is_admin
        )

    resume_responses = [ResumeResponse.model_validate(resume, from_attributes=True) for resume in resumes]

    paginated_data = PaginatedResponse(
        total=total,
        page=page,
        pageSize=pageSize,
        list=resume_responses
    )

    return APIResponse(
        code=200,
        message="成功",
        data=paginated_data.model_dump()
    )


@router.get("/{resume_id}", response_model=APIResponse)
async def get_resume(
    resume_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取简历详情"""
    resume_service = ResumeService(db)

    # 直接查询简历，不限制tenant（管理员可以查看所有，HR只能查看自己租户的）
    from sqlalchemy import select

    is_admin = current_user.role == "admin"

    if is_admin:
        # 管理员可以查看所有租户的简历
        resume_query = select(Resume).where(Resume.id == resume_id)
    else:
        # HR只能查看自己租户的简历
        resume_query = select(Resume).where(
            and_(Resume.id == resume_id, Resume.tenant_id == current_user.tenant_id)
        )

    # 添加user_id过滤（非管理员）
    if not is_admin:
        resume_query = resume_query.where(Resume.user_id == current_user.id)

    resume_result = await db.execute(resume_query)
    resume_basic = resume_result.scalar()

    if not resume_basic:
        return APIResponse(
            code=404,
            message="简历不存在或无权限访问"
        )

    # 获取完整的简历详情
    resume_data = await resume_service.get_resume_full_details(resume_id, resume_basic.tenant_id)

    if not resume_data:
        return APIResponse(
            code=404,
            message="简历不存在"
        )

    # 导入时间格式化工具
    from app.utils.datetime_formatter import format_datetime, format_date

    # 构建简历详情数据 - 使用数据库原始数据，让Schema自动转换
    resume_detail_data = {
        # 基础简历信息 - 直接使用数据库字段
        "id": resume_data["resume"].id,
        "created_at": resume_data["resume"].created_at,
        "updated_at": resume_data["resume"].updated_at,
        "tenant_id": resume_data["resume"].tenant_id,
        "user_id": resume_data["resume"].user_id,
        "candidate_name": resume_data["resume"].candidate_name,
        "email": resume_data["resume"].email,
        "phone": resume_data["resume"].phone,
        "position": resume_data["resume"].position,
        "status": resume_data["resume"].status,
        "source": resume_data["resume"].source,
        "source_channel_id": resume_data["resume"].source_channel_id,
        "job_id": resume_data["resume"].job_id,
        "experience_years": resume_data["resume"].experience_years,
        "education_level": resume_data["resume"].education_level,
        "age": resume_data["resume"].age,
        "gender": resume_data["resume"].gender,
        "location": resume_data["resume"].location,
        "school": resume_data["resume"].school,
        "major": resume_data["resume"].major,
        "skills": resume_data["resume"].skills,
        "resume_url": resume_data["resume"].resume_url,
        "conversation_summary": resume_data["resume"].conversation_summary,
        "submitted_at": resume_data["resume"].submitted_at,

        # 关联数据 - 使用数据库原始数据
        "work_experiences": [
            {
                **work.__dict__,
                "start_date": format_date(work.start_date) if work.start_date else None,
                "end_date": format_date(work.end_date) if work.end_date else None
            }
            for work in resume_data["work_experiences"]
        ],
        "project_experiences": [
            {
                **project.__dict__,
                "start_date": format_date(project.start_date) if project.start_date else None,
                "end_date": format_date(project.end_date) if project.end_date else None
            }
            for project in resume_data["project_experiences"]
        ],
        "education_histories": [
            {
                **edu.__dict__,
                "start_date": format_date(edu.start_date) if edu.start_date else None,
                "end_date": format_date(edu.end_date) if edu.end_date else None
            }
            for edu in resume_data["education_histories"]
        ],
        "job_preference": {
            **resume_data["job_preference"].__dict__,
            "available_date": format_date(resume_data["job_preference"].available_date) if resume_data["job_preference"] and resume_data["job_preference"].available_date else None
        } if resume_data["job_preference"] else None,
        "ai_match_results": [
            {
                **match.__dict__,
                "is_match": match.is_match,
                "match_score": match.match_score
            }
            for match in resume_data["ai_match_results"]
        ],
        "chat_histories": [
            {
                **chat.__dict__,
                "created_at": format_datetime(chat.created_at)
            }
            for chat in resume_data["chat_histories"]
        ],
        "interviews": [
            {
                "id": interview.id,
                "candidate_id": interview.candidate_id,
                "candidate_name": interview.candidate_name,
                "position": interview.position,
                "interview_date": format_date(interview.interview_date) if interview.interview_date else None,
                "interview_time": interview.interview_time.strftime("%H:%M") if interview.interview_time else None,
                "interviewer": interview.interviewer,
                "interviewer_title": interview.interviewer_title,
                "type": interview.type,
                "location": interview.location,
                "meeting_link": interview.meeting_link,
                "notes": interview.notes,
                "status": interview.status,
                "feedback": interview.feedback,
                "rating": interview.rating,
                "cancelled_at": format_datetime(interview.cancelled_at) if interview.cancelled_at else None,
                "cancellation_reason": interview.cancellation_reason,
                "created_at": format_datetime(interview.created_at) if interview.created_at else None,
                "updated_at": format_datetime(interview.updated_at) if interview.updated_at else None,
                "tenant_id": interview.tenant_id,
                "user_id": interview.user_id
            }
            for interview in resume_data["interviews"]
        ],
        "email_logs": [
            {
                "id": email.id,
                "recipient_email": email.recipient_email,
                "subject": email.subject,
                "content": email.content,
                "template_name": email.template_name,
                "status": email.status,
                "error_message": email.error_message,
                "resume_id": email.resume_id,
                "sent_by": email.sent_by,
                "sent_at": format_datetime(email.sent_at) if email.sent_at else None,
                "created_at": format_datetime(email.created_at) if email.created_at else None,
                "updated_at": format_datetime(email.updated_at) if email.updated_at else None,
                "tenant_id": email.tenant_id
            }
            for email in resume_data["email_logs"]
        ]
    }

    # 让Schema自动处理字段转换
    resume_response = ResumeDetailResponse.model_validate(resume_detail_data, from_attributes=False)

    return APIResponse(
        code=200,
        message="成功",
        data=resume_response.model_dump()
    )


@router.patch("/{resume_id}/status", response_model=APIResponse)
async def update_resume_status(
    resume_id: UUID,
    status_data: ResumeStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新简历状态"""
    resume_service = ResumeService(db)

    # 使用新的服务方法更新状态
    updated_resume = await resume_service.update_resume_status(
        resume_id=resume_id,
        tenant_id=current_user.tenant_id,
        status=status_data.status
    )

    if not updated_resume:
        return APIResponse(
            code=404,
            message="简历不存在"
        )

    resume_response = ResumeResponse.model_validate(updated_resume, from_attributes=True)

    return APIResponse(
        code=200,
        message="状态更新成功",
        data=resume_response.model_dump()
    )


@router.post("/{resume_id}/ai-match", response_model=APIResponse)
async def ai_match_resume(
    resume_id: UUID,
    match_data: AIMatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI匹配分析"""
    resume_service = ResumeService(db)

    # 使用新的服务方法检查简历是否存在
    resume_data = resume_service.get_resume_with_job_and_candidate(resume_id, current_user.tenant_id)
    if not resume_data:
        return APIResponse(
            code=404,
            message="简历不存在"
        )

    # 智能AI匹配分析
    if isinstance(db, AsyncSession):
        match_result = await _analyze_resume_match_async(resume_data, match_data.jobId, db)
    else:
        match_result = _analyze_resume_match(resume_data, match_data.jobId, db)

    return APIResponse(
        code=200,
        message="分析完成",
        data=match_result
    )


@router.post("/{resume_id}/send-email", response_model=APIResponse)
def send_email_to_candidate(
    resume_id: UUID,
    email_data: SendEmailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """发送邮件"""
    resume_service = ResumeService(db)

    # 使用新的服务方法检查简历是否存在
    resume_data = resume_service.get_resume_with_job_and_candidate(resume_id, current_user.tenant_id)
    if not resume_data:
        return APIResponse(
            code=404,
            message="简历不存在"
        )

    # TODO: 实现邮件发送逻辑

    return APIResponse(
        code=200,
        message="邮件发送成功"
    )


@router.get("/{resume_id}/download", response_model=APIResponse)
def download_resume(
    resume_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载简历"""
    resume_service = ResumeService(db)

    # 使用新的服务方法检查简历是否存在
    resume_data = resume_service.get_resume_with_job_and_candidate(resume_id, current_user.tenant_id)
    if not resume_data:
        return APIResponse(
            code=404,
            message="简历不存在"
        )

    # TODO: 实现文件下载逻辑

    return APIResponse(
        code=200,
        message="成功",
        data={"resumeUrl": resume_data["resume"].resume_url}
    )


async def _analyze_resume_match_async(resume_data: dict, job_id: UUID, db: AsyncSession) -> dict:
    """
    AI简历匹配分析（异步版本）

    Args:
        resume_data: 简历数据
        job_id: 职位ID
        db: 数据库会话

    Returns:
        dict: 匹配分析结果
    """
    try:
        # 获取职位信息
        from app.services.job_service import JobService
        job_service = JobService(db)
        job = await job_service.get_async(db, job_id)

        if not job:
            return {
                "isMatch": False,
                "score": 0,
                "reason": "目标职位不存在",
                "strengths": [],
                "weaknesses": ["职位信息缺失"],
                "recommendation": "无法进行匹配分析"
            }

        # 基于职位标题和简历信息的智能匹配分析
        job_title = job.title.lower()
        candidate_name = getattr(resume_data.get("candidate"), "name", "候选人")

        # 模拟匹配分数计算逻辑
        match_score = _calculate_match_score(job_title, resume_data)

        return {
            "isMatch": match_score >= 60,
            "score": match_score,
            "reason": _generate_match_reason(match_score, job_title, candidate_name),
            "strengths": _identify_strengths(job_title, resume_data),
            "weaknesses": _identify_weaknesses(job_title, resume_data),
            "recommendation": _generate_recommendation(match_score)
        }

    except Exception as e:
        # 返回默认错误结果
        return {
            "isMatch": False,
            "score": 0,
            "reason": f"匹配分析失败: {str(e)}",
            "strengths": [],
            "weaknesses": ["分析过程出现错误"],
            "recommendation": "请稍后重试或联系技术支持"
        }


def _analyze_resume_match(resume_data: dict, job_id: UUID, db: Session) -> dict:
    """
    AI简历匹配分析

    Args:
        resume_data: 简历数据
        job_id: 职位ID
        db: 数据库会话

    Returns:
        dict: 匹配分析结果
    """
    try:
        # 获取职位信息
        from app.services.job_service import JobService
        job_service = JobService(db)
        job = job_service.get(db, job_id)

        if not job:
            return {
                "isMatch": False,
                "score": 0,
                "reason": "目标职位不存在",
                "strengths": [],
                "weaknesses": ["职位信息缺失"],
                "recommendation": "无法进行匹配分析"
            }

        # 基于职位标题和简历信息的智能匹配分析
        job_title = job.title.lower()
        candidate_name = getattr(resume_data.get("candidate"), "name", "候选人")

        # 模拟匹配分数计算逻辑
        match_score = _calculate_match_score(job_title, resume_data)

        return {
            "isMatch": match_score >= 60,
            "score": match_score,
            "reason": _generate_match_reason(match_score, job_title, candidate_name),
            "strengths": _identify_strengths(job_title, resume_data),
            "weaknesses": _identify_weaknesses(job_title, resume_data),
            "recommendation": _generate_recommendation(match_score)
        }

    except Exception as e:
        # 返回默认错误结果
        return {
            "isMatch": False,
            "score": 0,
            "reason": f"匹配分析失败: {str(e)}",
            "strengths": [],
            "weaknesses": ["分析过程出现错误"],
            "recommendation": "请稍后重试或联系技术支持"
        }


def _calculate_match_score(job_title: str, resume_data: dict) -> int:
    """
    计算简历与职位的匹配分数

    Args:
        job_title: 职位标题
        resume_data: 简历数据

    Returns:
        int: 匹配分数 (0-100)
    """
    base_score = 50  # 基础分数

    # 基于职位类型的分数调整
    if "前端" in job_title or "front" in job_title:
        base_score += 25
    elif "后端" in job_title or "back" in job_title:
        base_score += 20
    elif "产品" in job_title or "product" in job_title:
        base_score += 15
    elif "设计" in job_title or "design" in job_title:
        base_score += 18

    # 模拟基于简历经验年限的调整
    work_experience = resume_data.get("work_experience", [])
    if len(work_experience) >= 3:
        base_score += 15
    elif len(work_experience) >= 1:
        base_score += 8

    # 模拟基于教育背景的调整
    education = resume_data.get("education", [])
    if education:
        base_score += 5

    return min(100, max(0, base_score))


def _generate_match_reason(score: int, job_title: str, candidate_name: str) -> str:
    """
    生成匹配原因说明
    """
    if score >= 90:
        return f"{candidate_name}与{job_title}职位高度匹配，具备优秀的专业背景和相关经验"
    elif score >= 75:
        return f"{candidate_name}与{job_title}职位匹配度良好，大部分要求都满足"
    elif score >= 60:
        return f"{candidate_name}与{job_title}职位基本匹配，具备一定基础"
    else:
        return f"{candidate_name}与{job_title}职位匹配度较低，建议考虑其他职位"


def _identify_strengths(job_title: str, resume_data: dict) -> list:
    """
    识别简历优势
    """
    strengths = []
    work_exp = resume_data.get("work_experience", [])
    education = resume_data.get("education", [])

    if len(work_exp) >= 3:
        strengths.append(f"拥有{len(work_exp)}年丰富工作经验")

    if len(work_exp) >= 1:
        first_exp = work_exp[0]
        if hasattr(first_exp, 'company') and first_exp.company:
            strengths.append(f"曾就职于{first_exp.company}")

    if "前端" in job_title:
        strengths.extend(["熟悉前端开发技术栈", "具备良好的代码规范"])
    elif "产品" in job_title:
        strengths.extend(["具备产品思维", "熟悉用户需求分析"])

    if education:
        strengths.append("教育背景良好")

    return strengths[:4]  # 最多返回4个优势


def _identify_weaknesses(job_title: str, resume_data: dict) -> list:
    """
    识别简历不足
    """
    weaknesses = []
    work_exp = resume_data.get("work_experience", [])

    if len(work_exp) < 1:
        weaknesses.append("缺少实际工作经验")
    elif len(work_exp) < 2:
        weaknesses.append("工作经验相对较少")

    # 基于职位类型的特定不足
    if "前端" in job_title:
        weaknesses.append("移动端开发经验不足")
    elif "产品" in job_title:
        weaknesses.append("缺少完整产品案例")

    return weaknesses[:3]  # 最多返回3个不足


def _generate_recommendation(score: int) -> str:
    """
    生成推荐建议
    """
    if score >= 90:
        return "强烈推荐面试，候选人非常匹配"
    elif score >= 75:
        return "推荐面试，候选人比较匹配"
    elif score >= 60:
        return "可以考虑面试，但需要进一步了解"
    else:
        return "不太推荐，建议寻找其他候选人"

