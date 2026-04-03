"""
错误恢复系统 - 自动重试与替代方案

实现类似 Claude Code 的错误恢复能力：
- 自动重试机制
- 替代工具方案
- 错误分类与处理策略
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable

import structlog

if TYPE_CHECKING:
    from ..tools.base import ToolResult

logger = structlog.get_logger(__name__)


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = 1         # 可忽略，继续执行
    MEDIUM = 2      # 需要重试
    HIGH = 3        # 需要替代方案
    CRITICAL = 4    # 必须停止


class ErrorType(Enum):
    """错误类型"""
    NETWORK = "network"           # 网络错误
    TIMEOUT = "timeout"           # 超时
    PERMISSION = "permission"     # 权限不足
    NOT_FOUND = "not_found"       # 资源不存在
    INVALID_INPUT = "invalid"     # 输入无效
    RATE_LIMIT = "rate_limit"     # 频率限制
    UNKNOWN = "unknown"           # 未知错误


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    initial_delay: float = 1.0      # 初始延迟（秒）
    max_delay: float = 30.0         # 最大延迟（秒）
    exponential_base: float = 2.0   # 指数退避基数
    jitter: bool = True             # 是否添加随机抖动


@dataclass
class ErrorRecoveryResult:
    """错误恢复结果"""
    success: bool
    recovered: bool = False
    retry_count: int = 0
    alternative_used: str | None = None
    error_message: str | None = None
    suggestion: str | None = None


class ErrorClassifier:
    """
    错误分类器
    
    根据错误信息自动分类错误类型和严重程度
    """
    
    # 错误模式匹配
    NETWORK_PATTERNS = [
        "connection", "network", "timeout", "unreachable",
        "ETIMEDOUT", "ECONNREFUSED", "ECONNRESET"
    ]
    
    PERMISSION_PATTERNS = [
        "permission", "access denied", "unauthorized",
        "EACCES", "EPERM", "forbidden"
    ]
    
    NOT_FOUND_PATTERNS = [
        "not found", "does not exist", "no such file",
        "ENOENT", "404"
    ]
    
    RATE_LIMIT_PATTERNS = [
        "rate limit", "too many requests", "throttled",
        "429", "quota exceeded"
    ]
    
    @classmethod
    def classify(cls, error_message: str) -> tuple[ErrorType, ErrorSeverity]:
        """
        分类错误
        
        Returns:
            (错误类型，严重程度)
        """
        error_lower = error_message.lower()
        
        # 网络错误
        if any(p.lower() in error_lower for p in cls.NETWORK_PATTERNS):
            return ErrorType.NETWORK, ErrorSeverity.MEDIUM
        
        # 权限错误
        if any(p.lower() in error_lower for p in cls.PERMISSION_PATTERNS):
            return ErrorType.PERMISSION, ErrorSeverity.HIGH
        
        # 资源不存在
        if any(p.lower() in error_lower for p in cls.NOT_FOUND_PATTERNS):
            return ErrorType.NOT_FOUND, ErrorSeverity.LOW
        
        # 频率限制
        if any(p.lower() in error_lower for p in cls.RATE_LIMIT_PATTERNS):
            return ErrorType.RATE_LIMIT, ErrorSeverity.HIGH
        
        # 超时
        if "timeout" in error_lower or "timed out" in error_lower:
            return ErrorType.TIMEOUT, ErrorSeverity.MEDIUM
        
        # 默认：未知错误
        return ErrorType.UNKNOWN, ErrorSeverity.MEDIUM


class ErrorRecovery:
    """
    错误恢复系统
    
    功能：
    1. 自动重试（指数退避）
    2. 替代工具方案
    3. 错误建议生成
    """
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
        self.classifier = ErrorClassifier()
        self._alternative_handlers: dict[str, Callable] = {}
    
    def register_alternative(
        self,
        tool_name: str,
        handler: Callable
    ):
        """
        注册替代工具处理器
        
        Args:
            tool_name: 原始工具名称
            handler: 替代处理器函数
        """
        self._alternative_handlers[tool_name] = handler
        logger.debug("Registered alternative handler", tool=tool_name)
    
    async def execute_with_recovery(
        self,
        tool_name: str,
        executor: Callable,
        *args,
        **kwargs
    ) -> ErrorRecoveryResult:
        """
        执行工具并自动恢复错误
        
        Args:
            tool_name: 工具名称
            executor: 执行函数
            *args, **kwargs: 执行参数
            
        Returns:
            恢复结果
        """
        retry_count = 0
        last_error = None
        
        while retry_count <= self.config.max_retries:
            try:
                # 尝试执行
                result = await executor(*args, **kwargs)
                
                # 检查是否有错误
                if hasattr(result, 'is_error') and result.is_error:
                    raise Exception(result.to_text() if hasattr(result, 'to_text') else str(result))
                
                return ErrorRecoveryResult(
                    success=True,
                    recovered=retry_count > 0,
                    retry_count=retry_count
                )
                
            except Exception as e:
                last_error = e
                error_msg = str(e)
                
                # 分类错误
                error_type, severity = self.classifier.classify(error_msg)
                
                logger.warning("Tool execution failed",
                             tool=tool_name,
                             error_type=error_type.value,
                             severity=severity.name,
                             retry=retry_count)
                
                # 严重错误直接返回
                if severity == ErrorSeverity.CRITICAL:
                    return ErrorRecoveryResult(
                        success=False,
                        error_message=error_msg,
                        suggestion=self._generate_suggestion(error_type, tool_name)
                    )
                
                # 检查是否需要重试
                if retry_count < self.config.max_retries:
                    if error_type in [ErrorType.NETWORK, ErrorType.TIMEOUT, ErrorType.RATE_LIMIT]:
                        # 可重试的错误类型
                        delay = self._calculate_delay(retry_count)
                        logger.info(f"Retrying after {delay}s", retry=retry_count)
                        await asyncio.sleep(delay)
                        retry_count += 1
                        continue
                
                # 尝试替代方案
                if tool_name in self._alternative_handlers:
                    logger.info("Trying alternative handler", tool=tool_name)
                    try:
                        alt_result = await self._alternative_handlers[tool_name](*args, **kwargs)
                        return ErrorRecoveryResult(
                            success=True,
                            recovered=True,
                            alternative_used=tool_name + "_alternative"
                        )
                    except Exception as alt_error:
                        logger.warning("Alternative also failed",
                                     tool=tool_name,
                                     error=str(alt_error))
                
                # 所有尝试都失败
                return ErrorRecoveryResult(
                    success=False,
                    error_message=error_msg,
                    retry_count=retry_count,
                    suggestion=self._generate_suggestion(error_type, tool_name)
                )
        
        # 达到最大重试次数
        return ErrorRecoveryResult(
            success=False,
            error_message=str(last_error),
            retry_count=retry_count,
            suggestion="已达到最大重试次数，请检查系统状态后重试"
        )
    
    def _calculate_delay(self, retry_count: int) -> float:
        """计算重试延迟（指数退避 + 抖动）"""
        import random
        
        delay = self.config.initial_delay * (
            self.config.exponential_base ** retry_count
        )
        delay = min(delay, self.config.max_delay)
        
        if self.config.jitter:
            # 添加 ±25% 的随机抖动
            delay = delay * (0.75 + random.random() * 0.5)
        
        return delay
    
    def _generate_suggestion(
        self,
        error_type: ErrorType,
        tool_name: str
    ) -> str:
        """生成错误处理建议"""
        suggestions = {
            ErrorType.NETWORK: (
                f"工具 '{tool_name}' 执行失败，可能是网络问题。\n"
                "建议：\n"
                "1. 检查网络连接\n"
                "2. 稍后重试\n"
                "3. 如果是 API 调用，检查 API 状态"
            ),
            ErrorType.TIMEOUT: (
                f"工具 '{tool_name}' 执行超时。\n"
                "建议：\n"
                "1. 操作可能耗时较长，请稍等\n"
                "2. 尝试分批执行\n"
                "3. 检查目标资源是否可用"
            ),
            ErrorType.PERMISSION: (
                f"工具 '{tool_name}' 权限不足。\n"
                "建议：\n"
                "1. 检查文件/目录权限\n"
                "2. 使用 sudo 或管理员权限\n"
                "3. 确认用户有执行该操作的权限"
            ),
            ErrorType.NOT_FOUND: (
                f"工具 '{tool_name}' 找不到目标资源。\n"
                "建议：\n"
                "1. 检查路径/名称是否正确\n"
                "2. 确认资源是否存在\n"
                "3. 使用 ls/find 等命令先查看"
            ),
            ErrorType.RATE_LIMIT: (
                f"工具 '{tool_name}' 触发频率限制。\n"
                "建议：\n"
                "1. 等待一段时间后重试\n"
                "2. 减少请求频率\n"
                "3. 考虑升级 API 配额"
            ),
            ErrorType.INVALID_INPUT: (
                f"工具 '{tool_name}' 输入无效。\n"
                "建议：\n"
                "1. 检查参数格式\n"
                "2. 确认输入符合要求\n"
                "3. 查看工具文档"
            ),
            ErrorType.UNKNOWN: (
                f"工具 '{tool_name}' 执行失败，原因未知。\n"
                "建议：\n"
                "1. 查看详细错误日志\n"
                "2. 尝试简化操作\n"
                "3. 联系技术支持"
            )
        }
        
        return suggestions.get(error_type, suggestions[ErrorType.UNKNOWN])


@dataclass
class FallbackConfig:
    """降级配置"""
    enabled: bool = True
    max_fallbacks: int = 2
    notify_user: bool = True


class FallbackChain:
    """
    降级链 - 多级备用方案
    
    当主工具失败时，依次尝试备用方案
    """
    
    def __init__(self, config: FallbackConfig = None):
        self.config = config or FallbackConfig()
        self._chains: dict[str, list[str]] = {}
    
    def register_chain(self, primary: str, fallbacks: list[str]):
        """
        注册降级链
        
        Args:
            primary: 主工具名称
            fallbacks: 备用工具列表（按优先级）
        """
        self._chains[primary] = fallbacks
        logger.info("Registered fallback chain",
                   primary=primary,
                   fallbacks=fallbacks)
    
    def get_fallbacks(self, tool_name: str) -> list[str]:
        """获取工具的备用方案列表"""
        return self._chains.get(tool_name, [])
    
    async def execute_with_fallbacks(
        self,
        tool_name: str,
        executor: Callable,
        *args,
        **kwargs
    ) -> tuple[Any | None, str | None]:
        """
        执行工具链（主工具 + 备用方案）
        
        Returns:
            (结果，使用的工具名称) 或 (None, 错误信息)
        """
        if not self.config.enabled:
            try:
                result = await executor(*args, **kwargs)
                return result, tool_name
            except Exception as e:
                return None, str(e)
        
        # 构建工具链
        tool_chain = [tool_name] + self.get_fallbacks(tool_name)
        attempts = 0
        last_error = None
        
        for tool in tool_chain[:self.config.max_fallbacks + 1]:
            attempts += 1
            
            try:
                logger.info("Attempting tool", tool=tool, attempt=attempts)
                result = await executor(*args, **kwargs)
                
                if self.config.notify_user and attempts > 1:
                    logger.info(f"Successfully recovered using {tool}")
                
                return result, tool
                
            except Exception as e:
                last_error = e
                logger.warning("Tool failed", tool=tool, error=str(e))
                continue
        
        # 所有尝试都失败
        return None, f"All attempts failed. Last error: {str(last_error)}"


# 预定义的降级链
DEFAULT_FALLBACK_CHAINS = {
    # 文件操作降级
    "file_read": ["cat", "head"],
    "file_write": ["echo", "printf"],
    "file_edit": ["sed", "awk"],
    
    # 搜索降级
    "grep": ["fgrep", "egrep"],
    "glob": ["find", "ls"],
    
    # Git 降级
    "git": ["gh", "hub"],
}
