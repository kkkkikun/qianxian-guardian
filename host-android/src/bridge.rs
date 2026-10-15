//! Splash 与 Android 宿主服务桥接器 (Service Bridge)
//! 拦截并处理 Splash 中的 host.request("octos.turn.start", {text: ...})

use std::sync::Arc;
use serde::{Deserialize, Serialize};
use crate::engine::{LocalModelBackend, GenerationMetrics};
use crate::grammar::PLAN_GBNF_GRAMMAR;

#[derive(Debug, Deserialize)]
pub struct TurnRequest {
    pub text: String,
}

#[derive(Debug, Serialize)]
pub struct TurnResponseData {
    pub text: String,
}

#[derive(Debug, Serialize)]
pub struct TurnResponse {
    pub is_ok: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub data: Option<TurnResponseData>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
}

pub struct ServiceBridge {
    backend: Arc<dyn LocalModelBackend>,
}

impl ServiceBridge {
    pub fn new(backend: Arc<dyn LocalModelBackend>) -> Self {
        Self { backend }
    }

    /// 执行一次管家回合，应用 GBNF 语法约束
    pub fn handle_turn_start(&self, req_json: &str) -> (TurnResponse, Option<GenerationMetrics>) {
        let req: TurnRequest = match serde_json::from_str(req_json) {
            Ok(r) => r,
            Err(e) => {
                return (
                    TurnResponse {
                        is_ok: false,
                        data: None,
                        error: Some(format!("参数解析失败: {e}")),
                    },
                    None,
                );
            }
        };

        match self.backend.generate(&req.text, Some(PLAN_GBNF_GRAMMAR)) {
            Ok((reply_text, metrics)) => (
                TurnResponse {
                    is_ok: true,
                    data: Some(TurnResponseData { text: reply_text }),
                    error: None,
                },
                Some(metrics),
            ),
            Err(e) => (
                TurnResponse {
                    is_ok: false,
                    data: None,
                    error: Some(format!("端侧推理失败: {e}")),
                },
                None,
            ),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::engine::ScriptedMockBackend;

    #[test]
    fn test_bridge_turn_success() {
        let bridge = ServiceBridge::new(Arc::new(ScriptedMockBackend));
        let req = r#"{"text":"【用户消息】本周六下午奥森南门骑车"}"#;
        let (resp, metrics) = bridge.handle_turn_start(req);

        assert!(resp.is_ok);
        assert!(resp.data.is_some());
        let text = resp.data.unwrap().text;
        assert!(text.contains("PLAN{"));
        assert!(text.contains("\"op\":\"create\""));
        assert!(metrics.is_some());
    }

    #[test]
    fn test_bridge_invalid_json() {
        let bridge = ServiceBridge::new(Arc::new(ScriptedMockBackend));
        let (resp, metrics) = bridge.handle_turn_start("not-a-json");

        assert!(!resp.is_ok);
        assert!(resp.error.is_some());
        assert!(metrics.is_none());
    }
}
