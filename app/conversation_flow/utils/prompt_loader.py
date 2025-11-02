"""
Prompt模板加载器

负责从文件系统加载和管理Prompt模板
"""
import os
from typing import Dict, Optional
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)


class PromptLoader:
    """Prompt模板加载器"""

    def __init__(self, base_dir: Optional[str] = None):
        """
        初始化Prompt加载器

        Args:
            base_dir: Prompt模板根目录，默认为 app/ai/prompts/conversation_flow
        """
        if base_dir is None:
            # 默认路径：app/ai/prompts/conversation_flow
            current_dir = Path(__file__).parent.parent.parent
            base_dir = current_dir / "ai" / "prompts" / "conversation_flow"

        self.base_dir = Path(base_dir)
        self._template_cache: Dict[str, str] = {}

        logger.info("prompt_loader_initialized", base_dir=str(self.base_dir))

    def load_template(self, scene_name: str) -> str:
        """
        加载Prompt模板

        Args:
            scene_name: 场景名称（对应文件名，不含.md后缀）

        Returns:
            Prompt模板内容

        Raises:
            FileNotFoundError: 模板文件不存在
        """
        # 检查缓存
        if scene_name in self._template_cache:
            logger.debug("prompt_template_cache_hit", scene_name=scene_name)
            return self._template_cache[scene_name]

        # 读取文件
        template_path = self.base_dir / f"{scene_name}.md"

        if not template_path.exists():
            logger.error(
                "prompt_template_not_found",
                scene_name=scene_name,
                path=str(template_path)
            )
            raise FileNotFoundError(
                f"Prompt模板不存在: {scene_name} (路径: {template_path})"
            )

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()

            # 缓存模板
            self._template_cache[scene_name] = template_content

            logger.info(
                "prompt_template_loaded",
                scene_name=scene_name,
                length=len(template_content)
            )

            return template_content

        except Exception as e:
            logger.error(
                "failed_to_load_prompt_template",
                scene_name=scene_name,
                error=str(e)
            )
            raise

    def clear_cache(self, scene_name: Optional[str] = None) -> None:
        """
        清除模板缓存

        Args:
            scene_name: 场景名称，如果为None则清除所有缓存
        """
        if scene_name is None:
            self._template_cache.clear()
            logger.info("all_prompt_template_cache_cleared")
        elif scene_name in self._template_cache:
            del self._template_cache[scene_name]
            logger.info("prompt_template_cache_cleared", scene_name=scene_name)


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
