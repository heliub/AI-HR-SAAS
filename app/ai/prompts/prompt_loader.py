"""
Prompt模板加载器

负责从文件系统加载和管理Prompt模板
"""
import os
from typing import Dict, Optional, Any
from pathlib import Path
import structlog

from app.ai.prompts.variable_substitution import substitute_variables
from app.ai.prompts.prompt_config import PROMPT_CONFIG

logger = structlog.get_logger(__name__)

class PromptLoader:
    """Prompt模板加载器"""

    def __init__(self, base_dir: Optional[str] = None):
        """
        初始化Prompt加载器

        Args:
            base_dir: Prompt模板根目录，默认为 app/ai/prompts
        """
        if base_dir is None:
            # 默认路径：app/ai/prompts
            current_dir = Path(__file__).parent.parent.parent
            base_dir = current_dir / "ai" / "prompts" 

        self.base_dir = Path(base_dir)
        self._template_cache: Dict[str, str] = {}

        logger.info("prompt_loader_initialized", base_dir=str(self.base_dir))

    def load_template(self, module: str, prompt_file: str) -> str:
        """
        加载Prompt模板

        Args:
            module: 模块名称
            prompt_file: 模板文件名（对应文件名，含.md后缀）

        Returns:
            Prompt模板内容

        Raises:
            FileNotFoundError: 模板文件不存在
        """
        # 检查缓存
        if prompt_file in self._template_cache:
            logger.debug("prompt_template_cache_hit", prompt_file=prompt_file)
            return self._template_cache[prompt_file]

        # 读取文件
        if module:
            template_path = self.base_dir / f"{module}" / f"{prompt_file}"
        else:
            template_path = self.base_dir / f"{prompt_file}"

        if not template_path.exists():
            logger.error(
                "prompt_template_not_found",
                prompt_file=prompt_file,
                path=str(template_path)
            )
            raise FileNotFoundError(
                f"Prompt模板不存在: {prompt_file} (路径: {template_path})"
            )

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()

            # 缓存模板
            self._template_cache[prompt_file] = template_content

            logger.info(
                "prompt_template_loaded",
                prompt_file=prompt_file,
                length=len(template_content)
            )

            return template_content

        except Exception as e:
            logger.error(
                "failed_to_load_prompt_template",
                prompt_file=prompt_file,
                error=str(e)
            )
            raise

    def clear_cache(self, prompt_file: Optional[str] = None) -> None:
        """
        清除模板缓存

        Args:
            prompt_file: 模板文件名，如果为None则清除所有缓存
        """
        if prompt_file is None:
            self._template_cache.clear()
            logger.info("all_prompt_template_cache_cleared")
        elif prompt_file in self._template_cache:
            del self._template_cache[prompt_file]
            logger.info("prompt_template_cache_cleared", prompt_file=prompt_file)

    def load_prompt(self, scene_name: str, template_vars: Dict[str, Any]) -> str:
         # 1. 读取场景配置
        scene_config = PROMPT_CONFIG.get(scene_name, {})
        template = self.load_template(scene_config.get("module"), scene_config.get("prompt"))
        prompt = substitute_variables(template, template_vars, missing_key_behavior="empty")
        return prompt

# 全局单例
_prompt_loader: Optional[PromptLoader] = None


def get_prompt_loader(base_dir: Optional[str] = None) -> PromptLoader:
    """
    获取Prompt加载器单例

    Args:
        base_dir: Prompt模板根目录

    Returns:
        PromptLoader实例
    """
    global _prompt_loader

    if _prompt_loader is None:
        _prompt_loader = PromptLoader(base_dir=base_dir)

    return _prompt_loader
