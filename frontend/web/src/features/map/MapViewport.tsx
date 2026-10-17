import { useEffect, useRef, useState } from 'react';
import { Map, NavigationControl, setWorkerUrl, type StyleSpecification, Marker } from 'maplibre-gl';
import { neighborhoodGeometries, demoIssuesByNeighborhood, type DemoStudyIssue } from '@arteria/shared/fixtures';

setWorkerUrl(new URL('maplibre-gl/dist/maplibre-gl-worker.mjs', import.meta.url).toString());

const baseStyle: StyleSpecification = {
  version: 8,
  sources: {
    'osm-tiles': {
      type: 'raster',
      tiles: [
        'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
      ],
      tileSize: 256,
      attribution: '© Contribuitori OpenStreetMap (ODbL)'
    }
  },
  layers: [
    {
      id: 'background',
      type: 'background',
      paint: { 'background-color': '#101820' }
    },
    {
      id: 'osm-raster',
      type: 'raster',
      source: 'osm-tiles',
      paint: {
        'raster-opacity': 0.65,
        'raster-saturation': -0.7,
        'raster-contrast': 0.2
      }
    }
  ]
};

interface MapViewportProps {
  neighborhoodId: string;
  center: [number, number];
  selectedIssueId: string | null;
  onSelectIssue?: (issue: DemoStudyIssue) => void;
  scenarioApplied?: boolean;
}

export default function MapViewport({
  neighborhoodId,
  center,
  selectedIssueId,
  onSelectIssue,
  scenarioApplied = false,
}: MapViewportProps) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<Map | null>(null);
  const markersRef = useRef<Marker[]>([]);
  const initialCenter = useRef(center);
  const [error, setError] = useState('');
  const [mapLoaded, setMapLoaded] = useState(false);

  useEffect(() => {
    if (!container.current) return;
    try {
      const instance = new Map({
        container: container.current,
        style: baseStyle,
        center: initialCenter.current,
        zoom: 14,
        pitch: 28,
        attributionControl: {}
      });
      map.current = instance;
      instance.addControl(new NavigationControl({ showCompass: true }), 'bottom-right');

      instance.on('load', () => {
        setMapLoaded(true);
      });

      instance.on('error', (event) => {
        if (process.env.NODE_ENV !== 'production') console.warn('MapLibre:', event.error?.message);
      });

      const observer = new ResizeObserver(() => instance.resize());
      observer.observe(container.current);
      return () => {
        observer.disconnect();
        markersRef.current.forEach(m => m.remove());
        markersRef.current = [];
        instance.remove();
        map.current = null;
      };
    } catch {
      setError('WebGL nu este disponibil. Selecția zonei rămâne accesibilă din panou.');
    }
  }, []);

  // Update center when neighborhood changes
  useEffect(() => {
    map.current?.flyTo({ center, zoom: 14.2, duration: 1200 });
  }, [center]);

  // Update vectors & pins when neighborhood or selection changes
  useEffect(() => {
    const instance = map.current;
    if (!instance || !mapLoaded) return;

    const geoData = neighborhoodGeometries[neighborhoodId];
    if (!geoData) return;

    // Boundary source & layers
    const boundaryGeoJson: GeoJSON.Feature<GeoJSON.Polygon> = {
      type: 'Feature',
      geometry: {
        type: 'Polygon',
        coordinates: [geoData.polygon]
      },
      properties: { name: geoData.name }
    };

    if (instance.getSource('area-boundary')) {
      (instance.getSource('area-boundary') as any).setData(boundaryGeoJson);
    } else {
      instance.addSource('area-boundary', {
        type: 'geojson',
        data: boundaryGeoJson
      });

      instance.addLayer({
        id: 'area-fill',
        type: 'fill',
        source: 'area-boundary',
        paint: {
          'fill-color': '#8bc9ed',
          'fill-opacity': 0.08
        }
      });

      instance.addLayer({
        id: 'area-line',
        type: 'line',
        source: 'area-boundary',
        paint: {
          'line-color': '#8bc9ed',
          'line-width': 2,
          'line-dasharray': [4, 2]
        }
      });
    }

    // Corridors source & layer
    const corridorFeatures: GeoJSON.Feature<GeoJSON.LineString>[] = geoData.corridors.map(c => ({
      type: 'Feature',
      geometry: {
        type: 'LineString',
        coordinates: c.coordinates
      },
      properties: { name: c.name }
    }));

    const corridorsGeoJson: GeoJSON.FeatureCollection<GeoJSON.LineString> = {
      type: 'FeatureCollection',
      features: corridorFeatures
    };

    if (instance.getSource('area-corridors')) {
      (instance.getSource('area-corridors') as any).setData(corridorsGeoJson);
    } else {
      instance.addSource('area-corridors', {
        type: 'geojson',
        data: corridorsGeoJson
      });

      instance.addLayer({
        id: 'corridors-line',
        type: 'line',
        source: 'area-corridors',
        paint: {
          'line-color': '#efc47c',
          'line-width': 3,
          'line-opacity': 0.8
        }
      });
    }

    // Interactive Pins for Issues
    markersRef.current.forEach(m => m.remove());
    markersRef.current = [];

    const issues = demoIssuesByNeighborhood[neighborhoodId] || [];
    issues.forEach(issue => {
      const el = document.createElement('button');
      el.type = 'button';
      const isSelected = selectedIssueId === issue.id;
      el.className = `custom-map-pin ${isSelected ? 'selected' : ''} ${scenarioApplied && isSelected ? 'scenario-active' : ''}`;
      el.setAttribute('role', 'button');
      el.setAttribute('tabindex', '0');
      el.setAttribute('aria-label', `Problemă semnalată: ${issue.title}, amplasament: ${issue.locationName}`);
      el.setAttribute('aria-pressed', isSelected ? 'true' : 'false');

      el.innerHTML = `
        <span class="pin-ring" aria-hidden="true"></span>
        <span class="pin-core" aria-hidden="true"></span>
        <span class="pin-label" aria-hidden="true">${issue.title.split(' ')[0]}</span>
      `;
      el.onclick = (e) => {
        e.preventDefault();
        onSelectIssue?.(issue);
      };
      el.onkeydown = (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelectIssue?.(issue);
        }
      };

      const marker = new Marker({ element: el })
        .setLngLat(issue.coordinates)
        .addTo(instance);

      markersRef.current.push(marker);
    });
  }, [neighborhoodId, selectedIssueId, scenarioApplied, mapLoaded, onSelectIssue]);

  return (
    <section className="map-viewport" aria-label="Hartă Iași">
      <div ref={container} className="map-canvas" />
      <div
        style={{
          position: 'absolute',
          top: '120px',
          left: '36px',
          background: 'rgba(24, 35, 46, 0.94)',
          backdropFilter: 'blur(8px)',
          border: '1px solid #42596a',
          borderRadius: '8px',
          padding: '10px 14px',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
          fontSize: '11px',
          color: '#a8bac9',
          zIndex: 2,
          pointerEvents: 'none',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ width: '14px', height: '10px', borderRadius: '2px', background: 'rgba(139, 201, 237, 0.2)', border: '1px dashed #8bc9ed' }}></span>
          Graniță estimată cartier
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ width: '14px', height: '3px', borderRadius: '2px', background: '#efc47c' }}></span>
          Coridoare majore mobilitate
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#8bc9ed', boxShadow: '0 0 6px #8bc9ed' }}></span>
          Punct problemă detectată
        </div>
        {scenarioApplied && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#a4d8bc', boxShadow: '0 0 6px #a4d8bc' }}></span>
            Intervenție scenariu activată
          </div>
        )}
      </div>
      {error && <p className="map-error" role="status">{error}</p>}
      <div className="map-coordinate">
        {center[1].toFixed(3)}° N / {center[0].toFixed(3)}° E
        <span>EPSG:4326 · OpenStreetMap ODbL</span>
      </div>
    </section>
  );
}
