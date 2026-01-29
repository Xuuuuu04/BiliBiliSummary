"""
数据源抽象层测试脚本

测试所有数据源功能的正确性和一致性。
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.backend.services.data_sources import (
    DataSourceFactory,
    DataSourceAdapter,
    BilibiliSource,
    YouTubeSource,
    UnsupportedPlatformError,
)
from src.backend.utils.logger import get_logger

logger = get_logger(__name__)


class DataSourceTester:
    """数据源测试类"""

    def __init__(self):
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = []

    def print_header(self, title: str):
        """打印测试标题"""
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80)

    def print_test(self, test_name: str, passed: bool, message: str = ""):
        """打印测试结果"""
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"  {message}")

        if passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1

        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'message': message
        })

    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 80)
        print("  测试摘要")
        print("=" * 80)
        total = self.passed_tests + self.failed_tests
        print(f"总计: {total} | 通过: {self.passed_tests} | 失败: {self.failed_tests}")
        print(f"成功率: {self.passed_tests / total * 100:.1f}%")
        print("=" * 80 + "\n")

    def test_factory_registration(self):
        """测试工厂注册功能"""
        self.print_header("测试1: 数据源工厂注册")

        # 测试获取支持的平台
        platforms = DataSourceFactory.get_supported_platforms()
        self.print_test(
            "获取支持的平台列表",
            'bilibili' in platforms and 'youtube' in platforms,
            f"支持的平台: {platforms}"
        )

        # 测试获取支持的域名
        domains = DataSourceFactory.get_supported_domains()
        has_bilibili = 'bilibili.com' in domains and 'b23.tv' in domains
        has_youtube = 'youtube.com' in domains and 'youtu.be' in domains
        self.print_test(
            "获取支持的域名列表",
            has_bilibili and has_youtube,
            f"支持的域名: {domains}"
        )

    def test_url_recognition(self):
        """测试URL识别功能"""
        self.print_header("测试2: URL识别")

        test_urls = [
            ("https://www.bilibili.com/video/BV1xx411c7mD", True, "B站完整链接"),
            ("https://b23.tv/xxxxx", True, "B站短链接"),
            ("BV1xx411c7mD", True, "直接BVID"),
            ("https://www.youtube.com/watch?v=xxx", True, "YouTube完整链接"),
            ("https://youtu.be/xxx", True, "YouTube短链接"),
            ("https://www.douyin.com/video/xxx", False, "抖音（不支持）"),
        ]

        for url, expected, description in test_urls:
            result = DataSourceFactory.is_supported_url(url)
            self.print_test(
                f"识别URL: {description}",
                result == expected,
                f"URL: {url} -> {result}"
            )

    def test_platform_detection(self):
        """测试平台检测"""
        self.print_header("测试3: 平台检测")

        test_cases = [
            ("https://www.bilibili.com/video/BV1xx", "bilibili"),
            ("https://b23.tv/xxxxx", "bilibili"),
            ("https://www.youtube.com/watch?v=xxx", "youtube"),
            ("https://youtu.be/xxx", "youtube"),
        ]

        for url, expected_platform in test_cases:
            try:
                platform = DataSourceFactory.get_platform_from_url(url)
                self.print_test(
                    f"检测平台: {url}",
                    platform == expected_platform,
                    f"期望: {expected_platform}, 实际: {platform}"
                )
            except Exception as e:
                self.print_test(
                    f"检测平台: {url}",
                    False,
                    f"异常: {str(e)}"
                )

    def test_source_creation(self):
        """测试数据源创建"""
        self.print_header("测试4: 数据源创建")

        # 测试从URL创建
        try:
            source = DataSourceFactory.create_from_url("https://www.bilibili.com/video/BV1xx")
            self.print_test(
                "从B站URL创建数据源",
                isinstance(source, BilibiliSource),
                f"类型: {type(source).__name__}, 平台: {source.platform_name}"
            )
        except Exception as e:
            self.print_test("从B站URL创建数据源", False, str(e))

        # 测试从平台名称创建
        try:
            source = DataSourceFactory.create_by_platform("bilibili")
            self.print_test(
                "从平台名称创建B站数据源",
                isinstance(source, BilibiliSource),
                f"类型: {type(source).__name__}"
            )
        except Exception as e:
            self.print_test("从平台名称创建B站数据源", False, str(e))

        try:
            source = DataSourceFactory.create_by_platform("youtube")
            self.print_test(
                "从平台名称创建YouTube数据源",
                isinstance(source, YouTubeSource),
                f"类型: {type(source).__name__}"
            )
        except Exception as e:
            self.print_test("从平台名称创建YouTube数据源", False, str(e))

        # 测试不支持的平台
        try:
            source = DataSourceFactory.create_by_platform("douyin")
            self.print_test("创建不支持的平台（应抛出异常）", False, "未抛出异常")
        except UnsupportedPlatformError:
            self.print_test("创建不支持的平台（应抛出异常）", True, "正确抛出异常")
        except Exception as e:
            self.print_test("创建不支持的平台（应抛出异常）", False, f"错误异常: {e}")

    def test_bilibili_source_interface(self):
        """测试B站数据源接口"""
        self.print_header("测试5: B站数据源接口")

        source = BilibiliSource()

        # 测试属性
        self.print_test(
            "平台名称属性",
            source.platform_name == "bilibili",
            f"平台名: {source.platform_name}"
        )

        self.print_test(
            "支持域名属性",
            "bilibili.com" in source.supported_domains and "b23.tv" in source.supported_domains,
            f"域名: {source.supported_domains[:2]}..."
        )

        # 测试URL检查
        self.print_test(
            "检查B站URL",
            source.is_supported_url("https://www.bilibili.com/video/BV1xx"),
            "正确识别B站URL"
        )

        self.print_test(
            "检查非B站URL",
            not source.is_supported_url("https://www.youtube.com/watch?v=xxx"),
            "正确拒绝非B站URL"
        )

    def test_bilibili_id_extraction(self):
        """测试B站ID提取（异步）"""
        self.print_header("测试6: B站 ID提取")

        async def run_tests():
            source = BilibiliSource()

            # 测试视频ID提取
            test_urls = [
                ("BV1xx411c7mD", "BV1xx411c7mD", "直接BVID"),
                ("https://www.bilibili.com/video/BV1xx411c7mD", "BV1xx411c7mD", "完整链接"),
                # 注意: B23短链接需要重定向才能解析，这是预期行为
                # ("https://b23.tv/xxxxx", None, "短链接（需解析）"),
            ]

            for url, expected_id, description in test_urls:
                try:
                    video_id = await source.extract_video_id(url)
                    if expected_id is None:
                        self.print_test(
                            f"提取视频ID: {description}",
                            True,
                            f"URL: {url} -> ID: {video_id}"
                        )
                    else:
                        success = video_id == expected_id
                        self.print_test(
                            f"提取视频ID: {description}",
                            success,
                            f"期望: {expected_id}, 实际: {video_id}"
                        )
                except Exception as e:
                    self.print_test(f"提取视频ID: {description}", False, str(e))

            # 测试用户ID提取
            user_urls = [
                ("https://space.bilibili.com/123456", "123456", "用户主页"),
                ("123456", "123456", "直接UID"),
            ]

            for url, expected_uid, description in user_urls:
                try:
                    user_id = await source.extract_user_id(url)
                    success = user_id == expected_uid
                    self.print_test(
                        f"提取用户ID: {description}",
                        success,
                        f"期望: {expected_uid}, 实际: {user_id}"
                    )
                except Exception as e:
                    self.print_test(f"提取用户ID: {description}", False, str(e))

        asyncio.run(run_tests())

    def test_youtube_source_interface(self):
        """测试YouTube数据源接口"""
        self.print_header("测试7: YouTube数据源接口（预留）")

        source = YouTubeSource()

        # 测试属性
        self.print_test(
            "平台名称属性",
            source.platform_name == "youtube",
            f"平台名: {source.platform_name}"
        )

        self.print_test(
            "支持域名属性",
            "youtube.com" in source.supported_domains and "youtu.be" in source.supported_domains,
            f"域名: {source.supported_domains[:2]}..."
        )

    def test_adapter_integration(self):
        """测试适配器集成"""
        self.print_header("测试8: 适配器集成")

        adapter = DataSourceAdapter()

        # 测试获取支持的平台
        platforms = adapter.get_supported_platforms()
        self.print_test(
            "适配器获取支持平台",
            'bilibili' in platforms and 'youtube' in platforms,
            f"平台: {platforms}"
        )

        # 测试URL检查
        self.print_test(
            "适配器URL检查（B站）",
            adapter.is_supported_url("https://www.bilibili.com/video/BV1xx"),
            "正确识别B站URL"
        )

        self.print_test(
            "适配器URL检查（YouTube）",
            adapter.is_supported_url("https://www.youtube.com/watch?v=xxx"),
            "正确识别YouTube URL"
        )

        self.print_test(
            "适配器URL检查（不支持）",
            not adapter.is_supported_url("https://www.douyin.com/video/xxx"),
            "正确拒绝不支持的平台"
        )

    def run_all_tests(self):
        """运行所有测试"""
        print("\n")
        print("╔" + "═" * 78 + "╗")
        print("║" + " " * 20 + "数据源抽象层测试套件" + " " * 36 + "║")
        print("╚" + "═" * 78 + "╝")

        # 运行测试
        self.test_factory_registration()
        self.test_url_recognition()
        self.test_platform_detection()
        self.test_source_creation()
        self.test_bilibili_source_interface()
        self.test_bilibili_id_extraction()
        self.test_youtube_source_interface()
        self.test_adapter_integration()

        # 打印摘要
        self.print_summary()

        return self.failed_tests == 0


if __name__ == "__main__":
    tester = DataSourceTester()
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)
