import ssl, json
from http.server import BaseHTTPRequestHandler, HTTPServer
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        d = json.dumps({"ok": True}).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(d)))
        self.send_header("connection", "close")
        self.end_headers()
        self.wfile.write(d); self.wfile.flush()
        try: self.connection.unwrap()
        except Exception: pass
        self.close_connection = True
    def log_message(self, *a): pass
s = HTTPServer(("127.0.0.1", 8195), H)
c = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
c.load_cert_chain("/tmp/ssl-cert.pem", "/tmp/ssl-key.pem")
s.socket = c.wrap_socket(s.socket, server_side=True)
print("listening 8195", flush=True)
s.serve_forever()
