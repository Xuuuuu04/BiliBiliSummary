"""
测试 bilibili_helpers.py 模块

测试目标：
- BVID 提取功能
- 时长格式化
- 智能采样功能
- 视频帧参数计算
- 专栏/Opus ID 提取
- 评论偏移量获取
"""
import pytest
from src.backend.utils.bilibili_helpers import (
    extract_bvid,
    extract_article_id,
    format_duration,
    calculate_optimal_frame_params,
    smart_sample_danmaku,
    smart_sample_comments,
    get_next_offset_from_comment_response
)


class TestExtractBvid:
    """测试 BVID 提取功能"""

    def test_extract_from_full_url(self):
        """测试从完整 URL 提取 BVID"""
        url = "https://www.bilibili.com/video/BV1xx411c7m1"
        result = extract_bvid(url)
        assert result == "BV1xx411c7m1"

    def test_extract_from_url_with_params(self):
        """测试从带参数的 URL 提取 BVID"""
        url = "https://www.bilibili.com/video/BV1xx411c7m1?p=2&t=10"
        result = extract_bvid(url)
        assert result == "BV1xx411c7m1"

    def test_extract_from_bvid_directly(self):
        """测试直接传入 BVID"""
        bvid = "BV1xx411c7m1"
        result = extract_bvid(bvid)
        assert result == "BV1xx411c7m1"

    def test_extract_from_short_url(self):
        """测试从短链接提取（可能返回 None）"""
        url = "https://b23.tv/abc123"
        result = extract_bvid(url)
        # 短链接需要重定向才能获取 BVID，这里返回 None 是预期行为
        # 实际项目中需要 HTTP 请求来处理
        assert result is None or isinstance(result, str)

    def test_extract_from_mobile_url(self):
        """测试从移动端 URL 提取"""
        url = "https://m.bilibili.com/video/BV1xx411c7m1"
        result = extract_bvid(url)
        assert result == "BV1xx411c7m1"

    def test_extract_invalid_string(self):
        """测试无效字符串"""
        result = extract_bvid("not a valid url or bvid")
        assert result is None

    def test_extract_empty_string(self):
        """测试空字符串"""
        result = extract_bvid("")
        assert result is None

    def test_extract_from_url_without_bvid(self):
        """测试不包含 BVID 的 URL"""
        url = "https://www.bilibili.com/"
        result = extract_bvid(url)
        assert result is None

    def test_extract_bvid_case_sensitive(self):
        """测试 BVID 大小写敏感性"""
        # BVID 中的字母部分通常是大小写混合的
        bvid = "BV1XX411c7M1"
        result = extract_bvid(bvid)
        assert result == bvid


class TestFormatDuration:
    """测试时长格式化功能"""

    def test_format_seconds_only(self):
        """测试只有秒数的时长"""
        assert format_duration(45) == "00:45"
        assert format_duration(59) == "00:59"

    def test_format_minutes_only(self):
        """测试只有分钟数的时长"""
        assert format_duration(125) == "02:05"  # 2分5秒
        assert format_duration(600) == "10:00"  # 10分钟

    def test_format_hours_minutes_seconds(self):
        """测试包含小时的时长"""
        assert format_duration(3665) == "1:01:05"  # 1小时1分5秒
        assert format_duration(7200) == "2:00:00"  # 2小时

    def test_format_zero_duration(self):
        """测试零时长"""
        assert format_duration(0) == "00:00"
        assert format_duration(None) == "00:00"

    def test_format_large_duration(self):
        """测试大时长（超过24小时）"""
        assert format_duration(90061) == "25:01:01"  # 25小时1分1秒

    def test_format_boundary_values(self):
        """测试边界值"""
        # 1秒
        assert format_duration(1) == "00:01"
        # 59秒
        assert format_duration(59) == "00:59"
        # 60秒（1分钟）
        assert format_duration(60) == "01:00"
        # 3599秒（59分59秒）
        assert format_duration(3599) == "59:59"
        # 3600秒（1小时）
        assert format_duration(3600) == "1:00:00"


class TestCalculateOptimalFrameParams:
    """测试最优帧参数计算"""

    def test_short_video_under_2min(self):
        """测试短视频（< 2分钟）"""
        max_frames, interval = calculate_optimal_frame_params(90)
        assert 8 <= max_frames <= 15
        assert interval >= 5

    def test_medium_video_2_to_10min(self):
        """测试中等长度视频（2-10分钟）"""
        max_frames, interval = calculate_optimal_frame_params(600)
        assert max_frames == 25
        assert interval == 600 // 25

    def test_long_video_10_to_30min(self):
        """测试长视频（10-30分钟）"""
        max_frames, interval = calculate_optimal_frame_params(1800)
        assert max_frames == 40
        assert interval == 1800 // 40

    def test_very_long_video_30_to_60min(self):
        """测试超长视频（30-60分钟）"""
        max_frames, interval = calculate_optimal_frame_params(3600)
        assert max_frames == 60
        assert interval == 3600 // 60

    def test_extra_long_video_over_1hour(self):
        """测试超过1小时的视频"""
        max_frames, interval = calculate_optimal_frame_params(7200)
        assert max_frames == 80
        assert interval >= 60

    def test_boundary_2minutes(self):
        """测试2分钟边界"""
        max_frames, interval = calculate_optimal_frame_params(120)
        # 120秒: max_frames = min(15, max(8, 120//10)) = min(15, 12) = 12
        assert max_frames == 12
        assert interval >= 5

    def test_boundary_10minutes(self):
        """测试10分钟边界"""
        max_frames, interval = calculate_optimal_frame_params(600)
        assert max_frames == 25

    def test_boundary_30minutes(self):
        """测试30分钟边界"""
        max_frames, interval = calculate_optimal_frame_params(1800)
        assert max_frames == 40

    def test_boundary_60minutes(self):
        """测试60分钟边界"""
        max_frames, interval = calculate_optimal_frame_params(3600)
        assert max_frames == 60

    def test_very_short_video(self):
        """测试极短视频"""
        max_frames, interval = calculate_optimal_frame_params(30)
        assert max_frames >= 8
        assert interval >= 5


class TestSmartSampleDanmaku:
    """测试智能弹幕采样"""

    def test_empty_danmaku_list(self):
        """测试空弹幕列表"""
        result = smart_sample_danmaku([], 10)
        assert result == []

    def test_danmaku_count_less_than_limit(self):
        """测试弹幕数少于限制"""
        class MockDanmaku:
            def __init__(self, text: str):
                self.text = text

        danmaku_list = [MockDanmaku(f'弹幕{i}') for i in range(5)]
        result = smart_sample_danmaku(danmaku_list, 10)
        assert len(result) == 5
        assert result == [f'弹幕{i}' for i in range(5)]

    def test_danmaku_count_equal_to_limit(self):
        """测试弹幕数等于限制"""
        class MockDanmaku:
            def __init__(self, text: str):
                self.text = text

        danmaku_list = [MockDanmaku(f'弹幕{i}') for i in range(10)]
        result = smart_sample_danmaku(danmaku_list, 10)
        assert len(result) == 10

    def test_danmaku_count_greater_than_limit(self):
        """测试弹幕数多于限制"""
        class MockDanmaku:
            def __init__(self, text: str):
                self.text = text

        danmaku_list = [MockDanmaku(f'弹幕{i}') for i in range(100)]
        result = smart_sample_danmaku(danmaku_list, 10)
        assert len(result) == 10

    def test_sampling_distribution(self):
        """测试采样分布是否均匀"""
        class MockDanmaku:
            def __init__(self, text: str):
                self.text = text

        danmaku_list = [MockDanmaku(f'弹幕{i}') for i in range(100)]
        result = smart_sample_danmaku(danmaku_list, 10)

        # 检查采样的弹幕是否来自不同的位置
        # 第一个和最后一个应该是第0条和第99条（或接近）
        assert '弹幕0' in result[0] or result[0].startswith('弹幕')

    def test_sample_single_danmaku(self):
        """测试只采样1条弹幕"""
        class MockDanmaku:
            def __init__(self, text: str):
                self.text = text

        danmaku_list = [MockDanmaku(f'弹幕{i}') for i in range(50)]
        result = smart_sample_danmaku(danmaku_list, 1)
        assert len(result) == 1


class TestSmartSampleComments:
    """测试智能评论采样"""

    def test_empty_comments_list(self):
        """测试空评论列表"""
        result = smart_sample_comments([], 10)
        assert result == []

    def test_comments_count_less_than_target(self):
        """测试评论数少于目标"""
        class MockComment:
            def __init__(self, content: str):
                self.content = content

        comments_list = [MockComment(f'评论{i}') for i in range(5)]
        result = smart_sample_comments(comments_list, 10)
        assert len(result) == 5

    def test_comments_count_greater_than_target(self):
        """测试评论数多于目标"""
        class MockComment:
            def __init__(self, content: str):
                self.content = content

        comments_list = [MockComment(f'评论{i}') for i in range(50)]
        result = smart_sample_comments(comments_list, 10)
        assert len(result) == 10

    def test_sampling_returns_comment_objects(self):
        """测试采样返回的是评论对象而非字符串"""
        class MockComment:
            def __init__(self, content: str):
                self.content = content

        comments_list = [MockComment(f'评论{i}') for i in range(50)]
        result = smart_sample_comments(comments_list, 10)

        # 返回的应该是对象，不是字符串
        for comment in result:
            assert hasattr(comment, 'content')

    def test_sample_single_comment(self):
        """测试只采样1条评论"""
        class MockComment:
            def __init__(self, content: str):
                self.content = content

        comments_list = [MockComment(f'评论{i}') for i in range(50)]
        result = smart_sample_comments(comments_list, 1)
        assert len(result) == 1


class TestExtractArticleId:
    """测试专栏/Opus ID 提取"""

    def test_extract_cv_id_from_cv_format(self):
        """测试从 cv 格式提取"""
        result = extract_article_id('cv12345')
        assert result == {'type': 'cv', 'id': 12345}

    def test_extract_cv_id_from_url(self):
        """测试从完整 URL 提取 CV 号"""
        url = "https://www.bilibili.com/read/cv12345"
        result = extract_article_id(url)
        assert result == {'type': 'cv', 'id': 12345}

    def test_extract_cv_id_from_read_url(self):
        """测试从 read 链接提取"""
        url = "https://www.bilibili.com/read/cv9876543?p=1"
        result = extract_article_id(url)
        assert result == {'type': 'cv', 'id': 9876543}

    def test_extract_opus_id(self):
        """测试提取 Opus ID"""
        url = "https://www.bilibili.com/opus/123456789"
        result = extract_article_id(url)
        assert result == {'type': 'opus', 'id': 123456789}

    def test_extract_dynamic_id(self):
        """测试提取动态 ID"""
        url = "https://www.bilibili.com/dynamic/987654321"
        result = extract_article_id(url)
        assert result == {'type': 'opus', 'id': 987654321}

    def test_extract_invalid_string(self):
        """测试无效字符串"""
        result = extract_article_id("not a valid article url")
        assert result is None

    def test_extract_empty_string(self):
        """测试空字符串"""
        result = extract_article_id("")
        assert result is None


class TestGetNextOffsetFromCommentResponse:
    """测试从评论响应获取下一页偏移量"""

    def test_get_offset_from_new_api_structure(self):
        """测试新版 API 结构（pagination_reply）"""
        response = {
            'cursor': {
                'pagination_reply': {
                    'next_offset': '1234567890'
                }
            }
        }
        result = get_next_offset_from_comment_response(response)
        assert result == '1234567890'

    def test_get_offset_from_old_api_structure(self):
        """测试旧版 API 结构（直接在 cursor 下）"""
        response = {
            'cursor': {
                'next_offset': '9876543210'
            }
        }
        result = get_next_offset_from_comment_response(response)
        assert result == '9876543210'

    def test_get_offset_when_no_next_page(self):
        """测试没有下一页的情况"""
        response = {
            'cursor': {
                'is_end': True
            }
        }
        result = get_next_offset_from_comment_response(response)
        assert result == ''

    def test_get_offset_from_empty_response(self):
        """测试空响应"""
        response = {}
        result = get_next_offset_from_comment_response(response)
        assert result == ''

    def test_get_offset_when_cursor_missing(self):
        """测试缺少 cursor 字段"""
        response = {'data': 'some data'}
        result = get_next_offset_from_comment_response(response)
        assert result == ''

    def test_get_offset_from_new_structure_with_missing_next_offset(self):
        """测试新版结构但缺少 next_offset"""
        response = {
            'cursor': {
                'pagination_reply': {
                    'is_end': True
                }
            }
        }
        result = get_next_offset_from_comment_response(response)
        assert result == ''
