# HTML 报告版本计划 / HTML Report Plan

> 为 Academic Report 的 **HTML 报告**制定的设计与实现计划。当前 HTML 由 Markdown 自动转换 + 通用样式表生成，缺乏针对「热点 / 四要素摘录 / 速览」的视觉结构。本计划提出**结构化 HTML 渲染**方案，使 HTML 报告专业、可速读、可导航、可打印。
>
> Design & implementation plan for the HTML report. The current HTML is auto-converted from Markdown with a generic stylesheet, lacking visual structure for hotspots / four-element excerpts / overview. This plan proposes a **structured HTML rendering** approach.

---

## 1. 现状 / Current State

- **转换路径**：`report_generator._convert_to_html` 用 `markdown` 库（`extra/tables/toc/sane_lists` 扩展）把 MD → HTML 片段，再套 `templates/report_html_template.html`（Jinja2），注入 `{{content}} / {{title}} / {{generation_time}}`。
- **模板**：通用 MD 样式（h1–h4、blockquote、table、code、hr），仅 `.summary` / `.footer` 两个专用 class。
- **四要素摘录**（2026-07-13 新增）在 HTML 里渲染成普通 `<p><strong>解决的问题 / Problem</strong></p><p>…</p>`，**无任何视觉区分**。
- **邮件**：`email_sender` 的 HTML 正文是固定模板（不随报告内容变化），报告作为 `.md` 附件发送。

### 1.1 主要不足 / Gaps

| # | 不足 | 影响 |
|---|------|------|
| 1 | 四要素摘录无视觉层级 | 「解决的问题/现有方案/新方案/效果及局限」混同为正文，不突出 |
| 2 | 热点之间无分隔 | 多热点报告难横向区分（无卡片/折叠/色条） |
| 3 | 速览逐篇列表与正文混同 | 顶部速览不够「可扫读」 |
| 4 | 无目录/锚点 | 长报告（10+ 篇）无法快速跳转 |
| 5 | 无打印/PDF 优化 | 阴影/背景浪费墨，分页不受控 |
| 6 | 双语标签平铺 | 「中文 / English」并排占空间，无切换 |
| 7 | 邮件正文与报告脱节 | 正文固定，不能预览报告要点 |

---

## 2. 目标 / Goals

- **专业学术外观**：卡片化热点、四要素徽章、清晰层级。
- **可速读**：顶部速览一眼覆盖所有论文；四要素图标+配色快速定位。
- **可导航**：热点/论文锚点 + 顶部目录跳转。
- **可打印**：`@media print` 优化，可直接「打印为 PDF」。
- **双语友好**：默认双语并排，可选语言切换。
- **邮件联动**：正文摘要 + HTML 附件（完整样式）。

---

## 3. 设计方案 / Design

### 3.0 设计原则：严谨简约 / Minimalist & Academic

> 用户要求风格**严谨简约、便于阅读**。据此确立的设计基调：
>
> - **克制用色**：黑白灰为主 + **单一中性强调色**（深蓝/墨绿其一，如 `#1f3a5f`）。**不用**红/橙/绿/紫的语义色板，**不用 emoji 图标**——靠排版层级而非颜色堆叠。
> - **排版优先**：衬线正文（如 Georgia/Source Serif）提升学术感，无衬线标签；充足行距(1.7)与留白；左对齐为主。
> - **细线分隔**：用 1px 浅灰线、缩进、字重区分层级，**不**用阴影卡片/大色块（仅热点用极淡底色或左侧 2px 色条）。
> - **四要素用「标签 + 缩进」**：每要素一行小号大写标签（PROBLEM / PRIOR WORK / METHOD / RESULTS，或中文），下接正文段落，统一灰阶；要素间用细线或留白分隔，**不**用彩色徽章。
> - **信息密度**：去掉一切装饰性元素；每屏承载更多内容，便于快速扫读与打印。

### 3.1 渲染策略：改用结构化 HTML（推荐方案 B）

| 方案 | 做法 | 优点 | 缺点 |
|------|------|------|------|
| **A. 增强 CSS** | 继续命令式 MD→HTML，用 `strong:contains(...)` 等 CSS/JS 针对标签文本加样式 | 改动小 | 脆弱（依赖文本匹配），样式难精确 |
| **B. 结构化渲染（推荐）** | `report_generator` 新增 `_render_html(ctx)`，直接生成带语义 class 的 HTML（`<article class="hotspot">`、`<section class="paper">`、`<div class="excerpt problem">`），套新模板 | 样式精确、可维护、可测试 | 改动中等（与 `_render_markdown` 并行） |

> **推荐 B**：MD 与 HTML 各走一条渲染路径，共享同一 `ctx`（_prepare 产出的 classified/summary/四要素/趋势）。HTML 不再依赖 markdown 库的转换，避免「四要素变成无语义 `<p>`」。

### 3.2 视觉结构（简约版）/ Visual Structure (Minimalist)

```
─────────────────────────────────────────────
 2023–2025  机器学习  研究报告
 报告生成时间 2026-07-13 · 涵盖时间 2023-01 至 2025-12 · arXiv/S2/OpenAlex
─────────────────────────────────────────────
 I. 报告速览
   收录 10 篇，3 个热点，高被引 2 篇。

   深度学习 (3)                          ← 小号大写热点名 + 篇数
     · 论文 A：核心内容一句话
     · 论文 B：核心内容一句话
   生成模型 (2) …
─────────────────────────────────────────────
 II. 分类论文展示

   热点一  深度学习                       ← 左 2px 色条 + 大写字重
   本热点聚焦……（介绍）

   1. 论文 A 标题
     作者 · 2024 · NeurIPS · 引用 187 · DOI 10.…
       PROBLEM                           ← 小号灰、字间距大、大写标签
       摘录语段……
       PRIOR WORK
       摘录语段……
       METHOD
       摘录语段……
       RESULTS & LIMITATIONS
       摘录语段……
       APA  Zhang L, … (2024). Title. *NeurIPS*.   ← 等宽小号

   整体分析 ……  · 奠基性参考 ……
─────────────────────────────────────────────
 III. 研究趋势
   趋势 ……   |   缺口 ……
─────────────────────────────────────────────
```

**四要素呈现（简约，无图标无彩色徽章）**：

| 要素 | 标签（小号大写灰） | 区分方式 |
|------|-------------------|----------|
| 解决的问题 | `PROBLEM / 解决的问题` | 标签 + 正文，细线分隔 |
| 已有方案 | `PRIOR WORK / 已有方案` | 同上 |
| 新方案 | `METHOD / 新方案` | 同上（仅此栏标签可用强调色字重） |
| 效果及局限性 | `RESULTS / 效果及局限` | 同上 |

- 缺失要素：标签后接淡灰「未明确提及」。
- 论文块之间用 1px 浅灰线分隔；热点用左侧 2px 深蓝色条（唯一强调色）。
- 字体：正文衬线（Source Serif/Georgia），标签无衬线大写小号；行距 1.7；最大宽 760–820px（阅读舒适区）。

### 3.3 目录与导航 / TOC

- 顶部 sticky 目录条：`速览 | 热点一 | 热点二 | … | 趋势`，点击锚点跳转。
- 每个论文标题带 `id`，速览卡片里的论文行可点击跳到该论文卡（论文多时尤其有用）。

### 3.4 双语 / Bilingual

- **默认**：双语并排（与现 MD 一致，标签「中文 / English」）。
- **增强（可选）**：顶部 `[中 / en / 双]` 切换按钮，用 `data-lang` + 一段 ~15 行 JS 切换显隐；HTML 文件内嵌，无需外部依赖。

### 3.5 打印 / PDF / Print

```css
@media print {
  .container { box-shadow: none; max-width: 100%; }
  .hotspot, .paper { break-inside: avoid; page-break-inside: avoid; }
  .toc { display: none; }            /* 打印时隐藏目录条 */
  body { background: white; }
}
```

### 3.6 邮件联动 / Email

- **正文**：改为「报告速览预览（前 1-2 个热点）+ 数据源/时间 + 『完整报告见附件』」。
- **附件**：同时附 `.html`（完整样式，浏览器打开即专业排版）和 `.md`（便于编辑/版本控制）。

---

## 4. 实现阶段 / Phased Implementation

| 阶段 | 内容 | 产出 |
|------|------|------|
| **Phase 1：结构化渲染骨架** | 新增 `_render_html(ctx)`，语义 class（hotspot/paper/excerpt），四要素徽章卡片样式；与 `_render_markdown` 并行，共享 ctx | HTML 四要素有视觉层级 ✅ |
| **Phase 2：速览/热点/趋势样式 + TOC** | 速览热点卡片网格、热点卡片色条、趋势两栏、顶部 sticky 目录锚点 | 可速读、可导航 ✅ |
| **Phase 3：双语切换 + 响应式 + 打印** | 语言切换按钮、移动端响应式、`@media print` 优化 | 多端可用 ✅ |
| **Phase 4：邮件联动 + 测试** | 邮件正文摘要预览 + 双附件；HTML 结构断言（四要素 class、占位、热点卡）；烟雾截图回归 | 闭环 ✅ |

> 每阶段独立可交付；Phase 1 即有肉眼可见的「专业度」提升。

---

## 5. 涉及文件 / Files

| 文件 | 改动 |
|------|------|
| `scripts/report_generator.py` | 新增 `_render_html`；`_convert_to_html` 改为调用它（或保留 MD 路径作 fallback） |
| `templates/report_html_template.html` | 重构为结构化模板（含徽章/卡片/TOC/print CSS），或拆为 `_render_html` 内联生成 |
| `scripts/email_sender.py` | 正文模板改为速览预览 + 双附件（.html + .md） |
| `test/test_report_generator.py` | HTML 结构断言：四要素 class、`未明确提及` 占位、热点卡、APA 块 |
| `报告格式设计.md` / `README.md` / `实施计划.md` | 同步 HTML 报告说明 |

---

## 6. 测试与验收 / Testing & Acceptance

1. **结构断言**：HTML 含 `<div class="excerpt problem">`、`<div class="hotspot">`、`未明确提及` 占位、`<code>` APA 块。
2. **多语言**：zh/en/bilingual 三模式均正确渲染四要素标签。
3. **降级**：四要素全空 → 回退完整 Abstract 段；无摘要 → 占位。
4. **打印**：浏览器「打印为 PDF」无阴影浪费、热点卡不被切断。
5. **邮件**：正文含速览预览；附件 .html 浏览器打开样式完整。
6. **回归**：现有 23 项 report_generator 测试不破；新增 ~6 项 HTML 结构测试。

---

## 7. 风险 / Risks

| 风险 | 处理 |
|------|------|
| 邮件客户端 CSS 兼容性 | **附件 HTML** 用完整 CSS（现代浏览器）；**邮件正文**只用内联样式 + 表格布局（兼容 Outlook/QQ/Gmail） |
| 图标/装饰 | 严谨简约风格**不使用 emoji 图标**，仅用大写文字标签 + 排版层级，零字体依赖 |
| markdown 库 vs 结构化渲染迁移 | 保留 `_render_markdown` 不变；`_render_html` 独立新增，互不影响 |
| 双语切换 JS 被邮件过滤 | 切换只用于附件 HTML（浏览器），邮件正文始终双语并排 |

---

## 8. 工作量估计 / Effort

| 阶段 | 估时 |
|------|------|
| Phase 1（骨架 + 四要素样式） | 2-3h |
| Phase 2（速览/热点/TOC） | 2-3h |
| Phase 3（双语/响应式/打印） | 1-2h |
| Phase 4（邮件联动/测试） | 2-3h |
| **合计** | **7-11h**，可按阶段交付 |
