-- 004: Multi-tenant dashboard product model expansions
-- Teams, principals, tags, catalog dimensions, audit partition guidance.
-- Apply after 001–003. Safe to run additively.

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;

DO $$ BEGIN
  CREATE TYPE auth_mode_kind AS ENUM (
    'oauth', 'workload_identity', 'mtls', 'api_key', 'none'
  );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE health_status_kind AS ENUM (
    'healthy', 'degraded', 'unhealthy', 'unknown'
  );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE data_classification_kind AS ENUM (
    'public', 'internal', 'confidential', 'regulated', 'phi', 'pci', 'secrets'
  );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS teams (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id        UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  slug          CITEXT NOT NULL,
  name          TEXT NOT NULL,
  escalation_contact TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (org_id, slug)
);

CREATE TABLE IF NOT EXISTS team_members (
  team_id       UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
  actor_id      UUID NOT NULL REFERENCES actors(id) ON DELETE CASCADE,
  role          TEXT NOT NULL DEFAULT 'member',
  PRIMARY KEY (team_id, actor_id)
);

-- Principals = actors with optional IdP subject mapping (already have actors;
-- this view/table adds workload metadata)
CREATE TABLE IF NOT EXISTS principals (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id        UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  actor_id      UUID REFERENCES actors(id) ON DELETE SET NULL,
  subject       TEXT NOT NULL,
  kind          TEXT NOT NULL CHECK (kind IN ('user', 'workload', 'service')),
  email         CITEXT,
  roles         TEXT[] NOT NULL DEFAULT '{}',
  idp_issuer    TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (org_id, subject)
);

CREATE TABLE IF NOT EXISTS connector_tags (
  connector_id  UUID NOT NULL REFERENCES connectors(id) ON DELETE CASCADE,
  tag           CITEXT NOT NULL,
  PRIMARY KEY (connector_id, tag)
);

CREATE TABLE IF NOT EXISTS connector_catalog_meta (
  connector_version_id UUID PRIMARY KEY REFERENCES connector_versions(id) ON DELETE CASCADE,
  auth_mode         TEXT NOT NULL DEFAULT 'oauth',
  transport_detail  TEXT, -- stdio | streamable_http | sse_legacy | gateway_proxy
  data_classification TEXT NOT NULL DEFAULT 'internal',
  source_repository TEXT,
  cert_expires_at   TIMESTAMPTZ,
  last_pentest_at   TIMESTAMPTZ,
  cve_critical_count INT NOT NULL DEFAULT 0,
  cve_high_count    INT NOT NULL DEFAULT 0,
  health_status     TEXT NOT NULL DEFAULT 'unknown',
  success_rate_24h  REAL,
  p95_latency_ms    INT,
  error_rate_24h    REAL,
  approval_denial_rate_24h REAL,
  budget_usage_ratio REAL,
  activity_24h      INT NOT NULL DEFAULT 0,
  data_residency    TEXT,
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS certification_hard_gates (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  connector_version_id UUID NOT NULL REFERENCES connector_versions(id) ON DELETE CASCADE,
  gate_key      TEXT NOT NULL,
  passed        BOOLEAN NOT NULL,
  detail        TEXT,
  checked_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (connector_version_id, gate_key)
);

-- Required hard gates (application enforces; rows document evidence)
COMMENT ON TABLE certification_hard_gates IS
  'Hard fail keys: pinned_digest, owner_present, no_embedded_creds, egress_restricted, tenant_authz, write_tools_require_approval, immutable_audit';

CREATE INDEX IF NOT EXISTS teams_org_idx ON teams (org_id);
CREATE INDEX IF NOT EXISTS principals_org_subject_idx ON principals (org_id, subject);
CREATE INDEX IF NOT EXISTS connector_tags_tag_idx ON connector_tags (tag);
CREATE INDEX IF NOT EXISTS catalog_meta_health_idx ON connector_catalog_meta (health_status);
CREATE INDEX IF NOT EXISTS catalog_meta_cert_exp_idx ON connector_catalog_meta (cert_expires_at);
CREATE INDEX IF NOT EXISTS catalog_meta_activity_idx ON connector_catalog_meta (activity_24h DESC);

ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE principals ENABLE ROW LEVEL SECURITY;
ALTER TABLE connector_catalog_meta ENABLE ROW LEVEL SECURITY;
ALTER TABLE certification_hard_gates ENABLE ROW LEVEL SECURITY;

-- RLS via org membership through parent tables where FK exists.
-- connector_catalog_meta joins connector_versions → connectors (org-scoped in v2 tables).
-- For 001 connectors (global catalog), policies are org-optional; tighten when connectors gain org_id.

CREATE OR REPLACE FUNCTION app_org_id() RETURNS text
LANGUAGE sql STABLE AS $$
  SELECT NULLIF(current_setting('app.org_id', true), '')
$$;

DROP POLICY IF EXISTS teams_org_isolation ON teams;
CREATE POLICY teams_org_isolation ON teams
  USING (org_id::text = app_org_id())
  WITH CHECK (org_id::text = app_org_id());

DROP POLICY IF EXISTS principals_org_isolation ON principals;
CREATE POLICY principals_org_isolation ON principals
  USING (org_id::text = app_org_id())
  WITH CHECK (org_id::text = app_org_id());

-- ---------------------------------------------------------------------------
-- High-volume audit partitioning guidance (run manually in production)
-- ---------------------------------------------------------------------------
-- Example monthly partition parent (illustrative — do not auto-migrate blindly):
--
-- CREATE TABLE tool_invocations_partitioned (
--   LIKE tool_invocations INCLUDING ALL
-- ) PARTITION BY RANGE (occurred_at);
--
-- CREATE TABLE tool_invocations_2026_09 PARTITION OF tool_invocations_partitioned
--   FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');
--
-- Retain hot indexes: (org_id, occurred_at DESC), (correlation_id), (connector_version_id).
-- Archive cold partitions to object storage after retention policy.
