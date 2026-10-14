// 探针：ignore_ssl_cert 字段是否真实贯通到后端
use makepad_script_std::makepad_network::{
    EventSink, HttpRequest, HttpResponse, NetworkBackend, NetworkResponse, NetworkRuntime, WsSend,
};
use makepad_script_std::makepad_script::{makepad_live_id::LiveId, script, *};
use makepad_script_std::{script_mod, with_vm, ScriptStd};
use std::sync::{Arc, Mutex};

struct CaptureBackend { seen: Mutex<Option<bool>> }
impl NetworkBackend for CaptureBackend {
    fn http_start(&self, _id: LiveId, r: HttpRequest, s: EventSink) -> Result<(), makepad_script_std::makepad_network::NetworkError> {
        *self.seen.lock().unwrap() = Some(r.ignore_ssl_cert);
        s.emit(NetworkResponse::HttpResponse { request_id: _id, response: HttpResponse::new(LiveId(42), 200, Default::default(), Some(b"ok".to_vec())) })
    }
    fn http_cancel(&self, _id: LiveId) -> Result<(), makepad_script_std::makepad_network::NetworkError> { Ok(()) }
    fn ws_open(&self, _id: LiveId, _r: HttpRequest, _s: EventSink) -> Result<(), makepad_script_std::makepad_network::NetworkError> { Ok(()) }
    fn ws_send(&self, _id: LiveId, _m: WsSend) -> Result<(), makepad_script_std::makepad_network::NetworkError> { Ok(()) }
    fn ws_close(&self, _id: LiveId) -> Result<(), makepad_script_std::makepad_network::NetworkError> { Ok(()) }
}

#[test]
fn probe_ignore_ssl_cert_roundtrip() {
    let backend = Arc::new(CaptureBackend { seen: Mutex::new(None) });
    let runtime = Arc::new(NetworkRuntime::with_backend(backend.clone()));
    let mut host = ScriptVmHost::new((), ScriptStd::with_network_runtime(runtime));
    host.script_vm = Some(Box::new(ScriptVmBase::new()));
    with_vm(&mut host, |vm| {
        script_mod(vm);
        let v = vm.eval(script! {
            use mod.std
            use mod.net
            let p = std.promise()
            let req = net.HttpRequest{
                url: "https://example.com"
                method: net.HttpMethod.GET
                ignore_ssl_cert: true
            }
            net.http_request(req) do net.HttpEvents{
                on_response: |res| p.resolve(res.status_code)
                on_error: |_err| p.resolve(-1)
            }
            p
        });
        assert!(!v.is_err(), "script failed: {:?}", v);
    });
    // 驱动网络运行时泵
    makepad_script_std::pump_network_runtime(&mut host);
    let seen = *backend.seen.lock().unwrap();
    assert_eq!(seen, Some(true), "ignore_ssl_cert 未贯通到后端: {:?}", seen);
}
