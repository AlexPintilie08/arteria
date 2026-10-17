# API Specification: Motor de Simulare Urbană & Modele Analitice (SUMO & Webster/HCM)

Acest document specifică contractul tehnic dintre interfața utilizator (Frontend Web/Mobile) și componenta de calcul/simulare spațială (`sim`), acoperind cele două căi de evaluare:
1. **Modele Analitice Deterministe:** Calcul instantaneu în browser/backend pe baza formulelor de capacitate Webster și HCM 2020.
2. **Simulare Microscopică Eclipse SUMO:** Execuție opțională a motorului microscopic prin protocolul TraCI/libsumo, cu raportare transparentă a modului (Live vs. Replay).

---

## 1. `POST /api/v1/simulation/sumo/run`

Inițiază o rulare microscopică SUMO pentru un coridor reconfigurat (ex. nodul Podu Roș cu pasaj subteran sau turbo-giratoriu).

- **Metodă HTTP:** `POST`
- **Antete (Headers):**
  - `Content-Type: application/json`
  - `Authorization: Bearer <access_token>`

### Payload Cerere (Request Body)
```json
{
  "corridor_id": "podu-ros-is01",
  "scenario_level": "moderate",
  "simulation_config": {
    "network_mode": "multimodal_tram_priority",
    "seed": 4092,
    "step_length_seconds": 0.5,
    "duration_seconds": 3600,
    "warmup_seconds": 600
  },
  "tuning_parameters": {
    "green_phase_seconds": 75,
    "ctp_priority_active": true,
    "lane_width_meters": 2.50,
    "traffic_demand_regime": "peak_morning",
    "load_factor_percent": 105
  },
  "interventions": [
    {
      "type": "turbo_roundabout",
      "geometry_geojson": {
        "type": "Point",
        "coordinates": [27.584, 47.153]
      },
      "parameters": {
        "inner_radius": 14.0,
        "circulating_lanes": 2,
        "slip_lane_splai": true
      }
    }
  ]
}
```

### Răspuns Așteptat (Response Schema - 202 Accepted)
```json
{
  "job_id": "sim_job_sumo_20261017_4092",
  "status": "queued",
  "stream_url": "/api/v1/simulation/sumo/stream/sim_job_sumo_20261017_4092",
  "estimated_duration_sec": 8.5,
  "engine": {
    "name": "Eclipse SUMO",
    "version": "1.21.0",
    "execution_mode": "cpu_microscopic_traci"
  }
}
```

---

## 2. Server-Sent Events (SSE) Telemetrie Rulare: `GET /api/v1/simulation/sumo/stream/{job_id}`

Transmite cadrele de progres către interfață în timp real pentru a actualiza bara de progres și indicatorii intermediari din panoul de comparare.

### Evenimente SSE
```text
event: progress
data: {"job_id":"sim_job_sumo_20261017_4092","current_step":900,"total_steps":3600,"vehicles_active":342,"teleports":0}

event: complete
data: {
  "job_id": "sim_job_sumo_20261017_4092",
  "status": "completed",
  "execution_mode": "live",
  "seed": 4092,
  "summary": {
    "total_vehicles_served": 2940,
    "avg_delay_seconds": 38.0,
    "p95_queue_meters": 140,
    "tram_commercial_speed_kmh": 14.1,
    "emissions_co2_kg": 115.4
  },
  "replay_token": "replay_sumo_podu_ros_mod_20261017"
}
```

---

## 3. `POST /api/v1/simulation/analytical/evaluate`

Evaluează matematic scenariul în sub 15ms utilizând formulările Webster și HCM 2020 (fără a porni SUMO). Aceasta este calea primară de execuție în interfață pentru un feedback instantaneu în timpul ajustării sliderelor.

### Payload Cerere
```json
{
  "corridor_id": "podu-ros-is01",
  "baseline_metrics": {
    "flow_capacity": 2180,
    "avg_delay": 74.2,
    "p95_queue": 340,
    "level_of_service": 5
  },
  "tuning_parameters": {
    "green_phase_seconds": 85,
    "ctp_priority_active": true,
    "lane_width_meters": 2.75,
    "traffic_demand_regime": "peak_morning",
    "load_factor_percent": 100
  },
  "alternative_level": "moderate"
}
```

### Răspuns Așteptat (200 OK)
```json
{
  "status": "calculated",
  "model": "Webster Delay + HCM 2020 Capacity Matrix",
  "metrics": {
    "flow_capacity": {
      "baseline": 2180,
      "scenario": 2940,
      "delta": 760,
      "unit": "veh/h",
      "percent_change": 34.8
    },
    "avg_delay": {
      "baseline": 74.2,
      "scenario": 38.0,
      "delta": -36.2,
      "unit": "secunde/veh",
      "percent_change": -48.7
    },
    "p95_queue": {
      "baseline": 340,
      "scenario": 140,
      "delta": -200,
      "unit": "metri",
      "percent_change": -58.8
    },
    "level_of_service": {
      "baseline": "LOS E",
      "scenario": "LOS C",
      "delta": -2,
      "unit": "clasa (A-F)"
    }
  },
  "epistemic_status": "deterministic_calculation",
  "warnings": []
}
```

---

## 4. Comportament în Interfață (Frontend UI/UX)
- **Feedback Haptic & Vizual:** La mișcarea sliderelor de fază verde sau factor de încărcare, valorile calculate sunt actualizate instantaneu prin calcul local (optimistic UI), urmat de sincronizarea cu backend-ul.
- **Etichetare Onestă:**
  - Dacă rularea provine din baza de date fără execuție proaspătă: Badge vizual galben: `Replay · ID: replay_sumo_podu_ros_mod_20261017`.
  - Dacă simularea microscopică este în curs: Indicator rotativ cu numărul de vehicule active și timpul rămas estimat.
  - Dacă SUMO nu este configurat pe mașină: Rămâne activ calculul determinist Webster/HCM cu eticheta `calculated` și explicația sursei în panoul de inspecție.
