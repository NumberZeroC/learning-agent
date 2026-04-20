#!/usr/bin/env python3
"""
Knowledge Parser - 知识内容解析工具

解析 LLM 返回的 JSON 内容，支持智能修复常见错误。
"""

import json
import re
import logging
from typing import Dict

logger = logging.getLogger("knowledge_parser")


def fix_json_quotes(raw_json: str) -> str:
    """
    修复 JSON：删除字符串值内部的中文引号等非法字符

    中文引号（unicode 8220/8221）在 JSON 中是非法字符，
    但它们在字符串值中只是用于强调，删除不影响语义。
    此方法只删除字符串值内部的中文引号，保留 JSON 结构的 ASCII 双引号。

    Args:
        raw_json: 原始 JSON 字符串

    Returns:
        str: 修复后的 JSON 字符串
    """
    result = []
    in_string = False
    escape_next = False

    for i, c in enumerate(raw_json):
        if escape_next:
            result.append(c)
            escape_next = False
            continue

        if c == '\\':
            result.append(c)
            escape_next = True
            continue

        # ASCII 双引号（unicode 34）：切换字符串状态
        if ord(c) == 34 and not escape_next:
            in_string = not in_string
            result.append(c)
            continue

        # 如果在字符串内部，遇到中文引号等非法字符就删除
        if in_string:
            # 中文引号 " " (unicode 8220/8221)
            if ord(c) == 8220 or ord(c) == 8221:
                continue
            # 中文单引号 ' ' (unicode 8216/8217) - 也删除，避免混淆
            if ord(c) == 8216 or ord(c) == 8217:
                continue

        result.append(c)

    return ''.join(result)


def parse_knowledge(content: str, fallback_name: str = "unknown") -> Dict:
    """
    解析知识内容（容错版，智能修复 JSON 错误）

    Args:
        content: LLM 返回的内容字符串
        fallback_name: 解析失败时的默认主题名称

    Returns:
        Dict: 解析后的知识字典
    """
    # 尝试提取 JSON 内容
    match = re.search(r"\{[\s\S]*\}", content)

    if match:
        raw_json = match.group()

        # 尝试直接解析
        try:
            return json.loads(raw_json)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON 解析失败：{e}，尝试智能修复...")

            # 智能修复：删除字符串值内部的中文引号
            fixed_json = fix_json_quotes(raw_json)

            try:
                result = json.loads(fixed_json)
                logger.info(f"✅ JSON 修复成功")
                return result
            except json.JSONDecodeError as e2:
                logger.warning(f"JSON 修复后仍失败：{e2}")

    # 解析失败，返回基础结构
    return {
        "topic_name": fallback_name,
        "description": content[:500] if content else "无内容",
        "subtopics": [],
        "raw_content": content,
    }


def strip_json_wrapper(content: str) -> str:
    """
    剥离 JSON 包装（如 ```json ... ```）

    Args:
        content: 包含可能的 markdown 包装的内容

    Returns:
        str: 去除包装后的内容
    """
    content = content.strip()

    # 剥离 ```json 和 ```
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]

    return content.strip()


def safe_json_loads(content: str, fallback: Dict = None) -> Dict:
    """
    安全的 JSON 解析，支持多种格式

    Args:
        content: JSON 字符串或带包装的内容
        fallback: 解析失败时的默认返回值

    Returns:
        Dict: 解析结果
    """
    if fallback is None:
        fallback = {}

    # 先剥离包装
    stripped = strip_json_wrapper(content)

    # 尝试解析
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        # 尝试修复
        fixed = fix_json_quotes(stripped)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            # 最后尝试用正则提取
            return parse_knowledge(stripped, fallback.get("topic_name", "unknown"))