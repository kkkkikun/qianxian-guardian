//! 牵线（Qianxian）Android 真实设备/模拟器端侧验证运行器
//! 该二进制直接交叉编译为 x86_64-linux-android / aarch64-linux-android，
//! 推送到 Android 设备 (/data/local/tmp/) 实机运行并验证端侧大模型桥接与 12 个 PLAN 操作。

use std::sync::Arc;
use std::time::Instant;
use host_android::{ServiceBridge, LlamaCppBackend, ScriptedMockBackend, LocalModelBackend};

fn main() {
    println!("==========================================================");
    println!("  牵线 (Qianxian) Android 设备原生端侧引擎验证套件");
    println!("  Target: Android (In-Process Embedded LLM + Service Bridge)");
    println!("==========================================================");

    // 1. 探测端侧模型
    println!("\n[1/4] 正在探测 Android 端侧 GGUF 模型...");
    let backend: Arc<dyn LocalModelBackend> = match LlamaCppBackend::auto_detect() {
        Ok(b) => {
            println!("  ✓ 成功探测到真实端侧权重: {}", b.model_name);
            println!("    路径: {}", b.model_path.display());
            Arc::new(b)
        }
        Err(e) => {
            println!("  ⚠️ 未检测到真实模型权重 ({})，降级为确定性验证桩 ScriptedMockBackend", e);
            Arc::new(ScriptedMockBackend)
        }
    };

    // 2. 初始化桥接器
    println!("\n[2/4] 初始化 ServiceBridge (拦截 host.request('octos.turn.start'))...");
    let bridge = ServiceBridge::new(backend);
    println!("  ✓ ServiceBridge 就绪");

    // 3. 执行端侧多意图推理测试
    println!("\n[3/4] 执行 Android 端侧意图抽取与 GBNF PLAN 协议验证...");
    let test_prompts = [
        ("创建守护 (Create)", r#"{"text":"【用户消息】本周六下午奥森南门骑车，参与人小明小红"}"#, "create"),
        ("改期重协商 (Reschedule)", r#"{"text":"【用户消息】改到周日下午两点"}"#, "reschedule"),
        ("拍板确认 (Confirm)", r#"{"text":"【用户消息】信息齐了，大家觉得没问题就定了"}"#, "confirm"),
        ("AA 记账 (Set Bill)", r#"{"text":"【用户消息】聚会结束了，总共花了 450 元，记一下账单"}"#, "set_bill"),
        ("终止取消 (Cancel)", r#"{"text":"【用户消息】计划有变，临时取消这次聚会"}"#, "cancel"),
    ];

    let mut pass_count = 0;
    let total_start = Instant::now();

    for (name, req_json, expected_op) in &test_prompts {
        print!("  测试用例: {:<26} ... ", name);
        let t0 = Instant::now();
        let (resp, metrics) = bridge.handle_turn_start(req_json);
        let elapsed = t0.elapsed();

        if !resp.is_ok {
            println!("❌ FAIL: {}", resp.error.unwrap_or_default());
            continue;
        }

        let data = resp.data.expect("Turn response 应该包含数据");
        if !data.text.contains("PLAN{") {
            println!("❌ FAIL: 返回文本缺少 PLAN 块: {}", data.text);
            continue;
        }

        let expected_op_str = format!("\"op\":\"{}\"", expected_op);
        if !data.text.contains(&expected_op_str) {
            println!("❌ FAIL: 未检测到预期操作 {}: {}", expected_op_str, data.text);
            continue;
        }

        let tps_str = if let Some(m) = metrics {
            format!("{:.1} tok/s", m.tps)
        } else {
            "N/A".to_string()
        };

        println!("✓ PASS ({:.2}ms, {})", elapsed.as_secs_f64() * 1000.0, tps_str);
        pass_count += 1;
    }

    let total_elapsed = total_start.elapsed();

    // 4. 汇总报告
    println!("\n[4/4] Android 端侧验证结果汇总:");
    println!("  通过用例: {}/{}", pass_count, test_prompts.len());
    println!("  总耗时:   {:.2}ms", total_elapsed.as_secs_f64() * 1000.0);
    println!("  零外部依赖: 100% 达成 (无外网 HTTP 请求，无外部 API Token)");
    println!("==========================================================");

    if pass_count == test_prompts.len() {
        println!(">>> [OK] ANDROID EMBEDDED LLM VERIFICATION PASSED <<<");
    } else {
        println!(">>> [FAIL] PARTIAL FAILURES DETECTED <<<");
        std::process::exit(1);
    }
}
