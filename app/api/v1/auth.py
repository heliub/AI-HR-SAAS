"""
Authentication endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.user_service import UserService
from app.core.security import security_manager

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    user_service = UserService()
    
    # TODO: 需要从请求中获取或从用户数据中确定tenant_id
    # 这里暂时硬编码，实际应该有租户识别机制
    tenant_id = 1
    
    user = await user_service.authenticate(
        db=db,
        email=login_data.email,
        password=login_data.password,
        tenant_id=tenant_id
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # 生成token
    access_token = security_manager.create_access_token(
        data={
            "sub": user.id,
            "tenant_id": user.tenant_id,
            "role": user.role
        }
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        tenant_id=user.tenant_id,
        username=user.username,
        role=user.role
    )

