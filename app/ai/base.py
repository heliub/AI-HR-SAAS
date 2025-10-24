"""
AI client base interface
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseAIClient(ABC):
    """AI客户端抽象基类"""
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """
        对话补全
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            **kwargs: 额外参数（temperature, max_tokens等）
        
        Returns:
            AI响应内容
        """
        pass
    
    @abstractmethod
    async def structured_output(
        self,
        messages: List[Dict[str, str]],
        response_model: Any,
        **kwargs
    ) -> Any:
        """
        结构化输出
        
        Args:
            messages: 消息列表
            response_model: Pydantic模型
            **kwargs: 额外参数
        
        Returns:
            结构化响应对象
        """
        pass

