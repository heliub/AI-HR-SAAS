"""
Conversation Question Tracking Service tests
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.models import Job, Resume, User, CandidateConversation, ConversationQuestionTracking
from app.services.conversation_question_tracking_service import ConversationQuestionTrackingService


@pytest.mark.asyncio
class TestConversationQuestionTrackingService:
    """会话问题跟踪服务测试"""
    
    async def test_create_question_tracking(self, db_session: AsyncSession, test_job: Job, test_resume: Resume, test_user: User):
        """测试创建问题跟踪记录"""
        # 先创建会话
        conversation_service = ConversationQuestionTrackingService(db_session)
        # 这里直接使用CandidateConversationService创建会话
        from app.services.candidate_conversation_service import CandidateConversationService
        conv_service = CandidateConversationService(db_session)
        
        conversation = await conv_service.create_conversation(
            tenant_id=test_user.tenant_id,
            user_id=test_user.id,
            resume_id=test_resume.id,
            job_id=test_job.id
        )
        
        # 创建问题跟踪记录
        service = ConversationQuestionTrackingService(db_session)
        
        tracking = await service.create_question_tracking(
            conversation_id=conversation.id,
            question_id=uuid4(),
            job_id=test_job.id,
            resume_id=test_resume.id,
            question="您是否有Python开发经验？",
            tenant_id=test_user.tenant_id,
            user_id=test_user.id
        )
        
        assert tracking is not None
        assert tracking.conversation_id == conversation.id
        assert tracking.job_id == test_job.id
        assert tracking.resume_id == test_resume.id
        assert tracking.question == "您是否有Python开发经验？"
        assert tracking.status == "pending"
    
    async def test_get_questions_by_conversation(self, db_session: AsyncSession, test_job: Job, test_resume: Resume, test_user: User):
        """测试根据会话ID获取问题跟踪列表"""
        # 先创建会话
        from app.services.candidate_conversation_service import CandidateConversationService
        conv_service = CandidateConversationService(db_session)
        
        conversation = await conv_service.create_conversation(
            tenant_id=test_user.tenant_id,
            user_id=test_user.id,
            resume_id=test_resume.id,
            job_id=test_job.id
        )
        
        # 创建问题跟踪记录
        service = ConversationQuestionTrackingService(db_session)
        
        question_id = uuid4()
        await service.create_question_tracking(
            conversation_id=conversation.id,
            question_id=question_id,
            job_id=test_job.id,
            resume_id=test_resume.id,
            question="您是否有Python开发经验？",
            tenant_id=test_user.tenant_id,
            user_id=test_user.id
        )
        
        # 获取问题跟踪列表
        trackings = await service.get_questions_by_conversation(
            conversation_id=conversation.id,
            tenant_id=test_user.tenant_id,
            user_id=test_user.id
        )
        
        assert len(trackings) == 1
        assert trackings[0].conversation_id == conversation.id
        assert trackings[0].question_id == question_id
        assert trackings[0].question == "您是否有Python开发经验？"
    
    async def test_update_question_status(self, db_session: AsyncSession, test_job: Job, test_resume: Resume, test_user: User):
        """测试更新问题状态"""
        # 先创建会话
        from app.services.candidate_conversation_service import CandidateConversationService
        conv_service = CandidateConversationService(db_session)
        
        conversation = await conv_service.create_conversation(
            tenant_id=test_user.tenant_id,
            user_id=test_user.id,
            resume_id=test_resume.id,
            job_id=test_job.id
        )
        
        # 创建问题跟踪记录
        service = ConversationQuestionTrackingService(db_session)
        
        tracking = await service.create_question_tracking(
            conversation_id=conversation.id,
            question_id=uuid4(),
            job_id=test_job.id,
            resume_id=test_resume.id,
            question="您是否有Python开发经验？",
            tenant_id=test_user.tenant_id,
            user_id=test_user.id
        )
        
        # 更新状态
        updated_tracking = await service.update_question_status(
            tracking_id=tracking.id,
            tenant_id=test_user.tenant_id,
            status="ongoing",
            user_id=test_user.id
        )
        
        assert updated_tracking is not None
        assert updated_tracking.id == tracking.id
        assert updated_tracking.status == "ongoing"
    
    async def test_update_question_satisfaction(self, db_session: AsyncSession, test_job: Job, test_resume: Resume, test_user: User):
        """测试更新问题满足状态"""
        # 先创建会话
        from app.services.candidate_conversation_service import CandidateConversationService
        conv_service = CandidateConversationService(db_session)
        
        conversation = await conv_service.create_conversation(
            tenant_id=test_user.tenant_id,
            user_id=test_user.id,
            resume_id=test_resume.id,
            job_id=test_job.id
        )
        
        # 创建问题跟踪记录
        service = ConversationQuestionTrackingService(db_session)
        
        tracking = await service.create_question_tracking(
            conversation_id=conversation.id,
            question_id=uuid4(),
            job_id=test_job.id,
            resume_id=test_resume.id,
            question="您是否有Python开发经验？",
            tenant_id=test_user.tenant_id,
            user_id=test_user.id
        )
        
        # 更新满足状态
        updated_tracking = await service.update_question_satisfaction(
            tracking_id=tracking.id,
            tenant_id=test_user.tenant_id,
            is_satisfied=True,
            user_id=test_user.id
        )
        
        assert updated_tracking is not None
        assert updated_tracking.id == tracking.id
        assert updated_tracking.is_satisfied is True
    
    async def test_update_question_tracking(self, db_session: AsyncSession, test_job: Job, test_resume: Resume, test_user: User):
        """测试更新问题跟踪信息"""
        # 先创建会话
        from app.services.candidate_conversation_service import CandidateConversationService
        conv_service = CandidateConversationService(db_session)
        
        conversation = await conv_service.create_conversation(
            tenant_id=test_user.tenant_id,
            user_id=test_user.id,
            resume_id=test_resume.id,
            job_id=test_job.id
        )
        
        # 创建问题跟踪记录
        service = ConversationQuestionTrackingService(db_session)
        
        tracking = await service.create_question_tracking(
            conversation_id=conversation.id,
            question_id=uuid4(),
            job_id=test_job.id,
            resume_id=test_resume.id,
            question="您是否有Python开发经验？",
            tenant_id=test_user.tenant_id,
            user_id=test_user.id
        )
        
        # 更新跟踪信息
        tracking_data = {
            "status": "completed",
            "is_satisfied": True
        }
        
        updated_tracking = await service.update_question_tracking(
            tracking_id=tracking.id,
            tenant_id=test_user.tenant_id,
            tracking_data=tracking_data,
            user_id=test_user.id
        )
        
        assert updated_tracking is not None
        assert updated_tracking.id == tracking.id
        assert updated_tracking.status == "completed"
        assert updated_tracking.is_satisfied is True
    
    async def test_delete_question_tracking(self, db_session: AsyncSession, test_job: Job, test_resume: Resume, test_user: User):
        """测试删除问题跟踪记录"""
        # 先创建会话
        from app.services.candidate_conversation_service import CandidateConversationService
        conv_service = CandidateConversationService(db_session)
        
        conversation = await conv_service.create_conversation(
            tenant_id=test_user.tenant_id,
            user_id=test_user.id,
            resume_id=test_resume.id,
            job_id=test_job.id
        )
        
        # 创建问题跟踪记录
        service = ConversationQuestionTrackingService(db_session)
        
        tracking = await service.create_question_tracking(
            conversation_id=conversation.id,
            question_id=uuid4(),
            job_id=test_job.id,
            resume_id=test_resume.id,
            question="您是否有Python开发经验？",
            tenant_id=test_user.tenant_id,
            user_id=test_user.id
        )
        
        # 删除跟踪记录
        success = await service.delete_question_tracking(
            tracking_id=tracking.id,
            tenant_id=test_user.tenant_id,
            user_id=test_user.id
        )
        
        assert success is True
        
        # 验证跟踪记录已被软删除
        deleted_tracking = await service.get_questions_by_conversation(
            conversation_id=conversation.id,
            tenant_id=test_user.tenant_id,
            user_id=test_user.id
        )
        
        # 应该返回空列表，因为记录已被软删除
        assert len(deleted_tracking) == 0
