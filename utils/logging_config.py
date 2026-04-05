#!/usr/bin/env python3
"""
统一日志配置

提供全项目统一的日志配置，包括：
- 控制台输出
- 文件轮转
- 线程标识
- 统一格式

使用方式：
    from utils.logging_config import setup_logging
    logger = setup_logging('module_name')
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
import threading


class ThreadLogFormatter(logging.Formatter):
    """带线程标识的日志格式器"""
    
    def format(self, record):
        record.thread_name = threading.current_thread().name
        return super().format(record)


def setup_logging(
    module_name: str,
    log_dir: str = "logs",
    level: int = logging.INFO,
    console: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 10
) -> logging.Logger:
    """
    设置统一日志配置
    
    Args:
        module_name: 模块名称
        log_dir: 日志目录
        level: 日志级别
        console: 是否输出到控制台
        max_bytes: 单个日志文件最大大小
        backup_count: 保留的备份文件数量
        
    Returns:
        配置好的 Logger 对象
    """
    logger = logging.getLogger(module_name)
    logger.setLevel(level)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    # 统一格式
    formatter = ThreadLogFormatter(
        '%(asctime)s - [%(thread_name)s] - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台 Handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        logger.addHandler(console_handler)
    
    # 文件 Handler（轮转）
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    log_file = log_path / f"{module_name}.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    logger.addHandler(file_handler)
    
    # 记录日志配置信息
    logger.info(f"📝 日志初始化：{module_name}")
    logger.info(f"   日志文件：{log_file}")
    logger.info(f"   日志策略：最多 {backup_count} 个文件，每个文件最大 {max_bytes / 1024 / 1024:.0f}MB")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    获取 Logger（不重新配置）
    
    适用于已经配置过日志的模块
    """
    return logging.getLogger(name)


# ============================================
# 日志级别快捷方式
# ============================================

class LogLevel:
    """日志级别常量"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


# ============================================
# 示例用法
# ============================================

if __name__ == "__main__":
    # 测试日志配置
    logger = setup_logging("test_module", console=True)
    
    logger.debug("这是一条调试日志")
    logger.info("这是一条信息日志")
    logger.warning("这是一条警告日志")
    logger.error("这是一条错误日志")
    logger.critical("这是一条严重错误日志")
    
    # 测试多线程日志
    def worker(num):
        log = setup_logging(f"worker_{num}", console=False)
        log.info(f"Worker {num} started")
    
    threads = []
    for i in range(3):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    print("\n✅ 日志测试完成")
