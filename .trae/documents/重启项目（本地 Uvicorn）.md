## 现状确认
- 当前开发服务在 terminal 4 运行：`uvicorn asgi:app --reload --host 0.0.0.0 --port 5001`（command_id: 91f9f99f-5415-42ca-96a7-29d44fecb9ae）。

## 重启步骤
1. 终止现有服务进程
   - 使用现有 command_id 停止正在运行的 uvicorn 进程（避免占用 5001 端口）。
2. 重新启动服务
   - 在同一工作目录重新执行：`source .venv/bin/activate && uvicorn asgi:app --reload --host 0.0.0.0 --port 5001`。
3. 验证启动成功
   - 请求健康检查接口：`GET /api/health` 与 `GET /api/v1/health`，确认返回 success。
   - 观察启动日志是否有 import error/端口占用等报错。

## 异常处理（若出现）
- 端口占用：更换端口（如 5002）或确认旧进程已结束。
- 依赖/导入异常：回溯报错文件并修复后再次重启。

确认后我将按上述步骤执行重启。