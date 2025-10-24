"""
Validation utilities
"""
import re
from typing import Optional


def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    """验证电话号码格式（支持多种格式）"""
    # 去除常见分隔符
    phone = re.sub(r'[\s\-\(\)]', '', phone)
    # 检查是否为10-15位数字，可选+前缀
    pattern = r'^\+?[0-9]{10,15}$'
    return re.match(pattern, phone) is not None


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    验证密码强度
    
    要求：
    - 至少8个字符
    - 至少一个大写字母
    - 至少一个小写字母
    - 至少一个数字
    
    Returns:
        (是否有效, 错误信息)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one digit"
    
    return True, None


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除非法字符"""
    # 移除路径分隔符和其他危险字符
    filename = re.sub(r'[/\\:*?"<>|]', '', filename)
    # 限制长度
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    return filename

