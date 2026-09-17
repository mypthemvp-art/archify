-- 005: Full Interactive MCP Registry Dashboard product model (target DDL)
-- Source: docs/INTERACTIVE-MCP-REGISTRY-DASHBOARD.md §4
-- Greenfield / migration target. Current scaffold remains 001–004.
-- Apply in a dedicated database or after mapping legacy tables.

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;

DO $$ BEGIN CREATE TYPE connector_lifecycle AS ENUM (
  'draft', 'active', 'deprecated', 'revoked', 'quarantined'
); EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE certification_status AS ENUM (
  'unverified', 'sandboxed', 'review_pending', 'reviewed',
  'certified', 'production_critical', 'expired', 'failed', 'quarantined'
); EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE operation_class AS ENUM (
  'read', 'write', 'delete', 'external_communication', 'exec'
); EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE risk_level AS ENUM ('low', 'medium', 'high', 'critical');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE transport_type AS ENUM (
  'stdio', 'streamable_http', 'http_sse_legacy', 'gateway_proxy'
); EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE test_run_status AS ENUM (
  'queued', 'provisioning', 'running', 'passed', 'failed', 'cancelled', 'error'
); EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE approval_status_full AS ENUM (
  'pending', 'approved', 'denied', 'expired', 'consumed', 'cancelled'
); EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE invocation_status AS ENUM (
  'started', 'succeeded', 'failed', 'denied', 'timed_out', 'redacted', 'blocked'
); EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN CREATE TYPE environment_name AS ENUM (
  'local', 'development', 'staging', 'production'
); EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Tenant / identity
CREATE TABLE IF NOT EXISTS organizations_v5 (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug citext NOT NULL UNIQUE,
  display_name text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS teams_v5 (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES organizations_v5(id) ON DELETE CASCADE,
  slug citext NOT NULL,
  display_name text NOT NULL,
  escalation_email citext,
  UNIQUE (org_id, slug)
);

CREATE TABLE IF NOT EXISTS principals_v5 (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES organizations_v5(id) ON DELETE CASCADE,
  subject text NOT NULL,
  principal_type text NOT NULL CHECK (principal_type IN ('human', 'service', 'workload')),
  email citext,
  display_name text,
  active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (org_id, subject)
);

CREATE TABLE IF NOT EXISTS projects_v5 (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES organizations_v5(id) ON DELETE CASCADE,
  slug citext NOT NULL,
  display_name text NOT NULL,
  repository_url text,
  data_classification text NOT NULL DEFAULT 'internal',
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (org_id, slug)
);

CREATE TABLE IF NOT EXISTS project_memberships (
  project_id uuid NOT NULL REFERENCES projects_v5(id) ON DELETE CASCADE,
  principal_id uuid NOT NULL REFERENCES principals_v5(id) ON DELETE CASCADE,
  role text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (project_id, principal_id, role)
);

-- Registry
CREATE TABLE IF NOT EXISTS connectors_v5 (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES organizations_v5(id) ON DELETE CASCADE,
  slug citext NOT NULL,
  display_name text NOT NULL,
  description text NOT NULL,
  category text NOT NULL,
  owner_team_id uuid REFERENCES teams_v5(id),
  lifecycle connector_lifecycle NOT NULL DEFAULT 'draft',
  source_repository_url text,
  source_license text,
  homepage_url text,
  created_by uuid REFERENCES principals_v5(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (org_id, slug)
);

CREATE TABLE IF NOT EXISTS connector_versions_v5 (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  connector_id uuid NOT NULL REFERENCES connectors_v5(id) ON DELETE CASCADE,
  version text NOT NULL,
  manifest jsonb NOT NULL,
  manifest_sha256 text NOT NULL,
  source_commit_sha text,
  image_ref text,
  image_digest text,
  sbom_uri text,
  provenance_uri text,
  signature_uri text,
  transport transport_type NOT NULL,
  endpoint_template text,
  auth_mode text NOT NULL,
  requested_scopes jsonb NOT NULL DEFAULT '[]'::jsonb,
  outbound_domains jsonb NOT NULL DEFAULT '[]'::jsonb,
  data_classifications jsonb NOT NULL DEFAULT '[]'::jsonb,
  trust_tier smallint NOT NULL CHECK (trust_tier BETWEEN 0 AND 4),
  certification certification_status NOT NULL DEFAULT 'unverified',
  certification_expires_at timestamptz,
  published_at timestamptz NOT NULL DEFAULT now(),
  deprecated_at timestamptz,
  UNIQUE (connector_id, version),
  UNIQUE (connector_id, manifest_sha256)
);

CREATE TABLE IF NOT EXISTS connector_tools (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  connector_version_id uuid NOT NULL REFERENCES connector_versions_v5(id) ON DELETE CASCADE,
  tool_name text NOT NULL,
  display_name text,
  description text NOT NULL,
  operation operation_class NOT NULL,
  risk risk_level NOT NULL,
  policy_key text NOT NULL,
  input_schema jsonb NOT NULL,
  output_schema jsonb,
  resource_selectors jsonb NOT NULL DEFAULT '[]'::jsonb,
  required_scopes jsonb NOT NULL DEFAULT '[]'::jsonb,
  approval_required boolean NOT NULL DEFAULT false,
  approval_mode text NOT NULL DEFAULT 'none'
    CHECK (approval_mode IN ('none', 'single', 'dual', 'change_ticket')),
  idempotency_required boolean NOT NULL DEFAULT false,
  timeout_seconds integer NOT NULL DEFAULT 30 CHECK (timeout_seconds BETWEEN 1 AND 900),
  max_response_bytes integer NOT NULL DEFAULT 1048576 CHECK (max_response_bytes BETWEEN 1024 AND 10485760),
  max_calls_per_run integer NOT NULL DEFAULT 20 CHECK (max_calls_per_run BETWEEN 1 AND 1000),
  enabled boolean NOT NULL DEFAULT true,
  UNIQUE (connector_version_id, tool_name)
);

CREATE TABLE IF NOT EXISTS connector_environment_eligibility (
  connector_version_id uuid NOT NULL REFERENCES connector_versions_v5(id) ON DELETE CASCADE,
  environment environment_name NOT NULL,
  eligible boolean NOT NULL DEFAULT false,
  reason text,
  PRIMARY KEY (connector_version_id, environment)
);

CREATE TABLE IF NOT EXISTS connector_activations_v5 (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES organizations_v5(id) ON DELETE CASCADE,
  project_id uuid NOT NULL REFERENCES projects_v5(id) ON DELETE CASCADE,
  connector_version_id uuid NOT NULL REFERENCES connector_versions_v5(id) ON DELETE CASCADE,
  environment environment_name NOT NULL,
  enabled boolean NOT NULL DEFAULT false,
  activation_status text NOT NULL CHECK (activation_status IN (
    'requested', 'approved', 'active', 'disabled', 'expired', 'rejected'
  )),
  requested_by uuid REFERENCES principals_v5(id),
  approved_by uuid REFERENCES principals_v5(id),
  approved_at timestamptz,
  expires_at timestamptz,
  policy_overrides jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (project_id, connector_version_id, environment)
);

CREATE INDEX IF NOT EXISTS connector_versions_v5_cert_idx
  ON connector_versions_v5 (certification, certification_expires_at);
CREATE INDEX IF NOT EXISTS connector_tools_operation_idx
  ON connector_tools (operation, risk, approval_required);
CREATE INDEX IF NOT EXISTS connector_activations_v5_lookup_idx
  ON connector_activations_v5 (project_id, environment, enabled, activation_status);

-- Assurance
CREATE TABLE IF NOT EXISTS security_test_suites (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES organizations_v5(id) ON DELETE CASCADE,
  slug citext NOT NULL,
  display_name text NOT NULL,
  version text NOT NULL,
  category text NOT NULL,
  definition jsonb NOT NULL,
  required_for_tier smallint NOT NULL DEFAULT 1 CHECK (required_for_tier BETWEEN 0 AND 4),
  active boolean NOT NULL DEFAULT true,
  UNIQUE (org_id, slug, version)
);

CREATE TABLE IF NOT EXISTS security_test_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES organizations_v5(id) ON DELETE CASCADE,
  connector_version_id uuid NOT NULL REFERENCES connector_versions_v5(id) ON DELETE CASCADE,
  suite_id uuid REFERENCES security_test_suites(id),
  requested_by uuid REFERENCES principals_v5(id),
  status test_run_status NOT NULL DEFAULT 'queued',
  sandbox_ref text,
  started_at timestamptz,
  completed_at timestamptz,
  summary jsonb NOT NULL DEFAULT '{}'::jsonb,
  evidence_uri text,
  result_sha256 text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS security_test_results (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  test_run_id uuid NOT NULL REFERENCES security_test_runs(id) ON DELETE CASCADE,
  test_id text NOT NULL,
  family text NOT NULL,
  severity risk_level,
  status text NOT NULL CHECK (status IN ('passed', 'failed', 'skipped', 'error')),
  details jsonb NOT NULL DEFAULT '{}'::jsonb,
  evidence_uri text,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (test_run_id, test_id)
);

CREATE TABLE IF NOT EXISTS certification_decisions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  connector_version_id uuid NOT NULL REFERENCES connector_versions_v5(id) ON DELETE CASCADE,
  decision certification_status NOT NULL,
  decided_by uuid REFERENCES principals_v5(id),
  rationale text NOT NULL,
  expires_at timestamptz,
  evidence jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS policy_versions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES organizations_v5(id) ON DELETE CASCADE,
  policy_key text NOT NULL,
  version text NOT NULL,
  engine text NOT NULL CHECK (engine IN ('opa', 'cedar', 'custom')),
  policy_document text NOT NULL,
  checksum text NOT NULL,
  active boolean NOT NULL DEFAULT false,
  created_by uuid REFERENCES principals_v5(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (org_id, policy_key, version)
);

CREATE TABLE IF NOT EXISTS policy_decisions_v5 (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  correlation_id uuid NOT NULL,
  org_id uuid NOT NULL REFERENCES organizations_v5(id) ON DELETE CASCADE,
  project_id uuid REFERENCES projects_v5(id),
  principal_id uuid REFERENCES principals_v5(id),
  connector_version_id uuid REFERENCES connector_versions_v5(id),
  tool_id uuid REFERENCES connector_tools(id),
  policy_version_id uuid REFERENCES policy_versions(id),
  input_hash text NOT NULL,
  decision text NOT NULL CHECK (decision IN ('allow', 'deny', 'approval_required', 'error')),
  reasons jsonb NOT NULL DEFAULT '[]'::jsonb,
  obligations jsonb NOT NULL DEFAULT '[]'::jsonb,
  decided_at timestamptz NOT NULL DEFAULT now()
);

-- Approvals + invocations
CREATE TABLE IF NOT EXISTS approval_requests_v5 (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES organizations_v5(id) ON DELETE CASCADE,
  correlation_id uuid NOT NULL,
  project_id uuid NOT NULL REFERENCES projects_v5(id),
  tenant_id text,
  requested_by uuid NOT NULL REFERENCES principals_v5(id),
  connector_version_id uuid NOT NULL REFERENCES connector_versions_v5(id),
  tool_id uuid NOT NULL REFERENCES connector_tools(id),
  environment environment_name NOT NULL,
  normalized_arguments jsonb NOT NULL,
  args_hash text NOT NULL,
  plan jsonb NOT NULL DEFAULT '{}'::jsonb,
  risk risk_level NOT NULL,
  approval_mode text NOT NULL,
  status approval_status_full NOT NULL DEFAULT 'pending',
  idempotency_key text NOT NULL,
  required_approver_count smallint NOT NULL DEFAULT 1,
  policy_version text,
  expires_at timestamptz NOT NULL,
  consumed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (org_id, correlation_id, args_hash)
);

CREATE TABLE IF NOT EXISTS approval_decisions_v5 (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  approval_request_id uuid NOT NULL REFERENCES approval_requests_v5(id) ON DELETE CASCADE,
  approver_id uuid NOT NULL REFERENCES principals_v5(id),
  decision text NOT NULL CHECK (decision IN ('approved', 'denied')),
  rationale text,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (approval_request_id, approver_id)
);

CREATE TABLE IF NOT EXISTS tool_invocations_v5 (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  correlation_id uuid NOT NULL,
  org_id uuid NOT NULL REFERENCES organizations_v5(id) ON DELETE CASCADE,
  project_id uuid REFERENCES projects_v5(id),
  tenant_id text,
  principal_id uuid REFERENCES principals_v5(id),
  connector_version_id uuid NOT NULL REFERENCES connector_versions_v5(id),
  tool_id uuid REFERENCES connector_tools(id),
  environment environment_name NOT NULL,
  args_hash text NOT NULL,
  approval_request_id uuid REFERENCES approval_requests_v5(id),
  policy_decision_id uuid REFERENCES policy_decisions_v5(id),
  status invocation_status NOT NULL,
  started_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz,
  latency_ms integer,
  request_bytes integer,
  response_bytes integer,
  response_hash text,
  redaction_count integer NOT NULL DEFAULT 0,
  error_code text,
  error_class text,
  trace_id text,
  evidence_uri text
);

CREATE TABLE IF NOT EXISTS connector_health_checks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  connector_version_id uuid NOT NULL REFERENCES connector_versions_v5(id) ON DELETE CASCADE,
  status text NOT NULL CHECK (status IN ('healthy', 'degraded', 'failing', 'unknown')),
  latency_ms integer,
  details jsonb NOT NULL DEFAULT '{}'::jsonb,
  checked_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS connector_quarantines_v5 (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  connector_version_id uuid NOT NULL REFERENCES connector_versions_v5(id) ON DELETE CASCADE,
  scope text NOT NULL CHECK (scope IN ('global', 'organization', 'project', 'environment')),
  scope_ref text,
  reason text NOT NULL,
  created_by uuid REFERENCES principals_v5(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  lifted_by uuid REFERENCES principals_v5(id),
  lifted_at timestamptz
);

CREATE INDEX IF NOT EXISTS tool_invocations_v5_time_idx ON tool_invocations_v5 (org_id, started_at DESC);
CREATE INDEX IF NOT EXISTS tool_invocations_v5_connector_idx ON tool_invocations_v5 (connector_version_id, started_at DESC);
CREATE INDEX IF NOT EXISTS tool_invocations_v5_corr_idx ON tool_invocations_v5 (correlation_id);
CREATE INDEX IF NOT EXISTS approvals_v5_pending_idx ON approval_requests_v5 (org_id, status, expires_at);

-- RLS
ALTER TABLE connectors_v5 ENABLE ROW LEVEL SECURITY;
ALTER TABLE connector_versions_v5 ENABLE ROW LEVEL SECURITY;
ALTER TABLE connector_activations_v5 ENABLE ROW LEVEL SECURITY;
ALTER TABLE security_test_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE approval_requests_v5 ENABLE ROW LEVEL SECURITY;
ALTER TABLE tool_invocations_v5 ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS org_connectors_v5_policy ON connectors_v5;
CREATE POLICY org_connectors_v5_policy ON connectors_v5
  USING (org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)
  WITH CHECK (org_id = NULLIF(current_setting('app.org_id', true), '')::uuid);

DROP POLICY IF EXISTS org_activations_v5_policy ON connector_activations_v5;
CREATE POLICY org_activations_v5_policy ON connector_activations_v5
  USING (org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)
  WITH CHECK (org_id = NULLIF(current_setting('app.org_id', true), '')::uuid);

DROP POLICY IF EXISTS org_test_runs_v5_policy ON security_test_runs;
CREATE POLICY org_test_runs_v5_policy ON security_test_runs
  USING (org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)
  WITH CHECK (org_id = NULLIF(current_setting('app.org_id', true), '')::uuid);

DROP POLICY IF EXISTS org_approval_v5_policy ON approval_requests_v5;
CREATE POLICY org_approval_v5_policy ON approval_requests_v5
  USING (org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)
  WITH CHECK (org_id = NULLIF(current_setting('app.org_id', true), '')::uuid);

DROP POLICY IF EXISTS org_invocations_v5_policy ON tool_invocations_v5;
CREATE POLICY org_invocations_v5_policy ON tool_invocations_v5
  USING (org_id = NULLIF(current_setting('app.org_id', true), '')::uuid)
  WITH CHECK (org_id = NULLIF(current_setting('app.org_id', true), '')::uuid);

-- Atomic approval consumption (gateway transaction)
-- UPDATE approval_requests_v5
-- SET status = 'consumed', consumed_at = now()
-- WHERE id = :approval_id AND status = 'approved' AND expires_at > now()
--   AND args_hash = :args_hash AND idempotency_key = :idempotency_key
-- RETURNING id;

COMMENT ON TABLE tool_invocations_v5 IS
  'Partition by month on started_at in production; archive signed exports to object storage.';
