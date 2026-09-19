#!/usr/bin/env node
/**
 * Full check of every read-only catalog automation (mutation none).
 * stdout: JSON report. Exit 1 when any blueprint fails a check.
 */
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { checkReadAutomationsFromRepo } from './lib/read-automation-check.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const report = checkReadAutomationsFromRepo(root);
process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
if (!report.ok) process.exit(1);
