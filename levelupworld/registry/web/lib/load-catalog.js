import fs from 'node:fs';
import path from 'node:path';

export function loadCatalog() {
  const file = path.join(process.cwd(), 'fixtures/scale-catalog.json');
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}
