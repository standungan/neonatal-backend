"""
Keterlibatan Orang Tua — PILAR 6: KERJASAMA DENGAN KELUARGA.

The parent-involvement instrument is Pillar 6 of the 8-pillar premature-baby
observation framework: 6 items, each scored 0–3 (3 = sesuai standar … 0 =
penyimpangan berat, perlu tindakan segera). This module is the single source of
truth; the API serves it to clients.

Replaces the earlier FICare 8-domain (0–4) Parent Engagement Index model.
"""

PILLAR_KEY = "keluarga"
PILLAR_LABEL = "Kerjasama dengan Keluarga"

# Ordered items (item_code = f"keluarga_{n}"), taken verbatim from the instrument.
ITEMS: list[str] = [
    "Ibu memberikan ASI/perah ASI",
    "Keluarga memahami kondisi bayi",
    "Keluarga terlibat dalam PMK",
    "Keluarga membantu perawatan dasar",
    "Keluarga mengikuti edukasi",
    "Keluarga memahami perawatan di rumah",
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
