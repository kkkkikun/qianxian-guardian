# 初赛交付倒计时清单（2026-10-01 盘点）

> 冻结：10-4 23:59（初赛）。已完成项列在「机器可验已完成」，
> 未完成项按**谁做**分列。

## 机器可验已完成（无需再动）

- [x] `hub check — PASSED`（仅 unsigned warning）。
      **当前 digest / commit 以核验命令为准**（避免文档过期）：
      `python3 $OCTO check app/qianxian/bundle` 与 `git rev-parse --short HEAD`
- [x] `hub scan` 7 问作答（`evidence/qianxian/review.json` + `review-answers.md`）
- [x] **三张关键截图**：`bundle/screenshots/{01-main,02-expanded,03-conflict}.png`
      （412×892；01 折叠态 / 02 展开态 / 03 冲突失败态）——本环境无图形会话，
      抓帧超时，故按**真实控件树渲染**，来源已在 review 答复中如实标注
- [x] card-host 真跑：14 项功能全量回归（`evidence/regression-20261001.md`）
- [x] 公仓推送（submit issue #1 已开；**commit 与 digest 在核验时同步刷新**）
- [x] 官方 issue **#13 已发**（队名 + 仓库地址）
- [x] 历史脱敏（真密码 0 残留）+ config.example 占位
- [x] PRIVACY / listing 真值（Aurora-X / foxmail / 公仓链接 200）
- [x] 文档自洽：13 内部链接有效 + 外部 URL 实测（`evidence/link-audit.md`）
- [x] 决策留痕：形态选型（`submission-form-decision.md`）、
      验收映射（`acceptance-mapping.md`）、对比度实测（`contrast-audit.md`）

## 待人（按截止排序）

| # | 事项 | 谁做 | 说明 |
|---|---|---|---|
| 1 | **演示视频** 2–3 分钟 | **你** | 按 `evidence/demo-script.md` 录（21 步三线 + 口播稿；每步输入均经真机验证） |
| 2 | **官方 issue #5 留言** | 我发（你给信息） | 需要：队伍成员 id、是否加群。草稿见 `official-issue-drafts.md`（队名/赛道已定） |
| 3 | **宿主原始像素截图**（可选） | 你（若有显示器机器） | `python3 $OCTO shot 8141 bundle/screenshots/01-main.png` 可覆盖现渲染图 |
| 4 | 成员名单锁定 | 你 | 10-4 当天锁（队名 Aurora-X 已定） |
| 5 | 队外复现（验收 #12） | 队外用户 | 按 `run.md` 三段式走一遍 |

## 冻结日动作（10-4）

1. 锁名单（队名/队长/成员登记）；
2. 确认 `master` HEAD 即冻结版本，**把该 commit 与 digest 写进 submit issue #1**；
3. 以冻结版本提交初赛材料（含视频）。

## 已不适用（形态差异，见 `acceptance-mapping.md`）

- Rinx GUI 六步、bot 移出房间、守护进程崩溃补偿——均为 Python guardian 原型的能力，
  script-app 形态不适用；同套设计在 `app/guardian/` 保留为场外证明（G1–G5 冒烟 70+ 断言全绿）。
