"""
Account API tests
"""
import pytest
from httpx import AsyncClient

from app.models import User


@pytest.mark.asyncio
class TestAccount:
    """账户设置接口测试"""
    
    async def test_update_password_success(self, client: AsyncClient, auth_headers: dict):
        """测试更新密码成功"""
        response = await client.put(
            "/api/v1/account/password",
            headers=auth_headers,
            json={
                "currentPassword": "password123",
                "newPassword": "newpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "成功" in data["message"]
    
    async def test_update_password_wrong_current(self, client: AsyncClient, auth_headers: dict):
        """测试更新密码当前密码错误"""
        response = await client.put(
            "/api/v1/account/password",
            headers=auth_headers,
            json={
                "currentPassword": "wrongpassword",
                "newPassword": "newpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 400
    
    async def test_update_notifications(self, client: AsyncClient, auth_headers: dict):
        """测试更新通知设置"""
        response = await client.put(
            "/api/v1/account/notifications",
            headers=auth_headers,
            json={
                "emailNotifications": True,
                "taskReminders": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200

