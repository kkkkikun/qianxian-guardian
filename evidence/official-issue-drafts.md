# 官方 issue 留言草稿（待成员信息补齐即发，2026-09-30）

## #5 参赛主题（gosimfoundation/hackathon-agenticapp26#5）

**状态：待补两个字段即可发送。** #13（仓库地址）已于 2026-09-30 发出并确认在列。

issue 要求格式：队伍名 / 队伍成员id / 参赛主题赛道 / 是否加群

```
- 队伍名：Aurora-X
- 队伍成员id：⬜ 待填（报名表上的成员 id）
- 参赛主题赛道：日历（官方 12 场景之一；联动即时消息）
- 是否加群：⬜ 待填（是/否）
```

发送命令（补完两个 ⬜ 后）：
```sh
gh issue comment 5 -R gosimfoundation/hackathon-agenticapp26 --body "$(cat 草稿)"
```

**为什么赛道填「日历」**：`task.md` 开篇即声明主场景为日历，官方 12 场景指南的日历条目
核心动词是「时间收敛、冲突检测、待定 vs 已确认」——与本作品逐条对齐，
证据见 `evidence/official-scenario-alignment.md`。

发送：`gh issue comment 5 -R gosimfoundation/hackathon-agenticapp26 --body "..."`

## #13 初赛仓库地址（gosimfoundation/hackathon-agenticapp26#13）

格式（issue 要求）：队伍名 / GitHub 仓库地址

```
队伍名：Aurora-X
GitHub 仓库地址：https://github.com/kkkkikun/qianxian-guardian
```

发送：`gh issue comment 13 -R gosimfoundation/hackathon-agenticapp26 --body "..."`

## 前置确认

- 公仓 `master` 已推送（含 LICENSE/PRIVACY/README/run/task/blueprint/evidence）
- submit issue：https://github.com/kkkkikun/qianxian-guardian/issues/1（digest 见核验命令）
- bundle：`app/qianxian/bundle`（`hub check — PASSED`，digest 见核验命令）
