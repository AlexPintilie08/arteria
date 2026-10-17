# API Specification: Autentificare și Sesiune Utilizator

Acest contract definește mecanismul de autentificare și autorizare pe client pentru planificatori urbani, ingineri de trafic și decidenți municipali în cadrul platformei ARTERIA.

---

## 1. `POST /api/v1/auth/login`

Autentifică un utilizator pe baza credențialelor și returnează token-urile de acces și starea profilului.

- **Metodă HTTP:** `POST`
- **Antete (Headers):**
  - `Content-Type: application/json`
  - `Accept: application/json`

### Payload Cerere (Request Body)
```json
{
  "email": "urbanist.sef@iasi.primaria.ro",
  "password": "SecurePassword#2026",
  "remember_me": true
}
```

### Răspuns Așteptat (Response Schema - 200 OK)
```json
{
  "user": {
    "id": "usr_iasi_09823",
    "name": "Arh. Elena Dumitrescu",
    "email": "urbanist.sef@iasi.primaria.ro",
    "role": "lead_urban_planner",
    "department": "Direcția de Urbanism și Mobilitate Iași",
    "permissions": [
      "analysis:create",
      "scenarios:edit",
      "simulation:run",
      "reports:export"
    ]
  },
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "refresh_token": "d7a8e9f0-21a4-4f88-b765-...",
    "expires_in": 3600,
    "token_type": "Bearer"
  }
}
```

### Comportament în Interfață (Frontend UI/UX)
- **Loading State:**
  - Butonul de submit afișează un spinner (`Lucide: Loader2`), textul devine „Se autentifică…”, iar câmpurile devin `disabled` pentru a preveni dubla trimitere.
- **Erori (401 Unauthorized / 422 Unprocessable):**
  - Câmpul de parolă este golit automat și primește `aria-invalid="true"`.
  - Apare un mesaj inline sub câmp: *„Email sau parolă incorectă. Reîncercați.”*
  - Notificare Toast discretă cu severitate `danger`: *„Autentificare eșuată. Verificați credențialele municipale.”*
- **Erori de rețea / 500 / 503:**
  - Toast persistent cu opțiune de `Retry` (Reîncearcă).
  - Fallback UI: Opțiune de activare imediată a modului „Invitat / Previzualizare Demo (Offline)”.

---

## 2. `GET /api/v1/auth/me`

Validează token-ul JWT stocat și reîmprospătează permisiunile și preferințele locale la inițializarea aplicației web sau mobile.

- **Metodă HTTP:** `GET`
- **Antete (Headers):**
  - `Authorization: Bearer <access_token>`

### Răspuns Așteptat (Response Schema - 200 OK)
```json
{
  "id": "usr_iasi_09823",
  "name": "Arh. Elena Dumitrescu",
  "role": "lead_urban_planner",
  "preferences": {
    "default_neighborhood": "podu-ros",
    "active_layers": ["roads", "cycling", "public_transport"],
    "units_system": "metric",
    "contrast_mode": "high_fidelity_dark"
  }
}
```

### Comportament în Interfață (Frontend UI/UX)
- **Loading State:**
  - Aplicația menține un `AppSplashSkeleton` fără flash-uri albe pe fundalul `#101820`.
- **Eroare 401 (Token Expirat):**
  - Trimitere automată și silențioasă către `/api/v1/auth/refresh`. Dacă refresh-ul eșuează, stocarea locală este curățată și utilizatorul este redirectat către `/login?redirect=/app` cu starea păstrată.

---

## 3. `POST /api/v1/auth/logout`

Revocă sesiunea curentă și invalidează refresh token-ul pe server.

- **Metodă HTTP:** `POST`
- **Payload Cerere:**
```json
{
  "refresh_token": "d7a8e9f0-21a4-4f88-b765-..."
}
```

### Răspuns Așteptat (204 No Content)
- Curăță `localStorage` / `SecureStore` (pe React Native).
- Resetează store-ul Zustand / Context API la starea `guest`.
- Redirectează către `/` cu un toast informativ de succes: *„Sesiunea a fost închisă cu succes.”*
