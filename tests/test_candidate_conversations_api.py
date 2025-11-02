"""
Candidate Conversation API tests
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.models import Job, Resume, User
from app.main import app


@pytest.mark.asyncio
class TestCandidateConversationAPI:
    """候选人会话API测试"""
    
    async def test_create_conversation(self, client: AsyncClient, db_session: AsyncSession, test_job: Job, test_resume: Resume, test_user: User, auth_headers: dict):
        """测试创建会话API"""
        # 准备请求数据
        request_data = {
            "resume_id": str(test_resume.id),
            "job_id": str(test_job.id)
        }
        
        # 发送请求
        response = await client.post(
            "/api/v1/candidate-conversations/",
            json=request_data,
            headers=auth_headers
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["resumeId"] == str(test_resume.id)
        assert data["jobId"] == str(test_job.id)
        assert data["status"] == "opened"
        assert data["stage"] == "greeting"
        assert "id" in data
    
    async def test_create_conversation_already_exists(self, client: AsyncClient, db_session: AsyncSession, test_job: Job, test_resume: Resume, test_user: User, auth_headers: dict):
        """测试创建已存在的会话"""
        # 先创建一个会话
        from app.services.candidate_conversation_service import CandidateConversationService
        service = CandidateConversationService(db_session)
        await service.create_conversation(
            tenant_id=test_user.tenant_id,
            user_id=test_user.id,
            resume_id=test_resume.id,
            job_id=test_job.id
        )
        
        # 准备请求数据
        request_data = {
            "resume_id": str(test_resume.id),
            "job_id": str(test_job.id)
        }
        
        # 发送请求
        response = await client.post(
            "/api/v1/candidate-conversations/",
            json=request_data,
            headers=auth_headers
        )
        
        # 验证响应
        assert response.status_code == 400
        assert "该简历和职位的会话已存在" in response.json()["detail"]
    
    async def test_get_conversations(self, client: AsyncClient, db_session: AsyncSession, test_job: Job, test_resume: Resume, test_user: User, auth_headers: dict):
        """测试获取会话列表API"""
        # 先创建几个会话
        from app.services.candidate_conversation_service import CandidateConversationService
        service = CandidateConversationService(db_session)
        
        conversation1 = await service.create_conversation(
            tenant_id=test_user.tenant_id,
            user_id=test_user.id,
            resume_id=test_resume.id,
            job_id=test_job.id
        )
        
        # 更新第一个会话状态
        await service.update_conversation_status(
            conversation_id=conversation1.id,
            tenant_id=test_user.tenant_id,
            status="ongoing",
            user_id=test_user.id
        )
        
        # 创建第二个会话
        from app.models import Job as JobModel, Resume as ResumeModel
        job2 = JobModel(
            tenant_id=test_user.tenant_id,
            user_id=test_user.id,
            title="高级工程师",
            description="高级工程师职位描述",
            requirements="5年以上经验"
        )
        db_session.add(job2)
        await db_session.commit()
        await db_session.refresh(job2)
        
        resume2 = ResumeModel(
            tenant_id=test_user.tenant_id,
            user_id=test_user.id,
            name="张三",
            email="zhangsan@example.com",
            phone="13800138000"
        )
        db_session.add(resume2)
        await db_session.commit()
        await db_session.refresh(resume2)
        
        conversation2 = await service.create_conversation(
            tenant_id=test_user.tenant_id,
            user_id=test_user.id,
            resume_id=resume2.id,
            job_id=job2.id
        )
        
        # 获取所有会话
        response = await client.get(
            "/api/v1/candidate-conversations/",
            headers=auth_headers
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["conversations"]) == 2
        
        # 按状态过滤
        response = await client.get(
            "/api/v1/candidate-conversations/?status=ongoing",
            headers=auth_headers
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["conversations"]) == 1
        assert data["conversations"][0]["id"] == str(conversation1.id)
        
        # 按职位过滤
        response = await client.get(
            f"/api/v1/candidate-conversations/?job_id={test_job.id}",
            headers=auth_headers
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["conversations"]) == 1
        assert data["conversations"][0]["id"] == str(conversation1.id)
        
        # 按简历过滤
        response = await client.get(
            f"/api/v1/candidate-conversations/?resume_id={test_resume.id}",
            headers=auth_headers
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["conversations"]) == 1
        assert data["conversations"][0]["id"] == str(conversation1.id)
