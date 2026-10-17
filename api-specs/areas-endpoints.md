# API Specification: Gestiunea Teritoriului, Zonelor și Straturilor Geospațiale

Definește contractele pentru obținerea frontierelor cartografice verificate ale Iașului, coridoarelor topologice OSM și metadatelor privind straturile de date disponibile.

---

## 1. `GET /api/v1/areas`

Furnizează lista oficială a cartierelor și zonelor de studiu din municipiul Iași, înlocuind marcajele provizorii de tip `preview-*`.

- **Metodă HTTP:** `GET`
- **Query Params:**
  - `city_id` (string, obligatoriu, default: `"iasi-ro"`)
  - `include_bounds` (boolean, opțional, default: `true`)

### Răspuns Așteptat (Response Schema - 200 OK)
```json
{
  "city": {
    "id": "iasi-ro",
    "name": "Iași",
    "crs_default": "EPSG:4326",
    "crs_projected": "EPSG:3844"
  },
  "areas": [
    {
      "id": "iasi-podu-ros",
      "slug": "podu-ros",
      "name": "Podu Roș (Coridor Bahlui)",
      "center": [27.584, 47.153],
      "bbox": [27.570, 47.140, 27.605, 47.165],
      "area_hectares": 142.5,
      "population_estimate": 18450,
      "validation_status": "certified_cadastral",
      "active_sensors_count": 8
    },
    {
      "id": "iasi-copou",
      "slug": "copou",
      "name": "Copou",
      "center": [27.568, 47.184],
      "bbox": [27.550, 47.170, 27.585, 47.198],
      "area_hectares": 210.0,
      "population_estimate": 24100,
      "validation_status": "certified_cadastral",
      "active_sensors_count": 5
    }
  ]
}
```

### Comportament în Interfață (Frontend UI/UX)
- **Loading State:**
  - Selectorul de zonă din Dock-ul Stânga afișează o animație subtilă de pulsare tip skeleton.
- **Error State (500 / Network Error):**
  - Selectorul oferă fallback pe cache-ul offline local (`neighborhoods` din fixtures), semnalizând cu badge galben: *„Mod date locale (Conexiune eșuată)”*.

---

## 2. `GET /api/v1/areas/{area_id}/geometry`

Returnează poligonul GeoJSON oficial de frontieră și coridoarele de rețea inspectabile pentru afișarea în `MapViewport`.

- **Metodă HTTP:** `GET`
- **Path Params:** `area_id` (ex: `iasi-podu-ros`)

### Răspuns Așteptat (Response Schema - 200 OK)
```json
{
  "area_id": "iasi-podu-ros",
  "crs": "EPSG:4326",
  "boundary": {
    "type": "Feature",
    "geometry": {
      "type": "Polygon",
      "coordinates": [
        [
          [27.572, 47.146],
          [27.598, 47.145],
          [27.602, 47.160],
          [27.586, 47.162],
          [27.573, 47.156],
          [27.572, 47.146]
        ]
      ]
    },
    "properties": {
      "stroke": "#8bc9ed",
      "stroke_width": 2,
      "fill_opacity": 0.08
    }
  },
  "corridors": {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "id": "cor_socola",
        "geometry": {
          "type": "LineString",
          "coordinates": [[27.584, 47.153], [27.592, 47.144], [27.601, 47.135]]
        },
        "properties": {
          "name": "Bulevardul Socola",
          "category": "arterial",
          "lanes": 6,
          "tram_track": true
        }
      }
    ]
  }
}
```

### Comportament în Interfață (Frontend UI/UX)
- La încărcarea geometriei, MapLibre animează viewport-ul (`fitBounds` pe `bbox`-ul zonei cu padding de 40px și durată de 900ms).
- Dacă geometria nu se poate descărca, viewport-ul păstrează centrul aproximativ fără a bloca interacțiunea cu restul aplicației.
