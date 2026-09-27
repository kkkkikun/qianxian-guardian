"""Matrix Client-Server API 最小封装（login / sync / send）。
出站幂等：send_message 的 txn_id 由调用方提供（蓝图：同 txn_id 重试不产生第二条消息）。
Token 缓存：access token 持久化到本地文件，重启不重新 login（Palpo 登录限流很严）。"""
import secrets
import time
from pathlib import Path

import requests


class MatrixClient:
    def __init__(self, homeserver: str, user_id: str, password: str,
                 token_path: str | None = None):
        self.hs = homeserver.rstrip("/")
        self.user_id = user_id
        self.password = password
        self.token_path = Path(token_path) if token_path else None
        self.token: str | None = None
        self._txn_counter = 0

    # ---- auth（token 优先，429 退避） ----
    def login(self) -> None:
        if self.token_path and self.token_path.exists():
            token = self.token_path.read_text(encoding="utf-8").strip()
            if token and self._whoami(token):
                self.token = token
                return
        self._login_with_retry()
        if self.token_path:
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            self.token_path.write_text(self.token, encoding="utf-8")

    def _login_with_retry(self, max_attempts: int = 5) -> None:
        for attempt in range(max_attempts):
            st, body = self._req("POST", "/_matrix/client/v3/login", {
                "type": "m.login.password",
                "identifier": {"type": "m.id.user", "user": self.user_id},
                "password": self.password,
            }, _no_auth=True, _retry_429=True)
            if st == 200:
                self.token = body["access_token"]
                return
            retry_ms = (body or {}).get("retry_after_ms")
            if st == 429 and retry_ms and attempt < max_attempts - 1:
                wait = min(retry_ms / 1000 + 1, 300)
                print(f"[matrix] login 429, wait {wait:.0f}s (attempt {attempt+1})")
                time.sleep(wait)
                continue
            raise RuntimeError(f"login failed: HTTP {st} {body}")
        raise RuntimeError("login: retries exhausted")

    def _whoami(self, token: str) -> bool:
        try:
            resp = requests.get(f"{self.hs}/_matrix/client/v3/account/whoami",
                                headers={"Authorization": f"Bearer {token}"}, timeout=10)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    # ---- sync（长轮询） ----
    def sync(self, since: str | None = None, timeout_ms: int = 30000) -> dict:
        params = {"timeout": str(timeout_ms)}
        if since:
            params["since"] = since
        st, body = self._req("GET", "/_matrix/client/v3/sync", params=params)
        if st != 200:
            raise RuntimeError(f"sync failed: HTTP {st} {body}")
        return body

    # ---- 出站（txn 幂等） ----
    def send_message(self, room_id: str, text: str, txn_id: str | None = None) -> str:
        if not self.token:
            raise RuntimeError("not logged in")
        txn = txn_id or self._next_txn()
        st, body = self._req(
            "PUT",
            f"/_matrix/client/v3/rooms/{room_id}/send/m.room.message/{txn}",
            {"msgtype": "m.text", "body": text},
        )
        if st != 200:
            raise RuntimeError(f"send failed: HTTP {st} {body} (txn={txn}，可原样重试)")
        return txn

    def send_message_with_retry(self, room_id: str, text: str, txn_id: str,
                                attempts: int = 3) -> str:
        """Outbox 对账语义：UNKNOWN 时用同一 txn_id 重试。"""
        last_err = None
        for _ in range(attempts):
            try:
                return self.send_message(room_id, text, txn_id=txn_id)
            except RuntimeError as e:
                last_err = e
                time.sleep(1)
        raise RuntimeError(f"send 仍不确定（txn={txn_id}）: {last_err}")

    # ---- internal ----
    def _next_txn(self) -> str:
        self._txn_counter += 1
        return f"guardian-{self.user_id}-{int(time.time()*1000)}-{self._txn_counter}-{secrets.token_hex(4)}"

    def _req(self, method: str, path: str, body: dict | None = None,
             params: dict | None = None, _no_auth: bool = False,
             _retry_429: bool = False, _attempt: int = 0):
        headers = {"Content-Type": "application/json"}
        if self.token and not _no_auth:
            headers["Authorization"] = f"Bearer {self.token}"
        url = f"{self.hs}{path}"
        try:
            poll = int((params or {}).get("timeout", 0))
        except (TypeError, ValueError):
            poll = 0
        resp = requests.request(method, url, json=body, params=params,
                                headers=headers, timeout=max(35, poll / 1000 + 10),
                                proxies={"http": None, "https": None})
        if _retry_429 and resp.status_code == 429 and _attempt < 5:
            try:
                retry_ms = resp.json().get("retry_after_ms", 3000)
            except ValueError:
                retry_ms = 3000
            time.sleep(min(retry_ms / 1000 + 1, 300))
            return self._req(method, path, body, params, _no_auth, _retry_429, _attempt + 1)
        try:
            return resp.status_code, resp.json()
        except ValueError:
            return resp.status_code, {"raw": resp.text[:500]}
