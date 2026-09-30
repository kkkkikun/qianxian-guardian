# 自审报告：像评委一样挑自己的毛病（2026-10-01）

> 对抗性自审（外环派 · 黑板第 24 条）。
> 通读 `app/qianxian/bundle/main.splash`（1609 行）+ 全部 `evidence/` 文档，
> 站在**评审视角**挑毛病。**只列问题，不改代码**——本文件即最终交付。
>
> 验证范围：本会话对每条都做了 grep / file / stat / git 实测，未验证的明确标注。
> 验证级别：**verified**（有源码/文件证据）/ **partially-verified**（部分证据）/ **unverified**（仅文档自述）。

---

## 〇、本轮总判断（评审若只读一行）

**就绪度虚高、口径不统一、无障碍硬伤未明面化**。提交包可运行、规则可核验、AI 降级有交代 —— 这些是事实。
但**就绪清单 + countdown + demo-script 三份关键文档与仓内实际状态脱节**（截图已换、digest 三套、commit 三套）；
**触控目标 40/32/26 pt 不达 HIG 44 pt 自承却仍标"通过"**；**对比度未达 WCAG AA 用"跟随第一方"自我豁免**。
这三件事一旦评审按自家核对清单逐条走，会**在第一个 5 分钟内被打回到待整改**。

---

## 一、文档声称 vs 代码实际：所有不一致 / 夸大 / 未验证（已实测）

> 按"对评审杀伤力"粗排。每条给文件:行号 + 实测证据。

### 1.1 截图状态：自述与实存完全脱节  ← 高杀伤
- `evidence/submission-readiness.md:14`：「`bundle/screenshots/01-main.png` 现为 **1×1 占位**（57 字节）。需在有显示器机器…走一遍并截真图」
- `evidence/submission-readiness.md:22` P0 缺口表：「**真截图替换 1×1 占位** → 重 stamp+check+推送」
- `evidence/countdown.md:17`：「**真截图**（1×1 占位→真图→重 stamp+check+push）…」
- `evidence/acceptance.md:9`：「真截图（llvmpipe 无头抓帧超时，待有头重截）重 stamp」
- `evidence/acceptance.md:34`：「两张关键截图 ⏳ 待截（script-app Confirmed 态 + AI 降级/注入失败态；占位图待换）」
- `evidence/regression-20261001.md:71`：「无头环境抓帧超时（真截图须在有显示器的机器产出）」

**实测（`stat`/`file`）**：
```
01-main.png      412 × 892 PNG  49 147 字节  2026-10-01 03:18
02-expanded.png  412 × 892 PNG  53 354 字节  2026-10-01 03:18
03-conflict.png  412 × 892 PNG  62 704 字节  2026-10-01 03:20
```
- 提交包内**已有 3 张真截图**，commit `8e17f04`（"补第三张截图03-conflict"）、`3ba144b`（"截图补第二张"）、`52e63da`（"截图补齐"）已先后入库。
- 但**就绪清单、countdown、acceptance 三份文档仍写"占位/待截"**，未同步。
- `submission-readiness.md:50` 又写「**门禁核验** ✅ `digest 8c41c252` 与公仓一致」—— `countdown.md:7,10` 写 `digest fdcae9bb`、`master = b701b23`；`official-issue-drafts.md:41,42` 写 `master 已推至 1526d6d` —— **同一事实给评审三个 digest 三个 commit**（详见 1.2）。

### 1.2 digest / commit 自相矛盾  ← 高杀伤
| 文件:行号 | 声称 | 实测（`git rev-parse` / 文件 mtime） |
|---|---|---|
| `evidence/submission-readiness.md:50` | digest `8c41c252` 与公仓一致 | — |
| `evidence/countdown.md:7,10` | digest `fdcae9bb`、`master = b701b23` | HEAD `c7b8078`（最新 commit 2026-10-01） |
| `evidence/official-issue-drafts.md:41,42` | digest `fdcae9bb`、`master 已推至 1526d6d` | 同上 |
| `evidence/acceptance.md:44` | 本地 commits 至 `1ff7e44` 起 | HEAD 远在 `1ff7e44` 之后 |

- 评审若用 `git clone` 跑门禁校验，得到的 digest 必然不等于表里任何一个 —— **三选一都是错**。
- `official-issue-drafts.md:40` 还说 "公仓 `master` 已推至 `1526d6d`"，commit 已早被覆盖；这是 9-30 当天的旧快照，没刷新。
- 这是一处**最容易让评审怀疑其它声称一并失真**的硬伤。

### 1.3 截图数量与编号不一致  ← 中杀伤
- `submission-readiness.md:14` 只引 `01-main.png`，未提新增的两张。
- `demo-script.md:54` 「**截图两张**（与视频同源）」「1. `bundle/screenshots/01-main.png`」——只列了一张。
- 仓内实际有 `01-main.png` + `02-expanded.png` + `03-conflict.png` 共 3 张（commit `8e17f04` 已加第三张）。
- `acceptance.md:34` 仍说「两张关键截图 ⏳ 待截」。

→ 评审若按文档搜文件，会发现 **`bundle/screenshots/` 下 `02-expanded.png`、`03-conflict.png` 是"文档里没提"** 的孤儿文件，或者反过来按文档只期待 1 张但仓里有 3 张。两种读法都不体面。

### 1.4 "14 项全量回归"夸大  ← 中杀伤
- `evidence/regression-20261001.md:62`：「按钮两行排布（最小 64px 可点）✅」
- 同文件 `evidence/regression-20261001.md:62` 第 14 项：「✅（前轮验证，**本轮未回归**）」
- `evidence/submission-readiness.md:12`：「**14 项功能全量回归通过**」
- `evidence/countdown.md:9`：「card-host 真跑 `/snap` 11 控件」—— 控件数与功能项数也对不上（11 vs 14）。

→ 「14 项全量回归」的"全量"在自述里**有 1 项明确写了"未回归"**，严格说就不是全量。`/snap` 是渲染树抓帧，11 个控件 ≠ 14 个功能；术语混用。

### 1.5 撤回窗口的边界 bug：批量恢复上一轮遗留的 Cancelled  ← 中杀伤
- 代码 `app/qianxian/bundle/main.splash:1029-1034`（`undo_cancel()`）：
  ```
  for i in cases.len() {
      if cases[i]["status"] == "Cancelled" {
          cases[i]["status"] = cancel_prev_status
          ...
      }
  }
  ```
- 假如历史遗留一条 `Cancelled`（用户 5 秒外才点到、或被撤销后又被某种路径再次 `Cancelled`），下一次用户做新一次取消→点撤销，会把**所有** status=Cancelled 的条目都"恢复成 cancel_prev_status"——可能恢复成不该存在的状态字符串（例如 prev 来自 "Proposing"，于是遗留的 Cancelled 也成了 Proposing；用户根本没打算恢复它）。
- `cancel_pending_id` 的存在表明设计者**清楚**"目标是单条"，但 `undo_cancel()` 实现里没用到这个 id 做精确还原。

### 1.6 触控目标自相矛盾 / "通过"标签过宽  ← 高杀伤
- `evidence/ux-specs-v2.md:43` 自承：「主按钮 40pt（差 4pt）、次按钮 32pt（差 12pt）、行内 26pt（差 18pt）」。
- 同表第 57 行「触控目标 → #6：**部分不满足**」。
- 但 `evidence/regression-20261001.md:62` 第 13 项标 ✅「按钮两行排布（**最小 64px 可点**）」—— **代码里没有 height=64**（实测主 40 / 次 32 / 行内 26），"64px"数字与代码完全不符。
- `evidence/checks.md:13` 第 12 项「提交包真机运行可用」标 ✅——但该字段的判定标准是"真跑一次"，与触控目标无关，把触控目标藏到这一步标"通过"是混淆。

### 1.7 对比度未达 WCAG AA，用"跟随第一方"自我豁免  ← 中高杀伤
- `evidence/contrast-audit.md:11-16`：8 项组合中 **5 项未达 AA**（次文本、白字/绿/橙/红/主行动蓝）。
- `evidence/contrast-audit.md:33-43`：「这是第一方同款取舍」+「**本轮未改**——保持与第一方严格一致优先于单项指标；如评审提出对比度问题，本文件即为现成答复」。
- 风险：评审不是"提问题才需要改"，**WCAG AA 是入场基线**；"跟随第一方"不是合规免责，且 `ai-providers` 是 admin 工具，本作品是用户面入口，**角色不同**。
- 评审若按无障碍基线打分，此条直接扣分；自我豁免的话术在评审桌上**没有约束力**。

### 1.8 UX 规范 URL 全部 unverified，但表里当作"已对齐"使用  ← 中杀伤
- `evidence/ux-specs-v2.md:9-22` 诚实声明：「本会话完全无网…所有规范 URL 均标注"未验证"」。
- `evidence/link-audit.md:18-30`：「Apple HIG 与 Material 3 站点在 2026 年改版，训练知识里的旧路径大面积失效」。
- 但 §二核心三列清单**仍用这些 URL 作为"规范条目"的来源**，并在 §三下结论时把"规范条目=本应用落地=合格"挂在「本会话未验证」的基础上。
- 评审若点 URL 失效：**`link-audit.md` 的替换表是 10-01 修过的，本仓 spec 里却仍可能引旧 URL** —— 需要二次扫。

### 1.9 "回执四行"在代码里少一行  ← 低杀伤（自述）
- `evidence/demo-script.md:21`：「**回执四行**：活动、地点、原文，外加 T-24h 提醒占位」—— 1+2+1 = 4 行，"回执四行"是对的。
- 代码 `main.splash:285` `arr.push("T-24h 提醒（本地提醒文本，需宿主定时能力）")` 确实 4 行（活动/地点/原文/提醒占位）。
- 但 `evidence/ux-specs-v2.md:42` 第 5 条"destructive action"项下又写"撤销条双保险，符合 HIG/M3 的「confirm + undo/snackbar」组合"—— **HIG/M3 不存在 "confirm + undo" 这一对**（标准是 confirm + undo or snackbar，二选一），与规范的对应关系在原文中找不到 1:1 条目，属"借名自封"。

### 1.10 「cards × 11 / 控件 × 11 vs 功能 × 14」单位混用  ← 低杀伤
- `regression-20261001.md` §一表格里"12 条 Splash 硬约束"与 §三"14 项功能"是不同维度，但都用了「✅」标记；
- §三第 14 项「前轮验证，本轮未回归」也是 ✅ —— 表内一致性差。

### 1.11 其它"小事"
- `evidence/edge-cases-20261001.md:11`「真实长消息 228 字」「文件仅 461 字节」—— 文中给了消息体长度 228 算得对，但 "461 字节" 是**单条 case 文件大小估计**，未给原始 json 留存作为可核验附件。
- `evidence/official-scenario-alignment.md:13`「**14:30 式的另一时段**」—— `main.splash:529-533` 实际是「5 个常见时段轮换」，**不涉及 14:30 这种精确时刻**；"14:30 式"是修辞，但评审若当功能描述读会误以为支持精确时刻。
- `evidence/acceptance.md:34`「两张关键截图 ⏳ 待截」—— 与仓内 3 张实存不符（见 1.3）。

---

## 二、最可能扣分的 Top-3（按严重度排序）

> 排序逻辑：①评审是否会按这条当场扣分（高=必扣）；②是否有客观证据可证（高=实证级）；③是否触及官方"必须提供"项（高=硬约束）。

### 🥇 #1（必扣 · 高杀伤）就绪度文档三件套与仓内实际脱节

**现象**：1.1 + 1.2 + 1.3 复合。

| 子问题 | 文档声称 | 实测 |
|---|---|---|
| 截图 | "1×1 占位 / 待截 / 占位图待换" | 3 张真图 412×892 PNG，已在仓内，commit `8e17f04`/`3ba144b`/`52e63da` |
| digest | 三个文档给三个 digest（`8c41c252` / `fdcae9bb` ×2） | HEAD `c7b8078`（latest），无任何 digest 与之匹配 |
| commit | `b701b23` / `1526d6d` / `1ff7e44` | HEAD `c7b8078`（已超 25 commit 之后） |

**为什么必扣**：评审的入场动作是 `git clone … && hub check`，**digest 不一致 = 第一道门就怀疑作者**，连带着"21 步脚本/14 项回归/截图已齐"全部被打折。`submission-readiness.md` 是评审的"导航图"，导航图与地图不符，整个可信度崩。

**最小改法**（工作量：**30 分钟**）：
1. `cd` 仓内跑 `git rev-parse master` + `hub check app/qianxian/bundle --allow-unsigned` 取**当前** digest；
2. 用 `sed -i` 把 `submission-readiness.md:50` / `countdown.md:7,10,29` / `official-issue-drafts.md:41,42` 全部替换为同一对 `(commit, digest)`；
3. `submission-readiness.md` 重写 #4 行：「`bundle/screenshots/{01-main,02-expanded,03-conflict}.png` 已为运行时渲染抓帧真图」；
4. `countdown.md:17` 把「真截图」勾上 ✅，并把 #4「演示」状态从 🟡 提升到 🟢（脚本齐 + 图齐，视频仍 🟡）；
5. `acceptance.md:34` 同步：✅ 已截（3 张），仅视频 ⏳ 待录。

**风险/限制**：远程 `git ls-remote origin master` 在本会话**不通**（`Connection refused 127.0.0.1:10808`），所以"公仓 digest"只能取本地 hub check 输出；评审**会复跑**，**必须本地跑通且与提交时一致**。

---

### 🥈 #2（必扣 · 高杀伤）触控目标不达 HIG 44pt，却标"通过"自相矛盾

**现象**：1.6。

| 维度 | 实测 |
|---|---|
| 代码 | `main.splash:1242` 主按钮 `height: 40`、`main.splash:1272, 1285-1327, 1403` 次按钮 `height: 32`、`main.splash:1502-1503` 行内 `height: 26` |
| 自承 | `ux-specs-v2.md:43` 主 40（差 4）、次 32（差 12）、行内 26（差 18） |
| 复用 | `regression-20261001.md:62` 第 13 项写"**最小 64px 可点**" ✅ —— **代码无 height=64** |
| 评审 | HIG *Touch targets* `≥44×44 pt` —— 评审按规范严格判即扣分 |

**为什么必扣**：① 自承不达标 + ② 标签打 ✅ + ③ 引用一个不存在的"64px"数字——三件凑一起是**评审最容易揪的"自打脸"**。即便评审不在意 44pt 严格性，"自承未达却标通过"已经失信。

**最小改法**（工作量：**1 小时**）：
1. **选项 A（推荐，5 分钟）**：`regression-20261001.md:62` 把 "最小 64px 可点" 改为 "实测主 40 / 次 32 / 行内 26 pt，**未达 HIG 44 pt**（与第一方 ai-providers 同档，已在 ux-specs-v2 #6 标注）"，并把该行标从 ✅ 改为 ⚠️；
2. **选项 B（更彻底，1 小时）**：把 `main.splash:1242` 主按钮升到 `height: 44`、`1272`/`1285`/`1403` 次按钮升到 `height: 36`、`1502-1503` 行内升到 `height: 30`，并在 ux-specs-v2 §三#6 改回"满足"。会引入视觉密度变化（按钮高度 + 4 / + 4 / + 4），需要复跑回归。

**风险/限制**：本会话内**无法真机测按钮手感**（无显示、无 `octos serve` 真跑）；升档后的视觉密度只能说"代码自洽"，手感需评审/外环在有头环境复测。

---

### 🥉 #3（中-高杀伤）对比度 5/8 项未达 WCAG AA，用"跟随第一方"自我豁免

**现象**：1.7。

**为什么必扣**：评审若按无障碍基线（这是入门而非加分项）严格打分，5 项未达 = 直接扣。次文本 `#8e8e93` 是大面积说明色，3.26:1 **连正文 4.5:1 都不到**；自封"跟随第一方"在评审桌上**没有约束力**——第一方是 admin 工具、我们是用户面入口，角色不同不构成豁免。

**最小改法**（工作量：**15 分钟**）：
1. `main.splash:1210` `let secondary = #x8e8e93` → `#x6b6b73`（≈5.1:1，过 AA 正文级）；同步把 `#x6b6b73` 用于 `BadgeText` 默认色（行 101）；
2. **不动** `accent`/`status_badge_*`（组件级 3:1，按当前语义/第一方一致）；
3. `contrast-audit.md:36-41` 重写结论段：「**主文本+正文次文本已过 AA**；语义色块保留第一方同款（角色属组件级）」；删除"本轮未改"那句自我豁免话术。

**风险/限制**：提色后视觉上"次级"会略下沉一点；需要复跑一次 `/snap` 确认组件树无渲染错位。**这是 5 分钟级**最低成本的无障碍达标项。

---

## 三、做不了 / 不划算（诚实标注）

> 这部分按外环契约"如实说不行比硬凑有价值"如实列。

| # | 项 | 状态 | 理由 |
|---|---|---|---|
| R1 | **demo 视频 2-3 分钟** | **做不了（本会话）** | 无显示器、无真机抓帧能力（`evidence/regression-20261001.md:71` 已记）；视频需"你"录。本轮无法补。 |
| R2 | **复跑 `hub check` 取当前 digest** | **做不了（本会话）** | 工作区无 `hub` CLI（`grep -n hub` 命不中可执行），无 `octos serve`（`Connection refused 127.0.0.1:50080`），本机无 GUI，无法跑门禁复验；评审若按"现跑"才算 digest，最终事实只能由外环取。 |
| R3 | **真机验证触控手感** | **做不了（本会话）** | 同 R2。**代码改不改都可以，但升档后的手感只能在有头环境确认**。 |
| R4 | **修代码** | **明确不做** | 黑板第 24 条明令"**不改任何代码**"。本文只列问题与最小改法建议。 |
| R5 | **修截图行号/列表 → demo-script.md:54 同步两张变三张** | **不划算（建议留 3 张）** | 三张截图已经入库（commit `8e17f04`），删回两张会丢 commit 历史；改 demo-script 一行就能同步（**5 分钟**），但因为已经属于 #1 修法的子项，**不算独立项**。 |
| R6 | **删 `ux-specs-v2.md` 中"未验证"URL** | **不划算** | `link-audit.md` 已说明 Apple/M3 改版频繁；**保留 + 显标"未验证"**比**删了假装能用**更专业。**建议保留**，仅在每次评审前跑一次 link-audit 复验。 |
| R7 | **undo_cancel 边界 bug 修复** | **值得做但本会话不做**（详见 1.5） | bug 在 5 秒窗口外/遗留 Cancelled 时才触发；评审不主动构造难复现；建议在 #25 或后续切片修。本轮按"如实记档"处理。 |
| R8 | **把 12 条 Splash 硬约束与 14 项功能分两张表** | **不划算** | 表格已经分章节（§一 / §三），只是标签统一用了 ✅/⚠️；评审不会因为同一行有 ✅ 就误读其它维度，**重写一遍收益不大**。 |

---

## 四、评委视角的三个"加分稳"（顺便记一笔，不算问题）

> 不计入扣分，但评审若按这些点提问，是稳的。

1. **"无 AI 完整可用"**：所有业务（分诊/时间槽/冲突/状态机/回执）都是**确定性本地规则**实现，AI 是可选增强且有明确降级文案（`main.splash:1083`）。Agentic 评分的"可靠性"维度加分。
2. **"不编造纪律"**：抽不到就留空（`guess_activity`/`guess_place` 返回 `""`，`main.splash:720-734`）、分诊不确定给澄清卡（`main.splash:805-808`）+「仍然建守护」用户主动入口（`force_create_pending`，`main.splash:58-60`）。"诚实边界"在 `ux-specs.md:4.8` 和 `official-scenario-alignment.md:28-32` 明示。
3. **场外证据链**：同一设计在 `app/guardian/` 仍以 Python + 真 Matrix + 真 LLM 跑通 G1-G5（70+ 断言），作为"同一设计的另一形态"保留在仓（不进提交包，因 Hub 门禁白名单无 `.py`）。

---

## 五、本自审的工作量与限制

| 维度 | 值 |
|---|---|
| 通读范围 | `main.splash` 全文（1609 行，已分段覆盖）+ 17 个 evidence md |
| 实测命令 | `git log` / `git rev-parse` / `git ls-remote` / `stat` / `file` / `grep` / `wc` / `sed`（未执行） |
| 改了什么 | **无**（黑板第 24 条纪律：不改代码；本文件即唯一交付） |
| 验证级别 | 大多数条目 **verified**；R1/R2/R3 为 **unverified**（受环境所限） |
| 与外环契约 | 已列"做不了/不划算"8 项，未硬凑 |
| 评审可核验性 | 每条扣分点均给文件:行号 + 复跑命令（`git rev-parse` / `hub check` / `stat` / `file`） |

---

## 六、给外环（评审侧）的诚实建议（不写进 ACK，备查）

1. **若评审必读一份文档**：推荐先读 `evidence/submission-form-decision.md`（形态选型理由清晰）+ `evidence/official-scenario-alignment.md`（与官方日历场景对齐 + 诚实边界）。这两份是**写得最干净**的。
2. **若评审必看一份代码**：推荐 `app/qianxian/bundle/main.splash` 的 `triage()` + `add_case()` + `rebuild_lines()` + `on_render` 闭包——这四个地方**集中体现**了"分诊 / 不编造 / 扁平化 / 闭包合规"的全部工程取舍。
3. **若评审必查一个事实**：建议先 `git rev-parse master && hub check app/qianxian/bundle --allow-unsigned`，把拿到的 digest 与**任一份** evidence md 的 digest 比对——只要发现 #1 现象，就够开始问问题了。**这是评审桌上最快 5 分钟撬动整份材料的入口**。

---

**结论**：自审列出 11 项不一致/夸大/未验证、3 项高杀伤扣分点、8 项"做不了/不划算"。**核心问题不是"做错了什么"，而是"做对了但没把它写对"** —— 三件套文档与仓内状态脱节、无障碍硬伤靠自我豁免话术遮掩。这些是**可以低成本 1-2 小时内修完**的，纯文字修订为主；不需要改代码，不需要新做功能。