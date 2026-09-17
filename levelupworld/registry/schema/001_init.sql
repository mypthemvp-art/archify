-- MCP Registry + Gateway schema (Postgres)
-- Week 1 foundation: catalog, versions, certifications, approvals, audit, budgets
-- Enable RLS in deploying environments; policies are illustrative.

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;

CREATE TYPE trust_tier AS ENUM (
  'unverified', 'sandboxed', 'reviewed', 'certified', 'production_critical'
);

CREATE TYPE capability_kind AS ENUM ('read', 'write', 'delete', 'external_communication');

CREATE TYPE transport_kind AS ENUM ('stdio', 'streamable_http', 'sse_legacy');

CREATE TYPE environment_kind AS ENUM ('development', 'staging', 'production');

CREATE TYPE certification_state AS ENUM (
  'draft', 'in_lab', 'failed', 'certified', 'quarantined', 'deprecated'
);

CREATE TYPE policy_decision AS ENUM ('allow', 'deny', 'require_approval', 'error');

CREATE TYPE approval_status AS ENUM (
  'pending', 'approved', 'denied', 'expired', 'consumed', 'revoked'
);

CREATE TABLE organizations (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug          CITEXT UNIQUE NOT NULL,
  name          TEXT NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE tenants (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id        UUID NOT NULL REFERENCES organizations(id),
  slug          CITEXT NOT NULL,
  name          TEXT NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (org_id, slug)
);

CREATE TABLE projects (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id     UUID NOT NULL REFERENCES tenants(id),
  slug          CITEXT NOT NULL,
  name          TEXT NOT NULL,
  environments  environment_kind[] NOT NULL DEFAULT ARRAY['development']::environment_kind[],
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, slug)
);

CREATE TABLE actors (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id        UUID NOT NULL REFERENCES organizations(id),
  subject       TEXT NOT NULL, -- user: or workload:
  email         CITEXT,
  display_name  TEXT,
  roles         TEXT[] NOT NULL DEFAULT '{}',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (org_id, subject)
);

CREATE TABLE connectors (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug               CITEXT UNIQUE NOT NULL,
  display_name       TEXT NOT NULL,
  category           TEXT NOT NULL,
  description        TEXT NOT NULL,
  owner_team         TEXT NOT NULL,
  escalation_contact TEXT NOT NULL,
  default_trust_tier trust_tier NOT NULL DEFAULT 'unverified',
  data_classification TEXT NOT NULL DEFAULT 'internal',
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE connector_versions (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  connector_id       UUID NOT NULL REFERENCES connectors(id) ON DELETE CASCADE,
  version            TEXT NOT NULL,              -- semver
  image_digest       TEXT,                       -- sha256:...
  transport          transport_kind NOT NULL,
  manifest_uri       TEXT,
  sbom_uri           TEXT,
  signature_uri      TEXT,
  oauth_scopes       TEXT[] NOT NULL DEFAULT '{}',
  outbound_domains   TEXT[] NOT NULL DEFAULT '{}',
  allowed_environments environment_kind[] NOT NULL DEFAULT ARRAY['development','staging']::environment_kind[],
  read_tool_count    INT NOT NULL DEFAULT 0,
  write_tool_count   INT NOT NULL DEFAULT 0,
  delete_tool_count  INT NOT NULL DEFAULT 0,
  certification_state certification_state NOT NULL DEFAULT 'draft',
  security_review_at TIMESTAMPTZ,
  certified_at       TIMESTAMPTZ,
  quarantined_at     TIMESTAMPTZ,
  quarantine_reason  TEXT,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (connector_id, version)
);

CREATE TABLE connector_tools (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  connector_version_id UUID NOT NULL REFERENCES connector_versions(id) ON DELETE CASCADE,
  tool_name          TEXT NOT NULL,
  capability         capability_kind NOT NULL,
  description        TEXT NOT NULL,
  input_schema       JSONB NOT NULL,
  risk_level         TEXT NOT NULL DEFAULT 'low', -- low|medium|high
  requires_approval  BOOLEAN NOT NULL DEFAULT false,
  UNIQUE (connector_version_id, tool_name)
);

CREATE TABLE project_connector_activations (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id         UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  connector_version_id UUID NOT NULL REFERENCES connector_versions(id),
  environment        environment_kind NOT NULL,
  active             BOOLEAN NOT NULL DEFAULT true,
  pinned             BOOLEAN NOT NULL DEFAULT true,
  activated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (project_id, connector_version_id, environment)
);

CREATE TABLE certification_runs (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  connector_version_id UUID NOT NULL REFERENCES connector_versions(id) ON DELETE CASCADE,
  suite              TEXT NOT NULL,
  status             TEXT NOT NULL, -- passed|failed|running
  report_uri         TEXT,
  started_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at        TIMESTAMPTZ,
  summary            JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE approval_requests (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id             UUID NOT NULL REFERENCES organizations(id),
  tenant_id          UUID NOT NULL REFERENCES tenants(id),
  project_id         UUID NOT NULL REFERENCES projects(id),
  environment        environment_kind NOT NULL,
  actor_id           UUID NOT NULL REFERENCES actors(id),
  connector_slug     TEXT NOT NULL,
  connector_version  TEXT NOT NULL,
  tool_name          TEXT NOT NULL,
  plan_markdown      TEXT NOT NULL,
  arguments          JSONB NOT NULL,
  args_hash          TEXT NOT NULL,
  idempotency_key    TEXT NOT NULL,
  status             approval_status NOT NULL DEFAULT 'pending',
  correlation_id     UUID NOT NULL,
  decided_by         UUID REFERENCES actors(id),
  decided_at         TIMESTAMPTZ,
  expires_at         TIMESTAMPTZ NOT NULL,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (project_id, idempotency_key, args_hash)
);

CREATE TABLE approval_grants (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  approval_request_id UUID NOT NULL REFERENCES approval_requests(id) ON DELETE CASCADE,
  grant_jws          TEXT NOT NULL,
  grant_id           TEXT NOT NULL UNIQUE,
  args_hash          TEXT NOT NULL,
  expires_at         TIMESTAMPTZ NOT NULL,
  consumed_at        TIMESTAMPTZ,
  revoked_at         TIMESTAMPTZ,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE audit_events (
  id                 BIGSERIAL PRIMARY KEY,
  event_hash         TEXT NOT NULL,              -- hash of this event payload
  prev_event_hash    TEXT,                       -- hash chain
  correlation_id     UUID NOT NULL,
  org_id             UUID,
  tenant_id          UUID,
  project_id         UUID,
  environment        environment_kind,
  actor_subject      TEXT NOT NULL,
  connector_slug     TEXT,
  connector_version  TEXT,
  tool_name          TEXT,
  args_hash          TEXT,
  policy_decision    policy_decision NOT NULL,
  approval_id        UUID,
  idempotency_key    TEXT,
  latency_ms         INT,
  outcome            TEXT,
  response_hash      TEXT,
  evidence_uri       TEXT,
  redaction_count    INT NOT NULL DEFAULT 0,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX audit_events_correlation_idx ON audit_events (correlation_id);
CREATE INDEX audit_events_created_idx ON audit_events (created_at DESC);
CREATE INDEX audit_events_connector_idx ON audit_events (connector_slug, tool_name);

CREATE TABLE budget_ledgers (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id             UUID NOT NULL,
  org_id             UUID NOT NULL,
  tenant_id          UUID NOT NULL,
  project_id         UUID NOT NULL,
  tool_calls         INT NOT NULL DEFAULT 0,
  tokens_in          BIGINT NOT NULL DEFAULT 0,
  tokens_out         BIGINT NOT NULL DEFAULT 0,
  cost_micros        BIGINT NOT NULL DEFAULT 0,
  duration_ms        INT NOT NULL DEFAULT 0,
  max_tools          INT NOT NULL DEFAULT 20,
  max_duration_ms    INT NOT NULL DEFAULT 900000,
  max_cost_micros    BIGINT NOT NULL DEFAULT 5000000,
  breached           BOOLEAN NOT NULL DEFAULT false,
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (run_id)
);

CREATE TABLE connector_health (
  connector_version_id UUID PRIMARY KEY REFERENCES connector_versions(id) ON DELETE CASCADE,
  success_rate_24h   NUMERIC(5,4),
  p95_latency_ms     INT,
  error_rate_24h     NUMERIC(5,4),
  policy_denial_rate_24h NUMERIC(5,4),
  last_health_at     TIMESTAMPTZ,
  healthy            BOOLEAN NOT NULL DEFAULT false,
  details            JSONB NOT NULL DEFAULT '{}'::jsonb
);

-- Illustrative RLS
ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE approval_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_connector_activations ENABLE ROW LEVEL SECURITY;
