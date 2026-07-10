"""
Menu Aksi — PILAR 8: KOLABORASI INTERPROFESIONAL.

Interprofessional-collaboration actions, pulled out of the Monitoring Bayi
(8-pillar observation) instrument into their own module: 6 items, each scored
0–3 (3 = sesuai standar … 0 = penyimpangan berat, perlu tindakan segera).
This module is the single source of truth; the API serves it to clients.
"""

PILLAR_KEY = "kolaborasi"
PILLAR_LABEL = "Kolaborasi Interprofesional"

# Ordered items (item_code = f"kolaborasi_{n}"), taken verbatim from the instrument.
ITEMS: list[str] = [
    "Catatan CPPT lengkap",
    "SBAR dilakukan saat handover",
    "Instruksi dokter terdokumentasi",
    "Perubahan kondisi bayi segera dilaporkan",
    "Kolaborasi dokter-perawat berjalan baik",
    "Seluruh tindakan terdokumentasi",
]

MAX_PER_ITEM = 3

# Flat catalog: [{item_code, text}, ...] and helpers.
CATALOG: list[dict] = [
    {"item_code": f"{PILLAR_KEY}_{i}", "text": text}
    for i, text in enumerate(ITEMS, start=1)
]
ALL_ITEM_CODES: list[str] = [c["item_code"] for c in CATALOG]
TOTAL_ITEMS = len(ALL_ITEM_CODES)              # 6
MAX_TOTAL = TOTAL_ITEMS * MAX_PER_ITEM         # 18


def category_for(percentage: float) -> str:
    if percentage >= 85:
        return "Sangat Baik"
    if percentage >= 70:
        return "Baik"
    if percentage >= 55:
        return "Cukup"
    if percentage >= 40:
        return "Kurang"
    return "Sangat Kurang"
