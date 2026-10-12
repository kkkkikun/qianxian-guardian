# 剧本 06 · 群智收敛（v0.10.0）：发投票 →（外部成员投票）→ 刷新计票 → 管家收敛
#   → 拍板 → 落盘。用注入 converge.json 驱动 app 链路（双账号投票归票已在
#   tools/qx-converge.py 单测 + palpo e2e 覆盖，见 evidence/v100-wp3-converge）。
TITLE = "群智收敛：从单人工具到群体协调协议"
STEPS = [
    ("click", "示例", 1.5),
    ("click", "建守护", 2.0),
    ("click", "#1 · 骑车", 2.0),
    ("click", "确认这条守护", 2.2),
    ("scroll", 300, 3),
    ("expect_text", "发投票到群"),
    ("shot", "群投票三按钮（降级明示）"),
    # 注入计票结果（伴生进程真实输出形状；case_id 由 seq 决定=1）
    ("inject", "converge.json", {"case_id": "1", "room": "!demo:local", "summary": "已报 2/3（B:2 E:1）", "winner": "B", "winner_slot": "周六-晚上", "counts": {"B": 2, "E": 1}, "voted": ["a", "b"], "non_member": [], "total_members": 3}),
    ("click", "刷新计票", 1.8),
    ("expect_text", "已报"),
    ("shot", "计票显示：已报 N/M → 可收敛到 X"),
    ("click", "管家收敛", 2.2),
    ("expect_text", "──▶"),
    ("shot", "收敛提案卡：diff+群投票分布"),
    ("click", "拍板执行", 2.5),
    ("expect_jail", "status", "Confirmed"),
    ("shot", "收敛落盘：改期生效"),
]
