"""
Volcengine (火山引擎) Provider

火山引擎兼容OpenAI格式，直接继承OpenAIClient
"""
from .openai import OpenAIClient


class VolcengineClient(OpenAIClient):
    """火山引擎客户端"""

    @property
    def provider_name(self) -> str:
        return "volcengine"
