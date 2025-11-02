"""
Candidate Conversation endpoints - 候选人会话相关API
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.api.responses import create_success_response, create_paginated_response
from app.models.user import User
from app.models.job import Job
from app.schemas.base import ListResponse
from app.schemas.candidate_conversation import (
    ConversationMessageListResponse,
    ConversationMessageResponse,
    SendMessageRequest,
    SendMessageResponse,
    CandidateConversationDetailResponse,
    CreateConversationRequest,
    ConversationListResponse,
    CandidateConversationResponse
)
from app.services.candidate_chat_history_service import CandidateChatHistoryService
from app.services.candidate_conversation_service import CandidateConversationService
from app.conversation_flow.orchestrator import ConversationFlowOrchestrator
from app.conversation_flow.models import (
    ConversationContext,
    ConversationStage,
    ConversationStatus,
    PositionInfo,
    Message as FlowMessage,
    NodeAction
)
from app.api.responses import APIResponse

router = APIRouter()


@router.post(
    "/create_conversation",
    response_model=APIResponse,
    summary="创建会话",
    description="根据简历ID和职位ID创建新的候选人会话"
)
async def create_conversation(
    request: CreateConversationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新的候选人会话

    - **resume_id**: 候选人简历ID
    - **job_id**: 职位ID
    """
    # 检查是否已存在相同的会话
    conversation_service = CandidateConversationService(db)
    existing_conversation = await conversation_service.get_conversation_by_job_and_resume(
        job_id=request.jobId,
        resume_id=request.resumeId,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        is_admin=current_user.role == "admin"
    )

    if existing_conversation:
        raise HTTPException(status_code=400, detail="该简历和职位的会话已存在")

    # 创建新会话
    conversation = await conversation_service.create_conversation(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        resume_id=request.resumeId,
        job_id=request.jobId
    )

    # 使用统一的响应格式
    return create_success_response(
        message="会话创建成功",
        data=CandidateConversationResponse.model_validate(conversation).model_dump()
    )


@router.get(
    "/get_conversations",
    response_model=APIResponse,
    summary="获取会话列表",
    description="获取当前用户有权限访问的会话列表"
)
async def get_conversations(
    status: Optional[str] = Query(None, description="会话状态过滤"),
    stage: Optional[str] = Query(None, description="会话阶段过滤"),
    resume_id: Optional[UUID] = Query(None, description="简历ID过滤"),
    job_id: Optional[UUID] = Query(None, description="职位ID过滤"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取会话列表

    - **status**: 会话状态过滤 (opened, ongoing, interrupted, ended)
    - **stage**: 会话阶段过滤 (greeting, questioning, intention, matched)
    - **resume_id**: 简历ID过滤
    - **job_id**: 职位ID过滤
    - **limit**: 返回数量（默认20，最大100）
    - **offset**: 偏移量（用于分页）
    """
    conversation_service = CandidateConversationService(db)
    conversations, total = await conversation_service.get_conversations(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        is_admin=current_user.role == "admin",
        status=status,
        stage=stage,
        resume_id=resume_id,
        job_id=job_id,
        limit=limit,
        offset=offset
    )

    # 转换为响应格式
    conversation_responses = [
        CandidateConversationResponse.model_validate(conv).model_dump()
        for conv in conversations
    ]

    # 使用统一的分页响应格式
    page = (offset // limit) + 1 if limit > 0 else 1
    return create_paginated_response(
        list=conversation_responses,
        total=total,
        page=page,
        page_size=limit,
        message="获取会话列表成功"
    )


@router.get(
    "/{conversation_id}/messages",
    response_model=APIResponse,
    summary="获取会话消息列表",
    description="根据会话ID获取该会话的所有消息记录"
)
async def get_conversation_messages(
    conversation_id: UUID = Path(..., description="会话ID"),
    limit: int = Query(100, ge=1, le=500, description="返回消息数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取会话消息列表

    - **conversation_id**: 会话ID
    - **limit**: 返回消息数量（默认100，最大500）
    - **offset**: 偏移量（用于分页）
    """
    # 验证会话是否存在且用户有权限访问
    conversation_service = CandidateConversationService(db)
    conversation = await conversation_service.get_conversation_by_id(
        conversation_id=conversation_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        is_admin=current_user.role == "admin"
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在或无权限访问")

    # 获取消息列表
    chat_history_service = CandidateChatHistoryService(db)
    messages = await chat_history_service.get_messages_by_conversation(
        conversation_id=conversation_id,
        tenant_id=current_user.tenant_id,
        limit=limit,
        offset=offset,
        order_desc=False  # 按时间正序返回
    )

    # 获取消息总数
    total = await chat_history_service.get_message_count(
        conversation_id=conversation_id,
        tenant_id=current_user.tenant_id
    )

    # 转换为响应格式
    message_responses = [
        ConversationMessageResponse.model_validate(msg).model_dump()
        for msg in messages
    ]

    # 使用统一的分页响应格式
    page = (offset // limit) + 1 if limit > 0 else 1
    return create_paginated_response(
        list=message_responses,
        total=total,
        page=page,
        page_size=limit,
        message="获取会话消息列表成功"
    )


@router.post(
    "/{conversation_id}/messages",
    response_model=APIResponse,
    summary="候选人发送消息",
    description="候选人发送消息，系统自动执行对话流程并返回AI回复"
)
async def send_candidate_message(
    conversation_id: UUID = Path(..., description="会话ID"),
    request: SendMessageRequest = ...,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    候选人发送消息并获取AI响应

    流程：
    1. 验证会话存在性和权限
    2. 保存候选人消息到数据库
    3. 加载会话历史消息
    4. 构建ConversationContext上下文
    5. 执行对话流程（ConversationFlowOrchestrator）
    6. 保存AI回复到数据库
    7. 返回结果

    - **conversation_id**: 会话ID
    - **content**: 消息内容
    """
    # 1. 验证会话
    conversation_service = CandidateConversationService(db)
    conversation = await conversation_service.get_conversation_by_id(
        conversation_id=conversation_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        is_admin=current_user.role == "admin"
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在或无权限访问")

    # 检查会话状态
    if conversation.status in ["ended", "deleted"]:
        raise HTTPException(status_code=400, detail=f"会话已{conversation.status}，无法继续对话")

    # 2. 保存候选人消息
    chat_history_service = CandidateChatHistoryService(db)
    candidate_message = await chat_history_service.create_message(
        tenant_id=current_user.tenant_id,
        resume_id=conversation.resume_id,
        conversation_id=conversation_id,
        sender="candidate",
        message=request.content,
        message_type="text"
    )

    # 3. 加载历史消息（最新50条）
    history_messages = await chat_history_service.get_latest_messages(
        conversation_id=conversation_id,
        tenant_id=current_user.tenant_id,
        limit=50
    )

    # 转换为流程所需的Message格式（倒序，最早的在前）
    history = [
        FlowMessage(
            sender=msg.sender,
            content=msg.message,  # 注意：CandidateChatHistory使用message字段
            message_type=msg.message_type,
            created_at=msg.created_at
        )
        for msg in reversed(history_messages)
    ]

    # 4. 构建ConversationContext
    # 获取职位信息
    from app.services.job_service import JobService
    job_service = JobService(db)
    job = await job_service.get_by_id(
        Job, conversation.job_id, current_user.tenant_id
    )

    position_info = PositionInfo(
        id=job.id,
        name=job.title,
        description=job.description,
        requirements=job.requirements
    ) if job else None

    # 构建上下文
    context = ConversationContext(
        conversation_id=conversation_id,
        tenant_id=current_user.tenant_id,
        user_id=conversation.user_id,
        job_id=conversation.job_id,
        resume_id=conversation.resume_id,
        conversation_status=ConversationStatus(conversation.status),
        conversation_stage=ConversationStage(conversation.stage),
        last_candidate_message=request.content,
        history=history,
        position_info=position_info
    )

    # 5. 执行对话流程
    orchestrator = ConversationFlowOrchestrator(db)
    flow_result = await orchestrator.execute(context)

    # 6. 保存AI回复（如果有）
    ai_message = None
    if flow_result.message:
        ai_message = await chat_history_service.create_message(
            tenant_id=current_user.tenant_id,
            resume_id=conversation.resume_id,
            conversation_id=conversation_id,
            sender="ai",
            message=flow_result.message,
            message_type="answer"
        )

    # 7. 更新会话状态（如果需要）
    if flow_result.action == NodeAction.SUSPEND:
        # 转人工
        await conversation_service.update_conversation_status(
            conversation_id=conversation_id,
            tenant_id=current_user.tenant_id,
            status="interrupted"
        )
    elif flow_result.action == NodeAction.SEND_MESSAGE:
        # 继续对话
        if conversation.status == "opened":
            await conversation_service.update_conversation_status(
                conversation_id=conversation_id,
                tenant_id=current_user.tenant_id,
                status="ongoing"
            )

    # 8. 返回响应
    response_data = {
        "candidateMessage": ConversationMessageResponse.model_validate(candidate_message).model_dump(),
        "aiMessage": ai_message.message if ai_message else None,
        "action": flow_result.action.value,
        "conversationStatus": conversation.status,
        "conversationStage": conversation.stage
    }

    return create_success_response(
        message="消息发送成功",
        data=response_data
    )


@router.get(
    "/{conversation_id}",
    response_model=APIResponse,
    summary="获取会话详情",
    description="获取会话详情，包含基本信息和最新10条消息"
)
async def get_conversation_detail(
    conversation_id: UUID = Path(..., description="会话ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取会话详情

    - **conversation_id**: 会话ID
    """
    # 获取会话
    conversation_service = CandidateConversationService(db)
    conversation = await conversation_service.get_conversation_by_id(
        conversation_id=conversation_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        is_admin=current_user.role == "admin"
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在或无权限访问")

    # 获取最新消息
    chat_history_service = CandidateChatHistoryService(db)
    latest_messages = await chat_history_service.get_latest_messages(
        conversation_id=conversation_id,
        tenant_id=current_user.tenant_id,
        limit=10
    )

    # 获取消息总数
    message_count = await chat_history_service.get_message_count(
        conversation_id=conversation_id,
        tenant_id=current_user.tenant_id
    )

    # 构建响应
    conversation_data = conversation.__dict__.copy()
    conversation_data["latestMessages"] = [
        ConversationMessageResponse.model_validate(msg).model_dump()
            for msg in reversed(latest_messages)  # 倒序显示（最早的在前）
    ]
    conversation_data["messageCount"] = message_count

    # 转换为camelCase格式
    response_data = CandidateConversationDetailResponse.model_validate(conversation_data).model_dump()

    return create_success_response(
        message="获取会话详情成功",
        data=response_data
    )
