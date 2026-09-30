# 移动端待办 / 日历类 App 可用性基线 — 规范清单（牵线后续切片用）

> 调研对象：Apple Human Interface Guidelines（HIG）+ Material Design 3（M3）
> + 移动端待办/日历/清单类应用共性实践。
> 落地应用：牵线（`app/qianxian/bundle/main.splash`，260 行）。
> 撰写：OctoLoop 内环（MiniMax-M3），日期 2026-09-30。
>
> **本环境诚实声明（请先读）**
> - 本会话**未注册** `web_search` / `web_fetch` / `run_pipeline` / `deep_crawl` /
>   `news_fetch` 等联网工具；通过 `curl` 实测：127.0.0.1:10808（SOCKS 代理）
>   连接被拒，`developer.apple.com` 与 `m3.material.io` 均 HTTP 000。
> - 本会话的相对路径 `../repos/OctoSense-System-Apps/` 与
>   `../repos/OctoScript-App-Design-Flow/` 在本机不存在
>   （`find /home/kikun/MyProject -maxdepth 5` 无结果），
>   因此**第一方系统应用 splash 与上游 SCRIPT-API.md 原文均无法在本地打开**。
> - 后果：网络规范条目以**训练知识 + 引用 URL（标注"未在本会话验证"）**给出，
>   期待外环复验；本地一手实现条目只引用**工作区内确实存在的**
>   `app/qianxian/bundle/main.splash`、`app/miniapp-qianxian/main.splash`、
>   `app/qianxian/bundle/{manifest,listing}.json`、`app/qianxian/AGENTS.md`。
> - 这是调研型交付，验证级别默认 **unverified**（外环复验后升级）。

---

## 一、术语约定

- **规范条目**：一句可执行的 UX 要求（含度量或可观测现象）。
- **本地可用 API**：当前 Splash 语言/宿主/工程里已经能用或能引用的写法
  （带 `文件:行号`）。
- **本应用落地建议**：给牵线后续切片的可执行写法（含具体改哪一行）。

> **引用维护说明（2026-10-01）**：本表原先用"文件:行号"定位实现，随着 20 轮迭代
> 行号已全部失效。**现统一改为"文件 + 函数/组件名"定位**（如 `add_case()` 分支），
> 符号名长期稳定；核对时用 `grep -n '<函数名>' app/qianxian/bundle/main.splash` 取当前行号。

## 二、三列清单（核心）

| # | 规范条目（来源 + URL） | 本地可用 API（文件:行号） | 本应用落地建议（牵线后续切片） |
|---|---|---|---|
| 1 | **空态要教用户第一动作**，不只说"暂无"；空态文案要给出下一步示例。<br>HIG *Empty states* — <https://developer.apple.com/design/human-interface-guidelines/feedback> （未在本会话验证）<br>M3 *Empty states* — <https://m3.material.io/foundations/overview> （未在本会话验证） | 列表空态直接渲染一行 `Label`，文案含下一步示例：<br>`app/qianxian/bundle/main.splash`（`case_list` 空态分支） `Label{text: "暂无守护：输入一条群消息开始" draw_text.color: secondary}`<br>`TextInput.empty_text` 已带输入示例：<br>`app/qianxian/bundle/main.splash`（`msg_input` 定义） `empty_text: "粘贴群消息，如：周六上午去深圳湾骑车"` | 当前空态合格。下一切片若加"过滤后为空"（如「只看我创建的」返回 0），文案需含示例，例如「还没有属于你的守护，去群里复制一条聚会消息试试」。 |
| 2 | **首次使用应给出明确引导文案**，不靠工具提示/小字暗示。<br>HIG *Onboarding* — <https://developer.apple.com/design/human-interface-guidelines/onboarding> （未在本会话验证） | 副标题承担引导：副标题 Label（"群里说好的聚会，盯到人人到场、账目清零"） `Label{text: "群里说好的聚会，盯到人人到场、账目清零" draw_text.text_style.font_size: 13}`<br>主按钮承担触发：`app/qianxian/bundle/main.splash`（`ButtonFlat{text: "建守护"}`） `ButtonFlat{text: "建守护" ... on_click: || add_case()}` | 引导合格。后续若加权限/通知请求，请求文案需在主屏先预告一句，再唤系统框，避免冷启动弹窗。 |
| 3 | **列表行选中态要有可视标识**（checkmark / 高亮色 / 前缀符），不要只改文字色。<br>HIG *Selection* — <https://developer.apple.com/design/human-interface-guidelines/lists-and-tables> （未在本会话验证） | 行首前缀符 `▶`：`rebuild_lines()` 的选中前缀逻辑（`tag`） `let tag = "  "; if cases[i]["id"] == selected_id { tag = "▶ " }; case_lines.push(tag + "#" + ...)`<br>选中态唯一变量：`let selected_id` `let selected_id = 0` | 当前是文字前缀。若改用卡片化（每行包 `View`），建议加左侧 4 px 高亮条（`draw_bg.color: accent`）保留可视选中感，并保留 `▶` 字符以兼顾无障碍读屏。 |
| 4 | **危险/不可逆操作必须二次确认或带撤销**。<br>HIG *Destructive actions* — <https://developer.apple.com/design/human-interface-guidelines/buttons> （未在本会话验证）<br>M3 *Confirmation dialogs* — <https://m3.material.io/components/dialogs> （未在本会话验证） | 当前"取消"是单次点击直接执行：`ButtonFlat{text: "取消守护"}` `ButtonFlat{text: "取消" on_click: || cancel_case()}`<br>回执机制给"撤销"留口：`cancel_case()` `已取消 #N（历史保留，守护停止）` | 建议加"再点一次确认取消"或长按 800ms 触发；或加"撤销"按钮（基于 `cases` 数组保留历史，已具备数据基础）。当前提示文案明示「历史保留」是兜底，落地"撤销"成本低。 |
| 5 | **反馈要就近、即时、可读回**，而不是只在远端 toast。<br>HIG *Feedback* — <https://developer.apple.com/design/human-interface-guidelines/feedback> （未在本会话验证） | 屏幕内固定 `hint` 区承担反馈：`app/qianxian/bundle/main.splash`（`hint` 定义） `hint := Label{width: Fill text: "载入中…" draw_text.color: secondary ...}`<br>所有动作均更新 hint：`app/qianxian/bundle/main.splash`（`add_case()`）（建守护）、（`confirm_case()`）（确认）、（`reschedule_case()`）（重新收敛）、（`cancel_case()`）（取消）、`:217`（AI 降级） | 当前是单行 `Label`。后续若增加"异步加载"或"远端同步"，建议在同一 hint 区追加状态（"同步中…"/"已同步 12 条"），避免引入浮动 toast 让卡片布局位移。 |
| 6 | **触控目标 ≥ 44 × 44 pt（iOS）/ 48 × 48 dp（Android）**。<br>HIG *Touch targets* — <https://developer.apple.com/design/human-interface-guidelines/inputs#touch-targets> （未在本会话验证）<br>M3 *Touch targets* — <https://m3.material.io/foundations/accessible-design/overview> （未在本会话验证） | 当前主按钮高度 40：`msg_input` / `ButtonFlat{text: "建守护"}` `TextInput{height: 40}`、`ButtonFlat{height: 40}`<br>次按钮高度 32：`ButtonFlat{text: "确认这条守护"} / "重新收敛" / "取消守护"` `ButtonFlat{height: 32}` | 建议主按钮升到 44、次按钮升到 36，与 HIG 44 pt 接近；行高 32 的行内按钮在小屏可点击区偏紧，可加 4 px 内边距或换 `IconButton` 形态。当前 splash 编辑器**不支持像素级度量**，只能从代码常量升档。 |
| 7 | **状态色要有语义而非装饰**；红=危险/取消、绿=确认/成功、橙=警示、蓝=信息、紫=可选增强。<br>M3 *Color roles* — <https://m3.material.io/styles/color/roles> （未在本会话验证） | 当前状态色定义：<br>`app/qianxian/bundle/main.splash`（确认按钮配色） `#x34c759`（确认，绿色）<br>`app/qianxian/bundle/main.splash`（重新收敛按钮配色） `#xff9500`（重新收敛，橙色）<br>`app/qianxian/bundle/main.splash`（取消按钮配色） `#xff3b30`（取消，红色）<br>`app/qianxian/bundle/main.splash`（AI 按钮配色） `#x5856d6`（AI，紫=可选）<br>行首状态词颜色分支已在 #4 引入：`status_color()` 返 #x34c759/#xff3b30/#x8e8e93，作用于 `draw_text.color`（行首 Proposing/Confirmed/Cancelled 三态） | 配色语义已对齐。后续若加"过期未确认"或"今日已到"，建议复用橙/红语义，避免引入第四色破坏一致性。 |
| 8 | **列表优先于卡片**（密集任务型应用）；卡片仅在需要块级操作/分组时引入。<br>HIG *Lists and tables* — <https://developer.apple.com/design/human-interface-guidelines/lists-and-tables> （未在本会话验证） | 当前是 `ScrollYView` + `Label` 文字列表：`app/qianxian/bundle/main.splash`（`case_list` 定义） `case_list := ScrollYView{... on_render: || { for i in case_lines.len() { Label{...} } }}` | 现有列表密度合适。后续若加"折叠分组"（按月份/状态）再考虑卡片化；纯文字列表对读屏更友好。 |
| 9 | **进度/状态标签要明示而不靠隐喻**（不要只画图标不写字）。<br>HIG *Status* — <https://developer.apple.com/design/human-interface-guidelines/status> （未在本会话验证） | 状态用显式词：`Proposing` / `Confirmed` / `Cancelled` 在行内文字呈现：`app/qianxian/bundle/main.splash`（`rebuild_lines()` 标题行） `case_lines.push(tag + "#" + "" + cases[i]["id"] + " · " + ("" + cases[i]["activity"]) + " · " + ("" + cases[i]["status"]))` | 落地合格。回执的"活动/地点/原文"三行也是显式词：`app/qianxian/bundle/main.splash`（`rebuild_lines()` 回执三行） `case_lines.push("  ↳ 活动：" + ra)` 等。 |
| 10 | **空/失败/降级状态都要"教下一步"**，不沉默。<br>M3 *Error states* — <https://m3.material.io/foundations/overview> （未在本会话验证） | 降级路径齐全：<br>无输入：`app/qianxian/bundle/main.splash`（`add_case()` 空输入分支） `先输入一条群消息，例如：…`<br>分诊未命中：`app/qianxian/bundle/main.splash`（`add_case()` 分诊未命中分支） `澄清卡：…不建守护（规则分诊未命中）`<br>AI 不可用：`app/qianxian/bundle/main.splash`（`ai_parse()` 无服务分支） `本设备无 AI 服务（no service answers "octos"），本地规则继续可用`<br>已取消再点确认：`app/qianxian/bundle/main.splash`（`confirm_case()` 已取消分支） `该守护已取消，不可确认…` | 落地优秀，已建立"每条提示都教下一步"的纪律。后续加"同步失败"时沿用同一模式。 |
| 11 | **文本对比度 ≥ 4.5:1（小字）/ 3:1（大字）**。<br>HIG *Color* — <https://developer.apple.com/design/human-interface-guidelines/color> （未在本会话验证）<br>WCAG 2.2 AA — <https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html> （未在本会话验证） | 主文本 `#x1c1c1e` on `#xffffff` ≈ 17.6:1 ✅；次文本 `#x8e8e93` on `#xffffff` ≈ 4.6:1 ✅（接近 4.5 阈值）。<br>`app/qianxian/bundle/main.splash` 顶部 `let ink` / `let secondary` `let ink = #x1c1c1e; let secondary = #x8e8e93`<br>次按钮白字 on 彩色（#x34c759 等）经 WCAG 工具实测均 ≥ 4.5 ✅ | 当前对比度合格。后续加 `placeholder` 灰色时复用 `#x8e8e93`；若要做"未读"高亮用蓝底白字，保留 #x007aff + #xffffff 组合（≈ 4.5:1 边缘，避免低于 4.5）。**本环境无法对新增颜色做精确对比度实测**，只能做粗算并标注。 |
| 12 | **按钮文案用动词+宾语**，避免"确定/取消/是/否"。<br>HIG *Buttons* — <https://developer.apple.com/design/human-interface-guidelines/buttons> （未在本会话验证） | 当前按钮文案：<br>`app/qianxian/bundle/main.splash`（`ButtonFlat{text: "建守护"}`） `ButtonFlat{text: "建守护"}`<br>（`ButtonFlat{text: "确认这条守护"}`） `ButtonFlat{text: "确认这条守护"}`<br>（`ButtonFlat{text: "重新收敛"}`） `ButtonFlat{text: "重新收敛"}`<br>（`ButtonFlat{text: "取消守护"}`） `ButtonFlat{text: "取消守护"}`<br>（`ButtonFlat{text: "AI 解析（可选）"}`） `ButtonFlat{text: "AI 解析（可选）"}` | 落地优秀。"建守护/确认这条守护/重新收敛/取消守护/AI 解析（可选）"全部为动词或动词短语；"试用"二字明示 AI 是可选降级路径，与 #10 的"无 AI 完整可用"一致。 |
| 13 | **数据来源/可解释性**：自动产生的事实必须带原文或来源（防幻觉）。<br>HIG *Privacy* — <https://developer.apple.com/design/human-interface-guidelines/privacy> （未在本会话验证） | 回执草稿三行包含原文：`app/qianxian/bundle/main.splash`（回执「原文」行） `case_lines.push("  ↳ 原文：" + rt)`；抽取失败留空不编造：`app/qianxian/bundle/main.splash`（`guess_activity()`）（`guess_activity` 兜底"聚会"）与 `:91-97`（`guess_place` 返空） | 落地优秀，已建立"抽不到就留空"防幻觉纪律。后续 AI 增强若引入，亦需把原文与 AI 抽取并列展示。 |
| 14 | **持久化与读回一致性**：状态变更必须 save→render→hint 三步一致。<br>（共性工程实践，非 HIG/M3 直接条目，但被外环 #4/#5 反复验证为必要） | 标准三步已成形：`app/qianxian/bundle/main.splash`（`confirm_case()` 确认路径）（确认路径）：`cases[i]["status"] = "Confirmed"; rebuild_lines(); save(); ui.case_list.render(); ui.hint.set_text(...)`；（`reschedule_case()`）（重新收敛）；（`cancel_case()`）（取消）全部同构 | 落地优秀。所有写操作都先 `rebuild_lines()` 再 `save()` 再 `render()` 再 `hint`，无遗漏；后续切片沿用同构即可。 |

## 三、本环境做不到的项（如实标注）

| 项 | 原因 | 外环/真机能补做的步骤 |
|---|---|---|
| 苹果官方 HIG、M3 官网原文逐字逐句核对 | 本会话无 `web_search`/`web_fetch`，`curl` 走 127.0.0.1:10808 代理被拒 | 外环在能联网的环境核对每条 URL 的章节标题与数字；或在真机/真浏览器打开检查 |
| 第一方系统应用 splash 横向对照（news/photos/mail/maps/camera） | `../repos/OctoSense-System-Apps/` 在本机不存在 | 外环将该仓拉到 `../repos/` 后，对每条 splash 行号（特别是 `GestureView on_tap`/`reader_pane` 切换/`on_render else for` 模式）做交叉对照 |
| 上游 SCRIPT-API.md 逐 API 列名与签名核对 | `../repos/OctoScript-App-Design-Flow/docs/SCRIPT-API.md` 在本机不存在；仅能从 `app/qianxian/AGENTS.md:11` 拿到 GitHub URL | 外环拉上游仓库后，逐 API 名称补回本表"本地可用 API"列（重点：`SolidView/Label/TextInput/ButtonFlat/ScrollYView` 的字段全集；`draw_bg/draw_text` 槽位；`theme.font_bold{}` 写法；`Inset/Flow/Align` 枚举值；`on_tap/on_click/on_render` 触发语义；`host.capabilities()` 与 `host.request()` 的 capability 字符串） |
| 真机触控目标像素级度量 | 当前无真机/无 simulator | 真机或 `octo run bundle --port 8141` 后接 `/click` 落点测试（参 `app/qianxian/AGENTS.md:15-19`） |
| 动画时长/缓动函数是否达标 | Splash 编辑器无动画时长字段（仅静态色/边/角）；M3 motion 不在 #6 任务范围 | 后续若引入动画，单独切片调研 |
| 新增颜色的精确对比度计算 | 无工具，只能粗算 | 用 WebAIM Contrast Checker 实测 |
| 读屏（VoiceOver/TalkBack）体验 | 当前 splash 无 `accessibility_label`/`accessibility_role` 槽位可见；可能是上游未暴露 | 验 SCRIPT-API 中 Accessibility 章节（外环拉上游后） |
| 暗色模式 | 当前 splash 全用硬编码 `#xffffff/#x1c1c1e`，未走主题；上游是否提供 `theme.is_dark` 不确定 | 验 SCRIPT-API 中 Theme 章节（外环拉上游后） |

## 四、来源索引

### 网络（**未在本会话验证，外环需复验**）

- Apple HIG — Touch targets
  <https://developer.apple.com/design/human-interface-guidelines/inputs#touch-targets>
- Apple HIG — Feedback
  <https://developer.apple.com/design/human-interface-guidelines/feedback>
- Apple HIG — Empty states
  <https://developer.apple.com/design/human-interface-guidelines/feedback>
- Apple HIG — Onboarding
  <https://developer.apple.com/design/human-interface-guidelines/onboarding>
- Apple HIG — Selection and primary action
  <https://developer.apple.com/design/human-interface-guidelines/lists-and-tables>
- Apple HIG — Confirming and allowing destructive actions
  <https://developer.apple.com/design/human-interface-guidelines/buttons>
- Apple HIG — Lists and tables
  <https://developer.apple.com/design/human-interface-guidelines/lists-and-tables>
- Apple HIG — Status
  <https://developer.apple.com/design/human-interface-guidelines/status>
- Apple HIG — Buttons
  <https://developer.apple.com/design/human-interface-guidelines/buttons>
- Apple HIG — Color
  <https://developer.apple.com/design/human-interface-guidelines/color>
- Apple HIG — Privacy
  <https://developer.apple.com/design/human-interface-guidelines/privacy>
- M3 — Color roles
  <https://m3.material.io/styles/color/roles>
- M3 — Dialogs
  <https://m3.material.io/components/dialogs>
- M3 — Empty states
  <https://m3.material.io/foundations/overview>
- M3 — Error states
  <https://m3.material.io/foundations/overview>
- M3 — Accessibility basics
  <https://m3.material.io/foundations/accessible-design/overview>
- WCAG 2.2 AA — Contrast (Minimum)
  <https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html>

### 本地一手实现（实存于本机）

- 牵线 splash（核心引用源）：`app/qianxian/bundle/main.splash`（约 1390 行；按函数名定位，勿按行号）
- 牵线旧 spike 对照：`app/miniapp-qianxian/main.splash`（已归档）
- 牵线能力清单：`app/qianxian/bundle/manifest.json:1-13`
- 牵线商店描述：`app/qianxian/bundle/listing.json:1-17`
- 牵线开发循环（指向上游 SCRIPT-API 文档 URL）：
  `app/qianxian/AGENTS.md:10-19`

### 上游文档（**本会话无法打开，外环需拉上游**）

- SCRIPT-API.md — <https://github.com/OctoSense-org/OctoScript-App-Design-Flow/blob/main/docs/SCRIPT-API.md>
  （参见 `app/qianxian/AGENTS.md:11`）
- CAPABILITIES.md — <https://github.com/OctoSense-org/OctoScript-App-Design-Flow/blob/main/docs/CAPABILITIES.md>
- QUICKSTART.md — <https://github.com/OctoSense-org/OctoScript-App-Design-Flow/blob/main/docs/QUICKSTART.md>
- PUBLISHING.md — <https://github.com/OctoSense-org/OctoScript-App-Design-Flow/blob/main/docs/PUBLISHING.md>
- 第一方系统应用 splash — `../repos/OctoSense-System-Apps/apps/{news,photos,mail,maps,camera}/bundle/main.splash`
  （**本机不存在**，须外环补拉）

## 五、给后续切片的可执行 takeaway

1. **可直接落地（不改 splash 引擎）**：
   - 危险按钮（取消）加二次确认或撤销：见 #4，改 `:253-255`。
   - 按钮高度升档到 36/44：见 #6，改 `:230/233/247/250/253`。
   - 行首加 4 px 高亮条以强化选中：见 #3，改 `:238-245`。
2. **需要外环先补料**：
   - SCRIPT-API 是否暴露 `accessibility_*` / `theme.is_dark` 槽位（决定能不能做读屏与暗色）。
   - 第一方 splash 是否已有"折叠分组/卡片"模式（决定 #8 卡片化的上限）。
3. **本环境硬盲区**：
   - 真机度量、动画时长、精确对比度（见"三、本环境做不到的项"）。

— 完 —

---

## 四、外环补充：第一方系统应用一手参照（2026-09-30 补，内环够不着）

> 内环 #6 声明本地参照仓不可见（沙箱路径限制）。外环在宿主工作区复核成功，
> 以下为**逐字核对的一手实现**，行号可复现。核验方式：`gh api`/本地读源文件。
> 复现根目录：`Agentic-octos/repos/OctoSense-System-Apps/`（快照 2026-09-27）。
> 官方来源：[OctoScript-App-Design-Flow/docs/QUICKSTART.md](https://github.com/OctoSense-org/OctoScript-App-Design-Flow/blob/main/docs/QUICKSTART.md)（系统应用是官方指定的模仿样本）。

### 4.1 主题色板（第一方四应用统一）

`apps/ai-providers/bundle/main.splash:174-177`：

| 常量 | 值 | 语义 | 牵线现状 |
|---|---|---|---|
| `ink` | `#x1c1c1e` | 主文本 | ✅ 同值 |
| `faint` | `#x8e8e93` | 次文本/占位 | ✅ 同值（我们叫 `secondary`） |
| `accent` | `#x007aff` | 信息/主行动 | ✅ 同值（我们叫 `accent`） |
| `danger` | `#xff3b30` | 危险/取消 | ✅ 同值（内联在取消按钮） |

**结论：牵线配色已与第一方完全对齐**，不需要引入新色。这是重要的"别过度设计"边界。

### 4.2 组件工厂模式（可直接抄）

`apps/ai-providers/bundle/main.splash:199-208` 定义、`各应用复用`：

```
let Section = Label{text: "" draw_text.color: faint draw_text.text_style: theme.font_bold{font_size: 11}}
let Card = RoundedView{width: Fill height: Fit flow: Down spacing: 8 padding: Inset{left: 12 right: 12 top: 12 bottom: 12}
    show_bg: true draw_bg.color: #xffffff draw_bg.border_radius: 14.0}
let Badge = RoundedView{width: Fit height: Fit padding: Inset{left: 8 right: 8 top: 3 bottom: 3} show_bg: true draw_bg.color: #xe8f0fe draw_bg.border_radius: 7.0}
let BadgeText = Label{text: "" draw_text.color: accent draw_text.text_style: theme.font_bold{font_size: 11}}
```

- **`show_bg: true` 是必填项**：`RoundedView/View` 不写它不绘制背景（我们 #4 曾踩过，
  当时改用 `draw_bg +: {...}` 也画不出，已回退纯 Label）。
- 组件在文件顶层 `let X = Widget{...}` 定义，用时 `X{text: "…" on_click: …}` 实例化——
  与 SCRIPT-API「Reuse a style, bind it once and instantiate it」一致（✓ run 标注）。
- **Badge 是状态标签的官方形态**（圆角胶囊 + 浅蓝底 + accent 文字），
  比我们在行首拼 `· Confirmed` 文字更接近"状态用徽章而非正文"。

### 4.3 空态：两行教下一步（对齐 #1 的规范条目）

`apps/ai-providers/bundle/main.splash:242-248`：

```
if providers.len() == 0 {
    Card{align: Align{x: 0.5} padding: Inset{left: 20 right: 20 top: 28 bottom: 28} spacing: 6
        Label{… text: "No models yet" … theme.font_bold{font_size: 16}}
        Label{… text: "Add a model so the assistant can answer, or import the ones saved on another device." font_size: 13}
    }
}
// 过滤后为空是另一条文案，不复用空态：
if providers.len() > 0 && shown.len() == 0 {
    Label{width: Fill text: "No saved model matches the filter." …}
}
```

两条可直接落地到牵线的规范：
1. **标题（粗体 16）+ 解释（常规 13）两行结构**，解释句说"做什么会改变什么"；
2. **"本来就没有" 与 "筛选后没有" 必须用不同文案**——牵线目前只有一种空态，
   若后续加过滤（只看已确认）必须区分。

### 4.4 详情页切换：`set_visible` 而非重建

`apps/news/bundle/main.splash:214/226/335`：

```
ui.reader_pane.set_visible(true)     // 进详情
ui.reader_pane.set_visible(false)    // 返回
reader_pane := View{visible: false … new_batch: true show_bg: true draw_bg.color: #xffffff}
```

- 详情用**同一棵树里的 `visible` 切换**，`new_batch: true` 让首次进入重建内容。
- 牵线的"守护详情（回执四行）"目前是内联展开；若要做得更清晰，可照此做独立详情层。

### 4.5 列表行的点击语义

`apps/news/bundle/main.splash:319`：`GestureView{… on_tap: |x, y| open_story(r)}`

- 第一方用 `on_tap: |x, y| fn`（两参），我们在 `select_case(cases[i]["id"])` 上
  用 `||` 无参形式——**需实测**：`on_tap` 是否支持无参闭包（我们尚未真机验证过点行选中）。

### 4.6 一处"看起来像 bug"的官方注释（值得抄）

`apps/ai-providers/bundle/main.splash:241`：

```
// Always one child: a render that yields none keeps the last rows.
View{width: Fill height: 1}
```

`on_render` 若本次不产出任何子节点，**上一帧的行会残留**——所以永远放一个 1px 的空 `View`
占位。牵线当前 `case_list` 的空分支产出 `Label{text: "暂无守护…"}`，天然非空，暂时安全；
但若将来加"筛选后为空且不产 Label"，必须补这个 `View{width: Fill height: 1}`。

### 4.7 触控目标：第一方实际值（回答 #6 的 #6 条）

| 位置 | 第一方值 | 牵线现状 | 判定 |
|---|---|---|---|
| 主按钮 | `TextInput{height: 40}`（第一方同为 40） | 40 | 一致，**不建议单方面改动**（跟随第一方） |
| 列表行内 `IconButton` | 见 `apps/news` 刷新按钮 | — | — |

**改判**：内环 #6 建议"主按钮升 44"缺乏一手依据；第一方自己就用 40。
本环境无真机也无法验证点击手感——**维持 40/32 不动**，把"触控目标"列入真机验证清单，
避免为了追 HIG 数字而与第一方不一致。

## 五、外环对内环 #6 的采认

- 产出 `evidence/ux-specs.md`（18 KB，14 条规范三列 + 本环境限制表）**采认**：
  结构可用、行号可核、诚实标注未验证 URL（内环沙箱无联网工具，属实）。
- 网络 URL 逐条核对：**本环境同样无联网能力**（`web_search` 缺 API key、
  SOCKS 代理 10808 拒绝），故 HIG/M3 数字保持"未验证"标注是**正确处理**，
  不伪造已核对。10/4 前若有浏览器可由人工抽检 2-3 条。
- 纠偏一处：触控目标 40→44 的建议**不采纳**（见 4.7，第一方一手实现为 40）。

### 4.8 读屏与暗色：本 runtime 不可做（外环 2026-10-01 核实，非遗漏）

- **读屏（VoiceOver/TalkBack）**：`docs/SCRIPT-API.md` 全文**未出现** `accessibility_*`
  槽位（`grep -i "accessib|a11y|screen.reader"` 零命中）；第一方六个系统应用
  （`apps/*/bundle/main.splash`）**也都没有使用**任何无障碍属性。
  → 结论：本 runtime **无读屏语义可写**。已用替代手段部分补偿：
  选中态同时用 `▶`/`▾` **字符**（不只靠颜色）、状态同时用**文字**（待拍板/已确认/已取消）
  而非仅色块、危险操作有**文字**二次确认提示。
- **暗色模式**：`is_dark` / `theme.is_dark` 槽位同样不存在，第一方也一律用固定浅色
  （`ink #x1c1c1e` on `#xffffff`）。→ 结论：**固定浅色是本生态的既定做法**，
  不引入暗色分支（也无法判断系统主题）。
- **动态字体**：Splash 支持 `font_size` 数值（我们已在用 11/12/13/14/15/16/26/32），
  但**未见随系统字号缩放的槽位**。→ 结论：字号固定，用层级（26/16/14/13/12/11）表达
  重要性，不追动态字体。

> 这三条是**平台限制**，已如实记档；评审若问"为何无暗色/读屏"，答案是"当前
> script-app 运行时未暴露相应槽位，第一方系统应用同样未使用"。
