#!/usr/bin/env bash
# qx-pack.sh —— 把 bundle-src/*.splash 按文件名序拼接为 bundle/main.splash。
#
# 为什么需要它：运行时只认单文件入口（源码级实证：OctoSense-App-Hub
# crates/app-contract/src/entry.rs 的 script_source 只读 bundle/main.splash，
# splash 语言的 use 只作用于同一 VM 内的命名空间，不能引入 bundle 里的其他文件）。
# 因此开发期按关注点拆分为 bundle-src/ 部件，交付物仍是拼接出的单文件。
#
# 用法：
#   tools/qx-pack.sh           # 拼接并覆盖 bundle/main.splash
#   tools/qx-pack.sh --check   # 只校验不同步 → 退出 1（qx-gate-check.sh 门禁调用）
#
# 铁律：bundle/main.splash 是生成物，永远不要直接编辑它；改 bundle-src/ 后跑本脚本。
set -euo pipefail
cd "$(dirname "$0")/.."

SRC_DIR=bundle-src
OUT=bundle/main.splash
TMP=$(mktemp)
trap 'rm -f "$TMP"' EXIT

shopt -s nullglob
parts=("$SRC_DIR"/*.splash)
if [ ${#parts[@]} -eq 0 ]; then
    echo "qx-pack: $SRC_DIR/ 下没有 .splash 部件" >&2
    exit 1
fi
for f in "${parts[@]}"; do
    cat "$f" >> "$TMP"
done

if [ "${1:-}" = "--check" ]; then
    if ! diff -q "$TMP" "$OUT" >/dev/null 2>&1; then
        echo "qx-pack: FAIL bundle/main.splash 与 bundle-src/ 不同步——先跑 tools/qx-pack.sh 再提交" >&2
        exit 1
    fi
    echo "qx-pack: PASS（bundle/main.splash 与 ${#parts[@]} 个部件同步）"
    exit 0
fi

mv "$TMP" "$OUT"
trap - EXIT
echo "qx-pack: bundle/main.splash ← ${#parts[@]} 个部件，共 $(wc -l < "$OUT") 行"
