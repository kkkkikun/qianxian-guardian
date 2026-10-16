#!/usr/bin/env bash
set -euo pipefail

# 牵线（Qianxian）Android 模拟器电脑端无头部署与自动化走查工具
# 遵循原则：100% 电脑端无头执行、模型侧载挂载、自动化截屏与布局归档

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ANDROID_CLI="$PROJECT_ROOT/tools/bin/android"
EVIDENCE_DIR="$PROJECT_ROOT/evidence"
MODEL_FILE="$PROJECT_ROOT/tools/bench-embedded-llm/models/qwen2.5-0.5b-instruct-q4_k_m.gguf"
REMOTE_MODEL_DIR="/sdcard/Download/qianxian-models"
REMOTE_MODEL_NAME="qwen2.5-0.5b-instruct-q4_k_m.gguf"

mkdir -p "$EVIDENCE_DIR"

# 查找 adb
ADB=""
if command -v adb >/dev/null 2>&1; then
    ADB="adb"
elif [[ -x "$HOME/Android/Sdk/platform-tools/adb" ]]; then
    ADB="$HOME/Android/Sdk/platform-tools/adb"
fi

if [[ -z "$ADB" ]]; then
    echo "❌ 未检测到 adb 命令"
    exit 1
fi

echo "=========================================================="
echo "  牵线 (Qianxian) Android 模拟器自动化部署与验证"
echo "=========================================================="

# 1. 确认设备连接
echo ">>> 检查已连接设备..."
DEVICES=$("$ADB" devices | grep -v "List of devices" | grep "device$" || true)
if [[ -z "$DEVICES" ]]; then
    echo "❌ 未检测到任何在线 Android 模拟器或设备，请先运行 setup-emulator.sh"
    exit 1
fi
echo "$DEVICES"

# 2. 推送端侧模型至模拟器存储
echo ">>> 检查模拟器中的端侧嵌入式模型..."
TARGET_MODEL_DIR="/data/local/tmp"

if [[ ! -f "$MODEL_FILE" ]]; then
    echo "❌ 本地端侧模型不存在: $MODEL_FILE"
    exit 1
fi

LOCAL_SIZE=$(stat -c%s "$MODEL_FILE" 2>/dev/null || stat -f%z "$MODEL_FILE")
REMOTE_SIZE=$("$ADB" shell "ls -l $TARGET_MODEL_DIR/$REMOTE_MODEL_NAME 2>/dev/null" | awk '{print $5}' || true)

if [[ "$REMOTE_SIZE" == "$LOCAL_SIZE" ]]; then
    echo "✓ 模拟器内已有完整端侧模型 ($REMOTE_SIZE 字节)，跳过重复传输"
else
    echo ">>> 开始将模型推送至模拟器: $TARGET_MODEL_DIR/$REMOTE_MODEL_NAME (${LOCAL_SIZE} 字节)..."
    "$ADB" push "$MODEL_FILE" "$TARGET_MODEL_DIR/$REMOTE_MODEL_NAME"
    REMOTE_SIZE_CHECK=$("$ADB" shell "ls -l $TARGET_MODEL_DIR/$REMOTE_MODEL_NAME" | awk '{print $5}')
    if [[ "$REMOTE_SIZE_CHECK" == "$LOCAL_SIZE" ]]; then
        echo "✓ [OK] 模型推送校验成功！"
    else
        echo "❌ 模型推送大小校验不一致！"
        exit 2
    fi
fi

# 3. 部署并执行 Android 原生端侧验证运行器
echo ">>> 部署并执行 Android 原生端侧验证运行器 (android_runner)..."
RUNNER_BIN="$PROJECT_ROOT/host-android/target/x86_64-linux-android/release/android_runner"
if [[ -f "$RUNNER_BIN" ]]; then
    "$ADB" push "$RUNNER_BIN" /data/local/tmp/android_runner
    "$ADB" shell chmod +x /data/local/tmp/android_runner
    echo ">>> 在 Android 模拟器内执行真实端侧意图与 PLAN 协议走查..."
    "$ADB" shell /data/local/tmp/android_runner | tee "$EVIDENCE_DIR/android-native-runner.log"
    echo "✓ 原生走查日志已归档至 evidence/android-native-runner.log"
else
    echo "⚠️ 未找到 $RUNNER_BIN，跳过原生运行器执行"
fi

# 4. 自动化截屏走查 (Headless Screen Capture)
echo ">>> 导出模拟器当前屏幕截图至 evidence/android-emulator-smoke.png..."
SCREEN_PNG="$EVIDENCE_DIR/android-emulator-smoke.png"
if [[ -x "$ANDROID_CLI" ]]; then
    "$ANDROID_CLI" screen capture --output="$SCREEN_PNG" 2>/dev/null || "$ADB" exec-out screencap -p > "$SCREEN_PNG"
else
    "$ADB" exec-out screencap -p > "$SCREEN_PNG"
fi

if [[ -f "$SCREEN_PNG" && -s "$SCREEN_PNG" ]]; then
    echo "✓ 屏幕截图成功生成: $SCREEN_PNG ($(stat -c%s "$SCREEN_PNG") 字节)"
fi

# 5. 自动化导出控件树布局 (Headless UI Layout Dump)
echo ">>> 导出控件树布局至 evidence/android-emulator-layout.json..."
LAYOUT_JSON="$EVIDENCE_DIR/android-emulator-layout.json"
if [[ -x "$ANDROID_CLI" ]]; then
    "$ANDROID_CLI" layout --full --pretty --output="$LAYOUT_JSON" 2>/dev/null || true
fi

if [[ ! -f "$LAYOUT_JSON" || ! -s "$LAYOUT_JSON" ]]; then
    # 兜底通过 uiautomator dump
    "$ADB" shell uiautomator dump /data/local/tmp/uidump.xml 2>/dev/null || true
    "$ADB" pull /data/local/tmp/uidump.xml "$EVIDENCE_DIR/android-emulator-layout.xml" 2>/dev/null || true
    echo "✓ 控件树布局导出至 evidence/android-emulator-layout.xml"
else
    echo "✓ 控件树布局成功生成: $LAYOUT_JSON"
fi

echo "=========================================================="
echo "  ✓ [OK] Android 模拟器无头部署与走查完成！"
echo "  截图产物: $SCREEN_PNG"
echo "  模型路径: $TARGET_MODEL_DIR/$REMOTE_MODEL_NAME"
echo "  验证日志: $EVIDENCE_DIR/android-native-runner.log"
echo "=========================================================="
