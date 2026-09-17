#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const repoPolicy = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  '../../../../.cursor/hooks/policy-pre-tool.mjs',
);
const body = fs.readFileSync(0, 'utf8');
const result = spawnSync(process.execPath, [repoPolicy], {
  input: body,
  encoding: 'utf8',
});
process.stdout.write(result.stdout || '');
process.stderr.write(result.stderr || '');
process.exit(result.status ?? 1);
