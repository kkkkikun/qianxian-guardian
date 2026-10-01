# UX 打磨规范对照 v3（联网核验版，2026-10-01）

> 落地应用：牵线 `app/qianxian/bundle/main.splash`（1765 行，符号名定位，行号会变）。
> 方法：本会话用 `web_fetch` 逐条实测官方 URL（HTTP 状态码见 §四）；
> `web_search` 因缺 `DEEPSEEK_API_KEY` 全程不可用（见 §四末），加分项竞品（Apple 日历 / Google 日历 / TickTick / Things 3）**未验证**，不编 URL。
> 诚实分级：W3C 四页 fetch 到**全文**（verified）；Apple HIG / M3 页面 fetch 到 **HTTP 200 + 章节标题**、
> 正文为 JS 渲染未提取到段落（partially-verified：URL 与标题实测可验，原文要点转引 v2 外环 `curl` 200 记录，不凭记忆编 URL）。
> 上一版：`evidence/ux-specs-v2.md`（外环复验记录：HIG 站 2026-10 已改版，四个旧路径 404 后已纠正）。

---

## 一、三列清单（18 条）

| # | 规范条目 | 来源 URL（实测状态） | 本应用落地建议（精确到函数名/组件名） |
|---|---|---|---|
| 1 | **空态要教第一动作**：不只说"暂无"，要给出下一步示例与一键入口。 | `https://developer.apple.com/design/human-interface-guidelines/feedback` —— 章节标题「Feedback｜Apple Developer Documentation」，HTTP 200（标题可验；正文 JS 渲染未提取，原文要点沿 v2 外环 200 记录：用非阻塞反馈教下一步） | 已落地，保持：`case_list.on_render` 内 `cases.len()==0` 分支 `Card{"还没有聚会守护"}` + 副文案"粘贴一条群消息开始…"；`msg_input.empty_text:"粘贴群消息，如：周六上午去深圳湾骑车"`；`fill_example()`（输入框非空不覆盖，只填示例）+ `ButtonFlat{"用示例试试"}`。打磨建议：筛选空分支（`filtered_idxs.len()==0`）文案已区分"这个筛选下还没有守护（当前筛选：X）"，**不动逻辑**，只建议后续把"换个标签看看"做成可点文本（当前是纯 `Label`，点不了）。 |
| 2 | **首次引导三步讲清"做什么"**，冷启动不弹窗、不强制教程。 | `https://developer.apple.com/design/human-interface-guidelines/onboarding` —— 章节标题「Onboarding｜Apple Developer Documentation」，HTTP 200（标题可验；正文同上，沿 v2 外环记录） | 已落地：`seq==0` 首用引导卡（"第一次用？三步起一条守护"①②③）+ `howto_show_flag`（`seq==0→"yes"` 自动展开，`seq>0→"no"`）+ `toggle_howto()` 与底部 `ButtonFlat{"怎么用？"}`。`Card` 副标题 `"群里说好的聚会，盯到人人到场、账目清零"` 即产品目的句。建议：保持"建过一条就永不回首用卡"（`seq>0` 恒消失）语义，不改。 |
| 3 | **列表选中态双编码**：前缀符/色条/底色至少两项，不要只改文字色。 | HIG `https://developer.apple.com/design/human-interface-guidelines/lists-and-tables`（「Lists and tables」，200，标题可验）<br>M3 `https://m3.material.io/components/lists`（「Lists – Material Design 3」，200，标题可验） | 已落地：`rebuild_lines()` 写 `case_selected[j]`（`"yes"/"no"`，`selected_id` 驱动）；渲染端 `prefix="▶ "` + `hi_w/hi_color`（`View{width:hi_w height:56 draw_bg.color:hi_color}`，`status_bar_color()` 取色）+ 展开前缀 `▾`。入口 `GestureView.on_tap→on_tap_card()→toggle_case()`（选中+折叠二合一）。读屏补偿：`▶/▾` 字符可被读出（见 §三 F）。建议：保持三编码并存，不删任一。 |
| 4 | **冲突提示显眼但非阻塞**：就近标在行内，不弹模态、不阻断主操作。 | `https://developer.apple.com/design/human-interface-guidelines/alerts` —— 「Alerts」，HTTP 200（标题可验；沿 v2 外环记录） | 已落地：`build_case_from_text()` 新建互标 + `cycle_slot()` 全量重算（`slot_day+slot_part` 同且非空→双向 `"yes"`，`Cancelled` 跳过）；`rebuild_lines()` 写 `case_conflict_lines[j]`（`⚠ 时间冲突…`）+ `case_conflict_party[j]`（双方整行）；渲染：展开态顶部红底卡 `RoundedView{#xff3b30}+白字 Label`（两行拼一串，避 A2/D 坑），折叠态 `TextLine{case_conflict_lines[j]}` + 徽章追加 `"·冲突"`（#18）。`hint` 同步回执（"仍冲突/已无冲突"）。建议：不动检测逻辑；若打磨只调冲突卡字号（当前 13pt bold，白 on 红）。 |
| 5 | **危险操作二次确认**：单次点击直删即违规；确认态必须明示后果+可放弃路径。 | HIG `https://developer.apple.com/design/human-interface-guidelines/buttons`（「Buttons」，200，标题可验）<br>M3 `https://m3.material.io/components/dialogs`（「Dialogs – Material Design 3」，200，标题可验） | 已落地（两段式按钮态，不用模态，避 E1 坑）：`cancel_case()`（`cancel_pending_id/flag`，文案"再点一次「确认取消」…5秒内点别的按钮或选别的卡可放弃"，`start_timeout(5.0)` 回收）+ `clear_all_data()`（`clear_pending_flag`，文案明示"真删 N 条（不可逆）"，`clear_prev_count` 回显）+ `cycle_slot()` 无时段首次只翻 `slot_init_asked` 不写值（#27 防编造）+ `force_create_pending`（"仍然建守护"二次按压）。确认态变体放 `case_list.on_render` 闭包内（根组件 `if` 不重算，E1）。建议：保持"点别的按钮即放弃"（`clear_cancel_pending("")`）语义。 |
| 6 | **危险操作带撤销（Snackbar 范式）**：5s 内可恢复，只恢复本次目标。 | `https://m3.material.io/components/snackbar` —— 「Snackbar - Material Design 3」，HTTP 200（标题可验；要点：短时撤销条配显式动作，沿 v2 外环 `curl` 200 记录） | 已落地：`undo_cancel()` + `undo_win_open/undo_show_flag2/cancelled_last_id`（#25 只恢复刚取消那条）；撤销条 `View{#xf2efff}+Label{"撤销窗口已开…"}+ButtonFlat{"撤销取消"}` 放 `on_render` 内（E1）；`start_timeout(5.0)` 到期归零并 `hint` 明示"已生效（撤销窗口已过）"，守卫防覆盖已撤销文案（#9）。`hint` 即撤销回执（"已撤销取消 #N → 恢复到 X（仅本次…）"）。建议：保持紫 `#x5856d6` 与红取消按钮的视觉区分，不改色。 |
| 7 | **触控目标 ≥44×44pt（HIG）**；主操作优先达标，次级至少给足间距。 | `https://developer.apple.com/design/human-interface-guidelines/inputs` —— 「Inputs」，HTTP 200（标题可验；触控目标 44pt 沿 v2 外环记录；另见 v2 §九 A/B：与第一方 `ai-providers` 一致属主动取舍） | 已落地（#29）：主区三键 `确认这条守护/重新收敛/取消守护` + `怎么用？` + 搜索框 + `people_input` + `添加` + `确认取消（5s）` + `撤销取消` 全 `height:44`；筛选 `GestureView height:32`（横向 `spacing:6` + 胶囊 `padding` 拉开间距）；低频四键（改时间/AI/导出/清空）折叠进"怎么用？"卡内（根底部从 3 行收至 2 行，防挤压）。建议：筛选条保持 32（第一方同款取舍，见 v2 §九），不硬升 44 破坏第一方一致性。 |
| 8 | **WCAG 2.5.8 Target Size (Minimum)**：指针目标至少 24×24 CSS px，否则用间距/等价路径豁免。 | `https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html` —— 「Understanding SC 2.5.8 Target Size (Minimum)」，HTTP 200 **全文可验**；原文要点："The size of the target for pointer inputs is at least 24 by 24 CSS pixels, except when: Spacing / Equivalent / Inline / User Agent Control / Essential." | 落地同 #7（44pt 主键远超 24px 下限；32 高筛选条靠 `spacing:6` 间距豁免思路，紧邻上下无重叠目标）。回归基线 `regression-20261001.md` #13 已更正"64px"误记。建议：以外环真机点按复验为准，不在本 runtime 量像素（编辑器无度量工具，见 v2 #6）。 |
| 9 | **WCAG 1.4.3 对比度（最小）**：正文 ≥4.5:1，大字（18pt/14pt bold）≥3:1。 | `https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html` —— 「Understanding SC 1.4.3 Contrast (Minimum)」，HTTP 200 **全文可验**；原文要点："The visual presentation of text and images of text has a contrast ratio of at least 4.5:1… Large-scale text… at least 3:1." | 落地：色板 `ink #x1c1c1e / secondary #x8e8e93 / accent #x007aff / danger #xff3b30` on `#xffffff/#xf2f2f7`；`evidence/contrast-audit.md` 已公式实算 8 组（6 组未达 AA 但与第一方同色值同结果，主动取舍存档）。验证工具：`https://webaim.org/resources/contrastchecker/`（200 全文可验，见 #10 行与 §四）。建议：不改色值（改即与第一方分叉）；新增文案默认用 `ink` 而非 `secondary`。 |
| 10 | **WCAG 1.4.11 非文本对比度**：识别组件与状态的视觉信息 ≥3:1。 | `https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html` —— 「Understanding SC 1.4.11 Non-text Contrast」，HTTP 200 **全文可验**；原文要点："The visual presentation of the following have a contrast ratio of at least 3:1 against adjacent color(s): User Interface Components… and states… Graphical Objects…" | 落地：`status_bar_color()` 左侧 `hi_w` 色条 + 标题行 10×10 `RoundedView{border_radius:5.0}` 状态色点（双编码，色弱不只靠色相，另有 `▶/徽章文字`）；`Badge` 底/字（`status_badge_bg/fg`：Confirmed `#xe6f7ec/#x1f8a3a`、Cancelled `#xfdecea/#xff3b30`）；冲突红卡白字；筛选选中 `accent` 底白字。复验工具：WebAIM Contrast Checker（上行，AA 要求"normal text 4.5:1 / large 3:1，graphics & UI components 3:1"）。建议：保持"色点+色条+文字"三重状态表达。 |
| 11 | **WCAG 1.4.4 文本缩放**：文本可放大到 200% 不丢内容与功能。 | `https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html` —— 「Understanding SC 1.4.4 Resize Text」，HTTP 200 **全文可验**；原文要点："Except for captions and images of text, text can be resized without assistive technology up to 200 percent without loss of content or functionality." | 本 runtime **做不到**（见 §三）：无动态字体槽位，全固定字号；补偿：字号层级 26/16/14/13/12/11（`TitleLine 16 / BodyLine 14 / TextLine·MetaLine·SectionLabel 13 / ReceiptLine·计数 12 / BadgeText 11`），容器全 `height:Fit` + 外层 `ScrollYView` 纵滚，放大字号只会撑高不截断（`Label` 自然换行，`export_data()` 长文本屏显已验证此行为）。`people_input` 截断用 24 字+"…+共 N 字"且展开态保留完整原文。 |
| 12 | **字体层级表达重要性（HIG Typography）**：三档以上字号+粗细区分标题/正文/辅助。 | `https://developer.apple.com/design/human-interface-guidelines/typography` —— 「Typography｜Apple Developer Documentation」，HTTP 200（标题可验；正文沿 v2 外环记录） | 已落地：主标题 26 bold / 卡标题 16 bold（`TitleLine`）/ 活动 14（`BodyLine`）/ 副标题·说明·hint 13（`TextLine/MetaLine/SectionLabel`）/ 回执·计数 12（`ReceiptLine`）/ 徽章 11 bold（`BadgeText`）；`theme.font_bold{font_size:N}` token。建议：新增 section 标题复用 `SectionLabel`（13 bold secondary），正文复用 `BodyLine`（14 ink），不发明新字号。 |
| 13 | **M3 Type scale**：Display/Headline/Title/Body/Label 五档角色，字号+行高+字重绑定。 | `https://m3.material.io/styles/typography/overview` —— 「Typography – Material Design 3」，HTTP 200（标题可验；正文沿 v2 外环记录） | 映射：Title→卡标题 16 bold / Body→`BodyLine` 14 + `TextLine` 13 / Label→`BadgeText` 11 bold + 筛选胶囊 13（选中 bold 白字/未选中常规 secondary）/ 计数 12。中文场景 CJK 等效大字按 WCAG 定义换算（见 #9）。建议：徽章文字保持 bold（小字号用字重补可读性），筛选选中/未选中用"底色+字重"双差（已是）。 |
| 14 | **状态色语义固定（HIG Color / M3 Color roles）**：红=危险、绿=确认、橙=警示、蓝=信息/主行动。 | HIG `https://developer.apple.com/design/human-interface-guidelines/color`（「Color」，200，标题可验）<br>M3 `https://m3.material.io/styles/color/roles`（「Color roles」，200，标题可验） | 已落地：`accent #x007aff` 蓝=主 CTA/信息（建守护/筛选选中/添加），`#x34c759` 绿=主行动确认（`确认这条守护`），`#xff3b30` 红=危险（取消/冲突卡/清空），`#xff9500` 橙=警示（重新收敛/改时间），`#x5856d6` 紫=撤销（独立于红绿避免混淆），灰 `#xf2f2f7/#xefeff4`=次级容器。缺"成功绿"已补（确认键绿）。建议：后续"已结算/已到场"类成功态复用 `#x34c759`，不引入新绿。 |
| 15 | **卡片分组（M3 Cards）**：圆角+留白+单职责，一卡一事，低频操作折叠。 | `https://m3.material.io/components/cards` —— 「Cards – Material Design 3」，HTTP 200（标题可验） | 已落地：`Card` 工厂 `RoundedView{border_radius:14 padding:12 spacing:8 白底}`；`Badge{border_radius:7}`；冲突卡 `border_radius:12`；展开态 section `spacing:2` + 细线 `View{height:1 #xefeff4}` 分隔；低频四键折叠进"怎么用？"卡（#29）；空分支永远留 1px 占位防残留。约束红线（A1/A2/A4）：卡内深度 ≤6、`show_bg:true`+显式宽高、同父不并置两同类子节点（冲突两行已各自成卡）。建议：新分组先套 `Card`，不手写圆角值。 |
| 16 | **按钮排布主次分明（M3 Buttons）**：主行动实心高对比，破坏性降权，确认态单独成行。 | `https://m3.material.io/components/buttons` —— 「Buttons – Material Design 3」，HTTP 200（标题可验） | 已落地：`action_row`（确认绿实心 / 重新收敛橙实心 / 取消守护灰底红字降权）+ 确认态 `确认取消（5s）` 红实心**单独成行**（`on_render` 顶部）+ 撤销 `撤销取消` 紫实心配浅紫条 + 低频区灰底三键 + 红字 `清空全部`。`draw_text` 白字 on 实心色，`border_radius:16/20`，`color_hover/color_down` 三态。建议：保持"默认取消键永不红底"（只有二次确认态才红底），防误触心智。 |
| 17 | **列表行信息三层（M3 Lists）**：标题/说明/原文截断，筛选+计数+搜索叠加。 | M3 Lists（同 #3）+ `https://m3.material.io/foundations/accessible-design/overview`（「Material Design」，200，标题可验；无障碍基线沿 v2 外环记录） | 已落地：折叠三行=标题+徽章 / `活动·地点·共N字` / 原文截断 24 字+"…"（`split("")` 逐字拼，B2/B3 绕法）；`set_filter()` 四标签（`all/Proposing/Confirmed/Cancelled`）+ `set_query()` 子串搜索（activity/place/text）叠加，计数 `"共 N / M 条"`（`filter_count_str/matched_total_str`）；选中用 `GestureView` 整卡可点。建议：截断阈值 24 字不动（改即影响"共 N 字"一致性契约）。 |
| 18 | **留白与分组节奏（HIG Layout / M3 Layout）**：8pt 网格，外 16 内 12/20，行距 10/12。 | HIG `https://developer.apple.com/design/human-interface-guidelines/layout`（「Layout」，200，标题可验）<br>M3 `https://m3.material.io/foundations/layout/applying-layout`（「Material Design」，200，标题可验） | 已落地：根 `SolidView{padding:16 spacing:12}` / `case_list ScrollYView{spacing:10}` / `Card{padding:12 spacing:8}`（首用/说明卡 `padding:20`）/ 输入行 `spacing:8` / 标题行 `spacing:8~10`；圆角梯度：卡 14 > 按钮 16/20 > 胶囊筛选 16 > Badge 7 > 色点 5。文案语气：动词化（"确认这条守护/重新收敛/取消守护"），`hint` 永远"动作+对象+结果"（如"已建守护 #3（分诊命中：time），已选中，点卡片可展开详情"），失败明示（"保存失败…仅在内存"），从不静默。建议：新按钮先看 §二 Top-8 再定位置，不另起第四行。 |

---

## 二、Top-8 打磨项（按 用户感知影响 × 实现成本 排序）

> 均为**文档级建议**（不改 bundle，`#26` 只写文档；排位供后续任务书参考）。

1. **徽章冲突后缀「·冲突」**（`rebuild_lines()` 内 `badge_t + "·冲突"`）：折叠态一眼可扫冲突，零渲染风险，感知最强。
2. **撤销条紫色独立编码**（`undo_bar` `#xf2efff` 底 + `#x5856d6` 键）：与红/绿/橙全部分开，用户把"撤销"认成独立安全网，误触取消的心理成本下降。
3. **筛选选中态双差**（`set_filter()` + 胶囊 `accent` 底白字 bold vs 灰底 secondary）：当前标签零歧义，次级用户（只看不建）获益最大。
4. **空态双分支文案**（`cases.len()==0` vs `filtered_idxs.len()==0`）：新用户得引导、老用户切筛选项不迷路，一次写对长期免维护。
5. **取消键默认降权**（`action_row` 灰底红字，红底只出现在 `确认取消（5s）`）：主区三键视觉重量"绿>橙>灰"，误点率最低成本下降。
6. **`hint` 动词+对象+结果句式**（`add_case/confirm_case/reschedule_case/cancel_case/undo_cancel/clear_all_data/cycle_slot/add_person` 全覆盖）：每次操作都有可朗读的回执，读屏缺失下的最强补偿。
7. **展开态 section 分组+细线**（`SectionLabel+BodyLine` × 状态/参与人/时间/活动/地点/原文/回执）：深度 6 上限内信息密度最高，扫读效率最好。
8. **色点+色条+文字三重状态**（`status_bar_color()` 10×10 点 + `hi_w` 条 + `case_badge_text` 中文）：色弱用户靠文字、普通用户靠色块，两端同时照顾。

---

## 三、明确不可为（对照 `splash-constraints.md`，逐条给替代补偿）

| # | 规范要求 | 硬约束 | 替代补偿（已落地） |
|---|---|---|---|
| N1 | 动态字体 / 系统字号跟随（HIG Typography Dynamic Type，WCAG 1.4.4 200%） | F：无 `user_scale/font_scale` 槽位（`docs/SCRIPT-API.md` 无此键；第一方六 splash 全固定字号；v2 §九 D 外环核实） | 固定 8 档字号层级（26/16/14/13/12/11）+ 全 `Fit` 高 + `ScrollYView`；`hint`/`export_data()` 长文本自然换行已验证不截断。 |
| N2 | 暗色模式（HIG Color / M3 dark scheme） | F：无 `is_dark` 槽位；第一方系统应用同样固定浅色 | 全浅色硬编码（白卡 + `#xf2f2f7` 输入底 + `ink` 文）；不写任何暗色分支，避免半吊子反转。 |
| N3 | 读屏语义（role/state/label，M3 Accessibility） | F：无 `accessibility_*` 槽位 | 字符补偿：选中 `▶`、展开 `▾`、冲突 `⚠`、回执 `↳`；状态全中文文字（待拍板/已确认/已取消/·冲突）；`hint` 每动作回执一句，可被顺序朗读。 |
| N4 | 精确时刻比较/相对时间（"今天/明天"，T-24h 真提醒） | F：无时钟/日期 API（时间槽只判"同天同时段"） | `guess_slot_day()` 遇"今天/明天/后天"留空（宁空不猜）；`cycle_slot()` 5 槽轮换确定性；回执写明"T-24h 提醒（本地提醒文本，需宿主定时能力）"，如实说明非真定时。 |
| N5 | 富文本换行（`\n`）/ 长文本自由排版 | B5：`Label` 内 `\n` 不换行（`export_data()` 是单 Label 自然换行，非 `\n` 生效） | 冲突两行拆两张卡（A2）或拼一串用 `｜` 分隔；回执四行拆 `case_receipt[j][_ri]` 循环多 `Label`；不用 `\n` 做布局。 |
| N6 | 深层嵌套详情页（状态/时间/参与人/回执一次铺全） | A1：节点深度约 6 上限，超则静默丢弃；A3 同层节点数受限 | 展开块严格与摘要同级、深度 6（状态/参与人+输入行/时间/活动/地点/原文/回执各一 `View`，按钮直接作子节点不另包层）；冲突摘要放折叠态（深层丢弃区不放关键信息，#21 实证）。 |
| N7 | 同卡多并列控件（两按钮/两文本并排一张卡） | A2：同父只渲染第一个同类子节点 | 两行合并进一个 `Label`（冲突卡）或各自一张卡；按钮行用 `flow:Right spacing` 单 `View` 包多个 `ButtonFlat`（异类节点不触发）。 |
| N8 | 任意位置的条件显隐（根 `if/visible`） | E1：根组件属性首次求值定型；C1：`on_render` 闭包禁读 `cases[i][…]` | 随状态变的全进 `case_list.on_render`（确认态按钮/撤销条/筛选栏/搜索框/说明卡/空态/列表），闭包只读扁平 `case_*/filter_*/current_*` 字符串数组，逻辑放 `rebuild_lines()/set_filter()/set_query()` 等函数上下文。 |
| N9 | 像素级度量与真机抓帧自证 | F：无头环境 `/g` grab 超时；编辑器无 WCAG/触控尺 | 静态审计（`splash-constraints.md` 自检命令全 0）+ jail 数据自证（`regression-20261001.md`）；真截图留待有显示器机器（回归 §四明示），本文件不臆测渲染效果。 |

---

## 四、URL 实测清单（本会话 `web_fetch`，`date -u`：2026-10-01 02:22 UTC，fetch 窗口约 02:10–02:22 UTC）

| URL | fetch 时间（UTC） | 状态码 | 标题/备注 |
|---|---|---|---|
| `https://developer.apple.com/design/human-interface-guidelines/typography` | 2026-10-01 ~02:1x | 200 | Typography｜Apple Developer Documentation（正文 JS 渲染未提取） |
| `https://developer.apple.com/design/human-interface-guidelines/color` | 同上 | 200 | Color（同上） |
| `https://developer.apple.com/design/human-interface-guidelines/buttons` | 同上 | 200 | Buttons（同上） |
| `https://developer.apple.com/design/human-interface-guidelines/lists-and-tables` | 同上 | 200 | Lists and tables（同上；v2 外环由 404 纠正而来） |
| `https://developer.apple.com/design/human-interface-guidelines/feedback` | 同上 | 200 | Feedback（同上；v2 外环由 404 纠正而来） |
| `https://developer.apple.com/design/human-interface-guidelines/alerts` | 同上 | 200 | Alerts（同上；v2 外环由 404 纠正而来） |
| `https://developer.apple.com/design/human-interface-guidelines/onboarding` | 同上 | 200 | Onboarding（同上） |
| `https://developer.apple.com/design/human-interface-guidelines/inputs` | 同上 | 200 | Inputs（同上） |
| `https://developer.apple.com/design/human-interface-guidelines/layout` | 同上 | 200 | Layout（同上） |
| `https://m3.material.io/components/lists` | 同上 | 200 | Lists – Material Design 3（正文 JS 渲染未提取） |
| `https://m3.material.io/components/dialogs` | 同上 | 200 | Dialogs – Material Design 3（同上） |
| `https://m3.material.io/components/app-bars` | 同上 | 200 | Top app bar – Material Design 3（注意：该路径实际标题为 Top app bar；v2 记"app-bars 200"属实，标题补正） |
| `https://m3.material.io/styles/color/roles` | 同上 | 200 | Color roles（同上） |
| `https://m3.material.io/components/cards` | 同上 | 200 | Cards – Material Design 3（同上） |
| `https://m3.material.io/components/buttons` | 同上 | 200 | Buttons – Material Design 3（同上） |
| `https://m3.material.io/styles/typography/overview` | 同上 | 200 | Typography – Material Design 3（同上） |
| `https://m3.material.io/components/snackbar` | 同上 | 200 | Snackbar（同上；v2 外环由 `snackbars` 404 纠正为单数） |
| `https://m3.material.io/foundations/accessible-design/overview` | 同上 | 200 | Material Design（仅壳标题；v2 外环由 `accessible-design/accessibility-basics` 404 纠正而来） |
| `https://m3.material.io/foundations/layout/applying-layout` | 同上 | 200 | Material Design（仅壳标题） |
| `https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html` | 同上 | 200 | 全文可验（1.4.3，§一 #9 引原文） |
| `https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html` | 同上 | 200 | 全文可验（1.4.11，§一 #10 引原文） |
| `https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html` | 同上 | 200 | 全文可验（2.5.8，§一 #8 引原文） |
| `https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html` | 同上 | 200 | 全文可验（1.4.4，§一 #11 引原文） |
| `https://webaim.org/resources/contrastchecker/` | 同上 | 200 | 全文可验（Contrast Checker：AA normal 4.5:1 / large 3:1，graphics & UI components 3:1） |
| `web_search`（3 queries×2 批） | 2026-10-01 ~02:0x | 失败 | `DeepSeek search has no API key for "DEEPSEEK_API_KEY"`；故竞品加分项（Apple 日历/Google 日历/TickTick/Things 3）**未验证（无搜索工具可用，2026-10-01）**，不编 URL。 |

> 禁止事项遵守：未改 `bundle/` 下任何文件；未碰工作区外 `.secrets/` 与任何凭据；未臆测运行效果（渲染结论以 `regression-20261001.md` 真机记录为准）。

— 完 —
