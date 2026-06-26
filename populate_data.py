"""
Populate NeonatalDB with comprehensive realistic data.
Clears existing monitoring/involvement records then inserts:
  - 15–21 monitoring records per baby (3x/day over admission period)
  - 4–8 involvement sessions per baby with realistic scores
"""
import uuid
import psycopg2
from datetime import datetime, timedelta, timezone

TZ7 = timezone(timedelta(hours=7))

conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="neonatal_db", user="neonatal_user", password="admin.123"
)
cur = conn.cursor()

# ── IDs ───────────────────────────────────────────────────────────────────────
PERAWAT_1 = 'aaaaaaaa-0001-0001-0001-000000000002'  # Siti Aisyah (perawat)
PERAWAT_2 = 'aaaaaaaa-0001-0001-0001-000000000003'  # Budi Santoso (perawat)

BABY_RIZKI  = 'cccccccc-0003-0003-0003-000000000001'
BABY_AISYAH = 'cccccccc-0003-0003-0003-000000000002'
BABY_FARHAN = 'cccccccc-0003-0003-0003-000000000003'
BABY_HANA   = 'cccccccc-0003-0003-0003-000000000004'

INC_01 = 'bbbbbbbb-0002-0002-0002-000000000001'
INC_02 = 'bbbbbbbb-0002-0002-0002-000000000002'
INC_04 = 'bbbbbbbb-0002-0002-0002-000000000004'
INC_05 = 'bbbbbbbb-0002-0002-0002-000000000005'

# ── Clear existing records ────────────────────────────────────────────────────
print("Clearing existing monitoring and involvement records...")
cur.execute("DELETE FROM parent_involvement_records")
cur.execute("DELETE FROM monitoring_records")
conn.commit()

# ── Helper ────────────────────────────────────────────────────────────────────
def dt(date_str, hour, minute=0):
    """Return timezone-aware datetime in WIB (UTC+7)."""
    d = datetime.strptime(date_str, "%Y-%m-%d")
    return datetime(d.year, d.month, d.day, hour, minute, tzinfo=TZ7)

def insert_monitoring(baby_id, recorded_by, obs_time,
                      suhu_bayi, suhu_inkubator, heart_rate, spo2,
                      expression_score, movement_score, catatan=None):
    cur.execute("""
        INSERT INTO monitoring_records
            (baby_id, recorded_by, observation_time,
             suhu_bayi, suhu_inkubator, heart_rate, spo2,
             expression_score, movement_score, catatan)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (baby_id, recorded_by, obs_time,
          suhu_bayi, suhu_inkubator, heart_rate, spo2,
          expression_score, movement_score, catatan))

def insert_involvement(baby_id, recorded_by, obs_time,
                       durasi_menyusui, durasi_interaksi, skor, kondisi):
    cur.execute("""
        INSERT INTO parent_involvement_records
            (baby_id, recorded_by, observation_time,
             durasi_menyusui, durasi_interaksi, skor_keterlibatan, kondisi_bayi)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (baby_id, recorded_by, obs_time,
          durasi_menyusui, durasi_interaksi, skor, kondisi))

# =============================================================================
# BABY 1 — Ahmad Rizki (Inkubator 01)
# 35 minggu, 2400g, masuk 12 Mei. Awalnya HR tinggi, membaik hari 3-5.
# =============================================================================
print("Inserting monitoring for Ahmad Rizki...")

rizki_data = [
    # (date,  hour, suhu_bayi, suhu_inc, hr,  spo2,  expr, move, catatan)
    ("2025-05-12", 9,  36.4, 33.0, 152, 94.5, 2, 2, "Baru masuk, adaptasi"),
    ("2025-05-12", 14, 36.6, 33.2, 148, 95.0, 2, 3, None),
    ("2025-05-12", 20, 36.5, 33.0, 150, 94.0, 2, 2, "HR masih elevated"),
    ("2025-05-13", 8,  36.7, 33.5, 145, 95.5, 3, 3, None),
    ("2025-05-13", 13, 36.8, 33.5, 142, 96.0, 3, 3, None),
    ("2025-05-13", 19, 36.7, 33.3, 144, 95.5, 3, 3, None),
    ("2025-05-14", 8,  36.9, 33.8, 138, 96.5, 3, 4, "Kondisi membaik"),
    ("2025-05-14", 14, 37.0, 33.8, 135, 97.0, 4, 4, None),
    ("2025-05-14", 20, 36.9, 33.6, 136, 96.5, 3, 4, None),
    ("2025-05-15", 8,  37.0, 34.0, 132, 97.5, 4, 4, None),
    ("2025-05-15", 14, 37.1, 34.0, 130, 97.5, 4, 5, None),
    ("2025-05-15", 20, 37.0, 33.8, 131, 97.0, 4, 4, None),
    ("2025-05-16", 8,  37.0, 34.0, 128, 98.0, 4, 5, None),
    ("2025-05-16", 14, 37.1, 34.0, 129, 98.0, 5, 5, "Kondisi sangat baik"),
    ("2025-05-16", 20, 37.0, 33.8, 127, 98.5, 4, 5, None),
]
for d in rizki_data:
    insert_monitoring(BABY_RIZKI, PERAWAT_1, dt(d[0], d[1]),
                      d[2], d[3], d[4], d[5], d[6], d[7], d[8])

print("Inserting involvement for Ahmad Rizki...")
insert_involvement(BABY_RIZKI, PERAWAT_1, dt("2025-05-13", 10), 15, 30, 50, "Tenang")
insert_involvement(BABY_RIZKI, PERAWAT_1, dt("2025-05-14", 10), 20, 40, 70, "Tenang")
insert_involvement(BABY_RIZKI, PERAWAT_1, dt("2025-05-15", 10), 25, 50, 81, "Aktif")
insert_involvement(BABY_RIZKI, PERAWAT_2, dt("2025-05-16", 10), 28, 55, 86, "Tenang")

# =============================================================================
# BABY 2 — Siti Aisyah (Inkubator 02)
# 33 minggu, 1950g, masuk 13 Mei. SpO2 rendah awalnya, gradual recovery.
# =============================================================================
print("Inserting monitoring for Siti Aisyah...")

aisyah_data = [
    ("2025-05-13", 10, 36.1, 34.0, 154, 91.5, 1, 2, "SpO2 rendah, perhatian"),
    ("2025-05-13", 15, 36.2, 34.0, 152, 92.0, 2, 2, None),
    ("2025-05-13", 21, 36.1, 33.8, 155, 91.0, 1, 1, "SpO2 masih di bawah batas"),
    ("2025-05-14", 8,  36.3, 34.2, 150, 92.5, 2, 2, None),
    ("2025-05-14", 14, 36.4, 34.2, 148, 93.0, 2, 3, "SpO2 mulai membaik"),
    ("2025-05-14", 20, 36.3, 34.0, 149, 93.5, 2, 2, None),
    ("2025-05-15", 8,  36.5, 34.5, 144, 94.0, 3, 3, None),
    ("2025-05-15", 14, 36.6, 34.5, 142, 94.5, 3, 3, None),
    ("2025-05-15", 20, 36.5, 34.3, 143, 95.0, 3, 3, None),
    ("2025-05-16", 8,  36.7, 34.5, 138, 95.5, 3, 4, None),
    ("2025-05-16", 14, 36.8, 34.5, 136, 96.0, 4, 4, "Kondisi membaik signifikan"),
    ("2025-05-16", 20, 36.7, 34.3, 137, 96.0, 3, 4, None),
]
for d in aisyah_data:
    insert_monitoring(BABY_AISYAH, PERAWAT_1, dt(d[0], d[1]),
                      d[2], d[3], d[4], d[5], d[6], d[7], d[8])

print("Inserting involvement for Siti Aisyah...")
insert_involvement(BABY_AISYAH, PERAWAT_1, dt("2025-05-14", 11), 8,  20, 36, "Rewel")
insert_involvement(BABY_AISYAH, PERAWAT_1, dt("2025-05-15", 11), 12, 30, 44, "Tenang")
insert_involvement(BABY_AISYAH, PERAWAT_2, dt("2025-05-16", 11), 18, 40, 59, "Tenang")

# =============================================================================
# BABY 3 — Muhammad Farhan (Inkubator 04, WARNING)
# 34 minggu, 2100g, masuk 10 Mei. Kondisi kritis awal, naik-turun.
# =============================================================================
print("Inserting monitoring for Muhammad Farhan...")

farhan_data = [
    ("2025-05-10", 8,  37.8, 34.5, 166, 90.5, 1, 1, "Kondisi kritis, HR & suhu tinggi"),
    ("2025-05-10", 14, 37.9, 34.5, 168, 90.0, 1, 1, "SpO2 sangat rendah"),
    ("2025-05-10", 21, 37.7, 34.3, 164, 91.0, 1, 2, None),
    ("2025-05-11", 8,  37.6, 34.5, 162, 91.5, 2, 2, None),
    ("2025-05-11", 14, 37.5, 34.5, 158, 92.0, 2, 2, "Sedikit membaik"),
    ("2025-05-11", 20, 37.6, 34.3, 160, 91.5, 1, 2, None),
    ("2025-05-12", 8,  37.4, 34.5, 156, 92.5, 2, 2, None),
    ("2025-05-12", 14, 37.3, 34.3, 154, 93.0, 2, 3, None),
    ("2025-05-12", 20, 37.5, 34.3, 158, 92.0, 2, 2, "Fluktuasi kondisi"),
    ("2025-05-13", 8,  37.6, 34.5, 162, 91.5, 1, 2, "Kondisi menurun kembali"),
    ("2025-05-13", 14, 37.7, 34.5, 164, 91.0, 1, 1, None),
    ("2025-05-13", 20, 37.6, 34.3, 161, 91.5, 2, 2, None),
    ("2025-05-14", 8,  37.4, 34.5, 158, 92.0, 2, 2, None),
    ("2025-05-14", 14, 37.5, 34.3, 160, 92.0, 2, 2, None),
    ("2025-05-14", 20, 37.6, 34.5, 162, 91.5, 1, 2, None),
    ("2025-05-15", 8,  37.5, 34.5, 159, 92.0, 2, 2, None),
    ("2025-05-15", 14, 37.6, 34.3, 161, 91.5, 2, 2, None),
    ("2025-05-15", 20, 37.7, 34.5, 163, 91.0, 1, 1, "Perlu perhatian khusus"),
    ("2025-05-16", 8,  37.6, 34.5, 160, 92.0, 2, 2, None),
    ("2025-05-16", 14, 37.6, 34.3, 160, 92.0, 2, 2, None),
    ("2025-05-16", 20, 37.7, 34.5, 162, 91.5, 1, 2, "Status warning berlanjut"),
]
for d in farhan_data:
    insert_monitoring(BABY_FARHAN, PERAWAT_2, dt(d[0], d[1]),
                      d[2], d[3], d[4], d[5], d[6], d[7], d[8])

print("Inserting involvement for Muhammad Farhan...")
insert_involvement(BABY_FARHAN, PERAWAT_2, dt("2025-05-11", 10), 5,  15, 20, "Tidur")
insert_involvement(BABY_FARHAN, PERAWAT_2, dt("2025-05-12", 10), 8,  20, 26, "Tidur")
insert_involvement(BABY_FARHAN, PERAWAT_1, dt("2025-05-13", 10), 10, 25, 30, "Rewel")
insert_involvement(BABY_FARHAN, PERAWAT_2, dt("2025-05-14", 10), 12, 28, 36, "Rewel")
insert_involvement(BABY_FARHAN, PERAWAT_1, dt("2025-05-15", 10), 10, 30, 32, "Tidur")
insert_involvement(BABY_FARHAN, PERAWAT_2, dt("2025-05-16", 10), 12, 25, 30, "Rewel")

# =============================================================================
# BABY 4 — Hana Putri (Inkubator 05)
# 37 minggu, 2800g, masuk 15 Mei. Kondisi baik, hampir pulang.
# =============================================================================
print("Inserting monitoring for Hana Putri...")

hana_data = [
    ("2025-05-15", 11, 36.9, 33.5, 138, 97.5, 4, 4, "Kondisi baik sejak masuk"),
    ("2025-05-15", 16, 37.0, 33.5, 140, 97.0, 4, 5, None),
    ("2025-05-15", 21, 36.9, 33.3, 137, 97.5, 4, 4, None),
    ("2025-05-16", 8,  37.0, 33.5, 135, 98.0, 5, 5, None),
    ("2025-05-16", 14, 37.1, 33.5, 133, 98.5, 5, 5, "Sangat baik, kemungkinan pulang segera"),
    ("2025-05-16", 20, 37.0, 33.3, 134, 98.0, 5, 5, None),
]
for d in hana_data:
    insert_monitoring(BABY_HANA, PERAWAT_1, dt(d[0], d[1]),
                      d[2], d[3], d[4], d[5], d[6], d[7], d[8])

print("Inserting involvement for Hana Putri...")
insert_involvement(BABY_HANA, PERAWAT_1, dt("2025-05-15", 13), 25, 55, 83, "Tenang")
insert_involvement(BABY_HANA, PERAWAT_1, dt("2025-05-16", 10), 30, 60, 90, "Aktif")
insert_involvement(BABY_HANA, PERAWAT_2, dt("2025-05-16", 15), 28, 58, 87, "Tenang")

# ── Update incubator statuses based on latest vitals ─────────────────────────
print("Updating incubator statuses...")

# Inkubator 01 - Ahmad Rizki: normal
cur.execute("UPDATE incubators SET status='terisi' WHERE incubator_id=%s", (INC_01,))
# Inkubator 02 - Siti Aisyah: last SpO2 96%, recovering but was warning → terisi
cur.execute("UPDATE incubators SET status='terisi' WHERE incubator_id=%s", (INC_02,))
# Inkubator 04 - Muhammad Farhan: still warning
cur.execute("UPDATE incubators SET status='warning' WHERE incubator_id=%s", (INC_04,))
# Inkubator 05 - Hana Putri: normal
cur.execute("UPDATE incubators SET status='terisi' WHERE incubator_id=%s", (INC_05,))

conn.commit()
cur.close()
conn.close()

print("\n✓ Done! Summary:")
print("  Ahmad Rizki  → 15 monitoring + 4 involvement records")
print("  Siti Aisyah  → 12 monitoring + 3 involvement records")
print("  M. Farhan    → 21 monitoring + 6 involvement records (warning status)")
print("  Hana Putri   →  6 monitoring + 3 involvement records")
print("  Total        → 54 monitoring + 16 involvement records")
