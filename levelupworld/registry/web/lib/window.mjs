/**
 * Fixed-row window for the catalog table.
 * Callers must render only [start, end) so 100+ connectors do not mount every row.
 */
export function visibleWindow({
  itemCount,
  scrollTop,
  viewportHeight,
  rowHeight,
  overscan = 4,
}) {
  const count = Math.max(0, itemCount | 0);
  const height = rowHeight > 0 ? rowHeight : 1;
  const view = viewportHeight > 0 ? viewportHeight : 0;
  const top = Math.max(0, scrollTop || 0);
  if (count === 0 || view === 0) {
    return { start: 0, end: 0, offsetY: 0, totalHeight: count * height };
  }
  const start = Math.max(0, Math.floor(top / height) - overscan);
  const visibleCount = Math.ceil(view / height);
  const end = Math.min(count, start + visibleCount + overscan * 2);
  return {
    start,
    end,
    offsetY: start * height,
    totalHeight: count * height,
  };
}
