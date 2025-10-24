"""
Datetime utilities
"""
from datetime import datetime, timezone
from typing import Optional
import pytz


def utcnow() -> datetime:
    """获取当前UTC时间"""
    return datetime.now(timezone.utc)


def to_utc(dt: datetime) -> datetime:
    """转换为UTC时间"""
    if dt.tzinfo is None:
        # 假设为UTC
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def format_datetime(dt: datetime, format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化datetime"""
    return dt.strftime(format_string)


def parse_datetime(dt_string: str, format_string: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """解析datetime字符串"""
    return datetime.strptime(dt_string, format_string)


def convert_timezone(dt: datetime, to_timezone: str = "UTC") -> datetime:
    """转换时区"""
    tz = pytz.timezone(to_timezone)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(tz)

