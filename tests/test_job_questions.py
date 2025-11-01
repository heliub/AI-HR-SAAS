"""
Job Question API tests
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.models import Job, User, JobQuestion
from app.schemas.job_question import JobQuestionCreate, JobQuestionUpdate
from app.services.job_question_service import JobQuestionService
from app.infrastructure.database.session import get_db


@pytest.mark.asyncio
class TestJobQuestions:
    """职位问题接口测试"""
    
    async def test_get_job_questions_list(self, client: AsyncClient, auth_headers: dict, test_job: Job, db_session: AsyncSession):
        """测试获取职位问题列表"""
        # 先创建一个问题
        job_question_service = JobQuestionService(db_session)
        
        question_data = {
            "question": "您是否有Python开发经验？",
            "question_type": "assessment",
            "is_required": True,
            "evaluation_criteria": "必须具备3年以上Python开发经验"
        }
        
        await job_question_service.create_question(
            job_id=test_job.id,
            tenant_id=test_job.tenant_id,
            user_id=test_job.created_by,
            question_data=question_data
        )
        
        response = await client.get(
            f"/api/v1/jobs/{test_job.id}/questions",
            headers=auth_headers,
            params={"page": 1, "pageSize": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["total"] >= 1
        assert len(data["data"]["list"]) >= 1
        assert data["data"]["list"][0]["question"] == "您是否有Python开发经验？"
    
    async def test_get_job_question_detail(self, client: AsyncClient, auth_headers: dict, test_job: Job, db_session: AsyncSession):
        """测试获取职位问题详情"""
        # 先创建一个问题
        job_question_service = JobQuestionService(db_session)
        
        question_data = {
            "question": "您是否有Python开发经验？",
            "question_type": "assessment",
            "is_required": True,
            "evaluation_criteria": "必须具备3年以上Python开发经验"
        }
        
        created_question = await job_question_service.create_question(
            job_id=test_job.id,
            tenant_id=test_job.tenant_id,
            user_id=test_job.created_by,
            question_data=question_data
        )
        
        response = await client.get(
            f"/api/v1/questions/{created_question.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["question"] == "您是否有Python开发经验？"
        assert data["data"]["questionType"] == "assessment"
        assert data["data"]["isRequired"] is True
    
    async def test_get_job_question_not_found(self, client: AsyncClient, auth_headers: dict):
        """测试获取不存在的问题"""
        response = await client.get(
            f"/api/v1/questions/{uuid4()}",
            headers=auth_headers
        )
        
        # API返回404状态码，而不是200状态码和code=404
        assert response.status_code == 404
    
    async def test_create_job_question(self, client: AsyncClient, auth_headers: dict, test_job: Job):
        """测试创建职位问题"""
        response = await client.post(
            f"/api/v1/jobs/{test_job.id}/questions",
            headers=auth_headers,
            json={
                "question": "您是否有Python开发经验？",
                "questionType": "assessment",
                "isRequired": True,
                "evaluationCriteria": "必须具备3年以上Python开发经验",
                "sortOrder": 1,
                "jobId": str(test_job.id)  # 添加jobId字段
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["question"] == "您是否有Python开发经验？"
        assert data["data"]["questionType"] == "assessment"
        assert data["data"]["isRequired"] is True
        assert data["data"]["jobId"] == str(test_job.id)
    
    async def test_create_job_question_invalid_job(self, client: AsyncClient, auth_headers: dict):
        """测试为不存在的职位创建问题"""
        fake_job_id = uuid4()
        response = await client.post(
            f"/api/v1/jobs/{fake_job_id}/questions",
            headers=auth_headers,
            json={
                "question": "您是否有Python开发经验？",
                "questionType": "assessment",
                "isRequired": True,
                "evaluationCriteria": "必须具备3年以上Python开发经验",
                "jobId": str(fake_job_id)  # 添加jobId字段
            }
        )
        
        # API返回404状态码，而不是200状态码和code=404
        assert response.status_code == 404
    
    async def test_update_job_question(self, client: AsyncClient, auth_headers: dict, test_job: Job, db_session: AsyncSession):
        """测试更新职位问题"""
        # 先创建一个问题
        job_question_service = JobQuestionService(db_session)
        
        question_data = {
            "question": "您是否有Python开发经验？",
            "question_type": "assessment",
            "is_required": True,
            "evaluation_criteria": "必须具备3年以上Python开发经验"
        }
        
        created_question = await job_question_service.create_question(
            job_id=test_job.id,
            tenant_id=test_job.tenant_id,
            user_id=test_job.created_by,
            question_data=question_data
        )
        
        response = await client.put(
            f"/api/v1/questions/{created_question.id}",
            headers=auth_headers,
            json={
                "question": "您是否有5年以上Python开发经验？",
                "questionType": "assessment",
                "isRequired": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["question"] == "您是否有5年以上Python开发经验？"
        assert data["data"]["isRequired"] is False
    
    async def test_update_job_question_not_found(self, client: AsyncClient, auth_headers: dict):
        """测试更新不存在的问题"""
        response = await client.put(
            f"/api/v1/questions/{uuid4()}",
            headers=auth_headers,
            json={
                "question": "您是否有5年以上Python开发经验？",
                "questionType": "assessment",
                "isRequired": False
            }
        )
        
        # API返回404状态码，而不是200状态码和code=404
        assert response.status_code == 404
    
    async def test_delete_job_question(self, client: AsyncClient, auth_headers: dict, test_job: Job, db_session: AsyncSession):
        """测试删除职位问题"""
        # 先创建一个问题
        job_question_service = JobQuestionService(db_session)
        
        question_data = {
            "question": "您是否有Python开发经验？",
            "question_type": "assessment",
            "is_required": True,
            "evaluation_criteria": "必须具备3年以上Python开发经验"
        }
        
        created_question = await job_question_service.create_question(
            job_id=test_job.id,
            tenant_id=test_job.tenant_id,
            user_id=test_job.created_by,
            question_data=question_data
        )
        
        response = await client.delete(
            f"/api/v1/questions/{created_question.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "删除成功"
    
    async def test_delete_job_question_not_found(self, client: AsyncClient, auth_headers: dict):
        """测试删除不存在的问题"""
        response = await client.delete(
            f"/api/v1/questions/{uuid4()}",
            headers=auth_headers
        )
        
        # API返回404状态码，而不是200状态码和code=404
        assert response.status_code == 404
    
    async def test_reorder_job_questions(self, client: AsyncClient, auth_headers: dict, test_job: Job, db_session: AsyncSession):
        """测试重新排序职位问题"""
        # 先创建两个问题
        job_question_service = JobQuestionService(db_session)
        
        question1_data = {
            "question": "您是否有Python开发经验？",
            "question_type": "assessment",
            "is_required": True,
            "evaluation_criteria": "必须具备3年以上Python开发经验"
        }
        
        question2_data = {
            "question": "您的期望薪资是多少？",
            "question_type": "information",
            "is_required": False
        }
        
        question1 = await job_question_service.create_question(
            job_id=test_job.id,
            tenant_id=test_job.tenant_id,
            user_id=test_job.created_by,
            question_data=question1_data
        )
        
        question2 = await job_question_service.create_question(
            job_id=test_job.id,
            tenant_id=test_job.tenant_id,
            user_id=test_job.created_by,
            question_data=question2_data
        )
        
        response = await client.post(
            f"/api/v1/jobs/{test_job.id}/questions/reorder",
            headers=auth_headers,
            json={
                "questions": [
                    {"questionId": str(question1.id), "sortOrder": 2},
                    {"questionId": str(question2.id), "sortOrder": 1}
                ]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "排序成功"
    
    async def test_reorder_job_questions_invalid_job(self, client: AsyncClient, auth_headers: dict):
        """测试为不存在的职位重新排序问题"""
        response = await client.post(
            f"/api/v1/jobs/{uuid4()}/questions/reorder",
            headers=auth_headers,
            json={
                "questions": [
                    {"questionId": str(uuid4()), "sortOrder": 1}
                ]
            }
        )
        
        # API返回404状态码，而不是200状态码和code=404
        assert response.status_code == 404
