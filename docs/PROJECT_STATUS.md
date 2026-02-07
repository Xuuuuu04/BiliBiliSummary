# BiliInsight（AI 视频深度分析助手）- 项目体检（develop）

最后复核：2026-02-05

## 状态
- 状态标签：active（以 `develop` 分支为主线）
- 定位：一键提取 B 站视频字幕/弹幕/评论/关键帧，并用多模态模型生成总结、舆情分析与深度研究报告；前端提供沉浸式分析与对话体验。

## 架构速览
- 启动入口：`asgi.py`
  - 日志：`src/backend/utils/logger.py` 的 `setup_logging()`
  - 应用工厂：`src/backend/http/app.py` 的 `create_app()`
- HTTP 层：`src/backend/http/`
  - API 聚合：`src/backend/http/api/router.py`
  - 路由：
    - `POST /api/analyze`、`POST /api/analyze/stream`、`POST /api/chat/stream`（`routes/analyze.py`）
    - `POST /api/research` + 研究历史/下载/阅读（`routes/research.py`）
    - 以及 `routes/bilibili.py`、`routes/qa.py`、`routes/settings.py`、`routes/user.py` 等
  - 用例编排：`src/backend/http/usecases/`（`AnalyzeService`、`ResearchService` 等）
- 领域服务：`src/backend/services/`
  - B 站数据：`services/bilibili/`（login/credential/video/content/search/user/rank/hot）
  - AI：`services/ai/`（含 `agents/deep_research_agent.py`、toolkit registry）
  - 数据源抽象：`services/data_sources/`（含 bilibili/youtube adapter）
- 前端：`src/frontend/`（原生 HTML/JS；后端在 `create_app()` 中挂载 `/`）
- 资源：`assets/`（截图、logo 等）

## 运行方式
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn asgi:app --reload --host 0.0.0.0 --port 5001
```

## 工程化现状
- 工具链：`pyproject.toml` 配置了 black/ruff/pytest/mypy（Python 3.12 目标）。
- 测试：存在 `tests/` 目录（可继续补关键链路的用例回归）。
- 分层清晰：HTTP（routes/usecases）→ services（bilibili/ai/data_sources）→ utils。

## 主要风险与建议（优先级）
- `.env` 需严格本地化：保持只提交 `.env.example`，避免误入库。
- 深度研究与多模态链路建议补“回归样例”：
  - 固定 1-3 个公开视频 URL，跑 `analyze/stream` 与 `research` 输出，保存为基准（golden）以便迭代不回退。
- API 文档建议补齐：把关键请求/响应 schema（尤其是 SSE 事件类型）写到 `docs/`，便于面试/交接。
