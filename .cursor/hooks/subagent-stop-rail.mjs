#!/usr/bin/env node
/** subagentStop rail. Follow-up is only consumed when status is completed. */
import fs from 'node:fs';
import { decideSubagentStop } from '../../levelupworld/scripts/lib/needs-attention-rails.mjs';

function readInput() {
  try {
    return JSON.parse(fs.readFileSync(0, 'utf8') || '{}');
  } catch {
    return null;
  }
}

const decision = decideSubagentStop(readInput());
process.stdout.write(`${JSON.stringify(decision)}\n`);
