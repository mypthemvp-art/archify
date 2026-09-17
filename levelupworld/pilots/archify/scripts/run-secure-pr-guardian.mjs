#!/usr/bin/env node
/**
 * Secure PR Guardian pilot runner (A003, A004, A021) — read-only evidence.
 */
import fs from 'node:fs';
import path from 'node:path';
import {
  PILOT_ROOT,
  REPO_ROOT,
  SECRET_PATTERNS,
  SENSITIVE_PATHS,
  RESTRICTED_LICENSES,
  argsHash,
  git,
  loadManifest,
  newCorrelationId,
  readTextSafe,
  redact,
  walkFiles,
  writeEvidence,
} from './lib.mjs';

const IGNORE = [
  '^node_modules/',
  '^\\.git/',
  '^archify/node_modules/',
  '^levelupworld/registry/gateway/\\.venv/',
  '^levelupworld/pilots/.*/evidence/runs/',
  '\\.png$',
  '\\.jpg$',
  '\\.webp$',
  '\\.zip$',
  '\\.webm$',
];

function scanSecrets(files) {
  const findings = [];
  for (const rel of files) {
    if (SENSITIVE_PATHS.some((re) => re.test(rel))) {
      findings.push({
        id: `sensitive-path:${rel}`,
        automation: 'A004',
        severity: 'medium',
        title: 'Sensitive path present in working tree',
        path: rel,
        evidence: 'Path matches sensitive-file heuristic',
        remediation: 'Confirm file is gitignored and never committed; rotate if previously leaked',
        redacted: true,
      });
    }
    const full = path.join(REPO_ROOT, rel);
    const text = readTextSafe(full);
    if (!text) continue;
    for (const pat of SECRET_PATTERNS) {
      if (pat.re.test(text)) {
        findings.push({
          id: `${pat.id}:${rel}`,
          automation: 'A004',
          severity: pat.id === 'private-key-block' ? 'critical' : 'high',
          title: pat.title,
          path: rel,
          evidence: redact(`Pattern ${pat.id} matched in ${rel}`),
          remediation: 'Remove secret, rotate credential, add to secret scanner allowlist only if false positive',
          redacted: true,
        });
        break;
      }
    }
  }
  return findings;
}

function scanLicenses() {
  const findings = [];
  const pkgPaths = walkFiles(REPO_ROOT, {
    maxFiles: 50,
    ignore: IGNORE,
  }).filter((p) => /(^|\/)package\.json$/.test(p));

  for (const rel of pkgPaths) {
    try {
      const pkg = JSON.parse(fs.readFileSync(path.join(REPO_ROOT, rel), 'utf8'));
      const license = pkg.license;
      if (typeof license === 'string' && RESTRICTED_LICENSES.has(license)) {
        findings.push({
          id: `license:${rel}:${license}`,
          automation: 'A003',
          severity: 'high',
          title: `Restricted license ${license}`,
          path: rel,
          evidence: `package.json license field is ${license}`,
          remediation: 'Replace dependency or obtain legal waiver before merge',
          redacted: false,
        });
      }
      // Scan direct deps for known restricted names is out of scope; note inventory size.
      const depCount =
        Object.keys(pkg.dependencies || {}).length + Object.keys(pkg.devDependencies || {}).length;
      if (depCount > 0) {
        findings.push({
          id: `license-inventory:${rel}`,
          automation: 'A003',
          severity: 'info',
          title: `Dependency inventory recorded (${depCount} packages)`,
          path: rel,
          evidence: `Counted dependencies in ${rel}`,
          remediation: 'Run full license scanner in CI for transitive deps',
          redacted: false,
        });
      }
    } catch {
      // ignore invalid package.json
    }
  }
  return findings;
}

function prRiskScore(secretFindings, licenseFindings) {
  const status = git(['status', '--porcelain']);
  const diffStat = git(['diff', '--stat', 'HEAD']);
  const changed = status.stdout ? status.stdout.split('\n').filter(Boolean) : [];
  let score = Math.min(40, changed.length * 2);
  if (secretFindings.some((f) => f.severity === 'critical' || f.severity === 'high')) score += 40;
  if (licenseFindings.some((f) => f.severity === 'high')) score += 25;
  if (changed.some((line) => /\.github\/workflows\//.test(line))) score += 10;
  if (changed.some((line) => /schema\/|migration/i.test(line))) score += 10;
  score = Math.min(100, score);

  const findings = [
    {
      id: 'pr-risk-summary',
      automation: 'A021',
      severity: score >= 70 ? 'high' : score >= 40 ? 'medium' : 'low',
      title: `PR risk score ${score}/100`,
      path: null,
      evidence: redact(
        `changed_files=${changed.length}; diff_stat_lines=${diffStat.stdout.split('\n').length}`,
      ),
      remediation: 'Address high findings before requesting review; keep mutation tools gated',
      redacted: false,
    },
  ];
  if (changed.length) {
    findings.push({
      id: 'changed-paths',
      automation: 'A021',
      severity: 'info',
      title: 'Changed paths snapshot',
      path: null,
      evidence: changed.slice(0, 30).join('; ') || 'clean tree',
      remediation: 'Ensure CODEOWNERS cover .github and levelupworld/.cursor paths',
      redacted: false,
    });
  }
  return { score, findings, changedCount: changed.length };
}

function main() {
  const manifest = loadManifest();
  const started = new Date().toISOString();
  const correlationId = newCorrelationId();
  const files = walkFiles(REPO_ROOT, { maxFiles: 350, ignore: IGNORE });
  const secretFindings = scanSecrets(files);
  const licenseFindings = scanLicenses();
  const risk = prRiskScore(secretFindings, licenseFindings);
  const findings = [...licenseFindings, ...secretFindings, ...risk.findings];
  const high = findings.filter((f) => ['high', 'critical'].includes(f.severity)).length;
  const result_status = high > 0 ? 'failed' : findings.some((f) => f.severity === 'medium') ? 'warn' : 'passed';
  const finished = new Date().toISOString();
  const args = {
    pilot_id: manifest.pilot_id,
    automations: ['A003', 'A004', 'A021'],
    files_scanned: files.length,
  };
  const bundle = {
    correlation_id: correlationId,
    pilot_id: manifest.pilot_id,
    plugin: 'secure-pr-guardian',
    automations: ['A003', 'A004', 'A021'],
    actor: process.env.PILOT_ACTOR || 'user:pilot',
    tenant: process.env.PILOT_TENANT || 'tenant_local',
    environment: process.env.PILOT_ENV || 'development',
    started_at: started,
    finished_at: finished,
    mutation: 'none',
    result_status,
    summary:
      `Secure PR Guardian pilot scanned ${files.length} files and ${risk.changedCount} dirty paths. ` +
      `${secretFindings.length} secret findings, ${licenseFindings.filter((f) => f.severity !== 'info').length} license issues, risk ${risk.score}/100.`,
    risk_score: risk.score,
    findings,
    arguments_hash: argsHash(args),
    connectors_used: ['git-repository', 'filesystem-sandbox'],
    evidence_uri: '',
  };
  const { jsonPath, mdPath } = writeEvidence(bundle);
  console.log(
    JSON.stringify({
      ok: true,
      plugin: bundle.plugin,
      result_status,
      risk_score: risk.score,
      findings: findings.length,
      correlation_id: correlationId,
      evidence_json: path.relative(REPO_ROOT, jsonPath),
      evidence_md: path.relative(REPO_ROOT, mdPath),
    }),
  );
  // Pilot certify treats runner success as process exit 0 even when findings fail —
  // certification gate decides expand/no-expand.
  process.exit(0);
}

main();
