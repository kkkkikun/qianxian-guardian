# #45 C切片 evidence

**Task**: #45 C切片 — agent 自适应提示（AGENT.md v2 临期提醒行为 + agent-brief.json 摘要 + 指路）。

**Commits**
- `cb9bb2b` qianxian UX #45 C切片：agent-brief.json自动同步+「怎么用」卡加第5条指路（main.splash，36 insertions）
- `cbb7c07` qianxian UX #45：AGENT.md标题修断行+主动提示行为小节+压到≤2KB（AGENT.md，25 insertions / 28 deletions）

## 改法一（main.splash）

1. **新增 `let brief_save_result = "ok"`**（line 558）—— 全局扁平字符串，照 `save_result` 范式。
2. **新增 `fn write_agent_brief()`**（line 565）—— 遍历 `cases` 构 `{id, activity, slot_day, slot_part, place, status}` 行（字段全部 `"" + x` 字符串化，与 cases.json 字段一一对应），整体包成 `{seq, cases}.to_json()` 落 `agent-brief.json`。
   - best-effort，失败不阻断：`brief_save_result` 翻 `"fail"`，不打 hint、不影响 cases.json 保存语义——brief 是辅助件、cases.json 才是事实源。取舍写在 fn 头注释里。
3. **`save()` 末尾追加 `write_agent_brief()`**（line 597）—— save() 是唯一落盘咽喉（5 个调用点 1215/1247/1284/1331/1426：建卡/改期/取消/AA/清空），全部路径自动带上。
4. **「怎么用」卡加第 5 条**（line 2257）：`Label{text: "5. 在宿主「Ask 牵线」面板可以问：「周六有什么安排？」——已确认的守护临期时我会主动提醒你" draw_text.color: ink draw_text.text_style.font_size: 14}`——接现有 4 条编号后；内层引号用 `「…」` 中文角括号避免与外层 ASCII `"` 冲突。

## 改法二（AGENT.md）

1. **标题断行瑕疵修复**：`# 牵线 Agent 自述（#3\n7 三件套之一）` → `（#37 三件套之一）`。
2. **新增 `## 主动提示行为（每次回答都要做）` 小节**（line 22）：
   - 先读 `agent-brief.json`（无则读 `cases.json`）；
   - Confirmed → 「提醒：已确认守护 #N·<activity>（<slot_day><slot_part>）」，多条取 slot 靠前；
   - Proposing → 末尾补「#N·<activity> 还没拍板，要继续吗？」；
   - 时间一律 slot_day/slot_part 相对词，不编造当前时刻/倒计时；
   - 全程只说话，无工具，tools=[] 边界重申一次。
3. **总长守住 ≤2KB**：trim 后 2033 字节（≤2048），保留所有主谓与关联段。

## 自测

**card-host 自测未能进行**：
- 沙箱内无 `card-host` / `card-host-qx` 二进制。
- 端口 8146 未监听（`ss -ltn | grep :8146` 无输出）。
- `/tmp/qx-inner45` 不存在。

按 splash 运行时规则（内环沙箱不可用），本项接受 `unverified`（外环在生产环境跑真机/真 runtime 复验，#32/#37/#43/#44 历史均按此口径）。`write_agent_brief()` 只在 `save()` 末尾调用，且 `save()` 是单咽喉（5 个调用点全部走它），结构上等价于"任何状态变更后 brief 都同步刷新"。

## 风险 / 后续

- brief 落盘失败时仅记 `brief_save_result` 全局字符串，不打 hint、不影响 cases.json 保存——这是任务文本明确要求的 best-effort 取舍，与"不静默编造"不冲突（cases.json 仍是事实源，brief 只是辅助件降级）。
- 时间表述严格只用 slot_day/slot_part 相对词（runtime 无时钟 API，agent 也不知道现在几点），AGENT.md 已写明。
- 「怎么用」卡第 5 条 Label 闭合内层用 `「…」` 角括号，避免与外层 `"` 冲突——`sed -n '2257p'` 实测确认。