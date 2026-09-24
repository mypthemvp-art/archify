-- Gateway runtime persistence (Phase B hardening).
-- Uses TEXT org/tenant/project ids matching AUTH principal claims (not UUID graph).
-- Apply after 001–005 when DATABASE_URL is set:
--   psql "$DATABASE_URL" -f levelupworld/registry/schema/006_gateway_runtime.sql

CREATE OR REPLACE FUNCTION app_org_id() RETURNS text
LANGUAGE sql STABLE AS $$
  SELECT NULLIF(current_setting('app.org_id', true), '')
$$;

CREATE TABLE IF NOT EXISTS gateway_audit_events (
  id                 BIGSERIAL PRIMARY KEY,
  event_hash         TEXT NOT NULL UNIQUE,
  prev_event_hash    TEXT,
  correlation_id     TEXT NOT NULL,
  org_id             TEXT NOT NULL,
  tenant_id          TEXT,
  project_id         TEXT,
  environment        TEXT,
  actor_subject      TEXT NOT NULL,
  connector_slug     TEXT,
  connector_version  TEXT,
  tool_name          TEXT,
  args_hash          TEXT,
  policy_decision    TEXT,
  approval_id        TEXT,
  idempotency_key    TEXT,
  latency_ms         INT,
  outcome            TEXT,
  response_hash      TEXT,
  evidence_uri       TEXT,
  redaction_count    INT NOT NULL DEFAULT 0,
  payload            JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS gateway_audit_events_corr_idx
  ON gateway_audit_events (correlation_id);
CREATE INDEX IF NOT EXISTS gateway_audit_events_org_time_idx
  ON gateway_audit_events (org_id, created_at DESC);
CREATE INDEX IF NOT EXISTS gateway_audit_events_connector_idx
  ON gateway_audit_events (org_id, connector_slug, tool_name);

CREATE TABLE IF NOT EXISTS gateway_approval_requests (
  id                     TEXT PRIMARY KEY,
  status                 TEXT NOT NULL,
  org_id                 TEXT NOT NULL,
  tenant_id              TEXT NOT NULL,
  project_id             TEXT NOT NULL,
  environment            TEXT NOT NULL,
  actor                  TEXT NOT NULL,
  connector_slug         TEXT NOT NULL,
  connector_version      TEXT NOT NULL,
  tool_name              TEXT NOT NULL,
  plan_markdown          TEXT NOT NULL,
  arguments              JSONB NOT NULL,
  args_hash              TEXT NOT NULL,
  idempotency_key        TEXT NOT NULL,
  correlation_id         TEXT NOT NULL,
  required_approver_count INT NOT NULL DEFAULT 1,
  approval_mode          TEXT NOT NULL DEFAULT 'single',
  decisions              JSONB NOT NULL DEFAULT '[]'::jsonb,
  step_up_required       BOOLEAN NOT NULL DEFAULT false,
  grant_id               TEXT,
  grant_jws              TEXT,
  decided_by             TEXT,
  decided_at             TIMESTAMPTZ,
  decision_note          TEXT,
  expires_at             TIMESTAMPTZ NOT NULL,
  created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  consumed_at            TIMESTAMPTZ,
  UNIQUE (org_id, project_id, idempotency_key, args_hash)
);

CREATE TABLE IF NOT EXISTS gateway_approval_grants (
  grant_id               TEXT PRIMARY KEY,
  approval_request_id    TEXT NOT NULL REFERENCES gateway_approval_requests(id) ON DELETE CASCADE,
  org_id                 TEXT NOT NULL,
  grant_jws              TEXT NOT NULL,
  claims                 JSONB NOT NULL,
  consumed_at            TIMESTAMPTZ,
  revoked_at             TIMESTAMPTZ,
  created_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS gateway_approvals_org_status_idx
  ON gateway_approval_requests (org_id, status, expires_at);
CREATE INDEX IF NOT EXISTS gateway_grants_org_idx
  ON gateway_approval_grants (org_id, grant_id);

ALTER TABLE gateway_audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE gateway_approval_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE gateway_approval_grants ENABLE ROW LEVEL SECURITY;
ALTER TABLE gateway_audit_events FORCE ROW LEVEL SECURITY;
ALTER TABLE gateway_approval_requests FORCE ROW LEVEL SECURITY;
ALTER TABLE gateway_approval_grants FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS gateway_audit_org ON gateway_audit_events;
CREATE POLICY gateway_audit_org ON gateway_audit_events
  USING (org_id = app_org_id())
  WITH CHECK (org_id = app_org_id());

DROP POLICY IF EXISTS gateway_approval_org ON gateway_approval_requests;
CREATE POLICY gateway_approval_org ON gateway_approval_requests
  USING (org_id = app_org_id())
  WITH CHECK (org_id = app_org_id());

DROP POLICY IF EXISTS gateway_grant_org ON gateway_approval_grants;
CREATE POLICY gateway_grant_org ON gateway_approval_grants
  USING (org_id = app_org_id())
  WITH CHECK (org_id = app_org_id());

COMMENT ON TABLE gateway_audit_events IS
  'Append-only gateway audit with hash chain; dual-written from AuditStore when DATABASE_URL is set.';
COMMENT ON TABLE gateway_approval_requests IS
  'Approval workflow rows; dual-written from ApprovalService when DATABASE_URL is set.';
