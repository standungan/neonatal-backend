from datetime import datetime, timezone
from io import BytesIO

from fpdf import FPDF

from app.schemas.report import BabyReportResponse

# ── palette ───────────────────────────────────────────────────────────────────
_BLUE = (30, 90, 160)
_BLUE_L = (222, 232, 245)
_GREY = (245, 246, 248)
_LINE = (223, 227, 233)
_WHITE = (255, 255, 255)
_BLACK = (33, 37, 41)
_MUTE = (120, 128, 138)
_GREEN = (40, 140, 80)
_AMBER = (200, 150, 30)
_RED = (200, 60, 60)
_BAND = (223, 244, 231)

CONTENT_W = 186.0  # A4 width 210 - margins 12*2

# ── enum labels ────────────────────────────────────────────────────────────────
_PENDIDIKAN = {"tidak_sekolah": "Tidak Sekolah", "sd": "SD", "smp": "SMP", "sma": "SMA",
               "diploma": "Diploma", "s1": "S1", "s2": "S2", "s3": "S3"}
_JNS_PERSALINAN = {"normal": "Normal", "sc": "Sectio Caesarea", "vakum": "Vakum", "forceps": "Forceps"}
_KONDISI = {"baik": "Baik", "cukup": "Cukup", "buruk": "Buruk"}
_JNS_KEHAMILAN = {"tunggal": "Tunggal", "kembar": "Kembar"}


def _lbl(m: dict, v) -> str:
    return m.get(v, v) if v else "-"


def _yn(v) -> str:
    return "-" if v is None else ("Ya" if v else "Tidak")


def _txt(v, suffix: str = "") -> str:
    if v is None or v == "":
        return "-"
    return f"{v}{suffix}"


def _pct_color(pct: float) -> tuple:
    if pct >= 85:
        return _GREEN
    if pct >= 70:
        return _BLUE
    if pct >= 55:
        return _AMBER
    if pct >= 40:
        return (200, 110, 40)
    return _RED


class _Report(FPDF):
    def header(self):
        self.set_fill_color(*_BLUE)
        self.rect(0, 0, 210, 16, "F")
        self.set_text_color(*_WHITE)
        self.set_font("Helvetica", "B", 10)
        self.set_xy(12, 4.5)
        self.cell(0, 8, "NEONATAL CARE SYSTEM   |   Sistem Monitoring Bayi pada Inkubator")
        self.set_text_color(*_BLACK)
        self.set_y(22)

    def footer(self):
        self.set_y(-11)
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*_MUTE)
        now = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")
        self.cell(0, 8, f"Dicetak: {now}          Halaman {self.page_no()}", align="C")
        self.set_text_color(*_BLACK)

    def ensure_space(self, h: float):
        """Start a new page if less than `h` mm remains — keeps a block together."""
        if self.get_y() + h > self.page_break_trigger:
            self.add_page()

    # ── building blocks ─────────────────────────────────────────────────────────
    def section(self, title: str):
        self.ln(1)
        self.set_fill_color(*_BLUE)
        self.set_text_color(*_WHITE)
        self.set_font("Helvetica", "B", 9.5)
        self.cell(CONTENT_W, 7, f"  {title}", ln=True, fill=True)
        self.set_text_color(*_BLACK)
        self.ln(1.5)

    def subsection(self, title: str):
        self.set_font("Helvetica", "B", 8.5)
        self.set_text_color(*_BLUE)
        self.cell(CONTENT_W, 5.5, title, ln=True)
        self.set_text_color(*_BLACK)

    def kv2(self, pairs: list[tuple[str, str]]):
        """Two label/value pairs per row."""
        colw = CONTENT_W / 2
        lab_w, val_w = 34.0, colw - 34.0
        i = 0
        while i < len(pairs):
            shade = (i // 2) % 2 == 1
            self.set_fill_color(*(_GREY if shade else _WHITE))
            for j in range(2):
                if i + j < len(pairs):
                    label, value = pairs[i + j]
                    self.set_font("Helvetica", "B", 8)
                    self.cell(lab_w, 6, f" {label}", fill=True)
                    self.set_font("Helvetica", "", 8)
                    self.cell(val_w, 6, str(value) if value not in (None, "") else "-", fill=True)
                else:
                    self.cell(colw, 6, "", fill=True)
            self.ln()
            i += 2

    def kv_long(self, label: str, value: str):
        self.set_font("Helvetica", "B", 8)
        self.cell(34, 5.5, f" {label}", ln=False)
        self.set_font("Helvetica", "", 8)
        x = self.get_x()
        self.multi_cell(CONTENT_W - 34, 5.5, value if value else "-")
        self.set_x(self.l_margin)

    def badge(self, text: str, color: tuple):
        self.set_font("Helvetica", "B", 8)
        w = self.get_string_width(text) + 6
        x, y = self.get_x(), self.get_y()
        self.set_fill_color(*color)
        self.set_text_color(*_WHITE)
        self.rect(x, y, w, 5.5, "F")
        self.set_xy(x, y)
        self.cell(w, 5.5, text, align="C")
        self.set_text_color(*_BLACK)
        self.set_xy(x + w + 3, y)

    def score_bar(self, label: str, score: int, maxv: int, pct: float):
        y = self.get_y()
        self.set_font("Helvetica", "", 8)
        self.cell(58, 5, label[:44])
        bx, bw, bh = self.get_x(), 78.0, 3.4
        by = y + 0.8
        self.set_fill_color(233, 236, 240)
        self.rect(bx, by, bw, bh, "F")
        self.set_fill_color(*_pct_color(pct))
        self.rect(bx, by, max(0.0, bw * pct / 100.0), bh, "F")
        self.set_xy(bx + bw + 3, y)
        self.set_font("Helvetica", "B", 8)
        self.cell(0, 5, f"{score}/{maxv}  ({pct:.0f}%)", ln=True)

    def assessment_head(self, title: str, total: int, maxv: int, pct: float, category: str | None):
        self.subsection(title)
        self.set_x(self.l_margin)
        self.badge(f"{pct:.0f}%  {category or ''}".strip(), _pct_color(pct))
        self.set_font("Helvetica", "", 8)
        self.cell(0, 5.5, f"Total {total}/{maxv}", ln=True)
        self.ln(1)

    def line_chart(self, x: float, y: float, w: float, h: float, title: str,
                   values: list, ymin: float, ymax: float, band=None, latest=None):
        self.set_font("Helvetica", "B", 7.5)
        self.set_text_color(*_BLUE)
        self.set_xy(x, y)
        self.cell(w, 4, title)
        if latest is not None:
            self.set_xy(x, y)   # same box — draw the latest value right-aligned
            self.set_text_color(*_MUTE)
            self.set_font("Helvetica", "", 7)
            self.cell(w, 4, f"terakhir: {latest}", align="R")
        self.set_text_color(*_BLACK)
        top = y + 5
        self.set_draw_color(*_LINE)
        self.set_line_width(0.2)
        if band:
            def yb(v):
                v = max(ymin, min(ymax, v))
                return top + h * (1 - (v - ymin) / (ymax - ymin))
            self.set_fill_color(*_BAND)
            y1, y2 = yb(band[1]), yb(band[0])
            self.rect(x, y1, w, y2 - y1, "F")
        self.rect(x, top, w, h)
        pts = [(i, v) for i, v in enumerate(values) if v is not None]
        if len(pts) >= 2:
            n = len(values)
            def px(i): return x + (w * i / (n - 1))
            def py(v):
                v = max(ymin, min(ymax, v))
                return top + h * (1 - (v - ymin) / (ymax - ymin))
            coords = [(px(i), py(v)) for i, v in pts]
            self.set_draw_color(*_BLUE)
            self.set_line_width(0.5)
            for a, b in zip(coords, coords[1:]):
                self.line(a[0], a[1], b[0], b[1])
            self.set_fill_color(*_BLUE)
            for cx, cy in coords:
                self.ellipse(cx - 0.7, cy - 0.7, 1.4, 1.4, "F")
        else:
            self.set_font("Helvetica", "", 6.5)
            self.set_text_color(*_MUTE)
            self.set_xy(x, top + h / 2 - 2)
            self.cell(w, 4, "data belum cukup", align="C")
            self.set_text_color(*_BLACK)


def _fnum(v):
    return "-" if v is None else (f"{v:g}" if isinstance(v, (int, float)) else str(v))


def generate_pdf(report: BabyReportResponse) -> bytes:
    pdf = _Report(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.set_margins(left=12, top=22, right=12)
    pdf.add_page()

    baby = report.baby
    parent = baby.parent
    maternal = baby.maternal
    asg = baby.current_assignment

    # ── title block ─────────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, "Laporan Perkembangan Bayi", ln=True, align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*_MUTE)
    reg = asg.no_registrasi_nicu if asg and asg.no_registrasi_nicu else "-"
    pdf.cell(0, 5, f"{baby.baby_name}   -   No. Registrasi {reg}   -   Hari ke-{baby.age_in_days}",
             ln=True, align="C")
    pdf.set_text_color(*_BLACK)
    pdf.ln(2)

    # ── 1. Data Registrasi ───────────────────────────────────────────────────────
    pdf.section("1. Data Registrasi")
    reg_pairs = [
        ("No. Reg NICU", reg),
        ("Tgl Masuk", asg.assigned_at.strftime("%d %b %Y %H:%M") if asg else "-"),
        ("Rumah Sakit", (asg.rumah_sakit if asg else None) or "-"),
        ("Ruang NICU", (asg.ruang_nicu if asg else None) or "-"),
        ("Inkubator", f"No. {asg.incubator_no}" if asg else "-"),
        ("Lokasi", (asg.location if asg else None) or "-"),
        ("DPJP", (asg.dpjp_name if asg else None) or "-"),
        ("Perawat Penerima", (asg.assigned_by_name if asg else None) or "-"),
    ]
    pdf.kv2(reg_pairs)
    pdf.ln(2)

    # ── 2. Identitas Bayi ────────────────────────────────────────────────────────
    pdf.section("2. Identitas Bayi")
    pdf.kv2([
        ("Nama", baby.baby_name),
        ("No. RM Bayi", baby.no_rm_bayi or "-"),
        ("Jenis Kelamin", "Laki-laki" if baby.gender == "laki_laki" else "Perempuan"),
        ("Gol. Darah", baby.golongan_darah or "-"),
        ("Tanggal Lahir", baby.birth_date.strftime("%d %b %Y")),
        ("Jam Lahir", baby.jam_lahir.strftime("%H:%M") if baby.jam_lahir else "-"),
        ("Usia Gestasi", _txt(baby.gestational_age, " mgg")),
        ("Usia Masuk NICU", _txt(baby.usia_masuk_nicu_jam, " jam")),
        ("Berat Lahir", _txt(_fnum(baby.birth_weight), " g") if baby.birth_weight else "-"),
        ("Panjang Lahir", _txt(_fnum(baby.birth_length), " cm") if baby.birth_length else "-"),
        ("Lingkar Kepala", _txt(_fnum(baby.lingkar_kepala), " cm") if baby.lingkar_kepala else "-"),
        ("Lingkar Dada", _txt(_fnum(baby.lingkar_dada), " cm") if baby.lingkar_dada else "-"),
        ("Jenis Kelahiran", baby.birth_type or "-"),
        ("Usia Saat Ini", f"{baby.age_in_days} hari"),
    ])
    pdf.ln(2)

    # ── 3. Rekam Medis Ibu ───────────────────────────────────────────────────────
    pdf.section("3. Rekam Medis Ibu")
    if maternal or parent:
        m = maternal
        pdf.subsection("A. Identitas Ibu")
        pdf.kv2([
            ("Nama Ibu", (parent.mother_name if parent else None) or "-"),
            ("No. Telepon", (parent.mother_phone if parent else None) or "-"),
            ("No. RM Ibu", (m.no_rm_ibu if m else None) or "-"),
            ("Umur", _txt(m.umur_ibu, " th") if m else "-"),
            ("Pendidikan", _lbl(_PENDIDIKAN, m.pendidikan) if m else "-"),
            ("Pekerjaan", (m.pekerjaan if m else None) or "-"),
            ("Gol. Darah", (m.golongan_darah if m else None) or "-"),
        ])
        if m and m.alamat:
            pdf.kv_long("Alamat", m.alamat)
        if m:
            pdf.ln(1)
            pdf.subsection("B. Riwayat Obstetri")
            pdf.kv2([
                ("Kehamilan ke-", _txt(m.kehamilan_ke)),
                ("Persalinan Hidup", _txt(m.jumlah_persalinan_hidup)),
                ("Riwayat Abortus", _yn(m.riwayat_abortus)),
                ("Riwayat Prematur", _yn(m.riwayat_prematur)),
                ("Riwayat BBLR", _yn(m.riwayat_bblr)),
                ("Riwayat Bayi Meninggal", _yn(m.riwayat_bayi_meninggal)),
            ])
            pdf.ln(1)
            pdf.subsection("C. Riwayat Kehamilan Saat Ini")
            pdf.kv2([
                ("Usia Kehamilan Lahir", _txt(m.usia_kehamilan_lahir, " mgg")),
                ("Kehamilan", _lbl(_JNS_KEHAMILAN, m.jenis_kehamilan)),
                ("Rutin ANC", _yn(m.anc_rutin)),
                ("Jml Kunjungan ANC", _txt(m.jumlah_anc)),
                ("Hipertensi", _yn(m.hipertensi_kehamilan)),
                ("Preeklamsia", _yn(m.preeklamsia)),
                ("Diabetes Gestasional", _yn(m.diabetes_gestasional)),
                ("Infeksi Saat Hamil", _yn(m.infeksi_hamil)),
                ("Perdarahan", _yn(m.perdarahan_hamil)),
                ("Ketuban Pecah Dini", _yn(m.ketuban_pecah_dini)),
                ("Merokok", _yn(m.merokok)),
                ("Paparan Asap Rokok", _yn(m.paparan_asap_rokok)),
                ("Konsumsi Alkohol", _yn(m.konsumsi_alkohol)),
                ("Obat Tertentu", _yn(m.obat_tertentu)),
            ])
            if m.obat_tertentu_ket:
                pdf.kv_long("Ket. Obat", m.obat_tertentu_ket)
            pdf.ln(1)
            pdf.subsection("D. Riwayat Persalinan")
            pdf.kv2([
                ("Tanggal Persalinan", m.tanggal_persalinan.strftime("%d %b %Y") if m.tanggal_persalinan else "-"),
                ("Jenis Persalinan", _lbl(_JNS_PERSALINAN, m.jenis_persalinan)),
                ("Tempat Persalinan", m.tempat_persalinan or "-"),
                ("APGAR 1' / 5'", f"{_txt(m.apgar_menit_1)} / {_txt(m.apgar_menit_5)}"),
            ])
            ind = ", ".join(m.indikasi_prematur or []) or "-"
            if m.indikasi_prematur_lainnya:
                ind += f" (lainnya: {m.indikasi_prematur_lainnya})"
            pdf.kv_long("Indikasi Prematur", ind)
            komp = ", ".join(m.komplikasi_persalinan or []) or "-"
            if m.komplikasi_lainnya:
                komp += f" (lainnya: {m.komplikasi_lainnya})"
            pdf.kv_long("Komplikasi Persalinan", komp)
            pdf.ln(1)
            pdf.subsection("E. Kondisi Ibu Setelah Melahirkan")
            pdf.kv2([
                ("Kondisi Umum", _lbl(_KONDISI, m.kondisi_umum)),
                ("Masih Dirawat", _yn(m.masih_dirawat)),
                ("Komplikasi Postpartum", _yn(m.komplikasi_postpartum)),
                ("Dapat Berjalan", _yn(m.dapat_berjalan)),
                ("Dapat Menyusui", _yn(m.dapat_menyusui)),
            ])
    else:
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(*_MUTE)
        pdf.cell(0, 6, "Belum ada rekam medis ibu.", ln=True)
        pdf.set_text_color(*_BLACK)
    pdf.ln(2)

    # ── 4. Kondisi Terkini ───────────────────────────────────────────────────────
    if baby.latest_vitals:
        v = baby.latest_vitals
        pdf.section("4. Kondisi Terkini (Vital)")
        warn = v.vital_status == "warning"
        pdf.set_x(pdf.l_margin)
        pdf.badge("PERHATIAN" if warn else "NORMAL", _RED if warn else _GREEN)
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(0, 5.5, f"Observasi: {v.observation_time.strftime('%d %b %Y %H:%M')}", ln=True)
        pdf.ln(1)
        pdf.kv2([
            ("Suhu Bayi", _txt(_fnum(v.suhu_bayi), " C")),
            ("Suhu Inkubator", _txt(_fnum(v.suhu_inkubator), " C")),
            ("Kelembapan Ink.", _txt(_fnum(v.kelembapan_inkubator), " %")),
            ("Heart Rate", _txt(v.heart_rate, " bpm")),
            ("Respiratory Rate", _txt(v.respiratory_rate, " /mnt")),
            ("SpO2", _txt(_fnum(v.spo2), " %")),
            ("Nyeri (NIPS)", f"{v.pain_score} / 7" if v.pain_score is not None else "-"),
            ("Ekspresi", f"{v.expression_score} / 5" if v.expression_score else "-"),
            ("Gerakan", f"{v.movement_score} / 5" if v.movement_score else "-"),
            ("Durasi Tidur", _txt(v.sleep_duration_min, " mnt")),
            ("Kualitas Tidur", f"{v.sleep_quality} / 5" if v.sleep_quality else "-"),
            ("Episode Gelisah", _txt(v.agitation_episodes)),
        ])
        pdf.ln(2)

    # ── 5. Grafik Tren Vital ─────────────────────────────────────────────────────
    hist = list(reversed(report.monitoring_history))  # oldest -> newest
    if len(hist) >= 2:
        pdf.ensure_space(42)
        pdf.section("5. Grafik Tren Vital")
        gap = 6
        cw = (CONTENT_W - 2 * gap) / 3
        x0 = pdf.l_margin
        y0 = pdf.get_y()
        ch = 24.0
        def col(vals):
            return [float(x) if x is not None else None for x in vals]
        suhu = col([r.suhu_bayi for r in hist])
        hr = col([r.heart_rate for r in hist])
        spo2 = col([r.spo2 for r in hist])
        pdf.line_chart(x0, y0, cw, ch, "Suhu Bayi (C)", suhu, 34, 40, band=(36, 37.5),
                       latest=_fnum(hist[-1].suhu_bayi))
        pdf.line_chart(x0 + cw + gap, y0, cw, ch, "Heart Rate (bpm)", hr, 70, 200, band=(100, 160),
                       latest=_fnum(hist[-1].heart_rate))
        pdf.line_chart(x0 + 2 * (cw + gap), y0, cw, ch, "SpO2 (%)", spo2, 80, 100, band=(93, 100),
                       latest=_fnum(hist[-1].spo2))
        pdf.set_y(y0 + ch + 7)
        pdf.set_font("Helvetica", "", 6.5)
        pdf.set_text_color(*_MUTE)
        pdf.cell(0, 4, "Area hijau = rentang normal.", ln=True)
        pdf.set_text_color(*_BLACK)
        pdf.ln(1)

    # ── 6. Riwayat Monitoring ────────────────────────────────────────────────────
    pdf.section("6. Riwayat Monitoring")
    headers = ["Tanggal & Waktu", "Suhu", "HR", "RR", "SpO2", "Nyeri", "Status"]
    col_w = [42, 24, 24, 24, 24, 24, 24]
    pdf.set_fill_color(*_BLUE_L)
    pdf.set_font("Helvetica", "B", 8)
    for h, w in zip(headers, col_w):
        pdf.cell(w, 6.5, f" {h}", border=1, fill=True)
    pdf.ln()
    pdf.set_font("Helvetica", "", 8)
    if not report.monitoring_history:
        pdf.set_text_color(*_MUTE)
        pdf.cell(0, 6, "  Belum ada data monitoring.", ln=True)
        pdf.set_text_color(*_BLACK)
    for i, rec in enumerate(report.monitoring_history[:15]):
        fill = i % 2 == 0
        pdf.set_fill_color(*(_GREY if fill else _WHITE))
        cells = [
            (f" {rec.observation_time.strftime('%d %b %Y %H:%M')}", "L"),
            (_txt(_fnum(rec.suhu_bayi)), "C"),
            (_txt(rec.heart_rate), "C"),
            (_txt(rec.respiratory_rate), "C"),
            (_txt(_fnum(rec.spo2)), "C"),
            (_txt(rec.pain_score) if rec.pain_score is not None else "-", "C"),
            ("Warning" if rec.vital_status == "warning" else "Normal", "C"),
        ]
        for (val, align), w in zip(cells, col_w):
            if val in ("Warning", "Normal"):
                pdf.set_text_color(*(_RED if val == "Warning" else _GREEN))
                pdf.cell(w, 6, val, border=1, fill=True, align=align)
                pdf.set_text_color(*_BLACK)
            else:
                pdf.cell(w, 6, val, border=1, fill=True, align=align)
        pdf.ln()
    pdf.ln(2)

    # ── 7. Penilaian 8 Pilar ─────────────────────────────────────────────────────
    pdf.section("7. Penilaian 8 Pilar Perawatan")
    obs = report.observation_latest
    inv = report.involvement_history[0] if report.involvement_history else None
    aksi = report.aksi_latest

    if obs:
        pdf.ensure_space(50)
        pdf.assessment_head(
            f"Observasi 'Monitoring Bayi' - 6 Pilar  ({obs.observation_time.strftime('%d %b %Y')})",
            obs.total_score, obs.max_total, obs.percentage, obs.category)
        for p in obs.pillars:
            pdf.score_bar(p.label, p.score, p.max, p.percentage)
        pdf.ln(2)

    if inv:
        pdf.ensure_space(50)
        pdf.assessment_head(
            f"Pilar 6 - Keterlibatan Orang Tua  ({inv.observation_time.strftime('%d %b %Y')})",
            inv.total_score, inv.max_total, inv.percentage, inv.category)
        for it in inv.items:
            pct = (it.score / it.max * 100) if it.max else 0
            pdf.score_bar(it.text, it.score, it.max, pct)
        pdf.ln(2)

    if aksi:
        pdf.ensure_space(50)
        pdf.assessment_head(
            f"Pilar 8 - Kolaborasi Interprofesional  ({aksi.observation_time.strftime('%d %b %Y')})",
            aksi.total_score, aksi.max_total, aksi.percentage, aksi.category)
        for it in aksi.items:
            pct = (it.score / it.max * 100) if it.max else 0
            pdf.score_bar(it.text, it.score, it.max, pct)
        pdf.ln(1)

    if not (obs or inv or aksi):
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(*_MUTE)
        pdf.cell(0, 6, "Belum ada data penilaian 8 pilar.", ln=True)
        pdf.set_text_color(*_BLACK)

    buf = BytesIO()
    buf.write(pdf.output())
    return buf.getvalue()
