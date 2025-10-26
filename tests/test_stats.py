"""
Statistics API tests
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestStats:
    """统计接口测试"""
    
    async def test_get_dashboard_stats(self, client: AsyncClient, auth_headers: dict):
        """测试获取Dashboard统计"""
        response = await client.get(
            "/api/v1/stats/dashboard",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "pendingResumes" in data["data"]
        assert "upcomingInterviews" in data["data"]
        assert "activeTasks" in data["data"]
        assert "openJobs" in data["data"]
    
    async def test_get_job_stats(self, client: AsyncClient, auth_headers: dict):
        """测试获取职位统计"""
        response = await client.get(
            "/api/v1/stats/jobs",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "totalJobs" in data["data"]
        assert "activeJobs" in data["data"]
    
    async def test_get_resume_stats(self, client: AsyncClient, auth_headers: dict):
        """测试获取简历统计"""
        response = await client.get(
            "/api/v1/stats/resumes",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "total" in data["data"]
        assert "pending" in data["data"]
    
    async def test_get_channel_stats(self, client: AsyncClient, auth_headers: dict):
        """测试获取渠道统计"""
        response = await client.get(
            "/api/v1/stats/channels",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "totalChannels" in data["data"]
    
    async def test_get_funnel_stats(self, client: AsyncClient, auth_headers: dict):
        """测试获取招聘漏斗统计"""
        response = await client.get(
            "/api/v1/stats/funnel",
            headers=auth_headers,
            params={
                "startDate": "2025-01-01",
                "endDate": "2025-01-31"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "totalResumes" in data["data"]
        assert "conversionRates" in data["data"]

