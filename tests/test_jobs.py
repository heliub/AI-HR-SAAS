"""
Job API tests
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Job, User


@pytest.mark.asyncio
class TestJobs:
    """职位接口测试"""
    
    async def test_get_jobs_list(self, client: AsyncClient, auth_headers: dict, test_job: Job):
        """测试获取职位列表"""
        response = await client.get(
            "/api/v1/jobs",
            headers=auth_headers,
            params={"page": 1, "pageSize": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["total"] >= 1
        assert len(data["data"]["list"]) >= 1
        assert data["data"]["list"][0]["title"] == "高级前端工程师"
    
    async def test_get_jobs_with_search(self, client: AsyncClient, auth_headers: dict, test_job: Job):
        """测试搜索职位"""
        response = await client.get(
            "/api/v1/jobs",
            headers=auth_headers,
            params={"search": "前端", "page": 1, "pageSize": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["total"] >= 1
    
    async def test_get_jobs_with_status_filter(self, client: AsyncClient, auth_headers: dict, test_job: Job):
        """测试按状态筛选职位"""
        response = await client.get(
            "/api/v1/jobs",
            headers=auth_headers,
            params={"status": "open", "page": 1, "pageSize": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert all(job["status"] == "open" for job in data["data"]["list"])
    
    async def test_get_job_detail(self, client: AsyncClient, auth_headers: dict, test_job: Job):
        """测试获取职位详情"""
        response = await client.get(
            f"/api/v1/jobs/{test_job.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["title"] == "高级前端工程师"
        assert data["data"]["department"] == "技术部"
    
    async def test_get_job_not_found(self, client: AsyncClient, auth_headers: dict):
        """测试获取不存在的职位"""
        from uuid import uuid4
        response = await client.get(
            f"/api/v1/jobs/{uuid4()}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 404
    
    async def test_create_job(self, client: AsyncClient, auth_headers: dict):
        """测试创建职位"""
        response = await client.post(
            "/api/v1/jobs",
            headers=auth_headers,
            json={
                "title": "Python后端工程师",
                "department": "技术部",
                "location": "上海",
                "type": "full-time",
                "status": "draft",
                "salary": "30K-50K",
                "description": "负责后端开发",
                "requirements": ["5年Python经验", "熟悉Django/FastAPI"],
                "education": "本科及以上"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["title"] == "Python后端工程师"
        assert data["data"]["status"] == "draft"
    
    async def test_update_job(self, client: AsyncClient, auth_headers: dict, test_job: Job):
        """测试更新职位"""
        response = await client.put(
            f"/api/v1/jobs/{test_job.id}",
            headers=auth_headers,
            json={
                "title": "资深前端工程师",
                "salary": "30K-50K"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["title"] == "资深前端工程师"
        assert data["data"]["salary"] == "30K-50K"
    
    async def test_update_job_status(self, client: AsyncClient, auth_headers: dict, test_job: Job):
        """测试更新职位状态"""
        response = await client.patch(
            f"/api/v1/jobs/{test_job.id}/status",
            headers=auth_headers,
            json={"status": "closed"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
    
    async def test_duplicate_job(self, client: AsyncClient, auth_headers: dict, test_job: Job):
        """测试复制职位"""
        response = await client.post(
            f"/api/v1/jobs/{test_job.id}/duplicate",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "(副本)" in data["data"]["title"]
        assert data["data"]["status"] == "draft"
    
    async def test_delete_job(self, client: AsyncClient, auth_headers: dict, test_job: Job):
        """测试删除职位"""
        response = await client.delete(
            f"/api/v1/jobs/{test_job.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
    
    async def test_ai_generate_job(self, client: AsyncClient, auth_headers: dict):
        """测试AI生成职位描述"""
        response = await client.post(
            "/api/v1/jobs/ai-generate",
            headers=auth_headers,
            json={
                "title": "高级Java工程师",
                "jobLevel": "P7-P8"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "description" in data["data"]
        assert "recruitmentInvitation" in data["data"]

