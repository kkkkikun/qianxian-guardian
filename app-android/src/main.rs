pub use makepad_widgets;
use makepad_widgets::*;
use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};
use std::net::TcpListener;
use std::io::{BufRead, BufReader, Write};
use std::path::PathBuf;
use host_android::{ServiceBridge, LocalModelBackend, LlamaCppBackend, ScriptedMockBackend};

app_main!(App, font_set: International);

const MAIN_SPLASH_SRC: &str = include_str!("../../bundle/main.splash");
const ICON_SVG: &[u8] = include_bytes!("../../bundle/assets/icon.svg");
const SHIELD_SVG: &[u8] = include_bytes!("../../bundle/assets/shield.svg");
const INFO_SVG: &[u8] = include_bytes!("../../bundle/assets/info.svg");

struct LocalAssetServer {
    origin: String,
    stop: Arc<AtomicBool>,
}

impl LocalAssetServer {
    fn start() -> Result<Self, String> {
        let listener = TcpListener::bind("127.0.0.1:0").map_err(|e| e.to_string())?;
        let port = listener.local_addr().map_err(|e| e.to_string())?.port();
        let stop = Arc::new(AtomicBool::new(false));
        let flag = stop.clone();

        std::thread::spawn(move || {
            for stream in listener.incoming() {
                if flag.load(Ordering::Relaxed) {
                    break;
                }
                let Ok(mut s) = stream else { continue };
                let _ = s.set_nonblocking(false);
                let _ = serve_asset(&mut s);
            }
        });

        Ok(LocalAssetServer {
            origin: format!("http://127.0.0.1:{port}"),
            stop,
        })
    }
}

impl Drop for LocalAssetServer {
    fn drop(&mut self) {
        self.stop.store(true, Ordering::Relaxed);
        let _ = std::net::TcpStream::connect(self.origin.trim_start_matches("http://"));
    }
}

fn serve_asset(stream: &mut std::net::TcpStream) -> std::io::Result<()> {
    let mut reader = BufReader::new(stream.try_clone()?);
    let mut request = String::new();
    reader.read_line(&mut request)?;
    let mut line = String::new();
    loop {
        line.clear();
        if reader.read_line(&mut line)? == 0 || line.trim().is_empty() {
            break;
        }
    }
    let path = request.split_whitespace().nth(1).unwrap_or("/").to_string();
    let clean_path = path.split('?').next().unwrap_or("").trim_start_matches('/');

    let bytes = if clean_path.ends_with("icon.svg") {
        Some(ICON_SVG)
    } else if clean_path.ends_with("shield.svg") {
        Some(SHIELD_SVG)
    } else if clean_path.ends_with("info.svg") {
        Some(INFO_SVG)
    } else {
        None
    };

    if let Some(content) = bytes {
        write!(
            stream,
            "HTTP/1.1 200 OK\r\nContent-Type: image/svg+xml\r\nContent-Length: {}\r\nConnection: close\r\n\r\n",
            content.len()
        )?;
        stream.write_all(content)?;
    } else {
        write!(stream, "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")?;
    }
    Ok(())
}

fn resolve_sandbox_dir() -> PathBuf {
    let candidate = PathBuf::from("/data/data/dev.aurorax.qianxian/files");
    if candidate.exists() || std::fs::create_dir_all(&candidate).is_ok() {
        return candidate;
    }
    let tmp = std::env::temp_dir().join("qianxian_sandbox");
    let _ = std::fs::create_dir_all(&tmp);
    tmp
}

script_mod! {
    use mod.prelude.widgets.*
    use mod.widgets.*

    startup() do #(App::script_component(vm)) {
        ui: Root {
            main_window := Window {
                window.title: "牵线 · 聚会筹办守护"
                window.inner_size: vec2(412, 892)
                pass +: { clear_color: #xf7f2ec }
                body +: {
                    padding: 0 margin: 0 spacing: 0 flow: Overlay
                    card := Splash { width: Fill height: Fill }
                }
            }
        }
    }
}

#[derive(Script, ScriptHook)]
pub struct App {
    #[live]
    ui: WidgetRef,
    #[rust]
    card_surface: SplashRef,
    #[rust]
    mounted: bool,
    #[rust]
    asset_server: Option<LocalAssetServer>,
    #[rust]
    service_bridge: Option<Arc<ServiceBridge>>,
    #[rust]
    sandbox_dir: PathBuf,
}

impl App {
    fn mount(&mut self, cx: &mut Cx) {
        let server = LocalAssetServer::start().ok();
        let origin = server.as_ref().map(|s| s.origin.clone()).unwrap_or_else(|| "http://127.0.0.1:8000".to_string());
        self.asset_server = server;

        let backend: Arc<dyn LocalModelBackend> = match LlamaCppBackend::auto_detect() {
            Ok(llama) => {
                log!("牵线 Android: 检测到真实端侧模型: {}", llama.model_name);
                Arc::new(llama)
            }
            Err(_) => {
                log!("牵线 Android: 未检测到本地 GGUF，启用确定性脚本引擎");
                Arc::new(ScriptedMockBackend)
            }
        };
        self.service_bridge = Some(Arc::new(ServiceBridge::new(backend)));

        let sandbox_dir = resolve_sandbox_dir();
        let _ = std::fs::create_dir_all(&sandbox_dir);
        self.sandbox_dir = sandbox_dir.clone();

        let splash = self.card_surface.clone();
        splash.set_sandbox_dir(cx, Some(sandbox_dir));
        splash.set_host_caps(cx, vec![
            "octos.turn.start".to_string(),
            "qianxian.clipboard.read".to_string(),
            "qianxian.notify".to_string(),
        ]);

        let script = MAIN_SPLASH_SRC.replace("{{assets}}", origin.trim_end_matches('/'));
        splash.set_text(cx, &script);

        // 启动时初始化常驻守护通知胶囊
        cx.show_notification(
            "🛡 牵线 · 实时守护中",
            "全流程聚会管家已就绪，实时盯梢聚会异动与天气突变",
        );
    }
}

impl AppMain for App {
    fn script_mod(vm: &mut ScriptVm) -> ScriptValue {
        makepad_widgets::script_mod(vm);
        self::script_mod(vm)
    }

    fn handle_event(&mut self, cx: &mut Cx, event: &Event) {
        if !self.mounted {
            self.card_surface = self.ui.splash(cx, ids!(card));
            self.mounted = true;
            makepad_widgets::widget_async::register_splash_isolate_mod(makepad_widgets::splash::register_agent_module);
            self.mount(cx);
        }

        let requests = makepad_widgets::splash_host::take_splash_host_requests();
        for req in requests {
            if req.service == "octos.turn.start" {
                if let Some(bridge) = &self.service_bridge {
                    let (resp, _metrics) = bridge.handle_turn_start(&req.args_json);
                    if resp.is_ok {
                        if let Some(data) = resp.data {
                            let json = serde_json::json!({ "text": data.text }).to_string();
                            let _ = makepad_widgets::splash_host::splash_host_respond(
                                cx,
                                req.heap_key,
                                req.req_id,
                                Ok(&json),
                            );
                        }
                    } else {
                        let err = resp.error.unwrap_or_else(|| "未知错误".to_string());
                        let _ = makepad_widgets::splash_host::splash_host_respond(
                            cx,
                            req.heap_key,
                            req.req_id,
                            Err(&err),
                        );
                    }
                }
            } else if req.service == "qianxian.clipboard.read" {
                let ext_file = PathBuf::from("/sdcard/Download/qianxian-clipboard.txt");
                let cb_file = self.sandbox_dir.join("clipboard_in.txt");
                let text = if ext_file.exists() {
                    let t = std::fs::read_to_string(&ext_file).unwrap_or_default();
                    let _ = std::fs::remove_file(&ext_file);
                    t
                } else if cb_file.exists() {
                    let t = std::fs::read_to_string(&cb_file).unwrap_or_default();
                    let _ = std::fs::remove_file(&cb_file);
                    t
                } else {
                    String::new()
                };
                let json = serde_json::json!({ "text": text }).to_string();
                let _ = makepad_widgets::splash_host::splash_host_respond(
                    cx,
                    req.heap_key,
                    req.req_id,
                    Ok(&json),
                );
            } else if req.service == "qianxian.notify" {
                if let Ok(v) = serde_json::from_str::<serde_json::Value>(&req.args_json) {
                    let title = v.get("title").and_then(|t| t.as_str()).unwrap_or("牵线 · 守护中");
                    let body = v.get("body").and_then(|b| b.as_str()).unwrap_or("");

                    // 1. 调用 Makepad 原生通知通道触发系统通知
                    cx.show_notification(title, body);

                    // 2. 将当前胶囊实时数据持久化存盘（供外部工具、桌面 Widget 或 ADB 读回断言）
                    let capsule_payload = serde_json::json!({
                        "title": title,
                        "body": body,
                        "updated_at": format!("{:?}", std::time::SystemTime::now()),
                        "ongoing": true,
                        "crisis": v.get("crisis").and_then(|c| c.as_str()).unwrap_or("no"),
                    });
                    let _ = std::fs::write(
                        self.sandbox_dir.join("ongoing_guard.json"),
                        capsule_payload.to_string(),
                    );
                    let _ = std::fs::write(
                        "/sdcard/Download/qianxian-live-capsule.json",
                        capsule_payload.to_string(),
                    );
                }
                let _ = makepad_widgets::splash_host::splash_host_respond(
                    cx,
                    req.heap_key,
                    req.req_id,
                    Ok("{}"),
                );
            }
        }

        self.ui.handle_event(cx, event, &mut Scope::empty());
    }
}
