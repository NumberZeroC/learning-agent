#!/usr/bin/env python3
"""
SQLite 数据库模型

提供统一的数据库访问层，支持：
- 工作流记录
- 对话历史
- LLM 审计日志
- 配置版本历史
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

# 数据库路径
DB_PATH = Path(__file__).parent.parent / "data" / "learning_agent.db"


def init_db():
    """初始化数据库，创建所有表"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 工作流执行记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id TEXT UNIQUE NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                total_tasks INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                duration_seconds REAL DEFAULT 0,
                status TEXT DEFAULT 'running',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 工作流任务详情表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                layer_num INTEGER NOT NULL,
                topic_name TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                result TEXT,
                error TEXT,
                start_time TEXT,
                end_time TEXT,
                retry_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id)
            )
        """)
        
        # 对话历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_histories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                session_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # LLM 审计日志表（替代 JSONL 文件）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                model TEXT NOT NULL,
                base_url TEXT,
                success INTEGER NOT NULL,
                prompt_tokens INTEGER DEFAULT 0,
                completion_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                cost REAL DEFAULT 0,
                duration_ms REAL DEFAULT 0,
                retries INTEGER DEFAULT 0,
                error_message TEXT,
                request_data TEXT,
                response_data TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 配置版本历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version INTEGER NOT NULL,
                config_data TEXT NOT NULL,
                change_description TEXT,
                changed_by TEXT DEFAULT 'system',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_workflow_tasks_workflow_id ON workflow_tasks(workflow_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_histories_agent ON chat_histories(agent_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_llm_audit_logs_agent ON llm_audit_logs(agent_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_llm_audit_logs_created ON llm_audit_logs(created_at)")
        
        logger.info("✅ 数据库初始化完成")


@contextmanager
def get_db():
    """获取数据库连接上下文管理器"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 支持字典访问
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ 数据库操作失败：{e}")
        raise
    finally:
        conn.close()


# ============================================
# 工作流数据访问
# ============================================

class WorkflowDAO:
    """工作流数据访问对象"""
    
    @staticmethod
    def create_workflow(workflow_id: str, started_at: str, total_tasks: int) -> int:
        """创建工作流记录"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO workflows (workflow_id, started_at, total_tasks, status)
                VALUES (?, ?, ?, 'running')
            """, (workflow_id, started_at, total_tasks))
            return cursor.lastrowid
    
    @staticmethod
    def complete_workflow(workflow_id: str, completed_at: str, success_count: int, 
                         failed_count: int, duration_seconds: float):
        """完成工作流"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE workflows 
                SET completed_at = ?, success_count = ?, failed_count = ?, 
                    duration_seconds = ?, status = 'completed'
                WHERE workflow_id = ?
            """, (completed_at, success_count, failed_count, duration_seconds, workflow_id))
    
    @staticmethod
    def create_task(workflow_id: str, task_id: str, layer_num: int, topic_name: str) -> int:
        """创建任务记录"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO workflow_tasks (workflow_id, task_id, layer_num, topic_name)
                VALUES (?, ?, ?, ?)
            """, (workflow_id, task_id, layer_num, topic_name))
            return cursor.lastrowid
    
    @staticmethod
    def update_task(task_id: str, status: str, result: Optional[Dict] = None, 
                   error: Optional[str] = None, end_time: Optional[str] = None):
        """更新任务状态"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE workflow_tasks 
                SET status = ?, result = ?, error = ?, end_time = ?
                WHERE task_id = ?
            """, (status, json.dumps(result, ensure_ascii=False) if result else None, 
                  error, end_time, task_id))
    
    @staticmethod
    def get_workflow(workflow_id: str) -> Optional[Dict]:
        """获取工作流详情"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM workflows WHERE workflow_id = ?", (workflow_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    @staticmethod
    def get_workflow_tasks(workflow_id: str) -> List[Dict]:
        """获取工作流所有任务"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM workflow_tasks WHERE workflow_id = ? ORDER BY layer_num, id
            """, (workflow_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def list_workflows(limit: int = 20) -> List[Dict]:
        """获取工作流列表"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM workflows ORDER BY created_at DESC LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]


# ============================================
# 对话历史数据访问
# ============================================

class ChatHistoryDAO:
    """对话历史数据访问对象"""
    
    @staticmethod
    def add_message(agent_name: str, role: str, content: str, 
                   timestamp: str, session_id: Optional[str] = None):
        """添加对话消息"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chat_histories (agent_name, role, content, timestamp, session_id)
                VALUES (?, ?, ?, ?, ?)
            """, (agent_name, role, content, timestamp, session_id))
    
    @staticmethod
    def get_history(agent_name: str, limit: int = 20, 
                   session_id: Optional[str] = None) -> List[Dict]:
        """获取对话历史"""
        with get_db() as conn:
            cursor = conn.cursor()
            if session_id:
                cursor.execute("""
                    SELECT * FROM chat_histories 
                    WHERE agent_name = ? AND session_id = ?
                    ORDER BY created_at DESC LIMIT ?
                """, (agent_name, session_id, limit))
            else:
                cursor.execute("""
                    SELECT * FROM chat_histories 
                    WHERE agent_name = ?
                    ORDER BY created_at DESC LIMIT ?
                """, (agent_name, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def clear_history(agent_name: str, session_id: Optional[str] = None):
        """清空对话历史"""
        with get_db() as conn:
            cursor = conn.cursor()
            if session_id:
                cursor.execute("""
                    DELETE FROM chat_histories 
                    WHERE agent_name = ? AND session_id = ?
                """, (agent_name, session_id))
            else:
                cursor.execute("""
                    DELETE FROM chat_histories WHERE agent_name = ?
                """, (agent_name,))


# ============================================
# LLM 审计日志数据访问
# ============================================

class LLMAuditLogDAO:
    """LLM 审计日志数据访问对象"""
    
    @staticmethod
    def log_call(agent_name: str, model: str, base_url: str, success: bool,
                prompt_tokens: int = 0, completion_tokens: int = 0,
                total_tokens: int = 0, cost: float = 0,
                duration_ms: float = 0, retries: int = 0,
                error_message: Optional[str] = None,
                request_data: Optional[str] = None,
                response_data: Optional[str] = None):
        """记录 LLM 调用"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO llm_audit_logs 
                (agent_name, model, base_url, success, prompt_tokens, completion_tokens,
                 total_tokens, cost, duration_ms, retries, error_message, 
                 request_data, response_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (agent_name, model, base_url, 1 if success else 0,
                  prompt_tokens, completion_tokens, total_tokens, cost,
                  duration_ms, retries, error_message, request_data, response_data))
    
    @staticmethod
    def get_logs(agent_name: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """获取审计日志"""
        with get_db() as conn:
            cursor = conn.cursor()
            if agent_name:
                cursor.execute("""
                    SELECT * FROM llm_audit_logs 
                    WHERE agent_name = ?
                    ORDER BY created_at DESC LIMIT ?
                """, (agent_name, limit))
            else:
                cursor.execute("""
                    SELECT * FROM llm_audit_logs 
                    ORDER BY created_at DESC LIMIT ?
                """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_stats() -> Dict:
        """获取统计信息"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # 总调用次数
            cursor.execute("SELECT COUNT(*) as total FROM llm_audit_logs")
            total = cursor.fetchone()['total']
            
            # 成功/失败次数
            cursor.execute("SELECT success, COUNT(*) as count FROM llm_audit_logs GROUP BY success")
            success_counts = {row['success']: row['count'] for row in cursor.fetchall()}
            
            # Token 总量
            cursor.execute("SELECT SUM(total_tokens) as total, SUM(prompt_tokens) as prompt, SUM(completion_tokens) as completion FROM llm_audit_logs")
            token_row = cursor.fetchone()
            
            # 成本总量
            cursor.execute("SELECT SUM(cost) as total_cost FROM llm_audit_logs")
            cost_row = cursor.fetchone()
            
            return {
                "total_calls": total,
                "success_calls": success_counts.get(1, 0),
                "failed_calls": success_counts.get(0, 0),
                "total_tokens": token_row['total'] or 0,
                "prompt_tokens": token_row['prompt'] or 0,
                "completion_tokens": token_row['completion'] or 0,
                "total_cost": cost_row['total_cost'] or 0
            }


# ============================================
# 配置版本数据访问
# ============================================

class ConfigVersionDAO:
    """配置版本数据访问对象"""
    
    @staticmethod
    def save_version(config_data: Dict, change_description: str = "", 
                    changed_by: str = "system") -> int:
        """保存配置版本"""
        with get_db() as conn:
            cursor = conn.cursor()
            # 获取下一个版本号
            cursor.execute("SELECT MAX(version) as max_ver FROM config_versions")
            row = cursor.fetchone()
            next_version = (row['max_ver'] or 0) + 1
            
            cursor.execute("""
                INSERT INTO config_versions (version, config_data, change_description, changed_by)
                VALUES (?, ?, ?, ?)
            """, (next_version, json.dumps(config_data, ensure_ascii=False, indent=2),
                  change_description, changed_by))
            return next_version
    
    @staticmethod
    def get_version(version: int) -> Optional[Dict]:
        """获取指定版本"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM config_versions WHERE version = ?", (version,))
            row = cursor.fetchone()
            if row:
                data = dict(row)
                data['config_data'] = json.loads(data['config_data'])
                return data
            return None
    
    @staticmethod
    def list_versions(limit: int = 10) -> List[Dict]:
        """获取版本列表"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, version, change_description, changed_by, created_at 
                FROM config_versions 
                ORDER BY version DESC LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]


# ============================================
# 初始化
# ============================================

def initialize():
    """初始化数据库"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    init_db()
    logger.info(f"📊 数据库路径：{DB_PATH}")


if __name__ == "__main__":
    # 测试初始化
    initialize()
    print("✅ 数据库初始化成功")
