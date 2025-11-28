"""
翻译服务
提供基于AI的内容翻译功能
"""
from typing import Optional
from uuid import UUID
from app.services.user_service import UserService
from app.ai.llm_caller import get_llm_caller
import structlog
import re

logger = structlog.get_logger(__name__)


class TranslationService():
    """翻译服务类"""

    def __init__(self):
        self.user_service = UserService()
        self.llm_caller = get_llm_caller()

    # 语言代码到语言名称的映射
    LANGUAGE_MAPPING = {
        "en": "English",
        "zh": "Chinese",
        "id": "Indonesian",
        "ja": "Japanese",
        "ko": "Korean",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "ru": "Russian",
        "ar": "Arabic",
        "pt": "Portuguese",
        "it": "Italian",
        "th": "Thai",
        "vi": "Vietnamese"
    }

    async def translate_content(
        self,
        content: str,
        user_id: Optional[UUID] = None
    ) -> str:
        """
        翻译内容

        Args:
            content: 需要翻译的内容
            user_id: 用户ID（用于获取用户语言设置）

        Returns:
            翻译后的内容
        """
        if not content or not content.strip():
            return content

        user_settings = await self.user_service.get_user_settings(user_id)
        if not user_settings or not user_settings.get("language"):
            return content
        target_language = user_settings.get("language")
        # 如果仍然没有目标语言，使用默认中文
        if not target_language:
            return content

        if self.textIsTargetLanguage(content, target_language):
            return content

        # 获取目标语言名称
        target_language_name = self.LANGUAGE_MAPPING.get(target_language)
        if not target_language_name:
            return content

        # 准备模板变量
        template_vars = {
            "source_text": content,
            "target_language": target_language_name
        }

        try:
            # 调用LLM进行翻译
            result = await self.llm_caller.call_with_scene(
                scene_name="text_translate",
                template_vars=template_vars
            )
            
            # 确保返回的是字符串
            if isinstance(result, dict):
                # 如果返回的是字典，尝试获取内容
                return result.get("translated_text", str(result))
            return content
        except Exception as e:
            logger.error(
                "translation_failed",
                content=content[:100],  # 只记录前100个字符
                target_language=target_language,
                error=str(e)
            )
            # 翻译失败时返回原文
            return content

    def textIsTargetLanguage(self, text: str, target_language: str) -> bool:
        """
        判断文本是否为目标语言
        """
        try:
            if target_language == "zh":
                return len(re.findall(r'[\u4e00-\u9fff]', text)) / len(text) > 0.5
            return False
        except Exception as e:
            logger.error(
                "textIsTargetLanguage_failed",
                target_language=target_language,
                error=str(e)
            )
            return False