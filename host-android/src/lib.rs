//! 牵线（Qianxian）Android 移动端内置大模型宿主核心库

pub mod engine;
pub mod grammar;
pub mod bridge;

pub use engine::{LocalModelBackend, LlamaCppBackend, ScriptedMockBackend, EngineError, GenerationMetrics};
pub use bridge::{ServiceBridge, TurnRequest, TurnResponse};
pub use grammar::PLAN_GBNF_GRAMMAR;
