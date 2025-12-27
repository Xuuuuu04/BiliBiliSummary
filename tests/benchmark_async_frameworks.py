"""
异步框架性能基准测试
对比 Flask vs FastAPI 的性能差异
"""
import asyncio
import time
import statistics
import httpx
from typing import List, Dict
from dataclasses import dataclass
import json

# ========== 配置 ==========

FLASK_BASE_URL = "http://localhost:5000"
FASTAPI_BASE_URL = "http://localhost:5001"

# 测试参数
CONCURRENT_REQUESTS = 50  # 并发请求数
TOTAL_REQUESTS = 100      # 总请求数
TIMEOUT = 30              # 超时时间（秒）

# ========== 数据结构 ==========

@dataclass
class BenchmarkResult:
    """基准测试结果"""
    framework: str
    endpoint: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_duration: float
    avg_latency: float
    min_latency: float
    max_latency: float
    p50_latency: float
    p95_latency: float
    p99_latency: float
    throughput: float  # req/s

    def to_dict(self) -> Dict:
        return {
            "framework": self.framework,
            "endpoint": self.endpoint,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "total_duration": round(self.total_duration, 3),
            "avg_latency": round(self.avg_latency * 1000, 2),  # ms
            "min_latency": round(self.min_latency * 1000, 2),
            "max_latency": round(self.max_latency * 1000, 2),
            "p50_latency": round(self.p50_latency * 1000, 2),
            "p95_latency": round(self.p95_latency * 1000, 2),
            "p99_latency": round(self.p99_latency * 1000, 2),
            "throughput": round(self.throughput, 2)
        }

    def print_summary(self):
        """打印测试结果摘要"""
        print(f"\n{'='*60}")
        print(f"框架: {self.framework} | 端点: {self.endpoint}")
        print(f"{'='*60}")
        print(f"总请求数: {self.total_requests}")
        print(f"成功请求: {self.successful_requests} ({self.successful_requests/self.total_requests*100:.1f}%)")
        print(f"失败请求: {self.failed_requests}")
        print(f"总耗时: {self.total_duration:.2f}s")
        print(f"吞吐量: {self.throughput:.2f} req/s")
        print(f"\n延迟统计 (毫秒):")
        print(f"  平均: {self.avg_latency*1000:.2f}ms")
        print(f"  最小: {self.min_latency*1000:.2f}ms")
        print(f"  最大: {self.max_latency*1000:.2f}ms")
        print(f"  P50:  {self.p50_latency*1000:.2f}ms")
        print(f"  P95:  {self.p95_latency*1000:.2f}ms")
        print(f"  P99:  {self.p99_latency*1000:.2f}ms")
        print(f"{'='*60}\n")

# ========== 测试函数 ==========

async def test_concurrent_requests(
    framework: str,
    base_url: str,
    endpoint: str = "/api/health",
    concurrent: int = CONCURRENT_REQUESTS,
    total: int = TOTAL_REQUESTS
) -> BenchmarkResult:
    """
    测试并发请求性能

    Args:
        framework: 框架名称 (Flask/FastAPI)
        base_url: API 基础 URL
        endpoint: 测试端点
        concurrent: 并发数
        total: 总请求数
    """
    print(f"\n[{framework}] 开始并发测试: {endpoint}")
    print(f"  -> 并发数: {concurrent}, 总请求: {total}")

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        latencies = []
        successful = 0
        failed = 0

        start_time = time.time()

        # 分批执行并发请求
        for batch_start in range(0, total, concurrent):
            batch_size = min(concurrent, total - batch_start)
            batch_end = batch_start + batch_size

            # 创建并发任务
            tasks = []
            for i in range(batch_size):
                task = client.get(f"{base_url}{endpoint}")
                tasks.append(task)

            # 执行并发请求
            batch_start_time = time.time()
            try:
                responses = await asyncio.gather(*tasks, return_exceptions=True)

                for response in responses:
                    if isinstance(response, Exception):
                        failed += 1
                    elif response.status_code == 200:
                        successful += 1
                        latency = time.time() - batch_start_time
                        latencies.append(latency)
                    else:
                        failed += 1

            except Exception as e:
                print(f"  ❌ 批次 {batch_start}-{batch_end} 失败: {e}")
                failed += batch_size

        total_duration = time.time() - start_time

    # 计算统计数据
    if latencies:
        avg_latency = statistics.mean(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        p50_latency = statistics.median(latencies)
        p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else max_latency
        p99_latency = statistics.quantiles(latencies, n=100)[98] if len(latencies) > 100 else max_latency
    else:
        avg_latency = min_latency = max_latency = p50_latency = p95_latency = p99_latency = 0

    throughput = successful / total_duration if total_duration > 0 else 0

    result = BenchmarkResult(
        framework=framework,
        endpoint=endpoint,
        total_requests=total,
        successful_requests=successful,
        failed_requests=failed,
        total_duration=total_duration,
        avg_latency=avg_latency,
        min_latency=min_latency,
        max_latency=max_latency,
        p50_latency=p50_latency,
        p95_latency=p95_latency,
        p99_latency=p99_latency,
        throughput=throughput
    )

    result.print_summary()

    return result

async def test_sse_stream(
    framework: str,
    base_url: str,
    endpoint: str = "/api/analyze"
) -> BenchmarkResult:
    """
    测试 SSE 流式响应性能

    Args:
        framework: 框架名称
        base_url: API 基础 URL
        endpoint: 测试端点
    """
    print(f"\n[{framework}] 开始 SSE 流式测试: {endpoint}")

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        latencies = []
        successful = 0
        failed = 0
        chunks_received = []

        start_time = time.time()

        # 测试单个流式请求
        try:
            request_start = time.time()
            ttfb = None  # 首字节时间

            async with client.stream(
                "POST",
                f"{base_url}{endpoint}",
                json={"url": "https://www.bilibili.com/video/BV1xx411c7mD"}
            ) as response:
                if response.status_code == 200:
                    chunk_count = 0
                    async for chunk in response.aiter_text():
                        if ttfb is None:
                            ttfb = time.time() - request_start

                        if chunk.strip():
                            chunk_count += 1
                            chunks_received.append(chunk)

                        # 限制读取的块数（避免测试时间过长）
                        if chunk_count >= 10:
                            break

                    successful = 1
                    latency = time.time() - request_start
                    latencies.append(latency)

                    print(f"  ✅ 流式请求成功")
                    print(f"     首字节时间(TTFB): {ttfb*1000:.2f}ms")
                    print(f"     接收块数: {chunk_count}")
                else:
                    failed = 1
                    print(f"  ❌ 流式请求失败: HTTP {response.status_code}")

        except Exception as e:
            failed = 1
            print(f"  ❌ 流式请求异常: {e}")

        total_duration = time.time() - start_time

    result = BenchmarkResult(
        framework=framework,
        endpoint=endpoint,
        total_requests=1,
        successful_requests=successful,
        failed_requests=failed,
        total_duration=total_duration,
        avg_latency=statistics.mean(latencies) if latencies else 0,
        min_latency=min(latencies) if latencies else 0,
        max_latency=max(latencies) if latencies else 0,
        p50_latency=statistics.median(latencies) if latencies else 0,
        p95_latency=statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else (max(latencies) if latencies else 0),
        p99_latency=statistics.quantiles(latencies, n=100)[98] if len(latencies) > 100 else (max(latencies) if latencies else 0),
        throughput=successful / total_duration if total_duration > 0 else 0
    )

    return result

async def test_async_operations(
    framework: str,
    base_url: str
) -> Dict[str, BenchmarkResult]:
    """
    测试异步操作性能对比

    Args:
        framework: 框架名称
        base_url: API 基础 URL
    """
    print(f"\n[{framework}] 开始异步操作性能测试")

    results = {}

    # 测试1: 同步操作
    print(f"\n  测试1: 同步操作 (阻塞 1s)")
    start = time.time()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/sync/test")
            if response.status_code == 200:
                duration = time.time() - start
                print(f"  ✅ 同步操作耗时: {duration:.2f}s")
                results["sync"] = duration
    except Exception as e:
        print(f"  ❌ 同步操作测试失败: {e}")
        results["sync"] = None

    # 测试2: 异步操作
    print(f"\n  测试2: 异步操作 (await 1s)")
    start = time.time()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/async/test")
            if response.status_code == 200:
                duration = time.time() - start
                print(f"  ✅ 异步操作耗时: {duration:.2f}s")
                results["async"] = duration
    except Exception as e:
        print(f"  ❌ 异步操作测试失败: {e}")
        results["async"] = None

    # 测试3: 并发操作
    print(f"\n  测试3: 并发操作 (5个任务并行)")
    start = time.time()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/concurrent/test")
            if response.status_code == 200:
                duration = time.time() - start
                data = response.json()
                print(f"  ✅ 并发操作耗时: {duration:.2f}s")
                print(f"     执行任务数: {data.get('tasks')}")
                results["concurrent"] = duration
    except Exception as e:
        print(f"  ❌ 并发操作测试失败: {e}")
        results["concurrent"] = None

    return results

# ========== 对比分析 ==========

def compare_results(flask_result: BenchmarkResult, fastapi_result: BenchmarkResult):
    """
    对比 Flask 和 FastAPI 性能差异

    Args:
        flask_result: Flask 测试结果
        fastapi_result: FastAPI 测试结果
    """
    print(f"\n{'='*60}")
    print(f"性能对比分析: Flask vs FastAPI")
    print(f"{'='*60}")

    # 计算性能提升百分比
    throughput_improvement = (
        (fastapi_result.throughput - flask_result.throughput) / flask_result.throughput * 100
        if flask_result.throughput > 0 else 0
    )

    latency_improvement = (
        (flask_result.p99_latency - fastapi_result.p99_latency) / flask_result.p99_latency * 100
        if flask_result.p99_latency > 0 else 0
    )

    print(f"\n吞吐量对比:")
    print(f"  Flask:  {flask_result.throughput:.2f} req/s")
    print(f"  FastAPI: {fastapi_result.throughput:.2f} req/s")
    print(f"  提升:   {throughput_improvement:+.1f}%")

    print(f"\nP99 延迟对比:")
    print(f"  Flask:  {flask_result.p99_latency*1000:.2f}ms")
    print(f"  FastAPI: {fastapi_result.p99_latency*1000:.2f}ms")
    print(f"  降低:   {latency_improvement:+.1f}%")

    print(f"\n成功率对比:")
    print(f"  Flask:  {flask_result.successful_requests}/{flask_result.total_requests} ({flask_result.successful_requests/flask_result.total_requests*100:.1f}%)")
    print(f"  FastAPI: {fastapi_result.successful_requests}/{fastapi_result.total_requests} ({fastapi_result.successful_requests/fastapi_result.total_requests*100:.1f}%)")

    print(f"{'='*60}\n")

    return {
        "throughput_improvement": throughput_improvement,
        "latency_improvement": latency_improvement
    }

# ========== 主测试流程 ==========

async def run_full_benchmark():
    """
    运行完整的基准测试套件
    """
    print("\n" + "="*60)
    print("异步框架性能基准测试")
    print("="*60)
    print(f"测试配置:")
    print(f"  - 并发请求数: {CONCURRENT_REQUESTS}")
    print(f"  - 总请求数: {TOTAL_REQUESTS}")
    print(f"  - 超时时间: {TIMEOUT}s")
    print(f"  - Flask URL: {FLASK_BASE_URL}")
    print(f"  - FastAPI URL: {FASTAPI_BASE_URL}")
    print("="*60)

    results = {
        "flask": {},
        "fastapi": {}
    }

    # 测试1: 并发请求性能
    print("\n" + "="*60)
    print("测试1: 并发请求性能")
    print("="*60)

    try:
        results["flask"]["concurrent"] = await test_concurrent_requests(
            "Flask", FLASK_BASE_URL, "/api/health"
        )
    except Exception as e:
        print(f"❌ Flask 并发测试失败: {e}")
        print("   提示: 请确保 Flask 应用正在运行 (python app.py)")

    try:
        results["fastapi"]["concurrent"] = await test_concurrent_requests(
            "FastAPI", FASTAPI_BASE_URL, "/api/health"
        )
    except Exception as e:
        print(f"❌ FastAPI 并发测试失败: {e}")
        print("   提示: 请确保 FastAPI 应用正在运行 (python poc/fastapi_app.py)")

    # 对比并发测试结果
    if "concurrent" in results["flask"] and "concurrent" in results["fastapi"]:
        compare_results(
            results["flask"]["concurrent"],
            results["fastapi"]["concurrent"]
        )

    # 测试2: SSE 流式响应
    print("\n" + "="*60)
    print("测试2: SSE 流式响应性能")
    print("="*60)

    try:
        results["flask"]["sse"] = await test_sse_stream(
            "Flask", FLASK_BASE_URL, "/api/analyze"
        )
    except Exception as e:
        print(f"❌ Flask SSE 测试失败: {e}")

    try:
        results["fastapi"]["sse"] = await test_sse_stream(
            "FastAPI", FASTAPI_BASE_URL, "/api/analyze"
        )
    except Exception as e:
        print(f"❌ FastAPI SSE 测试失败: {e}")

    # 测试3: 异步操作性能（仅 FastAPI）
    print("\n" + "="*60)
    print("测试3: 异步操作性能（仅 FastAPI）")
    print("="*60)

    try:
        results["fastapi"]["async_ops"] = await test_async_operations(
            "FastAPI", FASTAPI_BASE_URL
        )
    except Exception as e:
        print(f"❌ FastAPI 异步操作测试失败: {e}")

    # 保存结果
    save_results(results)

    print("\n" + "="*60)
    print("测试完成！结果已保存到 results/benchmark_results.json")
    print("="*60 + "\n")

    return results

def save_results(results: Dict):
    """
    保存测试结果到 JSON 文件
    """
    import os
    os.makedirs("results", exist_ok=True)

    # 转换为可序列化的格式
    serializable_results = {
        "timestamp": time.time(),
        "flask": {
            key: value.to_dict() if isinstance(value, BenchmarkResult) else value
            for key, value in results.get("flask", {}).items()
        },
        "fastapi": {
            key: value.to_dict() if isinstance(value, BenchmarkResult) else value
            for key, value in results.get("fastapi", {}).items()
        }
    }

    with open("results/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(serializable_results, f, indent=2, ensure_ascii=False)

    print("\n✅ 结果已保存到 results/benchmark_results.json")

# ========== 入口点 ==========

if __name__ == "__main__":
    print("\n🚀 启动异步框架性能基准测试...")

    # 检查依赖
    try:
        import httpx
    except ImportError:
        print("❌ 缺少依赖: httpx")
        print("请运行: pip install httpx")
        exit(1)

    # 运行测试
    asyncio.run(run_full_benchmark())
