# Developing this OctoSense app

> **Any coding agent, or none.** These instructions work the same for Codex, Claude Code, Cursor, Gemini CLI, GitHub Copilot or a person at a terminal: every step is a shell command or a file edit, and nothing here needs a particular agent, model or vendor. `AGENTS.md` is the one source of truth; `CLAUDE.md` and `GEMINI.md` only import it for agents that look for those names.

This repository is one OctoSense script app. `bundle/` is the app and the only
thing submitted to the App Hub; everything else stays outside it.

Follow the harness, and do not invent requirements or APIs:

- How to build, run and test: [QUICKSTART](https://github.com/OctoSense-org/OctoSense-App-Flow/blob/main/docs/QUICKSTART.md)
- The language and every API an app may use: [SCRIPT-API](https://github.com/OctoSense-org/OctoSense-App-Flow/blob/main/docs/SCRIPT-API.md)
- Capabilities: [CAPABILITIES](https://github.com/OctoSense-org/OctoSense-App-Flow/blob/main/docs/CAPABILITIES.md)
- Publishing, step by step, with the human checkpoints: [PUBLISHING](https://github.com/OctoSense-org/OctoSense-App-Flow/blob/main/docs/PUBLISHING.md)

The loop, with `OCTO=<path to OctoSense-App-Flow>/tools/octo` (the CLI
lives in the harness repository, not here), run from this directory: edit
`bundle-src/` 部件（不是 `bundle/main.splash`——它是 `tools/qx-pack.sh`
的拼接生成物；运行时只认单文件入口，见 app-contract/src/entry.rs）→
`tools/qx-pack.sh` 重新拼接 → `$OCTO run bundle --port 8141 --detach` → drive it
(`/click`, `/t`, `/snap`) and `$OCTO shot 8141 out.png` → `curl -s 127.0.0.1:8141/quit`
→ `$OCTO check bundle`。

Rules:

- Ask only for capabilities a screen uses; declare every `https://` host in
  `network.hosts`; never `http://`.
- Never collect a password, PIN or code; accounts go through a host service.
- Screenshots are real captures you looked at. Never a dummy.
- Restamp after every edit (`tools/octo check` does it). After signing, any
  edit needs a new stamp and signature.
- Keys, `.local-state/`, `build/` and review packets never enter `bundle/` or git.
- Stop at human steps: publisher key, publisher details, platform claims, submission.

This app's own requirements, data sources and tests:

- App: 「牵线」聚会筹办守护 (qianxian) — a group-chat gather-up guardian:
  triage a message into a Case, propose/confirm/reschedule/cancel with
  organizer-only confirm, AA split, honest AI suggestion card (LLM never
  touches the state machine; degraded paths are explicit).
- Data sources: `storage` only (on-device cases.json via host storage) and
  the `octos.turn.start` host service when present; `network.hosts` is empty.
  No facts are invented: fields the model cannot extract stay empty.
- Tests: `python3 app/qianxian/tools/qx-verify-v2.py` against a running
  card-host (14-step regression over the #31 detail/list interaction paths).
  Reproduction steps and version pins: [run.md](run.md); acceptance evidence
  under [evidence/](evidence/).
