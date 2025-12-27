# 测试文档

## 概述

本项目的测试套件使用 **pytest** 框架构建，覆盖核心业务逻辑模块，确保代码质量和稳定性。

## 测试统计

### 总体情况
- **测试用例总数**: 191 个
- **通过率**: 100%
- **代码覆盖率**: **75%** ✅
- **测试框架**: pytest + pytest-asyncio + pytest-cov

### 覆盖率详情

| 模块 | 语句数 | 未覆盖 | 覆盖率 |
|------|--------|--------|--------|
| `bilibili_helpers.py` | 69 | 0 | **100%** ✅ |
| `error_handler.py` | 74 | 0 | **100%** ✅ |
| `validators.py` | 76 | 5 | 93% |
| `async_helpers.py` | 27 | 2 | 93% |
| `logger.py` | 109 | 21 | 81% |
| `config_manager.py` | 118 | 47 | 60% |
| `http_client.py` | 56 | 56 | 0% |
| **总计** | 531 | 131 | **75%** |

## 测试文件结构

```
tests/
├── conftest.py                  # pytest 配置和共享 fixtures
├── __init__.py
├── test_utils/
│   ├── __init__.py
│   ├── test_bilibili_helpers.py  # 49 个测试用例
│   ├── test_validators.py        # 72 个测试用例
│   ├── test_async_helpers.py     # 14 个测试用例
│   ├── test_error_handler.py     # 30 个测试用例
│   └── test_config_manager.py    # 26 个测试用例
└── pytest.ini                    # pytest 配置文件
```

## 测试用例分布

### 1. test_bilibili_helpers.py (49 tests)

测试 B站工具方法模块：
- **TestExtractBvid** (9 tests) - BVID 提取功能
- **TestFormatDuration** (6 tests) - 时长格式化
- **TestCalculateOptimalFrameParams** (10 tests) - 视频帧参数计算
- **TestSmartSampleDanmaku** (6 tests) - 智能弹幕采样
- **TestSmartSampleComments** (5 tests) - 智能评论采样
- **TestExtractArticleId** (7 tests) - 专栏/Opus ID 提取
- **TestGetNextOffsetFromCommentResponse** (6 tests) - 评论分页

### 2. test_validators.py (72 tests)

测试输入验证模块：
- **TestValidateString** (12 tests) - 字符串验证
- **TestValidateUrl** (10 tests) - URL 验证
- **TestValidateInteger** (11 tests) - 整数验证
- **TestValidateBvid** (7 tests) - BVID 验证
- **TestValidateSearchKeyword** (8 tests) - 搜索关键词验证
- **TestValidateJsonData** (8 tests) - JSON 数据验证
- **TestSanitizeMarkdown** (8 tests) - Markdown 清理
- **TestValidateQuestionInput** (8 tests) - 问题输入验证

### 3. test_async_helpers.py (14 tests)

测试异步工具模块：
- **TestRunAsync** (14 tests) - 异步转同步运行
  - 简单协程执行
  - 延迟处理
  - 异常处理
  - 嵌套调用
  - 并发执行

### 4. test_error_handler.py (30 tests)

测试错误处理模块：
- **TestBaseAppException** (3 tests) - 基础异常类
- **TestValidationError** (3 tests) - 验证错误
- **TestNotFoundError** (2 tests) - 未找到错误
- **TestExternalServiceError** (2 tests) - 外部服务错误
- **TestConfigurationError** (2 tests) - 配置错误
- **TestErrorResponse** (7 tests) - 错误响应构建
- **TestHandleErrorsDecorator** (5 tests) - 错误处理装饰器
- **TestSanitizeErrorMessage** (6 tests) - 敏感信息过滤

### 5. test_config_manager.py (26 tests)

测试配置管理器模块：
- **TestConfigManagerInit** (2 tests) - 初始化
- **TestConfigManagerGet** (3 tests) - 配置读取
- **TestConfigManagerSet** (3 tests) - 配置更新
- **TestUpdateBilibiliCredentials** (3 tests) - B站凭据管理
- **TestConfigWatcher** (3 tests) - 配置监听
- **TestIsSensitive** (7 tests) - 敏感信息判断
- **TestValidateRequired** (2 tests) - 必需配置验证
- **TestGetConfigSummary** (2 tests) - 配置摘要生成
- **TestConfigManagerEdgeCases** (1 test) - 边界情况

## 安装测试依赖

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 或单独安装测试依赖
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

## 运行测试

### 运行所有测试
```bash
pytest
```

### 运行特定模块测试
```bash
pytest tests/test_utils/test_bilibili_helpers.py
pytest tests/test_utils/test_validators.py
```

### 生成覆盖率报告
```bash
# HTML 报告（推荐）
pytest --cov=src/backend/utils --cov-report=html

# 终端报告
pytest --cov=src/backend/utils --cov-report=term-missing

# XML 报告（CI/CD）
pytest --cov=src/backend/utils --cov-report=xml
```

### 查看覆盖率报告
```bash
# HTML 报告（在浏览器中打开）
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows
xdg-open htmlcov/index.html # Linux
```

### 运行特定测试
```bash
# 运行单个测试类
pytest tests/test_utils/test_bilibili_helpers.py::TestExtractBvid

# 运行单个测试方法
pytest tests/test_utils/test_bilibili_helpers.py::TestExtractBvid::test_extract_from_full_url

# 使用关键字过滤
pytest -k "test_extract"
pytest -k "bvid or url"
```

### 并行运行测试（需要安装 pytest-xdist）
```bash
pip install pytest-xdist
pytest -n auto  # 自动检测CPU核心数
```

## pytest 配置

`pytest.ini` 配置说明：

```ini
[pytest]
# 测试路径
testpaths = tests

# 命令行选项
addopts =
    -v                          # 详细输出
    --tb=short                  # 简短的traceback
    -p no:warnings              # 禁用警告

# 测试标记
markers =
    slow: 慢速测试
    integration: 集成测试
    unit: 单元测试
    asyncio: 异步测试
```

## 编写测试指南

### 测试命名规范

- 测试文件: `test_<module_name>.py`
- 测试类: `Test<ClassName>`
- 测试函数: `test_<function_name>_<scenario>`

### AAA 模式（Arrange-Act-Assert）

```python
def test_example():
    # Arrange - 准备测试数据
    input_data = "test input"

    # Act - 执行被测试的代码
    result = process(input_data)

    # Assert - 验证结果
    assert result == "expected output"
```

### 使用 Fixtures

```python
# 在 conftest.py 中定义 fixture
@pytest.fixture
def sample_data():
    return {"key": "value"}

# 在测试中使用
def test_with_fixture(sample_data):
    assert sample_data["key"] == "value"
```

### Mock 外部依赖

```python
from unittest.mock import Mock, patch

def test_with_mock():
    # 创建 mock 对象
    mock_service = Mock()
    mock_service.get_data.return_value = {"result": "success"}

    # 使用 patch
    with patch('module.service', mock_service):
        result = function_under_test()
        assert result == "success"
```

### 异步测试

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

### 异常测试

```python
def test_raises_exception():
    with pytest.raises(ValidationError) as exc_info:
        validate_string("", min_length=1)

    assert "长度不能少于" in str(exc_info.value)
```

## 持续集成

### GitHub Actions 示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install -r requirements-dev.txt
      - run: pytest --cov=src/backend/utils --cov-report=xml
      - uses: codecov/codecov-action@v3
```

## 最佳实践

1. **测试独立性**: 每个测试应该独立运行，不依赖其他测试
2. **测试速度**: 保持测试快速运行，使用 mock 避免慢速操作
3. **测试清晰性**: 使用描述性的测试名称和注释
4. **边界测试**: 测试边界值和异常情况
5. **覆盖率**: 目标覆盖率 ≥ 70%
6. **及时更新**: 代码修改后及时更新对应测试

## 常见问题

### Q: 测试失败怎么办？
A:
1. 查看详细的错误信息：`pytest -v`
2. 使用 pdb 调试：`pytest --pdb`
3. 只运行失败的测试：`pytest --lf`

### Q: 如何测试私有方法？
A: 私有方法（以 `_` 开头）也应该被测试。可以直接导入测试：

```python
from module import _private_function

def test_private():
    result = _private_function()
    assert result is not None
```

### Q: Mock 对象如何配置？
A: 使用 `unittest.mock.Mock`：

```python
mock = Mock()
mock.method.return_value = "value"
mock.method.side_effect = Exception("error")
```

## 下一步计划

- [ ] 添加服务层测试（bilibili_service, ai_service）
- [ ] 添加 API 路由测试
- [ ] 添加集成测试
- [ ] 提高覆盖率到 80%+
- [ ] 添加性能测试

---

**最后更新**: 2025-12-27
**维护者**: AI 测试助手
