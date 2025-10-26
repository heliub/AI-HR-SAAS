"""
Resume API tests
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Resume, Job


@pytest.mark.asyncio
class TestResumes:
    """简历接口测试"""
    
    async def test_get_resumes_list(self, client: AsyncClient, auth_headers: dict, test_resume: Resume):
        """测试获取简历列表"""
        response = await client.get(
            "/api/v1/resumes",
            headers=auth_headers,
            params={"page": 1, "pageSize": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["total"] >= 1
        assert len(data["data"]["list"]) >= 1
    
    async def test_get_resumes_with_search(self, client: AsyncClient, auth_headers: dict, test_resume: Resume):
        """测试搜索简历"""
        response = await client.get(
            "/api/v1/resumes",
            headers=auth_headers,
            params={"search": "张伟", "page": 1, "pageSize": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["total"] >= 1
    
    async def test_get_resumes_with_status_filter(self, client: AsyncClient, auth_headers: dict, test_resume: Resume):
        """测试按状态筛选简历"""
        response = await client.get(
            "/api/v1/resumes",
            headers=auth_headers,
            params={"status": "pending", "page": 1, "pageSize": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
    
    async def test_get_resumes_with_job_filter(self, client: AsyncClient, auth_headers: dict, test_resume: Resume, test_job: Job):
        """测试按职位筛选简历"""
        response = await client.get(
            "/api/v1/resumes",
            headers=auth_headers,
            params={"jobId": str(test_job.id), "page": 1, "pageSize": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
    
    async def test_get_resume_detail(self, client: AsyncClient, auth_headers: dict, test_resume: Resume):
        """测试获取简历详情"""
        response = await client.get(
            f"/api/v1/resumes/{test_resume.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["candidateName"] == "张伟"
        assert data["data"]["email"] == "zhangwei@example.com"
    
    async def test_get_resume_not_found(self, client: AsyncClient, auth_headers: dict):
        """测试获取不存在的简历"""
        from uuid import uuid4
        response = await client.get(
            f"/api/v1/resumes/{uuid4()}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 404
    
    async def test_update_resume_status(self, client: AsyncClient, auth_headers: dict, test_resume: Resume):
        """测试更新简历状态"""
        response = await client.patch(
            f"/api/v1/resumes/{test_resume.id}/status",
            headers=auth_headers,
            json={"status": "reviewing"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
    
    async def test_ai_match_resume(self, client: AsyncClient, auth_headers: dict, test_resume: Resume, test_job: Job):
        """测试AI匹配分析"""
        response = await client.post(
            f"/api/v1/resumes/{test_resume.id}/ai-match",
            headers=auth_headers,
            json={"jobId": str(test_job.id)}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "isMatch" in data["data"]
        assert "score" in data["data"]
    
    async def test_send_email_to_candidate(self, client: AsyncClient, auth_headers: dict, test_resume: Resume):
        """测试发送邮件"""
        response = await client.post(
            f"/api/v1/resumes/{test_resume.id}/send-email",
            headers=auth_headers,
            json={
                "subject": "面试邀请",
                "content": "您好，我们想邀请您参加面试..."
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
    
    async def test_download_resume(self, client: AsyncClient, auth_headers: dict, test_resume: Resume):
        """测试下载简历"""
        response = await client.get(
            f"/api/v1/resumes/{test_resume.id}/download",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

