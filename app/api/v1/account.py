"""
Account settings endpoints
"""
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.schemas.user import ProfileUpdateRequest, PasswordUpdateRequest, NotificationSettingsRequest
from app.schemas.base import APIResponse
from app.services.user_service import UserService
from app.models.user import User

router = APIRouter()


@router.put("/profile", response_model=APIResponse)
async def update_profile(
    profile_data: ProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新个人信息"""
    user_service = UserService()
    
    # TODO: 实现个人信息更新
    
    return APIResponse(
        code=200,
        message="个人信息更新成功"
    )


@router.put("/password", response_model=APIResponse)
async def update_password(
    password_data: PasswordUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新密码"""
    user_service = UserService()
    
    try:
        await user_service.update_password(
            db=db,
            user_id=current_user.id,
            current_password=password_data.currentPassword,
            new_password=password_data.newPassword
        )
        
        return APIResponse(
            code=200,
            message="密码更新成功"
        )
    except Exception as e:
        return APIResponse(
            code=400,
            message=str(e)
        )


@router.post("/avatar", response_model=APIResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传头像"""
    # TODO: 实现文件上传和头像更新
    
    return APIResponse(
        code=200,
        message="头像上传成功",
        data={"avatarUrl": "https://example.com/avatars/user1.jpg"}
    )


@router.post("/notifications", response_model=APIResponse)
async def update_notifications(
    settings_data: NotificationSettingsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新通知设置"""
    # TODO: 实现通知设置更新
    
    return APIResponse(
        code=200,
        message="通知设置更新成功"
    )

