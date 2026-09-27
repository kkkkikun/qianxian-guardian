-- 「牵线」guardian 状态库 — 唯一事实源（blueprint-gpt.md v0.7.1）
-- SQLite：WAL 模式；所有状态变更经白名单动作 + case_revision++ + audit

CREATE TABLE IF NOT EXISTS cases (
  id                  TEXT PRIMARY KEY,
  room_id             TEXT NOT NULL,
  organizer_id        TEXT NOT NULL,
  organizer_source    TEXT NOT NULL DEFAULT 'first_message',
  created_from_msg_id TEXT NOT NULL,
  status              TEXT NOT NULL,
  revision            INTEGER NOT NULL DEFAULT 1,
  timezone            TEXT NOT NULL DEFAULT 'Asia/Shanghai',
  created_at          TEXT NOT NULL
);
-- 每房间至多一个 Active Case（蓝图 v0.7.1 "Active 状态集合"）
CREATE UNIQUE INDEX IF NOT EXISTS idx_one_active_case_per_room
  ON cases(room_id) WHERE status IN (
    'Parsing','Clarifying','Collecting','Proposing','AwaitingConfirm',
    'Confirmed','Armed','Rescheduling','Settling','Unstable');

CREATE TABLE IF NOT EXISTS plans (
  plan_id            TEXT PRIMARY KEY,
  case_id            TEXT NOT NULL REFERENCES cases(id),
  revision           INTEGER NOT NULL,
  start_at           TEXT,
  end_at             TEXT,
  timezone           TEXT NOT NULL DEFAULT 'Asia/Shanghai',
  place              TEXT,
  place_geocode_id   TEXT,
  activity           TEXT,
  members            TEXT,   -- JSON array
  source_proposal_id TEXT,
  status             TEXT NOT NULL DEFAULT 'Active'  -- Active|Superseded
);
CREATE INDEX IF NOT EXISTS idx_plans_case ON plans(case_id, status);

CREATE TABLE IF NOT EXISTS proposals (
  id                 TEXT PRIMARY KEY,
  case_id            TEXT NOT NULL REFERENCES cases(id),
  based_on_revision  INTEGER NOT NULL,
  request_id         TEXT,
  selected_slot_id   TEXT,
  content            TEXT,
  basis_fact_ids     TEXT,   -- JSON array
  claims             TEXT,   -- JSON array
  status             TEXT NOT NULL DEFAULT 'Pending',  -- Pending|Approved|Rejected|Expired|Superseded
  created_at         TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_proposals_case ON proposals(case_id, status);

CREATE TABLE IF NOT EXISTS ledger (
  entry_id      TEXT PRIMARY KEY,
  case_id       TEXT NOT NULL REFERENCES cases(id),
  payer         TEXT NOT NULL,
  amount_cents  INTEGER NOT NULL,
  note          TEXT,
  settled_at    TEXT
);

CREATE TABLE IF NOT EXISTS scheduled_tasks (
  id          TEXT PRIMARY KEY,
  case_id     TEXT NOT NULL REFERENCES cases(id),
  kind        TEXT NOT NULL,   -- reminder|weather_check|case_deadline|activity_end
  due_at      TEXT NOT NULL,
  status      TEXT NOT NULL DEFAULT 'Pending',  -- Pending|Claimed|Running|Completed|Cancelled|NeedsRecovery
  txn_id      TEXT,
  created_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sched_due ON scheduled_tasks(status, due_at);

CREATE TABLE IF NOT EXISTS case_events (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  case_id          TEXT,           -- Case 诞生前的事件为 NULL
  matrix_event_id  TEXT NOT NULL,
  revision         INTEGER,
  type             TEXT NOT NULL,
  actor            TEXT NOT NULL,
  created_at       TEXT NOT NULL,
  evidence_ref     TEXT
);

CREATE TABLE IF NOT EXISTS outbox (
  id          TEXT PRIMARY KEY,
  case_id     TEXT,
  txn_id      TEXT NOT NULL UNIQUE,
  kind        TEXT NOT NULL,     -- M1|M2|M3
  room_id     TEXT NOT NULL,
  text        TEXT NOT NULL,
  status      TEXT NOT NULL DEFAULT 'Pending',  -- Pending|Sent|UNKNOWN|NEED_RECONCILIATION|Cancelled
  grant_ref   TEXT,
  created_at  TEXT NOT NULL,
  updated_at  TEXT
);

CREATE TABLE IF NOT EXISTS ingress_state (
  key   TEXT PRIMARY KEY,
  value TEXT
);

CREATE TABLE IF NOT EXISTS processed_events (
  event_id     TEXT PRIMARY KEY,
  room_id      TEXT NOT NULL,
  sender       TEXT,
  type         TEXT,
  processed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  ts           TEXT NOT NULL,
  actor        TEXT NOT NULL,
  action       TEXT NOT NULL,
  evidence_ref TEXT
);

-- G4b：外发授权（M3 需要；MVP 授权人 = 组织者）
CREATE TABLE IF NOT EXISTS grants (
  id         TEXT PRIMARY KEY,
  case_id    TEXT NOT NULL REFERENCES cases(id),
  room_id    TEXT NOT NULL,
  kind       TEXT NOT NULL,          -- reminder|settle|outreach
  mode       TEXT NOT NULL,          -- once|standing
  expiry     TEXT,
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL
);
