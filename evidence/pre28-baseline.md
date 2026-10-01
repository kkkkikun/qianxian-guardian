# 修复前基线（pre-28，外环独立驱动，2026-10-01 ~03:08 UTC）

> 目的：#28 修复（回执 `case_receipt[i]`→`[j]` + 删 `case_counts` 死代码）交付后，
> 用同一驱动脚本重跑，对比验证修复效果。本文件为对照组。
> 驱动脚本：`app/qianxian/tools/qx-drive-outer.py`（已升级 `click_title()` 精确点按 + `type_text()` /t 键入）。
> 端口 8143，全新 jail（/tmp/qx-pre28），bundle digest = `babd47ac`（#27 后）。

## 驱动日志（原文粘贴）

```
[base] W=52 HINT=['已载入 0 个聚会守护', '已确认', '已取消', '③ 组织者点同意，回执与提醒就位']
[fill-ex] W=42 HINT=['已填示例到输入框（不自动建守护），点「建守护」继续', ...]
[add1] W=56 HINT=['已建守护 #1（分诊命中：time），已选中，点卡片可展开详情', '已确认', '已取消']
[typed2] W=56 HINT=['已建守护 #1（分诊命中：time），已选中，点卡片可展开详情', ...]   # /t 键入后 hint 未变（输入框内容待查）
[add2] W=67 HINT=['已建守护 #2（分诊命中：time），已选中，点卡片可展开详情', '已确认', '已取消', '⚠ 时间冲突：#1 · 骑车 也占「周六-上午」时段']
[conflict-labels] ['待拍板·冲突', '⚠ 时间冲突：#1 · 骑车 也占「周六-上午」时段', '待拍板·冲突']   # 双条互标 ✅
[expand2] W=60 HINT=['已展开 #1（再点一次可折叠）', ...]   # ⚠️ 点 #2 标题实际展开的是 #1（驱动按文本子串匹配，点中冲突行引用；已修 click_title 精确匹配）
[confirm] W=60 HINT=['已确认 #2 → Confirmed（组织者拍板，读回一致）（作用于最新一条，因未选中）', ...]
[filter-conf] W=66 HINT=['已折叠 #1（点卡片可展开详情）', '已确认', '已取消', '⚠ 时间冲突：#1 · 骑车 也占「周六-上午」时段', '已确认·冲突']
[receipt-under-confirmed-filter] MISSING(疑似i/j下标bug)
[filter-all] W=60 HINT=['已展开 #1（再点一次可折叠）', ...]
[receipt-under-all-filter] MISSING
[howto] W=60 ...
[slot-btn-visible] True
[cycle-slot] W=60 ...   # 改时间点按 hint 无变化（作用对象不明，待精确验证）
[search-input] True
[/t-resp] {"ok":1}
[search-typed] W=63 ...
[clear-btn-visible] False   # 清空按钮折叠在「怎么用？」卡内且当时卡未展开到低频区
DRIVE-DONE
```

## 对照组结论（修复前行为，待 #28 交付后对比）

1. 冲突双条互标 ✅（`待拍板·冲突` ×2 + 冲突行）：冲突检测逻辑正常。
2. 回执在筛选/展开组合下 MISSING（两次）：与 `case_receipt[i]` vs `[j]` 下标不一致吻合，
   但本轮驱动有点按精度瑕疵（展开错卡），**不能单独作为 bug 实锤**，需 #28 交付后用 `click_title()` 精确重验。
3. 改时间按钮可达但点按效果不明；清空按钮折叠态不可达；搜索 /t 返回 ok 但过滤效果待查。
   以上三项在 #28 交付后重跑时一并精确验证。
