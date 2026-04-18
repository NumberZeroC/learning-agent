#!/usr/bin/env python3
"""
知识生成工作流编排器 (优化版 v2)

功能：
- 根据 KNOWLEDGE_FRAMEWORK 架构图定义工作流
- 使用 asyncio 实现任务级并发（层内并发）
- 子 Agent 调用大模型进行回答
- 工作流记录所有回答并保存

优化改进 v2：
- asyncio 替代线程池，更高效并发
- 层级顺序执行，层内任务并发
- 并发限制防止API限流
- 请求缓存减少重复调用
- 更好的进度显示
"""

import os
import sys
import json
import yaml
import asyncio
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
import logging
from logging.handlers import RotatingFileHandler
import traceback

from dotenv import load_dotenv

env_file = Path(__file__).parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

from services.llm_client import LLMClient

try:
    from utils.event_bus import publish_event, EventType

    EVENT_BUS_AVAILABLE = True
except Exception:
    EVENT_BUS_AVAILABLE = False


def _setup_logger():
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)

    logger = logging.getLogger("workflow")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(console)

    file = RotatingFileHandler(
        log_dir / "workflow.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    file.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file)

    return logger


logger = _setup_logger()


@dataclass
class Task:
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
    workflow_id: str
    started_at: str
    completed_at: str
    total_tasks: int
    success_count: int
    failed_count: int
    layer_results: Dict[str, Any]
    duration_seconds: float


class AsyncSubAgent:
    """异步子 Agent"""

    def __init__(
        self,
        name: str,
        role: str,
        layer: int,
        system_prompt: str,
        model: str = "qwen-plus",
        api_key: str = "",
        base_url: str = "",
        enable_cache: bool = True,
    ):
        self.name = name
        self.role = role
        self.layer = layer
        self.system_prompt = system_prompt

        self.llm_client = LLMClient(
            api_key=api_key,
            base_url=base_url,
            model=model,
            agent_name=name,
            enable_cache=enable_cache,
        )

    async def ask(self, question: str, max_retries: int = 2) -> Dict:
        user_message = question

        result = await self.llm_client.async_chat(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=self.system_prompt,
            max_retries=max_retries,
        )

        if result.get("success"):
            return {
                "success": True,
                "content": result["content"],
                "agent": self.name,
                "layer": self.layer,
                "tokens": result.get("usage", {}).get("total_tokens", 0),
                "cached": result.get("cached", False),
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Unknown error"),
                "agent": self.name,
            }

    async def close(self):
        await self.llm_client.async_close()


def create_sub_agents(
    config: Dict, enable_cache: bool = True
) -> Dict[str, AsyncSubAgent]:
    providers = config.get("providers", {})
    dashscope = providers.get("dashscope", {})

    api_key = ""
    try:
        from services.key_vault import get_key_vault

        vault = get_key_vault()
        api_key = vault.get_key("dashscope")
        if not api_key:
            raise ValueError("Key Vault 中未找到 API Key")
    except Exception:
        api_key = dashscope.get("api_key_value", "") or os.getenv(
            "DASHSCOPE_API_KEY", ""
        )

    base_url = dashscope.get("base_url", "https://coding.dashscope.aliyuncs.com/v1")

    agents_config = config.get("agents", {})
    agents = {}

    for agent_name, agent_conf in agents_config.items():
        if agent_conf.get("enabled", False) and agent_conf.get("layer", 0) > 0:
            agents[agent_name] = AsyncSubAgent(
                name=agent_name,
                role=agent_conf.get("role", "专家"),
                layer=agent_conf.get("layer", 0),
                system_prompt=agent_conf.get("system_prompt", ""),
                model=agent_conf.get("model", "qwen-plus"),
                api_key=api_key,
                base_url=base_url,
                enable_cache=enable_cache,
            )

    logger.info(f"✅ 创建 {len(agents)} 个异步子 Agent")
    return agents


class WorkflowOrchestrator:
    """工作流编排器（asyncio 版本）"""

    MAX_CONCURRENT_TASKS = 3

    def __init__(
        self,
        config_path: str = "config/agent_config.yaml",
        framework_path: str = "config/knowledge_framework.yaml",
        max_concurrent: int = 1,  # 暂停层内并发，避免 API 限流（2026-04-18）
        enable_cache: bool = True,
        auto_generate_framework: bool = True,
    ):
        self.config_path = Path(config_path)
        self.framework_path = Path(framework_path)
        self.config = self._load_config()
        self.agents: Dict[str, AsyncSubAgent] = {}
        self.tasks: List[Task] = []
        self.results: Dict[str, Any] = {}
        self.output_dir = Path("data/workflow_results")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 加载或生成知识架构
        self.architecture = self._load_or_generate_architecture(auto_generate_framework)
        self.max_concurrent = max_concurrent
        self.enable_cache = enable_cache
        self._current_workflow_id = ""

    def _load_config(self) -> Dict:
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _load_or_generate_architecture(self, auto_generate: bool = True) -> Dict:
        """加载知识架构，如果不存在则自动生成"""
        if self.framework_path.exists():
            logger.info(f"📐 从配置文件加载知识架构：{self.framework_path}")
            return self._load_architecture_from_file()
        elif auto_generate:
            logger.warning("⚠️  知识架构配置文件不存在，开始自动生成...")
            return self._generate_architecture()
        else:
            logger.error("❌ 知识架构配置文件不存在且未启用自动生成")
            raise FileNotFoundError(f"知识架构配置文件不存在：{self.framework_path}")

    def _load_architecture_from_file(self) -> Dict:
        """从 YAML 文件加载知识架构"""
        with open(self.framework_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        logger.info(f"✅ 成功加载知识架构：{data.get('name', 'Unknown')} v{data.get('version', '1.0')}")
        logger.info(f"   层级数：{len(data.get('layers', []))}")
        
        # 转换为内部格式
        return {
            "name": data.get("name", "Agent 开发面试知识体系"),
            "version": data.get("version", "1.0"),
            "layers": data.get("layers", [])
        }

    def _generate_architecture(self) -> Dict:
        """调用大模型生成知识架构"""
        logger.info("🤖 调用大模型生成知识架构...")
        
        # 创建临时 Agent 用于生成架构
        from services.llm_client import LLMClient
        
        # 获取 API Key
        try:
            from services.key_vault import get_key_vault
            vault = get_key_vault()
            api_key = vault.get_key("dashscope") or ""
        except Exception:
            api_key = self.config.get("providers", {}).get("dashscope", {}).get("api_key_value", "") or os.getenv("DASHSCOPE_API_KEY", "")
        
        base_url = self.config.get("providers", {}).get("dashscope", {}).get("base_url", "https://coding.dashscope.aliyuncs.com/v1")
        
        llm = LLMClient(
            api_key=api_key,
            base_url=base_url,
            model="qwen3.5-plus",
            agent_name="framework_generator",
            enable_cache=False
        )
        
        # 生成提示词
        system_prompt = """你是 AI 教育专家和知识架构师，擅长设计系统化的学习路径。

请为"AI Agent 开发岗位面试"设计一个完整的知识体系架构。

## 要求
1. **严格分为 5 个层级**（必须按顺序）：
   - 第 1 层：基础理论层（机器学习、深度学习基础）
   - 第 2 层：技术栈层（Python、框架、工具）
   - 第 3 层：核心能力层（任务规划、工具调用、记忆、多 Agent）
   - 第 4 层：工程实践层（项目、优化、部署）
   - 第 5 层：面试准备层（算法题、系统设计、行为面试）

2. **每层 3-4 个主题**，每个主题包含：
   - name: 主题名称（简洁，2-6 字）
   - description: 主题描述（15-30 字）
   - priority: 优先级（high/medium）
   - subtopics: 2-4 个子主题（列表）

3. **输出格式**：严格的 YAML 格式，可直接保存到配置文件

## 输出示例
```yaml
name: Agent 开发面试知识体系
version: "1.0"
description: AI Agent 开发岗位面试知识体系
layers:
  - layer: 1
    name: 基础理论层
    agent: theory_worker
    topics:
      - name: 主题名
        description: 描述
        priority: high
        subtopics:
          - 子主题 1
          - 子主题 2
```

请生成完整的知识架构 YAML。"""

        user_prompt = "请生成 AI Agent 开发面试的完整知识体系架构，分为 5 个层级，每层 3-4 个主题。"
        
        try:
            import asyncio
            
            async def generate():
                result = await llm.async_chat(
                    messages=[{"role": "user", "content": user_prompt}],
                    system_prompt=system_prompt,
                    max_retries=2
                )
                return result
            
            # 运行异步调用
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(generate())
            
            if result.get("success"):
                content = result.get("content", "")
                logger.info("✅ 大模型生成成功，解析 YAML...")
                
                # 提取 YAML 内容（移除可能的 markdown 代码块标记）
                yaml_content = content
                if "```yaml" in content:
                    yaml_content = content.split("```yaml")[1].split("```")[0]
                elif "```" in content:
                    yaml_content = content.split("```")[1].split("```")[0]
                
                # 解析 YAML
                data = yaml.safe_load(yaml_content)
                
                # 保存到配置文件
                self.framework_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.framework_path, "w", encoding="utf-8") as f:
                    f.write("# AI Agent 开发面试知识体系架构\n")
                    f.write(f"# 自动生成时间：{datetime.now().isoformat()}\n")
                    f.write(f"# 生成模型：qwen3.5-plus\n\n")
                    yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
                
                logger.info(f"📄 知识架构已保存到：{self.framework_path}")
                
                return {
                    "name": data.get("name", "Agent 开发面试知识体系"),
                    "version": data.get("version", "1.0"),
                    "layers": data.get("layers", [])
                }
            else:
                logger.error(f"❌ 大模型调用失败：{result.get('error')}")
                raise RuntimeError(f"知识架构生成失败：{result.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ 知识架构生成异常：{e}")
            # 降级：使用默认架构
            logger.warning("⚠️  使用默认知识架构")
            return self._get_default_architecture()

    def _get_default_architecture(self) -> Dict:
        """返回默认知识架构（降级方案）"""
        return {
            "name": "Agent 开发面试知识体系",
            "version": "1.0",
            "layers": [
                {
                    "layer": 1,
                    "name": "基础理论层",
                    "agent": "theory_worker",
                    "topics": [
                        {
                            "name": "AI 基础",
                            "description": "机器学习和深度学习基础",
                            "priority": "high",
                        },
                        {
                            "name": "LLM 原理",
                            "description": "大语言模型核心原理",
                            "priority": "high",
                        },
                        {
                            "name": "Agent 概念",
                            "description": "AI Agent 核心概念",
                            "priority": "high",
                        },
                        {
                            "name": "架构模式",
                            "description": "常见 Agent 架构模式",
                            "priority": "medium",
                        },
                    ],
                },
                {
                    "layer": 2,
                    "name": "技术栈层",
                    "agent": "tech_stack_worker",
                    "topics": [
                        {
                            "name": "Python 编程",
                            "description": "Python 核心技能",
                            "priority": "high",
                        },
                        {
                            "name": "Agent 框架",
                            "description": "主流 Agent 开发框架",
                            "priority": "high",
                        },
                        {
                            "name": "向量数据库",
                            "description": "向量存储与检索",
                            "priority": "high",
                        },
                    ],
                },
                {
                    "layer": 3,
                    "name": "核心能力层",
                    "agent": "core_skill_worker",
                    "topics": [
                        {
                            "name": "任务规划",
                            "description": "复杂任务分解与规划",
                            "priority": "high",
                        },
                        {
                            "name": "工具调用",
                            "description": "Function Calling 技术",
                            "priority": "high",
                        },
                        {
                            "name": "记忆管理",
                            "description": "短期与长期记忆",
                            "priority": "high",
                        },
                        {
                            "name": "多 Agent 协作",
                            "description": "多 Agent 系统设计",
                            "priority": "medium",
                        },
                    ],
                },
                {
                    "layer": 4,
                    "name": "工程实践层",
                    "agent": "engineering_worker",
                    "topics": [
                        {
                            "name": "项目经验",
                            "description": "典型 Agent 项目",
                            "priority": "high",
                        },
                        {
                            "name": "性能优化",
                            "description": "系统性能优化",
                            "priority": "medium",
                        },
                        {
                            "name": "部署运维",
                            "description": "生产环境部署",
                            "priority": "medium",
                        },
                    ],
                },
                {
                    "layer": 5,
                    "name": "面试准备层",
                    "agent": "interview_worker",
                    "topics": [
                        {
                            "name": "算法题",
                            "description": "编程算法准备",
                            "priority": "high",
                        },
                        {
                            "name": "系统设计",
                            "description": "系统设计面试",
                            "priority": "high",
                        },
                        {
                            "name": "行为面试",
                            "description": "软技能面试",
                            "priority": "medium",
                        },
                    ],
                },
            ],
        }

    def initialize(self):
        """初始化工作流"""
        logger.info("🚀 初始化工作流编排器（asyncio 版）")
        self.agents = create_sub_agents(self.config, self.enable_cache)
        self._create_tasks()
        logger.info(f"📋 创建 {len(self.tasks)} 个任务")
        self._load_partial_progress()

    async def async_initialize(self):
        """异步初始化"""
        self.initialize()

    def _load_partial_progress(self):
        """加载之前的部分进度（断点续传，从每任务独立文件加载）"""
        completed_topics = set()
        completed_tasks = 0

        # 扫描所有层的任务文件
        for layer_num in range(1, 6):  # 5 个层级
            layer_task_count = 0

            # 扫描该层的所有任务文件
            for task_file in sorted(
                self.output_dir.glob(f"layer_{layer_num}_task_*.json")
            ):
                try:
                    with open(task_file, "r", encoding="utf-8") as f:
                        task_data = json.load(f)

                    topic_name = task_data.get("data", {}).get(
                        "topic_name"
                    ) or task_data.get("topic_name", "unknown")
                    completed_topics.add((layer_num, topic_name))
                    layer_task_count += 1
                    completed_tasks += 1

                except Exception as e:
                    logger.warning(f"⚠️  加载任务文件失败 {task_file.name}: {e}")

            # 检查是否有合并文件（该层已全部完成）
            merged_file = self._get_layer_merged_file(layer_num)
            if merged_file.exists():
                try:
                    with open(merged_file, "r", encoding="utf-8") as f:
                        merged_data = json.load(f)

                    topic_count = len(merged_data.get("topics", []))
                    logger.info(
                        f"📥 第{layer_num}层已完成：{topic_count} 个主题（合并文件存在）"
                    )

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

            logger.info(
                f"📥 总加载进度：{len(completed_topics)}/{len(self.tasks)} 任务已完成"
            )
        else:
            logger.info("📥 无历史进度，从头开始")

    def _create_tasks(self):
        """根据架构图创建任务"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for layer_data in self.architecture["layers"]:
            layer_num = layer_data["layer"]
            layer_name = layer_data["name"]

            for topic in layer_data["topics"]:
                task = Task(
                    task_id=f"layer{layer_num}_topic_{topic['name']}_{timestamp}",
                    layer_num=layer_num,
                    topic_name=topic["name"],
                    status="pending",
                )
                self.tasks.append(task)

    def execute_workflow(self) -> WorkflowResult:
        """执行工作流（同步入口，内部使用asyncio，兼容Python 3.6）"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, self._async_execute_workflow())
                return future.result()
        else:
            return loop.run_until_complete(self._async_execute_workflow())

    async def _async_execute_workflow(self) -> WorkflowResult:
        """异步执行完整工作流"""
        workflow_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._current_workflow_id = workflow_id
        started_at = datetime.now()

        logger.info("=" * 60)
        logger.info(f"🎯 开始执行工作流：{workflow_id} (asyncio并发)")
        logger.info("=" * 60)

        if EVENT_BUS_AVAILABLE:
            try:
                publish_event(
                    EventType.WORKFLOW_START,
                    {
                        "workflow_id": workflow_id,
                        "total_tasks": len(self.tasks),
                        "concurrency": self.max_concurrent,
                    },
                    source="workflow_orchestrator",
                )
            except Exception:
                pass

        layer_tasks: Dict[int, List[Task]] = {}
        for task in self.tasks:
            if task.status == "skipped":
                continue
            if task.layer_num not in layer_tasks:
                layer_tasks[task.layer_num] = []
            layer_tasks[task.layer_num].append(task)

        layer_results = {}

        # ============================================
        # 🚀 关键改动：5 个 Agent 层间并发执行
        # ============================================
        # 准备所有层的 coroutine
        layer_coroutines = []
        layer_info_list = []  # 保存 (layer_num, layer_name) 用于后续处理

        for layer_num in sorted(layer_tasks.keys()):
            tasks = layer_tasks[layer_num]
            if not tasks:
                continue

            layer_data = next(
                (l for l in self.architecture["layers"] if l["layer"] == layer_num),
                None,
            )
            if not layer_data:
                continue

            agent_name = layer_data.get("agent")
            if not agent_name or agent_name not in self.agents:
                continue

            agent = self.agents[agent_name]
            layer_name = layer_data.get("name", f"第{layer_num}层")

            logger.info(
                f"\n📚 [Layer-{layer_num}] {layer_name} - {len(tasks)}任务 (并发={self.max_concurrent})"
            )

            # 收集 coroutine，不立即 await
            layer_coroutines.append(
                self._async_execute_layer(layer_num, tasks, agent, layer_name)
            )
            layer_info_list.append((layer_num, layer_name))

        # ✅ 5 层并发执行（5 个 Agent 同时工作）
        logger.info("\n" + "=" * 60)
        logger.info(f"🔥 启动层间并发：{len(layer_coroutines)} 层同时执行")
        logger.info("=" * 60)

        layer_results_list = await asyncio.gather(
            *layer_coroutines, return_exceptions=True
        )

        # 处理结果
        for i, layer_result in enumerate(layer_results_list):
            layer_num, layer_name = layer_info_list[i]
            if isinstance(layer_result, Exception):
                logger.error(f"❌ [Layer-{layer_num}] 执行异常：{layer_result}")
            else:
                layer_results[str(layer_num)] = layer_result
                self._merge_layer_results(layer_num, layer_result)
                logger.info(f"   ✅ [Layer-{layer_num}] 完成")

        completed_at = datetime.now()
        duration = (completed_at - started_at).total_seconds()

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
            duration_seconds=duration,
        )

        self._save_results(result)
        self._cleanup_temp_files()

        logger.info("=" * 60)
        logger.info(f"✅ 工作流完成！耗时：{duration:.2f}秒")
        logger.info(
            f"   成功：{success_count} | 失败：{failed_count} | 跳过：{skipped_count}"
        )
        logger.info("=" * 60)

        if EVENT_BUS_AVAILABLE:
            try:
                publish_event(
                    EventType.WORKFLOW_COMPLETE,
                    {
                        "workflow_id": workflow_id,
                        "success_count": success_count,
                        "failed_count": failed_count,
                        "duration_seconds": duration,
                    },
                    source="workflow_orchestrator",
                )
            except Exception:
                pass

        await self._close_agents()
        return result

    async def _async_execute_layer(
        self, layer_num: int, tasks: List[Task], agent: AsyncSubAgent, layer_name: str
    ) -> Dict:
        """异步执行单层任务（并发）"""
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def run_task_with_semaphore(task: Task, index: int):
            async with semaphore:
                return await self._async_execute_task(task, agent, index, len(tasks))

        results = await asyncio.gather(
            *[run_task_with_semaphore(task, i) for i, task in enumerate(tasks, 1)],
            return_exceptions=True,
        )

        layer_result = {
            "layer": layer_num,
            "layer_name": layer_name,
            "agent": agent.name,
            "topics": [],
        }

        for i, result in enumerate(results):
            task = tasks[i]
            if isinstance(result, Exception):
                task.status = "failed"
                task.error = str(result)
                logger.error(f"   ❌ [{i + 1}] {task.topic_name}: {result}")
            elif result.get("success"):
                task.status = "completed"
                task.result = result
                # 直接使用返回的 knowledge（包含详细内容）
                knowledge = result.get("knowledge")
                if not knowledge:
                    # 降级：如果没有 knowledge 字段，尝试解析 content
                    knowledge = self._parse_knowledge(
                        result.get("content", ""), task.topic_name
                    )
                layer_result["topics"].append(knowledge)
                self._save_task_result(layer_num, i + 1, knowledge)

                if EVENT_BUS_AVAILABLE:
                    try:
                        publish_event(
                            EventType.WORKFLOW_PROGRESS,
                            {
                                "workflow_id": self._current_workflow_id,
                                "layer_num": layer_num,
                                "task_index": i + 1,
                                "topic_name": task.topic_name,
                                "status": "completed",
                                "keypoints_count": self._count_keypoints(knowledge),
                            },
                            source="workflow_orchestrator",
                        )
                    except Exception:
                        pass
            else:
                task.status = "failed"
                task.error = result.get("error", "Unknown")
                logger.error(f"   ❌ [{i + 1}] {task.topic_name}: {task.error}")

        return layer_result

    async def _async_execute_task(
        self, task: Task, agent: AsyncSubAgent, index: int, total: int
    ) -> Dict:
        """异步执行单个任务（两轮生成）"""
        task.start_time = datetime.now().isoformat()
        task.status = "running"

        logger.info(f"   [{index}/{total}] 生成：{task.topic_name}")

        try:
            # 第一轮：生成主题结构
            question = self._build_question(task.topic_name, task.layer_num)
            answer = await agent.ask(question, max_retries=2)

            if not answer.get("success"):
                task.status = "failed"
                task.error = answer.get("error", "Unknown")
                task.end_time = datetime.now().isoformat()
                return answer

            # 解析第一轮结果
            knowledge = self._parse_knowledge(answer.get("content", ""), task.topic_name)

            # 第二轮：为每个关键知识点生成详细内容
            logger.info(f"   [{index}/{total}] 📝 已生成结构，开始生成关键知识点详情...")
            knowledge = await self._generate_keypoint_details_async(
                agent, knowledge, task.topic_name
            )

            task.status = "completed"
            task.result = answer
            task.end_time = datetime.now().isoformat()
            keypoint_count = self._count_keypoints(knowledge)
            logger.info(
                f"   [{index}/{total}] ✅ {task.topic_name}（含{keypoint_count}个知识点详情）"
            )

            # 返回包含详细内容的 knowledge
            return {
                "success": True,
                "content": json.dumps(knowledge, ensure_ascii=False),
                "knowledge": knowledge,
                "agent": agent.name,
                "layer": task.layer_num,
            }
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.end_time = datetime.now().isoformat()
            logger.error(f"   [{index}/{total}] ❌ 异常：{task.topic_name} - {e}")
            return {"success": False, "error": str(e), "agent": agent.name}

    async def _close_agents(self):
        """关闭所有Agent的连接"""
        for agent in self.agents.values():
            try:
                await agent.close()
            except Exception:
                pass

    def _cleanup_temp_files(self):
        """清理临时文件"""
        cleaned = 0
        for layer_num in range(1, 6):
            for task_file in self.output_dir.glob(f"layer_{layer_num}_task_*.json"):
                task_file.unlink()
                cleaned += 1
        logger.debug(f"🧹 清理临时文件：{cleaned}个")

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

    def _build_keypoint_question(
        self, topic_name: str, subtopic_name: str, key_point: str, difficulty: str
    ) -> str:
        """构建提问（第二轮：生成关键知识点详细内容）"""
        difficulty_map = {
            "beginner": "初级",
            "intermediate": "中级",
            "advanced": "高级",
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

    async def _generate_keypoint_details_async(
        self, agent: AsyncSubAgent, knowledge: Dict, topic_name: str
    ) -> Dict:
        """为每个关键知识点生成详细学习内容（异步版本）"""
        subtopics = knowledge.get("subtopics", [])

        for i, subtopic in enumerate(subtopics, 1):
            subtopic_name = subtopic.get("name", "")
            difficulty = subtopic.get("difficulty", "intermediate")
            key_points = subtopic.get("key_points", [])

            if not key_points:
                continue

            logger.info(f"       ├─ 子主题 {i}/{len(subtopics)}: {subtopic_name}")

            # 为每个关键知识点生成详细内容
            detailed_keypoints = []
            for j, key_point in enumerate(key_points, 1):
                logger.info(
                    f"           ├─ 知识点 {j}/{len(key_points)}: {key_point[:30]}..."
                )

                # 构建第二轮问题
                question = self._build_keypoint_question(
                    topic_name, subtopic_name, key_point, difficulty
                )

                # 向 Agent 提问（异步）
                answer = await agent.ask(question, max_retries=2)

                if answer.get("success"):
                    detailed_content = self._parse_knowledge(
                        answer.get("content", ""), key_point
                    )
                    detailed_keypoints.append(
                        {"key_point": key_point, "detailed_content": detailed_content}
                    )
                    logger.info(f"               ✅ 已生成详情")
                else:
                    logger.warning(
                        f"               ⚠️  生成失败：{answer.get('error', 'Unknown')[:50]}"
                    )
                    detailed_keypoints.append(
                        {
                            "key_point": key_point,
                            "error": answer.get("error", "Unknown error"),
                        }
                    )

            # 将详细内容添加到子主题
            subtopic["detailed_keypoints"] = detailed_keypoints

        return knowledge

    def _count_keypoints(self, knowledge: Dict) -> int:
        """统计已生成的知识点详情数量"""
        count = 0
        for subtopic in knowledge.get("subtopics", []):
            count += len(subtopic.get("detailed_keypoints", []))
        return count

    def _parse_knowledge(self, content: str, topic_name: str) -> Dict:
        """解析知识内容（容错版）"""
        import re

        match = re.search(r"\{[\s\S]*\}", content)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError as e:
                logger.warning(f"JSON 解析失败：{e}")

        return {
            "topic_name": topic_name,
            "description": content[:500] if content else "无内容",
            "subtopics": [],
            "raw_content": content,
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
            with open(task_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "layer": layer_num,
                        "task_index": task_index,
                        "topic_name": task_data.get("topic_name", "unknown"),
                        "status": "completed",
                        "completed_at": datetime.now().isoformat(),
                        "data": task_data,
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )

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
                "layer_name": layer_result.get("layer_name", f"第{layer_num}层"),
                "agent": layer_result.get("agent", "unknown"),
                "topics": layer_result.get("topics", []),
                "task_count": len(layer_result.get("topics", [])),
                "completed_at": datetime.now().isoformat(),
            }

            # 写入合并文件
            with open(merged_file, "w", encoding="utf-8") as f:
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

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(asdict(result), f, ensure_ascii=False, indent=2)

        logger.info(f"\n📄 结果已保存：{output_file}")

        # 保存按层级分类的结果
        for layer_num, layer_data in result.layer_results.items():
            layer_file = self.output_dir / f"layer_{layer_num}_workflow.json"

            with open(layer_file, "w", encoding="utf-8") as f:
                json.dump(layer_data, f, ensure_ascii=False, indent=2)

            logger.info(f"📄 第{layer_num}层已保存：{layer_file}")

        # 更新汇总文件
        self._update_summary(result)
        
        # 清除 Web 前端缓存（通知 Web 服务刷新数据）
        self._clear_web_cache()

    def _update_summary(self, result: WorkflowResult):
        """更新汇总文件"""
        summary_file = self.output_dir / "workflow_summary.json"

        if summary_file.exists():
            with open(summary_file, "r", encoding="utf-8") as f:
                summary = json.load(f)
        else:
            summary = {
                "workflows": [],
                "total_workflows": 0,
                "total_tasks": 0,
                "total_success": 0,
                "total_failed": 0,
            }

        summary["workflows"].append(
            {
                "workflow_id": result.workflow_id,
                "started_at": result.started_at,
                "completed_at": result.completed_at,
                "total_tasks": result.total_tasks,
                "success_count": result.success_count,
                "failed_count": result.failed_count,
                "duration_seconds": result.duration_seconds,
            }
        )

        summary["total_workflows"] = len(summary["workflows"])
        summary["total_tasks"] += result.total_tasks
        summary["total_success"] += result.success_count
        summary["total_failed"] += result.failed_count

        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        logger.info(f"📊 汇总已更新：{summary_file}")

    def _clear_web_cache(self):
        """清除 Web 前端缓存"""
        try:
            import urllib.request
            import json
            
            # 尝试调用 Web 服务的清除缓存 API
            web_url = "http://127.0.0.1:5001/api/workflow/cache/clear"
            
            req = urllib.request.Request(
                web_url,
                data=b'',
                method='POST',
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode('utf-8'))
                logger.info(f"🔄 Web 缓存已清除：{result.get('message', '')}")
        except Exception as e:
            # 缓存清除失败不影响主流程，只记录日志
            logger.warning(f"⚠️ 清除 Web 缓存失败（Web 服务可能未运行）: {e}")


# ============================================
# 主函数
# ============================================


def main():
    """主函数"""
    from dotenv import load_dotenv
    from pathlib import Path

    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)

    print("=" * 70)
    print("Learning Agent - 知识生成工作流 (asyncio优化版)")
    print("=" * 70)
    print()
    print("学习架构图：")
    print("   第 1 层：基础理论层 (AI 基础、LLM 原理、Agent 概念、架构模式)")
    print("   第 2 层：技术栈层 (Python、Agent 框架、向量数据库)")
    print("   第 3 层：核心能力层 (任务规划、工具调用、记忆管理、多 Agent)")
    print("   第 4 层：工程实践层 (项目经验、性能优化、部署运维)")
    print("   第 5 层：面试准备层 (算法题、系统设计、行为面试)")
    print()
    print("优化特性：")
    print("   asyncio并发（层内任务并发执行）")
    print("   httpx异步HTTP请求")
    print("   请求缓存（相同prompt跳过重复调用）")
    print("   断点续传（自动跳过已完成任务）")
    print()
    print("=" * 70)
    print()

    orchestrator = WorkflowOrchestrator(max_concurrent=1, enable_cache=True)  # 暂停层内并发，避免 API 限流

    print("初始化工作流...")
    orchestrator.initialize()
    print()

    print("执行工作流...")
    result = orchestrator.execute_workflow()

    print()
    print("=" * 70)
    print("工作流执行总结")
    print("=" * 70)
    print(f"   工作流 ID: {result.workflow_id}")
    print(f"   开始时间：{result.started_at}")
    print(f"   完成时间：{result.completed_at}")
    print(f"   总任务数：{result.total_tasks}")
    print(f"   成功：{result.success_count}")
    print(f"   失败：{result.failed_count}")
    print(f"   耗时：{result.duration_seconds:.2f}秒")
    print()

    print("各层级详情:")
    for layer_num, layer_data in result.layer_results.items():
        topics_count = len(layer_data.get("topics", []))
        agent_name = layer_data.get("agent", "unknown")
        layer_name = layer_data.get("layer_name", f"第{layer_num}层")
        print(
            f"   第{layer_num}层 ({layer_name}): Agent={agent_name}, 主题={topics_count}"
        )
    print()

    try:
        LLMClient.print_stats()
    except Exception as e:
        print(f"统计信息获取失败：{e}")

    print()
    print("=" * 70)
    print()
    print("工作流完成！结果已保存到 data/workflow_results/ 目录")
    print(f"   - data/workflow_results/workflow_{result.workflow_id}.json")
    print(f"   - data/workflow_results/layer_X_workflow.json")
    print(f"   - data/workflow_results/workflow_summary.json")
    print()


if __name__ == "__main__":
    main()
