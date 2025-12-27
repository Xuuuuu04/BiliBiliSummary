"""
测试 async_helpers.py 模块

测试目标：
- 异步转同步运行
- 事件循环处理
- 多线程场景
- 异常处理
"""
import pytest
import asyncio
from src.backend.utils.async_helpers import run_async


class TestRunAsync:
    """测试异步转同步运行功能"""

    @pytest.mark.asyncio
    async def test_run_async_with_simple_coroutine(self):
        """测试运行简单的协程"""
        async def simple_func():
            return "result"

        result = run_async(simple_func())
        assert result == "result"

    @pytest.mark.asyncio
    async def test_run_async_with_integer_result(self):
        """测试返回整数结果"""
        async def return_int():
            return 42

        result = run_async(return_int())
        assert result == 42

    @pytest.mark.asyncio
    async def test_run_async_with_dict_result(self):
        """测试返回字典结果"""
        async def return_dict():
            return {"key": "value", "number": 123}

        result = run_async(return_dict())
        assert result == {"key": "value", "number": 123}

    @pytest.mark.asyncio
    async def test_run_async_with_delay(self):
        """测试带延迟的协程"""
        async def delayed_func():
            await asyncio.sleep(0.1)
            return "done"

        result = run_async(delayed_func())
        assert result == "done"

    @pytest.mark.asyncio
    async def test_run_async_with_exception(self):
        """测试协程抛出异常"""
        async def raise_error():
            raise ValueError("Test error")

        with pytest.raises(ValueError) as exc_info:
            run_async(raise_error())
        assert "Test error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_run_async_with_multiple_awaits(self):
        """测试包含多个 await 的协程"""
        async def multiple_awaits():
            result1 = await asyncio.sleep(0.01, "first")
            result2 = await asyncio.sleep(0.01, "second")
            return result1 + result2

        result = run_async(multiple_awaits())
        assert result == "firstsecond"

    @pytest.mark.asyncio
    async def test_run_async_with_async_comprehension(self):
        """测试包含异步推导的协程"""
        async def async_comprehension():
            values = [asyncio.sleep(0.01, i) for i in range(3)]
            results = await asyncio.gather(*values)
            return sum(results)

        result = run_async(async_comprehension())
        assert result == 3  # 0 + 1 + 2

    @pytest.mark.asyncio
    async def test_run_async_with_none_result(self):
        """测试返回 None 的协程"""
        async def return_none():
            return None

        result = run_async(return_none())
        assert result is None

    @pytest.mark.asyncio
    async def test_run_async_with_list_result(self):
        """测试返回列表的协程"""
        async def return_list():
            return [1, 2, 3, 4, 5]

        result = run_async(return_list())
        assert result == [1, 2, 3, 4, 5]

    @pytest.mark.asyncio
    async def test_run_async_preserves_exception_type(self):
        """测试保留异常类型"""
        async def raise_custom_error():
            raise TypeError("Custom type error")

        with pytest.raises(TypeError) as exc_info:
            run_async(raise_custom_error())
        assert "Custom type error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_run_async_with_runtime_error(self):
        """测试 RuntimeError 场景"""
        # 这个测试模拟在没有现有事件循环的情况下创建新循环
        async def simple_task():
            return "success"

        # 每次调用 run_async 应该都能成功
        result1 = run_async(simple_task())
        assert result1 == "success"

        result2 = run_async(simple_task())
        assert result2 == "success"

    @pytest.mark.asyncio
    async def test_run_async_with_nested_async_calls(self):
        """测试嵌套异步调用"""
        async def inner_func():
            await asyncio.sleep(0.01)
            return "inner"

        async def outer_func():
            inner_result = await inner_func()
            await asyncio.sleep(0.01)
            return f"outer-{inner_result}"

        result = run_async(outer_func())
        assert result == "outer-inner"

    @pytest.mark.asyncio
    async def test_run_async_with_awaitable_future(self):
        """测试使用 Future"""
        async def with_future():
            loop = asyncio.get_event_loop()
            future = loop.create_future()
            loop.call_soon(future.set_result, "future_result")
            return await future

        result = run_async(with_future())
        assert result == "future_result"

    @pytest.mark.asyncio
    async def test_run_async_concurrent_execution(self):
        """测试并发执行多个协程"""
        async def task(name, delay):
            await asyncio.sleep(delay)
            return name

        # 模拟并发执行多个异步任务
        results = []
        results.append(run_async(task("task1", 0.01)))
        results.append(run_async(task("task2", 0.01)))
        results.append(run_async(task("task3", 0.01)))

        assert len(results) == 3
        assert "task1" in results
        assert "task2" in results
        assert "task3" in results
