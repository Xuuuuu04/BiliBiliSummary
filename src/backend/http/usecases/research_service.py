"""
================================================================================
深度研究用例服务 (src/backend/http/usecases/research_service.py)
================================================================================

【架构位置】
位于 HTTP 层的用例子模块 (usecases/)，是深度研究业务逻辑的编排层。

【设计模式】
- 用例模式 (Use Case Pattern): 封装深度研究业务流程
- 代理模式: 将请求代理给 AIService 的深度研究功能
- 仓库模式: 管理研究报告文件的存储和检索

【主要功能】
1. 深度研究流式输出：
   - 接收研究课题
   - 调用 AI 深度研究服务
   - 流式返回研究进度和结果

2. 研究报告管理：
   - list_history(): 列出所有历史报告
   - resolve_download_path(): 解析报告下载路径
   - read_report(): 读取报告内容

【文件命名规范】
研究报告文件名格式: {timestamp}_{id}_{topic}.{ext}
- timestamp: Unix 时间戳
- id: 短ID（用于标识）
- topic: 课题名称（URL编码）
- ext: .md 或 .pdf

【存储位置】
reports/ 目录（项目根目录下）

================================================================================
"""

import os
from collections.abc import Iterator
from datetime import datetime

from src.backend.http.core.errors import BadRequestError, NotFoundError
from src.backend.services.ai import AIService
from src.backend.services.bilibili import BilibiliService


class ResearchService:
    def __init__(self, ai_service: AIService, bilibili_service: BilibiliService):
        self._ai = ai_service
        self._bilibili = bilibili_service

    def stream(self, topic: str) -> Iterator[dict]:
        if not topic:
            raise BadRequestError("请输入研究课题")
        return self._ai.deep_research_stream(topic, self._bilibili)

    def list_history(self) -> dict:
        report_dir = "research_reports"
        if not os.path.exists(report_dir):
            return {"success": True, "data": []}

        reports_dict: dict[str, dict] = {}
        for filename in os.listdir(report_dir):
            if not (filename.endswith(".md") or filename.endswith(".pdf")):
                continue

            base, ext = filename.rsplit(".", 1)
            if base not in reports_dict:
                path = os.path.join(report_dir, filename)
                stats = os.stat(path)
                parts = base.split("_", 2)
                topic = parts[2] if len(parts) > 2 else base
                reports_dict[base] = {
                    "id": base,
                    "topic": topic,
                    "created_at": datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "has_md": False,
                    "has_pdf": False,
                }

            if ext == "md":
                reports_dict[base]["has_md"] = True
            if ext == "pdf":
                reports_dict[base]["has_pdf"] = True

        reports = list(reports_dict.values())
        reports.sort(key=lambda x: x["id"], reverse=True)
        return {"success": True, "data": reports}

    def resolve_download_path(self, file_id: str, format: str) -> tuple[str, str]:
        if format not in {"md", "pdf"}:
            raise BadRequestError("无效的格式")
        if ".." in file_id or "/" in file_id or "\\" in file_id:
            raise BadRequestError("无效的文件ID")

        filename = f"{file_id}.{format}"
        filepath = os.path.join("research_reports", filename)
        if not os.path.exists(filepath):
            raise NotFoundError("报告不存在")
        return filepath, filename

    def read_report(self, filename: str) -> dict:
        if ".." in filename or "/" in filename or "\\" in filename:
            raise BadRequestError("无效的文件名")

        filepath = os.path.join("research_reports", filename)
        if not os.path.exists(filepath):
            raise NotFoundError("报告不存在")

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        return {"success": True, "data": {"content": content, "filename": filename}}

