# 剧本 01 · agentic 主线：群消息 → 交给管家 → 降级（card-host 无 octos 服务）
#   → 本地规则建守护 → 确认 → 回执。
TITLE = "agentic 主线：一句话丢给管家（诚实降级路径）"
STEPS = [
    ("shot", "首屏：守护灯与空列表"),
    ("click", "示例", 1.5),
    ("shot", "示例已填入输入框"),
    ("click", "建守护", 2.0),
    ("expect_jail", "activity", "骑车"),
    ("shot", "#1 守护诞生（待拍板）"),
    ("click", "#1 · 骑车", 2.0),
    ("shot", "详情：状态线+键值"),
    ("click", "确认这条守护", 2.2),
    ("expect_text", "已确认"),
    ("expect_jail", "status", "Confirmed"),
    ("shot", "确认后：回执+日历行"),
    ("back_list",),
    ("shot", "回列表：守护灯+已确认徽章"),
]
