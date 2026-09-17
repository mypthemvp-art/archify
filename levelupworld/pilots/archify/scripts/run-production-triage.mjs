#!/usr/bin/env node
/**
 * Production Triage Copilot pilot runner (A024, A040) — read-only evidence.
 */
import fs from 'node:fs';
import path from 'node:path';
import {
  FIXTURES,
  REPO_ROOT,
  argsHash,
  git,
  loadManifest,
  newCorrelationId,
  readTextSafe,
  redact,
  writeEvidence,
} from './lib.mjs';

function loadCiLog() {
  const envPath = process.env.PILOT_CI_LOG;
  if (envPath && fs.existsSync(envPath)) return readTextSafe(envPath);
  return readTextSafe(path.join(FIXTURES, 'sample-ci-log.txt'));
}

function loadAlerts() {
  const envPath = process.env.PILOT_ALERTS;
  if (envPath && fs.existsSync(envPath)) {
    return JSON.parse(fs.readFileSync(envPath, 'utf8'));
  }
  return JSON.parse(fs.readFileSync(path.join(FIXTURES, 'sample-alerts.json'), 'utf8'));
}

function failingTestHypotheses(ciLog) {
  const hypotheses = [];
  const findings = [];
  const redactedLog = redact(ciLog);

  if (/jwt expired|expected 200 to equal 401/i.test(ciLog)) {
    hypotheses.push({
      rank: 1,
      statement: 'Auth middleware token-expiry path regressed or clock skew broke JWT validation expectations',
      evidence: 'CI log shows jwt expired and status 200 vs 401 assertion failure',
    });
    findings.push({
      id: 'a024-auth-jwt',
      automation: 'A024',
      severity: 'high',
      title: 'Failing test points at JWT expiry handling',
      path: 'src/auth/middleware.js',
      evidence: redact('AssertionError expected 200 to equal 401; Error: jwt expired'),
      remediation: 'Inspect verifyToken + middleware; confirm test clock and token fixtures',
      redacted: true,
    });
  }

  if (/FAIL |AssertionError|Error:/i.test(ciLog)) {
    hypotheses.push({
      rank: hypotheses.length + 1,
      statement: 'Recent commit on the failing branch introduced a behavioral change covered by unit tests',
      evidence: 'CI log contains FAIL / AssertionError markers',
    });
  }

  const log = git(['log', '-5', '--pretty=format:%h %ad %s', '--date=iso-strict']);
  if (log.status === 0 && log.stdout) {
    findings.push({
      id: 'a024-recent-commits',
      automation: 'A024',
      severity: 'info',
      title: 'Recent commits for correlation',
      path: null,
      evidence: log.stdout.split('\n').slice(0, 5).join(' | '),
      remediation: 'Diff suspect commits against failing test files',
      redacted: false,
    });
  }

  if (!hypotheses.length) {
    hypotheses.push({
      rank: 1,
      statement: 'Insufficient signal in CI log — gather full job artifacts',
      evidence: redactedLog.slice(0, 200) || 'empty log',
    });
  }

  findings.push({
    id: 'a024-ci-excerpt',
    automation: 'A024',
    severity: 'medium',
    title: 'CI failure excerpt captured (redacted)',
    path: null,
    evidence: redactedLog.split('\n').slice(0, 12).join(' | '),
    remediation: 'Attach full JUnit/SARIF in CI evidence store for deeper triage',
    redacted: true,
  });

  return { hypotheses, findings };
}

function buildTimeline(alerts) {
  const timeline = alerts.map((a) => ({
    at: a.at,
    event: redact(a.event),
    source: a.source || 'unknown',
  }));
  const log = git(['log', '-3', '--pretty=format:%aI %h %s']);
  if (log.status === 0) {
    for (const line of log.stdout.split('\n').filter(Boolean)) {
      const m = line.match(/^(\S+)\s+(\S+)\s+(.*)$/);
      if (m) {
        timeline.push({ at: m[1], event: `commit ${m[2]} — ${redact(m[3])}`, source: 'git' });
      }
    }
  }
  timeline.sort((a, b) => String(a.at).localeCompare(String(b.at)));
  return timeline;
}

function main() {
  const manifest = loadManifest();
  const started = new Date().toISOString();
  const correlationId = newCorrelationId();
  const ciLog = loadCiLog();
  const alerts = loadAlerts();
  const { hypotheses, findings } = failingTestHypotheses(ciLog);
  const timeline = buildTimeline(alerts);

  findings.push({
    id: 'a040-timeline-length',
    automation: 'A040',
    severity: 'info',
    title: `Incident timeline constructed (${timeline.length} events)`,
    path: null,
    evidence: `sources=${[...new Set(timeline.map((t) => t.source))].join(',')}`,
    remediation: 'Keep triage read-only; propose mitigations without auto-paging',
    redacted: false,
  });

  const finished = new Date().toISOString();
  const args = { pilot_id: manifest.pilot_id, automations: ['A024', 'A040'], alerts: alerts.length };
  const high = findings.some((f) => f.severity === 'high' || f.severity === 'critical');
  const bundle = {
    correlation_id: correlationId,
    pilot_id: manifest.pilot_id,
    plugin: 'production-triage-copilot',
    automations: ['A024', 'A040'],
    actor: process.env.PILOT_ACTOR || 'user:pilot',
    tenant: process.env.PILOT_TENANT || 'tenant_local',
    environment: process.env.PILOT_ENV || 'development',
    started_at: started,
    finished_at: finished,
    mutation: 'none',
    result_status: high ? 'warn' : 'passed',
    summary:
      `Production Triage Copilot built ${timeline.length} timeline events and ${hypotheses.length} ranked hypotheses from CI/alert fixtures. ` +
      'No mutate tools invoked.',
    risk_score: high ? 55 : 25,
    findings,
    hypotheses,
    timeline,
    arguments_hash: argsHash(args),
    connectors_used: ['cicd-observer', 'observability-reader', 'git-repository'],
    evidence_uri: '',
  };
  const { jsonPath, mdPath } = writeEvidence(bundle);
  console.log(
    JSON.stringify({
      ok: true,
      plugin: bundle.plugin,
      result_status: bundle.result_status,
      hypotheses: hypotheses.length,
      timeline: timeline.length,
      correlation_id: correlationId,
      evidence_json: path.relative(REPO_ROOT, jsonPath),
      evidence_md: path.relative(REPO_ROOT, mdPath),
    }),
  );
}

main();
