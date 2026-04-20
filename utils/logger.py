#!/usr/bin/env python3
"""
统一日志配置模块

功能：
- 统一的日志配置
- 自动轮转（最多保留 10 个文件）
- 文件大小限制（每个文件最大 10MB）
- 支持控制台和文件输出
"""

import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler


class LogConfig:
    """日志配置类"""
    
    # 日志配置常量
    MAX_BYTES = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT = 10  # 保留 10 个备份文件
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = '%(asctime)s - [%(levelname)s] - %(name)s - %(message)s'
    CONSOLE_FORMAT = '%(asctime)s - [%(levelname)s] - %(message)s'
    
    @classmethod
    def get_log_dir(cls, project_dir: Path = None) -> Path:
        """获取日志目录"""
        if project_dir is None:
            project_dir = Path(__file__).parent.parent
        log_dir = project_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        return log_dir
    
    @classmethod
    def get_file_handler(cls, log_file: str, log_dir: Path = None) -> RotatingFileHandler:
        """获取文件日志处理器"""
        if log_dir is None:
            log_dir = cls.get_log_dir()
        
        log_path = log_dir / log_file
        
        handler = RotatingFileHandler(
            log_path,
            maxBytes=cls.MAX_BYTES,
            backupCount=cls.BACKUP_COUNT,
            encoding='utf-8'
        )
        handler.setFormatter(logging.Formatter(cls.LOG_FORMAT))
        handler.setLevel(cls.LOG_LEVEL)
        
        return handler
    
    @classmethod
    def get_console_handler(cls) -> logging.StreamHandler:
        """获取控制台日志处理器"""
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(cls.CONSOLE_FORMAT))
        handler.setLevel(cls.LOG_LEVEL)
        return handler
    
    @classmethod
    def get_logger(cls, name: str, log_file: str = None, add_console: bool = True) -> logging.Logger:
        """
        获取配置好的 logger
        
        Args:
            name: logger 名称
            log_file: 日志文件名（可选，不传则只输出到控制台）
            add_console: 是否添加控制台输出
            
        Returns:
            配置好的 Logger 对象
        """
        logger = logging.getLogger(name)
        logger.setLevel(cls.LOG_LEVEL)
        
        # 避免重复添加 handler
        if logger.handlers:
            return logger
        
        # 添加文件处理器
        if log_file:
            file_handler = cls.get_file_handler(log_file)
            logger.addHandler(file_handler)
            logger.info(f"📝 日志文件：{log_file}")
            logger.info(f"📊 日志策略：最多保留 {cls.BACKUP_COUNT} 个文件，每个文件最大 {cls.MAX_BYTES // 1024 // 1024}MB")
        
        # 添加控制台处理器
        if add_console:
            console_handler = cls.get_console_handler()
            logger.addHandler(console_handler)
        
        return logger


# 便捷函数
def get_web_logger() -> logging.Logger:
    """获取 Web 服务的 logger"""
    return LogConfig.get_logger('web', 'web.log')


def get_workflow_logger() -> logging.Logger:
    """获取工作流的 logger"""
    return LogConfig.get_logger('workflow', 'workflow.log')


def get_service_logger(name: str) -> logging.Logger:
    """获取服务的 logger"""
    return LogConfig.get_logger(f'service.{name}', f'{name}.log')


def setup_logger(
    name: str,
    log_file: str,
    log_dir: Path = None,
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 10,
    add_console: bool = True,
) -> logging.Logger:
    """
    设置并返回一个配置好的 logger（兼容原有代码）

    这是合并 workflow_orchestrator.py 和 custom_topic_generator.py
    中 `_setup_logger` 方法的通用版本。

    Args:
        name: logger 名称
        log_file: 日志文件名
        log_dir: 日志目录（可选，默认为项目根目录下的 logs/）
        level: 日志级别
        max_bytes: 单个日志文件最大大小（默认 10MB）
        backup_count: 保留的备份文件数量（默认 10）
        add_console: 是否添加控制台输出

    Returns:
        logging.Logger: 配置好的 logger
    """
    # 确定日志目录
    if log_dir is None:
        log_dir = Path(__file__).parent.parent / "logs"

    log_dir.mkdir(exist_ok=True)

    logger = logging.getLogger(name)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # 控制台处理器
    if add_console:
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        console.setLevel(level)
        logger.addHandler(console)

    # 文件处理器（支持轮转）
    log_path = log_dir / log_file
    file = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    file.setLevel(level)
    logger.addHandler(file)

    return logger


# 预定义的便捷函数
def get_workflow_orchestrator_logger() -> logging.Logger:
    """获取 workflow_orchestrator 的 logger"""
    return setup_logger("workflow", "workflow.log")


def get_custom_topic_logger() -> logging.Logger:
    """获取 custom_topic_generator 的 logger"""
    return setup_logger("custom_topic", "custom_topic.log")


# 使用示例
if __name__ == '__main__':
    # 示例 1：获取 Web logger
    web_logger = get_web_logger()
    web_logger.info("Web 服务启动")
    
    # 示例 2：获取工作流 logger
    workflow_logger = get_workflow_logger()
    workflow_logger.info("工作流启动")
    
    # 示例 3：获取服务 logger
    ask_logger = get_service_logger('ask_service')
    ask_logger.info("Ask 服务初始化")
