"""
测试 error_handler.py 模块

测试目标：
- 异常类定义
- 错误响应构建
- SSE 错误响应
- 从异常构建响应
- 错误处理装饰器
- 敏感信息过滤
"""
import pytest
from flask import Flask, jsonify
from src.backend.utils.error_handler import (
    BaseAppException,
    ValidationError,
    NotFoundError,
    ExternalServiceError,
    ConfigurationError,
    ErrorResponse,
    handle_errors,
    sanitize_error_message
)


class TestBaseAppException:
    """测试基础异常类"""

    def test_base_exception_creation(self):
        """测试创建基础异常"""
        exc = BaseAppException("Test error")
        assert exc.message == "Test error"
        assert exc.status_code == 500
        assert exc.error_code == "BaseAppException"

    def test_base_exception_with_all_params(self):
        """测试带所有参数的基础异常"""
        exc = BaseAppException(
            message="Error message",
            error_code="CUSTOM_ERROR",
            details={"key": "value"},
            status_code=400
        )
        assert exc.message == "Error message"
        assert exc.error_code == "CUSTOM_ERROR"
        assert exc.details == {"key": "value"}
        assert exc.status_code == 400

    def test_base_exception_str_representation(self):
        """测试异常的字符串表示"""
        exc = BaseAppException("Test error")
        assert str(exc) == "Test error"


class TestValidationError:
    """测试验证错误异常"""

    def test_validation_error_creation(self):
        """测试创建验证错误"""
        exc = ValidationError("Invalid input")
        assert exc.message == "Invalid input"
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.status_code == 400

    def test_validation_error_with_field(self):
        """测试带字段的验证错误"""
        exc = ValidationError("Invalid input", field="username")
        assert exc.details['field'] == "username"

    def test_validation_error_with_details(self):
        """测试带详细信息的验证错误"""
        exc = ValidationError("Invalid input", field="email", details={"max_length": 100})
        assert exc.details['field'] == "email"
        assert exc.details['max_length'] == 100


class TestNotFoundError:
    """测试未找到错误异常"""

    def test_not_found_error_creation(self):
        """测试创建未找到错误"""
        exc = NotFoundError("Video")
        assert exc.message == "Video 不存在"
        assert exc.error_code == "NOT_FOUND"
        assert exc.status_code == 404

    def test_not_found_error_with_id(self):
        """测试带ID的未找到错误"""
        exc = NotFoundError("Video", "BV123")
        assert exc.message == "Video 不存在: BV123"
        assert exc.details['resource_type'] == "Video"
        assert exc.details['resource_id'] == "BV123"


class TestExternalServiceError:
    """测试外部服务错误异常"""

    def test_external_service_error_default_message(self):
        """测试外部服务错误默认消息"""
        exc = ExternalServiceError("BilibiliAPI")
        assert exc.message == "BilibiliAPI 服务暂时不可用"
        assert exc.error_code == "EXTERNAL_SERVICE_ERROR"
        assert exc.status_code == 503

    def test_external_service_error_custom_message(self):
        """测试自定义外部服务错误消息"""
        exc = ExternalServiceError("BilibiliAPI", "Connection timeout")
        assert exc.message == "Connection timeout"
        assert exc.details['service'] == "BilibiliAPI"


class TestConfigurationError:
    """测试配置错误异常"""

    def test_configuration_error_creation(self):
        """测试创建配置错误"""
        exc = ConfigurationError("Missing API key")
        assert exc.message == "Missing API key"
        assert exc.error_code == "CONFIGURATION_ERROR"
        assert exc.status_code == 500

    def test_configuration_error_with_config_key(self):
        """测试带配置键的配置错误"""
        exc = ConfigurationError("Invalid value", config_key="OPENAI_API_KEY")
        assert exc.details['config_key'] == "OPENAI_API_KEY"


class TestErrorResponse:
    """测试错误响应构建器"""

    def test_error_response_basic(self):
        """测试基础错误响应"""
        response, status_code = ErrorResponse.error(
            error_msg="Something went wrong",
            status_code=500
        )
        assert response['success'] is False
        assert response['error'] == "Something went wrong"
        assert status_code == 500

    def test_error_response_with_error_code(self):
        """测试带错误码的响应"""
        response, status_code = ErrorResponse.error(
            error_msg="Validation failed",
            error_code="VALIDATION_ERROR",
            status_code=400
        )
        assert response['error_code'] == "VALIDATION_ERROR"
        assert status_code == 400

    def test_error_response_with_details(self):
        """测试带详细信息的响应"""
        response, status_code = ErrorResponse.error(
            error_msg="Invalid input",
            error_code="VALIDATION_ERROR",
            details={"field": "email", "value": "invalid"},
            status_code=400
        )
        assert response['details'] == {"field": "email", "value": "invalid"}

    def test_sse_error_response_basic(self):
        """测试基础 SSE 错误响应"""
        response = ErrorResponse.sse_error("Error occurred")
        assert "data:" in response
        assert "Error occurred" in response
        assert '"type": "error"' in response

    def test_sse_error_response_with_type(self):
        """测试带类型的 SSE 错误响应"""
        response = ErrorResponse.sse_error("Network error", error_type="network")
        assert '"error_type": "network"' in response
        assert "Network error" in response

    def test_from_exception_with_base_app_exception(self):
        """测试从 BaseAppException 构建响应"""
        exc = ValidationError("Invalid input", field="username")
        response, status_code = ErrorResponse.from_exception(exc)

        assert response['success'] is False
        assert response['error'] == "Invalid input"
        assert response['error_code'] == "VALIDATION_ERROR"
        assert response['details']['field'] == "username"
        assert status_code == 400

    def test_from_exception_with_generic_exception(self):
        """测试从通用异常构建响应"""
        exc = Exception("Unexpected error")
        response, status_code = ErrorResponse.from_exception(exc)

        assert response['success'] is False
        assert response['error'] == "服务器内部错误"
        assert response['error_code'] == "INTERNAL_ERROR"
        assert status_code == 500


class TestHandleErrorsDecorator:
    """测试错误处理装饰器"""

    def test_handle_errors_with_no_exception(self, mock_logger):
        """测试没有异常时正常执行"""
        app = Flask(__name__)

        @app.route('/test')
        @handle_errors
        def test_route():
            return jsonify({"success": True, "data": "result"}), 200

        with app.test_client() as client:
            response = client.get('/test')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True

    def test_handle_errors_with_base_app_exception(self, mock_logger):
        """测试捕获 BaseAppException"""
        app = Flask(__name__)

        @app.route('/test')
        @handle_errors
        def test_route():
            raise ValidationError("Invalid input", field="email")

        with app.test_client() as client:
            response = client.get('/test')
            assert response.status_code == 400
            data = response.get_json()
            assert data['success'] is False
            assert data['error'] == "Invalid input"
            assert data['error_code'] == "VALIDATION_ERROR"

    def test_handle_errors_with_generic_exception(self, mock_logger):
        """测试捕获通用异常"""
        app = Flask(__name__)

        @app.route('/test')
        @handle_errors
        def test_route():
            raise ValueError("Unexpected error")

        with app.test_client() as client:
            response = client.get('/test')
            assert response.status_code == 500
            data = response.get_json()
            assert data['success'] is False
            assert data['error'] == "服务器内部错误"
            assert data['error_code'] == "INTERNAL_ERROR"

    def test_handle_errors_with_not_found_exception(self, mock_logger):
        """测试捕获 NotFoundError"""
        app = Flask(__name__)

        @app.route('/test')
        @handle_errors
        def test_route():
            raise NotFoundError("Video", "BV123")

        with app.test_client() as client:
            response = client.get('/test')
            assert response.status_code == 404
            data = response.get_json()
            assert data['success'] is False
            assert "Video 不存在" in data['error']

    def test_handle_errors_preserves_function_metadata(self):
        """测试装饰器保留函数元数据"""
        @handle_errors
        def test_function():
            """Test function docstring"""
            pass

        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ == "Test function docstring"


class TestSanitizeErrorMessage:
    """测试错误消息敏感信息过滤"""

    def test_sanitize_basic_error(self):
        """测试基本错误消息"""
        exc = Exception("Simple error message")
        result = sanitize_error_message(exc)
        assert result == "Simple error message"

    def test_sanitize_removes_file_path(self):
        """测试移除文件路径"""
        exc = Exception("File '/path/to/file.py', line 123: error")
        result = sanitize_error_message(exc)
        assert "File " not in result
        assert "'/path/to/file.py'" not in result

    def test_sanitize_removes_line_number(self):
        """测试移除行号"""
        exc = Exception("Error at line 456")
        result = sanitize_error_message(exc)
        assert ", line 456" not in result

    def test_sanitize_removes_both_file_and_line(self):
        """测试同时移除文件路径和行号"""
        exc = Exception("File '/secret/path/config.py', line 789: configuration error")
        result = sanitize_error_message(exc)
        assert "File " not in result
        assert "line 789" not in result
        assert "configuration error" in result

    def test_sanitize_preserves_normal_message(self):
        """测试保留正常错误消息"""
        exc = Exception("Database connection failed: timeout")
        result = sanitize_error_message(exc)
        assert "Database connection failed: timeout" in result

    def test_sanitize_empty_error(self):
        """测试空错误消息"""
        exc = Exception("")
        result = sanitize_error_message(exc)
        assert result == ""

    def test_sanitize_multiline_error(self):
        """测试多行错误消息"""
        exc = Exception("Line 1\nFile '/path/to/file.py', line 10\nLine 3")
        result = sanitize_error_message(exc)
        # 文件路径应被移除
        assert "'/path/to/file.py'" not in result
        assert ", line 10" not in result
        # 其他内容保留
        assert "Line 1" in result or "Line 3" in result
