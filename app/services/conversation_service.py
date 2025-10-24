"""
Conversation service
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Conversation, Task, Message
from app.services.base import BaseService
from app.ai.intent_classifier import IntentClassifier
from app.ai.conversation_handler import ConversationHandler
from app.ai.client import get_ai_client


class ConversationService(BaseService[Conversation]):
    """对话服务"""
    
    def __init__(self):
        super().__init__(Conversation)
        ai_client = get_ai_client()
        self.intent_classifier = IntentClassifier(ai_client)
        self.conversation_handler = ConversationHandler(ai_client)
    
    async def process_message(
        self,
        db: AsyncSession,
        user_id: int,
        tenant_id: int,
        message_content: str,
        conversation_id: Optional[int] = None,
        user_language: str = "en"
    ) -> Dict[str, Any]:
        """处理用户消息"""
        
        # 1. 获取或创建会话
        if not conversation_id:
            conversation = await self._create_conversation(db, user_id, tenant_id)
        else:
            conversation = await self.get_by_id(db, conversation_id, tenant_id)
        
        # 2. 获取当前活跃任务
        current_task = await self._get_current_task(db, conversation.id)
        
        # 3. 获取会话历史
        history = await self._get_conversation_history(
            db, 
            conversation.id,
            task_id=current_task.id if current_task else None
        )
        
        # 4. 意图识别
        intent_result = await self.intent_classifier.classify(
            user_message=message_content,
            conversation_history=history,
            current_task=current_task.context if current_task else None
        )
        
        # 5. 任务管理
        task = await self._manage_task(
            db,
            conversation.id,
            user_id,
            tenant_id,
            current_task,
            intent_result
        )
        
        # 6. 保存用户消息
        await self._save_message(
            db,
            conversation.id,
            task.id,
            "user",
            message_content,
            meta_info={"intent": intent_result.dict()}
        )
        
        # 7. 生成AI回复
        ai_response = await self.conversation_handler.generate_response(
            user_message=message_content,
            conversation_history=history,
            task_context=task.context or {},
            intent=intent_result.intent,
            user_language=user_language
        )
        
        # 8. 保存AI消息
        await self._save_message(
            db,
            conversation.id,
            task.id,
            "assistant",
            ai_response
        )
        
        await db.commit()
        
        return {
            "conversation_id": conversation.id,
            "task_id": task.id,
            "task_type": task.task_type,
            "response": ai_response,
            "intent": intent_result.intent
        }
    
    async def _create_conversation(
        self,
        db: AsyncSession,
        user_id: int,
        tenant_id: int
    ) -> Conversation:
        """创建新会话"""
        conversation = Conversation(
            tenant_id=tenant_id,
            user_id=user_id,
            title="New Conversation"
        )
        db.add(conversation)
        await db.flush()
        return conversation
    
    async def _get_current_task(
        self,
        db: AsyncSession,
        conversation_id: int
    ) -> Optional[Task]:
        """获取当前活跃任务"""
        query = select(Task).where(
            Task.conversation_id == conversation_id,
            Task.status == "active"
        ).order_by(Task.last_active_at.desc())
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def _manage_task(
        self,
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        tenant_id: int,
        current_task: Optional[Task],
        intent_result
    ) -> Task:
        """管理任务实例"""
        
        # 如果意图与当前任务一致，继续当前任务
        if current_task and current_task.task_type == intent_result.intent:
            current_task.last_active_at = datetime.utcnow()
            return current_task
        
        # 查找历史任务
        if current_task:
            current_task.status = "inactive"
        
        # 创建新任务
        new_task = Task(
            tenant_id=tenant_id,
            user_id=user_id,
            conversation_id=conversation_id,
            task_type=intent_result.intent,
            context=intent_result.task_context,
            status="active",
            last_active_at=datetime.utcnow()
        )
        db.add(new_task)
        await db.flush()
        
        return new_task
    
    async def _get_conversation_history(
        self,
        db: AsyncSession,
        conversation_id: int,
        task_id: Optional[int] = None,
        limit: int = 20
    ) -> List[Dict[str, str]]:
        """获取会话历史"""
        query = select(Message).where(
            Message.conversation_id == conversation_id
        )
        
        if task_id:
            query = query.where(Message.task_id == task_id)
        
        query = query.order_by(Message.created_at.desc()).limit(limit)
        
        result = await db.execute(query)
        messages = result.scalars().all()
        
        return [
            {"role": msg.role, "content": msg.content}
            for msg in reversed(messages)
        ]
    
    async def _save_message(
        self,
        db: AsyncSession,
        conversation_id: int,
        task_id: int,
        role: str,
        content: str,
        meta_info: Optional[dict] = None
    ) -> Message:
        """保存消息"""
        message = Message(
            tenant_id=await self._get_tenant_id(db, conversation_id),
            conversation_id=conversation_id,
            task_id=task_id,
            role=role,
            content=content,
            meta_info=meta_info
        )
        db.add(message)
        await db.flush()
        return message
    
    async def _get_tenant_id(self, db: AsyncSession, conversation_id: int) -> int:
        """获取会话的租户ID"""
        query = select(Conversation.tenant_id).where(Conversation.id == conversation_id)
        result = await db.execute(query)
        return result.scalar_one()

