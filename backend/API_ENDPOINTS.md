# Specificație Tehnică și Catalog Apeluri Backend (API Endpoints & Payloads)

Acest document descrie lista completă a apelurilor HTTP/JSON pe care aplicația web/mobilă ARTERIA le transmite către backend-ul FastAPI, împreună cu structura exactă a payload-urilor (cerere și răspuns), contractul de date și regulile de validare conform `docs/API_CONTRACT.md` și `docs/ARCHITECTURE.md`.

---

## 1. Convenții Globale

- **Format:** `application/json; charset=utf-8`
- **Ordonare coordonate GeoJSON:** `[longitudine, latitudine]` conform RFC 7946 (ex: `[27.584, 47.153]`).
- **Sistem de Coordonate de Referință (CRS):** `EPSG:4326` (WGS84) pentru intrare/ieșire; `EPSG:3844` (Stereo 70) pentru calcule spațiale metrice interne.
- **Timestamp-uri:** ISO 8601 UTC (ex: `2026-10-17T20:00:00Z`).
- **Stări Epistemice Obligatorii:** Orice măsurătoare include statusul cunoașterii:
  - `observed`: date preluate direct din senzori/buclă inductivă/OSM fără transformări speculative.
  - `calculated`: rezultat obținut printr-o formulă deterministă pe graful de rețea.
  - `estimated`: ipoteză sau model calitativ (ex: recomandări de model AI).
  - `unknown`: valoare absentă (`null`) cu explicarea explicită a motivului.

---

## 2. Lista Apelurilor Către Backend

| Metodă | Endpoint | Scop & Rol în Aplicație |
| :--- | :--- | :--- |
| `POST` | `/analyze` | Analizează rețeaua unui cartier/nod, calculează indicatorii și identifică problemele candidate. |
| `POST` | `/propose` | Solicită alternative structurate (Minimală, Moderată, Transformatoare) pentru o problemă dată. |
| `POST` | `/evaluate` | Construiește un scenariu virtual cu intervențiile alese, recalculează indicatorii și generează datele comparative Before/After. |

---

## 3. Detalierea Apelurilor

### 3.1. `POST /analyze`

Trimis atunci când utilizatorul alege un cartier/reper (ex: Podu Roș, Copou) și activează straturile de analiză (mers pe jos, velo, transport public, carosabil).

#### Exemplu Cerere (Request Body)
```json
{
  "area": {
    "city_id": "iasi-ro",
    "area_id": "podu-ros",
    "boundary": {
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
    "boundary_source": "known_area",
    "crs": "EPSG:4326"
  },
  "layers": [
    "roads",
    "walking",
    "cycling",
    "public_transport"
  ],
  "analysis": {
    "network_modes": ["walk", "bike", "drive"],
    "accessibility_thresholds": [
      { "value": 15, "unit": "minute", "mode": "walk" },
      { "value": 10, "unit": "minute", "mode": "bike" }
    ]
  },
  "data_as_of": null
}
```

#### Exemplu Răspuns (Response Body)
```json
{
  "analysis_id": "an_iasi_pr_20261017_01",
  "area": {
    "city_id": "iasi-ro",
    "area_id": "podu-ros",
    "crs": "EPSG:4326"
  },
  "created_at": "2026-10-17T20:45:00Z",
  "indicators": [
    {
      "id": "peak_flow_rate",
      "label": "Debit maxim la vârf (B-dul Socola)",
      "value": 2180,
      "unit": "veh/h",
      "status": "observed",
      "provenance": [
        {
          "source": "Primăria Municipiului Iași / Buclă inductivă",
          "source_version": "2026-10",
          "retrieved_at": "2026-10-17T08:15:00Z",
          "method": "inductive_loop_telemetry_5min_aggregation",
          "crs": "EPSG:4326"
        }
      ],
      "uncertainty": {
        "kind": "sensor_precision",
        "description": "Acuratețe detector buclă estimată la ±3.5%.",
        "interval": [2100, 2250],
        "confidence": 0.95
      }
    },
    {
      "id": "queue_95th_socola",
      "label": "Lungime coadă percentilă 95",
      "value": 340,
      "unit": "metri",
      "status": "calculated",
      "provenance": [
        {
          "source": "Camera Telemetry & Graph Queue Model",
          "source_version": "v1.2",
          "retrieved_at": "2026-10-17T08:15:00Z",
          "method": "shockwave_queue_propagation",
          "crs": "EPSG:3844"
        }
      ],
      "uncertainty": {
        "kind": "model_estimation",
        "description": "Calculat pe baza timpilor de roșu și sosiri în pluton.",
        "interval": [310, 360],
        "confidence": 0.90
      }
    },
    {
      "id": "walk_access",
      "label": "Acces pietonal la servicii în 15 min",
      "value": 68,
      "unit": "%",
      "status": "calculated",
      "provenance": [
        {
          "source": "OpenStreetMap",
          "source_version": "2026-10-01",
          "retrieved_at": "2026-10-17T10:00:00Z",
          "method": "isochrone_pedestrian_network",
          "crs": "EPSG:3844"
        }
      ],
      "uncertainty": {
        "kind": "network_coverage",
        "description": "Trotuarele secundare pot avea clasificări incomplete.",
        "interval": null,
        "confidence": null
      }
    }
  ],
  "issues": [
    {
      "id": "issue-podu-ros-1",
      "label": "Podu Roș Multi-Leg Center #IS-PR-01 (Congestie Critică LOS E/F)",
      "indicator_ids": ["peak_flow_rate", "queue_95th_socola"],
      "geometry": {
        "type": "Point",
        "coordinates": [27.584, 47.153]
      },
      "status": "observed",
      "provenance": [
        {
          "source": "Iași Urban Mobility Monitor",
          "source_version": "2026.Q3",
          "retrieved_at": "2026-10-17T08:15:00Z",
          "method": "level_of_service_hcm2020",
          "crs": "EPSG:4326"
        }
      ],
      "uncertainty": {
        "kind": "congestion_peak",
        "description": "Blocaj recurent în intervalele 07:45-08:45 și 16:30-17:45.",
        "interval": null,
        "confidence": null
      }
    }
  ],
  "layer_availability": [
    { "layer": "roads", "status": "observed", "reason": "Rețea OSM completă." },
    { "layer": "walking", "status": "observed", "reason": "Rețea pietonală disponibilă." },
    { "layer": "cycling", "status": "observed", "reason": "Trasee velo mapate." },
    { "layer": "public_transport", "status": "observed", "reason": "Linii tramvai CTP prezente." }
  ],
  "warnings": []
}
```

---

### 3.2. `POST /propose`

Trimis atunci când utilizatorul a selectat o problemă identificată și dorește ca motorul AI / catalogul de intervenții să genereze cele 3 opțiuni strategice.

#### Exemplu Cerere (Request Body)
```json
{
  "analysis_id": "an_iasi_pr_20261017_01",
  "area": {
    "city_id": "iasi-ro",
    "area_id": "podu-ros"
  },
  "issue_id": "issue-podu-ros-1",
  "intervention_catalog_version": "catalog-1",
  "constraints": {
    "max_affected_area": { "value": 3.5, "unit": "hectare" }
  },
  "requested_alternatives": ["minimal", "moderate", "transformative"]
}
```

#### Exemplu Răspuns (Response Body)
```json
{
  "proposal_set_id": "ps_pr_20261017_01",
  "analysis_id": "an_iasi_pr_20261017_01",
  "model": {
    "provider": "google-cloud-vertex",
    "model_id": "gemini-3.8-pro",
    "generated_at": "2026-10-17T20:46:12Z"
  },
  "alternatives": [
    {
      "level": "minimal",
      "summary": "Sincronizare dinamică semafoare și benzi de preselecție viraj dreapta liber spre Splai.",
      "interventions": [
        {
          "type": "traffic_signal_retiming",
          "geometry": { "type": "Point", "coordinates": [27.584, 47.153] },
          "parameters": {
            "green_extension_socola_sec": 12,
            "right_turn_free_slip_lane": true
          },
          "parameter_units": { "green_extension_socola_sec": "secunde" },
          "affected_feature_ids": ["osm-node-podu-ros-signals"]
        }
      ],
      "rationale": "Rezolvă evacuarea rapidă a fluxului spre Splai fără intervenții pe podul istoric.",
      "expected_impacts": [
        {
          "indicator_id": "queue_95th_socola",
          "direction": "decrease",
          "value": -75,
          "unit": "metri",
          "status": "estimated",
          "provenance": [],
          "uncertainty": {
            "kind": "qualitative_estimate",
            "description": "Necesită evaluare pe graful topologic.",
            "interval": null,
            "confidence": null
          }
        }
      ],
      "assumptions": [
        "Dulapurile de semnalizare permit integrarea senzorilor radar."
      ],
      "validation": {
        "status": "accepted",
        "checks": ["supported_type", "inside_area", "parameters_valid", "no_network_conflicts"]
      }
    },
    {
      "level": "moderate",
      "summary": "Sens giratoriu turbo cu descărcări directe și bandă prioritară CTP Tramvai.",
      "interventions": [
        {
          "type": "turbo_roundabout_conversion",
          "geometry": { "type": "Point", "coordinates": [27.584, 47.153] },
          "parameters": {
            "inner_radius_m": 14,
            "outer_radius_m": 28,
            "tram_priority_barrier": true
          },
          "parameter_units": { "inner_radius_m": "metri", "outer_radius_m": "metri" }
        }
      ],
      "rationale": "Reduce punctele de conflict de la 24 la 8 și asigură tranzitul nestingherit al tramvaiului.",
      "expected_impacts": [
        {
          "indicator_id": "peak_flow_rate",
          "direction": "increase",
          "value": 760,
          "unit": "veh/h",
          "status": "estimated",
          "provenance": [],
          "uncertainty": { "kind": "qualitative_estimate", "description": "Ipoteză de modelare.", "interval": null, "confidence": null }
        }
      ],
      "assumptions": [
        "Podul peste Bahlui suportă lărgirea refugiilor mediane la 2.5m."
      ],
      "validation": {
        "status": "accepted",
        "checks": ["supported_type", "inside_area", "parameters_valid"]
      }
    },
    {
      "level": "transformative",
      "summary": "Nod denivelat Podu Roș: Pasaj subteran Bd. Socola — Str. Palat + Pod pietonal verde peste Bahlui.",
      "interventions": [
        {
          "type": "grade_separated_underpass",
          "geometry": { "type": "LineString", "coordinates": [[27.584, 47.148], [27.584, 47.153], [27.584, 47.158]] },
          "parameters": {
            "underpass_lanes": 4,
            "vertical_clearance_m": 4.8,
            "deck_surface_mode": "tram_pedestrian_only"
          },
          "parameter_units": { "vertical_clearance_m": "metri" }
        }
      ],
      "rationale": "Elimină complet traficul de tranzit din piață, dedicând suprafața transportului public și pietonilor.",
      "expected_impacts": [
        {
          "indicator_id": "queue_95th_socola",
          "direction": "decrease",
          "value": -305,
          "unit": "metri",
          "status": "estimated",
          "provenance": [],
          "uncertainty": { "kind": "qualitative_estimate", "description": "Ipoteză structurală.", "interval": null, "confidence": null }
        }
      ],
      "assumptions": [
        "Studiul geotehnic confirmă viabilitatea fundațiilor sub cota albiei Bahlui."
      ],
      "validation": {
        "status": "accepted",
        "checks": ["supported_type", "inside_area", "parameters_valid"]
      }
    }
  ],
  "rejected_alternatives": [],
  "warnings": [
    "Impacturile estimate sunt ipoteze calitative generate conform catalogului; nu reprezintă rezultate de simulare fizică."
  ]
}
```

---

### 3.3. `POST /evaluate`

Trimis atunci când utilizatorul apasă pe **„Aplică în scenariu și evaluează”** pentru alternativa aleasă. Backend-ul creează un scenariu virtual, recalculează indicatorii pe graful modificat și returnează datele comparative detaliate (Baseline vs. Scenariu cu Delta).

#### Exemplu Cerere (Request Body)
```json
{
  "analysis_id": "an_iasi_pr_20261017_01",
  "area": {
    "city_id": "iasi-ro",
    "area_id": "podu-ros"
  },
  "baseline_id": "baseline_iasi_pr_2024",
  "proposal_set_id": "ps_pr_20261017_01",
  "alternative_level": "moderate",
  "interventions": [
    {
      "type": "turbo_roundabout_conversion",
      "geometry": { "type": "Point", "coordinates": [27.584, 47.153] },
      "parameters": {
        "inner_radius_m": 14,
        "outer_radius_m": 28,
        "tram_priority_barrier": true
      }
    }
  ],
  "evaluation": {
    "indicators": [
      "peak_flow_rate",
      "queue_95th_socola",
      "mean_waiting_time",
      "level_of_service"
    ],
    "traffic_simulation": {
      "requested": false,
      "mode": "none",
      "replay_id": null
    }
  }
}
```

#### Exemplu Răspuns (Response Body)
```json
{
  "evaluation_id": "ev_pr_20261017_moderate_01",
  "scenario_id": "sc_pr_turbo_roundabout",
  "created_at": "2026-10-17T20:47:00Z",
  "baseline": {
    "id": "baseline_iasi_pr_2024",
    "source_snapshot": "osm-iasi-2026-10-01"
  },
  "scenario": {
    "id": "sc_pr_turbo_roundabout",
    "intervention_catalog_version": "catalog-1"
  },
  "comparisons": [
    {
      "indicator_id": "peak_flow_rate",
      "baseline": {
        "value": 2180,
        "unit": "veh/h",
        "status": "observed",
        "provenance": [{ "source": "Buclă inductivă Iași", "source_version": "2026", "retrieved_at": "2026-10-17T08:15:00Z", "method": "inductive_loop", "crs": "EPSG:4326" }],
        "uncertainty": { "kind": "sensor_precision", "description": "±3.5%", "interval": null, "confidence": null }
      },
      "scenario": {
        "value": 2940,
        "unit": "veh/h",
        "status": "calculated",
        "provenance": [{ "source": "ARTERIA Sim Engine", "source_version": "v1.0", "retrieved_at": "2026-10-17T20:47:00Z", "method": "turbo_roundabout_capacity_model", "crs": "EPSG:3844" }],
        "uncertainty": { "kind": "model_calibration", "description": "Calculat pe baza coeficienților Brilon-Bondzio.", "interval": [2800, 3050], "confidence": 0.9 }
      },
      "delta": {
        "value": 760,
        "unit": "veh/h",
        "status": "calculated",
        "provenance": [],
        "uncertainty": { "kind": "delta_confidence", "description": "+34.9% creștere de debit", "interval": null, "confidence": null }
      }
    },
    {
      "indicator_id": "queue_95th_socola",
      "baseline": {
        "value": 340,
        "unit": "metri",
        "status": "calculated",
        "provenance": [{ "source": "Graph Queue Model", "source_version": "v1.2", "retrieved_at": "2026-10-17T08:15:00Z", "method": "queue_shockwave", "crs": "EPSG:3844" }],
        "uncertainty": { "kind": "model_estimation", "description": "Coadă la orele 08:15", "interval": null, "confidence": null }
      },
      "scenario": {
        "value": 140,
        "unit": "metri",
        "status": "calculated",
        "provenance": [{ "source": "ARTERIA Sim Engine", "source_version": "v1.0", "retrieved_at": "2026-10-17T20:47:00Z", "method": "queue_dissipation_rate", "crs": "EPSG:3844" }],
        "uncertainty": { "kind": "model_estimation", "description": "Descărcare continuă pe braț spiralat", "interval": [120, 160], "confidence": 0.85 }
      },
      "delta": {
        "value": -200,
        "unit": "metri",
        "status": "calculated",
        "provenance": [],
        "uncertainty": { "kind": "delta_confidence", "description": "-58.8% reducere coadă", "interval": null, "confidence": null }
      }
    },
    {
      "indicator_id": "mean_waiting_time",
      "baseline": {
        "value": 74.2,
        "unit": "secunde/veh",
        "status": "calculated",
        "provenance": [{ "source": "Telemetry Delay Monitor", "source_version": "v1.0", "retrieved_at": "2026-10-17T08:15:00Z", "method": "delay_webster", "crs": "EPSG:4326" }],
        "uncertainty": { "kind": "delay_calc", "description": "Timp așteptare la coadă", "interval": null, "confidence": null }
      },
      "scenario": {
        "value": 38.0,
        "unit": "secunde/veh",
        "status": "calculated",
        "provenance": [{ "source": "ARTERIA Sim Engine", "source_version": "v1.0", "retrieved_at": "2026-10-17T20:47:00Z", "method": "delay_uninterrupted_flow", "crs": "EPSG:3844" }],
        "uncertainty": { "kind": "delay_calc", "description": "Timp așteptare la intrarea în inel", "interval": [32, 44], "confidence": 0.85 }
      },
      "delta": {
        "value": -36.2,
        "unit": "secunde/veh",
        "status": "calculated",
        "provenance": [],
        "uncertainty": { "kind": "delta_confidence", "description": "-48.8% reducere timp întârziere", "interval": null, "confidence": null }
      }
    }
  ],
  "simulation": {
    "status": "not_requested",
    "mode": "none",
    "run_id": null,
    "started_at": null,
    "completed_at": null,
    "simulator": null,
    "configuration": null,
    "measurements": []
  },
  "warnings": [
    "Indicatorii comparativi au fost calculați pe graful de rețea topologic. Nicio simulare SUMO macroscopică nu a fost fabricată."
  ]
}
```

---

## 4. Coduri de Eroare Returnate de Backend

Conform standardului API, backend-ul returnează erori structurate:

```json
{
  "error": {
    "code": "invalid_area_or_constraints",
    "message": "Zona selectată conține geometrii nesuportate de catalogul activ.",
    "details": [
      {
        "field": "area.boundary",
        "reason": "Poligonul depășește limita maximă configurată de 50 hectare."
      }
    ],
    "request_id": "req_01JABCDEF123456"
  }
}
```

| Cod HTTP | `error.code` | Semnificație |
| :--- | :--- | :--- |
| `400` | `bad_request` | Corpul cererii nu este un JSON valid sau are câmpuri lipsă. |
| `404` | `not_found` | `analysis_id`, `issue_id` sau `baseline_id` nu există în stocarea backend. |
| `409` | `conflict` | Intervenția solicitată intră în conflict fizic cu elemente existente de rețea. |
| `422` | `unprocessable_entity` | Schema sau constrângerile geometrice Pydantic au eșuat. |
| `500` / `503` | `upstream_unavailable` | Furnizorul LLM sau motorul de simulare nu a răspuns în timp util. |
