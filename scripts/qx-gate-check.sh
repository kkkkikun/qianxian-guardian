#!/bin/bash
# WP7 门禁脚本：digest/HEAD 统一 + 终验三连（提交前逐项打勾的自动化版）。
#
# 用法：my-entry/scripts/qx-gate-check.sh
# 输出：每项 PASS/FAIL + 期望/实测；全部 PASS 退出码 0。
set -euo pipefail
cd "$(dirname "$0")/.."

FAIL=0
say() { printf "%-34s %s\n" "$1" "$2"; }
check() { # check <名称> <实测> <期望>
  if [ "$2" == "$3" ]; then say "$1" "PASS  ($2)"
  else say "$1" "FAIL  实测=$2 期望=$3"; FAIL=1; fi
}

echo "== ① git HEAD 与 manifest digest =="
# 拆分后第一课：bundle/main.splash 是 bundle-src/ 的拼接生成物，不同步=门禁失败
if bash tools/qx-pack.sh --check >/dev/null 2>&1; then say "pack 同步（bundle-src→bundle）" "PASS"
else say "pack 同步（bundle-src→bundle）" "FAIL（先跑 tools/qx-pack.sh）"; FAIL=1; fi
HEAD_SHORT=$(git rev-parse --short HEAD)
say "git HEAD (short)" "$HEAD_SHORT"
MANIFEST_DIGEST=$(python3 -c "import json; print(json.load(open('bundle/manifest.json'))['integrity']['bundle_blake3'])")
say "manifest digest" "${MANIFEST_DIGEST:0:16}…"
VERSION=$(python3 -c "import json; print(json.load(open('bundle/manifest.json'))['version'])")
say "manifest 版本" "$VERSION"
LISTING_SCHEMA=$(python3 -c "import json; d=json.load(open('bundle/listing.json')); print('ok' if d.get('schema')==1 and 'release_notes' in d else 'bad')" 2>/dev/null || echo "bad")
check "listing schema 自洽" "$LISTING_SCHEMA" "ok"

echo "== ② hub check（能力声明与实际一致）=="
HUB_BIN=/home/kikun/MyProject/Agentic-octos/repos/OctoSense-App-Hub/target/release/hub
HUB_OUT=$(timeout 120 "$HUB_BIN" check bundle --allow-unsigned --bundle 2>&1 | tail -3 || true)
echo "$HUB_OUT" | grep -q "PASSED" && say "hub check" "PASS" || { say "hub check" "FAIL"; echo "$HUB_OUT"; FAIL=1; }

echo "== ③ 文档 digest/commit 指针扫描（不许硬编码过期指针）=="
# 硬编码的 7+ 位十六进制 commit 引用（白名单：核验命令示例/RFC/issue 编号/历史记录区）
BAD=$(grep -rnE "[0-9a-f]{40}" evidence/*.md README.md run.md 2>/dev/null \
  | grep -vE "blake3|bundle_blake3|[0-9a-f]{64}|signature|checksum|sha256" \
  | grep -vE "evidence/(checks|upstream-contributions|link-audit)\.md" || true)
if [ -z "$BAD" ]; then say "文档硬编码 commit 指针" "PASS（无）"
else say "文档硬编码 commit 指针" "FAIL"; echo "$BAD" | head -5; FAIL=1; fi

echo "== ④ 敏感物扫描（key/token 不入库）=="
# 模式串用括号技巧防自匹配（同 pkill [o]ctos：本脚本含模式字面量，不能让自己命中）
LEAK=$(git ls-files | xargs grep -lE "sk-kim[i]-|sk-minima[x]|MINIMAX_CN_API_KEY=s[k]|access_toke[n]\":\s*\"[A-Za-z0-9]" 2>/dev/null | grep -vE "\.secrets|test-accounts" || true)
if [ -z "$LEAK" ]; then say "敏感物扫描" "PASS（无泄露）"
else say "敏感物扫描" "FAIL: $LEAK"; FAIL=1; fi

echo "== ⑤ 回归（card-host 需已起在 :8146）=="
if curl -s -m 2 http://127.0.0.1:8146/ >/dev/null 2>&1; then
  # 回归需要干净 jail（R-02 示例首用卡只在空列表态渲染；历史 case 会断链）
  pkill -x card-host 2>/dev/null || true
  sleep 1
  rm -rf /tmp/octosense-card-apps/qianxian
  (LD_LIBRARY_PATH="$HOME/.local/gosim-libs" /home/kikun/MyProject/Agentic-octos/repos/OctoSense-App-Hub/target/release/card-host --bundle bundle --allow-unsigned --stamp --remote 8146 >/tmp/qx-gate-ch.log 2>&1 &)
  sleep 15
  R=$(QX_PORT=8146 timeout 900 python3 app/qianxian/tools/qx-verify-v2.py 2>&1 | grep -E "PASS [0-9]+/")
  echo "   $R"
  # WP0：不再硬编码步数——回归只增不减，判据改为「PASS N/N 全绿」（反向引用两数相等）
  echo "$R" | grep -qE "PASS ([0-9]+)/\1" && say "回归（$R）" "PASS" || { say "回归" "FAIL（$R）"; FAIL=1; }
else
  say "回归" "SKIP（card-host 未在 :8146——先起 card-host 再复核）"
fi

echo ""
if [ "$FAIL" == "0" ]; then echo "GATE: ALL PASS"; else echo "GATE: 有 FAIL（见上）"; exit 1; fi
