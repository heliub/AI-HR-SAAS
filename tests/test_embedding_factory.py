#!/usr/bin/env python3
"""
测试 embedding 工厂函数
"""
import asyncio
import os
from app.ai.llm.factory import get_embedding, get_embedding_cache_info, clear_embedding_cache
from app.ai.llm.types import EmbeddingRequest


async def test_embedding_factory():
    """测试 embedding 工厂函数"""
    # 设置环境变量（在实际应用中应该从 .env 文件加载）
    
    
    try:
        # 获取 embedding 客户端
        print("获取 embedding 客户端...")
        embedding_client = get_embedding(provider="volcengine")
        print(f"成功获取客户端: {embedding_client.provider_name}")
        
        # 测试缓存
        print("\n测试缓存...")
        cache_info = get_embedding_cache_info()
        print(f"缓存信息: {cache_info}")
        
        # 再次获取相同 provider，应该从缓存返回
        print("\n再次获取相同 provider...")
        embedding_client2 = get_embedding(provider="volcengine")
        print(f"两个客户端是同一个实例: {embedding_client is embedding_client2}")
        
        # 测试创建 embedding
        print("\n测试创建 embedding...")
        request = EmbeddingRequest(
            model="doubao-embedding-text-240715",
            input="Hello, world!",
        )
        response = await embedding_client.create_embedding(request)
        print(response)
        print(f"Embedding 创建成功，向量维度: {len(response.data[0].embedding)}")
        
        # 清除缓存
        print("\n清除缓存...")
        clear_embedding_cache()
        cache_info = get_embedding_cache_info()
        print(f"清除后的缓存信息: {cache_info}")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_embedding_factory())
