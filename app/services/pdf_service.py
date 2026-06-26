from datetime import datetime, timezone
from io import BytesIO

from fpdf import FPDF

from app.schemas.report import BabyReportResponse

_GREY = (245, 245, 245)
_BLUE = (30, 90, 160)
_WHITE = (255, 255, 255)
_BLACK = (30, 30, 30)
_RED = (200, 50, 50)
_GREEN = (40, 140, 80)


class _Report(FPDF):
    def header(self):
        self.set_fill_color(*_BLUE)
        self.rect(0, 0, 210, 18, "F")
        self.set_text_color(*_WHITE)
        self.set_font("Helvetica", "B", 11)
        self.set_xy(10, 4)
        self.cell(0, 10, "NEONATAL CARE SYSTEM  |  Sistem Monitoring Bayi pada Inkubator", ln=False)
        self.set_text_color(*_BLACK)
        self.ln(18)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(120, 120, 120)
        now = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")
        self.cell(0, 10, f"Dicetak: {now}  |  Halaman {self.page_no()}", align="C")

    def section_title(self, title: str):
        self.set_fill_color(*_BLUE)
        self.set_text_color(*_WHITE)
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 8, f"  {title}", ln=True, fill=True)
        self.set_text_color(*_BLACK)
        self.ln(2)

    def kv_row(self, label: str, value: str, shade: bool = False):
        if shade:
            self.set_fill_color(*_GREY)
        else:
            self.set_fill_color(*_WHITE)
        self.set_font("Helvetica", "B", 9)
        self.cell(55, 7, label, fill=shade)
        self.set_font("Helvetica", "", 9)
        self.cell(0, 7, str(value) if value else "-", ln=True, fill=shade)


def generate_pdf(report: BabyReportResponse) -> bytes:
    pdf = _Report(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(left=12, top=22, right=12)
    pdf.add_page()

    baby = report.baby
    parent = baby.parent

    # ── Title ─────────────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Laporan Perkembangan Bayi", ln=True, align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f"Hari ke-{baby.age_in_days} dalam inkubator", ln=True, align="C")
    pdf.set_text_color(*_BLACK)
    pdf.ln(4)

    # ── Baby Info ──────────────────────────────────────────────────────────────
    pdf.section_title("1. Informasi Bayi")
    shade = False
    rows = [
        ("Nama Bayi",          baby.baby_name),
        ("Jenis Kelamin",      "Laki-laki" if baby.gender == "laki_laki" else "Perempuan"),
        ("Tanggal Lahir",      baby.birth_date.strftime("%d %b %Y")),
        ("Berat Lahir",        f"{baby.birth_weight} gram" if baby.birth_weight else "-"),
        ("Panjang Lahir",      f"{baby.birth_length} cm" if baby.birth_length else "-"),
        ("Usia Gestasi",       f"{baby.gestational_age} minggu" if baby.gestational_age else "-"),
        ("Jenis Kelahiran",    baby.birth_type or "-"),
        ("Usia Saat Ini",      f"{baby.age_in_days} hari"),
    ]
    if baby.current_assignment:
        rows.append(("Inkubator",   f"No. {baby.current_assignment.incubator_no}  |  {baby.current_assignment.location or '-'}"))
        rows.append(("Tanggal Masuk", baby.current_assignment.assigned_at.strftime("%d %b %Y %H:%M")))
    for label, val in rows:
        pdf.kv_row(label, val, shade)
        shade = not shade
    pdf.ln(4)

    # ── Parent Info ────────────────────────────────────────────────────────────
    if parent:
        pdf.section_title("2. Informasi Orang Tua")
        shade = False
        for label, val in [
            ("Nama Ibu",        parent.mother_name or "-"),
            ("Nama Ayah",       parent.father_name or "-"),
            ("No. Telepon",     parent.mother_phone or "-"),
            ("Riwayat Medis",   parent.mother_medical_history or "-"),
        ]:
            pdf.kv_row(label, val, shade)
            shade = not shade
        pdf.ln(4)

    # ── Latest Vitals ──────────────────────────────────────────────────────────
    if baby.latest_vitals:
        v = baby.latest_vitals
        pdf.section_title("3. Kondisi Terkini")
        shade = False
        vitals = [
            ("Waktu Observasi",   v.observation_time.strftime("%d %b %Y %H:%M")),
            ("Suhu Bayi",         f"{v.suhu_bayi} C" if v.suhu_bayi else "-"),
            ("Suhu Inkubator",    f"{v.suhu_inkubator} C" if v.suhu_inkubator else "-"),
            ("Kelembapan Inkubator", f"{v.kelembapan_inkubator} %" if v.kelembapan_inkubator else "-"),
            ("Heart Rate",        f"{v.heart_rate} bpm" if v.heart_rate else "-"),
            ("Respiratory Rate",  f"{v.respiratory_rate} /min" if v.respiratory_rate else "-"),
            ("SpO2",              f"{v.spo2} %" if v.spo2 else "-"),
            ("Expression Score",  f"{v.expression_score} / 5" if v.expression_score else "-"),
            ("Movement Score",    f"{v.movement_score} / 5" if v.movement_score else "-"),
            ("Pain Score (NIPS)", f"{v.pain_score} / 7" if v.pain_score is not None else "-"),
            ("Durasi Tidur",      f"{v.sleep_duration_min} menit" if v.sleep_duration_min else "-"),
            ("Kualitas Tidur",    f"{v.sleep_quality} / 5" if v.sleep_quality else "-"),
            ("Episode Gelisah",   str(v.agitation_episodes) if v.agitation_episodes is not None else "-"),
        ]
        for label, val in vitals:
            pdf.kv_row(label, val, shade)
            shade = not shade
        pdf.ln(4)

    # ── Monitoring History Table ───────────────────────────────────────────────
    pdf.section_title("4. Riwayat Monitoring")
    headers = ["Tanggal & Waktu", "Suhu", "HR", "RR", "SpO2", "Eksp", "Gerak", "Nyeri"]
    col_w = [40, 22, 18, 18, 22, 18, 18, 18]

    pdf.set_fill_color(210, 220, 240)
    pdf.set_font("Helvetica", "B", 8)
    for h, w in zip(headers, col_w):
        pdf.cell(w, 7, h, border=1, fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 8)
    for i, rec in enumerate(report.monitoring_history[:20]):   # cap at 20 rows
        fill = i % 2 == 0
        pdf.set_fill_color(*(_GREY if fill else _WHITE))
        row_data = [
            rec.observation_time.strftime("%d %b %Y %H:%M"),
            str(rec.suhu_bayi) if rec.suhu_bayi else "-",
            str(rec.heart_rate) if rec.heart_rate else "-",
            str(rec.respiratory_rate) if rec.respiratory_rate else "-",
            str(rec.spo2) if rec.spo2 else "-",
            str(rec.expression_score) if rec.expression_score else "-",
            str(rec.movement_score) if rec.movement_score else "-",
            str(rec.pain_score) if rec.pain_score is not None else "-",
        ]
        for val, w in zip(row_data, col_w):
            pdf.cell(w, 6, val, border=1, fill=fill)
        pdf.ln()
    pdf.ln(4)

    # ── Involvement Summary ───────────────────────────────────────────────────
    s = report.involvement_summary
    pdf.section_title("5. Ringkasan Keterlibatan Orang Tua")
    shade = False
    inv_rows = [
        ("Total Sesi",               str(s.total_sessions)),
        ("Rata-rata Skor",           f"{s.avg_skor:.1f} / 100" if s.avg_skor else "-"),
        ("Skor Terakhir",            f"{s.latest_skor} / 100  ({s.latest_kategori})" if s.latest_skor is not None else "-"),
        ("Rata-rata Durasi Menyusui", f"{s.avg_durasi_menyusui:.1f} menit" if s.avg_durasi_menyusui else "-"),
        ("Rata-rata Durasi Interaksi", f"{s.avg_durasi_interaksi:.1f} menit" if s.avg_durasi_interaksi else "-"),
    ]
    for label, val in inv_rows:
        pdf.kv_row(label, val, shade)
        shade = not shade
    pdf.ln(4)

    # ── Pillar 8 domain breakdown (latest assessment) ──────────────────────────
    if report.involvement_history:
        latest = report.involvement_history[0]
        pdf.section_title("6. Rincian Keterlibatan (8 Domain FICare)")
        shade = False
        domains = [
            ("Kehadiran (Presence)",            latest.presence_score),
            ("Interaksi Fisik",                 latest.physical_interaction_score),
            ("Partisipasi Menyusui",            latest.feeding_participation_score),
            ("Partisipasi Perawatan",           latest.care_participation_score),
            ("Pemahaman Kondisi",               latest.knowledge_score),
            ("Komunikasi Klinis",               latest.communication_score),
            ("Kesiapan Emosional",              latest.emotional_readiness_score),
            ("Kesiapan Pulang",                 latest.discharge_readiness_score),
        ]
        for label, val in domains:
            pdf.kv_row(label, f"{val} / 4" if val is not None else "-", shade)
            shade = not shade

    buf = BytesIO()
    buf.write(pdf.output())
    return buf.getvalue()
