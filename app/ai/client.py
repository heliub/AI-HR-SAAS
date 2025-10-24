"""
AI client implementations
"""
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel

from app.ai.base import BaseAIClient
from app.core.config import settings
from app.core.exceptions import AIServiceException


class OpenAIClient(BaseAIClient):
    """OpenAI客户端实现"""
    
    def __init__(self, api_key: str = None, model: str = None, **kwargs):
        self.client = ChatOpenAI(
            api_key=api_key or settings.AI_API_KEY,
            model=model or settings.AI_MODEL,
            temperature=kwargs.get('temperature', settings.AI_TEMPERATURE),
            max_tokens=kwargs.get('max_tokens', settings.AI_MAX_TOKENS),
        )
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """对话补全"""
        try:
            lc_messages = self._convert_messages(messages)
            response = await self.client.ainvoke(lc_messages)
            return response.content
        except Exception as e:
            raise AIServiceException(f"OpenAI API call failed: {str(e)}")
    
    async def structured_output(
        self,
        messages: List[Dict[str, str]],
        response_model: Any,
        **kwargs
    ) -> Any:
        """结构化输出"""
        try:
            # 添加JSON格式指令
            system_message = {
                "role": "system",
                "content": f"You must respond with valid JSON matching this schema: {response_model.schema_json()}"
            }
            messages_with_instruction = [system_message] + messages
            
            lc_messages = self._convert_messages(messages_with_instruction)
            
            # 使用JSON输出解析器
            parser = JsonOutputParser(pydantic_object=response_model)
            chain = self.client | parser
            
            result = await chain.ainvoke(lc_messages)
            return response_model(**result)
        except Exception as e:
            raise AIServiceException(f"Structured output failed: {str(e)}")
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> List:
        """转换消息格式"""
        lc_messages = []
        for msg in messages:
            if msg['role'] == 'user':
                lc_messages.append(HumanMessage(content=msg['content']))
            elif msg['role'] == 'assistant':
                lc_messages.append(AIMessage(content=msg['content']))
            elif msg['role'] == 'system':
                lc_messages.append(SystemMessage(content=msg['content']))
        return lc_messages


class AIClientFactory:
    """AI客户端工厂"""
    
    @staticmethod
    def create_client(provider: str = None, **kwargs) -> BaseAIClient:
        """
        创建AI客户端
        
        Args:
            provider: 提供商（openai, anthropic等）
            **kwargs: 额外参数
        
        Returns:
            AI客户端实例
        """
        provider = provider or settings.AI_PROVIDER
        
        if provider == "openai":
            return OpenAIClient(**kwargs)
        elif provider == "anthropic":
            # TODO: 实现Anthropic客户端
            raise NotImplementedError("Anthropic client not implemented yet")
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")


def get_ai_client(**kwargs) -> BaseAIClient:
    """获取AI客户端实例"""
    return AIClientFactory.create_client(**kwargs)

