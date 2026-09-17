#!/usr/bin/env node
/**
 * Shared helpers for Weeks 7–8 pilot evidence runners.
 */
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const here = path.dirname(fileURLToPath(import.meta.url));
export const PILOT_ROOT = path.resolve(here, '..');
export const REPO_ROOT = path.resolve(PILOT_ROOT, '../../..');
export const EVIDENCE_RUNS = path.join(PILOT_ROOT, 'evidence', 'runs');
export const FIXTURES = path.join(PILOT_ROOT, 'fixtures');

export function loadManifest() {
  return JSON.parse(fs.readFileSync(path.join(PILOT_ROOT, 'pilot.manifest.json'), 'utf8'));
}

export function newCorrelationId() {
  return crypto.randomUUID();
}

export function argsHash(obj) {
  return crypto.createHash('sha256').update(JSON.stringify(obj)).digest('hex');
}

export function ensureRunsDir() {
  fs.mkdirSync(EVIDENCE_RUNS, { recursive: true });
}

export function writeEvidence(bundle) {
  ensureRunsDir();
  const base = `${bundle.plugin}-${bundle.correlation_id.slice(0, 8)}`;
  const jsonPath = path.join(EVIDENCE_RUNS, `${base}.json`);
  const mdPath = path.join(EVIDENCE_RUNS, `${base}.md`);
  bundle.evidence_uri = `file://${jsonPath}`;
  fs.writeFileSync(jsonPath, `${JSON.stringify(bundle, null, 2)}\n`);
  fs.writeFileSync(mdPath, toMarkdown(bundle));
  return { jsonPath, mdPath, bundle };
}

export function toMarkdown(b) {
  const lines = [
    `# Pilot evidence — ${b.plugin}`,
    '',
    `- correlation_id: \`${b.correlation_id}\``,
    `- automations: ${b.automations.join(', ')}`,
    `- result: **${b.result_status}**`,
    `- mutation: \`${b.mutation}\``,
    `- environment: ${b.environment}`,
    `- risk_score: ${b.risk_score ?? 'n/a'}`,
    '',
    `## Summary`,
    '',
    b.summary,
    '',
    `## Findings`,
    '',
  ];
  if (!b.findings.length) {
    lines.push('_No findings._', '');
  } else {
    for (const f of b.findings) {
      lines.push(
        `### [${f.severity}] ${f.title}`,
        '',
        `- automation: ${f.automation}`,
        `- path: ${f.path || 'n/a'}`,
        `- evidence: ${f.evidence}`,
        `- remediation: ${f.remediation}`,
        '',
      );
    }
  }
  if (b.hypotheses?.length) {
    lines.push('## Hypotheses', '');
    for (const h of b.hypotheses) {
      lines.push(`${h.rank}. ${h.statement}`, `   - evidence: ${h.evidence}`, '');
    }
  }
  if (b.timeline?.length) {
    lines.push('## Timeline', '');
    for (const t of b.timeline) {
      lines.push(`- ${t.at} · ${t.source || 'unknown'} — ${t.event}`);
    }
    lines.push('');
  }
  return `${lines.join('\n')}\n`;
}

export function git(args, cwd = REPO_ROOT) {
  const r = spawnSync('git', args, { cwd, encoding: 'utf8' });
  return {
    status: r.status ?? 1,
    stdout: (r.stdout || '').trim(),
    stderr: (r.stderr || '').trim(),
  };
}

export function walkFiles(root, { maxFiles = 400, ignore = [] } = {}) {
  const out = [];
  const ignoreRe = ignore.map((p) => new RegExp(p));
  function walk(dir) {
    if (out.length >= maxFiles) return;
    let entries;
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch {
      return;
    }
    for (const ent of entries) {
      if (out.length >= maxFiles) return;
      const full = path.join(dir, ent.name);
      const rel = path.relative(root, full);
      if (ignoreRe.some((re) => re.test(rel))) continue;
      if (ent.isDirectory()) walk(full);
      else if (ent.isFile()) out.push(rel);
    }
  }
  walk(root);
  return out;
}

export function readTextSafe(filePath, maxBytes = 200_000) {
  try {
    const buf = fs.readFileSync(filePath);
    const slice = buf.subarray(0, maxBytes).toString('utf8');
    return slice;
  } catch {
    return '';
  }
}

/** Redact secret-looking values; never echo raw secrets in findings. */
export function redact(text) {
  return String(text)
    .replace(/(api[_-]?key|password|secret|token|private[_-]?key)\s*[:=]\s*['"]?[^\s'"]{6,}/gi, '$1=[REDACTED]')
    .replace(/\b[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b/g, '[REDACTED_JWT]')
    .replace(/\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b/g, '[REDACTED_GH_TOKEN]')
    .replace(/\bAKIA[0-9A-Z]{16}\b/g, '[REDACTED_AWS_KEY]');
}

export const SECRET_PATTERNS = [
  { id: 'aws-access-key', re: /\bAKIA[0-9A-Z]{16}\b/, title: 'Possible AWS access key' },
  { id: 'github-pat', re: /\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b/, title: 'Possible GitHub token' },
  { id: 'jwt', re: /\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b/, title: 'Possible JWT' },
  {
    id: 'assignment-secret',
    re: /(api[_-]?key|password|secret|token|private[_-]?key)\s*[:=]\s*['"]?[^\s'"]{8,}/i,
    title: 'Secret-looking assignment',
  },
  { id: 'private-key-block', re: /-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----/, title: 'Private key material' },
];

export const SENSITIVE_PATHS = [
  /^\.env(\.|$)/i,
  /(^|\/)secrets?\//i,
  /(^|\/)credentials\./i,
  /\.pem$/i,
  /\.key$/i,
  /(^|\/)id_rsa/i,
];

export const RESTRICTED_LICENSES = new Set(['GPL-3.0', 'AGPL-3.0', 'SSPL-1.0', 'BUSL-1.1']);
