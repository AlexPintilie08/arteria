'use client';

import { useCallback, useMemo, useState } from 'react';
import { controlledAnalysisMessage, loadSimCatalog, searchSimPlaces, type LoadedSimCatalog, type SourcedPlace } from './sim-geography';

interface NeighborhoodExplorerProps {
  selectedPlace: SourcedPlace | null;
  onSelect: (place: SourcedPlace) => void;
  onClear: () => void;
  fillEnabled: boolean;
  onFillChange: (enabled: boolean) => void;
  analysisEnabled?: boolean;
}

export function NeighborhoodExplorer({
  selectedPlace,
  onSelect,
  onClear,
  fillEnabled,
  onFillChange,
  analysisEnabled = false,
}: NeighborhoodExplorerProps) {
  const [catalog, setCatalog] = useState<LoadedSimCatalog | null>(null);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const results = useMemo(() => catalog ? searchSimPlaces(catalog.places, query) : [], [catalog, query]);

  const loadCatalog = useCallback(async () => {
    if (catalog || loading) return;
    setLoading(true);
    setError('');
    try {
      const [catalogResponse, validationResponse] = await Promise.all([
        fetch('/data/iasi-neighborhoods.geojson'),
        fetch('/data/iasi-neighborhood-validation.json'),
      ]);
      if (!catalogResponse.ok || !validationResponse.ok) throw new Error('Fișierele catalogului SIM nu au putut fi încărcate.');
      const [catalogJson, validationJson] = await Promise.all([catalogResponse.json(), validationResponse.json()]);
      setCatalog(loadSimCatalog(catalogJson, validationJson));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Catalogul geografic nu a putut fi încărcat.');
    } finally {
      setLoading(false);
    }
  }, [catalog, loading]);

  function handleToggle(event: React.SyntheticEvent<HTMLDetailsElement>) {
    if (event.currentTarget.open) void loadCatalog();
  }

  const properties = selectedPlace?.feature.properties ?? {};
  const sourceUrl = typeof properties.source_url === 'string' ? properties.source_url : null;
  const sourceId = typeof properties.source_object_id === 'string' ? properties.source_object_id : selectedPlace?.id;
  const uncertainty = typeof properties.uncertainty_notes === 'string'
    ? properties.uncertainty_notes
    : 'Nu există o notă de incertitudine pentru această înregistrare.';
  const retrievedAt = typeof properties.retrieved_at === 'string'
    ? properties.retrieved_at
    : catalog?.metadata.retrieved_at;
  const snapshotAt = typeof properties.source_snapshot_at === 'string'
    ? properties.source_snapshot_at
    : catalog?.metadata.source_snapshot_at;

  return (
    <details className="sim-explorer" onToggle={handleToggle}>
      <summary className="sim-explorer-summary">
        <span>
          Catalog geografic SIM
          <small>OpenStreetMap · navigare geografică</small>
        </span>
        <span aria-hidden="true">⌄</span>
      </summary>

      <div className="sim-explorer-body">
        <p className="sim-source-note">
          Acoperire OSM parțială. Poligoanele sunt extinderi de locuri mapate în OpenStreetMap, nu limite administrative oficiale.
          Punctele rămân puncte; nu le atribuim contururi.
        </p>

        {loading && <p role="status" className="supporting">Se încarcă catalogul SIM…</p>}
        {error && <p role="alert" className="error">{error}</p>}
        {catalog && (
          <>
            <p className="sim-counts">
              {catalog.places.filter((place) => place.geometryType !== 'Point').length} poligoane · {catalog.places.filter((place) => place.geometryType === 'Point').length} repere punctuale
              {catalog.skippedCount > 0 ? ` · ${catalog.skippedCount} înregistrări invalide omise` : ''}
            </p>
            <label className="sim-search-label" htmlFor="sim-place-search">Caută cartier sau reper OSM</label>
            <input
              id="sim-place-search"
              className="sim-search"
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="De exemplu, Tătărași"
              autoComplete="off"
            />
            <ul className="sim-place-list" aria-label="Rezultate din catalogul OSM">
              {results.map((place) => (
                <li key={place.id}>
                  <button
                    type="button"
                    className={selectedPlace?.id === place.id ? 'sim-place-option selected' : 'sim-place-option'}
                    aria-pressed={selectedPlace?.id === place.id}
                    onClick={() => onSelect(place)}
                  >
                    <span>{place.name}</span>
                    <small>{place.geometryType === 'Point' ? 'Punct OSM · fără contur' : 'Poligon OSM'}</small>
                  </button>
                </li>
              ))}
              {results.length === 0 && <li className="supporting">Nu există potriviri în catalog.</li>}
            </ul>
            {catalog.metadata.attribution && (
              <p className="sim-attribution">
                {catalog.metadata.attribution} · licență {catalog.metadata.license ?? 'ODbL-1.0'}
                {catalog.metadata.attribution_url && <> · <a href={catalog.metadata.attribution_url} target="_blank" rel="noreferrer">detalii licență</a></>}
              </p>
            )}
          </>
        )}

        {selectedPlace && (
          <section className="sim-selected-place" aria-label={`Detalii sursă pentru ${selectedPlace.name}`}>
            <div className="sim-selected-heading">
              <div>
                <span className="sim-record-kind">{selectedPlace.geometryType === 'Point' ? 'Punct numai pentru navigare' : 'Extindere poligonală OSM'}</span>
                <h3>{selectedPlace.name}</h3>
              </div>
              <button type="button" className="sim-clear-button" onClick={onClear}>Revino la repere demo</button>
            </div>

            {selectedPlace.geometryType !== 'Point' && (
              <label className="sim-fill-toggle">
                <input type="checkbox" checked={fillEnabled} onChange={(event) => onFillChange(event.target.checked)} />
                Umple conturul pe hartă
              </label>
            )}

            {selectedPlace.validation.status === 'requires_controlled_analysis' && (
              <p className="notice" role="status">
                {controlledAnalysisMessage(selectedPlace)}
              </p>
            )}
            <p className="notice" role="status">
              {analysisEnabled
                ? selectedPlace.geometryType === 'Point'
                  ? 'Acest reper este doar un punct OSM. SIM nu îi atribuie o limită și nu îl trimite spre analiză de zonă.'
                  : selectedPlace.validation.status === 'valid'
                    ? 'Poligonul poate fi analizat la cerere cu motorul de graf pietonal SIM. Această selecție nu pornește automat o analiză.'
                    : 'Această geometrie este disponibilă pentru navigarea hărții; analiza standard nu este eligibilă.'
                : 'Previzualizare geografică numai. Analiza, scenariile și comparațiile nu sunt conectate la această selecție.'}
            </p>
            <dl className="sim-metadata">
              <div><dt>Sursă</dt><dd>OpenStreetMap</dd></div>
              <div><dt>ID obiect</dt><dd>{sourceId}</dd></div>
              {retrievedAt && <div><dt>Preluat</dt><dd>{retrievedAt}</dd></div>}
              {snapshotAt && <div><dt>Instantaneu OSM</dt><dd>{snapshotAt}</dd></div>}
              <div><dt>Incertitudine</dt><dd>{uncertainty}</dd></div>
              {sourceUrl && <div><dt>Obiect sursă</dt><dd><a href={sourceUrl} target="_blank" rel="noreferrer">Deschide în OpenStreetMap</a></dd></div>}
            </dl>
          </section>
        )}
      </div>
    </details>
  );
}
