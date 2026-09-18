import { Suspense } from 'react';
import VirtualCatalog from '../../components/VirtualCatalog';
import { loadCatalog } from '../../lib/load-catalog';

export default function RegistryPage() {
  const catalog = loadCatalog();
  return (
    <Suspense fallback={<main className="shell">Loading catalog…</main>}>
      <VirtualCatalog items={catalog.connectors} />
    </Suspense>
  );
}
