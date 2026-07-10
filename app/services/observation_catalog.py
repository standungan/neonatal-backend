"""
Instrumen Observasi Perawatan Bayi Prematur — Delapan Pilar.

Catalog of the observation items across 6 pillars (42 items), each scored 0–3
(3 = sesuai standar … 0 = penyimpangan berat, tindakan segera). This module is
the single source of truth; the API serves it to clients.

Note: two pillars are intentionally NOT part of this clinical instrument, each
covered by its own separate module:
  - "Kerjasama dengan Keluarga"     → Keterlibatan Orang Tua (involvement).
  - "Kolaborasi Interprofesional"   → Aksi (aksi module).
"""

# Each pillar: key, human label, and its ordered items as (item_code, text).
# item_code = f"{pillar_key}_{n}" (stable identifier used in the stored JSONB).

PILLARS: list[dict] = [
    {
        "key": "tidur",
        "label": "Menjaga Masa Tidur Bayi",
        "items": [
            "Bayi memperoleh periode tidur tanpa gangguan minimal 60 menit",
            "Bayi mudah kembali tidur setelah tindakan",
            "Bayi tidak sering terbangun akibat kebisingan",
            "Bayi menunjukkan tidur tenang tanpa menangis berlebihan",
            "Pencahayaan inkubator sesuai kebutuhan",
            "Kebisingan ruangan terkendali",
            "Nesting terpasang dengan benar",
            "Posisi bayi nyaman selama tidur",
        ],
    },
    {
        "key": "nyeri",
        "label": "Manajemen Stres dan Nyeri",
        "items": [
            "Ekspresi wajah menunjukkan kenyamanan",
            "Tangisan terkendali",
            "Gerakan ekstremitas tenang",
            "Skor NIPS dalam batas normal",
            "Bayi tenang setelah tindakan invasif",
            "Tidak terdapat tanda stres fisiologis",
        ],
    },
    {
        "key": "posisi",
        "label": "Posisi dan Penanganan Bayi",
        "items": [
            "Posisi bayi sesuai diagnosis",
            "Posisi fleksi dipertahankan",
            "Kepala dan leher sejajar",
            "Perubahan posisi dilakukan sesuai jadwal",
            "Tidak terdapat tekanan berlebih pada tubuh",
            "Selang medis tetap aman saat perubahan posisi",
        ],
    },
    {
        "key": "kulit",
        "label": "Perlindungan Kulit",
        "items": [
            "Kulit utuh tanpa luka",
            "Tidak terdapat ruam popok",
            "Tidak terdapat iritasi plester",
            "Area sensor monitor tidak mengalami iritasi",
            "Tali pusat bersih",
            "Tidak ada tanda flebitis",
            "Warna kulit normal",
            "Kelembaban inkubator sesuai standar",
        ],
    },
    {
        "key": "nutrisi",
        "label": "Nutrisi Optimal",
        "items": [
            "Nutrisi diberikan sesuai jadwal",
            "Volume nutrisi sesuai kebutuhan",
            "ASI diberikan sesuai program",
            "Tidak terjadi muntah setelah pemberian nutrisi",
            "Balance cairan sesuai target",
            "Berat badan meningkat sesuai target",
            "Tidak terdapat intoleransi nutrisi",
            "OGT terpasang dengan baik (bila ada)",
        ],
    },
    {
        "key": "lingkungan",
        "label": "Lingkungan Penyembuhan",
        "items": [
            "Suhu ruangan sesuai standar",
            "Humidity inkubator sesuai standar",
            "Pencahayaan sesuai standar",
            "Kebisingan <45 dB",
            "Alarm tidak berbunyi terus-menerus",
            "Lingkungan sekitar bersih dan nyaman",
        ],
    },
]

MAX_PER_ITEM = 3

# Flat catalog: [{pillar_key, pillar_label, item_code, text}, ...]
CATALOG: list[dict] = []
# item_code -> pillar_key
ITEM_TO_PILLAR: dict[str, str] = {}
for _p in PILLARS:
    for _i, _text in enumerate(_p["items"], start=1):
        _code = f"{_p['key']}_{_i}"
        CATALOG.append(
            {"pillar_key": _p["key"], "pillar_label": _p["label"], "item_code": _code, "text": _text}
        )
        ITEM_TO_PILLAR[_code] = _p["key"]

ALL_ITEM_CODES: list[str] = [c["item_code"] for c in CATALOG]
TOTAL_ITEMS = len(ALL_ITEM_CODES)                 # 42
MAX_TOTAL = TOTAL_ITEMS * MAX_PER_ITEM            # 126


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
