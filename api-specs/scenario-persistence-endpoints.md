# API Specification: Persistență, Salvare și Export Scenarii

Contractul pentru salvarea, listarea, partajarea și exportul de rapoarte tehnice ale scenariilor configurate de utilizatori.

---

## 1. `POST /api/v1/scenarios`

Salvează scenariul configurat local (intervenții, parametri de reglaj ciclu semaforic, lățimi de bandă, priorități CTP) într-un proiect de planificare persistent.

- **Metodă HTTP:** `POST`
- **Antete (Headers):**
  - `Content-Type: application/json`
  - `Authorization: Bearer <access_token>`

### Payload Cerere (Request Body)
```json
{
  "title": "Optimizare Tranzit Podu Roș — Varianta CTP Prioritar",
  "area_id": "iasi-podu-ros",
  "issue_id": "issue-podu-ros-1",
  "alternative_level": "moderate",
  "tuning_parameters": {
    "green_phase_seconds": 80,
    "ctp_priority_active": true,
    "lane_width_meters": 2.75
  },
  "notes": "Scenariu pregătit pentru ședința Comisiei de Circulație din 24 Octombrie 2026."
}
```

### Răspuns Așteptat (Response Schema - 201 Created)
```json
{
  "id": "sc_saved_9182",
  "share_url": "https://arteria.iasi.ro/app?scenario=sc_saved_9182",
  "created_at": "2026-10-17T18:48:00Z",
  "author": {
    "id": "usr_iasi_09823",
    "name": "Arh. Elena Dumitrescu"
  },
  "status": "draft_municipal"
}
```

### Comportament în Interfață (Frontend UI/UX)
- **Feedback:**
  - Dialog modal / Toast de succes: *„Scenariu salvat cu succes!”* cu buton direct de copiere a link-ului de colaborare (`share_url`).

---

## 2. `GET /api/v1/scenarios/{id}/export`

Generează și descarcă raportul tehnic consolidat în format GeoJSON sau PDF executiv pentru comisiile de urbanism.

- **Metodă HTTP:** `GET`
- **Query Params:**
  - `format` (`geojson` | `pdf` | `json`)
- **Răspuns Așteptat (200 OK):**
  - Fișier binar `application/pdf` sau `application/geo+json` cu header `Content-Disposition: attachment; filename="raport-tehnic-podu-ros-2026.pdf"`.
- **Comportament Frontend:**
  - Butonul de descărcare trece în stare de loading cu bară de progres descărcare; declanșează salvarea nativă prin `URL.createObjectURL(blob)`.
