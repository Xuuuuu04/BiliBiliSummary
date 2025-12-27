"""
API 端点集成测试

测试所有 API v1 端点的功能
"""

import pytest
from unittest.mock import patch, MagicMock


class TestHealthEndpoints:
    """健康检查端点测试"""

    def test_health_check(self, client):
        """测试基础健康检查"""
        response = client.get('/api/v1/health')

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'status' in data
        assert data['status'] == 'healthy'

    def test_detailed_health_check(self, client):
        """测试详细健康检查"""
        response = client.get('/api/v1/health/detailed')

        assert response.status_code in [200, 503]  # 服务可能降级
        data = response.get_json()
        assert 'success' in data
        assert 'services' in data


class TestVideoEndpoints:
    """视频端点测试"""

    @patch('src.backend.services.bilibili.video_service.VideoService.get_info')
    def test_get_video_info_success(self, mock_get_info, client):
        """测试成功获取视频信息"""
        # Mock 响应
        mock_get_info.return_value = {
            'success': True,
            'data': {
                'bvid': 'BV1test123',
                'title': '测试视频',
                'author': '测试UP主',
                'view': 1000
            }
        }

        response = client.get('/api/v1/video/BV1test123/info')

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['bvid'] == 'BV1test123'

    def test_get_video_info_invalid_bvid(self, client):
        """测试无效 BVID"""
        response = client.get('/api/v1/video/invalid_bvid/info')

        # 应该返回错误（但可能不是 404，因为 bilibili-api 可能会尝试处理）
        assert response.status_code >= 400


class TestSearchEndpoints:
    """搜索端点测试"""

    def test_search_videos_missing_keyword(self, client):
        """测试缺少关键词的搜索请求"""
        response = client.get('/api/v1/search/videos')

        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert '缺少搜索关键词' in data['error']


class TestResponseFormat:
    """响应格式测试"""

    def test_success_response_format(self, client):
        """测试成功响应格式"""
        response = client.get('/api/v1/health')

        data = response.get_json()
        assert 'success' in data
        assert isinstance(data['success'], bool)

    def test_error_response_format(self, client):
        """测试错误响应格式"""
        response = client.get('/api/v1/search/videos')

        data = response.get_json()
        assert 'success' in data
        assert data['success'] is False
        assert 'error' in data
