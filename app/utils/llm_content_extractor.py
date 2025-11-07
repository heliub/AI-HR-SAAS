"""
基于大模型的文件内容提取工具类

支持PDF和图片文件的纯文本内容提取，使用LLM进行智能解析
专注于内容提取，不进行结果解析
支持Base64文件数据输入
调用方只需传入文件数据，无需关心模型和提示词细节
"""

import base64
import gc
import os
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import logging

from app.ai.llm import (
    get_llm,
    LLMRequest,
    UserMessage,
    SystemMessage,
    TextContent,
    ImageUrlContent,
    ImageUrl,
    FileContent,
    FileData,
    LLMError,
)

# 配置日志
logger = logging.getLogger(__name__)


class LLMContentExtractor:
    """
    基于大模型的文件内容提取工具类
    
    专注于从PDF和图片文件中提取纯文本内容，不进行结果解析
    支持Base64文件数据输入
    调用方只需传入文件数据，无需关心模型和提示词细节
    """
    
    # 支持的文件类型
    SUPPORTED_IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    SUPPORTED_DOCUMENT_TYPES = {".pdf", ".doc", ".docx"}
    SUPPORTED_TYPES = SUPPORTED_IMAGE_TYPES.union(SUPPORTED_DOCUMENT_TYPES)
    
    # MIME类型映射
    MIME_TYPES = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".pdf": "application/pdf",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    
    def __init__(self, provider: str = "volcengine"):
        """
        初始化LLM内容提取器
        
        Args:
            provider: LLM提供商，支持 "openai" 或 "volcengine"
        """
        self.provider = provider
        self._llm = None
        
        # 根据提供商设置默认模型和参数
        if provider == "openai":
            self.model = "gpt-4o"
            self.temperature = 0.1
            self.max_tokens = 10000
        else:  # volcengine
            self.model = "doubao-seed-1-6-vision-250815"
            self.temperature = 0.1
            self.max_tokens = 10000
        
        # 设置默认提示词
        self.default_prompt = "Only extract all text content from files. Do not rephrase, summarize, or rewrite any content. Do not file title if multiple files are provided."
    
    @property
    def llm(self):
        """获取LLM客户端（懒加载）"""
        if self._llm is None:
            self._llm = get_llm(provider=self.provider, timeout=180.0)
        return self._llm
    
    @staticmethod
    def get_file_mime_type(file_extension: str) -> str:
        """根据文件扩展名获取MIME类型"""
        ext = file_extension.lower()
        return LLMContentExtractor.MIME_TYPES.get(ext, "application/octet-stream")
    
    @staticmethod
    def validate_file_data(file_data: str, file_extension: str) -> Tuple[bool, str]:
        """
        验证文件数据是否有效
        
        Args:
            file_data: Base64编码的文件数据
            file_extension: 文件扩展名
            
        Returns:
            (是否有效, 错误信息)
        """
        if not file_data:
            return False, "文件数据为空"
        
        if not file_extension:
            return False, "文件扩展名为空"
        
        ext = file_extension.lower()
        if ext not in LLMContentExtractor.SUPPORTED_TYPES:
            return False, f"不支持的文件类型: {ext}"
        
        try:
            # 尝试解码Base64数据以验证其有效性
            base64.b64decode(file_data)
            return True, ""
        except Exception as e:
            return False, f"无效的Base64数据: {str(e)}"
    
    async def extract_text_from_base64(
        self, 
        file_data_list: List[Dict[str, str]]
    ) -> str:
        """
        从Base64编码的文件数据中提取纯文本内容
        
        Args:
            file_data_list: 文件数据列表，每个元素包含file_data、file_extension和filename(可选)
            
        Returns:
            提取的纯文本内容
            
        Raises:
            ValueError: 文件数据无效或不支持的文件格式
            LLMError: LLM调用失败
        """
        # 验证所有文件数据
        for item in file_data_list:
            file_data = item.get("file_data")
            file_extension = item.get("file_extension")
            
            is_valid, error_msg = self.validate_file_data(file_data, file_extension)
            if not is_valid:
                raise ValueError(f"无效文件数据: {error_msg}")
        
        # 构建消息内容
        content_parts = []
        
        for item in file_data_list:
            file_data = item["file_data"]
            file_extension = item["file_extension"]
            filename = item.get("filename", f"file{file_extension}")
            mime_type = self.get_file_mime_type(file_extension)
            
            if file_extension.lower() in self.SUPPORTED_IMAGE_TYPES:
                # 图片格式文件
                content_parts.append(
                    ImageUrlContent(
                        image_url=ImageUrl(
                            url=f"data:{mime_type};base64,{file_data}",
                            detail="high"
                        )
                    )
                )
            elif file_extension.lower() in self.SUPPORTED_DOCUMENT_TYPES:
                # 文档格式文件
                content_parts.append(
                    FileContent(
                        file=FileData(
                            file_data=f"data:{mime_type};base64,{file_data}",
                            filename=filename,
                        )
                    )
                )
            else:
                raise ValueError(f"不支持的文件格式: {file_extension}")
        
        try:
            # 创建请求
            request = LLMRequest(
                model=self.model,
                messages=[
                    SystemMessage(content=self.default_prompt),
                    UserMessage(content=content_parts)
                ],
                temperature=self.temperature,
                max_completion_tokens=self.max_tokens,
            )
            
            # 调用LLM
            response = await self.llm.chat(request)
            result = response.content.strip()
            
            # 执行垃圾回收
            gc.collect()
            
            return result
            
        except LLMError as e:
            logger.error(f"文件内容提取失败: {e}")
            traceback.print_exc()
            raise
        except Exception as e:
            logger.error(f"未知错误: {e}")
            traceback.print_exc()
            raise
    
    async def extract_text_from_files(
        self, 
        file_paths: List[str]
    ) -> str:
        """
        从多个文件路径中提取纯文本内容（在一次模型调用中处理）
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            提取的纯文本内容
            
        Raises:
            FileNotFoundError: 任何一个文件不存在
            ValueError: 不支持的文件格式
            LLMError: LLM调用失败
        """
        # 验证所有文件是否存在并读取文件数据
        file_data_list = []
        for file_path in file_paths:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 获取文件扩展名
            file_extension = Path(file_path).suffix
            filename = os.path.basename(file_path)
            
            # 验证文件类型
            if file_extension.lower() not in self.SUPPORTED_TYPES:
                raise ValueError(f"不支持的文件类型: {file_extension}")
            
            # 读取文件并编码为Base64
            with open(file_path, "rb") as f:
                file_data = base64.b64encode(f.read()).decode("utf-8")
            
            file_data_list.append({
                "file_data": file_data,
                "file_extension": file_extension,
                "filename": filename
            })
        
        # 调用Base64方法
        return await self.extract_text_from_base64(file_data_list)
    
    async def batch_extract_text_from_base64(
        self, 
        file_data_list: List[Dict[str, str]], 
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """
        批量从Base64编码的文件数据中提取纯文本内容
        
        Args:
            file_data_list: 文件数据列表，每个元素包含file_data和file_extension
            max_concurrent: 最大并发数
            
        Returns:
            提取结果列表，每个元素包含文件信息和提取内容或错误信息
        """
        import asyncio
        
        # 创建信号量控制并发数
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def extract_single_file(file_info):
            async with semaphore:
                try:
                    # 为单个文件创建文件数据列表
                    single_file_list = [{
                        "file_data": file_info["file_data"],
                        "file_extension": file_info["file_extension"],
                        "filename": file_info.get("filename")
                    }]
                    content = await self.extract_text_from_base64(single_file_list)
                    return {
                        "file_info": file_info,
                        "content": content,
                        "success": True,
                    }
                except Exception as e:
                    return {
                        "file_info": file_info,
                        "error": str(e),
                        "success": False,
                    }
        
        # 执行并发提取
        tasks = [extract_single_file(file_info) for file_info in file_data_list]
        results = await asyncio.gather(*tasks)
        
        # 执行垃圾回收
        gc.collect()
        
        return results
    
    async def batch_extract_text_from_files(
        self, 
        file_paths: List[str], 
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """
        批量从文件路径中提取纯文本内容（兼容性方法）
        
        Args:
            file_paths: 文件路径列表
            max_concurrent: 最大并发数
            
        Returns:
            提取结果列表，每个元素包含文件路径和提取内容或错误信息
        """
        # 准备文件数据列表
        file_data_list = []
        for file_path in file_paths:
            if not os.path.exists(file_path):
                # 添加不存在的文件信息，以便在结果中返回错误
                file_data_list.append({
                    "file_path": file_path,
                    "file_data": None,
                    "file_extension": None,
                    "filename": os.path.basename(file_path),
                })
                continue
            
            # 读取文件并编码为Base64
            file_extension = Path(file_path).suffix
            filename = os.path.basename(file_path)
            
            with open(file_path, "rb") as f:
                file_data = base64.b64encode(f.read()).decode("utf-8")
            
            file_data_list.append({
                "file_path": file_path,
                "file_data": file_data,
                "file_extension": file_extension,
                "filename": filename,
            })
        
        # 调用Base64批量方法
        results = await self.batch_extract_text_from_base64(
            file_data_list=[
                {
                    "file_data": item["file_data"],
                    "file_extension": item["file_extension"],
                    "filename": item["filename"]
                }
                for item in file_data_list if item["file_data"] is not None
            ],
            max_concurrent=max_concurrent
        )
        
        # 合并结果
        final_results = []
        base64_results = {result["file_info"]["filename"]: result for result in results}
        
        for item in file_data_list:
            if item["file_data"] is None:
                # 不存在的文件
                final_results.append({
                    "file_path": item["file_path"],
                    "error": f"文件不存在: {item['file_path']}",
                    "success": False,
                })
            else:
                # 存在的文件
                result = base64_results.get(item["filename"])
                if result:
                    final_results.append({
                        "file_path": item["file_path"],
                        "content": result["content"],
                        "success": result["success"],
                        "error": result.get("error"),
                    })
        
        return final_results


# 模块级别的函数接口，提供更简单的调用方式

# 默认提取器实例
_default_extractor = None

def _get_default_extractor():
    """获取默认提取器实例（懒加载）"""
    global _default_extractor
    if _default_extractor is None:
        _default_extractor = LLMContentExtractor(provider="volcengine")
    return _default_extractor


async def extract_text_from_base64(
    file_data_list: List[Dict[str, str]]
) -> str:
    """
    从Base64编码的文件数据中提取纯文本内容（模块级别函数）
    
    Args:
        file_data_list: 文件数据列表，每个元素包含file_data、file_extension和filename(可选)
        
    Returns:
        提取的纯文本内容
        
    Raises:
        ValueError: 文件数据无效或不支持的文件格式
        LLMError: LLM调用失败
    """
    extractor = _get_default_extractor()
    return await extractor.extract_text_from_base64(file_data_list)


async def extract_text_from_files(
    file_paths: List[str]
) -> str:
    """
    从多个文件路径中提取纯文本内容（模块级别函数）
    
    Args:
        file_paths: 文件路径列表
        
    Returns:
        提取的纯文本内容
        
    Raises:
        FileNotFoundError: 任何一个文件不存在
        ValueError: 不支持的文件格式
        LLMError: LLM调用失败
    """
    extractor = _get_default_extractor()
    return await extractor.extract_text_from_files(file_paths)


async def batch_extract_text_from_base64(
    file_data_list: List[Dict[str, str]], 
    max_concurrent: int = 3
) -> List[Dict[str, Any]]:
    """
    批量从Base64编码的文件数据中提取纯文本内容（模块级别函数）
    
    Args:
        file_data_list: 文件数据列表，每个元素包含file_data和file_extension
        max_concurrent: 最大并发数
        
    Returns:
        提取结果列表，每个元素包含文件信息和提取内容或错误信息
    """
    extractor = _get_default_extractor()
    return await extractor.batch_extract_text_from_base64(file_data_list, max_concurrent)


async def batch_extract_text_from_files(
    file_paths: List[str], 
    max_concurrent: int = 3
) -> List[Dict[str, Any]]:
    """
    批量从文件路径中提取纯文本内容（模块级别函数）
    
    Args:
        file_paths: 文件路径列表
        max_concurrent: 最大并发数
        
    Returns:
        提取结果列表，每个元素包含文件路径和提取内容或错误信息
    """
    extractor = _get_default_extractor()
    return await extractor.batch_extract_text_from_files(file_paths, max_concurrent)


def set_default_provider(provider: str):
    """
    设置默认LLM提供商
    
    Args:
        provider: LLM提供商，支持 "openai" 或 "volcengine"
    """
    global _default_extractor
    _default_extractor = LLMContentExtractor(provider=provider)
    
    