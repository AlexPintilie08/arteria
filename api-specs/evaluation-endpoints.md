# API Specification: Evaluare Scenarii și Simulare Comparativă (SUMO)

Contractul pentru endpoint-ul `POST /evaluate`, utilizat de Matricea Comparativă Înainte / După pentru recalcularea indicatorilor și coordonarea execuțiilor SUMO.

---

## 1. `POST /api/v1/evaluate`

Calculează matricea de comparație între situația inițială (Baseline) și scenariul virtual propus pe aceeași topologie, cu sau fără simulare microscopică de trafic SUMO.

- **Metodă HTTP:** `POST`
- **Antete (Headers):**
  - `Content-Type: application/json`
  - `Authorization: Bearer <access_token>`

### Payload Cerere (Request Body)
```json
{
  "analysis_id": "an_iasi_20261017_pr01",
  "area": {
    "city_id": "iasi-ro",
    "area_id": "iasi-podu-ros"
  },
  "baseline_id": "baseline_iasi_2024_osm_q3",
  "proposal_set_id": "ps_pr01_alt_set",
  "alternative_level": "minimal",
  "tuning_parameters": {
    "green_phase_seconds": 75,
    "ctp_priority_active": true,
    "lane_width_meters": 2.5
  },
  "interventions": [
    {
      "type": "signal_timing_optimization",
      "geometry": { "type": "Point", "coordinates": [27.584, 47.153] },
      "parameters": { "green_phase_extension_sec": 15 }
    }
  ],
  "evaluation": {
    "indicators": [
      "flow_capacity",
      "p95_queue_length",
      "avg_vehicle_delay",
      "level_of_service"
    ],
    "traffic_simulation": {
      "requested": true,
      "mode": "live",
      "replay_id": null,
      "seed": 4092,
      "duration_seconds": 3600
    }
  }
}
```

### Răspuns Așteptat (Response Schema - 200 OK)
```json
{
  "evaluation_id": "ev_iasi_pr01_20261017",
  "scenario_id": "sc_podu_ros_min_tuned",
  "created_at": "2026-10-17T18:45:00Z",
  "baseline": {
    "id": "baseline_iasi_2024_osm_q3",
    "source_snapshot": "osm-iasi-2026-10-01"
  },
  "scenario": {
    "id": "sc_podu_ros_min_tuned",
    "intervention_catalog_version": "catalog-v1-pydantic"
  },
  "comparisons": [
    {
      "indicator_id": "flow_capacity",
      "label": "Debit maxim la vârf (Flow Rate)",
      "baseline": {
        "value": 2180,
        "unit": "veh/h",
        "status": "calculated",
        "provenance": [{ "source": "Bucle inductive Podu Roș", "method": "capacity_hcm2020", "crs": "EPSG:3844", "retrieved_at": "2026-10-02T10:00:00Z", "source_version": "v1" }],
        "uncertainty": { "kind": "tolerance", "description": "±30 veh/h", "interval": [2150, 2210], "confidence": 0.95 }
      },
      "scenario": {
        "value": 2520,
        "unit": "veh/h",
        "status": "calculated",
        "provenance": [{ "source": "Model rețea topologică", "method": "capacity_hcm2020", "crs": "EPSG:3844", "retrieved_at": "2026-10-17T18:45:00Z", "source_version": "v1" }],
        "uncertainty": { "kind": "tolerance", "description": "±45 veh/h", "interval": [2475, 2565], "confidence": 0.9 }
      },
      "delta": {
        "value": 340,
        "unit": "veh/h",
        "status": "calculated",
        "provenance": [],
        "uncertainty": { "kind": "computed_delta", "description": "Diferență netă pozitivă (+15.6%)", "interval": null, "confidence": null }
      }
    },
    {
      "indicator_id": "avg_vehicle_delay",
      "label": "Timp mediu de așteptare (Delay)",
      "baseline": {
        "value": 74.2,
        "unit": "secunde/veh",
        "status": "calculated",
        "provenance": [{ "source": "Webster Delay Formulation", "method": "signal_cycle_analysis", "crs": "EPSG:3844", "retrieved_at": "2026-10-02T10:00:00Z", "source_version": "v1" }],
        "uncertainty": { "kind": "tolerance", "description": "±2.5 s", "interval": [71.7, 76.7], "confidence": 0.95 }
      },
      "scenario": {
        "value": 54.8,
        "unit": "secunde/veh",
        "status": "calculated",
        "provenance": [{ "source": "Webster Delay Formulation", "method": "signal_cycle_analysis", "crs": "EPSG:3844", "retrieved_at": "2026-10-17T18:45:00Z", "source_version": "v1" }],
        "uncertainty": { "kind": "tolerance", "description": "±3.0 s", "interval": [51.8, 57.8], "confidence": 0.9 }
      },
      "delta": {
        "value": -19.4,
        "unit": "secunde/veh",
        "status": "calculated",
        "provenance": [],
        "uncertainty": { "kind": "computed_delta", "description": "Reducere netă timp așteptare (-26.1%)", "interval": null, "confidence": null }
      }
    }
  ],
  "simulation": {
    "status": "completed",
    "mode": "live",
    "run_id": "sumo_run_98412_seed4092",
    "started_at": "2026-10-17T18:44:10Z",
    "completed_at": "2026-10-17T18:44:58Z",
    "simulator": {
      "name": "Eclipse SUMO",
      "version": "1.21.0"
    },
    "configuration": {
      "net_file": "iasi_podu_ros_scenario_min.net.xml",
      "routes_file": "peak_morning_ctp_demand.rou.xml",
      "step_length": 0.5
    },
    "measurements": []
  },
  "warnings": []
}
```

### Comportament în Interfață (Frontend UI/UX)
- **Stare Simulare în Curs (Polling / WebSocket SSE):**
  - Bara de simulare afișează: `SUMO Rulare live: pasul 1800/3600 (50%)` cu feedback grafic în timp real.
  - Nu blochează restul taburilor; utilizatorul poate continua explorarea.
- **Dacă simularea este mod `replay`:**
  - Badge-ul de simulare indică explicit galben: *„Replay din 02.10.2026 · ID: sumo_run_98412”*.
- **Eroare SUMO (504 Timeout / 500 Crash):**
  - Rămân afișate valorile calculate matematic (Webster/HCM) cu eticheta `calculated`, iar la secțiunea de simulare apare un card distinct de avertisment: *„Simularea microscopică a eșuat. Se afișează calculul topologic determinist.”*
