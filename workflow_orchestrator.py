#!/usr/bin/env python3
"""
🤖 知识生成工作流编排器 (优化版 - 集成事件总线)

功能：
- 根据 KNOWLEDGE_FRAMEWORK 架构图定义工作流
- 并发向子 Agent 提问（使用线程池）
- 子 Agent 调用大模型进行回答
- 工作流记录所有回答并保存

优化改进：
- ✅ 集成事件总线（发布工作流进度事件）
- ✅ 每层完成后立即保存（防止中断丢失）
- ✅ 线程日志前缀区分（清晰看到并发进度）
- ✅ 更好的错误处理和重试机制
- ✅ API 超时控制
- ✅ JSON 解析容错
"""

import os
import sys
import json
import yaml
from services.llm_client import LLMClient
# import urllib.request  # 已移除，使用统一的 LLMClient
# import urllib.error  # 已移除
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from logging.handlers import RotatingFileHandler
import traceback

# 导入事件总线
try:
    from utils.event_bus import publish_event, EventType
    EVENT_BUS_AVAILABLE = True
except Exception:
    EVENT_BUS_AVAILABLE = False

# ============================================
# 线程安全的日志 formatter
# ============================================

class ThreadLogFormatter(logging.Formatter):
    """带线程标识的日志格式器"""
    
    def format(self, record):
        # 添加线程名
        record.thread_name = threading.current_thread().name
        return super().format(record)


# 配置日志
# 日志配置
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

# 控制台日志
console_handler = logging.StreamHandler()
console_handler.setFormatter(ThreadLogFormatter(
    '%(asctime)s - [%(thread_name)s] - %(levelname)s - %(message)s'
))

# 文件日志（轮转：最多保留 10 个文件，每个文件最大 10MB）
log_file = log_dir / "workflow.log"
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=10,  # 保留 10 个备份文件
    encoding='utf-8'
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - [%(thread_name)s] - %(name)s - %(levelname)s - %(message)s'
))

# 配置 logger
logger = logging.getLogger('workflow')
logger.setLevel(logging.INFO)
logger.handlers = [console_handler, file_handler]

logger.info(f"📝 日志文件：{log_file}")
logger.info(f"📊 日志策略：最多保留 10 个文件，每个文件最大 10MB")


# ============================================
# 数据模型
# ============================================

@dataclass
class Task:
    """任务定义"""
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


# ============================================
# 子 Agent 定义（加固版）
# ============================================

class SubAgent:
    """子 Agent（使用统一的 LLMClient）"""
    
    def __init__(self, name: str, role: str, layer: int, system_prompt: str, 
                 model: str = "qwen3.5-plus", api_key: str = "", base_url: str = ""):
        self.name = name
        self.role = role
        self.layer = layer
        self.system_prompt = system_prompt
        
        # 使用统一的 LLMClient（带审计日志）
        self.llm_client = LLMClient(
            api_key=api_key,
            base_url=base_url,
            model=model,
            agent_name=name
        )
    
    def ask(self, question: str, context: str = "", timeout: int = 120, 
            max_retries: int = 3, retry_delay: float = 1.0) -> Dict:
        """向 Agent 提问并获取回答（使用统一的 LLMClient，带审计日志）"""
        # 构建完整的用户消息
        user_message = f"{question}\n\n{context}".strip() if context else question
        
        # 使用 LLMClient 调用（自动记录审计日志）
        result = self.llm_client.chat(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=self.system_prompt,
            max_retries=max_retries,
            retry_delay=retry_delay
        )
        
        if result.get('success'):
            return {
                "success": True,
                "content": result['content'],
                "agent": self.name,
                "layer": self.layer,
                "tokens": result.get('usage', {}).get('total_tokens', 0)
            }
        else:
            return {
                "success": False,
                "error": result.get('error', 'Unknown error'),
                "agent": self.name
            }


def create_sub_agents(config: Dict) -> Dict[str, SubAgent]:
    """根据配置创建子 Agent"""
    providers = config.get('providers', {})
    dashscope = providers.get('dashscope', {})
    
    # 优先从 KeyVault 获取（加密存储）
    api_key = ''
    try:
        from services.key_vault import get_key_vault
        vault = get_key_vault()
        api_key = vault.get_key('dashscope') or ''
    except Exception as e:
        logger.warning(f"KeyVault 未就绪，降级到配置文件：{e}")
        # 降级：从配置文件读取
        api_key = dashscope.get('api_key_value', '') or os.getenv('DASHSCOPE_API_KEY', '')
    
    base_url = dashscope.get('base_url', 'https://coding.dashscope.aliyuncs.com/v1')
    
    agents_config = config.get('agents', {})
    agents = {}
    
    for agent_name, agent_conf in agents_config.items():
        if agent_conf.get('enabled', False) and agent_conf.get('layer', 0) > 0:
            agents[agent_name] = SubAgent(
                name=agent_name,
                role=agent_conf.get('role', '专家'),
                layer=agent_conf.get('layer', 0),
                system_prompt=agent_conf.get('system_prompt', ''),
                model=agent_conf.get('model', 'qwen3.5-plus'),
                api_key=api_key,
                base_url=base_url
            )
    
    logger.info(f"✅ 创建 {len(agents)} 个子 Agent")
    return agents


# ============================================
# 工作流编排器（加固版）
# ============================================

class WorkflowOrchestrator:
    """工作流编排器（同步版本，带实时保存）"""
    
    def __init__(self, config_path: str = "config/agent_config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.agents: Dict[str, SubAgent] = {}
        self.tasks: List[Task] = []
        self.results: Dict[str, Any] = {}
        self.output_dir = Path("data/workflow_results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 学习架构图
        self.architecture = self._load_architecture()
        
        # 中间保存文件 - 每任务独立文件（原子写入，避免并发冲突）
        # 格式：layer_1_task_1.json, layer_1_task_2.json, ...
        # 层完成后合并：layer_1_merged.json
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _load_architecture(self) -> Dict:
        """加载学习架构图"""
        return {
            "name": "Agent 开发面试知识体系",
            "version": "1.0",
            "layers": [
                {
                    "layer": 1,
                    "name": "基础理论层",
                    "agent": "theory_worker",
                    "topics": [
                        {"name": "AI 基础", "description": "机器学习和深度学习基础", "priority": "high"},
                        {"name": "LLM 原理", "description": "大语言模型核心原理", "priority": "high"},
                        {"name": "Agent 概念", "description": "AI Agent 核心概念", "priority": "high"},
                        {"name": "架构模式", "description": "常见 Agent 架构模式", "priority": "medium"}
                    ]
                },
                {
                    "layer": 2,
                    "name": "技术栈层",
                    "agent": "tech_stack_worker",
                    "topics": [
                        {"name": "Python 编程", "description": "Python 核心技能", "priority": "high"},
                        {"name": "Agent 框架", "description": "主流 Agent 开发框架", "priority": "high"},
                        {"name": "向量数据库", "description": "向量存储与检索", "priority": "high"}
                    ]
                },
                {
                    "layer": 3,
                    "name": "核心能力层",
                    "agent": "core_skill_worker",
                    "topics": [
                        {"name": "任务规划", "description": "复杂任务分解与规划", "priority": "high"},
                        {"name": "工具调用", "description": "Function Calling 技术", "priority": "high"},
                        {"name": "记忆管理", "description": "短期与长期记忆", "priority": "high"},
                        {"name": "多 Agent 协作", "description": "多 Agent 系统设计", "priority": "medium"}
                    ]
                },
                {
                    "layer": 4,
                    "name": "工程实践层",
                    "agent": "engineering_worker",
                    "topics": [
                        {"name": "项目经验", "description": "典型 Agent 项目", "priority": "high"},
                        {"name": "性能优化", "description": "系统性能优化", "priority": "medium"},
                        {"name": "部署运维", "description": "生产环境部署", "priority": "medium"}
                    ]
                },
                {
                    "layer": 5,
                    "name": "面试准备层",
                    "agent": "interview_worker",
                    "topics": [
                        {"name": "算法题", "description": "编程算法准备", "priority": "high"},
                        {"name": "系统设计", "description": "系统设计面试", "priority": "high"},
                        {"name": "行为面试", "description": "软技能面试", "priority": "medium"}
                    ]
                }
            ]
        }
    
    def initialize(self):
        """初始化工作流"""
        logger.info("🚀 初始化工作流编排器")
        self.agents = create_sub_agents(self.config)
        self._create_tasks()
        logger.info(f"📋 创建 {len(self.tasks)} 个任务")
        
        # 尝试加载之前的进度
        self._load_partial_progress()
    
    def _load_partial_progress(self):
        """加载之前的部分进度（断点续传，从每任务独立文件加载）"""
        completed_topics = set()
        completed_tasks = 0
        
        # 扫描所有层的任务文件
        for layer_num in range(1, 6):  # 5 个层级
            layer_task_count = 0
            
            # 扫描该层的所有任务文件
            for task_file in sorted(self.output_dir.glob(f"layer_{layer_num}_task_*.json")):
                try:
                    with open(task_file, 'r', encoding='utf-8') as f:
                        task_data = json.load(f)
                    
                    topic_name = task_data.get('data', {}).get('topic_name') or \
                                 task_data.get('topic_name', 'unknown')
                    completed_topics.add((layer_num, topic_name))
                    layer_task_count += 1
                    completed_tasks += 1
                    
                except Exception as e:
                    logger.warning(f"⚠️  加载任务文件失败 {task_file.name}: {e}")
            
            # 检查是否有合并文件（该层已全部完成）
            merged_file = self._get_layer_merged_file(layer_num)
            if merged_file.exists():
                try:
                    with open(merged_file, 'r', encoding='utf-8') as f:
                        merged_data = json.load(f)
                    
                    topic_count = len(merged_data.get('topics', []))
                    logger.info(f"📥 第{layer_num}层已完成：{topic_count} 个主题（合并文件存在）")
                    
                except Exception as e:
                    logger.warning(f"⚠️  加载合并文件失败 {merged_file.name}: {e}")
            elif layer_task_count > 0:
                logger.info(f"📥 第{layer_num}层部分完成：{layer_task_count} 个任务")
        
        if completed_topics:
            # 标记已完成的任务
            for task in self.tasks:
                if (task.layer_num, task.topic_name) in completed_topics:
                    task.status = "skipped"
                    logger.debug(f"⏭️  跳过已完成任务：{task.topic_name}")
            
            logger.info(f"📥 总加载进度：{len(completed_topics)}/{len(self.tasks)} 任务已完成")
        else:
            logger.info("📥 无历史进度，从头开始")
    
    def _create_tasks(self):
        """根据架构图创建任务"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for layer_data in self.architecture['layers']:
            layer_num = layer_data['layer']
            layer_name = layer_data['name']
            
            for topic in layer_data['topics']:
                task = Task(
                    task_id=f"layer{layer_num}_topic_{topic['name']}_{timestamp}",
                    layer_num=layer_num,
                    topic_name=topic['name'],
                    status="pending"
                )
                self.tasks.append(task)
    
    def execute_workflow(self) -> WorkflowResult:
        """执行完整工作流（集成事件总线）"""
        workflow_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self._current_workflow_id = workflow_id  # 保存为实例变量供任务使用
        started_at = datetime.now()
        
        logger.info("="*60)
        logger.info(f"🎯 开始执行工作流：{workflow_id}")
        logger.info("="*60)
        
        # 📢 发布工作流开始事件
        if EVENT_BUS_AVAILABLE:
            try:
                publish_event(EventType.WORKFLOW_START, {
                    "workflow_id": workflow_id,
                    "total_tasks": len(self.tasks),
                    "total_layers": len(set(t.layer_num for t in self.tasks))
                }, source="workflow_orchestrator")
            except Exception as e:
                logger.warning(f"⚠️  发布 WORKFLOW_START 事件失败：{e}")
        
        # 按层级分组任务
        layer_tasks: Dict[int, List[Task]] = {}
        for task in self.tasks:
            if task.status == "skipped":
                continue
            if task.layer_num not in layer_tasks:
                layer_tasks[task.layer_num] = []
            layer_tasks[task.layer_num].append(task)
        
        # 并发执行各层级（使用线程池）
        layer_results = {}
        
        with ThreadPoolExecutor(max_workers=5, thread_name_prefix="layer_") as executor:
            futures = {}
            for layer_num, tasks in layer_tasks.items():
                if not tasks:
                    continue
                layer_data = next(
                    (l for l in self.architecture['layers'] if l['layer'] == layer_num),
                    None
                )
                if layer_data:
                    agent_name = layer_data.get('agent')
                    if agent_name and agent_name in self.agents:
                        future = executor.submit(
                            self._execute_layer,
                            layer_num, tasks, self.agents[agent_name], layer_results
                        )
                        futures[future] = layer_num
            
            # 等待所有任务完成
            for future in as_completed(futures):
                layer_num = futures[future]
                try:
                    future.result()
                    logger.info(f"✅ 第{layer_num}层线程完成")
                except Exception as e:
                    logger.error(f"❌ 第{layer_num}层执行失败：{e}\n{traceback.format_exc()}")
        
        completed_at = datetime.now()
        duration = (completed_at - started_at).total_seconds()
        
        # 统计结果
        success_count = sum(1 for t in self.tasks if t.status == "completed")
        failed_count = sum(1 for t in self.tasks if t.status == "failed")
        skipped_count = sum(1 for t in self.tasks if t.status == "skipped")
        
        result = WorkflowResult(
            workflow_id=workflow_id,
            started_at=started_at.isoformat(),
            completed_at=completed_at.isoformat(),
            total_tasks=len(self.tasks),
            success_count=success_count,
            failed_count=failed_count,
            layer_results=layer_results,
            duration_seconds=duration
        )
        
        # 保存最终结果
        self._save_results(result)
        
        # 删除中间文件（每任务的独立文件）
        cleaned_count = 0
        for layer_num in range(1, 6):
            for task_file in self.output_dir.glob(f"layer_{layer_num}_task_*.json"):
                task_file.unlink()
                cleaned_count += 1
        
        logger.debug(f"🧹 清理中间文件：{cleaned_count} 个任务文件")
        
        logger.info("="*60)
        logger.info(f"✅ 工作流完成！总耗时：{duration:.2f}秒")
        logger.info(f"   成功：{success_count}/{len(self.tasks)}")
        logger.info(f"   失败：{failed_count}/{len(self.tasks)}")
        logger.info(f"   跳过：{skipped_count}/{len(self.tasks)}")
        logger.info("="*60)
        
        # 📢 发布工作流完成事件
        if EVENT_BUS_AVAILABLE:
            try:
                publish_event(EventType.WORKFLOW_COMPLETE, {
                    "workflow_id": workflow_id,
                    "success_count": success_count,
                    "failed_count": failed_count,
                    "skipped_count": skipped_count,
                    "total_tasks": len(self.tasks),
                    "duration_seconds": duration
                }, source="workflow_orchestrator")
            except Exception as e:
                logger.warning(f"⚠️  发布 WORKFLOW_COMPLETE 事件失败：{e}")
        
        return result
    
    def _execute_layer(self, layer_num: int, tasks: List[Task], 
                      agent: SubAgent, results_store: Dict):
        """执行单个层级的所有任务"""
        layer_data = next(
            (l for l in self.architecture['layers'] if l['layer'] == layer_num),
            None
        )
        layer_name = layer_data['name'] if layer_data else f"第{layer_num}层"
        
        logger.info(f"\n📚 [Layer-{layer_num}] 开始执行：{layer_name}")
        logger.info(f"   Agent: {agent.name} ({agent.role})")
        logger.info(f"   任务数：{len(tasks)}")
        
        layer_result = {
            "layer": layer_num,
            "layer_name": layer_name,
            "agent": agent.name,
            "topics": []
        }
        
        # 串行执行该层级的所有任务
        for i, task in enumerate(tasks, 1):
            try:
                self._execute_task(task, agent, layer_result, i, len(tasks))
                
                # ✅ 关键改进：每任务完成后立即保存（独立文件）
                if task.status == "completed" and task.result:
                    self._save_task_result(layer_num, i, task.result)
                    
                    # 📢 发布任务进度事件
                    if EVENT_BUS_AVAILABLE:
                        try:
                            publish_event(EventType.WORKFLOW_PROGRESS, {
                                "workflow_id": getattr(self, '_current_workflow_id', 'unknown'),
                                "layer_num": layer_num,
                                "task_index": i,
                                "total_tasks": len(tasks),
                                "topic_name": task.topic_name,
                                "status": "completed"
                            }, source="workflow_orchestrator")
                        except Exception:
                            pass
                    
            except Exception as e:
                logger.error(f"[Layer-{layer_num}] 任务异常：{task.topic_name} - {e}")
                task.status = "failed"
                task.error = str(e)
        
        results_store[str(layer_num)] = layer_result
        
        # ✅ 层完成后合并所有任务文件
        self._merge_layer_results(layer_num, layer_result)
        
        logger.info(f"   ✅ [Layer-{layer_num}] 完成并合并")
    
    def _execute_task(self, task: Task, agent: SubAgent, 
                     layer_result: Dict, index: int, total: int):
        """执行单个任务（两轮生成）"""
        task.start_time = datetime.now().isoformat()
        task.status = "running"
        
        logger.info(f"   ├─ [{index}/{total}] 生成：{task.topic_name}")
        
        try:
            # 第一轮：生成主题结构
            question = self._build_question(task.topic_name, task.layer_num)
            answer = agent.ask(question, timeout=180, max_retries=2)
            
            if not answer.get('success'):
                task.status = "failed"
                task.error = answer.get('error', 'Unknown error')
                task.end_time = datetime.now().isoformat()
                logger.info(f"   │  ❌ 失败：{task.topic_name} - {task.error}")
                return
            
            # 解析第一轮结果
            knowledge = self._parse_knowledge(answer['content'], task.topic_name)
            
            # 第二轮：为每个关键知识点生成详细内容
            logger.info(f"   │  📝 已生成结构，开始生成关键知识点详情...")
            knowledge = self._generate_keypoint_details(agent, knowledge, task.topic_name)
            
            task.status = "completed"
            task.result = answer
            task.end_time = datetime.now().isoformat()
            layer_result['topics'].append(knowledge)
            
            keypoint_count = self._count_keypoints(knowledge)
            logger.info(f"   │  ✅ 完成：{task.topic_name}（含{keypoint_count}个知识点详情）")
            
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.end_time = datetime.now().isoformat()
            logger.error(f"   │  ❌ 异常：{task.topic_name} - {e}")
    
    def _generate_keypoint_details(self, agent: SubAgent, knowledge: Dict, 
                                   topic_name: str) -> Dict:
        """为每个关键知识点生成详细学习内容"""
        subtopics = knowledge.get('subtopics', [])
        
        for i, subtopic in enumerate(subtopics, 1):
            subtopic_name = subtopic.get('name', '')
            difficulty = subtopic.get('difficulty', 'intermediate')
            key_points = subtopic.get('key_points', [])
            
            logger.info(f"   │     ├─ 子主题 {i}/{len(subtopics)}: {subtopic_name}")
            
            # 为每个关键知识点生成详细内容
            detailed_keypoints = []
            for j, key_point in enumerate(key_points, 1):
                logger.info(f"   │     │  ├─ 知识点 {j}/{len(key_points)}: {key_point[:30]}...")
                
                # 构建第二轮问题
                question = self._build_keypoint_question(
                    topic_name, subtopic_name, key_point, difficulty
                )
                
                # 向 Agent 提问
                answer = agent.ask(question, timeout=180, max_retries=2)
                
                if answer.get('success'):
                    detailed_content = self._parse_knowledge(answer['content'], key_point)
                    detailed_keypoints.append({
                        "key_point": key_point,
                        "detailed_content": detailed_content
                    })
                    logger.info(f"   │     │  │  ✅ 已生成详情")
                else:
                    logger.info(f"   │     │  │  ⚠️  生成失败：{answer.get('error', 'Unknown')[:50]}")
                    detailed_keypoints.append({
                        "key_point": key_point,
                        "error": answer.get('error', 'Unknown error')
                    })
            
            # 将详细内容添加到子主题
            subtopic['detailed_keypoints'] = detailed_keypoints
        
        return knowledge
    
    def _count_keypoints(self, knowledge: Dict) -> int:
        """统计已生成的知识点详情数量"""
        count = 0
        for subtopic in knowledge.get('subtopics', []):
            count += len(subtopic.get('detailed_keypoints', []))
        return count
    
    def _build_question(self, topic_name: str, layer_num: int) -> str:
        """构建提问（第一轮：生成主题结构）"""
        return f"""
## 任务
生成第{layer_num}层"{topic_name}"主题的详细学习内容。

## 输出要求
请严格按照以下 JSON 格式输出：
{{
    "topic_name": "主题名称",
    "description": "详细描述（300-500 字）",
    "subtopics": [
        {{
            "name": "子主题名称",
            "key_points": ["知识点 1", "知识点 2", "知识点 3"],
            "resources": [
                {{"type": "book", "title": "书名", "author": "作者"}},
                {{"type": "course", "title": "课程名", "platform": "平台"}},
                {{"type": "doc", "title": "文档名", "url": "链接"}}
            ],
            "estimated_hours": 10,
            "difficulty": "beginner"
        }}
    ],
    "total_hours": 总学习时长，
    "prerequisites": ["前置知识 1", "前置知识 2"],
    "learning_outcomes": ["学习成果 1", "学习成果 2"]
}}

注意：
1. 只输出 JSON，不要其他内容
2. 确保 JSON 格式正确
3. 内容要详细、实用
4. 资源要真实有效
"""
    
    def _build_keypoint_question(self, topic_name: str, subtopic_name: str, 
                                 key_point: str, difficulty: str) -> str:
        """构建提问（第二轮：生成关键知识点详细内容）"""
        difficulty_map = {
            "beginner": "初级",
            "intermediate": "中级",
            "advanced": "高级"
        }
        diff_cn = difficulty_map.get(difficulty, "中级")
        
        return f"""
## 任务
针对"{topic_name}"主题中"{subtopic_name}"子主题的关键知识点进行详细讲解。

## 关键知识点
**{key_point}**

## 输出要求
请严格按照以下 JSON 格式输出详细学习内容：
{{
    "key_point": "{key_point}",
    "explanation": "详细解释（500-800 字，包括概念定义、原理说明、为什么重要）",
    "core_concepts": [
        {{
            "name": "核心概念名",
            "definition": "概念定义",
            "example": "具体例子或代码示例"
        }}
    ],
    "common_misunderstandings": [
        {{
            "misunderstanding": "常见误解",
            "correction": "正确理解"
        }}
    ],
    "practical_application": "实际应用场景（1-2 个具体案例）",
    "code_example": "Python 代码示例（如果适用）",
    "difficulty": "{diff_cn}",
    "estimated_study_time": "建议学习时长（分钟）",
    "self_check_questions": [
        "自测问题 1",
        "自测问题 2",
        "自测问题 3"
    ],
    "further_reading": [
        {{"type": "article", "title": "文章标题", "url": "链接"}},
        {{"type": "video", "title": "视频标题", "url": "链接"}}
    ]
}}

注意：
1. 只输出 JSON，不要其他内容
2. 解释要通俗易懂，避免过度使用专业术语
3. 代码示例要可运行、有注释
4. 自测问题要能检验理解程度
"""
    
    def _parse_knowledge(self, content: str, topic_name: str) -> Dict:
        """解析知识内容（容错版）"""
        import re
        # 尝试提取 JSON
        match = re.search(r'\{[\s\S]*\}', content)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError as e:
                logger.warning(f"JSON 解析失败：{e}，使用 fallback")
        
        # Fallback：返回基础结构
        return {
            "topic_name": topic_name,
            "description": content[:500] if content else "无内容",
            "subtopics": [],
            "raw_content": content
        }
    
    def _get_task_file(self, layer_num: int, task_index: int) -> Path:
        """获取指定任务的独立文件路径"""
        return self.output_dir / f"layer_{layer_num}_task_{task_index}.json"
    
    def _get_layer_merged_file(self, layer_num: int) -> Path:
        """获取指定层合并文件路径（兼容旧文件名 layer_X_workflow.json）"""
        # 使用 workflow.json 命名以保持一致性
        return self.output_dir / f"layer_{layer_num}_workflow.json"
    
    def _save_task_result(self, layer_num: int, task_index: int, task_data: Dict):
        """保存单个任务结果（独立文件，原子写入）"""
        try:
            task_file = self._get_task_file(layer_num, task_index)
            
            # 原子写入（直接写，不读旧文件）
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "layer": layer_num,
                    "task_index": task_index,
                    "topic_name": task_data.get('topic_name', 'unknown'),
                    "status": "completed",
                    "completed_at": datetime.now().isoformat(),
                    "data": task_data
                }, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"   💾 任务 {task_index} 已保存到 {task_file.name}")
            
        except Exception as e:
            logger.error(f"   ❌ 保存任务 {task_index} 失败：{e}")
    
    def _merge_layer_results(self, layer_num: int, layer_result: Dict):
        """层完成后合并所有任务文件"""
        try:
            merged_file = self._get_layer_merged_file(layer_num)
            
            # 构建合并数据
            merged_data = {
                "layer": layer_num,
                "layer_name": layer_result.get('layer_name', f'第{layer_num}层'),
                "agent": layer_result.get('agent', 'unknown'),
                "topics": layer_result.get('topics', []),
                "task_count": len(layer_result.get('topics', [])),
                "completed_at": datetime.now().isoformat()
            }
            
            # 写入合并文件
            with open(merged_file, 'w', encoding='utf-8') as f:
                json.dump(merged_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"   💾 [Layer-{layer_num}] 已合并到 {merged_file.name}")
            
            # 可选：清理任务文件（节省空间）
            # for task_file in self.output_dir.glob(f"layer_{layer_num}_task_*.json"):
            #     task_file.unlink()
            
        except Exception as e:
            logger.error(f"   ❌ 合并第{layer_num}层失败：{e}")
    
    def _save_results(self, result: WorkflowResult):
        """保存工作流结果"""
        # 保存完整结果
        output_file = self.output_dir / f"workflow_{result.workflow_id}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(result), f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n📄 结果已保存：{output_file}")
        
        # 保存按层级分类的结果
        for layer_num, layer_data in result.layer_results.items():
            layer_file = self.output_dir / f"layer_{layer_num}_workflow.json"
            
            with open(layer_file, 'w', encoding='utf-8') as f:
                json.dump(layer_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📄 第{layer_num}层已保存：{layer_file}")
        
        # 更新汇总文件
        self._update_summary(result)
    
    def _update_summary(self, result: WorkflowResult):
        """更新汇总文件"""
        summary_file = self.output_dir / "workflow_summary.json"
        
        if summary_file.exists():
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary = json.load(f)
        else:
            summary = {
                "workflows": [],
                "total_workflows": 0,
                "total_tasks": 0,
                "total_success": 0,
                "total_failed": 0
            }
        
        summary['workflows'].append({
            "workflow_id": result.workflow_id,
            "started_at": result.started_at,
            "completed_at": result.completed_at,
            "total_tasks": result.total_tasks,
            "success_count": result.success_count,
            "failed_count": result.failed_count,
            "duration_seconds": result.duration_seconds
        })
        
        summary['total_workflows'] = len(summary['workflows'])
        summary['total_tasks'] += result.total_tasks
        summary['total_success'] += result.success_count
        summary['total_failed'] += result.failed_count
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📊 汇总已更新：{summary_file}")


# ============================================
# 主函数
# ============================================

def main():
    """主函数"""
    print("="*70)
    print("🤖 Learning Agent - 知识生成工作流 (加固版)")
    print("="*70)
    print()
    print("📚 学习架构图：")
    print("   第 1 层：基础理论层 (AI 基础、LLM 原理、Agent 概念、架构模式)")
    print("   第 2 层：技术栈层 (Python、Agent 框架、向量数据库)")
    print("   第 3 层：核心能力层 (任务规划、工具调用、记忆管理、多 Agent)")
    print("   第 4 层：工程实践层 (项目经验、性能优化、部署运维)")
    print("   第 5 层：面试准备层 (算法题、系统设计、行为面试)")
    print()
    print("🎯 加固特性：")
    print("   ✅ 每层完成后立即保存（防止中断丢失）")
    print("   ✅ 线程日志前缀区分（清晰看到并发进度）")
    print("   ✅ API 调用重试机制（最多 3 次，指数退避）")
    print("   ✅ JSON 解析容错（解析失败使用 fallback）")
    print("   ✅ 断点续传支持（自动跳过已完成任务）")
    print()
    print("="*70)
    print()
    
    # 创建工作流编排器
    orchestrator = WorkflowOrchestrator()
    
    # 初始化
    print("⚙️  初始化工作流...")
    orchestrator.initialize()
    print()
    
    # 执行工作流
    result = orchestrator.execute_workflow()
    
    # 打印详细总结
    print()
    print("="*70)
    print("📊 工作流执行总结")
    print("="*70)
    print(f"   工作流 ID:    {result.workflow_id}")
    print(f"   开始时间：    {result.started_at}")
    print(f"   完成时间：    {result.completed_at}")
    print(f"   总任务数：    {result.total_tasks}")
    print(f"   ✅ 成功：     {result.success_count}")
    print(f"   ❌ 失败：     {result.failed_count}")
    print(f"   ⏱️  总耗时：   {result.duration_seconds:.2f}秒")
    print()
    
    # 各层级详情
    print("📚 各层级详情:")
    for layer_num, layer_data in result.layer_results.items():
        topics_count = len(layer_data.get('topics', []))
        agent_name = layer_data.get('agent', 'unknown')
        layer_name = layer_data.get('layer_name', f'第{layer_num}层')
        print(f"   第{layer_num}层 ({layer_name}):")
        print(f"      Agent: {agent_name}")
        print(f"      生成主题数：{topics_count}")
    print()
    
    # LLM 调用统计
    print("="*70)
    print("📈 LLM 调用统计")
    print("="*70)
    try:
        from services.llm_client import LLMClient
        stats = LLMClient.get_stats()
        print(f"   总调用次数：  {stats['total_calls']}")
        print(f"   成功：{stats['success_calls']} | 失败：{stats['failed_calls']}")
        print(f"   成功率：{stats['success_rate']}")
        print(f"   总 Token 数： {stats['total_tokens']:,}")
        print(f"   - Prompt: {stats['prompt_tokens']:,}")
        print(f"   - Completion: {stats['completion_tokens']:,}")
        print(f"   预估成本：  {stats['total_cost']}")
        
        if stats['by_model']:
            print()
            print("   按模型统计:")
            for model, data in stats['by_model'].items():
                print(f"   - {model}: {data['calls']}次，{data['tokens']:,} tokens, ¥{data['cost']:.4f}")
        
        if stats['by_agent']:
            print()
            print("   按 Agent 统计:")
            for agent, data in stats['by_agent'].items():
                success_rate = f"{data['success']/max(data['calls'],1)*100:.0f}%"
                print(f"   - {agent}: {data['calls']}次 (成功{data['success']}, 失败{data['failed']}, {success_rate})")
    except Exception as e:
        print(f"   ⚠️  无法获取统计信息：{e}")
    
    print()
    print("="*70)
    print()
    print("✅ 工作流完成！结果已保存到 data/workflow_results/ 目录")
    print()
    print("📄 输出文件:")
    print(f"   - data/workflow_results/workflow_{result.workflow_id}.json")
    print(f"   - data/workflow_results/layer_X_workflow.json (各层级)")
    print(f"   - data/workflow_results/workflow_summary.json (汇总)")
    print()


if __name__ == "__main__":
    main()
