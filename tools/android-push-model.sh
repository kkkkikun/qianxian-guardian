#!/usr/bin/env bash
set -euo pipefail

# 牵线（Qianxian）端侧内置大模型推送到 Android 设备工具
# 用法: ./tools/android-push-model.sh [0.5b | 1.5b]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MODEL_DIR="$PROJECT_ROOT/tools/bench-embedded-llm/models"

TARGET_MODEL_NAME="${1:-0.5b}"
DEST_DIR="/sdcard/Download/qianxian-models"

# 查找 adb 工具
ADB=""
if command -v adb >/dev/null 2>&1; then
    ADB="adb"
elif [[ -x "/mnt/d/platform-tools/adb.exe" ]]; then
    ADB="/mnt/d/platform-tools/adb.exe"
elif [[ -n "${ANDROID_HOME:-}" && -x "$ANDROID_HOME/platform-tools/adb" ]]; then
    ADB="$ANDROID_HOME/platform-tools/adb"
fi

if [[ -z "$ADB" ]]; then
    echo "❌ 未检测到 adb 命令，请确保 Android SDK platform-tools 在环境变量中。"
    exit 1
fi

case "$TARGET_MODEL_NAME" in
    "0.5b"|"0.5B")
        LOCAL_FILE="$MODEL_DIR/qwen2.5-0.5b-instruct-q4_k_m.gguf"
        REMOTE_NAME="qwen2.5-0.5b-instruct-q4_k_m.gguf"
        ;;
    "1.5b"|"1.5B")
        LOCAL_FILE="$MODEL_DIR/qwen2.5-1.5b-instruct-q4_k_m.gguf"
        REMOTE_NAME="qwen2.5-1.5b-instruct-q4_k_m.gguf"
        ;;
    *)
        echo "❌ 未知模型类型: $TARGET_MODEL_NAME (仅支持 0.5b 或 1.5b)"
        exit 1
        ;;
esac

if [[ ! -f "$LOCAL_FILE" ]]; then
    echo "❌ 本地模型文件不存在: $LOCAL_FILE"
    echo "请先在 tools/bench-embedded-llm/ 下运行 ./download_models.sh 下载模型。"
    exit 1
fi

LOCAL_SIZE=$(stat -c%s "$LOCAL_FILE" 2>/dev/null || stat -f%z "$LOCAL_FILE")
LOCAL_SIZE_MB=$(( LOCAL_SIZE / 1024 / 1024 ))

echo "=========================================================="
echo "  牵线 (Qianxian) Android 端侧模型推送"
echo "  选定模型: $REMOTE_NAME (~${LOCAL_SIZE_MB}MB)"
echo "  目标路径: $DEST_DIR/$REMOTE_NAME"
echo "=========================================================="

echo ">>> 检查已连接的 Android 设备..."
DEVICE_COUNT=$("$ADB" devices | grep -v "List of devices" | grep "device$" | wc -l || true)

if [[ "$DEVICE_COUNT" -eq 0 ]]; then
    echo "⚠️ 未发现已授权的 Android 设备，请确保："
    echo "  1. 手机已开启「开发者选项」与「USB 调试」"
    echo "  2. 手机已允许电脑进行 USB 调试连接"
    echo "  3. 运行 '$ADB devices' 能够显示设备序列号"
    exit 1
fi

"$ADB" devices

echo ">>> 创建目标文件夹: $DEST_DIR"
"$ADB" shell "mkdir -p $DEST_DIR"

echo ">>> 开始推送大模型文件 (传输需要几十秒，请稍候)..."
"$ADB" push "$LOCAL_FILE" "$DEST_DIR/$REMOTE_NAME"

echo ">>> 验证手机端文件大小..."
REMOTE_SIZE=$("$ADB" shell "ls -l $DEST_DIR/$REMOTE_NAME" | awk '{print $5}')
echo "手机端文件大小: $REMOTE_SIZE 字节 (本地: $LOCAL_SIZE 字节)"

if [[ "$REMOTE_SIZE" == "$LOCAL_SIZE" ]]; then
    echo "✓ [OK] 模型推送且完整性校验成功！"
    echo "手机本地路径: $DEST_DIR/$REMOTE_NAME"
else
    echo "⚠️ 警告：手机端文件大小与本地不一致，可能传输被截断，请重试。"
    exit 2
fi

echo "=========================================================="
echo "下一步：构建并安装 Android App，宿主将自动从该路径挂载离线模型。"
echo "=========================================================="
