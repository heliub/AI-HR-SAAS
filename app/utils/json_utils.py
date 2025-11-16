import json
import re
from typing import Union


class JsonParser:
    """通用 JSON 解析类"""

    @staticmethod
    def parse(reply) -> Union[dict, list]:
        """解析回复数据"""
        try:
            if isinstance(reply, dict):
                return reply
            if isinstance(reply, list):
                return reply
            reply = JsonParser.clean_reply(reply)
            return json.loads(reply)
        except json.JSONDecodeError:
            fixed_reply = JsonParser.fix_json(reply)
            return JsonParser.manual_parse(fixed_reply)

    @staticmethod
    def clean_reply(reply) -> str:
        if not isinstance(reply, str):
            print(f"无法解析的行: {reply}")
            return str(reply)  # 将非字符串类型转换为字符串
        # 移除可能的markdown格式
        reply = re.sub(r'```json|```|\n', '', reply)
        # 移除多余的空白字符
        reply = reply.strip()
        return reply

    @staticmethod
    def fix_json(json_str) -> str:
        """尝试修复不合法的 JSON 字符串"""
        # 替换多余的逗号
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        # 将多行字符串合并为一行
        json_str = json_str.replace('\n', ' ')
        return json_str

    @staticmethod
    def manual_parse(json_str) -> Union[dict, list]:
        """手动解析修复后的 JSON 字符串"""
        result = []
        for item in re.findall(r'{[^}]+}', json_str):
            current_item = {}
            item = item.strip('{}')
            for pair in item.split(','):
                if ':' in pair:
                    key, value = pair.split(':', 1)
                    key = key.strip().strip('"')
                    value = value.strip().strip('"')
                    current_item[key] = value
            if current_item:
                result.append(current_item)
        if len(result) == 1:
            return result[0]
        if len(result) > 1:
            return result
        raise ValueError(f"无法解析的JSON字符串: {json_str}")
