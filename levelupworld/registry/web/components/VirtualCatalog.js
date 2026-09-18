'use client';

import { useMemo, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { filterAndSort, SAVED_VIEWS } from '../lib/filter-catalog.mjs';
import { visibleWindow } from '../lib/window.mjs';

const ROW = 56;
const CARD = 132;
const VIEWPORT = 640;

export default function VirtualCatalog({ items }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const view = searchParams.get('view') === 'cards' ? 'cards' : 'table';
  const [scrollTop, setScrollTop] = useState(0);

  const filtered = useMemo(() => filterAndSort(items, searchParams), [items, searchParams]);
  const rowHeight = view === 'cards' ? CARD : ROW;
  const windowed = visibleWindow({
    itemCount: filtered.length,
    scrollTop,
    viewportHeight: VIEWPORT,
    rowHeight,
    overscan: 4,
  });
  const slice = filtered.slice(windowed.start, windowed.end);

  function replaceQuery(next) {
    const qs = next.toString();
    router.replace(qs ? `/registry?${qs}` : '/registry');
  }

  function setParam(key, value) {
    const next = new URLSearchParams(searchParams.toString());
    if (!value) next.delete(key);
    else next.set(key, value);
    replaceQuery(next);
  }

  function applyView(query) {
    const next = new URLSearchParams(query);
    if (view === 'cards') next.set('view', 'cards');
    replaceQuery(next);
    setScrollTop(0);
  }

  return (
    <main className="shell">
      <h1>Connector catalog</h1>
      <p className="meta">
        Virtualized table for {items.length} connectors. This page is the control plane.
        Invocation still goes through the policy gateway.
      </p>
      <div className="views">
        <label>
          Saved view{' '}
          <select
            value={SAVED_VIEWS.find((v) => v.query === searchParams.toString().replace(/&?view=cards/, '').replace(/^&/, ''))?.id || 'custom'}
            onChange={(e) => {
              const chosen = SAVED_VIEWS.find((v) => v.id === e.target.value);
              if (chosen) applyView(chosen.query);
            }}
          >
            {SAVED_VIEWS.map((v) => (
              <option key={v.id} value={v.id}>
                {v.label}
              </option>
            ))}
            <option value="custom">Custom</option>
          </select>
        </label>
        <button type="button" className={view === 'table' ? 'active' : ''} onClick={() => setParam('view', '')}>
          Table
        </button>
        <button type="button" className={view === 'cards' ? 'active' : ''} onClick={() => setParam('view', 'cards')}>
          Cards
        </button>
      </div>
      <div className="filters">
        <input
          type="search"
          placeholder="Name, tool, owner…"
          value={searchParams.get('q') || ''}
          onChange={(e) => setParam('q', e.target.value)}
        />
        <select value={searchParams.get('category') || ''} onChange={(e) => setParam('category', e.target.value)}>
          <option value="">Category</option>
          {[...new Set(items.map((c) => c.category))].sort().map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
        <select value={searchParams.get('operation') || ''} onChange={(e) => setParam('operation', e.target.value)}>
          <option value="">Operation</option>
          <option value="read">read-only</option>
          <option value="write,delete,external_communication">write / delete / external</option>
        </select>
        <select value={searchParams.get('trustTier') || ''} onChange={(e) => setParam('trustTier', e.target.value)}>
          <option value="">Trust tier</option>
          <option value="4,5">certified+</option>
          <option value="2,3">staging band</option>
        </select>
        <select value={searchParams.get('environment') || ''} onChange={(e) => setParam('environment', e.target.value)}>
          <option value="">Environment</option>
          <option>development</option>
          <option>staging</option>
          <option>production</option>
        </select>
        <select value={searchParams.get('health') || ''} onChange={(e) => setParam('health', e.target.value)}>
          <option value="">Health</option>
          <option>healthy</option>
          <option>degraded</option>
          <option>failing</option>
        </select>
        <select value={searchParams.get('sort') || 'rank'} onChange={(e) => setParam('sort', e.target.value === 'rank' ? '' : e.target.value)}>
          <option value="rank">Sort: rank</option>
          <option value="name">Sort: name</option>
          <option value="-activity_24h">Sort: activity</option>
          <option value="p95_latency_ms">Sort: p95</option>
        </select>
      </div>
      <p className="meta" data-catalog={items.length} data-filtered={filtered.length} data-rendered={slice.length}>
        Showing window {windowed.start + (slice.length ? 1 : 0)}–{windowed.end} of {filtered.length} filtered
        ({items.length} in catalog). Mounted rows: {slice.length}.
      </p>
      <div
        className="scroller"
        onScroll={(e) => setScrollTop(e.currentTarget.scrollTop)}
      >
        <div style={{ height: windowed.totalHeight, position: 'relative' }}>
          {view === 'table' ? (
            <table style={{ position: 'absolute', top: windowed.offsetY, left: 0, right: 0 }}>
              <thead>
                <tr>
                  <th>Connector</th>
                  <th>Category</th>
                  <th>Tools</th>
                  <th>Trust</th>
                  <th>Health</th>
                  <th>Security</th>
                  <th>Data</th>
                  <th>Owner</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {slice.map((c) => (
                  <tr key={c.slug} style={{ height: ROW }}>
                    <td>
                      <strong>{c.display_name}</strong>
                      <div className="muted">
                        <code>
                          {c.slug}@{c.version}
                        </code>
                      </div>
                    </td>
                    <td>{c.category}</td>
                    <td>
                      R{c.read_tool_count} W{c.write_tool_count} D{c.delete_tool_count} X{c.external_tool_count}
                    </td>
                    <td>
                      <span className="badge">{c.trust_tier}</span>
                      <div className="muted">{c.certification_state}</div>
                    </td>
                    <td>
                      {c.health?.status}
                      <div className="muted">
                        p95 {c.health?.p95_latency_ms}ms · {c.health?.calls_24h} calls
                      </div>
                    </td>
                    <td className={`posture-${c.security?.posture}`}>
                      {c.security?.posture}
                      <div className="muted">{c.security?.signed ? 'signed' : 'unsigned'} · SBOM {c.security?.sbom ? 'yes' : 'no'}</div>
                    </td>
                    <td>
                      {c.data_classification}
                      <div className="muted">{(c.outbound_domains || []).join(', ')}</div>
                    </td>
                    <td>{c.owner_team}</td>
                    <td>
                      <a href={`/registry/connectors/${c.slug}/versions/${c.version}`}>View</a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="card-list" style={{ position: 'absolute', top: windowed.offsetY, left: 0, right: 0 }}>
              {slice.map((c) => (
                <article key={c.slug} className="card" style={{ minHeight: CARD - 8 }}>
                  <strong>{c.display_name}</strong>
                  <div className="muted">
                    <code>
                      {c.slug}@{c.version}
                    </code>{' '}
                    · {c.category} · {c.trust_tier}
                  </div>
                  <p>{c.description}</p>
                  <a href={`/registry/connectors/${c.slug}/versions/${c.version}`}>View</a>
                </article>
              ))}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
