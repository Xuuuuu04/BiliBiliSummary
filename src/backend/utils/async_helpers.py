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
        - Python 3.10+ 推荐使用 asyncio.run() 而不是 get_event_loop()
        - 该函数主要用于在 Flask 同步路由中调用异步函数
        - 在多线程环境下使用时需要注意事件循环隔离
    """
    try:
        # 优先使用 asyncio.run()（推荐方式）
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果事件循环正在运行，创建新线程运行
            import concurrent.futures
            import threading

            result = [None]
            exception = [None]

            def run_in_new_loop():
                try:
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    result[0] = new_loop.run_until_complete(coro)
                    new_loop.close()
                except Exception as e:
                    exception[0] = e

            thread = threading.Thread(target=run_in_new_loop)
            thread.start()
            thread.join()

            if exception[0]:
                raise exception[0]
            return result[0]
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # 如果没有事件循环，创建新的
        return asyncio.run(coro)
