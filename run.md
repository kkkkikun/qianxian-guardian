# run.md — 启动方式与独立复现步骤

> 目标读者：评审/队外用户。按本文件应能在**一台全新 WSL2/Ubuntu 22.04**上复现双账号全流程。
> 所有步骤在 2026-09-27 于本机实测通过（见 `evidence/`）。

## 版本（锁定）

| 组件 | 版本/提交 | 来源 |
|---|---|---|
| guardian（本作品） | `my-entry/app/guardian/`（随提交仓库固定） | 自研，Apache 2.0 |
| Rinx（宿主，GUI 演示用） | main `a72e4b00`（含 PR #28 assistant-executor）；比赛核查基线 `05daf9b` | hagency-org |
| octos serve（LLM 运行时） | `2.0.3-rc.13`（源码 `repos/octos` 构建） | octos-org |
| Palpo（本地 homeserver） | main（9/27 构建）+ PostgreSQL 17（Docker `gosim-pg`） | palpo-im |
| 模型 | DeepSeek-V4-Flash（ModelScope OpenAI 兼容端点）；正式提交切 MiniMax/Kimi（赞助额度，同配置机制） | modelscope / 赞助商 |
| Python | 3.10+，仅依赖 `requests` | — |

## 一次性准备

```sh
# 1. 基础依赖（WSL2 图形演示需要；纯脚本复现不需要）
sudo apt-get install -y libasound2-dev libpulse-dev libdrm-dev docker.io

# 2. 数据库（Postgres 17 容器；国内镜像）
docker run -d --name gosim-pg --restart unless-stopped \
  -e POSTGRES_PASSWORD=palpo_dev -e POSTGRES_USER=palpo -e POSTGRES_DB=palpo \
  -p 127.0.0.1:5433:5432 docker.m.daocloud.io/library/postgres:17

# 3. Palpo 启动（config 已含 db url / allow_registration）
./palpo-ctl.sh start
curl -s http://127.0.0.1:8128/_matrix/client/versions   # 应返回版本列表

# 4. 测试账号：test-accounts.json 已含双账号 + bot；
#    新环境重新注册：两段式 UIAa（首次 POST 取 session，
#    二次带【相同 device_id】+ session + m.login.dummy），注意限流 429 退避
```

## 双账号全流程复现（P0-C / 验收条件 12）

```sh
cd my-entry/app/guardian
cp config.example.json config.json        # bot 凭据已填本地服务器

# 确定性全链冒烟（含 M1/M2/M3 授权、越权确认、UNKNOWN 对账）
python3 smoke_g4b.py

# 注入攻击拦截 + scheduler 崩溃补偿（G5）
python3 smoke_g5.py

# 完整守卫进程（bot 常驻收消息；Rinx GUI 发消息触发）
python3 -m guardian.main
```

**Rinx GUI 路线**（视觉演示，可选）：`../../run-rinx.sh` → `rinx_test_a` 登录
（homeserver 手填 `http://127.0.0.1:8128`）→ 建群邀请 `@guardian_bot` → 群里发
"周六上午去深圳湾骑车，大概两小时？" → guardian 解析并回提案（M1）→
组织者回复"同意" → 群内回执（M2）→ 活动簿 `http://127.0.0.1:8129/` 显示 Confirmed。

## 数据来源与限制

- 群消息：**本地 Palpo 测试服务器的练习数据**（合成账号），非真实用户数据
- 天气（P1）：Open-Meteo 公开 API（无 key），显示采集时间
- LLM：DeepSeek-V4-Flash（演示）；解析输出经严格 JSON 校验 + 防编造比对后才落库

## 已知限制

- 活动簿 Web 仅绑 127.0.0.1（单机演示；多人 token/角色在 P2）
- E2EE 加密房间未验证（与官方核验口径一致）
- 2 账号演示规模；大群未优化
