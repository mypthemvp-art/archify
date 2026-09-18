#!/usr/bin/env node
/** Spec alias: beforeMCPExecution → policy preflight (args hash + gateway). */
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
await import(pathToFileURL(path.join(here, 'policy-pre-tool.mjs')).href);
