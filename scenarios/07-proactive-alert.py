# 剧本 07 · 主动守护（v0.10.0 WP4）：pending_plan.json 注入 → 进聊天 → 主动预警
#   提案卡 → 拍板 → 改期落盘 + 一次性消费。
#   真实天气决策分级（沉默留痕三档）已在 evidence/v100-wp4-proactive 覆盖。
TITLE = "主动守护：管家凌晨复核，到点醒来干活"
STEPS = [
    ("click", "示例", 1.5),
    ("click", "建守护", 2.0),
    ("click", "#1 · 骑车", 2.0),
    ("click", "确认这条守护", 2.2),
    ("back_list",),
    # pending_plan.json 由守护进程写入（此处注入等价形态；改期到周二-上午）
    ("inject", "pending_plan.json", {"id": 1, "trigger": "proactive_weather", "precip": 72.0, "weather": "深圳", "day": "周二", "part": "上午", "reply": "⛈ 主动预警：#1 骑车明天降水概率 72%（open-meteo·深圳），建议顺延。已备好改期提案，请拍板。\nPLAN{\"op\":\"reschedule\",\"id\":\"1\",\"slot_day\":\"周二\",\"slot_part\":\"上午\"}", "at": "2026-10-12T03:00:00"}),
    ("goto_chat", "看看"),
    ("expect_text", "主动预警"),
    ("expect_text", "降水概率"),
    ("shot", "主动预警：降水 72%，已备好改期提案"),
    ("expect_text", "──▶"),
    ("click", "拍板执行", 2.5),
    ("expect_jail", "status", "Confirmed"),
    ("shot", "主动提案拍板落盘"),
]
