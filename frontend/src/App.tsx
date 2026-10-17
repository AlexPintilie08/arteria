import { useEffect, useRef, useState } from 'react';
import { Map as MapLibreMap, setWorkerUrl } from 'maplibre-gl';
import mapLibreWorkerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';

type Health = { status: string; service: string };

const DEMO_STYLE = 'https://tiles.openfreemap.org/styles/dark';

setWorkerUrl(mapLibreWorkerUrl);

function useBackendHealth() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const controller = new AbortController();

    async function check() {
      try {
        const response = await fetch('/api/health', { signal: controller.signal });
        if (!response.ok) throw new Error(`Backend returned HTTP ${response.status}`);
        const result = (await response.json()) as Health;
        if (active) {
          setHealth(result);
          setError(null);
        }
      } catch (reason) {
        if (active && !controller.signal.aborted) {
          setHealth(null);
          setError(reason instanceof Error ? reason.message : 'Backend is unavailable.');
        }
      }
    }

    void check();
    const timer = window.setInterval(() => void check(), 5000);
    return () => {
      active = false;
      controller.abort();
      window.clearInterval(timer);
    };
  }, []);

  return { health, error };
}

export default function App() {
  const mapContainer = useRef<HTMLDivElement>(null);
  const [mapError, setMapError] = useState(false);
  const { health, error } = useBackendHealth();

  useEffect(() => {
    if (!mapContainer.current) return;

    const map = new MapLibreMap({
      container: mapContainer.current,
      style: DEMO_STYLE,
      center: [27.594, 47.158],
      zoom: 12,
      pitch: 42,
      bearing: -18,
    });
    map.on('error', () => setMapError(true));
    map.once('load', () => setMapError(false));

    return () => map.remove();
  }, []);

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="#home" aria-label="ARTERIA home">
          <span className="brand-mark" aria-hidden="true">A</span>
          <span>
            <strong>ARTERIA</strong>
            <small>BY ARION</small>
          </span>
        </a>
        <p className="tagline">Understand the city. Shape its future.</p>
        <div className={`connection ${health ? 'is-online' : 'is-offline'}`} role="status" aria-live="polite">
          <span className="connection-dot" />
          {health ? 'Backend connected' : 'Backend unavailable'}
        </div>
      </header>

      <section className="map-stage" aria-label="Iași map preview">
        <div className="map-canvas" ref={mapContainer} />
        {mapError && (
          <div className="map-fallback" role="status">
            <span className="fallback-grid" aria-hidden="true" />
            <div>
              <strong>Map preview unavailable</strong>
              <p>The OpenFreeMap style could not load. The ARTERIA shell is still running.</p>
            </div>
          </div>
        )}
        <div className="map-caption">
          <span className="live-indicator" />
          <span>IAȘI, ROMANIA</span>
          <span className="caption-divider">/</span>
          <span>MAP PREVIEW</span>
        </div>
      </section>

      <aside className="status-panel" aria-label="Development status">
        <span className="eyebrow">LOCAL DEVELOPMENT</span>
        <h1>City intelligence, taking shape.</h1>
        <p className="panel-copy">Backend status updates automatically while this local application is open.</p>
        <div className="service-card">
          <div className="service-heading">
            <span className={`service-icon ${health ? 'service-ready' : 'service-error'}`} aria-hidden="true">
              {health ? '✓' : '!' }
            </span>
            <div>
              <strong>Backend API</strong>
              <small>{health ? health.service : 'GET /health'}</small>
            </div>
            <span className={`service-state ${health ? '' : 'state-offline'}`}>{health ? 'ONLINE' : 'OFFLINE'}</span>
          </div>
          {error && <p className="error-detail">{error}. Start both services with <code>scripts/dev</code>.</p>}
        </div>
        <p className="data-note">Map tiles use the OpenFreeMap public style with MapLibre attribution. Urban analysis is not implemented yet.</p>
      </aside>

      <footer className="app-footer">
        <span>ARTERIA by ARION</span>
        <span>DEVELOPMENT FOUNDATION · 0.1.0</span>
      </footer>
    </main>
  );
}
