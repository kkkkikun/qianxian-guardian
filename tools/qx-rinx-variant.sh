#!/bin/bash
# v0.8.0：生成 Rinx 演示变体 bundle。
#
# 背景：主 bundle（App Hub 提交形态，contract 1.10）声明了 device_calendar 能力 +
#   requires:["host-api-v1"] + host_api.optional + agent.instructions/model（新契约字段）
#   ——Rinx backup 的 vendored contract 是旧快照（封闭能力清单 + deny_unknown_fields，
#   AgentSpec 只认 profile/tools/max_iterations/token_budget），遇到这些字段会拒载。
#   Rinx 是决赛实机演示宿主，所以要一份去掉这些字段的变体 manifest（其余文件与主
#   bundle 同源拷贝）。这是 v0.4.0 计划「变体 manifest」纪律的延续。
#   PLAN 协议嵌在 app 内提示词（build_agent_turn），不依赖 manifest 的 instructions——
#   剥掉不影响管家对话；AGENT.md 文件仍在 bundle 内（宿主 Ask 面板按约定路径读）。
#
# 用法：tools/qx-rinx-variant.sh [输出目录，默认 /tmp/qx-rinx-bundle]
set -euo pipefail
SRC="$(cd "$(dirname "$0")/../bundle" && pwd)"
DST="${1:-/tmp/qx-rinx-bundle}"
rm -rf "$DST"
mkdir -p "$DST"
# manifest 剥离新契约字段（python3 稳妥删键）
python3 - "$SRC/manifest.json" "$DST/manifest.json" <<'EOF'
import json, sys
m = json.load(open(sys.argv[1]))
m["capabilities"] = [c for c in m["capabilities"] if c != "device_calendar"]
m.pop("host_api", None)
m.pop("requires", None)
# Rinx backup 拒绝一切 agent 块（「Bundle agent profiles are not supported here；
# declare explicit octos.* services instead」——v0.3.0 在档结论）：管家对话走
# octos.turn.start 显式服务声明，不需要 agent 会话配置；AGENT.md 文件保留在 bundle
# 内（宿主 Ask 面板按约定路径读取）。
m.pop("agent", None)
json.dump(m, open(sys.argv[2], "w"), ensure_ascii=False, indent=2)
EOF
# 其余文件原样拷贝（main.splash / AGENT.md / 图标等）
for f in "$SRC"/*; do
  b="$(basename "$f")"
  [ "$b" = "manifest.json" ] && continue
  cp -r "$f" "$DST/"
done
# 重算 digest（变体 manifest 与主 bundle 不同——不 stamp 会被 Rinx Review 拒
# 「bundle digest … does not match」，2026-10-11 实测踩坑）
HUB=/home/kikun/MyProject/Agentic-octos/repos/OctoSense-App-Hub/target/release/hub
"$HUB" stamp "$DST" >/dev/null
echo "Rinx 变体已生成：$DST（manifest 差异：-device_calendar/-host_api/-requires/-agent 块；已重 stamp）"
