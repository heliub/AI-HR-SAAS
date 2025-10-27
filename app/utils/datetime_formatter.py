"""
日期时间格式化工具
提供更可读的时间格式
"""
from datetime import datetime
from typing import Optional, Union
from pydantic import GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic.fields import FieldInfo

class FormattedDateTime:
    """格式化的日期时间类"""

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: dict, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        """自定义JSON schema"""
        json_schema = handler(core_schema)
        json_schema.update({
            "type": "string",
            "format": "formatted-datetime",
            "pattern": "^\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}$"
        })
        return json_schema

class FormattedDate:
    """格式化的日期类"""

    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: dict, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        """自定义JSON schema"""
        json_schema = handler(core_schema)
        json_schema.update({
            "type": "string",
            "format": "formatted-date",
            "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
        })
        return json_schema

def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """
    格式化日期时间为可读格式

    Args:
        dt: datetime对象，可以是None

    Returns:
        格式化后的字符串，如 "2025-01-13 10:30:00"
    """
    if dt is None:
        return None

    # 确保datetime对象有时区信息
    if dt.tzinfo is None:
        # 如果没有时区信息，假设是UTC+8（北京时间）
        dt = dt.replace(tzinfo=None)  # 先移除时区，避免转换错误

    # 格式化为 "YYYY-MM-DD HH:mm:ss"
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def format_date(dt: Optional[Union[datetime, str]]) -> Optional[str]:
    """
    格式化日期为可读格式

    Args:
        dt: datetime对象或字符串，可以是None

    Returns:
        格式化后的字符串，如 "2025-01-13"
    """
    if dt is None:
        return None

    # 如果已经是字符串，直接返回
    if isinstance(dt, str):
        return dt

    # 格式化为 "YYYY-MM-DD"
    return dt.strftime("%Y-%m-%d")

def format_time_ago(dt: Optional[datetime]) -> Optional[str]:
    """
    格式化为"多久以前"的格式

    Args:
        dt: datetime对象，可以是None

    Returns:
        格式化后的字符串，如 "2小时前"、"3天前"
    """
    if dt is None:
        return None

    now = datetime.now()
    if dt.tzinfo:
        now = now.replace(tzinfo=dt.tzinfo)

    delta = now - dt

    if delta.total_seconds() < 60:
        return "刚刚"
    elif delta.total_seconds() < 3600:
        minutes = int(delta.total_seconds() / 60)
        return f"{minutes}分钟前"
    elif delta.total_seconds() < 86400:
        hours = int(delta.total_seconds() / 3600)
        return f"{hours}小时前"
    elif delta.total_seconds() < 604800:
        days = int(delta.total_seconds() / 86400)
        return f"{days}天前"
    elif delta.total_seconds() < 2592000:
        weeks = int(delta.total_seconds() / 604800)
        return f"{weeks}周前"
    elif delta.total_seconds() < 31536000:
        months = int(delta.total_seconds() / 2592000)
        return f"{months}个月前"
    else:
        years = int(delta.total_seconds() / 31536000)
        return f"{years}年前"

# Pydantic field类型定义
class FormattedDateTimeField:
    """格式化的日期时间字段类型"""

    @staticmethod
    def serialize(dt: Optional[datetime]) -> Optional[str]:
        """序列化方法"""
        return format_datetime(dt)

class FormattedDateField:
    """格式化的日期字段类型"""

    @staticmethod
    def serialize(dt: Optional[datetime]) -> Optional[str]:
        """序列化方法"""
        return format_date(dt)

class FormattedTimeAgoField:
    """格式化的"多久以前"字段类型"""

    @staticmethod
    def serialize(dt: Optional[datetime]) -> Optional[str]:
        """序列化方法"""
        return format_time_ago(dt)