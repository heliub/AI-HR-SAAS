"""
Candidate Conversation endpoints - 候选人会话相关API
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.api.responses import success_response
from app.models.user import User
from app.schemas.candidate_conversation import (
    ConversationMessageListResponse,
    ConversationMessageResponse,
    SendMessageRequest,
    SendMessageResponse,
    CandidateConversationDetailResponse
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

router = APIRouter()


@router.get(
    "/{conversation_id}/messages",
    response_model=ConversationMessageListResponse,
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
        is_admin=current_user.is_admin
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
        ConversationMessageResponse.model_validate(msg)
        for msg in messages
    ]

    return ConversationMessageListResponse(
        total=total,
        messages=message_responses
    )


@router.post(
    "/{conversation_id}/messages",
    response_model=SendMessageResponse,
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
        is_admin=current_user.is_admin
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
    job = await job_service.get_job_by_id(
        job_id=conversation.job_id,
        tenant_id=current_user.tenant_id
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
    return SendMessageResponse(
        candidate_message=ConversationMessageResponse.model_validate(candidate_message),
        ai_message=ConversationMessageResponse.model_validate(ai_message) if ai_message else None,
        action=flow_result.action.value,
        conversation_status=conversation.status,
        conversation_stage=conversation.stage
    )


@router.get(
    "/{conversation_id}",
    response_model=CandidateConversationDetailResponse,
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
        is_admin=current_user.is_admin
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
    return CandidateConversationDetailResponse(
        **conversation.__dict__,
        latest_messages=[
            ConversationMessageResponse.model_validate(msg)
            for msg in reversed(latest_messages)  # 倒序显示（最早的在前）
        ],
        message_count=message_count
    )
