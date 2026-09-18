#!/usr/bin/env node
/** Spec alias: afterMCPExecution → audit completion events. */
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
await import(pathToFileURL(path.join(here, 'post-tool-audit-log.mjs')).href);
