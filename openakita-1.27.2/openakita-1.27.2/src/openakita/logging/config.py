"""
日志配置和初始化

功能:
- 配置根日志记录器
- 设置文件处理器（按天轮转 + 按大小轮转）
- 设置错误日志处理器（只记录 ERROR/CRITICAL）
- 设置控制台处理器
- 设置会话日志处理器（供 AI 查询）
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .handlers import ColoredConsoleHandler, ErrorOnlyHandler, SessionLogHandler


def setup_logging(
    log_dir: Path | None = None,
    log_level: str = "INFO",
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    log_file_prefix: str = "openakita",
    log_max_size_mb: int = 10,
    log_backup_count: int = 30,
    log_to_console: bool = True,
    log_to_file: bool = True,
) -> logging.Logger:
    """
    配置日志系统

    Args:
        log_dir: 日志目录
        log_level: 日志级别
        log_format: 日志格式
        log_file_prefix: 日志文件前缀
        log_max_size_mb: 单个日志文件最大大小（MB）
        log_backup_count: 保留的日志文件数量
        log_to_console: 是否输出到控制台
        log_to_file: 是否输出到文件

    Returns:
        根日志记录器
    """
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # 清除现有处理器
    root_logger.handlers.clear()

    # 创建格式化器
    formatter = logging.Formatter(log_format)

    # 控制台处理器
    if log_to_console:
        console_handler = ColoredConsoleHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # 文件处理器
    if log_to_file and log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        # 主日志文件（按大小轮转，每个文件最大 log_max_size_mb MB）
        main_log_file = log_dir / f"{log_file_prefix}.log"
        main_handler = RotatingFileHandler(
            main_log_file,
            maxBytes=log_max_size_mb * 1024 * 1024,
            backupCount=log_backup_count,
            encoding="utf-8",
        )
        main_handler.setLevel(logging.DEBUG)
        main_handler.setFormatter(formatter)
        root_logger.addHandler(main_handler)

        # 错误日志文件（只记录 ERROR/CRITICAL，按天轮转）
        error_log_file = log_dir / "error.log"
        error_handler = ErrorOnlyHandler(
            error_log_file,
            when="midnight",
            interval=1,
            backupCount=log_backup_count,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)

    # 会话日志处理器（供 AI 查询当前会话日志）
    session_handler = SessionLogHandler(logging.DEBUG)
    # 会话日志使用简化格式，只保留消息内容
    session_formatter = logging.Formatter("%(message)s")
    session_handler.setFormatter(session_formatter)
    root_logger.addHandler(session_handler)

    # 减少第三方库的日志输出
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        日志记录器
    """
    return logging.getLogger(name)
