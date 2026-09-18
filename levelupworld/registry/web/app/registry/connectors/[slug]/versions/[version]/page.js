import Link from 'next/link';
import { notFound } from 'next/navigation';
import { loadCatalog } from '../../../../../../lib/load-catalog';

export function generateStaticParams() {
  return loadCatalog().connectors.map((c) => ({ slug: c.slug, version: c.version }));
}

export default async function ConnectorVersionPage({ params }) {
  const { slug, version } = await params;
  const item = loadCatalog().connectors.find((c) => c.slug === slug && c.version === version);
  if (!item) notFound();
  return (
    <main className="shell">
      <p>
        <Link href="/registry">Catalog</Link>
      </p>
      <article className="detail">
        <h1>{item.display_name}</h1>
        <p className="muted">
          <code>
            {item.slug}@{item.version}
          </code>{' '}
          · {item.category} · {item.trust_tier} · {item.certification_state}
        </p>
        <p>{item.description}</p>
        <ul>
          <li>Owner: {item.owner_team}</li>
          <li>Transport: {item.transport}</li>
          <li>Classification: {item.data_classification}</li>
          <li>Environments: {(item.allowed_environments || []).join(', ')}</li>
          <li>
            Security: {item.security?.posture} · signed {item.security?.signed ? 'yes' : 'no'} · CVE critical{' '}
            {item.security?.cve_critical} / high {item.security?.cve_high}
          </li>
          <li>Digest: <code>{item.image_digest}</code></li>
        </ul>
        <p className="meta">
          Synthetic scale row. Activation, quarantine, and tool calls are enforced by the policy gateway, not this page.
        </p>
      </article>
    </main>
  );
}
