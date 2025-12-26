#!/usr/bin/env python3
"""
Logger Utility
日志工具模块

基于 DEVELOPMENT_GUIDE.md 第7.1节实现
提供统一的日志系统配置和工具函数
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

# 模块级日志记录器
logger = logging.getLogger(__name__)


def setup_logging(config) -> logging.Logger:
    """
    配置全局日志系统

    基于 DEVELOPMENT_GUIDE.md 第7.1节实现
    支持文件轮转和控制台双输出

    Args:
        config: Config 配置对象，包含 logging 配置

    Returns:
        logging.Logger: 配置好的根日志记录器

    Raises:
        ValueError: 如果日志级别无效
        OSError: 如果无法创建日志文件
    """
    # 获取日志级别
    log_level_str = config.logging.level.upper()
    try:
        log_level = getattr(logging, log_level_str)
    except AttributeError:
        raise ValueError(
            f"无效的日志级别: {config.logging.level}\n"
            f"有效级别: DEBUG, INFO, WARNING, ERROR, CRITICAL"
        )

    # 日志文件路径
    log_file = Path(config.logging.logfile)

    # 确保日志目录存在
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise OSError(f"无法创建日志目录: {log_file.parent}: {e}")

    # 配置根记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 清除旧的 handlers 避免重复添加
    root_logger.handlers.clear()

    # 定义日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler 1: 文件轮转（防止日志占满磁盘）
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=config.logging.max_log_size,
            backupCount=config.logging.backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)
    except Exception as e:
        logger.error(f"无法创建文件日志处理器: {e}")

    # Handler 2: 控制台输出（方便调试）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)

    # 记录初始化信息
    logger.info("=" * 60)
    logger.info("日志系统初始化完成")
    logger.info(f"日志级别: {log_level_str}")
    logger.info(f"日志文件: {log_file.absolute()}")
    logger.info(f"文件轮转: {config.logging.max_log_size / 1024 / 1024:.1f}MB x {config.logging.backup_count} 份")
    logger.info("=" * 60)

    return root_logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取日志记录器

    Args:
        name: 日志记录器名称，通常为 __name__

    Returns:
        logging.Logger: 日志记录器实例
    """
    return logging.getLogger(name)


# 便捷别名
setup = setup_logging
get = get_logger
