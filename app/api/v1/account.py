"""
Account settings endpoints
"""
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.schemas.user import ProfileUpdateRequest, PasswordUpdateRequest, UserSettingRequest, UserSettingResponse
from app.schemas.base import APIResponse
from app.services.user_service import UserService
from app.models.user import User
import traceback

router = APIRouter()


@router.put("/profile", response_model=APIResponse)
async def update_profile(
    profile_data: ProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新个人信息"""
    user_service = UserService()

    try:
        # 转换数据，只传递非空字段
        update_data = {}
        if profile_data.name is not None:
            update_data['name'] = profile_data.name
        if profile_data.email is not None:
            update_data['email'] = profile_data.email

        # 如果没有要更新的字段，直接返回
        if not update_data:
            return APIResponse(
                code=400,
                message="没有要更新的字段"
            )

        # 更新个人信息
        updated_user = await user_service.update_profile(
            db=db,
            user_id=current_user.id,
            **update_data
        )

        # 返回更新后的用户信息（不包含敏感信息）
        from app.schemas.user import UserResponse
        user_response = UserResponse.model_validate(updated_user, from_attributes=True)

        return APIResponse(
            code=200,
            message="个人信息更新成功",
            data=user_response.model_dump(by_alias=True)
        )
    except Exception as e:
        traceback.print_exc()
        # 处理异常
        error_message = str(e)
        if "already registered" in error_message:
            return APIResponse(
                code=400,
                message="该邮箱已被注册"
            )
        return APIResponse(
            code=400,
            message=f"更新失败: {error_message}"
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
    import os
    import uuid
    from datetime import datetime

    user_service = UserService()

    try:
        # 验证文件类型
        if not file.content_type or not file.content_type.startswith('image/'):
            return APIResponse(
                code=400,
                message="只支持图片文件"
            )

        # 验证文件大小（限制为5MB）
        max_size = 5 * 1024 * 1024  # 5MB
        file_content = await file.read()
        if len(file_content) > max_size:
            return APIResponse(
                code=400,
                message="文件大小不能超过5MB"
            )

        # 重置文件指针
        await file.seek(0)

        # 生成唯一文件名
        file_extension = os.path.splitext(file.filename)[1] if file.filename else '.jpg'
        unique_filename = f"{uuid.uuid4()}{file_extension}"

        # 创建上传目录（如果不存在）
        upload_dir = "uploads/avatars"
        os.makedirs(upload_dir, exist_ok=True)

        # 保存文件
        file_path = os.path.join(upload_dir, unique_filename)
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)

        # 生成访问URL
        avatar_url = f"/static/avatars/{unique_filename}"

        # 更新用户头像
        updated_user = await user_service.update_avatar(
            db=db,
            user_id=current_user.id,
            avatar_url=avatar_url
        )

        return APIResponse(
            code=200,
            message="头像上传成功",
            data={"avatarUrl": avatar_url}
        )
    except Exception as e:
        # 如果上传失败，删除已上传的文件
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)

        return APIResponse(
            code=500,
            message=f"头像上传失败: {str(e)}"
        )


@router.post("/settings", response_model=APIResponse)
async def update_user_settings(
    settings_data: UserSettingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新用户设置"""
    user_service = UserService()
    print("settings_data", settings_data)
    try:
        # 更新用户设置
        result = await user_service.update_user_settings(
            db=db,
            user_id=current_user.id,
            language=settings_data.language,
            email_notifications=settings_data.emailNotifications,
            task_reminders=settings_data.taskReminders
        )

        return APIResponse(
            code=200,
            message="用户设置更新成功",
            data=result
        )
    except Exception as e:
        return APIResponse(
            code=400,
            message=f"更新失败: {str(e)}"
        )


@router.get("/settings", response_model=APIResponse)
async def get_user_settings(
    current_user: User = Depends(get_current_user)
):
    """获取用户设置"""
    user_service = UserService()

    try:
        # 获取用户设置
        result = await user_service.get_user_settings(
            user_id=current_user.id
        )

        return APIResponse(
            code=200,
            message="获取用户设置成功",
            data=result
        )
    except Exception as e:
        return APIResponse(
            code=400,
            message=f"获取失败: {str(e)}"
        )

