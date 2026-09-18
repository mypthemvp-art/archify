import './globals.css';

export const metadata = {
  title: 'MCP Registry Catalog',
  description: 'Virtualized control-plane catalog for 100+ MCP connectors.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <header className="top">
          <div className="brand">
            <strong>Agent-Ops</strong>
            <span>Registry catalog · gateway enforces</span>
          </div>
          <nav>
            <a href="/registry">Catalog</a>
          </nav>
        </header>
        {children}
      </body>
    </html>
  );
}
