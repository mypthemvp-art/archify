-- Week 3–4: concrete RLS policies using app.org_id GUC
-- Application must: SELECT set_config('app.org_id', '<uuid-or-slug>', true);

CREATE OR REPLACE FUNCTION app_org_id() RETURNS text
LANGUAGE sql STABLE AS $$
  SELECT NULLIF(current_setting('app.org_id', true), '')
$$;

-- Example policies for implementation-starter tables
DROP POLICY IF EXISTS connector_versions_org_isolation ON connector_versions_v2;
CREATE POLICY connector_versions_org_isolation ON connector_versions_v2
  USING (org_id::text = app_org_id())
  WITH CHECK (org_id::text = app_org_id());

DROP POLICY IF EXISTS activations_org_isolation ON connector_activations;
CREATE POLICY activations_org_isolation ON connector_activations
  USING (org_id::text = app_org_id())
  WITH CHECK (org_id::text = app_org_id());

DROP POLICY IF EXISTS approvals_org_isolation ON approval_requests_v2;
CREATE POLICY approvals_org_isolation ON approval_requests_v2
  USING (org_id::text = app_org_id())
  WITH CHECK (org_id::text = app_org_id());

DROP POLICY IF EXISTS invocations_org_isolation ON tool_invocations;
CREATE POLICY invocations_org_isolation ON tool_invocations
  USING (org_id::text = app_org_id())
  WITH CHECK (org_id::text = app_org_id());

DROP POLICY IF EXISTS test_runs_org_isolation ON test_runs;
CREATE POLICY test_runs_org_isolation ON test_runs
  USING (org_id::text = app_org_id())
  WITH CHECK (org_id::text = app_org_id());

DROP POLICY IF EXISTS policy_decisions_org_isolation ON policy_decisions;
CREATE POLICY policy_decisions_org_isolation ON policy_decisions
  USING (org_id::text = app_org_id())
  WITH CHECK (org_id::text = app_org_id());

-- Force RLS even for table owners in application roles
ALTER TABLE connector_versions_v2 FORCE ROW LEVEL SECURITY;
ALTER TABLE connector_activations FORCE ROW LEVEL SECURITY;
ALTER TABLE approval_requests_v2 FORCE ROW LEVEL SECURITY;
ALTER TABLE tool_invocations FORCE ROW LEVEL SECURITY;
ALTER TABLE test_runs FORCE ROW LEVEL SECURITY;
ALTER TABLE policy_decisions FORCE ROW LEVEL SECURITY;
