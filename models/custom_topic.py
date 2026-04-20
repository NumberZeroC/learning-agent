#!/usr/bin/env python3
"""
CustomTopicResult - 自定义主题结果

自定义主题知识生成的结果数据结构。
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class CustomTopicResult:
    """自定义主题结果"""
    topic_id: str
    topic_name: str
    agent: str
    success: bool
    knowledge: Optional[Dict] = None
    error: Optional[str] = None
    created_at: str = ""
    keypoint_count: int = 0