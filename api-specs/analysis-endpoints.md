# API Specification: Analiză Teritorială și Diagnoză Mobilitate

Contractul pentru endpoint-ul `POST /analyze` și fluxul asociat de telemetrie în timp real din rețeaua CTP Iași și senzorii buclelor electromagnetice.

---

## 1. `POST /api/v1/analyze`

Execută evaluarea topologică pe baza rețelei stradale OpenStreetMap, recensământului CTP și indicatorilor de accesibilitate.

- **Metodă HTTP:** `POST`
- **Antete (Headers):**
  - `Content-Type: application/json`
  - `Authorization: Bearer <access_token>` (opțional în modul public/read-only)

### Payload Cerere (Request Body)
```json
{
  "area": {
    "city_id": "iasi-ro",
    "area_id": "iasi-podu-ros",
    "boundary": null,
    "boundary_source": "known_area",
    "crs": "EPSG:4326"
  },
  "layers": [
    "roads",
    "walking",
    "cycling",
    "public_transport",
    "parking",
    "green_space"
  ],
  "analysis": {
    "network_modes": ["walk", "bike", "drive"],
    "accessibility_thresholds": [
      { "value": 5, "unit": "minute", "mode": "walk" },
      { "value": 15, "unit": "minute", "mode": "walk" },
      { "value": 10, "unit": "minute", "mode": "bike" }
    ]
  },
  "data_as_of": "2026-10-01T00:00:00Z"
}
```

### Răspuns Așteptat (Response Schema - 200 OK)
```json
{
  "analysis_id": "an_iasi_20261017_pr01",
  "area": {
    "city_id": "iasi-ro",
    "area_id": "iasi-podu-ros",
    "crs": "EPSG:4326"
  },
  "created_at": "2026-10-17T18:40:00Z",
  "indicators": [
    {
      "id": "walk_access_5min",
      "label": "Populație cu acces pietonal la servicii în 5 min",
      "value": 68.4,
      "unit": "%",
      "status": "calculated",
      "provenance": [
        {
          "source": "OpenStreetMap + Recensământ INS",
          "source_version": "2026-Q3",
          "retrieved_at": "2026-10-02T10:00:00Z",
          "method": "isochrone_catchment_graph",
          "crs": "EPSG:3844"
        }
      ],
      "uncertainty": {
        "kind": "coverage_limitation",
        "description": "Calculat pe graf pietonal continuu; scările de bloc și intrările secundare nu sunt cartate complet.",
        "interval": [65.2, 71.6],
        "confidence": 0.92
      }
    },
    {
      "id": "cycle_connectivity",
      "label": "Indice conectivitate trasee velo",
      "value": 0.42,
      "unit": "ratio",
      "status": "calculated",
      "provenance": [
        {
          "source": "OSM cycling lanes + PMUD Iași",
          "source_version": "2026-09",
          "retrieved_at": "2026-10-02T10:00:00Z",
          "method": "topological_network_efficiency",
          "crs": "EPSG:3844"
        }
      ],
      "uncertainty": {
        "kind": "methodological",
        "description": "Pistele partajate cu trotuarul sunt penalizate cu factorul 0.5 din cauza conflictelor pietonale.",
        "interval": null,
        "confidence": null
      }
    }
  ],
  "telemetry": {
    "timestamp": "2026-10-17T08:15:00Z",
    "regime": "peak_morning",
    "metrics": {
      "peak_flow_rate_veh_h": 2180,
      "max_queue_meters": 340,
      "avg_delay_seconds": 74.2,
      "level_of_service": "LOS E/F",
      "tram_commercial_speed_kmh": 9.4
    }
  },
  "issues": [
    {
      "id": "issue-podu-ros-1",
      "label": "Podu Roș Multi-Leg Center #IS-PR-01 (Congestie Critică LOS E/F)",
      "category": "nod_rutier",
      "indicator_ids": ["walk_access_5min", "cycle_connectivity"],
      "status": "observed",
      "provenance": [
        {
          "source": "Senzori electromagnetici buclă Podu Roș",
          "source_version": "2026.10",
          "retrieved_at": "2026-10-17T08:15:00Z",
          "method": "induction_loop_telemetry",
          "crs": "EPSG:4326"
        }
      ],
      "uncertainty": {
        "kind": "hardware_drift",
        "description": "Eroare marjă senzor ±3% în condiții de ploaie torențială.",
        "interval": [71.5, 76.9],
        "confidence": 0.95
      },
      "geometry": {
        "type": "Point",
        "coordinates": [27.584, 47.153]
      }
    }
  ],
  "layer_availability": [
    { "layer": "roads", "status": "observed", "reason": "Rețea OSM completă și verificată." },
    { "layer": "parking", "status": "unknown", "reason": "Datele cadastrale privind parcările rezidențiale nu sunt digitalizate în această zonă." }
  ],
  "warnings": [
    "Datele de debit reprezintă intervalul orar 08:00 - 09:00 din zile lucrătoare de toamnă."
  ]
}
```

### Comportament în Interfață (Frontend UI/UX)
- **Loading State:**
  - Dock-ul Stânga blochează butonul „Se analizează…”, cu iconiță rotativă.
  - Deck-ul Orizontal de sub hartă afișează 3 carduri Skeleton cu efect de shimmer discret (`rgba(255,255,255,0.04)`).
  - Harta nu este demontată; un overlay discret semi-transparent cu progress bar linear apare la marginea superioară a hărții.
- **Eroare (422 Invalid Geometry / 503 Upstream Failure):**
  - Butonul de analiză redevine activ.
  - Zona de indicatori afișează o componentă `ErrorNotice` cu explicație tehnică și buton `Reîncearcă Diagnoza`.
  - Nu se șterge starea anterioară selectată dacă utilizatorul a navigat accidental.
