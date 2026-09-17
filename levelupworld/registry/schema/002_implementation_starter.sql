-- Registry Implementation Starter schema (additive)
-- Aligns with Custom MCP Registry Dashboard data model.

CREATE TABLE IF NOT EXISTS connector_versions_v2 (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL,
  slug text NOT NULL,
  version text NOT NULL,
  manifest jsonb NOT NULL,
  manifest_sha256 text NOT NULL,
  image_digest text,
  trust_tier smallint NOT NULL,
  certification_status text NOT NULL,
  lifecycle_status text NOT NULL,
  owner_team text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (org_id, slug, version)
);

CREATE TABLE IF NOT EXISTS tool_definitions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  connector_version_id uuid NOT NULL REFERENCES connector_versions_v2(id) ON DELETE CASCADE,
  tool_name text NOT NULL,
  input_schema jsonb NOT NULL,
  operation text NOT NULL CHECK (operation IN ('read','write','delete','external_communication')),
  risk text NOT NULL,
  policy_key text NOT NULL,
  approval_required boolean NOT NULL DEFAULT false,
  UNIQUE (connector_version_id, tool_name)
);

CREATE TABLE IF NOT EXISTS connector_activations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL,
  connector_version_id uuid NOT NULL REFERENCES connector_versions_v2(id),
  project_id uuid NOT NULL,
  environment text NOT NULL,
  enabled boolean NOT NULL DEFAULT false,
  approved_by uuid,
  approved_at timestamptz,
  expires_at timestamptz,
  UNIQUE (org_id, connector_version_id, project_id, environment)
);

CREATE TABLE IF NOT EXISTS approval_requests_v2 (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL,
  correlation_id uuid NOT NULL,
  actor_id uuid NOT NULL,
  tool_id uuid NOT NULL REFERENCES tool_definitions(id),
  environment text NOT NULL,
  args_hash text NOT NULL,
  normalized_arguments jsonb NOT NULL,
  plan jsonb,
  risk text NOT NULL,
  status text NOT NULL,
  approver_id uuid,
  expires_at timestamptz NOT NULL,
  idempotency_key text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tool_invocations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  correlation_id uuid NOT NULL,
  org_id uuid NOT NULL,
  actor_id uuid NOT NULL,
  connector_version_id uuid NOT NULL REFERENCES connector_versions_v2(id),
  tool_name text NOT NULL,
  environment text NOT NULL,
  args_hash text NOT NULL,
  approval_request_id uuid REFERENCES approval_requests_v2(id),
  policy_decision text NOT NULL,
  status text NOT NULL,
  latency_ms integer,
  response_hash text,
  redaction_count integer NOT NULL DEFAULT 0,
  occurred_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS test_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL,
  connector_version_id uuid NOT NULL REFERENCES connector_versions_v2(id),
  suite text NOT NULL,
  status text NOT NULL, -- queued|running|passed|failed
  report jsonb NOT NULL DEFAULT '{}'::jsonb,
  started_at timestamptz NOT NULL DEFAULT now(),
  finished_at timestamptz
);

CREATE TABLE IF NOT EXISTS policy_decisions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL,
  policy_key text NOT NULL,
  correlation_id uuid NOT NULL,
  decision text NOT NULL,
  reason text,
  input jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS tool_invocations_corr_idx ON tool_invocations (correlation_id);
CREATE INDEX IF NOT EXISTS tool_invocations_occurred_idx ON tool_invocations (occurred_at DESC);
CREATE INDEX IF NOT EXISTS connector_activations_project_idx ON connector_activations (project_id, environment);

ALTER TABLE connector_versions_v2 ENABLE ROW LEVEL SECURITY;
ALTER TABLE connector_activations ENABLE ROW LEVEL SECURITY;
ALTER TABLE approval_requests_v2 ENABLE ROW LEVEL SECURITY;
ALTER TABLE tool_invocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE test_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE policy_decisions ENABLE ROW LEVEL SECURITY;
