/**
 * Full check of every catalog automation whose mutation class is `none`.
 * Opens each blueprint. Does not sample. Does not mutate.
 */
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';

const CONTRACT = ['trigger', 'inputs', 'plan', 'guardrails', 'approval', 'evidence', 'verification'];

function parseFrontmatter(text) {
  const match = String(text || '').match(/^---\n([\s\S]*?)\n---/);
  if (!match) return null;
  const data = {};
  for (const line of match[1].split('\n')) {
    const idx = line.indexOf(':');
    if (idx === -1) continue;
    const key = line.slice(0, idx).trim();
    let value = line.slice(idx + 1).trim();
    if (value.startsWith('[') && value.endsWith(']')) {
      value = value
        .slice(1, -1)
        .split(',')
        .map((part) => part.trim())
        .filter(Boolean);
    }
    data[key] = value;
  }
  return data;
}

function blueprintPath(autoDir, id) {
  const prefix = `${id.toLowerCase()}-`;
  const hit = fs.readdirSync(autoDir).find((name) => name.startsWith(prefix) && name.endsWith('.md'));
  return hit ? path.join(autoDir, hit) : null;
}

export function auditReadBlueprint(auto, text, { skillExists = true } = {}) {
  const findings = [];
  const fm = parseFrontmatter(text);
  if (!fm) {
    findings.push({ id: auto.id, check: 'frontmatter', detail: 'missing frontmatter' });
    return findings;
  }
  if (fm.id !== auto.id) findings.push({ id: auto.id, check: 'id', detail: `frontmatter id ${fm.id}` });
  if (fm.mutation !== 'none') findings.push({ id: auto.id, check: 'mutation', detail: `frontmatter mutation ${fm.mutation}` });
  if (fm.title !== auto.title) findings.push({ id: auto.id, check: 'title', detail: 'title does not match catalog' });
  if (!String(text).includes(auto.trigger)) findings.push({ id: auto.id, check: 'trigger', detail: 'trigger text missing' });
  if (!String(text).includes(auto.capability)) findings.push({ id: auto.id, check: 'capability', detail: 'capability text missing' });
  if (!String(text).includes(auto.output)) findings.push({ id: auto.id, check: 'output', detail: 'output text missing' });
  if (!String(text).includes('Mutation class: `none`')) {
    findings.push({ id: auto.id, check: 'mutation_class', detail: 'checklist is not mutation none' });
  }
  if (!String(text).includes('Prefer read-only discovery')) {
    findings.push({ id: auto.id, check: 'read_only', detail: 'missing read-only instruction' });
  }
  for (const section of [
    '## Trigger',
    '## Connector / plugin capability',
    '## Output and guardrail',
    '## Automation contract checklist',
    '## Agent instructions',
    '## Tools policy',
  ]) {
    if (!String(text).includes(section)) findings.push({ id: auto.id, check: 'section', detail: section });
  }
  const contract = Array.isArray(fm.contract) ? fm.contract : [];
  for (const step of CONTRACT) {
    if (!contract.includes(step)) findings.push({ id: auto.id, check: 'contract', detail: step });
  }
  if (!String(text).includes('Denied: production shell')) {
    findings.push({ id: auto.id, check: 'deny', detail: 'tools policy does not deny production shell' });
  }
  if (!String(text).includes('Require approval gateway:')) {
    findings.push({ id: auto.id, check: 'approval_gate', detail: 'tools policy has no approval gateway' });
  }
  const allowed = String(text)
    .split('\n')
    .find((line) => line.includes('Allowed without approval'));
  if (!allowed || !/scoped read\/search\/fetch\/diagnose/.test(allowed)) {
    findings.push({ id: auto.id, check: 'allowed_tools', detail: 'allowed tools are not limited to read/search/fetch/diagnose' });
  }
  if (!skillExists) findings.push({ id: auto.id, check: 'skill', detail: 'skill file missing' });
  return findings;
}

export function checkReadAutomations({ root, catalog, autoDir, skillsDir }) {
  const correlation_id = `read-automation-check-${crypto.randomUUID()}`;
  const automations = catalog.automations || [];
  const read = automations.filter((auto) => auto.mutation === 'none');
  const skipped = automations.filter((auto) => auto.mutation !== 'none').map((auto) => auto.id);
  const findings = [];
  const checked = [];

  for (const auto of read) {
    const file = blueprintPath(autoDir, auto.id);
    if (!file) {
      findings.push({ id: auto.id, check: 'blueprint', detail: 'file missing' });
      continue;
    }
    const text = fs.readFileSync(file, 'utf8');
    const plugin = auto.plugin === 'unassigned' ? 'levelupworld-catalog-router' : auto.plugin;
    const skill = path.join(skillsDir, plugin, 'SKILL.md');
    findings.push(...auditReadBlueprint(auto, text, { skillExists: fs.existsSync(skill) }));
    checked.push(auto.id);
  }

  const readIds = new Set(read.map((auto) => auto.id));
  for (const name of fs.readdirSync(autoDir)) {
    const match = /^(a\d{3})-/i.exec(name);
    if (!match) continue;
    const text = fs.readFileSync(path.join(autoDir, name), 'utf8');
    const fm = parseFrontmatter(text);
    if (fm?.mutation === 'none' && !readIds.has(fm.id)) {
      findings.push({ id: fm.id || name, check: 'orphan', detail: 'blueprint says none but catalog does not' });
    }
  }

  return {
    correlation_id,
    tenant: null,
    checked: checked.length,
    skipped: skipped.length,
    findings,
    ok: findings.length === 0 && checked.length === read.length,
  };
}

export function checkReadAutomationsFromRepo(root) {
  const catalog = JSON.parse(fs.readFileSync(path.join(root, 'levelupworld/docs/catalog.json'), 'utf8'));
  return checkReadAutomations({
    root,
    catalog,
    autoDir: path.join(root, '.cursor/automations'),
    skillsDir: path.join(root, '.cursor/skills/levelupworld'),
  });
}
