# 剧本 04 · 主动守护 + 群收敛（v0.10.0 新特性）：主动预警提案 → 结案卡 → 收敛提案。
#   依赖 jail 预置（converge.json 由伴生进程写入；本剧本用注入形态验证 app 链路）。
TITLE = "主动守护与群体收敛（v0.10.0）"
STEPS = [
    ("click", "示例", 1.5),
    ("click", "建守护", 2.0),
    ("click", "#1 · 骑车", 2.0),
    ("click", "确认这条守护", 2.2),
    # 群收敛三按钮（Confirmed 态显示）
    ("scroll", 300, 3),
    ("expect_text", "发投票到群"),
    ("expect_text", "刷新计票"),
    ("expect_text", "管家收敛"),
    ("shot", "群投票三按钮（降级明示）"),
    ("back_list",),
    ("shot", "回列表"),
]
