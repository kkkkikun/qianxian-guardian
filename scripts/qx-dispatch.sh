#!/bin/bash
# 外环派单助手v2：cd锚定 + 任务文本内嵌 + 禁止外读
TASK="$1"
BASE_CWD=/home/kikun/MyProject/Agentic-octos/my-entry
REPO=/home/kikun/MyProject/Agentic-octos
# 模型通路：默认 Kimi Coding Plan（用户提供 sk-kimi key，2026-10-11 实测 PLAN 合规+工具调用）；
# QX_PROVIDER=minimax-cn 可切回 MiniMax-M3（key 均在 .secrets/，不入库）。
if [ "${QX_PROVIDER:-kimi}" = "minimax-cn" ]; then
  KEY=$(cat $REPO/.secrets/minimax_cn.key)
  PROVIDER=minimax-cn; MODEL=MiniMax-M3; KEYENV=MINIMAX_CN_API_KEY
else
  KEY=$(cat $REPO/.secrets/kimi-api-key)
  PROVIDER=kimi-coding; MODEL=kimi-for-coding; KEYENV=KIMI_CODING_API_KEY
fi
COMMON="
【纪律】单文件 commit（仅任务明确允许的文件），不 push。禁全量 git diff/show/log -p；定点 grep/sed，单次 shell 输出 ≤30 行。必须实际编辑文件并 git commit 后才结束回合。
【环境】工作目录必须始终是 /home/kikun/MyProject/Agentic-octos/my-entry。所有命令前必须 cd 到此路径。不要 cat 外环黑板文件（你可能读到旧仓库的内容）。本任务的所有必读内容都在下方任务文本里。
【任务全文】$TASK"
mkdir -p /tmp/qx-logs
for i in 1 2 3; do
  OUT=/tmp/qx-logs/run-$(date +%s)-$$.log
  if [ $i -gt 1 ]; then MSG="【催办$i】上轮失败，立即动手。$COMMON"
  else MSG="$COMMON"; fi
  ( cd "$BASE_CWD" && env "$KEYENV=$KEY" OCTOS_HOME=$REPO/.octos-home \
    $REPO/repos/octos/target/release/octos chat \
    --provider "$PROVIDER" --model "$MODEL" --json -m "$MSG" ) > "$OUT" 2>&1
  if grep -qE 'ACK\(done|ACK\(blocked' "$OUT"; then
    echo "OK attempt=$i log=$OUT"
    grep -E "ACK\((done|blocked)" "$OUT" | head -1
    exit 0
  fi
  echo "FLAKY attempt=$i log=$OUT"
done
echo "FAILED after 3"
exit 1
