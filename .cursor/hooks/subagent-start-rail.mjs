#!/usr/bin/env node
/** subagentStart rail. ask is treated as deny by Cursor, so this only returns allow or deny. */
import fs from 'node:fs';
import { decideSubagentStart } from '../../levelupworld/scripts/lib/needs-attention-rails.mjs';

function readInput() {
  try {
    return JSON.parse(fs.readFileSync(0, 'utf8') || '{}');
  } catch {
    return null;
  }
}

const decision = decideSubagentStart(readInput());
process.stdout.write(`${JSON.stringify(decision)}\n`);
