"""
图片OCR工具
用于从图片中提取文本，支持文件流和本地文件路径两种模式
"""

import os
import tempfile
import asyncio
import hashlib
import threading
import base64
from io import BytesIO
from typing import Optional, Union, BinaryIO, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

import pytesseract
from PIL import Image, ImageEnhance
import structlog

logger = structlog.get_logger(__name__)


# 自定义异常类
class OCRError(Exception):
    """OCR相关错误的基类"""
    pass


class ImageValidationError(OCRError):
    """图片验证错误"""
    pass


class TesseractError(OCRError):
    """Tesseract引擎错误"""
    pass


class ResourceExhaustionError(OCRError):
    """资源耗尽错误"""
    pass


class OCRTimeoutError(OCRError):
    """OCR处理超时错误"""
    pass


@dataclass
class OCRConfig:
    """OCR配置类"""
    lang: str = "chi_sim+eng+ind"
    config: Optional[str] = None
    oem: Optional[int] = None
    psm: Optional[int] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    supported_formats: Tuple[str, ...] = ('JPEG', 'PNG', 'TIFF', 'BMP', 'GIF')
    timeout: int = 30
    max_concurrent: int = 5
    preprocess_options: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        # 验证语言配置
        if not self.lang:
            raise ValueError("语言配置不能为空")
        
        # 验证文件大小
        if self.max_file_size <= 0:
            raise ValueError("最大文件大小必须大于0")
        
        # 验证并发数
        if self.max_concurrent <= 0:
            raise ValueError("最大并发数必须大于0")
        
        # 验证超时时间
        if self.timeout <= 0:
            raise ValueError("超时时间必须大于0")


class ImageOCR:
    """图片OCR识别器"""
    
    # 支持的语言列表
    SUPPORTED_LANGUAGES = {
        "chinese": "chi_sim",
        "english": "eng",
        "indonesian": "ind"
    }
    
    # 常用语言组合
    LANGUAGE_COMBINATIONS = {
        "chinese_only": "chi_sim",
        "english_only": "eng",
        "indonesian_only": "ind",
        "chinese_english": "chi_sim+eng",
        "chinese_indonesian": "chi_sim+ind",
        "english_indonesian": "eng+ind",
        "all_three": "chi_sim+eng+ind"
    }
    
    # 类变量，用于跟踪不同配置的实例
    _instances = {}
    _instance_lock = threading.Lock()
    
    def __init__(self, config: Optional[OCRConfig] = None):
        """
        初始化OCR识别器
        
        Args:
            config: OCR配置对象，如果为None则使用默认配置
        """
        self.config = config or OCRConfig()
        
        # 构建tesseract配置
        config_parts = []
        
        if self.config.oem is not None:
            config_parts.append(f"--oem {self.config.oem}")
        
        if self.config.psm is not None:
            config_parts.append(f"--psm {self.config.psm}")
            
        if self.config.config:
            config_parts.append(self.config.config)
            
        self.tesseract_config = " ".join(config_parts) if config_parts else None
        
        # 检查依赖项
        self._check_dependencies()
        
        # 初始化线程池
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent)
    
    @classmethod
    def get_default_instance(cls, lang: str = "chi_sim+eng+ind", timeout: int = 30) -> 'ImageOCR':
        """获取指定配置的实例（多例模式）"""
        # 创建配置键
        config_key = f"{lang}_{timeout}"
        
        # 先尝试从缓存获取
        if config_key in cls._instances:
            return cls._instances[config_key]
        
        # 缓存中没有，需要创建新实例
        with cls._instance_lock:
            # 双重检查，防止多线程同时创建
            if config_key not in cls._instances:
                # 创建一个临时配置
                temp_config = OCRConfig()
                temp_config.lang = lang
                temp_config.timeout = timeout
                # 创建新实例
                cls._instances[config_key] = cls(temp_config)
        
        return cls._instances[config_key]
    
    def _check_dependencies(self):
        """检查所有依赖项"""
        # 检查tesseract版本
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract版本: {version}")
        except Exception as e:
            raise TesseractError(f"Tesseract未安装或不可用: {str(e)}")
        
        # 检查语言包
        try:
            available_langs = pytesseract.get_languages(config='')
            required_langs = set(self.config.lang.split('+'))
            missing_langs = required_langs - set(available_langs)
            
            if missing_langs:
                logger.warning(f"可能缺少语言包: {', '.join(missing_langs)}")
                # 注意：这里不抛出异常，因为某些情况下语言包可能以不同方式命名
        except Exception as e:
            logger.warning(f"检查语言包失败: {str(e)}")
        
        # 检查系统资源
        self._check_system_resources()
    
    def _check_system_resources(self):
        """检查系统资源"""
        # 检查临时目录空间
        try:
            temp_dir = tempfile.gettempdir()
            stat = os.statvfs(temp_dir)
            free_space = stat.f_bavail * stat.f_frsize
            
            if free_space < 100 * 1024 * 1024:  # 100MB
                logger.warning(f"临时目录空间不足: {free_space / (1024*1024):.2f}MB")
        except Exception as e:
            logger.warning(f"检查系统资源失败: {str(e)}")
    
    def _validate_image_file(self, image_path: str):
        """验证图片文件"""
        # 检查文件是否存在
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
        
        # 检查文件大小
        file_size = os.path.getsize(image_path)
        if file_size > self.config.max_file_size:
            raise ImageValidationError(
                f"图片文件过大: {file_size / (1024*1024):.2f}MB，最大允许: {self.config.max_file_size / (1024*1024):.2f}MB"
            )
        
        # 检查文件类型
        try:
            with Image.open(image_path) as img:
                if img.format not in self.config.supported_formats:
                    raise ImageValidationError(f"不支持的图片格式: {img.format}")
        except Exception as e:
            if isinstance(e, ImageValidationError):
                raise
            raise ImageValidationError(f"无效的图片文件: {str(e)}")
    
    def _validate_image_bytes(self, image_bytes: bytes):
        """验证图片字节流"""
        if not image_bytes:
            raise ValueError("图片字节流不能为空")
        
        # 检查大小
        if len(image_bytes) > self.config.max_file_size:
            raise ImageValidationError(
                f"图片字节流过大: {len(image_bytes) / (1024*1024):.2f}MB，最大允许: {self.config.max_file_size / (1024*1024):.2f}MB"
            )
        
        # 检查是否为有效图片
        try:
            with Image.open(BytesIO(image_bytes)) as img:
                if img.format not in self.config.supported_formats:
                    raise ImageValidationError(f"不支持的图片格式: {img.format}")
        except Exception as e:
            if isinstance(e, ImageValidationError):
                raise
            raise ImageValidationError(f"无效的图片字节流: {str(e)}")
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """图片预处理"""
        if not self.config.preprocess_options:
            return image
        
        # 创建副本以避免修改原始图片
        processed_image = image.copy()
        
        # 转换为灰度图
        if self.config.preprocess_options.get('grayscale', False):
            processed_image = processed_image.convert('L')
        
        # 调整对比度
        if 'contrast_factor' in self.config.preprocess_options:
            enhancer = ImageEnhance.Contrast(processed_image)
            processed_image = enhancer.enhance(self.config.preprocess_options['contrast_factor'])
        
        # 调整亮度
        if 'brightness_factor' in self.config.preprocess_options:
            enhancer = ImageEnhance.Brightness(processed_image)
            processed_image = enhancer.enhance(self.config.preprocess_options['brightness_factor'])
        
        # 调整锐度
        if 'sharpness_factor' in self.config.preprocess_options:
            enhancer = ImageEnhance.Sharpness(processed_image)
            processed_image = enhancer.enhance(self.config.preprocess_options['sharpness_factor'])
        
        # 调整大小
        if 'max_size' in self.config.preprocess_options:
            max_size = self.config.preprocess_options['max_size']
            processed_image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # 二值化
        if self.config.preprocess_options.get('binarize', False):
            if processed_image.mode != 'L':
                processed_image = processed_image.convert('L')
            
            threshold = self.config.preprocess_options.get('binarize_threshold', 128)
            processed_image = processed_image.point(lambda x: 0 if x < threshold else 255, '1')
        
        return processed_image
    
    def _perform_ocr(self, image: Image.Image, output_type: str, timeout: int) -> Union[str, Dict[str, Any]]:
        """执行OCR识别"""
        try:
            # 预处理图片
            processed_image = self._preprocess_image(image)
            
            # 执行OCR识别
            if output_type == "string":
                return pytesseract.image_to_string(
                    processed_image, 
                    lang=self.config.lang, 
                    config=self.tesseract_config,
                    timeout=timeout
                )
            elif output_type == "dict":
                return pytesseract.image_to_data(
                    processed_image, 
                    lang=self.config.lang, 
                    config=self.tesseract_config,
                    output_type=pytesseract.Output.DICT,
                    timeout=timeout
                )
            elif output_type == "dataframe":
                return pytesseract.image_to_data(
                    processed_image, 
                    lang=self.config.lang, 
                    config=self.tesseract_config,
                    output_type=pytesseract.Output.DATAFRAME,
                    timeout=timeout
                )
            else:
                raise ValueError(f"不支持的输出类型: {output_type}")
        except pytesseract.TesseractError as e:
            raise TesseractError(f"Tesseract OCR错误: {str(e)}")
        except pytesseract.TesseractNotFoundError as e:
            raise TesseractError(f"Tesseract未找到: {str(e)}")
        except pytesseract.TSVNotSupported as e:
            raise TesseractError(f"TSV格式不支持: {str(e)}")
        except Exception as e:
            if "timeout" in str(e).lower():
                raise OCRTimeoutError(f"OCR处理超时({timeout}秒): {str(e)}")
            raise OCRError(f"OCR识别失败: {str(e)}")
    
    def _handle_ocr_exception(self, e: Exception, context: str):
        """处理OCR异常"""
        if isinstance(e, (ImageValidationError, TesseractError, ResourceExhaustionError, OCRTimeoutError)):
            logger.error(f"OCR处理失败: {context}", error=str(e), error_type=type(e).__name__)
            raise
        else:
            logger.error(f"OCR处理失败: {context}", error=str(e), error_type=type(e).__name__)
            raise OCRError(f"OCR处理失败: {str(e)}")
    
    def extract_text_from_path(
        self,
        image_path: str,
        output_type: str = "string",
        timeout: Optional[int] = None
    ) -> Union[str, Dict[str, Any]]:
        """
        从本地图片文件路径提取文本
        
        Args:
            image_path: 图片文件路径
            output_type: 输出类型 ("string", "dict", "dataframe")
            timeout: 超时时间(秒)，如果为None则使用配置中的默认值
            
        Returns:
            识别出的文本或详细结果
        """
        if timeout is None:
            timeout = self.config.timeout
            
        # 验证图片文件
        self._validate_image_file(image_path)
        
        try:
            # 使用上下文管理器确保资源释放
            with Image.open(image_path) as img:
                # 执行OCR识别
                return self._perform_ocr(img, output_type, timeout)
                
        except Exception as e:
            self._handle_ocr_exception(e, f"从文件路径提取文本失败: {image_path}")
    
    def extract_text_from_bytes(
        self,
        image_bytes: bytes,
        output_type: str = "string",
        timeout: Optional[int] = None
    ) -> Union[str, Dict[str, Any]]:
        """
        从图片字节流提取文本
        
        Args:
            image_bytes: 图片字节流
            output_type: 输出类型 ("string", "dict", "dataframe")
            timeout: 超时时间(秒)，如果为None则使用配置中的默认值
            
        Returns:
            识别出的文本或详细结果
        """
        if timeout is None:
            timeout = self.config.timeout
            
        # 验证图片字节流
        self._validate_image_bytes(image_bytes)
        
        try:
            # 从字节流创建图片对象
            with Image.open(BytesIO(image_bytes)) as img:
                # 执行OCR识别
                return self._perform_ocr(img, output_type, timeout)
                
        except Exception as e:
            self._handle_ocr_exception(e, "从字节流提取文本失败")
    
    def extract_text_from_base64(
        self,
        base64_string: str,
        output_type: str = "string",
        timeout: Optional[int] = None
    ) -> Union[str, Dict[str, Any]]:
        """
        从base64编码的图片字符串提取文本
        
        Args:
            base64_string: base64编码的图片字符串
            output_type: 输出类型 ("string", "dict", "dataframe")
            timeout: 超时时间(秒)，如果为None则使用配置中的默认值
            
        Returns:
            识别出的文本或详细结果
        """
        if timeout is None:
            timeout = self.config.timeout
            
        try:
            # 解码base64字符串
            image_bytes = base64.b64decode(base64_string)
            # 调用字节流方法
            return self.extract_text_from_bytes(image_bytes, output_type, timeout)
        except Exception as e:
            self._handle_ocr_exception(e, "从base64字符串提取文本失败")
    
    def extract_text_from_file_object(
        self,
        file_object: BinaryIO,
        output_type: str = "string",
        timeout: Optional[int] = None
    ) -> Union[str, Dict[str, Any]]:
        """
        从文件对象提取文本
        
        Args:
            file_object: 文件对象
            output_type: 输出类型 ("string", "dict", "dataframe")
            timeout: 超时时间(秒)，如果为None则使用配置中的默认值
            
        Returns:
            识别出的文本或详细结果
        """
        if timeout is None:
            timeout = self.config.timeout
            
        try:
            # 保存当前位置
            current_pos = file_object.tell()
            
            # 从文件对象创建图片对象
            with Image.open(file_object) as img:
                # 执行OCR识别
                result = self._perform_ocr(img, output_type, timeout)
            
            # 恢复文件对象位置
            file_object.seek(current_pos)
            
            return result
                
        except Exception as e:
            # 确保恢复文件对象位置
            try:
                file_object.seek(current_pos)
            except:
                pass
            self._handle_ocr_exception(e, "从文件对象提取文本失败")
    
    def extract_text_with_boxes(
        self,
        image_source: Union[str, bytes, BinaryIO],
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        提取文本并返回文本框位置信息
        
        Args:
            image_source: 图片源，可以是路径、字节流或文件对象
            timeout: 超时时间(秒)，如果为None则使用配置中的默认值
            
        Returns:
            包含文本和位置信息的字典
        """
        if timeout is None:
            timeout = self.config.timeout
            
        image_size = None
        try:
            # 根据输入类型处理图片
            if isinstance(image_source, str):
                self._validate_image_file(image_source)
                with Image.open(image_source) as img:
                    image_size = img.size
                    # 直接使用原始图片，不复制
                    processed_image = self._preprocess_image(img)
            elif isinstance(image_source, bytes):
                self._validate_image_bytes(image_source)
                with Image.open(BytesIO(image_source)) as img:
                    image_size = img.size
                    # 直接使用原始图片，不复制
                    processed_image = self._preprocess_image(img)
            else:
                # 保存当前位置
                current_pos = image_source.tell()
                with Image.open(image_source) as img:
                    image_size = img.size
                    # 直接使用原始图片，不复制
                    processed_image = self._preprocess_image(img)
                # 恢复文件对象位置
                image_source.seek(current_pos)
                
            # 获取OCR数据
            data = pytesseract.image_to_data(
                processed_image, 
                lang=self.config.lang, 
                config=self.tesseract_config,
                output_type=pytesseract.Output.DICT,
                timeout=timeout
            )
            
            # 提取有效文本和位置信息
            boxes = []
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 0:  # 过滤掉置信度为0的结果
                    text = data['text'][i].strip()
                    if text:  # 过滤掉空文本
                        boxes.append({
                            'text': data['text'][i],
                            'confidence': int(data['conf'][i]),
                            'bbox': {
                                'x': data['left'][i],
                                'y': data['top'][i],
                                'width': data['width'][i],
                                'height': data['height'][i]
                            }
                        })
            
            return {
                'text': ' '.join([box['text'] for box in boxes]),
                'boxes': boxes,
                'image_size': image_size
            }
            
        except Exception as e:
            self._handle_ocr_exception(e, "提取文本和位置信息失败")
    
    async def extract_text_from_multiple_images_async(
        self,
        image_sources: List[Union[str, bytes, BinaryIO]],
        output_type: str = "string",
        timeout: Optional[int] = None,
        max_concurrent: Optional[int] = None
    ) -> List[Union[str, Dict[str, Any]]]:
        """
        异步并发处理多个图片
        
        Args:
            image_sources: 图片源列表，可以是路径、字节流或文件对象
            output_type: 输出类型 ("string", "dict", "dataframe")
            timeout: 每个图片的超时时间(秒)，如果为None则使用配置中的默认值
            max_concurrent: 最大并发数，如果为None则使用配置中的默认值
            
        Returns:
            识别结果列表
        """
        if timeout is None:
            timeout = self.config.timeout
            
        if max_concurrent is None:
            max_concurrent = self.config.max_concurrent
            
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_single_image(source):
            async with semaphore:
                loop = asyncio.get_event_loop()
                try:
                    if isinstance(source, str):
                        return await loop.run_in_executor(
                            self.executor, self.extract_text_from_path, source, output_type, timeout
                        )
                    elif isinstance(source, bytes):
                        return await loop.run_in_executor(
                            self.executor, self.extract_text_from_bytes, source, output_type, timeout
                        )
                    else:
                        return await loop.run_in_executor(
                            self.executor, self.extract_text_from_file_object, source, output_type, timeout
                        )
                except Exception as e:
                    logger.error(f"处理图片失败", error=str(e))
                    return f"处理失败: {str(e)}"
        
        tasks = [process_single_image(src) for src in image_sources]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def extract_text_from_multiple_images(
        self,
        image_sources: List[Union[str, bytes, BinaryIO]],
        output_type: str = "string",
        timeout: Optional[int] = None
    ) -> List[Union[str, Dict[str, Any]]]:
        """
        从多个图片中批量提取文本（同步版本）
        
        Args:
            image_sources: 图片源列表，可以是路径、字节流或文件对象
            output_type: 输出类型 ("string", "dict", "dataframe")
            timeout: 每个图片的超时时间(秒)，如果为None则使用配置中的默认值
            
        Returns:
            识别结果列表
        """
        if timeout is None:
            timeout = self.config.timeout
            
        results = []
        
        for i, source in enumerate(image_sources):
            try:
                if isinstance(source, str):
                    result = self.extract_text_from_path(source, output_type, timeout)
                elif isinstance(source, bytes):
                    result = self.extract_text_from_bytes(source, output_type, timeout)
                else:
                    result = self.extract_text_from_file_object(source, output_type, timeout)
                    
                results.append(result)
                
            except Exception as e:
                logger.error(f"处理第{i+1}张图片失败", error=str(e))
                results.append(f"处理失败: {str(e)}")
                
        return results
    
    @staticmethod
    def get_available_languages() -> List[str]:
        """
        获取可用的OCR语言列表
        
        Returns:
            可用语言代码列表
        """
        try:
            return pytesseract.get_languages(config='')
        except Exception as e:
            logger.error("获取可用语言列表失败", error=str(e))
            return []
    
    @staticmethod
    def get_tesseract_version() -> str:
        """
        获取Tesseract版本信息
        
        Returns:
            Tesseract版本字符串
        """
        try:
            return str(pytesseract.get_tesseract_version())
        except Exception as e:
            logger.error("获取Tesseract版本失败", error=str(e))
            return "未知"
    
    @classmethod
    def get_supported_languages(cls) -> Dict[str, str]:
        """
        获取支持的语言列表
        
        Returns:
            支持的语言字典，键为语言名称，值为Tesseract语言代码
        """
        return cls.SUPPORTED_LANGUAGES.copy()
    
    @classmethod
    def get_language_combinations(cls) -> Dict[str, str]:
        """
        获取预定义的语言组合
        
        Returns:
            语言组合字典，键为组合名称，值为Tesseract语言代码组合
        """
        return cls.LANGUAGE_COMBINATIONS.copy()
    
    def close(self):
        """关闭资源"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


def extract_text_from_image(
    image_source: Union[str, bytes, BinaryIO],
    lang: str = "chi_sim+eng+ind",
    output_type: str = "string",
    timeout: int = 30
) -> Union[str, Dict[str, Any]]:
    """
    从图片中提取文本的便捷函数（使用多例模式）
    
    Args:
        image_source: 图片源，可以是路径、字节流、文件对象或base64字符串
        lang: 识别语言，默认为中文简体+英文+印尼语
        output_type: 输出类型 ("string", "dict", "dataframe")
        timeout: 超时时间(秒)
        
    Returns:
        识别出的文本或详细结果
    """
    # 获取或创建指定配置的实例
    ocr = ImageOCR.get_default_instance(lang, timeout)
    
    if isinstance(image_source, str):
        # 检查是否为data URI格式的base64字符串
        if image_source.startswith(('data:image/jpeg;base64,', 'data:image/png;base64,', 'data:image/gif;base64,')):
            # 带有data URI前缀的base64字符串，需要提取纯base64部分
            base64_part = image_source.split(',', 1)[1]
            return ocr.extract_text_from_base64(base64_part, output_type, timeout)
        elif os.path.isfile(image_source):
            # 检查是否为存在的文件路径
            return ocr.extract_text_from_path(image_source, output_type, timeout)
        else:
            # 尝试作为base64字符串处理
            return ocr.extract_text_from_base64(image_source, output_type, timeout)
    elif isinstance(image_source, bytes):
        return ocr.extract_text_from_bytes(image_source, output_type, timeout)
    else:
        return ocr.extract_text_from_file_object(image_source, output_type, timeout)
