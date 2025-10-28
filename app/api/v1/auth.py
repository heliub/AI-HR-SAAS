"""
Authentication endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPAuthorizationCredentials

from app.api.deps import get_db, get_current_user
from app.schemas.auth import LoginRequest, LoginResponse, LogoutRequest, UserInfo
from app.schemas.base import APIResponse
from app.services.user_service import UserService
from app.core.security import security_manager, security
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
    from datetime import datetime, timezone
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    
    # 生成token
    from datetime import datetime, timedelta
    from app.services.auth_token_service import AuthTokenService

    access_token = security_manager.create_access_token(
        data={
            "sub": str(user.id),
            "tenantId": str(user.tenant_id),
            "role": user.role
        }
    )

    # 将token存入数据库用于管理
    auth_token_service = AuthTokenService()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)  # 设置24小时过期

    await auth_token_service.create_token(
        db=db,
        tenant_id=str(user.tenant_id),
        user_id=str(user.id),
        token=access_token,
        expires_at=expires_at
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
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """用户登出（仅当前设备）"""
    from app.services.auth_token_service import AuthTokenService

    token = credentials.credentials
    auth_token_service = AuthTokenService()

    # 撤销当前token（加入黑名单）
    success = await auth_token_service.revoke_token(
        db=db,
        token=token,
        user_id=str(current_user.id)
    )

    if not success:
        return APIResponse(
            code=400,
            message="无效的token或已过期"
        )

    return APIResponse(
        code=200,
        message="登出成功"
    )


@router.post("/logout-all", response_model=APIResponse)
async def logout_all_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """用户登出（所有设备）"""
    from app.services.auth_token_service import AuthTokenService

    auth_token_service = AuthTokenService()

    # 撤销用户的所有token（强制登出所有设备）
    revoked_count = await auth_token_service.revoke_all_user_tokens(
        db=db,
        user_id=str(current_user.id)
    )

    return APIResponse(
        code=200,
        message=f"已成功登出 {revoked_count} 个设备"
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
