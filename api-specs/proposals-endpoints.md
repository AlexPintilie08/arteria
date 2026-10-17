# API Specification: Generare și Validare Propuneri de Intervenție

Contractul pentru endpoint-ul `POST /propose`, utilizat de Editorul de Scenarii pentru a obține alternative structurate (Minimală, Moderată, Transformatoare) validate pe catalogul municipal.

---

## 1. `POST /api/v1/propose`

Generează și validează alternative de intervenție urbană conform catalogului de tipuri de intervenție autorizate și constrângerilor de spațiu fizic.

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
  "issue_id": "issue-podu-ros-1",
  "intervention_catalog_version": "catalog-v1-pydantic",
  "constraints": {
    "max_affected_area": { "value": 3.5, "unit": "hectare" },
    "preserve_tram_corridor": true,
    "budget_ceiling_eur": 15000000
  },
  "requested_alternatives": ["minimal", "moderate", "transformative"]
}
```

### Răspuns Așteptat (Response Schema - 200 OK)
```json
{
  "proposal_set_id": "ps_pr01_alt_set",
  "analysis_id": "an_iasi_20261017_pr01",
  "model": {
    "provider": "anthropic-claude-3-7-sonnet",
    "model_id": "urban-spatial-agent-v2",
    "generated_at": "2026-10-17T18:42:00Z"
  },
  "alternatives": [
    {
      "level": "minimal",
      "summary": "Sincronizare dinamică semafoare și preselecție viraj dreapta liber spre Splai Bahlui.",
      "timeframe": "1-2 luni",
      "cost_category": "redus",
      "estimated_budget_eur": 45000,
      "interventions": [
        {
          "type": "signal_timing_optimization",
          "geometry": { "type": "Point", "coordinates": [27.584, 47.153] },
          "parameters": {
            "green_phase_extension_sec": 12,
            "corridor": "B-dul Socola"
          }
        },
        {
          "type": "slip_lane_segregation",
          "geometry": { "type": "LineString", "coordinates": [[27.584, 47.153], [27.586, 47.152]] },
          "parameters": {
            "barrier_type": "flexible_bollards",
            "lane_width_meters": 3.25
          }
        }
      ],
      "rationale": "Eliberează rapid fluxul de viraj spre Splai fără modificări structurale pe pod.",
      "expected_impacts": [
        {
          "indicator_id": "queue_length",
          "direction": "decrease",
          "value": -22.0,
          "unit": "%",
          "status": "estimated",
          "provenance": [],
          "uncertainty": {
            "kind": "qualitative_estimate",
            "description": "Ipoteză pre-simulare bazată pe ecuația Webster de capacitate.",
            "interval": null,
            "confidence": null
          }
        }
      ],
      "assumptions": [
        "Infrastructura cablată a semafoarelor suportă controller adaptiv cu protocol VLog."
      ],
      "validation": {
        "status": "accepted",
        "checks": ["supported_type", "inside_area", "parameters_valid", "tram_conflict_free"]
      }
    },
    {
      "level": "moderate",
      "summary": "Sens giratoriu turbo cu descărcări directe și bandă prioritară CTP Tramvai.",
      "timeframe": "6-9 luni",
      "cost_category": "mediu",
      "estimated_budget_eur": 420000,
      "interventions": [],
      "rationale": "Reduce punctele de conflict de la 24 la 8 și asigură tranzitul nestingherit al tramvaiului.",
      "expected_impacts": [],
      "assumptions": [],
      "validation": {
        "status": "accepted",
        "checks": ["supported_type", "inside_area", "parameters_valid"]
      }
    },
    {
      "level": "transformative",
      "summary": "Nod denivelat Podu Roș: Pasaj subteran Bd. Socola — Str. Palat + Pod pietonal verde.",
      "timeframe": "24-30 luni",
      "cost_category": "ridicat",
      "estimated_budget_eur": 18500000,
      "interventions": [],
      "rationale": "Elimină traficul greu de tranzit de la suprafața râului Bahlui.",
      "expected_impacts": [],
      "assumptions": [],
      "validation": {
        "status": "accepted",
        "checks": ["supported_type", "inside_area", "parameters_valid"]
      }
    }
  ],
  "rejected_alternatives": [],
  "warnings": [
    "Impacturile estimate sunt ipoteze calitative. Efectele măsurabile necesită rularea evaluării / simulării."
  ]
}
```

### Comportament în Interfață (Frontend UI/UX)
- **Loading State:**
  - Taburile de nivel (Minimală / Moderată / Transformatoare) afișează badge-ul de „Calcul generativ…”.
  - Utilizatorul poate naviga între alte secțiuni fără ca cererea în fundal să blocheze UI-ul (`AbortController` activat doar dacă utilizatorul schimbă cartierul).
- **Error State (409 Incompatible Scenario):**
  - Când propunerea e respinsă de validatoarele geometrice, se afișează `rejected_alternatives` cu motivul tehnic specific (ex: *„Lățimea minimă a culoarului de tramvai ar fi încălcată”*), oferind buton de relaxare a constrângerilor.
