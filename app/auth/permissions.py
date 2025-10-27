"""
完整的RBAC权限系统
基于角色的访问控制
"""
from enum import Enum
from typing import List, Dict, Set, Optional
from uuid import UUID
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)


class Permission(Enum):
    """权限枚举"""

    # 简历相关权限
    READ_RESUME = "read:resume"
    WRITE_RESUME = "write:resume"
    DELETE_RESUME = "delete:resume"
    READ_ALL_RESUMES = "read:all_resumes"
    EXPORT_RESUMES = "export:resumes"

    # 职位相关权限
    READ_JOB = "read:job"
    WRITE_JOB = "write:job"
    DELETE_JOB = "delete:job"
    PUBLISH_JOB = "publish:job"

    # 候选人相关权限
    READ_CANDIDATE = "read:candidate"
    WRITE_CANDIDATE = "write:candidate"
    DELETE_CANDIDATE = "delete:candidate"
    CONTACT_CANDIDATE = "contact:candidate"

    # 面试相关权限
    READ_INTERVIEW = "read:interview"
    WRITE_INTERVIEW = "write:interview"
    DELETE_INTERVIEW = "delete:interview"
    SCHEDULE_INTERVIEW = "schedule:interview"

    # 统计相关权限
    READ_ANALYTICS = "read:analytics"
    READ_DASHBOARD = "read:dashboard"

    # 系统管理权限
    MANAGE_USERS = "manage:users"
    MANAGE_TENANT = "manage:tenant"
    SYSTEM_ADMIN = "system:admin"


class Role(Enum):
    """角色枚举"""

    # 租户级别角色
    TENANT_ADMIN = "tenant_admin"  # 租户管理员
    HR_MANAGER = "hr_manager"      # HR经理
    HR_SPECIALIST = "hr_specialist"  # HR专员
    RECRUITER = "recruiter"        # 招聘专员
    INTERVIEWER = "interviewer"    # 面试官

    # 系统级别角色
    SYSTEM_ADMIN = "system_admin"  # 系统管理员
    SUPPORT = "support"            # 技术支持


@dataclass
class RolePermission:
    """角色权限映射"""
    role: Role
    permissions: Set[Permission]
    description: str


# 预定义的角色权限映射
ROLE_PERMISSIONS: Dict[Role, RolePermission] = {
    Role.TENANT_ADMIN: RolePermission(
        role=Role.TENANT_ADMIN,
        permissions={
            # 简历权限
            Permission.READ_ALL_RESUMES, Permission.WRITE_RESUME, Permission.DELETE_RESUME,
            Permission.EXPORT_RESUMES,
            # 职位权限
            Permission.READ_JOB, Permission.WRITE_JOB, Permission.DELETE_JOB, Permission.PUBLISH_JOB,
            # 候选人权限
            Permission.READ_CANDIDATE, Permission.WRITE_CANDIDATE, Permission.DELETE_CANDIDATE,
            Permission.CONTACT_CANDIDATE,
            # 面试权限
            Permission.READ_INTERVIEW, Permission.WRITE_INTERVIEW, Permission.DELETE_INTERVIEW,
            Permission.SCHEDULE_INTERVIEW,
            # 统计权限
            Permission.READ_ANALYTICS, Permission.READ_DASHBOARD,
            # 管理权限
            Permission.MANAGE_USERS, Permission.MANAGE_TENANT,
        },
        description="租户管理员，拥有租户内的所有权限"
    ),

    Role.HR_MANAGER: RolePermission(
        role=Role.HR_MANAGER,
        permissions={
            # 简历权限
            Permission.READ_ALL_RESUMES, Permission.WRITE_RESUME, Permission.EXPORT_RESUMES,
            # 职位权限
            Permission.READ_JOB, Permission.WRITE_JOB, Permission.PUBLISH_JOB,
            # 候选人权限
            Permission.READ_CANDIDATE, Permission.WRITE_CANDIDATE, Permission.CONTACT_CANDIDATE,
            # 面试权限
            Permission.READ_INTERVIEW, Permission.WRITE_INTERVIEW, Permission.SCHEDULE_INTERVIEW,
            # 统计权限
            Permission.READ_ANALYTICS, Permission.READ_DASHBOARD,
        },
        description="HR经理，负责招聘策略和团队管理"
    ),

    Role.HR_SPECIALIST: RolePermission(
        role=Role.HR_SPECIALIST,
        permissions={
            # 简历权限
            Permission.READ_RESUME, Permission.WRITE_RESUME,
            # 职位权限
            Permission.READ_JOB, Permission.WRITE_JOB,
            # 候选人权限
            Permission.READ_CANDIDATE, Permission.WRITE_CANDIDATE,
            # 面试权限
            Permission.READ_INTERVIEW, Permission.WRITE_INTERVIEW,
        },
        description="HR专员，负责日常招聘工作"
    ),

    Role.RECRUITER: RolePermission(
        role=Role.RECRUITER,
        permissions={
            # 简历权限
            Permission.READ_RESUME,
            # 职位权限
            Permission.READ_JOB,
            # 候选人权限
            Permission.READ_CANDIDATE, Permission.CONTACT_CANDIDATE,
            # 面试权限
            Permission.READ_INTERVIEW, Permission.SCHEDULE_INTERVIEW,
        },
        description="招聘专员，负责候选人沟通和面试安排"
    ),

    Role.INTERVIEWER: RolePermission(
        role=Role.INTERVIEWER,
        permissions={
            # 简历权限
            Permission.READ_RESUME,
            # 面试权限
            Permission.READ_INTERVIEW, Permission.WRITE_INTERVIEW,
        },
        description="面试官，只能查看候选人简历和填写面试反馈"
    ),

    Role.SYSTEM_ADMIN: RolePermission(
        role=Role.SYSTEM_ADMIN,
        permissions={
            # 系统管理员拥有所有权限
            Permission.SYSTEM_ADMIN,
        },
        description="系统管理员，拥有系统级别的所有权限"
    ),

    Role.SUPPORT: RolePermission(
        role=Role.SUPPORT,
        permissions={
            # 技术支持权限，主要用于问题排查
            Permission.READ_RESUME, Permission.READ_JOB, Permission.READ_CANDIDATE,
            Permission.READ_INTERVIEW, Permission.READ_ANALYTICS,
        },
        description="技术支持，只读权限用于问题排查"
    ),
}


class PermissionChecker:
    """权限检查器"""

    def __init__(self):
        self.logger = logger.bind(component="PermissionChecker")

    def has_permission(
        self,
        user_roles: List[Role],
        required_permission: Permission,
        resource_tenant_id: Optional[UUID] = None,
        user_tenant_id: Optional[UUID] = None,
        resource_owner_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None
    ) -> bool:
        """
        检查用户是否具有特定权限

        Args:
            user_roles: 用户角色列表
            required_permission: 需要的权限
            resource_tenant_id: 资源所属租户ID
            user_tenant_id: 用户所属租户ID
            resource_owner_id: 资源所有者ID
            user_id: 用户ID

        Returns:
            是否有权限
        """
        try:
            # 1. 检查租户权限
            if resource_tenant_id and user_tenant_id:
                if resource_tenant_id != user_tenant_id:
                    self.logger.warning(
                        "Tenant access denied",
                        user_tenant_id=str(user_tenant_id),
                        resource_tenant_id=str(resource_tenant_id)
                    )
                    return False

            # 2. 系统管理员跳过权限检查
            if Role.SYSTEM_ADMIN in user_roles:
                return True

            # 3. 检查资源所有者权限（某些情况下用户可以访问自己的资源）
            if resource_owner_id and user_id:
                if resource_owner_id == user_id:
                    # 用户可以访问自己的资源（需要进一步细化权限规则）
                    owner_permissions = {
                        Permission.READ_RESUME, Permission.WRITE_RESUME,
                        Permission.READ_CANDIDATE, Permission.WRITE_CANDIDATE,
                    }
                    if required_permission in owner_permissions:
                        return True

            # 4. 检查角色权限
            for role in user_roles:
                role_permission = ROLE_PERMISSIONS.get(role)
                if role_permission and required_permission in role_permission.permissions:
                    return True

            self.logger.warning(
                "Permission denied",
                user_roles=[r.value for r in user_roles],
                required_permission=required_permission.value,
                user_id=str(user_id) if user_id else None
            )
            return False

        except Exception as e:
            self.logger.error(
                "Error checking permission",
                error=str(e),
                required_permission=required_permission.value
            )
            return False

    def get_user_permissions(self, user_roles: List[Role]) -> Set[Permission]:
        """获取用户的所有权限"""
        permissions = set()
        for role in user_roles:
            role_permission = ROLE_PERMISSIONS.get(role)
            if role_permission:
                permissions.update(role_permission.permissions)
        return permissions

    def can_access_resource(
        self,
        user_roles: List[Role],
        resource_type: str,
        action: str,
        resource_tenant_id: Optional[UUID] = None,
        user_tenant_id: Optional[UUID] = None,
        **kwargs
    ) -> bool:
        """
        检查是否可以访问特定资源

        Args:
            user_roles: 用户角色
            resource_type: 资源类型 (resume, job, candidate, interview)
            action: 操作类型 (read, write, delete, publish, contact, etc.)
            resource_tenant_id: 资源租户ID
            user_tenant_id: 用户租户ID
            **kwargs: 其他参数

        Returns:
            是否可以访问
        """
        # 构建权限字符串
        permission_str = f"{action}:{resource_type}"

        try:
            required_permission = Permission(permission_str)
        except ValueError:
            self.logger.error(
                "Invalid permission",
                permission_str=permission_str
            )
            return False

        return self.has_permission(
            user_roles=user_roles,
            required_permission=required_permission,
            resource_tenant_id=resource_tenant_id,
            user_tenant_id=user_tenant_id,
            **kwargs
        )


# 全局权限检查器实例
permission_checker = PermissionChecker()


def require_permission(permission: Permission):
    """
    权限装饰器

    用法：
    @require_permission(Permission.READ_RESUME)
    async def get_resume(resume_id: UUID, current_user: User = Depends(get_current_user)):
        pass
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 从kwargs中获取用户信息
            current_user = kwargs.get('current_user')
            if not current_user:
                raise PermissionError("Authentication required")

            # 获取资源ID（如果存在）
            resource_id = kwargs.get('resume_id') or kwargs.get('job_id') or kwargs.get('candidate_id')

            # 检查权限
            has_permission = permission_checker.has_permission(
                user_roles=current_user.roles,
                required_permission=permission,
                resource_tenant_id=getattr(kwargs.get('resource'), 'tenant_id', None) if 'resource' in kwargs else None,
                user_tenant_id=current_user.tenant_id,
                resource_owner_id=getattr(kwargs.get('resource'), 'user_id', None) if 'resource' in kwargs else None,
                user_id=current_user.id,
                resource_id=resource_id
            )

            if not has_permission:
                raise PermissionError(f"Permission denied: {permission.value}")

            return await func(*args, **kwargs)
        return wrapper
    return decorator


class ResourceOwnerChecker:
    """资源所有者检查器"""

    @staticmethod
    def is_resource_owner(user_id: UUID, resource) -> bool:
        """检查用户是否是资源所有者"""
        if not resource:
            return False

        # 检查不同的所有权字段
        owner_fields = ['user_id', 'created_by', 'owner_id']
        for field in owner_fields:
            if hasattr(resource, field):
                if getattr(resource, field) == user_id:
                    return True

        return False

    @staticmethod
    def can_access_resource(
        user_id: UUID,
        user_roles: List[Role],
        resource,
        required_permission: Permission
    ) -> bool:
        """检查用户是否可以访问资源"""
        # 1. 系统管理员可以访问所有资源
        if Role.SYSTEM_ADMIN in user_roles:
            return True

        # 2. 资源所有者可以访问自己的资源（限制权限）
        if ResourceOwnerChecker.is_resource_owner(user_id, resource):
            # 定义所有者可以访问的权限
            owner_permissions = {
                Permission.READ_RESUME, Permission.WRITE_RESUME,
                Permission.READ_CANDIDATE, Permission.WRITE_CANDIDATE,
                Permission.READ_JOB, Permission.WRITE_JOB,
            }
            return required_permission in owner_permissions

        # 3. 检查角色权限
        return permission_checker.has_permission(
            user_roles=user_roles,
            required_permission=required_permission,
            resource_tenant_id=getattr(resource, 'tenant_id', None),
            resource_owner_id=user_id,
            user_id=user_id
        )