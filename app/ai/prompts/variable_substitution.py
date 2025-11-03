"""
变量替换工具

提供Prompt模板的变量替换功能，类似Java中的StringSubstitutor
"""
import re
from typing import Dict, Any
import structlog

logger = structlog.get_logger(__name__)


class VariableSubstitutor:
    """变量替换器"""

    def __init__(
        self,
        prefix: str = "${",
        suffix: str = "}",
        escape_char: str = "$"
    ):
        """
        初始化变量替换器

        Args:
            prefix: 变量前缀，默认 ${
            suffix: 变量后缀，默认 }
            escape_char: 转义字符，默认 $
        """
        self.prefix = prefix
        self.suffix = suffix
        self.escape_char = escape_char

        # 构建正则表达式模式
        # 匹配: ${变量名}
        escaped_prefix = re.escape(prefix)
        escaped_suffix = re.escape(suffix)
        self.pattern = re.compile(
            f"{escaped_prefix}([^{escaped_suffix}]+){escaped_suffix}"
        )

    def replace(
        self,
        template: str,
        values: Dict[str, Any],
        missing_key_behavior: str = "keep"
    ) -> str:
        """
        替换模板中的变量

        Args:
            template: 模板字符串
            values: 变量值字典
            missing_key_behavior: 缺失key的处理方式
                - "keep": 保留原始占位符（默认）
                - "empty": 替换为空字符串
                - "error": 抛出异常

        Returns:
            替换后的字符串

        Raises:
            KeyError: 当 missing_key_behavior="error" 且变量不存在时

        Examples:
            >>> sub = VariableSubstitutor()
            >>> template = "Hello ${name}, you are ${age} years old"
            >>> values = {"name": "Alice", "age": 30}
            >>> sub.replace(template, values)
            'Hello Alice, you are 30 years old'
        """

        def replacer(match):
            var_name = match.group(1).strip()

            if var_name in values:
                value = values[var_name]
                # 转换为字符串
                return str(value) if value is not None else ""
            else:
                if missing_key_behavior == "keep":
                    return match.group(0)  # 保留原始占位符
                elif missing_key_behavior == "empty":
                    logger.warning(
                        "variable_not_found_replaced_with_empty",
                        variable=var_name
                    )
                    return ""
                elif missing_key_behavior == "error":
                    raise KeyError(f"变量 '{var_name}' 在values中不存在")
                else:
                    raise ValueError(
                        f"不支持的missing_key_behavior: {missing_key_behavior}"
                    )

        result = self.pattern.sub(replacer, template)

        return result


# 全局单例
_default_substitutor = VariableSubstitutor()


def substitute_variables(
    template: str,
    values: Dict[str, Any],
    missing_key_behavior: str = "keep"
) -> str:
    """
    替换模板中的变量（便捷函数）

    Args:
        template: 模板字符串
        values: 变量值字典
        missing_key_behavior: 缺失key的处理方式

    Returns:
        替换后的字符串

    Examples:
        >>> template = "Hello ${name}"
        >>> substitute_variables(template, {"name": "World"})
        'Hello World'
    """
    return _default_substitutor.replace(template, values, missing_key_behavior)
