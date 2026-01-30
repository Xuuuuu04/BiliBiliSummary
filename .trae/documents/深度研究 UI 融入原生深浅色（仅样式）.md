## 问题复盘（结合你给的截图）
- 深色模式下“研究过程”控制栏/按钮组偏亮、偏“白底胶囊”，和原生 `.toolbar` / `.analysis-meta span` 的深浅层级不一致。
- 深度研究卡片内部的预览/原始数据区域使用了强调色虚线框与浅色底，导致整体更像“新系统”，而不是原生的 `card-bg → nav-hover-bg → input-bg` 三级层次。
- 你要求“功能不调整”，因此只做 CSS 融合，不动 JS 交互与数据流。

## 改造目标
- 深浅色下统一回到原生主题层次：
  - 外层：`--card-bg`
  - 二级容器：`--nav-hover-bg`
  - 输入/代码块：`--input-bg`
- 强调色只用于“边条/文本/边框高亮”，不再大面积铺底或强阴影。

## 实施步骤（只改样式）

## 1) 控制栏完全对齐原生 Toolbar 语言
- `.timeline-controls`：对齐 `.toolbar` 的背景（`--toolbar-bg` + blur）、边框、圆角与阴影强度。
- `.timeline-controls-buttons`：不再使用明显的“白底胶囊”，改为原生的轻量分组（`--nav-hover-bg`/透明 + 边框）。
- `.timeline-control-btn`：显式 `appearance: none; -webkit-appearance: none;`，并采用类似 `.analysis-meta span` 的标签风格（`--input-bg` + 细边框）。
- “开/关”状态：仅改边框/文字色（accent），背景仍保持 `--input-bg`，避免强对比。

## 2) 深度研究卡片回归原生“二级面板”外观
- `.dr-card`：背景固定用 `--nav-hover-bg`，默认弱阴影或无阴影（遵循原生卡片体系）。
- active 状态：用左边条 + 轻描边（`rgba(var(--accent-rgb),...)`）表达；去掉强调色大阴影。
- thinking/tool/report/system/completed/failed：仅通过左边条颜色区分（蓝/主体色/绿/红），保持原生克制。

## 3) 预览/原始数据/来源列表的底色与边框统一
- `.dr-preview/.dr-pre/.dr-source-row`：背景切到 `--input-bg`，边框用 `--border-color` 的 alpha 版本。
- 去掉强调色虚线框的“强存在感”，只保留轻微区分（必要时虚线仍可保留，但颜色跟随 `--border-color`）。

## 4) 回归验证（不改功能）
- 深色/浅色各验证一次：research 面板的控制栏、卡片层级、预览区、来源列表可读性。
- 切换 video/article/user/research 确认不会把原生主题带偏（只影响深度研究局部样式）。

## 预计修改文件
- 仅修改 [style.css](file:///Users/xushaoyang/Desktop/Bilibili_Analysis_Helper/src/frontend/style.css)（深度研究相关选择器与按钮外观），不动任何 JS。