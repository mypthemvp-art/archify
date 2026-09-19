#!/usr/bin/env node
/**
 * Stress the virtualized catalog: thousands of filter/window passes must stay bounded.
 */
import assert from 'node:assert/strict';
import { filterAndSort } from '../web/lib/filter-catalog.mjs';
import { visibleWindow } from '../web/lib/window.mjs';
import catalog from '../web/fixtures/scale-catalog.json' with { type: 'json' };

const items = catalog.connectors;
assert.ok(items.length >= 100);

const started = performance.now();
let maxRendered = 0;
let widest = 0;
for (let i = 0; i < 4000; i += 1) {
  const filtered = filterAndSort(items, {
    category: i % 5 === 0 ? 'database' : '',
    operation: i % 7 === 0 ? 'read' : i % 9 === 0 ? 'write,delete,external_communication' : '',
    q: i % 11 === 0 ? 'list' : '',
    trustTier: i % 3 === 0 ? '4,5' : '',
    environment: i % 4 === 0 ? 'production' : '',
    sort: i % 2 === 0 ? '-activity_24h' : 'rank',
  });
  widest = Math.max(widest, filtered.length);
  const rowHeight = 56;
  const scrollTop = (i * rowHeight) % Math.max(rowHeight, filtered.length * rowHeight);
  const windowed = visibleWindow({
    itemCount: filtered.length,
    scrollTop,
    viewportHeight: 640,
    rowHeight,
    overscan: 4,
  });
  const rendered = windowed.end - windowed.start;
  maxRendered = Math.max(maxRendered, rendered);
  if (filtered.length >= 80) {
    assert.ok(rendered < 40, `window exploded: rendered=${rendered} filtered=${filtered.length} i=${i}`);
  }
  assert.ok(windowed.start >= 0 && windowed.end <= filtered.length);
}

const big = Array.from({ length: 2000 }, (_, i) => ({
  ...items[i % items.length],
  slug: `scale-${i}`,
  rank: i + 1,
}));
const bigWindow = visibleWindow({
  itemCount: big.length,
  scrollTop: 56 * 1500,
  viewportHeight: 640,
  rowHeight: 56,
  overscan: 4,
});
assert.ok(bigWindow.end - bigWindow.start < 40);
assert.ok(bigWindow.start > 1400);

const elapsedMs = Math.round(performance.now() - started);
assert.ok(elapsedMs < 8000, `catalog stress too slow: ${elapsedMs}ms`);
console.log(
  JSON.stringify({
    ok: true,
    iterations: 4000,
    catalog: items.length,
    synthetic: big.length,
    max_rendered: maxRendered,
    widest_filter: widest,
    elapsed_ms: elapsedMs,
  }),
);
