'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { Map, NavigationControl, setWorkerUrl, type GeoJSONSource, type StyleSpecification, type MapMouseEvent } from 'maplibre-gl';
import type { SourcedPlace } from '../neighborhoods/sim-geography';
import { featureBounds, placeCenter } from '../neighborhoods/sim-geography';
import { geometryFeatureCollection, safeFeatureCollection } from '../workspace/map-first-data';

setWorkerUrl(new URL('maplibre-gl/dist/maplibre-gl-worker.mjs', import.meta.url).toString());

const mapStyle: StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution: '© OpenStreetMap contributors · ODbL-1.0',
    },
  },
  layers: [
    { id: 'background', type: 'background', paint: { 'background-color': '#111923' } },
    { id: 'osm-raster', type: 'raster', source: 'osm', paint: { 'raster-opacity': 0.72, 'raster-saturation': -0.45 } },
  ],
};

interface Props {
  places: SourcedPlace[];
  selectedId: string | null;
  selectedProblemId: string | null;
  problems: unknown;
  candidateGeometry: unknown;
  fillPolygons: boolean;
  onSelect: (place: SourcedPlace) => void;
}
const emptyCollection: GeoJSON.FeatureCollection = { type: 'FeatureCollection', features: [] };

export default function NeighborhoodCatalogMap({ places, selectedId, selectedProblemId, problems, candidateGeometry, fillPolygons, onSelect }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const mapRef = useRef<Map | null>(null);
  const onSelectRef = useRef(onSelect);
  const placesRef = useRef(places);
  const selectedRef = useRef<string | null>(null);
  const hoveredRef = useRef<string | null>(null);
  const initialFitRef = useRef(false);
  const [ready, setReady] = useState(false);
  const [mapError, setMapError] = useState('');
  onSelectRef.current = onSelect;
  placesRef.current = places;

  const catalogData = useMemo<GeoJSON.FeatureCollection>(() => ({
    type: 'FeatureCollection',
    features: places.map((place) => ({
      ...place.feature,
      id: place.id,
      properties: { ...place.feature.properties, catalog_id: place.id, catalog_name: place.name },
    })) as GeoJSON.Feature[],
  }), [places]);
  const problemData = useMemo(() => safeFeatureCollection(problems) as unknown as GeoJSON.FeatureCollection, [problems]);
  const selectedProblemData = useMemo<GeoJSON.FeatureCollection>(() => ({
    type: 'FeatureCollection',
    features: selectedProblemId
      ? problemData.features.filter((feature) => feature.properties?.problem_id === selectedProblemId)
      : [],
  }), [problemData, selectedProblemId]);
  const candidateData = useMemo(() => geometryFeatureCollection(candidateGeometry) as unknown as GeoJSON.FeatureCollection, [candidateGeometry]);

  useEffect(() => {
    if (!container.current) return;
    try {
      const instance = new Map({
        container: container.current,
        style: mapStyle,
        center: [27.59, 47.16],
        zoom: 12.4,
        minZoom: 10,
        maxZoom: 19,
        pitch: 0,
        attributionControl: { compact: true },
      });
      mapRef.current = instance;
      instance.addControl(new NavigationControl({ showCompass: true }), 'bottom-right');
      instance.once('load', () => setReady(true));
      instance.on('error', (event) => {
        if (!instance.isStyleLoaded() && event.error) setMapError('Harta nu a putut încărca stilul cartografic. Catalogul SIM rămâne disponibil în listă.');
      });
      const resizeObserver = new ResizeObserver(() => instance.resize());
      resizeObserver.observe(container.current);
      return () => {
        resizeObserver.disconnect();
        instance.remove();
        mapRef.current = null;
      };
    } catch {
      setMapError('Harta nu este disponibilă în acest browser. Catalogul SIM rămâne disponibil în listă.');
    }
  }, []);

  useEffect(() => {
    const instance = mapRef.current;
    if (!instance || !ready) return;
    if (!instance.getSource('sim-catalog')) {
      instance.addSource('sim-catalog', { type: 'geojson', data: catalogData, promoteId: 'catalog_id' });
      instance.addLayer({
        id: 'sim-catalog-fill', type: 'fill', source: 'sim-catalog',
        paint: {
          'fill-color': ['case', ['boolean', ['feature-state', 'selected'], false], '#f4c978', ['boolean', ['feature-state', 'hover'], false], '#79d6bb', '#77b9de'],
          'fill-opacity': ['case', ['boolean', ['feature-state', 'selected'], false], fillPolygons ? 0.29 : 0.1, fillPolygons ? 0.13 : 0.025],
        },
      });
      instance.addLayer({
        id: 'sim-catalog-outline', type: 'line', source: 'sim-catalog',
        paint: {
          'line-color': ['case', ['boolean', ['feature-state', 'selected'], false], '#fff0b9', ['boolean', ['feature-state', 'hover'], false], '#9ce7d1', '#83c8ea'],
          'line-width': ['case', ['boolean', ['feature-state', 'selected'], false], 3.5, ['boolean', ['feature-state', 'hover'], false], 2.6, 1.4],
          'line-opacity': 0.96,
        },
      });
      instance.addLayer({
        id: 'sim-catalog-points', type: 'circle', source: 'sim-catalog',
        filter: ['==', ['geometry-type'], 'Point'],
        paint: {
          'circle-color': ['case', ['boolean', ['feature-state', 'selected'], false], '#fff0b9', ['boolean', ['feature-state', 'hover'], false], '#9ce7d1', '#f4c978'],
          'circle-radius': ['case', ['boolean', ['feature-state', 'selected'], false], 9, ['boolean', ['feature-state', 'hover'], false], 8, 6],
          'circle-stroke-color': '#15212a', 'circle-stroke-width': 2.5,
        },
      });

      const pickPlace = (event: MapMouseEvent) => {
        const feature = instance.queryRenderedFeatures(event.point, { layers: ['sim-catalog-fill', 'sim-catalog-outline', 'sim-catalog-points'] })[0];
        const id = feature?.properties?.catalog_id;
        if (typeof id !== 'string') return;
        const place = placesRef.current.find((item) => item.id === id);
        if (place) onSelectRef.current(place);
      };
      const updateHover = (event: MapMouseEvent) => {
        const feature = instance.queryRenderedFeatures(event.point, { layers: ['sim-catalog-fill', 'sim-catalog-outline', 'sim-catalog-points'] })[0];
        const nextId = typeof feature?.properties?.catalog_id === 'string' ? feature.properties.catalog_id as string : null;
        if (hoveredRef.current && hoveredRef.current !== nextId) {
          instance.setFeatureState({ source: 'sim-catalog', id: hoveredRef.current }, { hover: false });
        }
        if (nextId && hoveredRef.current !== nextId) instance.setFeatureState({ source: 'sim-catalog', id: nextId }, { hover: true });
        hoveredRef.current = nextId;
        instance.getCanvas().style.cursor = nextId ? 'pointer' : '';
      };
      const clearHover = () => {
        if (hoveredRef.current) instance.setFeatureState({ source: 'sim-catalog', id: hoveredRef.current }, { hover: false });
        hoveredRef.current = null;
        instance.getCanvas().style.cursor = '';
      };
      instance.on('click', pickPlace);
      instance.on('mousemove', updateHover);
      instance.on('mouseout', clearHover);
    }
    (instance.getSource('sim-catalog') as GeoJSONSource).setData(catalogData);
    if (!initialFitRef.current && places.length) {
      const bounds = places.map((place) => featureBounds(place.feature)).filter((value): value is [[number, number], [number, number]] => value !== null);
      if (bounds.length) {
        instance.fitBounds([
          [Math.min(...bounds.map((item) => item[0][0])), Math.min(...bounds.map((item) => item[0][1]))],
          [Math.max(...bounds.map((item) => item[1][0])), Math.max(...bounds.map((item) => item[1][1]))],
        ], { padding: 64, maxZoom: 12.8, duration: 700 });
        initialFitRef.current = true;
      }
    }
  }, [catalogData, places, ready]);

  useEffect(() => {
    const instance = mapRef.current;
    if (!instance || !ready || !instance.getLayer('sim-catalog-fill')) return;
    if (selectedRef.current) instance.setFeatureState({ source: 'sim-catalog', id: selectedRef.current }, { selected: false });
    selectedRef.current = selectedId;
    if (selectedId) instance.setFeatureState({ source: 'sim-catalog', id: selectedId }, { selected: true });
    if (!selectedId) return;
    const place = places.find((item) => item.id === selectedId);
    if (!place) return;
    if (place.geometryType === 'Point') {
      const center = placeCenter(place);
      if (center) instance.flyTo({ center, zoom: Math.max(instance.getZoom(), 15), duration: 700 });
    } else {
      const bounds = featureBounds(place.feature);
      if (bounds) instance.fitBounds(bounds, { padding: { top: 70, right: 70, bottom: 70, left: 70 }, maxZoom: 15.5, duration: 750 });
    }
  }, [selectedId, places, ready]);

  useEffect(() => {
    const instance = mapRef.current;
    if (!instance || !ready || !instance.getLayer('sim-catalog-fill')) return;
    instance.setPaintProperty('sim-catalog-fill', 'fill-opacity', ['case', ['boolean', ['feature-state', 'selected'], false], fillPolygons ? 0.29 : 0.1, fillPolygons ? 0.13 : 0.025]);
    if (!instance.getSource('sim-problems')) {
      instance.addSource('sim-problems', { type: 'geojson', data: problemData });
      instance.addLayer({ id: 'sim-problem-fill', type: 'fill', source: 'sim-problems', paint: { 'fill-color': '#e87978', 'fill-opacity': 0.12 } });
      instance.addLayer({ id: 'sim-problem-line', type: 'line', source: 'sim-problems', paint: { 'line-color': '#f27c7a', 'line-width': 2.2, 'line-dasharray': [2, 1] } });
      instance.addLayer({ id: 'sim-problem-points', type: 'circle', source: 'sim-problems', filter: ['==', ['geometry-type'], 'Point'], paint: { 'circle-color': '#ff817b', 'circle-radius': 6, 'circle-stroke-color': '#fff0e8', 'circle-stroke-width': 2 } });
    } else (instance.getSource('sim-problems') as GeoJSONSource).setData(problemData);
    if (!instance.getSource('sim-selected-problem')) {
      instance.addSource('sim-selected-problem', { type: 'geojson', data: selectedProblemData });
      instance.addLayer({ id: 'sim-selected-problem-fill', type: 'fill', source: 'sim-selected-problem', paint: { 'fill-color': '#f5c76d', 'fill-opacity': 0.22 } });
      instance.addLayer({ id: 'sim-selected-problem-line', type: 'line', source: 'sim-selected-problem', paint: { 'line-color': '#ffe08c', 'line-width': 4, 'line-dasharray': [1, 1] } });
      instance.addLayer({ id: 'sim-selected-problem-points', type: 'circle', source: 'sim-selected-problem', filter: ['==', ['geometry-type'], 'Point'], paint: { 'circle-color': '#ffe08c', 'circle-radius': 9, 'circle-stroke-color': '#3a2b12', 'circle-stroke-width': 2 } });
    } else (instance.getSource('sim-selected-problem') as GeoJSONSource).setData(selectedProblemData);
    if (!instance.getSource('sim-candidate')) {
      instance.addSource('sim-candidate', { type: 'geojson', data: candidateData });
      instance.addLayer({ id: 'sim-candidate-fill', type: 'fill', source: 'sim-candidate', paint: { 'fill-color': '#68d2ad', 'fill-opacity': 0.18 } });
      instance.addLayer({ id: 'sim-candidate-line', type: 'line', source: 'sim-candidate', paint: { 'line-color': '#73e0bb', 'line-width': 4, 'line-dasharray': [1, 1] } });
      instance.addLayer({ id: 'sim-candidate-points', type: 'circle', source: 'sim-candidate', filter: ['==', ['geometry-type'], 'Point'], paint: { 'circle-color': '#73e0bb', 'circle-radius': 8, 'circle-stroke-color': '#10231d', 'circle-stroke-width': 2 } });
    } else (instance.getSource('sim-candidate') as GeoJSONSource).setData(candidateData);
  }, [problemData, selectedProblemData, candidateData, fillPolygons, ready]);

  return <div className="catalog-map" aria-label="Harta Iași și catalogul geografic SIM">
    <div ref={container} className="catalog-map-canvas" />
    <div className="catalog-map-legend" aria-label="Legendă hartă">
      <span><i className="legend-area" /> Zone mapate SIM</span>
      <span><i className="legend-point" /> Loc punctual fără contur</span>
      <span><i className="legend-problem" /> Probleme detectate de SIM</span>
      {selectedProblemData.features.length > 0 && <span><i className="legend-problem-selected" /> Problemă selectată</span>}
      {candidateData.features.length > 0 && <span><i className="legend-candidate" /> Geometrie candidată SIM</span>}
    </div>
    {mapError && <p className="catalog-map-error" role="status">{mapError}</p>}
    <div className="catalog-map-attribution">© OpenStreetMap contributors · ODbL-1.0 · © OpenStreetMap tiles</div>
  </div>;
}
