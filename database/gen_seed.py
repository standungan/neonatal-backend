# -*- coding: utf-8 -*-
"""Generate a rich, deterministic seed_data.sql for the Neonatal Care System.

Imports the REAL observation catalog so item codes / MAX_TOTAL / category
bands can never drift from the backend. Emits pure SQL (run after schema.sql).
"""
import importlib.util
import json
import random
import zlib
from datetime import datetime, timedelta, timezone
from pathlib import Path


def rng_for(*parts):
    """Deterministic RNG keyed by parts (stable across runs, unlike hash())."""
    return random.Random(zlib.crc32("|".join(map(str, parts)).encode()))

ROOT = Path(__file__).resolve().parents[2]   # backend/database/gen_seed.py -> repo root
CATALOG_PY = ROOT / "backend" / "app" / "services" / "observation_catalog.py"

# ── load the catalog module standalone (it imports nothing) ──────────────────
spec = importlib.util.spec_from_file_location("observation_catalog", CATALOG_PY)
cat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cat)
PILLARS = cat.PILLARS
MAX_TOTAL = cat.MAX_TOTAL          # 144
MAX_PER_ITEM = cat.MAX_PER_ITEM    # 3
ALL_ITEM_CODES = cat.ALL_ITEM_CODES
category_for = cat.category_for

# involvement = Pillar 6 "Kerjasama dengan Keluarga" (6 items, 0–3)
INV_CATALOG_PY = ROOT / "backend" / "app" / "services" / "involvement_catalog.py"
_ispec = importlib.util.spec_from_file_location("involvement_catalog", INV_CATALOG_PY)
icat = importlib.util.module_from_spec(_ispec)
_ispec.loader.exec_module(icat)
INV_ITEM_CODES = icat.ALL_ITEM_CODES        # keluarga_1..6
INV_MAX_TOTAL = icat.MAX_TOTAL              # 18
inv_category_for = icat.category_for

# aksi = Pillar 8 "Kolaborasi Interprofesional" (6 items, 0–3)
AKSI_CATALOG_PY = ROOT / "backend" / "app" / "services" / "aksi_catalog.py"
_aspec = importlib.util.spec_from_file_location("aksi_catalog", AKSI_CATALOG_PY)
acat = importlib.util.module_from_spec(_aspec)
_aspec.loader.exec_module(acat)
AKSI_ITEM_CODES = acat.ALL_ITEM_CODES       # kolaborasi_1..6
AKSI_MAX_TOTAL = acat.MAX_TOTAL             # 18
aksi_category_for = acat.category_for

TZ7 = timezone(timedelta(hours=7))

# bcrypt hash of "Password123!" (reused from the original seed)
PW = "$2b$12$mVNFQ/MY10L6vCb8hx9C9eXKfnWQGZHQDkBu3a.oZYhgQR5Xtjn0K"

# ── identifiers ──────────────────────────────────────────────────────────────
U_ADMIN   = "aaaaaaaa-0001-0001-0001-000000000001"
U_PER1    = "aaaaaaaa-0001-0001-0001-000000000002"  # Siti Aisyah
U_PER2    = "aaaaaaaa-0001-0001-0001-000000000003"  # Budi Santoso
U_DOK1    = "aaaaaaaa-0001-0001-0001-000000000004"  # dr. Anisa
U_PER3    = "aaaaaaaa-0001-0001-0001-000000000005"  # Rahmawati
U_DOK2    = "aaaaaaaa-0001-0001-0001-000000000006"  # dr. Bagus

def INC(n): return f"bbbbbbbb-0002-0002-0002-{n:012d}"
def BABY(n): return f"cccccccc-0003-0003-0003-{n:012d}"

NURSES = [U_PER1, U_PER2, U_PER3]

# ── incubators ───────────────────────────────────────────────────────────────
INCUBATORS = [
    (INC(1), "01", "NICU Ruang A", "terisi"),
    (INC(2), "02", "NICU Ruang A", "terisi"),
    (INC(3), "03", "NICU Ruang A", "kosong"),
    (INC(4), "04", "NICU Ruang A", "warning"),
    (INC(5), "05", "NICU Ruang B", "terisi"),
    (INC(6), "06", "NICU Ruang B", "warning"),
    (INC(7), "07", "NICU Ruang B", "terisi"),
    (INC(8), "08", "NICU Ruang B", "terisi"),
    (INC(9), "09", "NICU Ruang B", "tidak_tersedia"),
]

# ── babies ───────────────────────────────────────────────────────────────────
# profile drives generated vitals / observation quality / PEI over time.
#   q0 -> q1 = observation avg item score at start / end of window (0..3) → trend
#   pei0 -> pei1 = PEI domain avg at start / end
#   state: "stable" | "improving" | "warning" | "critical"
BABIES = [
    dict(id=BABY(1), name="Ahmad Rizki",        gender="laki_laki", bd="2026-06-24",
         bw=2400, bl=46.0, ga=35, btype="SC",     inc=INC(1),
         mother="Rina Dewi", father="Budi Rizki", phone="081234567890",
         mhist="Hipertensi ringan dalam kehamilan",
         nurse=U_PER1, state="improving", q0=2.3, q1=2.8, pei0=2.6, pei1=3.4, force0=0),
    dict(id=BABY(2), name="Siti Zahra",         gender="perempuan", bd="2026-06-26",
         bw=1950, bl=42.5, ga=33, btype="Normal", inc=INC(2),
         mother="Kartini", father="Hasan", phone="082345678901",
         mhist=None,
         nurse=U_PER1, state="stable", q0=2.2, q1=2.3, pei0=2.0, pei1=2.2, force0=0),
    dict(id=BABY(3), name="Muhammad Farhan",    gender="laki_laki", bd="2026-06-22",
         bw=1450, bl=40.0, ga=30, btype="Normal", inc=INC(4),
         mother="Yuni Astuti", father="Farhan Sr", phone="083456789012",
         mhist="Diabetes gestasional; KPD 18 jam",
         nurse=U_PER2, state="warning", q0=1.7, q1=1.9, pei0=1.6, pei1=1.8, force0=0),
    dict(id=BABY(4), name="Hana Putri",         gender="perempuan", bd="2026-06-20",
         bw=2800, bl=48.0, ga=37, btype="SC",     inc=INC(5),
         mother="Dewi Lestari", father="Anton", phone="084567890123",
         mhist=None,
         nurse=U_PER1, state="stable", q0=2.7, q1=2.9, pei0=3.2, pei1=3.6, force0=0),
    dict(id=BABY(5), name="Bilqis Ramadhani",   gender="perempuan", bd="2026-06-28",
         bw=1100, bl=37.0, ga=28, btype="SC",     inc=INC(6),
         mother="Nur Halimah", father="Zulkifli", phone="085678901234",
         mhist="Preeklampsia berat; sangat prematur (ELBW)",
         nurse=U_PER2, state="critical", q0=1.4, q1=1.6, pei0=1.2, pei1=1.5, force0=2),
    dict(id=BABY(6), name="Kenzo Pratama",      gender="laki_laki", bd="2026-06-25",
         bw=1700, bl=41.0, ga=32, btype="Normal", inc=INC(7),
         mother="Melati Sari", father="Gunawan", phone="086789012345",
         mhist=None,
         nurse=U_PER3, state="improving", q0=2.0, q1=2.5, pei0=1.8, pei1=2.6, force0=0),
    dict(id=BABY(7), name="Aleena Zahira",      gender="perempuan", bd="2026-06-27",
         bw=2050, bl=43.0, ga=34, btype="Normal", inc=INC(8),
         mother="Fitri Handayani", father="Rizal", phone="087890123456",
         mhist=None,
         nurse=U_PER3, state="stable", q0=2.5, q1=2.6, pei0=2.8, pei1=3.0, force0=0),
]

# discharged baby (history only) — previously in incubator 03, now discharged
DISCHARGED = dict(
    id=BABY(8), name="Gibran Maulana", gender="laki_laki", bd="2026-06-05",
    bw=2600, bl=47.0, ga=36, btype="Normal", inc=INC(3),
    mother="Ayu Wandira", father="Teguh", phone="088901234567",
    mhist=None, nurse=U_PER1,
    admitted="2026-06-05 09:00:00+07", discharged="2026-06-30 10:00:00+07",
)

# ── time window: last 4 days up to the morning of 2026-07-08 ─────────────────
DAYS = ["2026-07-05", "2026-07-06", "2026-07-07"]      # full days (3 rounds)
LAST_DAY = "2026-07-08"                                 # morning round only
MON_HOURS = [8, 14, 20]
OBS_HOUR = 9
INV_HOUR = 11


def dt(date_str, hour, minute=0):
    d = datetime.strptime(date_str, "%Y-%m-%d")
    return datetime(d.year, d.month, d.day, hour, minute, tzinfo=TZ7)


def sql_ts(d):
    return d.strftime("%Y-%m-%d %H:%M:%S+07")


def q(s):
    if s is None:
        return "NULL"
    return "'" + s.replace("'", "''") + "'"


# progress 0..1 across the window (used to interpolate trends)
_SLOTS = []
for di, day in enumerate(DAYS):
    for h in MON_HOURS:
        _SLOTS.append((day, h))
_SLOTS.append((LAST_DAY, MON_HOURS[0]))
N_SLOTS = len(_SLOTS)


def lerp(a, b, t):
    return a + (b - a) * t


# ── generators ───────────────────────────────────────────────────────────────
def gen_observation_scores(rng, q_target, force_zeros=0):
    """Full 48-item score map centred on q_target; returns (scores, total, pct, cat)."""
    scores = {}
    for code in ALL_ITEM_CODES:
        v = round(q_target + rng.uniform(-0.55, 0.55))
        scores[code] = max(0, min(MAX_PER_ITEM, v))
    # force the lowest-value items to 0 (critical deviations)
    for code in sorted(scores, key=lambda c: scores[c])[:force_zeros]:
        scores[code] = 0
    total = sum(scores.values())
    pct = round(total / MAX_TOTAL * 100, 1)   # backend rounds to 1 decimal
    return scores, total, pct, category_for(pct)


def gen_vitals(rng, baby, t):
    """Return a dict of monitoring column values, coloured by state + trend t(0..1)."""
    st = baby["state"]
    if st == "warning":
        suhu = round(rng.uniform(37.4, 37.9), 1)
        sinc = round(rng.uniform(34.0, 34.8), 1)
        hum = round(rng.uniform(58, 65), 2)
        hr = rng.randint(158, 172)
        rr = rng.randint(64, 74)
        spo2 = round(rng.uniform(90.0, 93.5), 2)
        expr = rng.randint(2, 3); mov = rng.randint(2, 3)
        pain = rng.randint(3, 5)
        sleep = rng.randint(35, 60); sq = rng.randint(2, 3); agit = rng.randint(2, 4)
    elif st == "critical":
        suhu = round(rng.uniform(36.0, 36.4), 1)
        sinc = round(rng.uniform(34.5, 35.5), 1)
        hum = round(rng.uniform(62, 70), 2)
        hr = rng.randint(168, 185)
        rr = rng.randint(66, 78)
        spo2 = round(rng.uniform(87.0, 92.0), 2)
        expr = rng.randint(1, 2); mov = rng.randint(1, 2)
        pain = rng.randint(4, 6)
        sleep = rng.randint(25, 45); sq = rng.randint(1, 2); agit = rng.randint(3, 5)
    else:  # stable / improving — vitals drift into the healthy band as t→1
        suhu = round(lerp(37.1, 36.8, t) + rng.uniform(-0.1, 0.1), 1)
        sinc = round(lerp(34.0, 33.2, t) + rng.uniform(-0.2, 0.2), 1)
        hum = round(lerp(58, 53, t) + rng.uniform(-1.5, 1.5), 2)
        hr = int(lerp(148, 130, t)) + rng.randint(-4, 4)
        rr = int(lerp(56, 46, t)) + rng.randint(-2, 2)
        spo2 = round(lerp(95.5, 98.5, t) + rng.uniform(-0.5, 0.5), 2)
        expr = min(5, max(1, round(lerp(3, 4, t)) + rng.randint(-1, 1)))
        mov = min(5, max(1, round(lerp(3, 4, t)) + rng.randint(-1, 1)))
        pain = max(0, round(lerp(2, 0, t)) + rng.randint(0, 1))
        sleep = int(lerp(80, 130, t)) + rng.randint(-10, 10)
        sq = min(5, max(1, round(lerp(3, 5, t)) + rng.randint(-1, 1)))
        agit = max(0, round(lerp(2, 0, t)) + rng.randint(0, 1))
    return dict(suhu=suhu, sinc=sinc, hum=hum, hr=hr, rr=rr, spo2=spo2,
                expr=expr, mov=mov, pain=pain, sleep=sleep, sq=sq, agit=agit)


MON_NOTES = {
    "warning": ["Takipnea, monitoring ketat", "SpO2 borderline, O2 dinaikkan", None],
    "critical": ["Desaturasi berulang, lapor DPJP", "Apnea singkat, stimulasi taktil", "Kondisi belum stabil"],
    "stable": [None, None, "Kondisi stabil", "Toleransi minum baik"],
    "improving": [None, "Perbaikan klinis", None, "BB naik, aktif"],
}
KONDISI = ["Tenang", "Aktif", "Rewel", "Tidur"]

# ── updates02: maternal record + expanded NICU intake ─────────────────────────
BLOOD = ["O", "A", "B", "AB", "O", "A", "B", "O"]
EDU = ["sma", "diploma", "s1", "s1", "smp", "s2", "sma", "sma"]
JOBS = ["Ibu Rumah Tangga", "Guru", "Karyawan Swasta", "Wiraswasta", "PNS", "Perawat", "Pedagang", "Ibu Rumah Tangga"]
INC_LOC = {i: loc for i, no, loc, st in INCUBATORS}


def qb(v):   # boolean literal or NULL
    return "NULL" if v is None else ("TRUE" if v else "FALSE")


def qi(v):   # int literal or NULL
    return "NULL" if v is None else str(v)


def qjson(v):  # JSONB array literal or NULL
    return "NULL" if v is None else "'" + json.dumps(v, ensure_ascii=False).replace("'", "''") + "'::jsonb"


def baby_extra(b, idx):
    """Extended baby identity fields (updates02), derived deterministically."""
    rng = rng_for("babyx", b["id"])
    return dict(
        no_rm_bayi=f"RM-B-{idx:04d}",
        jam_lahir=f"{rng.randint(0, 23):02d}:{rng.choice([0, 15, 30, 45]):02d}:00",
        usia_masuk_nicu_jam=rng.randint(2, 12),
        lingkar_kepala=round(b["bl"] * 0.62, 1),
        lingkar_dada=round(b["bl"] * 0.58, 1),
        golongan_darah=BLOOD[(idx - 1) % len(BLOOD)],
    )


def gen_maternal(b, idx):
    """Mother's structured medical record — coherent with the baby's profile."""
    rng = rng_for("maternal", b["id"])
    mh = (b.get("mhist") or "").lower()
    state = b.get("state", "stable")
    preek = "preeklam" in mh
    hipert = "hipertensi" in mh
    dm = "diabetes" in mh
    kpd = "kpd" in mh or "ketuban" in mh
    indikasi = []
    if preek: indikasi.append("Preeklamsia")
    if kpd: indikasi.append("Ketuban pecah dini (PPROM)")
    if dm: indikasi.append("Diabetes gestasional")
    if state in ("warning", "critical") and not indikasi:
        indikasi.append("Persalinan prematur spontan")
    komplikasi = ["Perdarahan"] if state == "critical" else (["Tidak ada komplikasi"] if state == "stable" else [])
    apgar1 = {"critical": 4, "warning": 6, "improving": 6, "stable": 7}.get(state, 7)
    return dict(
        no_rm_ibu=f"RM-I-{idx:04d}", umur_ibu=rng.randint(21, 38),
        pendidikan=EDU[(idx - 1) % len(EDU)], pekerjaan=JOBS[(idx - 1) % len(JOBS)],
        alamat=f"Jl. Contoh No. {idx * 3}, Kota", golongan_darah=BLOOD[(idx - 1) % len(BLOOD)],
        kehamilan_ke=rng.randint(1, 4), jumlah_persalinan_hidup=rng.randint(0, 2),
        riwayat_abortus=rng.random() < 0.2,
        riwayat_prematur=state in ("warning", "critical") or rng.random() < 0.2,
        riwayat_bblr=rng.random() < 0.25, riwayat_bayi_meninggal=rng.random() < 0.1,
        usia_kehamilan_lahir=b["ga"], jenis_kehamilan="tunggal",
        anc_rutin=rng.random() < 0.85, jumlah_anc=rng.randint(2, 8),
        hipertensi_kehamilan=hipert or preek, preeklamsia=preek, diabetes_gestasional=dm,
        infeksi_hamil=rng.random() < 0.15, perdarahan_hamil=state == "critical",
        ketuban_pecah_dini=kpd, merokok=False, paparan_asap_rokok=rng.random() < 0.3,
        konsumsi_alkohol=False, obat_tertentu=False, obat_tertentu_ket=None,
        tanggal_persalinan=b["bd"],
        jenis_persalinan="sc" if b["btype"].upper() == "SC" else "normal",
        tempat_persalinan="RSUD Kota Sehat",
        indikasi_prematur=indikasi or None, indikasi_prematur_lainnya=None,
        komplikasi_persalinan=komplikasi or None, komplikasi_lainnya=None,
        apgar_menit_1=apgar1, apgar_menit_5=min(apgar1 + 2, 9),
        kondisi_umum={"critical": "buruk", "warning": "cukup"}.get(state, "baik"),
        masih_dirawat=state in ("warning", "critical"), komplikasi_postpartum=state == "critical",
        dapat_berjalan=state != "critical", dapat_menyusui=state in ("stable", "improving"),
    )


# maternal-record column order (must match the INSERT below)
_MAT_COLS = [
    "no_rm_ibu", "umur_ibu", "pendidikan", "pekerjaan", "alamat", "golongan_darah",
    "kehamilan_ke", "jumlah_persalinan_hidup", "riwayat_abortus", "riwayat_prematur",
    "riwayat_bblr", "riwayat_bayi_meninggal", "usia_kehamilan_lahir", "jenis_kehamilan",
    "anc_rutin", "jumlah_anc", "hipertensi_kehamilan", "preeklamsia", "diabetes_gestasional",
    "infeksi_hamil", "perdarahan_hamil", "ketuban_pecah_dini", "merokok", "paparan_asap_rokok",
    "konsumsi_alkohol", "obat_tertentu", "obat_tertentu_ket", "tanggal_persalinan",
    "jenis_persalinan", "tempat_persalinan", "indikasi_prematur", "indikasi_prematur_lainnya",
    "komplikasi_persalinan", "komplikasi_lainnya", "apgar_menit_1", "apgar_menit_5",
    "kondisi_umum", "masih_dirawat", "komplikasi_postpartum", "dapat_berjalan", "dapat_menyusui",
]
_MAT_BOOL = {
    "riwayat_abortus", "riwayat_prematur", "riwayat_bblr", "riwayat_bayi_meninggal", "anc_rutin",
    "hipertensi_kehamilan", "preeklamsia", "diabetes_gestasional", "infeksi_hamil", "perdarahan_hamil",
    "ketuban_pecah_dini", "merokok", "paparan_asap_rokok", "konsumsi_alkohol", "obat_tertentu",
    "masih_dirawat", "komplikasi_postpartum", "dapat_berjalan", "dapat_menyusui",
}
_MAT_INT = {
    "umur_ibu", "kehamilan_ke", "jumlah_persalinan_hidup", "usia_kehamilan_lahir",
    "jumlah_anc", "apgar_menit_1", "apgar_menit_5",
}
_MAT_JSON = {"indikasi_prematur", "komplikasi_persalinan"}


def mat_value(col, v):
    if col in _MAT_BOOL: return qb(v)
    if col in _MAT_INT: return qi(v)
    if col in _MAT_JSON: return qjson(v)
    return q(v)


# assign index + extra fields to every baby (active + discharged)
_ALL_BABIES = list(enumerate(BABIES, start=1)) + [(len(BABIES) + 1, DISCHARGED)]
for _idx, _b in _ALL_BABIES:
    _b["_idx"] = _idx
    _b["_x"] = baby_extra(_b, _idx)
    _b["_mat"] = gen_maternal(_b, _idx)


# ── build SQL ────────────────────────────────────────────────────────────────
out = []
def w(s=""): out.append(s)

w("-- =============================================================================")
w("-- Seed Data (rich demo) — Sistem Monitoring Bayi pada Inkubator")
w("-- Run AFTER schema.sql.  Generated — do not edit by hand; see backend/database/gen_seed.py.")
w("--")
w("--   8 users · 9 incubators · 8 babies (7 active + 1 discharged)")
w("--   ~4 days of time-series: monitoring (3x/day) + daily observation + involvement")
w("--   Covers stable, improving, warning and critical cases.")
w("--")
w('--   All passwords are bcrypt hashes of "Password123!"')
w('--   Logins: admin@neonatal.rs · siti.aisyah@neonatal.rs · dr.anisa@neonatal.rs (+others)')
w("-- =============================================================================")
w()
w("BEGIN;")
w()
w("-- Idempotent: clear existing rows (children first) before reseeding.")
w("TRUNCATE TABLE audit_logs, aksi_records, observations, parent_involvement_records,")
w("    monitoring_records, baby_incubator_assignments, maternal_records, parents, babies,")
w("    incubators, users RESTART IDENTITY CASCADE;")
w()

# ── users ──
w("-- ── USERS ────────────────────────────────────────────────────────────────")
w("INSERT INTO users (id, role, email, password_hash, full_name) VALUES")
users = [
    (U_ADMIN, "admin",   "admin@neonatal.rs",        "Administrator Sistem"),
    (U_PER1,  "perawat", "siti.aisyah@neonatal.rs",  "Siti Aisyah"),
    (U_PER2,  "perawat", "budi.santoso@neonatal.rs", "Budi Santoso"),
    (U_PER3,  "perawat", "rahmawati@neonatal.rs",    "Rahmawati"),
    (U_DOK1,  "dokter",  "dr.anisa@neonatal.rs",     "dr. Anisa Permata, Sp.A"),
    (U_DOK2,  "dokter",  "dr.bagus@neonatal.rs",     "dr. Bagus Wicaksono, Sp.A"),
]
rows = [f"('{i}', '{r}', {q(e)}, '{PW}', {q(n)})" for i, r, e, n in users]
w(",\n".join(rows) + ";")
w()

# ── incubators ──
w("-- ── INCUBATORS ───────────────────────────────────────────────────────────")
w("INSERT INTO incubators (incubator_id, incubator_no, location, status) VALUES")
rows = [f"('{i}', {q(no)}, {q(loc)}, '{st}')" for i, no, loc, st in INCUBATORS]
w(",\n".join(rows) + ";")
w()

# ── babies ──
w("-- ── BABIES ───────────────────────────────────────────────────────────────")
w("INSERT INTO babies (baby_id, baby_name, gender, birth_date, birth_weight, birth_length, "
  "gestational_age, birth_type, no_rm_bayi, jam_lahir, usia_masuk_nicu_jam, lingkar_kepala, "
  "lingkar_dada, golongan_darah, is_active) VALUES")
rows = []
for b in BABIES + [DISCHARGED]:
    x = b["_x"]
    active = "FALSE" if b is DISCHARGED else "TRUE"
    rows.append(f"('{b['id']}', {q(b['name'])}, '{b['gender']}', '{b['bd']}', "
                f"{b['bw']:.2f}, {b['bl']:.1f}, {b['ga']}, {q(b['btype'])}, "
                f"{q(x['no_rm_bayi'])}, '{x['jam_lahir']}', {x['usia_masuk_nicu_jam']}, "
                f"{x['lingkar_kepala']:.1f}, {x['lingkar_dada']:.1f}, '{x['golongan_darah']}', {active})")
d = DISCHARGED
w(",\n".join(rows) + ";")
w()

# ── parents ──
w("-- ── PARENTS (one-to-one with babies) ─────────────────────────────────────")
w("INSERT INTO parents (baby_id, mother_name, father_name, mother_phone, mother_medical_history) VALUES")
rows = []
for b in BABIES + [DISCHARGED]:
    rows.append(f"('{b['id']}', {q(b['mother'])}, {q(b['father'])}, {q(b['phone'])}, {q(b['mhist'])})")
w(",\n".join(rows) + ";")
w()

# ── assignments ──
w("-- ── BABY ↔ INCUBATOR ASSIGNMENTS (+ registration data, updates02) ─────────")
w("INSERT INTO baby_incubator_assignments (baby_id, incubator_id, assigned_by, assigned_at, "
  "discharged_at, status, no_registrasi_nicu, rumah_sakit, ruang_nicu, dpjp_id) VALUES")
DOKS = [U_DOK1, U_DOK2]
rows = []
for b in BABIES:
    assigned = f"{b['bd']} 08:00:00+07"
    idx = b["_idx"]
    reg = f"NICU-2026-{idx:04d}"
    dpjp = DOKS[(idx - 1) % len(DOKS)]
    rows.append(f"('{b['id']}', '{b['inc']}', '{b['nurse']}', '{assigned}', NULL, 'active', "
                f"'{reg}', 'RSUD Kota Sehat', {q(INC_LOC[b['inc']])}, '{dpjp}')")
reg_d = f"NICU-2026-{d['_idx']:04d}"
rows.append(f"('{d['id']}', '{d['inc']}', '{d['nurse']}', '{d['admitted']}', '{d['discharged']}', "
            f"'discharged', '{reg_d}', 'RSUD Kota Sehat', {q(INC_LOC[d['inc']])}, '{DOKS[(d['_idx']-1) % len(DOKS)]}')")
w(",\n".join(rows) + ";")
w()

# ── maternal records (updates02) ──
w("-- ── MATERNAL RECORDS (rekam medis ibu — updates02) ───────────────────────")
w("INSERT INTO maternal_records (baby_id, " + ", ".join(_MAT_COLS) + ") VALUES")
rows = []
for b in BABIES + [DISCHARGED]:
    m = b["_mat"]
    vals = ", ".join(mat_value(c, m[c]) for c in _MAT_COLS)
    rows.append(f"('{b['id']}', {vals})")
w(",\n".join(rows) + ";")
w()

# ── monitoring ──
w("-- ── MONITORING RECORDS (3x/day over the window) ──────────────────────────")
w("INSERT INTO monitoring_records")
w("    (baby_id, recorded_by, observation_time, suhu_bayi, suhu_inkubator, kelembapan_inkubator,")
w("     heart_rate, respiratory_rate, spo2, expression_score, movement_score, pain_score,")
w("     sleep_duration_min, sleep_quality, agitation_episodes, catatan) VALUES")
mon_rows = []
for b in BABIES:
    rng = rng_for("mon", b["id"])
    for si, (day, h) in enumerate(_SLOTS):
        t = si / (N_SLOTS - 1)
        v = gen_vitals(rng, b, t)
        note = rng.choice(MON_NOTES[b["state"]])
        ts = sql_ts(dt(day, h))
        nurse = rng.choice(NURSES)
        mon_rows.append(
            f"('{b['id']}', '{nurse}', '{ts}', {v['suhu']:.1f}, {v['sinc']:.1f}, {v['hum']:.2f}, "
            f"{v['hr']}, {v['rr']}, {v['spo2']:.2f}, {v['expr']}, {v['mov']}, {v['pain']}, "
            f"{v['sleep']}, {v['sq']}, {v['agit']}, {q(note)})"
        )
w(",\n".join(mon_rows) + ";")
w()

# ── involvement (Pillar 6 — Kerjasama dengan Keluarga; 6 items 0–3) ──
w("-- ── PARENT INVOLVEMENT RECORDS — Pilar 6 (6 items 0–3; %=total/18*100) ────")
w("INSERT INTO parent_involvement_records")
w("    (baby_id, recorded_by, observation_time, scores, catatan,")
w("     durasi_menyusui, durasi_interaksi, kondisi_bayi, total_score, percentage, category) VALUES")
inv_rows = []
inv_days = DAYS + [LAST_DAY]
for b in BABIES:
    rng = rng_for("inv", b["id"])
    for di, day in enumerate(inv_days):
        t = di / (len(inv_days) - 1)
        # reuse the baby's pei trend (0–4) mapped onto the 0–3 item scale
        item_avg = lerp(b["pei0"], b["pei1"], t) * 3 / 4
        scores = {}
        for code in INV_ITEM_CODES:
            v = round(item_avg + rng.uniform(-0.55, 0.55))
            scores[code] = max(0, min(3, v))
        total = sum(scores.values())
        pct = round(total / INV_MAX_TOTAL * 100, 1)
        catg = inv_category_for(pct)
        js = json.dumps(scores, separators=(",", ":"))
        menyusui = rng.randint(5, 25) if b["state"] != "critical" else rng.randint(0, 10)
        interaksi = rng.randint(20, 60)
        kondisi = rng.choice(KONDISI)
        ts = sql_ts(dt(day, INV_HOUR))
        nurse = rng.choice(NURSES)
        inv_rows.append(
            f"('{b['id']}', '{nurse}', '{ts}', '{js}'::jsonb, NULL, "
            f"{menyusui}, {interaksi}, {q(kondisi)}, {total}, {pct:.1f}, {q(catg)})"
        )
w(",\n".join(inv_rows) + ";")
w()

# ── observations ──
w("-- ── OBSERVATIONS (Monitoring Bayi, 6 pillars / 42 items scored 0–3; daily) ─")
w("--   scores JSONB is the full 42-item map; total_score/percentage/category")
w("--   are precomputed to match the backend (total/126*100, category bands).")
w("INSERT INTO observations")
w("    (baby_id, recorded_by, observation_time, scores, catatan, total_score, percentage, category) VALUES")
obs_rows = []
obs_days = DAYS + [LAST_DAY]
for b in BABIES:
    rng = rng_for("obs", b["id"])
    for di, day in enumerate(obs_days):
        t = di / (len(obs_days) - 1)
        qv = lerp(b["q0"], b["q1"], t)
        # only the latest few days carry the forced criticals for the critical baby
        fz = b["force0"] if (b["force0"] and di >= len(obs_days) - 2) else 0
        scores, total, pct, catg = gen_observation_scores(rng, qv, force_zeros=fz)
        js = json.dumps(scores, separators=(",", ":"))
        note = None
        if fz:
            note = "Terdapat item penyimpangan berat — tindakan segera"
        elif catg in ("Sangat Baik", "Baik") and di == len(obs_days) - 1:
            note = "Perkembangan sesuai target"
        ts = sql_ts(dt(day, OBS_HOUR))
        nurse = rng.choice(NURSES)
        obs_rows.append(
            f"('{b['id']}', '{nurse}', '{ts}', '{js}'::jsonb, {q(note)}, {total}, {pct:.2f}, {q(catg)})"
        )
w(",\n".join(obs_rows) + ";")
w()

# ── aksi (Menu Aksi — Kolaborasi Interprofesional; 6 items 0–3) ──
w("-- ── AKSI RECORDS — Kolaborasi Interprofesional (6 items 0–3; %=total/18*100) ─")
w("INSERT INTO aksi_records")
w("    (baby_id, recorded_by, observation_time, scores, catatan, total_score, percentage, category) VALUES")
aksi_rows = []
aksi_days = DAYS + [LAST_DAY]
for b in BABIES:
    rng = rng_for("aksi", b["id"])
    for di, day in enumerate(aksi_days):
        t = di / (len(aksi_days) - 1)
        avg = lerp(b["q0"], b["q1"], t)   # collaboration quality tracks overall care quality
        scores = {}
        for code in AKSI_ITEM_CODES:
            v = round(avg + rng.uniform(-0.55, 0.55))
            scores[code] = max(0, min(3, v))
        total = sum(scores.values())
        pct = round(total / AKSI_MAX_TOTAL * 100, 1)
        catg = aksi_category_for(pct)
        js = json.dumps(scores, separators=(",", ":"))
        ts = sql_ts(dt(day, 13))
        nurse = rng.choice(NURSES)
        aksi_rows.append(
            f"('{b['id']}', '{nurse}', '{ts}', '{js}'::jsonb, NULL, {total}, {pct:.1f}, {q(catg)})"
        )
w(",\n".join(aksi_rows) + ";")
w()

# ── a few audit-log samples ──
w("-- ── AUDIT LOG (sample entries) ───────────────────────────────────────────")
w("INSERT INTO audit_logs (user_id, action, table_name, record_id, ip_address, details) VALUES")
audit = [
    (U_PER1, "LOGIN", "NULL", "NULL", "10.0.0.21", None),
    (U_DOK1, "LOGIN", "NULL", "NULL", "10.0.0.30", None),
    (U_ADMIN, "CREATE", "'users'", f"'{U_PER3}'", "10.0.0.10", '{"role": "perawat"}'),
    (U_DOK1, "EXPORT", "'babies'", f"'{BABY(3)}'", "10.0.0.30", '{"format": "pdf"}'),
]
rows = []
for uid, act, tbl, rid, ip, det in audit:
    detv = q(det) if det else "NULL"
    rows.append(f"('{uid}', '{act}', {tbl}, {rid}, '{ip}', {detv})")
w(",\n".join(rows) + ";")
w()
w("COMMIT;")
w()

sql = "\n".join(out) + "\n"
target = ROOT / "backend" / "database" / "seed_data.sql"
target.write_text(sql, encoding="utf-8")

# ── summary to stderr for review ─────────────────────────────────────────────
print(f"WROTE {target}")
print(f"users=6 incubators={len(INCUBATORS)} babies={len(BABIES)+1}")
print(f"monitoring_rows={len(mon_rows)} involvement_rows={len(inv_rows)} observation_rows={len(obs_rows)} aksi_rows={len(aksi_rows)}")
print(f"MAX_TOTAL={MAX_TOTAL} n_item_codes={len(ALL_ITEM_CODES)} slots_per_baby={N_SLOTS}")
# show observation category spread
print("obs sample (baby, day-index -> pct/category):")
for b in BABIES:
    rng = rng_for("obs", b["id"])
    line = [b["name"][:14].ljust(14)]
    for di in range(len(obs_days)):
        t = di / (len(obs_days) - 1)
        qv = lerp(b["q0"], b["q1"], t)
        fz = b["force0"] if (b["force0"] and di >= len(obs_days) - 2) else 0
        _, total, pct, catg = gen_observation_scores(rng, qv, force_zeros=fz)
        line.append(f"{pct:5.1f}%={catg[:4]}")
    print("  " + " ".join(line))
