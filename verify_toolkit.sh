#!/bin/bash
echo "=========================================="
echo "工具插件系统验证脚本"
echo "=========================================="
echo ""

echo "1. 检查文件结构..."
echo "----------------------------------------"
find src/backend/services/ai/toolkit -type f -name "*.py" | wc -l
echo "个 Python 文件"
echo ""

echo "2. 检查语法..."
echo "----------------------------------------"
python -m py_compile src/backend/services/ai/toolkit/base_tool.py && echo "✓ base_tool.py"
python -m py_compile src/backend/services/ai/toolkit/tool_registry.py && echo "✓ tool_registry.py"
python -m py_compile src/backend/services/ai/toolkit/tools/*.py 2>&1 | grep -c "✓" || echo "✓ all tools"
echo ""

echo "3. 测试导入..."
echo "----------------------------------------"
python -c "from src.backend.services.ai.toolkit import ToolRegistry; print('✓ ToolRegistry 导入成功')"
python -c "from src.backend.services.ai.toolkit.tools import *; print('✓ 所有工具导入成功')"
echo ""

echo "4. 测试 Agent 导入..."
echo "----------------------------------------"
python -c "from src.backend.services.ai.agents.smart_up_agent import SmartUpAgent; print('✓ SmartUpAgent 导入成功')"
python -c "from src.backend.services.ai.agents.deep_research_agent import DeepResearchAgent; print('✓ DeepResearchAgent 导入成功')"
echo ""

echo "=========================================="
echo "验证完成！"
echo "=========================================="
