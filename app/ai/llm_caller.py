"""
LLM调用封装

提供CLG1通用执行逻辑的封装
"""
import json
import os
from typing import Dict, Any, Optional, Union
import structlog

from app.ai.llm.factory import get_llm
from app.ai.llm.types import LLMRequest, UserMessage
from app.ai.llm.errors import LLMError
from app.ai.prompts.prompt_loader import get_prompt_loader
from app.ai.prompts.variable_substitution import substitute_variables
from app.ai.prompts.prompt_config import PROMPT_CONFIG

logger = structlog.get_logger(__name__)


class LLMCaller:
    """LLM调用器"""

    def __init__(
        self,
        provider: str = "volcengine",
        default_model: str = "doubao-1.5-pro-32k-250115",
        default_temperature: float = 0.1,
        default_max_completion_tokens: int = 2000
    ):
        """
        初始化LLM调用器

        Args:
            provider: LLM provider名称
            default_model: 默认模型
            default_temperature: 默认温度参数
            default_max_completion_tokens: 默认最大token数
        """
        self.provider = provider
        self.default_model = default_model
        self.default_temperature = default_temperature
        self.default_max_completion_tokens = default_max_completion_tokens
        self.prompt_loader = get_prompt_loader()
        self.llm_client = get_llm(provider=provider)

        logger.info(
            "llm_caller_initialized",
            provider=provider,
            model=default_model
        )

    async def call_with_scene(
        self,
        scene_name: str,
        template_vars: Dict[str, Any],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_completion_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        parse_json: bool = True
    ) -> Union[Dict[str, Any], str]:
        """
        基于场景名称调用LLM（CLG1通用逻辑）

        自动从prompt_config.py读取场景配置（model, temperature等）

        Args:
            scene_name: 场景名称（对应Prompt模板文件名）
            template_vars: 模板变量字典
            system_prompt: 系统提示词（可选，优先级高于配置）
            model: 模型名称（可选，优先级高于配置）
            temperature: 温度参数（可选，优先级高于配置）
            max_completion_tokens: 最大token数（可选，优先级高于配置）
            top_p: top_p参数（可选，优先级高于配置）
            parse_json: 是否解析JSON响应（默认True）

        Returns:
            LLM响应结果（parse_json=True时为字典，parse_json=False时为原始字符串）
            类型为Union[Dict[str, Any], str]

        Raises:
            LLMError: LLM调用失败
            json.JSONDecodeError: JSON解析失败
        """
        # 1. 读取场景配置
        scene_config = PROMPT_CONFIG.get(scene_name, {})

        # 2. 合并参数（显式传参 > 场景配置 > 默认值）
        final_model = model or scene_config.get("model") or self.default_model
        final_temperature = temperature if temperature is not None else scene_config.get("temperature", self.default_temperature)
        final_max_completion_tokens = max_completion_tokens or scene_config.get("max_completion_tokens") or self.default_max_completion_tokens
        final_top_p = top_p if top_p is not None else scene_config.get("top_p")
        final_system = system_prompt or scene_config.get("system")
        final_json_output = parse_json or scene_config.get("json_output")   
        
        try:
            prompt = self.prompt_loader.load_prompt(
                scene_name=scene_name,
                template_vars=template_vars
            )
        except FileNotFoundError as e:
            logger.error(
                "prompt_template_not_found",
                scene_name=scene_name,
                error=str(e)
            )
            raise

        # 5. 调用LLM
        return await self.call_with_prompt(
            prompt=prompt,
            system_prompt=final_system,
            model=final_model,
            temperature=final_temperature,
            max_completion_tokens=final_max_completion_tokens,
            top_p=final_top_p,
            parse_json=final_json_output,
            scene_name=scene_name
        )

    async def call_with_prompt(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_completion_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        parse_json: bool = True,
        scene_name: Optional[str] = None
    ) -> Union[Dict[str, Any], str]:
        """
        直接使用Prompt调用LLM

        Args:
            prompt: Prompt内容
            system_prompt: 系统提示词
            model: 模型名称
            temperature: 温度参数
            max_completion_tokens: 最大token数
            top_p: top_p参数
            parse_json: 是否解析JSON响应
            scene_name: 场景名称（用于日志记录）

        Returns:
            LLM响应结果（parse_json=True时为字典，parse_json=False时为原始字符串，JSON解析失败时为原始字符串）
            类型为Union[Dict[str, Any], str]
        """
        # 使用默认值
        model = model or self.default_model
        temperature = temperature if temperature is not None else self.default_temperature
        max_completion_tokens = max_completion_tokens or self.default_max_completion_tokens

        # 构建请求
        request = LLMRequest(
            model=model,
            messages=[UserMessage(content=prompt)],
            system=system_prompt,
            temperature=temperature,
            max_completion_tokens=max_completion_tokens,
            top_p=top_p
        )

        logger.info(
            "llm_call_started",
            scene_name=scene_name,
            model=model,
            prompt_length=len(prompt)
        )

        try:
            # 调用LLM
            response = await self.llm_client.chat(request)

            content = response.content or ""

            logger.info(
                "llm_call_completed",
                scene_name=scene_name,
                model=model,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                response_length=len(content)
            )

            # 解析JSON
            if parse_json:
                try:
                    return self._parse_json_response(content)
                except LLMError as e:
                    logger.warning(
                        "json_parse_failed_returning_raw_content",
                        scene_name=scene_name,
                        model=model,
                        error=str(e)
                    )
                    # JSON解析失败时返回原始内容，以便上游进行针对性处理
                    return content
            else:
                # 直接返回原始响应内容，而不是封装成{"content": content}结构
                return content

        except LLMError as e:
            logger.error(
                "llm_call_failed",
                scene_name=scene_name,
                model=model,
                error=str(e)
            )
            raise

    def _parse_json_response(
        self,
        content: str
    ) -> Dict[str, Any]:
        """
        解析JSON响应

        Args:
            content: LLM响应内容

        Returns:
            解析后的字典

        Raises:
            LLMError: JSON解析失败（包装JSONDecodeError，触发重试）
        """
        # 移除markdown代码块标记
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        try:
            result = json.loads(content)
            return result

        except json.JSONDecodeError as e:
            # 包装成LLMError，触发重试机制
            raise LLMError(f"JSON解析失败: {str(e)}，原始内容: {content[:100]}...")


# 全局单例
_default_llm_caller: Optional[LLMCaller] = None


def get_llm_caller(
    provider: str = "volcengine",
    model: Optional[str] = None
) -> LLMCaller:
    """
    获取LLM调用器单例

    Args:
        provider: LLM provider名称
        model: 默认模型名称

    Returns:
        LLMCaller实例
    """
    global _default_llm_caller

    if _default_llm_caller is None:
        kwargs = {"provider": provider}
        if model:
            kwargs["default_model"] = model

        _default_llm_caller = LLMCaller(**kwargs)

    return _default_llm_caller
