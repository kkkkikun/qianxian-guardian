# 实机剧本 05 · 场景：定不下时间？把投票发到群里，大家回个字母，管家帮你收敛。
TITLE = "场景⑤：群里投个票，管家帮你定时间"
STEPS = [
    ("click", "示例", 1.5),
    ("click", "建守护", 2.0),
    ("click", "#1 · 骑车", 2.0),
    ("click", "确认这条守护", 2.2),
    ("scroll", 300, 3),
    ("expect_text", "发投票到群"),
    ("shot", "定不下时间？点「发投票到群」——候选时段 A-E，成员回个字母就算投票"),
    ("inject", "converge.json", {"case_id": "1", "room": "!demo:local", "summary": "已报 2/3（B:2 E:1）", "winner": "B", "winner_slot": "周六-晚上", "counts": {"B": 2, "E": 1}, "voted": ["a", "b"], "non_member": [], "total_members": 3}),
    ("click", "刷新计票", 1.8),
    ("expect_text", "已报"),
    ("shot", "大家投完了：已报 2/3，周六晚上票最高"),
    ("click", "管家收敛", 2.2),
    ("expect_text", "──▶"),
    ("shot", "管家按票数出提案：改到周六-晚上"),
    ("click", "拍板执行", 2.5),
    ("expect_jail", "status", "Confirmed"),
    ("shot", "你拍板，时间就定了——从群投票到定档，一步到位"),
]
