"""
pytest 配置文件和共享 fixtures
"""
import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Dict, Any

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def event_loop():
    """创建整个测试会话共享的事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_bilibili_service():
    """Mock BilibiliService"""
    service = Mock()
    service.get_video_info = AsyncMock(return_value={'success': True, 'data': {}})
    service.get_video_subtitles = AsyncMock(return_value=[])
    service.get_video_danmaku = AsyncMock(return_value=[])
    service.get_video_comments = AsyncMock(return_value=[])
    return service


@pytest.fixture
def sample_video_data() -> Dict[str, Any]:
    """示例视频数据"""
    return {
        'bvid': 'BV1xx411c7m1',
        'title': '测试视频标题',
        'desc': '这是一个测试视频的描述',
        'owner': {
            'name': '测试UP主',
            'mid': 123456789
        },
        'duration': 365,  # 6分5秒
        'view': 10000,
        'like': 500,
        'coin': 200,
        'favorite': 150,
        'share': 50,
        'pubdate': 1704067200  # 2024-01-01
    }


@pytest.fixture
def sample_danmaku_list():
    """示例弹幕数据"""
    class MockDanmaku:
        def __init__(self, text: str):
            self.text = text

    return [MockDanmaku(f'弹幕{i}') for i in range(100)]


@pytest.fixture
def sample_comments_list():
    """示例评论数据"""
    class MockComment:
        def __init__(self, content: str):
            self.content = content
            self.like = 10
            self.reply = 5

    return [MockComment(f'评论{i}') for i in range(50)]


@pytest.fixture
def sample_user_data():
    """示例用户数据"""
    return {
        'mid': 123456789,
        'name': '测试用户',
        'sex': '男',
        'sign': '这是个性签名',
        'level': 6,
        'face': 'https://example.com/avatar.jpg',
        'follower': 10000,
        'following': 100,
        'video_count': 50
    }


@pytest.fixture
def mock_ai_service():
    """Mock AIService"""
    service = Mock()
    service.analyze_video = AsyncMock(return_value='这是分析结果')
    service.chat = AsyncMock(return_value='这是回答')
    return service


@pytest.fixture
def mock_config():
    """Mock 配置对象"""
    config = Mock()
    config.OPENAI_API_KEY = 'test-api-key'
    config.OPENAI_API_BASE = 'https://api.test.com/v1'
    config.OPENAI_MODEL = 'test-model'
    config.QA_MODEL = 'test-qa-model'
    config.DEEP_RESEARCH_MODEL = 'test-research-model'
    config.BILIBILI_SESSDATA = ''
    config.FLASK_PORT = 5000
    config.FLASK_HOST = 'localhost'
    config.FLASK_DEBUG = False
    return config


@pytest.fixture
def temp_env_file(tmp_path):
    """创建临时 .env 文件"""
    env_file = tmp_path / ".env"
    env_file.write_text("# Test env file\nTEST_KEY=test_value\n")
    return env_file


@pytest.fixture
def mock_async_response():
    """Mock 异步响应"""
    async def mock_func(*args, **kwargs):
        return {'success': True, 'data': {}}

    return mock_func


@pytest.fixture
def sample_article_data():
    """示例专栏数据"""
    return {
        'id': 12345,
        'title': '测试专栏标题',
        'summary': '这是专栏摘要',
        'content': '这是专栏正文内容',
        'author': {
            'mid': 123456789,
            'name': '测试作者'
        },
        'views': 5000,
        'likes': 300
    }


@pytest.fixture
def sample_search_results():
    """示例搜索结果"""
    class MockVideo:
        def __init__(self, bvid: str, title: str):
            self.bvid = bvid
            self.title = title
            self.author = '测试UP主'
            self.duration = 300

    return [MockVideo(f'BV{i}x411c7m1', f'测试视频{i}') for i in range(10)]


@pytest.fixture
def mock_credential():
    """Mock B站凭据"""
    class MockCredential:
        def __init__(self):
            self.sessdata = 'test_sessdata'
            self.bili_jct = 'test_bili_jct'
            self.buvid3 = 'test_buvid3'
            self.dedeuserid = 'test_userid'

    return MockCredential()


@pytest.fixture
def sample_opus_data():
    """示例 Opus 动态数据"""
    return {
        'id': 987654321,
        'title': '测试动态标题',
        'content': '这是动态内容',
        'author': {
            'mid': 123456789,
            'name': '测试用户'
        },
        'publish_time': 1704067200,
        'likes': 1000
    }


@pytest.fixture
def error_response_data():
    """错误响应数据"""
    return {
        'success': False,
        'error': '测试错误消息',
        'error_code': 'TEST_ERROR',
        'details': {'field': 'test_field'}
    }


@pytest.fixture
def mock_logger():
    """Mock logger"""
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def sample_frame_params():
    """示例视频帧参数"""
    return {
        'duration': 600,  # 10分钟
        'expected_max_frames': 25,
        'expected_interval': 24
    }


@pytest.fixture
def mock_http_client():
    """Mock HTTP 客户端"""
    client = Mock()
    client.get = AsyncMock(return_value=Mock(status_code=200, json=lambda: {}))
    client.post = AsyncMock(return_value=Mock(status_code=200, json=lambda: {}))
    return client


# 测试数据生成器
def generate_test_danmaku(count: int) -> list:
    """生成测试弹幕数据"""
    class MockDanmaku:
        def __init__(self, text: str):
            self.text = text

    return [MockDanmaku(f'弹幕{i}') for i in range(count)]


def generate_test_comments(count: int) -> list:
    """生成测试评论数据"""
    class MockComment:
        def __init__(self, content: str):
            self.content = content
            self.like = 10
            self.reply = 5

    return [MockComment(f'评论{i}') for i in range(count)]


# 添加到 conftest 以便在其他测试中使用
pytest.generate_test_danmaku = generate_test_danmaku
pytest.generate_test_comments = generate_test_comments
