#!/usr/bin/env python3
"""本地天气网关（宿主侧场外服务）：card-host/Rinx 的 makepad HTTP 后端不吃
https_proxy 环境变量且本机直连 open-meteo 被静默丢包——网关代取并返回极小 JSON。
仅监听 127.0.0.1；上游经用户代理（10808）。真机上无此服务时 app 自动回落直连。
"""
import json
import os
import ssl
import subprocess
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PROXY = "http://127.0.0.1:10808"
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        print("REQ", self.path[:120], flush=True)
        if not self.path.startswith("/wx"):
            self.send_error(404)
            return
        # /wx?url=<open-meteo 完整 URL>
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(self.path).query)
        target = (qs.get("url") or [""])[0]
        if "open-meteo.com" not in target:
            self._json({"ok": False, "error": "host not allowed"})
            return
        try:
            with OPENER.open(target, timeout=20) as r:
                raw = r.read()
                print("UPSTREAM", r.status, len(raw), flush=True)
                data = json.loads(raw.decode())
            self._json({"ok": True, "data": data})
        except Exception as e:
            print("UPSTREAM-ERR", str(e)[:120], flush=True)
            self._json({"ok": False, "error": str(e)})

    def _json(self, v):
        d = json.dumps(v).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(d)))
        self.send_header("connection", "close")
        self.end_headers()
        self.wfile.write(d)
        self.wfile.flush()
        # rustls 客户端严格要求 close_notify——python ssl 需显式 unwrap 发出
        try:
            self.connection.unwrap()
        except Exception:
            pass
        self.close_connection = True


if __name__ == "__main__":
    port = int(os.environ.get("QX_WX_PORT", "8195"))
    # 准入硬规则：脚本内 http:// 一律拒绝 → 网关走 HTTPS（自签名证书，
    # app 侧对应 ignore_ssl_cert: true——仅回环开发网关使用）
    cert = os.path.expanduser("~/.local/qx-wx-gw-cert.pem")
    key = os.path.expanduser("~/.local/qx-wx-gw-key.pem")
    if not (os.path.exists(cert) and os.path.exists(key)):
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
                        "-keyout", key, "-out", cert, "-days", "365",
                        "-subj", "/CN=127.0.0.1"], check=True, capture_output=True)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(cert, key)
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    print(httpd.server_address[1], flush=True)
    httpd.serve_forever()
