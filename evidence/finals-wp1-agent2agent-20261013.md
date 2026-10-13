# WP1 · 双实例牵线：agent × agent 群体协调（旗舰）证据

> 验证级别：**verified**（palpo 双账号真实房间全链）；边界如实标注在文末。

## 链路（全链无人类输入字符，拍板点击除外）

1. 组织者端（card-host 真 UI 驱动）：建守护「周六上午去深圳湾骑车」→ 确认 → 详情「发投票到群」。
   card-host 无 matrix 服务 → 按 WP3-A 降级设计，app 把投票卡文案填进输入框；
   e2e 读回该文案由 guardian MatrixClient 真发入房（**协议文案与 app 同源**，非手抄）。
2. 成员端伴生进程 `tools/qx-member-agent.py`：sync 读房 → 识别投票卡 → 读本端 jail
   cases.json → **确定性自治策略**（模型零参与）：首选撞期（成员周六-上午已有羽毛球守护）
   → 投顺延项 B + 房内一句理由「首选撞期，顺延到 周六-下午」。
3. 组织端归票桥 `qx-converge-bridge.py` 写 converge.json → app「刷新计票」→
   「管家收敛」出改期 diff 提案卡 → 人点「拍板」→ cases.json 落盘（周六-下午，仍 Confirmed）。
4. 改票幂等：成员手动改投 C（app 侧 Outbox member-revote.json → 伴生进程发信）→
   归票 latest-wins，胜项翻转为 C；手动票不被自治重评估回滚（auto=false 守卫）。

## 复现

```sh
./palpo-ctl.sh start            # palpo @8128 + PG
python3 tools/qx-wp1-e2e.py     # 期望：WP1-E2E ALL PASS（16 项断言）
python3 tools/qx-member-agent.py --selftest   # 期望：7/7 PASS（策略纯函数）
python3 tools/qx-converge.py                  # 期望：归票自测 5/5（含改票幂等）
```

e2e 实测输出（2026-10-13 本轮真跑）：

```
[PASS] 组织者建守护 #1 / 已确认 Confirmed / 发投票到群按钮可见 / 投票卡文案已从 app 取回
[PASS] 成员端自治投票 B（顺延）+ 理由 :: B 首选撞期（周六-上午），顺延到 周六-下午
[PASS] 字母票 B 真达房间 / 顺延理由真达房间
[PASS] 归票：winner=B（顺延票被归入）:: 已报 1/0（B:1）
[PASS] 计票显示（已报 1/1）/ 管家收敛按钮可见 / 收敛提案卡出现（拍板键）
[PASS] 拍板落盘：改期为周六-下午且仍已确认 :: 周六-下午 Confirmed
[PASS] 改投幂等：归票 latest-wins 胜项翻转为 C :: winner=C counts={'C': 1}
[PASS] 成员端显示手动改投（auto=false 不被自治回滚）/ 手动票稳定
WP1-E2E ALL PASS
```

## 回归新增（R-32/33/34）

- R-32：jail 注入 member-vote.json → 主页「管家替你投了 B（周六-下午）——首选撞期，顺延」
  横幅 + 「改投首选」按钮 → 点击后 Outbox member-revote.json 落盘断言。
- R-33：`qx-member-agent.py --selftest` 7/7（首选无冲突/顺延/全撞弃权/多撞顺延/空候选/卡片识别/活跃态过滤）。
- R-34：`qx-converge.py` 归票自测（latest-wins 幂等既有覆盖）。

## 诚实边界

- **自治策略是确定性规则**：冲突判定与顺延选择全由代码算，模型不替人表态。
- **真实多设备未验**：同机两 jail 目录 + 同 palpo 两账号；跨设备仅协议层一致。
- **跨账号小程序投票入口受平台限制**：Rinx #90 在案（mini-app 消息编辑/读取缺口）——
  本实现走群消息协议降级路径，不依赖该能力。
- 归票摘要「已报 1/0」中 M=0：组织者守护未加参与人名单（名单为空时归票按实际回复计，
  非成员拒收语义以名单非空为前提——WP3 单测在案）。
- 伴生进程定位同 guardian：宿主侧场外组件；app 自身不触网（card-host 上发送通路为
  文案填回输入框 + 手动/伴生转发，UI 明示）。
