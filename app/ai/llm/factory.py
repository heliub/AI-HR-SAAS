"""
LLM工厂函数

根据provider名称创建对应的LLM客户端
"""
from typing import Optional, Dict
import os
import threading
from app.core.config import settings
from .base import BaseLLMClient, BaseEmbeddingClient
from .providers import OpenAIClient, VolcengineClient
from .providers.volcengine_embedding import VolcengineEmbeddingClient
from .errors import LLMValidationError


# provider名称到客户端类的映射
PROVIDER_REGISTRY = {
    "openai": OpenAIClient,
    "volcengine": VolcengineClient,
}

# embedding provider名称到客户端类的映射
EMBEDDING_PROVIDER_REGISTRY = {
    "volcengine": VolcengineEmbeddingClient,
}

# 全局缓存字典，用于存储已创建的客户端实例
_LLM_CLIENT_CACHE: Dict[str, BaseLLMClient] = {}

# 全局缓存字典，用于存储已创建的embedding客户端实例
_EMBEDDING_CLIENT_CACHE: Dict[str, BaseEmbeddingClient] = {}

# 线程锁，确保缓存的线程安全
_CACHE_LOCK = threading.Lock()
_EMBEDDING_CACHE_LOCK = threading.Lock()


def get_llm(
    provider: str,
    base_url: Optional[str] = None,
    timeout: float = 60.0,
    max_retries: int = 3,
) -> BaseLLMClient:
    """
    获取LLM客户端

    Args:
        provider: provider名称（openai, volcengine等）
        base_url: API base URL（可选，未传则从settings读取）
        timeout: 请求超时时间（秒）
        max_retries: 最大重试次数

    Returns:
        LLM客户端实例

    Raises:
        LLMValidationError: provider不支持或配置缺失

    Examples:
        >>> # 从配置读取
        >>> llm = get_llm(provider="openai")

        >>> # 显式传参
        >>> llm = get_llm(
        ...     provider="openai",
        ...     base_url="https://api.openai.com/v1"
        ... )
    """
    # 检查provider是否支持
    if provider not in PROVIDER_REGISTRY:
        supported = ", ".join(PROVIDER_REGISTRY.keys())
        raise LLMValidationError(
            f"不支持的provider: {provider}，支持的provider: {supported}",
            field="provider",
        )

    # 如果没有显式传参，从settings读取
    if base_url is None:
        provider_config = _get_provider_config(provider)
        if base_url is None:
            base_url = provider_config.get("base_url")

    api_key = os.getenv(f"{provider.upper()}_API_KEY")
    # 验证api_key
    if not api_key:
        raise LLMValidationError(
            f"provider '{provider}' 缺少api_key，请在配置中设置或显式传参",
            field="api_key",
        )

    # 生成缓存键，包含所有影响客户端行为的参数
    cache_key = f"{provider}"  # 只使用API key后8位确保安全

    # 先检查缓存，如果命中则直接返回（无需加锁）
    if cache_key in _LLM_CLIENT_CACHE:
        return _LLM_CLIENT_CACHE[cache_key]

    # 缓存未命中，需要创建新实例，此时加锁
    with _CACHE_LOCK:
        # 双重检查：在获取锁后再次检查缓存，防止其他线程已经创建了实例
        if cache_key in _LLM_CLIENT_CACHE:
            return _LLM_CLIENT_CACHE[cache_key]

        # 创建新客户端实例
        client_class = PROVIDER_REGISTRY[provider]
        client = client_class(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )

        # 缓存客户端实例
        _LLM_CLIENT_CACHE[cache_key] = client
        return client


def get_embedding(
    provider: str,
    base_url: Optional[str] = None,
    timeout: float = 60.0,
    max_retries: int = 3,
) -> BaseEmbeddingClient:
    """
    获取Embedding客户端

    Args:
        provider: provider名称（volcengine等）
        base_url: API base URL（可选，未传则从settings读取）
        timeout: 请求超时时间（秒）
        max_retries: 最大重试次数

    Returns:
        Embedding客户端实例

    Raises:
        LLMValidationError: provider不支持或配置缺失

    Examples:
        >>> # 从配置读取
        >>> embedding = get_embedding(provider="volcengine")

        >>> # 显式传参
        >>> embedding = get_embedding(
        ...     provider="volcengine",
        ...     base_url="https://ark.cn-beijing.volces.com/api/v3"
        ... )
    """
    # 检查provider是否支持
    if provider not in EMBEDDING_PROVIDER_REGISTRY:
        supported = ", ".join(EMBEDDING_PROVIDER_REGISTRY.keys())
        raise LLMValidationError(
            f"不支持的embedding provider: {provider}，支持的provider: {supported}",
            field="provider",
        )

    # 如果没有显式传参，从settings读取
    if base_url is None:
        provider_config = _get_embedding_provider_config(provider)
        if base_url is None:
            base_url = provider_config.get("base_url")

    api_key = os.getenv(f"{provider.upper()}_API_KEY")
    # 验证api_key
    if not api_key:
        raise LLMValidationError(
            f"embedding provider '{provider}' 缺少api_key，请在配置中设置或显式传参",
            field="api_key",
        )

    # 生成缓存键，包含所有影响客户端行为的参数
    cache_key = f"{provider}"  # 只使用API key后8位确保安全

    # 先检查缓存，如果命中则直接返回（无需加锁）
    if cache_key in _EMBEDDING_CLIENT_CACHE:
        return _EMBEDDING_CLIENT_CACHE[cache_key]

    # 缓存未命中，需要创建新实例，此时加锁
    with _EMBEDDING_CACHE_LOCK:
        # 双重检查：在获取锁后再次检查缓存，防止其他线程已经创建了实例
        if cache_key in _EMBEDDING_CLIENT_CACHE:
            return _EMBEDDING_CLIENT_CACHE[cache_key]

        # 创建新客户端实例
        client_class = EMBEDDING_PROVIDER_REGISTRY[provider]
        client = client_class(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )

        # 缓存客户端实例
        _EMBEDDING_CLIENT_CACHE[cache_key] = client
        return client


def clear_cache(provider: Optional[str] = None) -> None:
    """
    清除客户端缓存

    Args:
        provider: 要清除的provider名称，如果为None则清除所有缓存
    """
    with _CACHE_LOCK:
        if provider is None:
            _CLIENT_CACHE.clear()
        else:
            # 清除特定provider的缓存
            keys_to_remove = [k for k in _CLIENT_CACHE.keys() if k.startswith(f"{provider}:")]
            for key in keys_to_remove:
                del _CLIENT_CACHE[key]


def clear_embedding_cache(provider: Optional[str] = None) -> None:
    """
    清除Embedding客户端缓存

    Args:
        provider: 要清除的provider名称，如果为None则清除所有缓存
    """
    with _EMBEDDING_CACHE_LOCK:
        if provider is None:
            _EMBEDDING_CLIENT_CACHE.clear()
        else:
            # 清除特定provider的缓存
            keys_to_remove = [k for k in _EMBEDDING_CLIENT_CACHE.keys() if k.startswith(f"{provider}:")]
            for key in keys_to_remove:
                del _EMBEDDING_CLIENT_CACHE[key]


def get_cache_info() -> Dict[str, int]:
    """
    获取缓存信息

    Returns:
        包含各provider缓存数量的字典
    """
    with _CACHE_LOCK:
        cache_info = {}
        for key in _CLIENT_CACHE.keys():
            provider = key.split(":")[0]
            cache_info[provider] = cache_info.get(provider, 0) + 1
        return cache_info


def get_embedding_cache_info() -> Dict[str, int]:
    """
    获取Embedding缓存信息

    Returns:
        包含各provider缓存数量的字典
    """
    with _EMBEDDING_CACHE_LOCK:
        cache_info = {}
        for key in _EMBEDDING_CLIENT_CACHE.keys():
            provider = key.split(":")[0]
            cache_info[provider] = cache_info.get(provider, 0) + 1
        return cache_info


def _get_provider_config(provider: str) -> dict:
    """
    从settings获取provider配置

    Args:
        provider: provider名称

    Returns:
        配置字典

    Raises:
        LLMValidationError: 配置不存在
    """
    for provider_config in settings.AI_PROVIDERS:
        if provider_config.get("provider") == provider:
            return provider_config

    raise LLMValidationError(
        f"未在配置中找到provider '{provider}'，请在settings.AI_PROVIDERS中添加配置",
        field="provider",
    )


def _get_embedding_provider_config(provider: str) -> dict:
    """
    从settings获取embedding provider配置

    Args:
        provider: provider名称

    Returns:
        配置字典

    Raises:
        LLMValidationError: 配置不存在
    """
    for provider_config in settings.EMBEDDING_PROVIDERS:
        if provider_config.get("provider") == provider:
            return provider_config

    raise LLMValidationError(
        f"未在配置中找到embedding provider '{provider}'，请在settings.EMBEDDING_PROVIDERS中添加配置",
        field="provider",
    )
