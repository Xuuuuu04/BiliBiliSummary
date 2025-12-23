"""
统一日志系统
提供标准化的日志输出格式和级别
"""
import logging
import sys
from pathlib import Path
from datetime import datetime


# 日志颜色配置
class LogColors:
    """终端日志颜色"""
    RESET = '\033[0m'
    BOLD = '\033[1m'

    # 级别颜色
    DEBUG = '\033[36m'      # 青色
    INFO = '\033[32m'       # 绿色
    WARNING = '\033[33m'    # 黄色
    ERROR = '\033[31m'      # 红色
    CRITICAL = '\033[35m'   # 紫色

    # 模块标签颜色
    MODULE = '\033[38;5;214m'  # 橙色


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器"""

    COLORS = {
        logging.DEBUG: LogColors.DEBUG,
        logging.INFO: LogColors.INFO,
        logging.WARNING: LogColors.WARNING,
        logging.ERROR: LogColors.ERROR,
        logging.CRITICAL: LogColors.CRITICAL,
    }

    def format(self, record):
        # 获取对应级别的颜色
        level_color = self.COLORS.get(record.levelno, LogColors.RESET)

        # 格式化级别名称
        levelname = f"{level_color}{record.levelname}{LogColors.RESET}"

        # 格式化模块名
        module_name = f"{LogColors.MODULE}[{record.name}]{LogColors.RESET}"

        # 格式化消息
        message = record.getMessage()

        # 组合格式
        formatted = f"{levelname} {module_name} {message}"

        # 添加异常信息（如果有）
        if record.exc_info:
            formatted += '\n' + self.formatException(record.exc_info)

        return formatted


# 日志配置
LOG_CONFIG = {
    'level': logging.INFO,
    'format': '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    'datefmt': '%H:%M:%S'
}


# 日志器缓存
_loggers = {}


def get_logger(name: str, level: int = None) -> logging.Logger:
    """
    获取或创建日志器

    Args:
        name: 日志器名称（通常使用模块名）
        level: 日志级别（可选，默认使用全局配置）

    Returns:
        logging.Logger: 配置好的日志器实例

    Example:
        from src.backend.utils.logger import get_logger

        logger = get_logger(__name__)
        logger.info("这是一条信息")
        logger.error("这是一条错误")
    """
    if name in _loggers:
        return _loggers[name]

    # 创建日志器
    logger = logging.getLogger(name)

    # 设置日志级别
    if level is None:
        level = LOG_CONFIG['level']
    logger.setLevel(level)

    # 避免重复添加 handler
    if not logger.handlers:
        # 创建控制台 handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        # 使用带颜色的格式化器
        formatter = ColoredFormatter()
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    # 缓存日志器
    _loggers[name] = logger

    return logger


def set_global_level(level: int):
    """
    设置全局日志级别

    Args:
        level: 日志级别 (logging.DEBUG, logging.INFO, etc.)
    """
    LOG_CONFIG['level'] = level

    # 更新所有已存在的日志器
    for logger in _loggers.values():
        logger.setLevel(level)
        for handler in logger.handlers:
            handler.setLevel(level)


# 便捷函数
def debug(msg: str, name: str = None):
    """输出 DEBUG 级别日志"""
    if name:
        get_logger(name).debug(msg)
    else:
        logging.debug(msg)


def info(msg: str, name: str = None):
    """输出 INFO 级别日志"""
    if name:
        get_logger(name).info(msg)
    else:
        logging.info(msg)


def warning(msg: str, name: str = None):
    """输出 WARNING 级别日志"""
    if name:
        get_logger(name).warning(msg)
    else:
        logging.warning(msg)


def error(msg: str, name: str = None, exc_info: bool = False):
    """输出 ERROR 级别日志"""
    if name:
        get_logger(name).error(msg, exc_info=exc_info)
    else:
        logging.error(msg, exc_info=exc_info)
