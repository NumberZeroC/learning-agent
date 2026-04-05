#!/usr/bin/env python3
"""
LLM 调用审计日志（优化版）

独立记录所有 LLM 调用，用于：
- 成本审计
- 调用追踪
- 性能分析
- 安全合规

优化改进：
- ✅ 使用 SQLite 存储（替代 JSONL/CSV 文件）
- ✅ 保留文件导出功能（用于备份）
- ✅ 支持复杂查询和统计
"""

import os
import json
import csv
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
import logging


# ============================================
# 数据模型
# ============================================

@dataclass
class LLMAuditRecord:
    """LLM 调用审计记录"""
    timestamp: str
    agent_name: str
    model: str
    base_url: str
    success: bool
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    duration_ms: float = 0.0
    retries: int = 0
    error_message: Optional[str] = None
    request_id: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d%H%M%S%f")[:20])
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_csv_row(self) -> List:
        return [
            self.timestamp,
            self.request_id,
            self.agent_name,
            self.model,
            self.base_url,
            self.success,
            self.prompt_tokens,
            self.completion_tokens,
            self.total_tokens,
            self.cost,
            self.duration_ms,
            self.retries,
            self.error_message or ""
        ]


# ============================================
# 审计日志记录器
# ============================================

class LLMAuditLogger:
    """
    LLM 调用审计日志记录器
    
    特性：
    - 独立日志文件（不与主进程日志混合）
    - JSON 和 CSV 双格式存储
    - 线程安全
    - 自动按日期分割文件
    - 支持查询和导出
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
        
        # 日志目录
        self.log_dir = Path("data/llm_audit_logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 当前日志文件（保留文件日志用于备份）
        self._current_date = datetime.now().strftime("%Y-%m-%d")
        self._json_log_path = self.log_dir / f"llm_calls_{self._current_date}.jsonl"
        self._csv_log_path = self.log_dir / f"llm_calls_{self._current_date}.csv"
        
        # 线程锁
        self._file_lock = threading.Lock()
        
        # 内存缓存（用于快速统计）
        self._cache: List[LLMAuditRecord] = []
        self._cache_max_size = 1000
        
        # CSV 文件头
        self._csv_header = [
            "timestamp", "request_id", "agent_name", "model", "base_url",
            "success", "prompt_tokens", "completion_tokens", "total_tokens",
            "cost", "duration_ms", "retries", "error_message"
        ]
        
        # 初始化 SQLite 数据库
        self._init_database()
        
        # 初始化 CSV 文件（如果不存在）
        self._init_csv()
        
        self._initialized = True
        
        print(f"✅ LLM 审计日志初始化完成（SQLite + 文件备份）")
        print(f"   SQLite 数据库：data/learning_agent.db (llm_audit_logs 表)")
        print(f"   JSON 日志：{self._json_log_path}")
        print(f"   CSV 日志：{self._csv_log_path}")
    
    def _init_database(self):
        """初始化 SQLite 数据库"""
        try:
            from models.database import initialize, LLMAuditLogDAO
            initialize()
            self.audit_dao = LLMAuditLogDAO
        except Exception as e:
            print(f"⚠️  SQLite 初始化失败：{e}，将仅使用文件日志")
            self.audit_dao = None
    
    def _init_csv(self):
        """初始化 CSV 文件（添加表头）"""
        if not self._csv_log_path.exists():
            with self._file_lock:
                with open(self._csv_log_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(self._csv_header)
    
    def _rotate_file_if_needed(self):
        """检查是否需要按日期轮转文件"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        if current_date != self._current_date:
            self._current_date = current_date
            self._json_log_path = self.log_dir / f"llm_calls_{self._current_date}.jsonl"
            self._csv_log_path = self.log_dir / f"llm_calls_{self._current_date}.csv"
            self._init_csv()
    
    def log(self, record: LLMAuditRecord):
        """
        记录一条 LLM 调用审计日志（SQLite + 文件备份）
        
        Args:
            record: 审计记录
        """
        self._rotate_file_if_needed()
        
        with self._file_lock:
            # 写入 SQLite 数据库（主要存储）
            if self.audit_dao:
                try:
                    self.audit_dao.log_call(
                        agent_name=record.agent_name,
                        model=record.model,
                        base_url=record.base_url,
                        success=record.success,
                        prompt_tokens=record.prompt_tokens,
                        completion_tokens=record.completion_tokens,
                        total_tokens=record.total_tokens,
                        cost=record.cost,
                        duration_ms=record.duration_ms,
                        retries=record.retries,
                        error_message=record.error_message
                    )
                except Exception as e:
                    print(f"⚠️  SQLite 写入失败：{e}")
            
            # 写入 JSONL 文件（备份）
            with open(self._json_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record.to_dict(), ensure_ascii=False) + '\n')
            
            # 写入 CSV 文件（备份）
            with open(self._csv_log_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(record.to_csv_row())
            
            # 添加到内存缓存
            self._cache.append(record)
            if len(self._cache) > self._cache_max_size:
                self._cache.pop(0)
    
    def log_call(
        self,
        agent_name: str,
        model: str,
        base_url: str,
        success: bool,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        cost: float = 0.0,
        duration_ms: float = 0.0,
        retries: int = 0,
        error_message: Optional[str] = None
    ):
        """
        便捷方法：记录 LLM 调用
        
        Args:
            agent_name: Agent 名称
            model: 模型名称
            base_url: API 基础 URL
            success: 是否成功
            prompt_tokens: 输入 Token 数
            completion_tokens: 输出 Token 数
            total_tokens: 总 Token 数
            cost: 成本（人民币）
            duration_ms: 调用耗时（毫秒）
            retries: 重试次数
            error_message: 错误信息（失败时）
        """
        record = LLMAuditRecord(
            timestamp=datetime.now().isoformat(),
            agent_name=agent_name,
            model=model,
            base_url=base_url,
            success=success,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=cost,
            duration_ms=duration_ms,
            retries=retries,
            error_message=error_message
        )
        self.log(record)
    
    def get_records(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        agent_name: Optional[str] = None,
        model: Optional[str] = None,
        success_only: bool = False,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        查询审计日志
        
        Args:
            start_time: 开始时间（ISO 格式）
            end_time: 结束时间（ISO 格式）
            agent_name: Agent 名称过滤
            model: 模型名称过滤
            success_only: 只返回成功记录
            limit: 返回数量限制
            
        Returns:
            审计记录列表
        """
        results = []
        
        # 从缓存中查找
        for record in self._cache:
            # 时间过滤
            if start_time and record.timestamp < start_time:
                continue
            if end_time and record.timestamp > end_time:
                continue
            
            # Agent 过滤
            if agent_name and record.agent_name != agent_name:
                continue
            
            # 模型过滤
            if model and record.model != model:
                continue
            
            # 成功/失败过滤
            if success_only and not record.success:
                continue
            
            results.append(record.to_dict())
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_stats(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取统计信息
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            统计信息字典
        """
        records = self.get_records(start_time, end_time, limit=10000)
        
        if not records:
            return {
                "total_calls": 0,
                "success_calls": 0,
                "failed_calls": 0,
                "success_rate": "0.0%",
                "total_tokens": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_cost": 0.0,
                "avg_duration_ms": 0.0,
                "avg_tokens_per_call": 0.0,
                "by_agent": {},
                "by_model": {}
            }
        
        # 基础统计
        total_calls = len(records)
        success_calls = sum(1 for r in records if r['success'])
        failed_calls = total_calls - success_calls
        total_tokens = sum(r['total_tokens'] for r in records)
        prompt_tokens = sum(r['prompt_tokens'] for r in records)
        completion_tokens = sum(r['completion_tokens'] for r in records)
        total_cost = sum(r['cost'] for r in records)
        total_duration = sum(r['duration_ms'] for r in records)
        
        # 按 Agent 统计
        by_agent = {}
        for r in records:
            agent = r['agent_name']
            if agent not in by_agent:
                by_agent[agent] = {
                    "calls": 0,
                    "success": 0,
                    "failed": 0,
                    "tokens": 0,
                    "cost": 0.0
                }
            by_agent[agent]["calls"] += 1
            if r['success']:
                by_agent[agent]["success"] += 1
            else:
                by_agent[agent]["failed"] += 1
            by_agent[agent]["tokens"] += r['total_tokens']
            by_agent[agent]["cost"] += r['cost']
        
        # 按模型统计
        by_model = {}
        for r in records:
            model = r['model']
            if model not in by_model:
                by_model[model] = {
                    "calls": 0,
                    "tokens": 0,
                    "cost": 0.0
                }
            by_model[model]["calls"] += 1
            by_model[model]["tokens"] += r['total_tokens']
            by_model[model]["cost"] += r['cost']
        
        return {
            "total_calls": total_calls,
            "success_calls": success_calls,
            "failed_calls": failed_calls,
            "success_rate": f"{success_calls / max(total_calls, 1) * 100:.1f}%",
            "total_tokens": total_tokens,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_cost": f"¥{total_cost:.4f}",
            "avg_duration_ms": f"{total_duration / max(total_calls, 1):.2f}",
            "avg_tokens_per_call": f"{total_tokens / max(total_calls, 1):.1f}",
            "by_agent": by_agent,
            "by_model": by_model
        }
    
    def export_to_json(self, output_path: str, start_time: Optional[str] = None, end_time: Optional[str] = None):
        """导出审计日志为 JSON 文件"""
        records = self.get_records(start_time, end_time, limit=100000)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 已导出 {len(records)} 条记录到 {output_path}")
    
    def export_to_csv(self, output_path: str, start_time: Optional[str] = None, end_time: Optional[str] = None):
        """导出审计日志为 CSV 文件"""
        records = self.get_records(start_time, end_time, limit=100000)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(self._csv_header)
            for record in records:
                r = LLMAuditRecord(**record)
                writer.writerow(r.to_csv_row())
        
        print(f"✅ 已导出 {len(records)} 条记录到 {output_path}")
    
    def clear_cache(self):
        """清空内存缓存"""
        self._cache.clear()
    
    def get_log_files(self) -> List[Path]:
        """获取所有日志文件列表"""
        return sorted(self.log_dir.glob("llm_calls_*.jsonl"))
    
    def get_total_records(self) -> int:
        """获取缓存中的记录数"""
        return len(self._cache)


# ============================================
# 全局实例
# ============================================

_audit_logger: Optional[LLMAuditLogger] = None


def get_audit_logger() -> LLMAuditLogger:
    """获取全局审计日志记录器"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = LLMAuditLogger()
    return _audit_logger


def log_llm_call(**kwargs):
    """
    便捷函数：记录 LLM 调用
    
    用法：
    log_llm_call(
        agent_name="theory_worker",
        model="qwen-plus",
        success=True,
        prompt_tokens=1000,
        completion_tokens=500,
        cost=0.005
    )
    """
    logger = get_audit_logger()
    logger.log_call(**kwargs)


def get_llm_stats(**kwargs) -> Dict[str, Any]:
    """
    便捷函数：获取 LLM 调用统计
    
    用法：
    stats = get_llm_stats()
    stats = get_llm_stats(agent_name="theory_worker")
    """
    logger = get_audit_logger()
    return logger.get_stats(**kwargs)
