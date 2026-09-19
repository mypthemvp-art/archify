#!/usr/bin/env node
/** stop rail. Retries an errored turn so it does not sit in Needs Attention. */
import fs from 'node:fs';
import { decideAgentStop } from '../../levelupworld/scripts/lib/needs-attention-rails.mjs';

function readInput() {
  try {
    return JSON.parse(fs.readFileSync(0, 'utf8') || '{}');
  } catch {
    return null;
  }
}

const decision = decideAgentStop(readInput());
process.stdout.write(`${JSON.stringify(decision)}\n`);
