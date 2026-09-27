「牵线」guardian — G1 骨架
====

结构：
  schema.sql        唯一事实源（蓝图 v0.7.1 全量 schema）
  guardian/config.py    配置加载
  guardian/db.py        连接(WAL)/schema 初始化/审计与 revision 助手
  guardian/matrix.py    Matrix Client-Server API 最小封装（login/sync/send，txn 幂等）
  guardian/ingress.py   入站幂等 + bot 自排除 + 事件分发
  guardian/main.py      常驻循环（sync long-poll + scheduler 占位）
  smoke_g1.py           G1 端到端冒烟：双账号发消息 → guardian 落库 → 重放不重复

运行：
  pip install requests
  cp config.example.json config.json   # 填 bot 账号
  python3 -m guardian.main             # 常驻
  python3 smoke_g1.py                  # 冒烟

设计要点（对应蓝图 v0.7.1）：
  - 入站幂等：last_sync_token 持久化 + processed_event_id 主键去重 + 同事务提交
  - bot 自身事件在 ingress 层丢弃（防自触发闭环）
  - m.room.message 之外的 event 类型仅分类不入分诊
  - 每房间至多一个 Active Case：cases 表部分唯一索引（DB 保证，非业务代码自觉）
  - 审计只追加；case_revision 单调递增
