"""
工具插件系统测试脚本
验证工具注册、schema生成和基本功能
"""
import sys
import json
from src.backend.services.ai.toolkit import ToolRegistry
from src.backend.services.ai.toolkit.tools import (
    SearchVideosTool,
    AnalyzeVideoTool,
    WebSearchTool,
    SearchUsersTool,
    GetUserRecentVideosTool,
    FinishResearchTool
)


def test_tool_registration():
    """测试工具注册"""
    print("=" * 60)
    print("测试 1: 工具注册")
    print("=" * 60)

    # 清空注册中心
    ToolRegistry.clear()

    # 注册所有工具
    tools = [
        SearchVideosTool(),
        AnalyzeVideoTool(),
        WebSearchTool(),
        SearchUsersTool(),
        GetUserRecentVideosTool(),
        FinishResearchTool()
    ]

    for tool in tools:
        ToolRegistry.register(tool)

    print(f"✓ 成功注册 {ToolRegistry.count()} 个工具")
    print(f"✓ 工具列表: {', '.join(ToolRegistry.list_tools())}")
    print()


def test_tool_schemas():
    """测试工具Schema生成"""
    print("=" * 60)
    print("测试 2: 工具Schema生成")
    print("=" * 60)

    schemas = ToolRegistry.list_tools_schema()

    print(f"✓ 生成了 {len(schemas)} 个工具Schema\n")

    for i, schema in enumerate(schemas, 1):
        func_name = schema['function']['name']
        func_desc = schema['function']['description']
        params = schema['function']['parameters']

        print(f"{i}. {func_name}")
        print(f"   描述: {func_desc}")
        print(f"   参数: {json.dumps(params, ensure_ascii=False)}")
        print()


def test_tool_retrieval():
    """测试工具获取"""
    print("=" * 60)
    print("测试 3: 工具获取")
    print("=" * 60)

    # 测试获取单个工具
    search_tool = ToolRegistry.get_tool('search_videos')
    print(f"✓ 获取工具: {search_tool.name}")
    print(f"  描述: {search_tool.description}")
    print(f"  类名: {search_tool.__class__.__name__}")
    print()

    # 测试工具信息
    tool_info = ToolRegistry.get_tool_info('search_videos')
    print(f"✓ 工具详细信息:")
    print(f"  名称: {tool_info['name']}")
    print(f"  模块: {tool_info['module']}")
    print()


def test_parameter_validation():
    """测试参数验证"""
    print("=" * 60)
    print("测试 4: 参数验证")
    print("=" * 60)

    search_tool = ToolRegistry.get_tool('search_videos')

    # 测试有效参数
    valid_args = {'keyword': 'Python教程'}
    is_valid = search_tool.validate_args(valid_args)
    print(f"✓ 有效参数验证: {is_valid} (keyword='Python教程')")

    # 测试无效参数（缺少必需参数）
    invalid_args = {}
    is_valid = search_tool.validate_args(invalid_args)
    print(f"✓ 无效参数验证: {is_valid} (缺少keyword)")
    print()


def test_tool_categories():
    """测试工具分类"""
    print("=" * 60)
    print("测试 5: 工具分类")
    print("=" * 60)

    # 注册分类工具
    ToolRegistry.clear()
    ToolRegistry.register(SearchVideosTool(), category='bilibili')
    ToolRegistry.register(WebSearchTool(), category='external')

    print(f"✓ 所有工具: {ToolRegistry.list_tools()}")
    print(f"✓ B站工具: {ToolRegistry.list_tools(category='bilibili')}")
    print(f"✓ 外部工具: {ToolRegistry.list_tools(category='external')}")
    print()


def test_tool_unregistration():
    """测试工具注销"""
    print("=" * 60)
    print("测试 6: 工具注销")
    print("=" * 60)

    # 注销前
    count_before = ToolRegistry.count()
    print(f"注销前工具数量: {count_before}")

    # 注销工具
    success = ToolRegistry.unregister('search_videos')
    print(f"✓ 注销 'search_videos': {success}")

    # 注销后
    count_after = ToolRegistry.count()
    print(f"注销后工具数量: {count_after}")
    print()


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("工具插件系统测试")
    print("=" * 60 + "\n")

    try:
        test_tool_registration()
        test_tool_schemas()
        test_tool_retrieval()
        test_parameter_validation()
        test_tool_categories()
        test_tool_unregistration()

        print("=" * 60)
        print("✓ 所有测试通过!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
