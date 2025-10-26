"""
Authentication API tests
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Tenant


@pytest.mark.asyncio
class TestAuth:
    """认证接口测试"""
    
    async def test_login_success(self, client: AsyncClient, test_user: User):
        """测试登录成功"""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "登录成功"
        assert "token" in data["data"]
        assert data["data"]["user"]["email"] == "test@example.com"
    
    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        """测试登录密码错误"""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 401
        assert "错误" in data["message"]
    
    async def test_login_user_not_found(self, client: AsyncClient):
        """测试登录用户不存在"""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "notexist@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 401
    
    async def test_get_current_user(self, client: AsyncClient, auth_headers: dict, test_user: User):
        """测试获取当前用户信息"""
        response = await client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["email"] == "test@example.com"
        assert data["data"]["name"] == "测试用户"
    
    async def test_get_current_user_without_token(self, client: AsyncClient):
        """测试未携带token获取用户信息"""
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 403
    
    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """测试无效token获取用户信息"""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
    
    async def test_logout(self, client: AsyncClient, auth_token: str):
        """测试登出"""
        response = await client.post(
            "/api/v1/auth/logout",
            json={"token": auth_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "登出成功"

