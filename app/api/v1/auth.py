"""
Authentication endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.schemas.auth import LoginRequest, LoginResponse, LogoutRequest, UserInfo
from app.schemas.base import APIResponse
from app.services.user_service import UserService
from app.core.security import security_manager
from app.models.user import User

router = APIRouter()


@router.post("/login", response_model=APIResponse)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    user_service = UserService()
    
    # 首先通过邮箱找到用户
    user = await user_service.get_by_email_any_tenant(db, login_data.email)
    
    if not user:
        return APIResponse(
            code=401,
            message="邮箱或密码错误"
        )
    
    # 验证密码
    if not security_manager.verify_password(login_data.password, user.password_hash):
        return APIResponse(
            code=401,
            message="邮箱或密码错误"
        )
    
    # 更新最后登录时间
    from datetime import datetime
    user.last_login_at = datetime.utcnow()
    await db.commit()
    
    # 生成token
    access_token = security_manager.create_access_token(
        data={
            "sub": str(user.id),
            "tenant_id": str(user.tenant_id),
            "role": user.role
        }
    )
    
    user_info = UserInfo(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        avatar=user.avatar_url
    )
    
    response_data = LoginResponse(
        token=access_token,
        user=user_info
    )
    
    return APIResponse(
        code=200,
        message="登录成功",
        data=response_data.model_dump()
    )


@router.post("/logout", response_model=APIResponse)
async def logout(
    logout_data: LogoutRequest,
    db: AsyncSession = Depends(get_db)
):
    """用户登出"""
    # TODO: 实现token撤销逻辑（将token加入黑名单或从数据库中删除）
    
    return APIResponse(
        code=200,
        message="登出成功"
    )


@router.get("/me", response_model=APIResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户信息"""
    user_info = UserInfo(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        avatar=current_user.avatar_url
    )
    
    return APIResponse(
        code=200,
        message="成功",
        data=user_info.model_dump()
    )
