#!/usr/bin/env node
/**
 * Prove the catalog window mounts a slice of a 100+ connector list, not every row.
 */
import assert from 'node:assert/strict';
import { filterAndSort } from '../web/lib/filter-catalog.mjs';
import { visibleWindow } from '../web/lib/window.mjs';
import catalog from '../web/fixtures/scale-catalog.json' with { type: 'json' };

const items = catalog.connectors;
assert.ok(items.length >= 100, `expected >=100 connectors, got ${items.length}`);

const top = visibleWindow({
  itemCount: items.length,
  scrollTop: 0,
  viewportHeight: 640,
  rowHeight: 56,
  overscan: 4,
});
assert.equal(top.start, 0);
assert.ok(top.end < 40, `top window too large: ${top.end}`);
assert.ok(top.end < items.length);

const mid = visibleWindow({
  itemCount: items.length,
  scrollTop: 56 * 80,
  viewportHeight: 640,
  rowHeight: 56,
  overscan: 4,
});
assert.ok(mid.start > 60, `expected scrolled start, got ${mid.start}`);
assert.ok(mid.end - mid.start < 40);
assert.ok(mid.end <= items.length);

const empty = visibleWindow({ itemCount: 0, scrollTop: 0, viewportHeight: 640, rowHeight: 56 });
assert.equal(empty.end, 0);

const readonlyProd = filterAndSort(items, {
  operation: 'read',
  trustTier: '4,5',
  environment: 'production',
  health: 'healthy,degraded',
});
assert.ok(readonlyProd.length >= 5, `saved view empty: ${readonlyProd.length}`);
assert.ok(readonlyProd.every((c) => c.write_tool_count === 0 && c.allowed_environments.includes('production')));

const writes = filterAndSort(items, { operation: 'write,delete,external_communication' });
assert.ok(writes.length >= 5);
assert.ok(writes.every((c) => c.write_tool_count || c.delete_tool_count || c.external_tool_count));

const quarantined = filterAndSort(items, { certification_state: 'quarantined' });
assert.ok(quarantined.length >= 3);

const cve = filterAndSort(items, { posture: 'review_required,blocked' });
assert.ok(cve.length >= 3);

const db = filterAndSort(items, { category: 'database', q: 'list_database' });
assert.ok(db.length >= 1);
assert.ok(db.every((c) => c.category === 'database'));

console.log(
  JSON.stringify({
    ok: true,
    catalog: items.length,
    top_window: top.end - top.start,
    readonly_prod: readonlyProd.length,
    writes: writes.length,
  }),
);
