## 现状调研结论（已核对前后端真实数据流）
- 前端是原生 HTML/CSS/JS（无 React/Vue 构建链），入口为 [index.html](file:///Users/xushaoyang/Desktop/Bilibili_Analysis_Helper/src/frontend/index.html) 与主逻辑 [script.js](file:///Users/xushaoyang/Desktop/Bilibili_Analysis_Helper/src/frontend/script.js)。
- 全局主题基于 CSS 变量 + `body.dark-theme` 覆写，且按模式（video/article/user/research）通过 `mode-*` class 做局部配色：见 [style.css](file:///Users/xushaoyang/Desktop/Bilibili_Analysis_Helper/src/frontend/style.css) 与 [modes.js](file:///Users/xushaoyang/Desktop/Bilibili_Analysis_Helper/src/frontend/js/ui/modes.js)。
- 深度研究 UI 的“过程面板”主要由 `addTimelineItem()` 动态拼 DOM/HTML，且存在大量内联 style 分支（导致视觉不统一、难维护）：[script.js:L1009-L1164](file:///Users/xushaoyang/Desktop/Bilibili_Analysis_Helper/src/frontend/script.js#L1009-L1164)。
- 后端（FastAPI）SSE 事件真实类型与字段已确认：`round_start / thinking / content / tool_start / tool_progress / tool_result / report_start / done / error`；接口为 `POST /api/research`、`GET /api/research/history`、`GET /api/research/download/{file_id}/{format}`、`GET /api/research/report/{filename}`：见 [research.py](file:///Users/xushaoyang/Desktop/Bilibili_Analysis_Helper/src/backend_fastapi/api/routes/research.py) 与 [deep_research_agent.py](file:///Users/xushaoyang/Desktop/Bilibili_Analysis_Helper/src/backend/services/ai/agents/deep_research_agent.py)。
- 仓库内存在一份更“现代化”的深度研究样式草案 [research-redesign.css](file:///Users/xushaoyang/Desktop/Bilibili_Analysis_Helper/src/frontend/research-redesign.css)，但当前未被页面引入，因此默认不生效。

## 设计方向（参考主流 Deep Research 产品的 UI 权衡）
- 深度研究 UI 的核心矛盾是“过程透明度 vs 信息密度 vs 可读性”。对比分析普遍建议：报告（Report）与过程（Steps/Timeline）做分区；Sources/引用应可快速定位；工具调用与结果以卡片分组、支持折叠与状态（start/progress/result/error）呈现。参考：Deep Research UI 对比文章（Perplexity/Manus/ChatGPT/Gemini）https://www.franciscomoretti.com/blog/comparing-deep-research-uis 。
- 卡片式信息承载适合高频状态变更与列表分组，关键在于层级（标题/元信息/正文）、统一间距与“可折叠+可操作”的组件化：卡片式设计原则综述 https://developer.jdcloud.com/article/1409 。

## 目标（你提出的“统一、流畅、清晰、以主体色融入重构”落地为可交付项）
- 全站 UI：统一设计语言（字体/间距/阴影/圆角/边框/交互动效/空态/错误态），不同功能面板保持同一组件体系。
- 模式化主题：每个功能面板根据主体色（mode accent）自动派生按钮、badge、卡片左边条、hover、focus ring 与图表点色，避免“到处写 var(--bili-pink/blue)”的硬编码。
- 深度研究：把现有“事件流”升级成“流程体验”——可理解的时间线、轮次分组、工具卡片、实时预览、可折叠细节、报告生成阶段清晰提示、历史/下载一体化。

## 实施计划（按可控范围逐步推进，且保证与现有接口兼容）

## 1) 统一设计系统（Design Tokens + 组件层）
1. 新增一层“语义化变量”（例如 `--accent/--accent-soft/--accent-contrast/--accent-border`、`--surface-1/2/3`、`--radius-sm/md/lg`、`--shadow-1/2`、`--space-1..n`），由现有 `--bili-pink/blue/yellow` 映射生成。
2. 将按钮、输入框、卡片、标签（badge/chip）、列表项、弹窗/抽屉等抽成统一 class（不引入框架，只做 CSS 组件化）。
3. 统一动效与交互：hover/active/focus、加载 skeleton、滚动条、禁用态、错误提示。

## 2) 各功能面板 UI 重构（保持结构不大改，先做到统一与顺滑）
1. 梳理现有面板结构（tab-pane + sidebar + drawer），把主要容器改为一致的 header/body/toolbar/scroll 区。
2. 把当前分散在多个选择器中的“模式配色”收敛为：只要容器挂 `data-mode="video|article|user|research"`，内部组件自动继承 accent。
3. 修正常见不一致：卡片间距、分隔线、表格/markdown 样式、meta 信息区的对齐与密度。

## 3) 深度研究全流程体验升级（重点）
1. 事件模型前端归一化：建立 `normalizeResearchEvent(raw)`，把 `tool_start/tool_progress/tool_result` 统一成 {tool, status, ts, title, subtitle, payload, metrics}，减少 `addTimelineItem()` 里对 payload 的“硬分支 + 内联 style”。
2. 时间线重构为“卡片流 + 轮次分组”
   - Round 分组：`round_start` 生成 round header card，后续事件归入该组。
   - 节点类型：Thinking、Tool（start/progress/result）、Report（report_start + content）、System（done/error）。
   - 每张卡支持：折叠/展开、复制关键信息、打开链接、查看结构化 JSON（开发/高级选项）。
3. 工具卡片（Tool Card）统一组件：
   - Header：工具名 + 状态 pill（Running/Done/Failed）+ 耗时 + token/条数等 metrics。
   - Body：参数（args chips）、结果摘要（result summary）、可展开“详情/原始结果”。
   - 对 `web_search` 提供 source list（标题/域名/时间），并统一 link 样式。
   - 对 `analyze_video`：把当前 ghost 预览（右侧）改成可开关的“侧预览/折叠面板”，移动端自动降级。
4. 报告面板增强：
   - 报告生成阶段（report_start）显示“正在组织报告”并锁定一个固定区域，避免用户在 timeline 与 report 间迷失。
   - `content` 流写入报告时做节流渲染（降低 Marked 重渲染频率，提升流畅度）。
5. 历史/下载体验：
   - `done` 后以更明确的“产出卡片”呈现：报告标题、生成时间、下载 MD/PDF 按钮、查看报告按钮。
   - 历史列表支持搜索、按时间排序、悬停显示摘要。

## 4) 后端信息交换小幅增强（可选，但强烈建议，且向后兼容）
1. SSE 每条事件补充 `ts`（ISO 时间）、`event_id`（uuid/自增）、`run_id`（一次研究固定），前端可据此做排序、去重与性能统计。
2. tool 事件补充 `tool_call_id` 与统一 status 字段（start/progress/result/error），以及可选 `ui_hints`（例如建议 icon、accent、可折叠字段）。
3. 保持旧字段不变：即便前端不升级也能继续跑；新前端优先读增强字段。

## 5) 验证与回归（确保“优化”不是只改皮肤）
1. 覆盖四种模式的主流程：输入/加载/错误/空态/成功。
2. 深度研究全流程：SSE 断线重连、长文本流、并行 analyze_video 多卡片、history/download。
3. 响应式与暗色模式：>=1400、1200、移动端三档；确保 tool preview 不遮挡内容。

## 交付物（改动范围预告）
- 前端：
  - 更新 [style.css](file:///Users/xushaoyang/Desktop/Bilibili_Analysis_Helper/src/frontend/style.css)（引入语义 tokens + 组件化样式）
  - 调整 [index.html](file:///Users/xushaoyang/Desktop/Bilibili_Analysis_Helper/src/frontend/index.html)（为 research 添加控制栏/分组容器/必要的 data-mode）
  - 重构 [script.js](file:///Users/xushaoyang/Desktop/Bilibili_Analysis_Helper/src/frontend/script.js) 中 deep research UI 渲染：拆出 `deep-research-ui.js`（或利用现成 [research-api.js](file:///Users/xushaoyang/Desktop/Bilibili_Analysis_Helper/src/frontend/js/api/research-api.js) 做数据层）
  - 评估并吸收 [research-redesign.css](file:///Users/xushaoyang/Desktop/Bilibili_Analysis_Helper/src/frontend/research-redesign.css) 中可复用的现代卡片流样式（最终以“真正生效”为准：引入或合并）
- 后端（可选增强）：
  - 更新 [deep_research_agent.py](file:///Users/xushaoyang/Desktop/Bilibili_Analysis_Helper/src/backend/services/ai/agents/deep_research_agent.py) 的事件字段（增加 run_id/event_id/ts 等）

如果你确认该计划，我会从“统一设计系统”开始落地，并优先把深度研究流程完整重构到可用、顺滑、统一的交互，再回到其他面板做整体一致性收敛。