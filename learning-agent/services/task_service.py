#!/usr/bin/env python3
"""
任务服务

管理工作流任务的执行和状态追踪
"""

import os
import sys
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid

# 添加项目路径
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

from workflow_orchestrator import WorkflowOrchestrator


class TaskService:
    """
    任务服务
    
    功能：
    - 创建工作流任务
    - 执行任务（异步）
    - 查询任务状态
    - 获取生成结果
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self.config_path = project_dir / "config" / "agent_config.yaml"
        self.data_dir = project_dir / "data" / "workflow_results"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 任务状态存储
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._running_tasks: Dict[str, threading.Thread] = {}
        
        self._initialized = True
    
    def execute(
        self,
        user_request: str = "生成完整的 Agent 开发学习路线",
        layers: Optional[List[int]] = None,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """
        执行工作流任务
        
        Args:
            user_request: 用户需求
            layers: 指定层级（None 表示全部）
            priority: 优先级
            
        Returns:
            任务信息
        """
        task_id = str(uuid.uuid4())[:8]
        
        # 创建任务记录
        self._tasks[task_id] = {
            "task_id": task_id,
            "user_request": user_request,
            "layers": layers,
            "priority": priority,
            "status": "running",
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
            "result": None,
            "error": None
        }
        
        # 异步执行工作流
        def run_workflow():
            try:
                orchestrator = WorkflowOrchestrator(config_path=str(self.config_path))
                result = orchestrator.execute_workflow(user_request, layers=layers)
                
                self._tasks[task_id]["status"] = "completed"
                self._tasks[task_id]["completed_at"] = datetime.now().isoformat()
                self._tasks[task_id]["result"] = result
                
            except Exception as e:
                self._tasks[task_id]["status"] = "failed"
                self._tasks[task_id]["error"] = str(e)
        
        thread = threading.Thread(target=run_workflow, daemon=True)
        thread.start()
        self._running_tasks[task_id] = thread
        
        return {
            "task_id": task_id,
            "status": "running",
            "message": "任务已启动，正在后台执行"
        }
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        if task_id not in self._tasks:
            return {
                "error": "Task not found",
                "task_id": task_id
            }
        
        task = self._tasks[task_id]
        return {
            "task_id": task["task_id"],
            "status": task["status"],
            "created_at": task["created_at"],
            "completed_at": task["completed_at"],
            "error": task["error"]
        }
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务"""
        return list(self._tasks.values())
    
    def get_generated_knowledge(self, layer: Optional[int] = None) -> Dict[str, Any]:
        """获取生成的知识"""
        knowledge = {}
        
        # 从数据目录加载
        if layer:
            layer_file = self.data_dir / f"layer_{layer}_workflow.json"
            if layer_file.exists():
                with open(layer_file, 'r', encoding='utf-8') as f:
                    knowledge[f"layer_{layer}"] = json.load(f)
        else:
            # 加载所有层级
            for layer_file in self.data_dir.glob("layer_*_workflow.json"):
                layer_num = layer_file.stem.split('_')[1]
                try:
                    with open(layer_file, 'r', encoding='utf-8') as f:
                        knowledge[f"layer_{layer_num}"] = json.load(f)
                except Exception:
                    pass
        
        return knowledge
    
    def get_summary(self) -> Dict[str, Any]:
        """获取工作流总结"""
        summary_file = self.data_dir / "workflow_summary.json"
        
        if summary_file.exists():
            with open(summary_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {"error": "Summary not found"}


# 全局实例
_task_service: Optional[TaskService] = None


def get_task_service(verbose: bool = False) -> TaskService:
    """获取任务服务单例"""
    global _task_service
    if _task_service is None:
        _task_service = TaskService()
        if verbose:
            print("✅ TaskService 初始化完成")
    return _task_service
