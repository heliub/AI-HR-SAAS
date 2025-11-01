"""
Candidate Conversation Service tests
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.models import Job, Resume, User, CandidateConversation
from app.services.candidate_conversation_service import CandidateConversationService


@pytest.mark.asyncio
class TestCandidateConversationService:
    """候选人会话服务测试"""
    
    async def test_create_conversation(self, db_session: AsyncSession, test_job: Job, test_resume: Resume, test_user: User):
        """测试创建会话"""
        service = CandidateConversationService(db_session)
        
        conversation = await service.create_conversation(
            tenant_id=test_user.tenant_id,
            user_id=test_user.id,
            resume_id=test_resume.id,
            job_id=test_job.id
        )
        
        assert conversation is not None
        assert conversation.tenant_id == test_user.tenant_id
        assert conversation.user_id == test_user.id
        assert conversation.resume_id == test_resume.id
        assert conversation.job_id == test_job.id
        assert conversation.status == "opened"
        assert conversation.stage == "greeting"
    
    async def test_get_conversation_by_id(self, db_session: AsyncSession, test_job: Job, test_resume: Resume, test_user: User):
        """测试根据ID获取会话"""
        service = CandidateConversationService(db_session)
        
        # 先创建会话
        created_conversation = await service.create_conversation(
            tenant_id=test_user.tenant_id,
            user_id=test_user.id,
            resume_id=test_resume.id,
            job_id=test_job.id
        )
        
        # 获取会话
        conversation = await service.get_conversation_by_id(
            conversation_id=created_conversation.id,
            tenant_id=test_user.tenant_id,
            user_id=test_user.id
        )
        
        assert conversation is not None
        assert conversation.id == created_conversation.id
        assert conversation.resume_id == test_resume.id
        assert conversation.job_id == test_job.id
    
    async def test_get_conversation_by_id_not_found(self, db_session: AsyncSession, test_user: User):
        """测试根据ID获取不存在的会话"""
        service = CandidateConversationService(db_session)
        
        conversation = await service.get_conversation_by_id(
            conversation_id=uuid4(),
            tenant_id=test_user.tenant_id,
            user_id=test_user.id
        )
        
        assert conversation is None
    
    async def test_get_conversation_by_job_and_resume(self, db_session: AsyncSession, test_job: Job, test_resume: Resume, test_user: User):
        """测试根据职位ID和简历ID获取会话"""
        service = CandidateConversationService(db_session)
        
        # 先创建会话
        created_conversation = await service.create_conversation(
            tenant_id=test_user.tenant_id,
            user_id=test_user.id,
            resume_id=test_resume.id,
            job_id=test_job.id
        )
        
        # 获取会话
        conversation = await service.get_conversation_by_job_and_resume(
            job_id=test_job.id,
            resume_id=test_resume.id,
            tenant_id=test_user.tenant_id,
            user_id=test_user.id
        )
        
        assert conversation is not None
        assert conversation.id == created_conversation.id
        assert conversation.resume_id == test_resume.id
        assert conversation.job_id == test_job.id
    
    async def test_get_conversation_by_job_and_resume_not_found(self, db_session: AsyncSession, test_job: Job, test_user: User):
        """测试根据职位ID和简历ID获取不存在的会话"""
        service = CandidateConversationService(db_session)
        
        conversation = await service.get_conversation_by_job_and_resume(
            job_id=test_job.id,
            resume_id=uuid4(),
            tenant_id=test_user.tenant_id,
            user_id=test_user.id
        )
        
        assert conversation is None
    
    async def test_update_conversation_status(self, db_session: AsyncSession, test_job: Job, test_resume: Resume, test_user: User):
        """测试更新会话状态"""
        service = CandidateConversationService(db_session)
        
        # 先创建会话
        created_conversation = await service.create_conversation(
            tenant_id=test_user.tenant_id,
            user_id=test_user.id,
            resume_id=test_resume.id,
            job_id=test_job.id
        )
        
        # 更新状态
        updated_conversation = await service.update_conversation_status(
            conversation_id=created_conversation.id,
            tenant_id=test_user.tenant_id,
            status="ongoing",
            user_id=test_user.id
        )
        
        assert updated_conversation is not None
        assert updated_conversation.id == created_conversation.id
        assert updated_conversation.status == "ongoing"
    
    async def test_update_conversation_stage(self, db_session: AsyncSession, test_job: Job, test_resume: Resume, test_user: User):
        """测试更新会话阶段"""
        service = CandidateConversationService(db_session)
        
        # 先创建会话
        created_conversation = await service.create_conversation(
            tenant_id=test_user.tenant_id,
            user_id=test_user.id,
            resume_id=test_resume.id,
            job_id=test_job.id
        )
        
        # 更新阶段
        updated_conversation = await service.update_conversation_stage(
            conversation_id=created_conversation.id,
            tenant_id=test_user.tenant_id,
            stage="questioning",
            user_id=test_user.id
        )
        
        assert updated_conversation is not None
        assert updated_conversation.id == created_conversation.id
        assert updated_conversation.stage == "questioning"
    
    async def test_update_conversation_summary(self, db_session: AsyncSession, test_job: Job, test_resume: Resume, test_user: User):
        """测试更新会话摘要"""
        service = CandidateConversationService(db_session)
        
        # 先创建会话
        created_conversation = await service.create_conversation(
            tenant_id=test_user.tenant_id,
            user_id=test_user.id,
            resume_id=test_resume.id,
            job_id=test_job.id
        )
        
        # 更新摘要
        summary = "候选人对该职位表现出浓厚兴趣，具备相关技能"
        updated_conversation = await service.update_conversation_summary(
            conversation_id=created_conversation.id,
            tenant_id=test_user.tenant_id,
            summary=summary,
            user_id=test_user.id
        )
        
        assert updated_conversation is not None
        assert updated_conversation.id == created_conversation.id
        assert updated_conversation.summary == summary
    
    async def test_update_conversation(self, db_session: AsyncSession, test_job: Job, test_resume: Resume, test_user: User):
        """测试更新会话信息"""
        service = CandidateConversationService(db_session)
        
        # 先创建会话
        created_conversation = await service.create_conversation(
            tenant_id=test_user.tenant_id,
            user_id=test_user.id,
            resume_id=test_resume.id,
            job_id=test_job.id
        )
        
        # 更新会话信息
        conversation_data = {
            "status": "ongoing",
            "stage": "questioning",
            "summary": "候选人对该职位表现出浓厚兴趣"
        }
        
        updated_conversation = await service.update_conversation(
            conversation_id=created_conversation.id,
            tenant_id=test_user.tenant_id,
            conversation_data=conversation_data,
            user_id=test_user.id
        )
        
        assert updated_conversation is not None
        assert updated_conversation.id == created_conversation.id
        assert updated_conversation.status == "ongoing"
        assert updated_conversation.stage == "questioning"
        assert updated_conversation.summary == "候选人对该职位表现出浓厚兴趣"
    
    async def test_delete_conversation(self, db_session: AsyncSession, test_job: Job, test_resume: Resume, test_user: User):
        """测试删除会话"""
        service = CandidateConversationService(db_session)
        
        # 先创建会话
        created_conversation = await service.create_conversation(
            tenant_id=test_user.tenant_id,
            user_id=test_user.id,
            resume_id=test_resume.id,
            job_id=test_job.id
        )
        
        # 删除会话
        success = await service.delete_conversation(
            conversation_id=created_conversation.id,
            tenant_id=test_user.tenant_id,
            user_id=test_user.id
        )
        
        assert success is True
        
        # 验证会话已被软删除
        deleted_conversation = await service.get_conversation_by_id(
            conversation_id=created_conversation.id,
            tenant_id=test_user.tenant_id,
            user_id=test_user.id
        )
        
        assert deleted_conversation is None
