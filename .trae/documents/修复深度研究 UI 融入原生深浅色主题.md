## 问题定位（为什么“不像原生深浅色主题”）
- 原生主题的层级是：外层背景（`body` 的渐变与纹理）→ 主内容卡片（`--card-bg`）→ 内部区域（`--nav-hover-bg / --input-bg`）→ 轻量强调（边条/文字/图标）。见 [style.css](file:///Users/xushaoyang/Desktop/Bilibili_Analysis_Helper/src/frontend/style.css#L136-L148) 与 `.content-display/.toolbar` 现有用法。
- 当前深度研究新卡片（`.dr-card`）使用 `--surface-1`（等同 `--card-bg`）+ 强调色阴影（`rgba(var(--accent-rgb), ...)`），再叠加 `data-mode` 对 `--nav-active-bg` 的全局覆写，导致整体“色深/层级/强调方式”与原生组件不一致。
  - 具体：`body[data-mode]{ --nav-active-bg: ... }` 覆盖了原本的 `--nav-active-bg`（浅色为 `#FFF0F5`，深色为 `#2D1E22`），会让侧边栏与多处选中态风格偏离原生。见 [style.css](file:///Users/xushaoyang/Desktop/Bilibili_Analysis_Helper/src/frontend/style.css#L18-L128)。
  - 深度研究卡片区域的背景/边框/阴影与原生时间线气泡（原本用 `--nav-hover-bg`）不一致，导致“太实/太跳”。见 [style.css](file:///Users/xushaoyang/Desktop/Bilibili_Analysis_Helper/src/frontend/style.css#L2856-L3110)。

## 修复目标（保持你要的卡片化，但融入原生深浅色）
- 保留：轮次分组、工具卡片、折叠/自动滚动/报告节流等交互（JS 不动或微调）。
- 调整：配色与层级回归原生逻辑——内层卡片采用 `--nav-hover-bg / --input-bg` 的层级色，强调只用“左边条 + 文案 + 轻量背景”，深浅色下都自然。

## 实施计划（仅改样式与少量主题变量，最大化兼容）

## 1) 恢复原生主题变量，不让 data-mode 改写系统底色
- 移除/回退 `body[data-mode]` 与 `body.dark-theme[data-mode]` 对 `--nav-active-bg` 的覆写，让导航选中背景回到原生（浅色 `#FFF0F5` / 深色 `#2D1E22`）。
- 保留 `--accent/--accent-soft/--accent-border` 用于文字/边条强调，但不再影响系统的“底色”变量。

## 2) 深度研究卡片与控制栏全面融入原生深浅色层级
- `.timeline-controls`：改为复用原生 `.toolbar` 的视觉语言（同样的 `--toolbar-bg` 玻璃态、同样的边框与阴影强度），并让按钮 hover/active 的底色来自 `--nav-hover-bg` 而非 `--surface-1`。
- `.dr-card`：
  - 背景从 `--surface-1(=card-bg)` 调整为 `--nav-hover-bg`，让卡片成为“内容卡片里的二级面板”，层级更像原生。
  - 去掉强调色大面积阴影（`rgba(var(--accent-rgb),...)`），改为：默认 `--card-shadow` 的弱阴影/hover 加深；active 状态用“左边条 + 轻描边”表达。
  - 增加 `::before` 左边条：
    - thinking：`--bili-blue`
    - tool/report/system：`--accent`（仍支持按模式主体色）
    - completed：`--success`
    - failed：`--danger`
- `.dr-preview/.dr-pre/.dr-source-row`：背景统一切到 `--input-bg` 或 `--nav-hover-bg`，深色下不再使用亮白 `rgba(255,255,255,0.03)`，保证“深色更沉、信息更清晰”。

## 3) 状态徽标颜色修复（避免全都变成 accent）
- 给 `.dr-status-success/.dr-status-danger` 添加专用颜色与边框（成功绿/错误红），并为深色主题做对应 alpha 调整，使状态一眼可辨且不破坏主题。

## 4) 验证与回归
- 浅色/深色各跑一遍：
  - research/video/article/user 四模式切换，确认背景、导航选中态、按钮、研究过程卡片层级一致。
  - 深度研究流式进行中/完成/错误三类状态卡片可读性。

## 将改动的文件
- [style.css](file:///Users/xushaoyang/Desktop/Bilibili_Analysis_Helper/src/frontend/style.css)（核心：回退 `--nav-active-bg` 覆写 + 调整 `.timeline-controls/.dr-card/.dr-preview` 等）
- 预计不改 JS；如需让卡片类型更精确匹配边条色，可能对 [deep-research-ui.js](file:///Users/xushaoyang/Desktop/Bilibili_Analysis_Helper/src/frontend/js/ui/deep-research-ui.js) 做极小的 class 标记补强（可选）。