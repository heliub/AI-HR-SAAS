"""
User endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, get_current_admin_user
from app.schemas.user import UserCreate, UserResponse, UserListResponse
from app.services.user_service import UserService
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """创建用户（仅管理员）"""
    user_service = UserService()
    
    user = await user_service.create_user(
        db=db,
        tenant_id=user_data.tenant_id,
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        role=user_data.role,
        language=user_data.language
    )
    
    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户信息"""
    return UserResponse.model_validate(current_user)


@router.get("/", response_model=UserListResponse)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户列表"""
    user_service = UserService()
    
    users = await user_service.get_multi(
        db=db,
        skip=skip,
        limit=limit,
        tenant_id=current_user.tenant_id
    )
    
    total = len(users)  # TODO: 实现count方法
    
    return UserListResponse(
        users=[UserResponse.model_validate(u) for u in users],
        total=total
    )

