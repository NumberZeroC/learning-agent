"""
Agent 自主执行循环 - ReAct 模式（增强版）

实现完整的 "思考→行动→观察→再思考→再行动" 循环
新增功能：
- 上下文窗口智能压缩
- 工具结果智能摘要
- 错误自动恢复机制
- 跨会话记忆支持
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import click
import structlog

from ..models.messages import Message
from .context_manager import ContextManager, SessionMemory
from .error_recovery import ErrorRecovery, RetryConfig, FallbackChain, DEFAULT_FALLBACK_CHAINS

if TYPE_CHECKING:
    from ..llm.base import LLMProvider
    from ..tools.registry import ToolRegistry
    from ..tools.base import ToolContext

logger = structlog.get_logger(__name__)


class AgentLoop:
    """
    增强版 Agent 自主执行循环
    
    新增能力：
    1. 上下文窗口管理 - 自动压缩超出限制的消息
    2. 智能摘要 - 工具结果自动摘要，保留关键信息
    3. 错误恢复 - 自动重试 + 替代方案
    4. 记忆系统 - 跨会话记忆用户偏好和项目上下文
    """
    
    def __init__(
        self,
        llm: LLMProvider,
        registry: ToolRegistry,
        context: ToolContext,
        max_iterations: int = 20,
        max_context_tokens: int = 100000,
        enable_memory: bool = True,
    ):
        self.llm = llm
        self.registry = registry
        self.context = context
        self.max_iterations = max_iterations
        self.tools = registry.get_definitions()
        
        # 新增：上下文管理器
        self.context_manager = ContextManager(max_tokens=max_context_tokens)
        
        # 新增：错误恢复系统
        self.error_recovery = ErrorRecovery(config=RetryConfig(
            max_retries=3,
            initial_delay=1.0,
            max_delay=30.0,
            exponential_base=2.0,
            jitter=True
        ))
        
        # 新增：降级链
        self.fallback_chain = FallbackChain()
        for primary, fallbacks in DEFAULT_FALLBACK_CHAINS.items():
            self.fallback_chain.register_chain(primary, fallbacks)
        
        # 新增：跨会话记忆
        self.memory = SessionMemory() if enable_memory else None
    
    async def run(self, task: str) -> str:
        """
        执行完整的 Agent 循环（增强版）
        
        新增功能：
        1. 上下文压缩 - 自动管理 Token 限制
        2. 智能摘要 - 工具结果自动摘要
        3. 错误恢复 - 自动重试 + 替代方案
        4. 记忆集成 - 添加相关记忆到上下文
        
        Args:
            task: 用户任务
            
        Returns:
            最终回复文本
        """
        # 新增：从记忆中获取相关上下文
        context_enhancement = ""
        if self.memory:
            memory_context = self.memory.get_context(task)
            if memory_context:
                context_enhancement = f"\n\n{memory_context}"
        
        messages = [Message(role="user", content=task + context_enhancement)]
        iteration = 0
        final_answer = ""
        tool_execution_stats = {"success": 0, "failed": 0, "recovered": 0}
        
        while iteration < self.max_iterations:
            iteration += 1
            logger.debug("Agent iteration", iteration=iteration, max=self.max_iterations)
            
            # 新增：检查是否需要压缩上下文
            if self.context_manager.should_compress(messages):
                logger.info("Compressing context window")
                messages = self.context_manager.compress_messages(messages)
                stats = self.context_manager.get_stats()
                click.echo(click.style(
                    f"📦 Context compressed: {stats.original_tokens} → {stats.compressed_tokens} tokens "
                    f"({stats.compression_ratio:.0%} reduction)",
                    dim=True
                ))
            
            # 1. 调用 LLM
            response = await self.llm.chat(messages, tools=self.tools if self.tools else None)
            
            # 2. 检查是否有文本回复（可能是最终答案）
            if response.text:
                click.echo(response.text)
                final_answer = response.text
            
            # 3. 检查是否有工具调用
            if not response.tool_calls:
                # 没有工具调用，任务完成
                logger.info("Agent completed", iterations=iteration)
                break
            
            # 4. 执行所有工具调用（带错误恢复）
            tool_results = []
            for tool_call in response.tool_calls:
                click.echo()
                click.echo(click.style(f"🔧 Using tool: {tool_call.name}", bold=True, fg="cyan"))
                
                # 新增：使用错误恢复系统执行工具
                async def execute_tool():
                    return await self.registry.execute_tool(
                        tool_call.name,
                        tool_call.input,
                        self.context
                    )
                
                # 使用降级链执行
                result, used_tool = await self.fallback_chain.execute_with_fallbacks(
                    tool_call.name,
                    execute_tool
                )
                
                if result is None:
                    # 执行失败，使用错误恢复
                    recovery_result = await self.error_recovery.execute_with_recovery(
                        tool_call.name,
                        execute_tool
                    )
                    
                    tool_execution_stats["failed"] += 1
                    
                    if recovery_result.success:
                        tool_execution_stats["recovered"] += 1
                        click.echo(click.style(
                            f"   ✅ Recovered after {recovery_result.retry_count} retries",
                            fg="green"
                        ))
                        result = await execute_tool()
                    else:
                        click.echo(click.style(
                            f"   ❌ Failed: {recovery_result.error_message}",
                            fg="red"
                        ))
                        if recovery_result.suggestion:
                            click.echo(click.style(
                                f"   💡 Suggestion: {recovery_result.suggestion[:200]}",
                                dim=True,
                                fg="yellow"
                            ))
                        tool_results.append({
                            "tool_call_id": tool_call.id,
                            "name": tool_call.name,
                            "result": f"Error: {recovery_result.error_message}",
                            "is_error": True,
                            "suggestion": recovery_result.suggestion
                        })
                        continue
                elif used_tool != tool_call.name:
                    click.echo(click.style(
                        f"   ⚡ Using fallback: {used_tool}",
                        fg="yellow"
                    ))
                
                tool_execution_stats["success"] += 1
                
                result_text = result.to_text() if hasattr(result, 'to_text') else str(result)
                
                # 新增：智能摘要工具结果
                if len(result_text) > 2000:
                    result_text = self.context_manager.summarize_tool_result(result_text, max_length=1500)
                    click.echo(click.style(f"   📝 Summarized long output", dim=True))
                
                click.echo(click.style(f"   Result: {result_text[:200]}", dim=True))
                
                tool_results.append({
                    "tool_call_id": tool_call.id,
                    "name": tool_call.name,
                    "result": result_text,
                    "is_error": result.is_error if hasattr(result, 'is_error') else False
                })
            
            # 5. 将工具结果添加到消息历史
            messages.append(Message(role="assistant", content=response.text))
            
            # 添加工具结果作为用户消息（让 LLM 继续分析）
            for tr in tool_results:
                tool_result_content = (
                    f"[Tool {tr['name']} result]: {tr['result']}"
                )
                messages.append(Message(role="user", content=tool_result_content))
            
            # 6. 继续循环，让 LLM 基于工具结果继续分析
        
        if iteration >= self.max_iterations:
            logger.warning("Agent reached max iterations", max=self.max_iterations)
            click.echo()
            click.echo(click.style("⚠️ 达到最大迭代次数，停止执行", fg="yellow"))
        
        # 新增：保存任务相关的记忆
        if self.memory and final_answer:
            # 提取关键信息保存
            self.memory.set(
                key=f"task_{iteration}_{hash(task) % 10000}",
                content=final_answer[:500],
                tags=["task", "completed"]
            )
        
        # 显示执行统计
        click.echo()
        click.echo(click.style(
            f"📊 Execution Stats: {tool_execution_stats['success']} success, "
            f"{tool_execution_stats['failed']} failed, "
            f"{tool_execution_stats['recovered']} recovered",
            dim=True
        ))
        
        return final_answer


async def run_agent_task(
    llm: LLMProvider,
    registry: ToolRegistry,
    context: ToolContext,
    task: str,
    max_iterations: int = 20,
) -> str:
    """
    运行 Agent 任务（批处理模式）
    
    Args:
        llm: LLM 提供者
        registry: 工具注册表
        context: 工具上下文
        task: 任务描述
        max_iterations: 最大迭代次数
        
    Returns:
        最终回复
    """
    agent = AgentLoop(llm, registry, context, max_iterations)
    return await agent.run(task)
