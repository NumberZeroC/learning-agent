#!/usr/bin/env python3
"""
Task 数据模型

定义工作流任务和工作流结果的数据结构。
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional


@dataclass
class Task:
    """工作流任务"""
    task_id: str
    layer_num: int
    topic_name: str
    status: str = "pending"
    result: Optional[Dict] = None
    error: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    retry_count: int = 0


@dataclass
class WorkflowResult:
    """工作流结果"""
    workflow_id: str
    started_at: str
    completed_at: str
    total_tasks: int
    success_count: int
    failed_count: int
    layer_results: Dict[str, Any]
    duration_seconds: float