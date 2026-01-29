"""
异步工具函数模块

提供异步转同步的辅助函数，解决循环依赖问题
"""
import asyncio
from typing import Any, Coroutine


def run_async(coro: Coroutine[Any, Any, Any]) -> Any:
    """
    在同步上下文中运行异步函数

    Args:
        coro: 异步协程对象

    Returns:
        异步函数的返回值

    Note:
        - 专为 Flask 多线程环境设计
        - 使用 asyncio.run() 确保每个线程都有独立的事件循环
        - 自动处理事件循环的创建和清理
        - 线程安全，避免事件循环冲突
    """
    # 使用 asyncio.run() 创建新的事件循环并运行协程
    # 这会自动处理事件循环的创建、运行和清理
    return asyncio.run(coro)
