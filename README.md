# Neonatal Care — Backend (FastAPI) & Dashboard API Guide

REST API for the Neonatal Care System: authentication, role-based access control, baby & incubator
management, vital-sign monitoring, parent-involvement tracking, reporting (incl. PDF), and audit logging.

This single document serves two audiences:
- **Backend developers** — [Tech stack](#tech-stack), [Architecture](#architecture), [Running locally](#running-the-backend-locally).
- **Dashboard / client developers** — everything from [API quick facts](#api-quick-facts) onward is a
  complete integration contract (auth, every endpoint, exact request/response JSON, enums, errors,
  business rules). You can build a client without reading the source.

→ See the [root README](../README.md) for the full-stack overview and architecture.

> **Live, always-current reference:** the running backend serves Swagger UI at **`{BASE_URL}/docs`**
> and ReDoc at **`{BASE_URL}/redoc`** — try real requests there with your token.

---

## Tech Stack

| Concern | Choice |
|---|---|
| Framework | FastAPI (async) |
| ORM | SQLAlchemy 2.0 (async) + Alembic |
| Validation | Pydantic v2 |
| Auth | JWT (python-jose), bcrypt via Passlib |
| Database | PostgreSQL (asyncpg driver) |
| Storage | Local filesystem (S3-ready) |

---

## Architecture

A clean layered design — each request flows top-down, each layer depends only on the one below:

```
api/v1/        HTTP routing, dependency injection, RBAC guards
   │
services/      business logic, score/warning calculation, audit hooks
   │
repositories/  data access (SQLAlchemy queries)
   │
models/        ORM entities  ·  schemas/ Pydantic request/response models
```

`core/` holds cross-cutting concerns: `config.py` (settings), `security.py` (hashing + JWT),
`database.py` (async session).

```
app/
├── api/v1/        auth, users, incubators, babies, monitoring,
│                  involvement, reports, dashboard, audit
├── core/          config · security · database
├── models/        user, incubator, baby, parent, assignment,
│                  monitoring, involvement, audit
├── schemas/       pydantic models per domain
├── services/      one module per domain + audit_service, storage_service
├── repositories/  data-access per aggregate
└── main.py        app factory, CORS, static /uploads, router mounts
```

---

## Running the backend locally

### Prerequisites
- Python 3.12+
- PostgreSQL 14+

### Install
```bash
python -m venv venv
venv\Scripts\activate          # Windows  (source venv/bin/activate on *nix)
pip install -r requirements.txt
```

### Database
```bash
createdb neonatal
psql -d neonatal -f database/schema.sql
psql -d neonatal -f database/seed_data.sql
```

### Environment — `backend/.env`
```env
SECRET_KEY=change-me-to-a-long-random-string
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/neonatal
# optional (defaults shown)
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
STORAGE_BACKEND=local
STORAGE_LOCAL_PATH=./uploads
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5000
```

| Var | Required | Notes |
|---|---|---|
| `SECRET_KEY` | ✅ | JWT signing secret |
| `DATABASE_URL` | ✅ | Must use the `postgresql+asyncpg://` scheme |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | — | Default `480` (8h) |
| `ALLOWED_ORIGINS` | — | Comma-separated CORS origins (**add your dashboard's origin here**) |

### Run
```bash
uvicorn app.main:app --reload --port 8000
```
- Swagger UI → http://localhost:8000/docs
- ReDoc → http://localhost:8000/redoc
- Health → http://localhost:8000/health

### Migrations (Alembic) & tests
```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
pytest
```

---
---

# Dashboard API Guide

Everything below is the **integration contract** for building a dashboard / web client.

## API quick facts

| | |
|---|---|
| **Base URL** | `http://localhost:8000` (dev). All endpoints below are relative to this. |
| **API prefix** | every endpoint starts with `/api/v1` (except `/health`, `/uploads`, `/docs`). |
| **Content-Type** | `application/json`, except photo upload (multipart). |
| **Auth** | JWT Bearer token in the `Authorization` header (see [Authentication](#authentication)). |
| **IDs** | All resource IDs are **UUID** strings. |
| **Dates/times** | ISO‑8601 with offset, e.g. `2026-05-16T09:30:00+07:00`. `birth_date` is `YYYY-MM-DD`. |
| **Numbers** | Temperatures, weights, SpO₂ are JSON numbers (decimals). |
| **Health check** | `GET /health` → `{"status":"ok","version":"1.0.0"}` (no auth). |

### CORS (read before you start)
The API uses `allow_credentials: true` and only permits origins listed in the backend's
`ALLOWED_ORIGINS` env var (comma-separated). **Add your dashboard's origin** (e.g.
`http://localhost:5173`) there, or browser requests are blocked:
```
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```
> A server-side **Backend-for-Frontend (BFF)** proxy avoids CORS entirely and keeps the JWT off the
> browser (recommended for production). If you call the API directly from the browser, store the
> token carefully.

---

## Authentication

JWT, algorithm **HS256**, **expires in 8 hours** (480 min). Payload: `{ "sub": <user_id>, "role": <role>, "exp": <unix-ts> }`.

### Log in
```
POST /api/v1/auth/login
Content-Type: application/json

{ "email": "admin@neonatal.rs", "password": "Password123!" }
```
**200 OK**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "aaaaaaaa-0001-0001-0001-000000000001",
  "full_name": "Administrator Sistem",
  "role": "admin"
}
```
**401** `{ "detail": "Email atau password salah" }` on bad credentials.

### Use the token — send on every authenticated request
```
Authorization: Bearer <access_token>
```

### Who am I — `GET /api/v1/auth/me` *(any role)*
```json
{
  "id": "aaaaaaaa-0001-0001-0001-000000000001",
  "role": "admin",
  "email": "admin@neonatal.rs",
  "full_name": "Administrator Sistem",
  "is_active": true,
  "created_at": "2026-01-10T08:00:00+00:00"
}
```

### Token expiry / 401 handling
Missing, invalid, or expired tokens return **401**. Catch 401 globally and redirect to login.

---

## Roles & access control (RBAC)

Three roles: **`admin`**, **`perawat`** (nurse), **`dokter`** (doctor). Each endpoint is guarded:

| Guard | Who passes |
|---|---|
| **Any** | any authenticated user |
| **Perawat/Admin** | nurse or admin — all data *entry* |
| **Admin** | admin only — user management & audit log |

A logged-in user lacking the role gets **403** `{ "detail": "Akses tidak diizinkan untuk role ini" }`.

| Area | Read | Write |
|---|---|---|
| Dashboard, incubators, babies, monitoring, involvement, reports | **Any** | **Perawat/Admin** |
| Incubator create/update | Any | **Admin** |
| Users, Audit log | — | **Admin** |

> Doctors (`dokter`) are effectively **read-only**: view dashboards, babies, reports, trends, and
> export PDFs, but cannot create/update records.

---

## Conventions

- **Pagination:** list endpoints accept `skip` (default `0`) and `limit` (monitoring/involvement
  default `50`, audit default `100`). Records come back newest-first.
- **Error shape (HTTP errors):** `{ "detail": "message" }` with status `400/401/403/404/413/415`.
- **Validation errors (422):** `{ "detail": [ { "loc": ["body","spo2"], "msg": "...", "type": "..." } ] }`.
- **Empty success (204 No Content):** password reset, deactivate user, discharge baby.

---

## Enums (use these exact string values)

| Enum | Values |
|---|---|
| `role` | `admin` · `perawat` · `dokter` |
| `gender` | `laki_laki` · `perempuan` |
| Incubator `status` | `kosong` (empty) · `terisi` (occupied) · `warning` · `tidak_tersedia` (unavailable) |
| `vital_status` | `normal` · `warning` |
| Involvement `skor_kategori` | `Rendah` · `Sedang` · `Baik` · `Sangat Baik` |
| Audit `action` | `LOGIN` · `CREATE` · `UPDATE` · `DELETE` · `UPLOAD_PHOTO` · `EXPORT` |

---

## Endpoints

### Dashboard — `GET /api/v1/dashboard` *(Any)*
Single call powering the home screen: aggregate counts + every incubator with its baby and latest vitals.
```json
{
  "stats": { "total": 7, "terisi": 3, "kosong": 3, "warning": 1, "tidak_tersedia": 0 },
  "incubators": [
    {
      "incubator_id": "bbbbbbbb-...-01", "incubator_no": "01",
      "location": "NICU Ruang A", "status": "terisi",
      "current_baby": {
        "baby_id": "cccccccc-...-01", "baby_name": "Ahmad Rizki",
        "age_in_days": 407, "birth_weight": 2400.00,
        "assigned_at": "2025-05-12T09:00:00+07:00"
      },
      "latest_vitals": {
        "suhu_bayi": 37.0, "heart_rate": 127, "spo2": 98.50,
        "observation_time": "2025-05-16T14:00:00+07:00", "vital_status": "normal"
      }
    }
  ]
}
```
`current_baby` and `latest_vitals` are `null` for empty incubators.

### Incubators
| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/api/v1/incubators` | Any | List all (+ current baby) |
| GET | `/api/v1/incubators/available` | Any | Only `kosong` incubators (assignment dropdown) |
| GET | `/api/v1/incubators/{incubator_id}` | Any | One incubator + current baby |
| POST | `/api/v1/incubators` | Admin | Create — `{ "incubator_no":"08", "location":"NICU Ruang C" }` |
| PUT | `/api/v1/incubators/{incubator_id}` | Admin | Update — `{ "location":"...", "status":"tidak_tersedia" }` (both optional) |

**Detail response:**
```json
{
  "incubator_id": "bbbbbbbb-...-01", "incubator_no": "01", "location": "NICU Ruang A",
  "status": "terisi", "created_at": "...", "updated_at": "...",
  "current_baby": {
    "baby_id": "cccccccc-...-01", "baby_name": "Ahmad Rizki",
    "birth_date": "2025-05-12T00:00:00+00:00", "assigned_at": "2025-05-12T09:00:00+07:00"
  }
}
```

### Babies
| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/api/v1/babies` | Any | List (basic) |
| GET | `/api/v1/babies/{baby_id}` | Any | Full detail (+ parent, assignment, latest vitals) |
| POST | `/api/v1/babies` | Perawat/Admin | Register baby + parent + assign to incubator |
| PUT | `/api/v1/babies/{baby_id}` | Perawat/Admin | Update name / weight / clinical notes |
| POST | `/api/v1/babies/{baby_id}/discharge` | Perawat/Admin | Discharge (frees incubator) → **204** |

**Register body** (parent created in the same call; `incubator_id` must be a `kosong` incubator):
```json
{
  "baby_name": "Bayi Ny. Sari", "gender": "perempuan", "birth_date": "2026-06-20",
  "birth_weight": 2100.0, "birth_length": 45.0, "gestational_age": 34,
  "birth_type": "Caesar", "clinical_notes": "Prematur, observasi ketat",
  "parent": {
    "mother_name": "Sari Dewi", "father_name": "Andi", "mother_phone": "081234567890",
    "mother_medical_history": null, "birth_history": null,
    "delivery_history": null, "additional_notes": null
  },
  "incubator_id": "bbbbbbbb-...-03"
}
```
**Baby detail response** (also from register/update):
```json
{
  "baby_id": "cccccccc-...-01", "baby_name": "Ahmad Rizki", "gender": "laki_laki",
  "birth_date": "2025-05-12", "birth_weight": 2400.0, "birth_length": 47.0,
  "gestational_age": 36, "birth_type": "Normal", "clinical_notes": "...",
  "is_active": true, "created_at": "...", "age_in_days": 407,
  "parent": {
    "parent_id": "...", "mother_name": "Rina Dewi", "father_name": "Budi Rizki",
    "mother_phone": "0812...", "mother_medical_history": null,
    "birth_history": null, "delivery_history": null, "additional_notes": null
  },
  "current_assignment": {
    "assignment_id": "...", "incubator_id": "bbbbbbbb-...-01", "incubator_no": "01",
    "location": "NICU Ruang A", "assigned_at": "2025-05-12T09:00:00+07:00",
    "assigned_by_name": "Siti Aisyah"
  },
  "latest_vitals": { /* MonitoringSummary — same vital fields as a monitoring record + vital_status */ }
}
```

### Monitoring (vital signs — 8-Pillar clinical fields)
| Method | Path | Role | Purpose |
|---|---|---|---|
| POST | `/api/v1/babies/{baby_id}/monitoring` | Perawat/Admin | Record an observation |
| GET | `/api/v1/babies/{baby_id}/monitoring?skip=0&limit=50` | Any | History (newest first) |
| POST | `/api/v1/monitoring/{monitoring_id}/photo` | Perawat/Admin | Attach a photo (multipart) |

**Create body** — only `observation_time` is required; send whatever was measured:
```json
{
  "observation_time": "2026-06-22T10:00:00+07:00",
  "suhu_bayi": 36.8, "suhu_inkubator": 33.5, "kelembapan_inkubator": 55.0,
  "heart_rate": 128, "respiratory_rate": 48, "spo2": 98.0,
  "expression_score": 3, "movement_score": 4,
  "pain_score": 1, "sleep_duration_min": 120, "sleep_quality": 4, "agitation_episodes": 0,
  "catatan": "Bayi tenang"
}
```
| Field | Unit / range | Pillar |
|---|---|---|
| `suhu_bayi`, `suhu_inkubator` | °C | 1 / 2 |
| `kelembapan_inkubator` | % RH | 7 (incubator environment) |
| `heart_rate` | bpm | 1 |
| `respiratory_rate` | breaths/min | 1 |
| `spo2` | % | 1 |
| `expression_score`, `movement_score` | 1–5 | 6 (proxy) |
| `pain_score` | 0–7 (NIPS) | 6 |
| `sleep_duration_min` | minutes | 5 |
| `sleep_quality` | 1–5 | 5 |
| `agitation_episodes` | count | 5 |

**201 Created** — response adds server fields + computed `vital_status`:
```json
{
  "monitoring_id": "...", "baby_id": "...", "recorded_by": "...", "recorder_name": "Siti Aisyah",
  "observation_time": "2026-06-22T10:00:00+07:00",
  "suhu_bayi": 36.8, "suhu_inkubator": 33.5, "kelembapan_inkubator": 55.0,
  "heart_rate": 128, "respiratory_rate": 48,
  "spo2": 98.0, "expression_score": 3, "movement_score": 4,
  "pain_score": 1, "sleep_duration_min": 120, "sleep_quality": 4, "agitation_episodes": 0,
  "catatan": "Bayi tenang", "foto_url": null, "vital_status": "normal",
  "created_at": "2026-06-22T03:00:00+00:00"
}
```
Out-of-range scores → **422**.

**Photo upload** — `multipart/form-data`, field **`file`**, JPEG/PNG/WebP, **max 5 MB**:
```
POST /api/v1/monitoring/{monitoring_id}/photo
file=<binary>
```
**200** `{ "monitoring_id": "...", "foto_url": "/uploads/<baby_id>/<monitoring_id>.jpg" }`
Display at **`{BASE_URL}{foto_url}`** (static mount). Errors: **415** (type), **413** (> 5 MB).

### Parent Involvement (Pillar 8 — FICare)
| Method | Path | Role | Purpose |
|---|---|---|---|
| POST | `/api/v1/babies/{baby_id}/involvement` | Perawat/Admin | Record an assessment |
| GET | `/api/v1/babies/{baby_id}/involvement?skip=0&limit=50` | Any | History (newest first) |
| GET | `/api/v1/babies/{baby_id}/involvement/summary` | Any | Aggregated summary |

**Create body** — the 8 FICare sub-domains are each rated **0–4** (`0`=none … `4`=consistent);
durations are optional/informational:
```json
{
  "observation_time": "2026-06-22T11:00:00+07:00",
  "durasi_menyusui": 20, "durasi_interaksi": 45,
  "presence_score": 4, "physical_interaction_score": 4, "feeding_participation_score": 3,
  "care_participation_score": 3, "knowledge_score": 3, "communication_score": 3,
  "emotional_readiness_score": 3, "discharge_readiness_score": 2,
  "catatan": "Ibu aktif", "kondisi_bayi": "Tenang"
}
```
| Domain field | Meaning |
|---|---|
| `presence_score` | Kehadiran (visit frequency/duration) |
| `physical_interaction_score` | Sentuhan, menggendong, kangaroo care |
| `feeding_participation_score` | Partisipasi menyusui / ASI perah |
| `care_participation_score` | Ganti popok, kebersihan, menenangkan |
| `knowledge_score` | Pemahaman kondisi & rencana perawatan |
| `communication_score` | Keterlibatan saat diskusi klinis |
| `emotional_readiness_score` | Kecemasan & kepercayaan diri |
| `discharge_readiness_score` | Kompetensi perawatan & kesadaran darurat |

**201 Created** — server computes the **Parent Engagement Index (PEI)** and category:
```json
{
  "involvement_id": "...", "baby_id": "...", "recorded_by": "...", "recorder_name": "Siti Aisyah",
  "observation_time": "2026-06-22T11:00:00+07:00",
  "durasi_menyusui": 20, "durasi_interaksi": 45,
  "presence_score": 4, "physical_interaction_score": 4, "feeding_participation_score": 3,
  "care_participation_score": 3, "knowledge_score": 3, "communication_score": 3,
  "emotional_readiness_score": 3, "discharge_readiness_score": 2,
  "catatan": "Ibu aktif",
  "skor_keterlibatan": 78, "skor_kategori": "Sangat Baik",
  "kondisi_bayi": "Tenang", "created_at": "2026-06-22T04:00:00+00:00"
}
```
Each domain ∈ 0–4 (else **422**). **PEI = round(sum of 8 domains / 32 × 100)**.

**Summary** (`/summary`):
```json
{
  "total_sessions": 4, "avg_skor": 71.8,
  "avg_durasi_menyusui": 15.0, "avg_durasi_interaksi": 37.5,
  "latest_skor": 78, "latest_kategori": "Sangat Baik"
}
```

### Monitoring Bayi — instrumen observasi (7 pilar / 48 item)
Instrumen observasi perawatan bayi prematur (ditampilkan di UI sebagai **"Monitoring Bayi"**):
**48 item** dalam **7 pilar**, tiap item skor **0–3** (3 = sesuai standar … 0 = penyimpangan berat).
Katalog item bersifat tetap dan di-serve oleh API. _(Aspek "kerjasama dengan keluarga" tidak termasuk
di sini — sudah ditangani modul **Keterlibatan Orang Tua**.)_

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/api/v1/observation/catalog` | Any | Katalog 7 pilar + 48 item (untuk membangun form) |
| POST | `/api/v1/babies/{baby_id}/observation` | Perawat/Admin | Simpan satu sesi observasi |
| GET | `/api/v1/babies/{baby_id}/observation?skip&limit` | Any | Riwayat (terbaru dulu) |

**Katalog** (`/observation/catalog`) → `{ pillars: [{ key, label, items: [{ item_code, text }] }], total_items: 48, max_total: 144 }`.
`item_code` berformat `"{pillar_key}_{n}"` (mis. `tidur_1`, `kulit_8`).

**Create body** — `scores` adalah map `item_code → 0..3` (item yang tak diisi dihitung 0):
```json
{
  "observation_time": "2026-07-07T09:00:00+07:00",
  "scores": { "tidur_1": 3, "tidur_2": 2, "nyeri_4": 1, "kulit_1": 0 },
  "catatan": "Kulit ada iritasi plester"
}
```
**201 Created** — server menghitung skor per pilar, total, kategori, dan alarm:
```json
{
  "observation_id": "...", "baby_id": "...", "recorded_by": "...", "recorder_name": "Siti Aisyah",
  "observation_time": "2026-07-07T09:00:00+07:00",
  "scores": { "tidur_1": 3, "...": 0 }, "catatan": "...",
  "total_score": 108, "max_total": 144, "percentage": 75.0, "category": "Baik",
  "pillars": [ { "key": "tidur", "label": "Menjaga Masa Tidur Bayi", "score": 20, "max": 24, "percentage": 83.3 }, "…7 pilar" ],
  "alarms": [ { "item_code": "kulit_1", "text": "Kulit utuh tanpa luka", "pillar_label": "Perlindungan Kulit", "score": 0 } ],
  "created_at": "2026-07-07T02:00:00+00:00"
}
```
- **Kategori** (dari persentase total): `≥85` Sangat Baik · `70–84` Baik · `55–69` Cukup · `40–54` Kurang · `<40` Sangat Kurang.
- **Alarm** = item dengan skor 0/1. Ada item skor **0** → status inkubator dinaikkan ke `warning`.
- Untuk dashboard: gunakan `pillars[].percentage` sebagai delapan sumbu **radar/spider chart**.

### Reports
| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/api/v1/babies/{baby_id}/report` | Any | Full report payload (JSON) |
| GET | `/api/v1/babies/{baby_id}/report/pdf` | Any | Generated PDF download |

**JSON report** bundles everything for a baby's report page:
```json
{
  "baby": { /* Baby detail, incl. latest_vitals */ },
  "monitoring_history":  [ /* MonitoringResponse[], newest first */ ],
  "involvement_history": [ /* InvolvementResponse[], newest first */ ],
  "involvement_summary": { /* summary */ },
  "generated_at": "2026-06-22T05:00:00+00:00"
}
```
Use `involvement_history[0]` for the latest Pillar-8 breakdown; reverse `monitoring_history` for
chronological trend charts.

**PDF** returns `application/pdf`. It accepts the token via the `Authorization: Bearer` header **or**
a `?token=<JWT>` query param — the latter lets you open the PDF directly in a browser tab:
```
{BASE_URL}/api/v1/babies/{baby_id}/report/pdf?token=<access_token>
```

### Users *(Admin only)*
| Method | Path | Purpose | Returns |
|---|---|---|---|
| GET | `/api/v1/users` | List users | `UserResponse[]` |
| POST | `/api/v1/users` | Create — `{ "role":"perawat","email":"...","password":"...","full_name":"..." }` | `UserResponse` (201) |
| GET | `/api/v1/users/{user_id}` | Get one | `UserResponse` |
| PUT | `/api/v1/users/{user_id}` | Update — `{ "full_name":"...", "is_active":false }` (optional) | `UserResponse` |
| POST | `/api/v1/users/{user_id}/reset-password` | `{ "new_password":"..." }` | **204** |
| DELETE | `/api/v1/users/{user_id}` | Deactivate (soft) | **204** |

> `DELETE` **deactivates** (`is_active=false`); it does not hard-delete.

### Audit Log *(Admin only)* — `GET /api/v1/audit-logs`
Query: `skip` (0), `limit` (100), `action` (optional, e.g. `LOGIN`, `CREATE`).
```json
[
  {
    "log_id": "...", "user_id": "aaaaaaaa-...-02", "user_name": "Siti Aisyah",
    "action": "CREATE", "table_name": "monitoring_records", "record_id": "...",
    "ip_address": "127.0.0.1", "details": { "skor": 78, "kategori": "Sangat Baik" },
    "created_at": "2026-06-22T04:00:00+00:00"
  }
]
```
`details` is free-form JSON (or `null`). The trail is immutable.

---

## Business rules the UI should reflect

**Vital `warning`** — computed server-side; show a clear alert when `warning`. A record is `warning`
if **any** of:

| Vital | Normal range |
|---|---|
| Heart rate | 100–160 bpm |
| Respiratory rate | 40–60 /min |
| SpO₂ | ≥ 93 % |
| Body temp (`suhu_bayi`) | 36.0–37.5 °C |
| Pain score (NIPS) | < 4 (≥ 4 = pain → warning) |

A `warning` monitoring record can also bump the incubator's `status` to `warning` (visible on the dashboard).

**Parent Engagement Index (PEI)** — `skor_keterlibatan` 0–100, categorised:
`0–25` Rendah · `26–50` Sedang · `51–75` Baik · `76–100` Sangat Baik. Color-code accordingly.

**Score scales** — expression/movement/sleep-quality: 1–5; pain: 0–7 (NIPS); FICare domains: 0–4.

See [docs/8 pillar NICU.md](../docs/8%20pillar%20NICU.md) for the clinical framework behind these fields.

---

## Data model (mental model)

```
User (admin|perawat|dokter)
Incubator ──< BabyIncubatorAssignment >── Baby ──1:1── Parent
                                            │
                                            ├──< MonitoringRecord          (vitals; recorded_by User)
                                            └──< ParentInvolvementRecord   (FICare; recorded_by User)
AuditLog (who did what, when)
```
- A baby has exactly **one active** incubator assignment at a time; discharge ends it.
- Monitoring & involvement records are **append-only** from the client's perspective (create + list).

---

## Typical dashboard flow

1. `POST /auth/login` → store `access_token`; set `Authorization: Bearer` on all calls.
2. `GET /dashboard` → render incubator grid + status counts.
3. Click an incubator → `GET /incubators/{id}` (or reuse dashboard payload).
4. Open a baby → `GET /babies/{id}/report` → Kondisi Terkini, Pillar-8 breakdown, history table, trend charts.
5. (Nurse/Admin) record data → `POST /babies/{id}/monitoring`, `POST /babies/{id}/involvement`,
   optionally `POST /monitoring/{id}/photo`.
6. Export → open `…/report/pdf?token=<jwt>` in a new tab.
7. (Admin) `GET /users`, `GET /audit-logs` for the admin section.

---

## Demo accounts (seeded)

| Role | Email | Password |
|---|---|---|
| Admin | `admin@neonatal.rs` | `Password123!` |
| Perawat | `siti.aisyah@neonatal.rs` | `Password123!` |
| Dokter | `dr.anisa@neonatal.rs` | `Password123!` |

> Actual passwords depend on how the database was seeded — confirm with the backend owner if a login fails.

---

*Field or status-code question? The live Swagger UI at `{BASE_URL}/docs` mirrors this exactly and
lets you execute requests with your token.*
