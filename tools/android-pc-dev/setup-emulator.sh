#!/usr/bin/env bash
set -euo pipefail

# 牵线（Qianxian）Android 模拟器电脑端无头初始化脚本
# 遵循原则：100% 电脑端、零窗口、零音频打扰（Headless Mode）

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ANDROID_CLI="$PROJECT_ROOT/tools/bin/android"

if [[ ! -x "$ANDROID_CLI" ]]; then
    echo "❌ 未找到 android CLI 工具: $ANDROID_CLI"
    exit 1
fi

echo "=========================================================="
echo "  牵线 (Qianxian) Android 虚拟设备 (AVD) 无头部署"
echo "=========================================================="

# 1. 检查或创建虚拟设备
AVD_NAME="medium_phone"
echo ">>> 检查已有虚拟设备..."
EXISTING_AVDS=$("$ANDROID_CLI" emulator list 2>/dev/null || true)

if echo "$EXISTING_AVDS" | grep -q "$AVD_NAME"; then
    echo "✓ 虚拟设备已存在: $AVD_NAME"
else
    echo ">>> 未发现虚拟设备，开始自动创建 $AVD_NAME..."
    "$ANDROID_CLI" emulator create "$AVD_NAME"
    echo "✓ 虚拟设备创建成功: $AVD_NAME"
fi

# 2. 检查当前是否已有模拟器或设备运行
ADB=""
if command -v adb >/dev/null 2>&1; then
    ADB="adb"
elif [[ -x "$HOME/Android/Sdk/platform-tools/adb" ]]; then
    ADB="$HOME/Android/Sdk/platform-tools/adb"
fi

if [[ -n "$ADB" ]]; then
    RUNNING_DEV=$("$ADB" devices | grep -v "List of devices" | grep "device$" | head -n 1 | awk '{print $1}' || true)
    if [[ -n "$RUNNING_DEV" ]]; then
        echo "✓ 检测到已有正在运行的 Android 设备/模拟器: $RUNNING_DEV"
        "$ADB" devices
        exit 0
    fi
fi

# 3. 启动无头模拟器
echo ">>> 以无头模式启动模拟器 (--headless, 无弹窗、无音频)..."
EMU_BIN=""
if [[ -x "$HOME/Android/Sdk/emulator/emulator" ]]; then
    EMU_BIN="$HOME/Android/Sdk/emulator/emulator"
fi

if [[ ! -e "/dev/kvm" && -n "$EMU_BIN" ]]; then
    echo "⚠️ 未检测到 /dev/kvm，使用软件模拟 (-no-accel)..."
    "$EMU_BIN" "@$AVD_NAME" -no-window -no-audio -no-accel -gpu swiftshader_indirect >/tmp/qianxian-emulator.log 2>&1 &
    EMULATOR_PID=$!
else
    "$ANDROID_CLI" emulator start --headless "$AVD_NAME" >/tmp/qianxian-emulator.log 2>&1 &
    EMULATOR_PID=$!
fi
echo "模拟器后台进程 PID: $EMULATOR_PID"

echo ">>> 等待模拟器启动就绪..."
if [[ -n "$ADB" ]]; then
    "$ADB" wait-for-device
    echo "✓ 模拟器设备已上线！"
    
    # 等待系统完全 boot 完成
    echo ">>> 等待 Android 系统启动完成 (sys.boot_completed)..."
    while true; do
        BOOT_STATUS=$("$ADB" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r' || true)
        if [[ "$BOOT_STATUS" == "1" ]]; then
            break
        fi
        sleep 2
    done
    echo "✓ Android 系统启动完成！"
    "$ADB" devices
fi

echo "=========================================================="
echo "  无头 Android 模拟器就绪，可执行 deploy-emulator.sh 部署"
echo "=========================================================="
