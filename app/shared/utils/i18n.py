"""
Internationalization utilities
"""
from typing import Dict, Optional

from app.core.config import settings


# 静态语言映射表
MESSAGES = {
    "en": {
        "welcome": "Welcome",
        "login_success": "Login successful",
        "login_failed": "Login failed",
        "not_found": "Resource not found",
        "unauthorized": "Unauthorized access",
        "forbidden": "Access forbidden",
        "internal_error": "Internal server error",
    },
    "zh": {
        "welcome": "欢迎",
        "login_success": "登录成功",
        "login_failed": "登录失败",
        "not_found": "资源不存在",
        "unauthorized": "未授权访问",
        "forbidden": "禁止访问",
        "internal_error": "内部服务器错误",
    },
    "id": {
        "welcome": "Selamat datang",
        "login_success": "Login berhasil",
        "login_failed": "Login gagal",
        "not_found": "Sumber tidak ditemukan",
        "unauthorized": "Akses tidak sah",
        "forbidden": "Akses dilarang",
        "internal_error": "Kesalahan server internal",
    },
}


class I18n:
    """国际化管理器"""
    
    def __init__(self, default_language: str = None):
        self.default_language = default_language or settings.DEFAULT_LANGUAGE
        self.messages = MESSAGES
    
    def get_message(self, key: str, language: Optional[str] = None) -> str:
        """
        获取翻译消息
        
        Args:
            key: 消息键
            language: 语言代码（如果为None，使用默认语言）
        
        Returns:
            翻译后的消息，如果找不到则返回key
        """
        lang = language or self.default_language
        
        # 确保语言代码有效
        if lang not in self.messages:
            lang = self.default_language
        
        return self.messages.get(lang, {}).get(key, key)
    
    def translate(self, key: str, language: str, **kwargs) -> str:
        """
        翻译并格式化消息
        
        Args:
            key: 消息键
            language: 语言代码
            **kwargs: 格式化参数
        
        Returns:
            翻译并格式化后的消息
        """
        message = self.get_message(key, language)
        if kwargs:
            try:
                message = message.format(**kwargs)
            except KeyError:
                pass
        return message


# 全局I18n实例
i18n = I18n()


def get_message(key: str, language: Optional[str] = None) -> str:
    """获取翻译消息的便捷函数"""
    return i18n.get_message(key, language)

