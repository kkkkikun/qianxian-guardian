# 已知限制与后续工作

> 初赛提交：如实列出未验证平台、未接通的服务、练习数据范围（2026-09-29 更新）。

## 未验证平台

- E2EE 加密房间未验证（演示用未加密房间，与官方核验口径一致；架构上预留）。
- 大于 4 人的群未优化（2 账号演示规模；设计上不设硬上限）。
- 手机侧载任意应用包不支持（官方口径）；演示用 `card-host` / 桌面 Shell 读本地目录。
- 跨平台：script-app 仅在 Linux card-host 实测；android/ios/macos 声明前需真机验证（当前 listing 只写实测过的平台）。

## 未接通的服务

- 天气（P1，明确划出）：Open-Meteo 对账未实现，不猜、不拿旧数据冒充实时。
- AI/助手：商店应用在 card-host 与 OctoSense Shell 均无 `octos.*`/`model` 服务（`no service answers`，官方 9-27 状态页确认）；本应用无 AI 完整可用，AI 解析仅为可选增强且有降级。
- bot 移出房间的 Dormant 真实路径：代码就绪，待 Rinx GUI 双账号实测（acceptance #6）。
- 系统日历写入：只写自建活动簿（SQLite/script-app storage）；跨应用日历是复赛增强。

## 练习数据范围

- 群消息：本地 Palpo 测试服务器的合成账号（`rinx_test_a/b` + `@guardian_bot`），非真实用户数据；演示时标注“练习数据”。
- LLM 实测：DeepSeek-V4-Flash（ModelScope，演示）；解析输出经严格 JSON 校验 + 防编造比对后才落库。

## 后续工作（复赛方向）

- 天气风险评估（降水概率/体感/风速阈值，octo-weather 同款指标表）+ 天气源故障明示“无法核验”。
- 组织者转移/显式认领（MVP 组织者=首发消息者，不支持转移）。
- 原生互动卡片（初赛用房间消息 + 活动簿网页卡/应用页）。
- 本地模型切换（octos 原生配置，P2）。
