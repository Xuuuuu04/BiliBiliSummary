"""
单元测试 - APIResponse 工具类

测试统一响应格式
"""

import pytest
import json
from flask import Flask
from src.backend.api.utils.response import APIResponse


@pytest.fixture
def app():
    """Flask 应用 fixture"""
    app = Flask(__name__)
    return app


class TestAPIResponse:
    """APIResponse 工具类测试"""

    def test_success_response(self, app):
        """测试成功响应"""
        with app.app_context():
            response, status_code = APIResponse.success(data={'test': 'data'})

            assert status_code == 200

            # 解析 JSON 响应
            data = json.loads(response.get_data(as_text=True))
            assert data['success'] is True
            assert data['data'] == {'test': 'data'}

    def test_success_response_with_message(self, app):
        """测试带消息的成功响应"""
        with app.app_context():
            response, status_code = APIResponse.success(
                data={'test': 'data'},
                message='操作成功'
            )

            data = json.loads(response.get_data(as_text=True))
            assert data['message'] == '操作成功'

    def test_success_response_with_meta(self, app):
        """测试带元数据的成功响应"""
        with app.app_context():
            meta = {'page': 1, 'total': 100}
            response, status_code = APIResponse.success(
                data=[1, 2, 3],
                meta=meta
            )

            data = json.loads(response.get_data(as_text=True))
            assert data['meta'] == meta

    def test_error_response(self, app):
        """测试错误响应"""
        with app.app_context():
            response, status_code = APIResponse.error(
                error_msg='测试错误',
                status_code=400
            )

            assert status_code == 400

            data = json.loads(response.get_data(as_text=True))
            assert data['success'] is False
            assert data['error'] == '测试错误'

    def test_error_response_with_code(self, app):
        """测试带错误码的错误响应"""
        with app.app_context():
            response, status_code = APIResponse.error(
                error_msg='验证失败',
                error_code='VALIDATION_ERROR',
                status_code=400
            )

            data = json.loads(response.get_data(as_text=True))
            assert data['error_code'] == 'VALIDATION_ERROR'

    def test_paginated_response(self, app):
        """测试分页响应"""
        with app.app_context():
            response, status_code = APIResponse.paginated(
                data=[1, 2, 3],
                page=1,
                page_size=10,
                total=25
            )

            data = json.loads(response.get_data(as_text=True))
            assert data['meta']['pagination']['page'] == 1
            assert data['meta']['pagination']['total_pages'] == 3
            assert data['meta']['pagination']['has_next'] is True
            assert data['meta']['pagination']['has_prev'] is False

    def test_not_found_response(self, app):
        """测试 404 响应"""
        with app.app_context():
            response, status_code = APIResponse.not_found('视频')

            assert status_code == 404
            data = json.loads(response.get_data(as_text=True))
            assert '不存在' in data['error']

    def test_unauthorized_response(self, app):
        """测试 401 响应"""
        with app.app_context():
            response, status_code = APIResponse.unauthorized()

            assert status_code == 401
            data = json.loads(response.get_data(as_text=True))
            assert data['error_code'] == 'UNAUTHORIZED'

    def test_rate_limit_response(self, app):
        """测试 429 响应"""
        with app.app_context():
            response, status_code = APIResponse.rate_limit_exceeded(retry_after=60)

            assert status_code == 429
            data = json.loads(response.get_data(as_text=True))
            assert data['error_code'] == 'RATE_LIMIT_EXCEEDED'
            assert data['details']['retry_after'] == 60
