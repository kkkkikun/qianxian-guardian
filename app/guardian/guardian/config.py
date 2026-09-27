"""guardian 配置加载。config.json 不入库（含 bot 凭据）。"""
import json
import os
from pathlib import Path

DEFAULTS = {
    "homeserver": "http://127.0.0.1:8128",
    "bot_user_id": "@guardian_bot:127.0.0.1:8128",
    "bot_password": "",
    "db_path": str(Path(__file__).resolve().parents[2] / "guardian.db"),
    "timezone": "Asia/Shanghai",
    "poll_timeout_ms": 30000,
}


def load(path: str | None = None) -> dict:
    cfg_path = path or os.environ.get(
        "GUARDIAN_CONFIG",
        str(Path(__file__).resolve().parents[1] / "config.json"),
    )
    cfg = dict(DEFAULTS)
    if os.path.exists(cfg_path):
        with open(cfg_path, encoding="utf-8") as f:
            cfg.update(json.load(f))
    for key in ("homeserver", "bot_user_id", "bot_password", "db_path"):
        if not cfg.get(key):
            raise SystemExit(f"config 缺少必填项: {key} (config: {cfg_path})")
    return cfg
