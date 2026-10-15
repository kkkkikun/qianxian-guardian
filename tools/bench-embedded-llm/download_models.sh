#!/usr/bin/env bash
set -euo pipefail

# 牵线（Qianxian）端侧内置大模型下载脚本
# 默认从国内高速镜像（ModelScope）拉取 GGUF Q4_K_M 权重量化文件

TARGET_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/models"
mkdir -p "$TARGET_DIR"

MODELS=(
    "Qwen2.5-0.5B-Instruct:https://modelscope.cn/models/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/master/qwen2.5-0.5b-instruct-q4_k_m.gguf:qwen2.5-0.5b-instruct-q4_k_m.gguf:397"
    "Qwen2.5-1.5B-Instruct:https://modelscope.cn/models/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/master/qwen2.5-1.5b-instruct-q4_k_m.gguf:qwen2.5-1.5b-instruct-q4_k_m.gguf:1100"
)

echo "=========================================================="
echo "  牵线 (Qianxian) 端侧内置模型下载工具 (ModelScope)"
echo "  目标存储目录: $TARGET_DIR"
echo "=========================================================="

CHOICE="${1:-all}"

download_model() {
    local name="$1"
    local url="$2"
    local filename="$3"
    local approx_mb="$4"
    local dest="$TARGET_DIR/$filename"

    if [[ -f "$dest" ]]; then
        echo "✓ [$name] 已存在: $dest ($(du -h "$dest" | cut -f1))"
        return 0
    fi

    echo ">>> 开始下载 [$name] (~${approx_mb}MB)..."
    if command -v curl >/dev/null 2>&1; then
        curl -L --progress-bar "$url" -o "$dest.tmp"
    elif command -v wget >/dev/null 2>&1; then
        wget --show-progress "$url" -O "$dest.tmp"
    else
        python3 -c "
import urllib.request, sys
url = '$url'
dest = '$dest.tmp'
print('Downloading with python urllib...')
urllib.request.urlretrieve(url, dest)
"
    fi
    mv "$dest.tmp" "$dest"
    echo "✓ [$name] 下载成功: $dest ($(du -h "$dest" | cut -f1))"
}

case "$CHOICE" in
    "0.5b"|"0.5B")
        download_model "Qwen2.5-0.5B-Instruct" \
            "https://modelscope.cn/models/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/master/qwen2.5-0.5b-instruct-q4_k_m.gguf" \
            "qwen2.5-0.5b-instruct-q4_k_m.gguf" "397"
        ;;
    "1.5b"|"1.5B")
        download_model "Qwen2.5-1.5B-Instruct" \
            "https://modelscope.cn/models/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/master/qwen2.5-1.5b-instruct-q4_k_m.gguf" \
            "qwen2.5-1.5b-instruct-q4_k_m.gguf" "1100"
        ;;
    "all")
        for item in "${MODELS[@]}"; do
            IFS=":" read -r m_name m_url m_file m_mb <<< "$item"
            download_model "$m_name" "$m_url" "$m_file" "$m_mb"
        done
        ;;
    *)
        echo "用法: $0 [0.5b | 1.5b | all]"
        exit 1
        ;;
esac

echo "=========================================================="
echo "模型准备完成。请运行 eval_runner.py 开展「稳定·快速·可靠」三维实测。"
echo "=========================================================="
