"""
字符串工具函数
用于处理逗号分隔的字符串字段
"""

from typing import List, Optional


def split_string_field(value: Optional[str], separator: str = ",") -> List[str]:
    """
    将字符串字段分割为列表

    Args:
        value: 输入字符串，可能为None
        separator: 分隔符，默认为逗号

    Returns:
        分割后的字符串列表
    """
    if not value or not value.strip():
        return []

    return [item.strip() for item in value.split(separator) if item.strip()]


def join_string_field(items: List[str], separator: str = ",") -> Optional[str]:
    """
    将列表连接为字符串字段

    Args:
        items: 字符串列表
        separator: 分隔符，默认为逗号

    Returns:
        连接后的字符串，如果列表为空则返回None
    """
    if not items:
        return None

    # 过滤掉空字符串
    filtered_items = [item.strip() for item in items if item and item.strip()]
    if not filtered_items:
        return None

    return separator.join(filtered_items)


def normalize_string_field(value: Optional[str], separator: str = ",") -> Optional[str]:
    """
    标准化字符串字段：去除多余空格，统一分隔符

    Args:
        value: 输入字符串
        separator: 目标分隔符

    Returns:
        标准化后的字符串
    """
    if not value or not value.strip():
        return None

    # 先按各种可能的分隔符分割
    items = []
    for char in [",", ";", "，", "；", "|", "、"]:
        if char in value:
            items = [item.strip() for item in value.split(char) if item.strip()]
            break

    # 如果没有找到分隔符，将整个字符串作为一个项
    if not items:
        items = [value.strip()] if value.strip() else []

    # 过滤空项并用统一分隔符连接
    filtered_items = [item for item in items if item]
    return separator.join(filtered_items) if filtered_items else None


def add_to_string_field(current_value: Optional[str], new_items: List[str], separator: str = ",") -> str:
    """
    向字符串字段添加新项目

    Args:
        current_value: 当前字符串值
        new_items: 要添加的新项目列表
        separator: 分隔符

    Returns:
        更新后的字符串
    """
    existing_items = split_string_field(current_value, separator)
    all_items = existing_items + new_items

    # 去重并保持顺序
    seen = set()
    unique_items = []
    for item in all_items:
        if item and item.strip() and item not in seen:
            seen.add(item)
            unique_items.append(item.strip())

    return separator.join(unique_items) if unique_items else ""


def remove_from_string_field(current_value: Optional[str], items_to_remove: List[str], separator: str = ",") -> Optional[str]:
    """
    从字符串字段中移除指定项目

    Args:
        current_value: 当前字符串值
        items_to_remove: 要移除的项目列表
        separator: 分隔符

    Returns:
        更新后的字符串
    """
    existing_items = split_string_field(current_value, separator)
    remaining_items = [item for item in existing_items if item not in items_to_remove]

    return join_string_field(remaining_items, separator)


def contains_in_string_field(current_value: Optional[str], search_item: str, separator: str = ",") -> bool:
    """
    检查字符串字段是否包含指定项目

    Args:
        current_value: 当前字符串值
        search_item: 要搜索的项目
        separator: 分隔符

    Returns:
        是否包含
    """
    if not current_value or not search_item:
        return False

    items = split_string_field(current_value, separator)
    return search_item.strip() in items