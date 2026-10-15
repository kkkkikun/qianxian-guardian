# 牵线（Qianxian）Android 原生端宿主 + 内置端侧 LLM (Route A)

> **定位**：基于 Makepad 原生 Android 运行时的移动端宿主，内嵌 `llama.cpp` 端侧大模型推理引擎。
> **目标**：手机完全断网离线，0 外部 API 依赖，端侧完成群消息抽取与 12 个 PLAN 提案拍板。

---

## 1. 架构核心与数据流

```
 ┌────────────────────────────────────────────────────────┐
 │            Qianxian 脚本应用 (bundle/main.splash)       │
 │            100% 复用现有 40/40 项回归状态机与 UI 布局      │
 └───────────────────────────┬────────────────────────────┘
                             │
            host.request("octos.turn.start", {text})
                             │
 ┌───────────────────────────▼────────────────────────────┐
 │        Android 宿主网关 (host-android/src/bridge.rs)     │
 │        - 注册 "octos.turn.start" 原生服务接口           │
 │        - 内存守护与请求排队 (单并发保护移动端 CPU)        │
 └───────────────────────────┬────────────────────────────┘
                             │
                异步通道 (Crossbeam / Channel)
                             │
 ┌───────────────────────────▼────────────────────────────┐
 │      内置端侧推理引擎 (host-android/src/engine.rs)       │
 │      - 引擎底层: llama.cpp (aarch64-linux-android NEON)│
 │      - 模型权重: Qwen2.5-0.5B / 1.5B (GGUF Q4_K_M)     │
 │      - 解码约束: GBNF 语法树 (确保 100% PLAN 格式合规)  │
 └───────────────────────────┬────────────────────────────┘
                             │
                生成结果 (含单行 PLAN{...}) 回调
                             │
 ┌───────────────────────────▼────────────────────────────┐
 │            UI 渲染 PLAN 差异卡片 -> 用户点击拍板        │
 └────────────────────────────────────────────────────────┘
```

---

## 2. 目录结构

```
host-android/
├── Cargo.toml            # Android 宿主工程配置 (含 llama-cpp 与 aarch64 依赖)
├── README.md             # 本文档
└── src/
    ├── lib.rs            # Crate 入口
    ├── engine.rs         # llama.cpp 端侧模型生命周期与推理执行
    ├── bridge.rs         # Splash 与宿主间的 "octos.turn.start" 桥接
    └── grammar.rs        # GBNF 语法内嵌定义
```

---

## 3. 模型选型与评测

评测套件位于 `my-entry/tools/bench-embedded-llm/`：
- `test_dataset.json`：包含 10 组核心测试用例（标准抽取、no-facts 留空、改期、加人、记账、纯问答）。
- `grammar.gbnf`：约束解码语法规则。
- `download_models.sh`：自动从国内 ModelScope 镜像拉取 Qwen2.5-0.5B / 1.5B 权重。
- `eval_runner.py`：自动化打分工具，统计「延迟 / 吞吐 / PLAN 合规率 / 幻觉率」。

---

## 4. 构建与真机运行 (准备工作)

1. **环境依赖**：
   - Rust 1.95+ 与 Android 目标平台：
     ```bash
     rustup target add aarch64-linux-android
     ```
   - Android NDK (r25c+) 与 `cargo-makepad` 工具链：
     ```bash
     cargo install --path ../repos/makepad/tools/cargo_makepad
     ```
2. **下载端侧模型**：
   ```bash
   ./tools/bench-embedded-llm/download_models.sh 0.5b
   ```
3. **编译并部署**：
   ```bash
   cargo makepad android run -p host-android --release
   ```
