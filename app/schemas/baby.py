import uuid
from datetime import date, datetime, time
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


GenderType = Literal["laki_laki", "perempuan"]
BloodType = Literal["A", "B", "AB", "O"]
Pendidikan = Literal["tidak_sekolah", "sd", "smp", "sma", "diploma", "s1", "s2", "s3"]
JenisPersalinan = Literal["normal", "sc", "vakum", "forceps"]
KondisiUmum = Literal["baik", "cukup", "buruk"]
JenisKehamilan = Literal["tunggal", "kembar"]


# ---------- parent (unchanged: name / father / phone) ----------

class ParentCreate(BaseModel):
    mother_name: str | None = None
    father_name: str | None = None
    mother_phone: str | None = None
    mother_medical_history: str | None = None
    birth_history: str | None = None
    delivery_history: str | None = None
    additional_notes: str | None = None


class ParentResponse(BaseModel):
    parent_id: uuid.UUID
    mother_name: str | None
    father_name: str | None
    mother_phone: str | None
    mother_medical_history: str | None
    birth_history: str | None
    delivery_history: str | None
    additional_notes: str | None

    model_config = {"from_attributes": True}


# ---------- maternal record (updates02: Rekam Jejak Ibu Bayi) ----------

class MaternalCreate(BaseModel):
    # A. identitas ibu (name/phone stay in ParentCreate)
    no_rm_ibu: str | None = None
    umur_ibu: int | None = None
    pendidikan: Pendidikan | None = None
    pekerjaan: str | None = None
    alamat: str | None = None
    golongan_darah: BloodType | None = None
    # B. riwayat obstetri
    kehamilan_ke: int | None = None
    jumlah_persalinan_hidup: int | None = None
    riwayat_abortus: bool | None = None
    riwayat_prematur: bool | None = None
    riwayat_bblr: bool | None = None
    riwayat_bayi_meninggal: bool | None = None
    # C. riwayat kehamilan saat ini
    usia_kehamilan_lahir: int | None = None
    jenis_kehamilan: JenisKehamilan | None = None
    anc_rutin: bool | None = None
    jumlah_anc: int | None = None
    hipertensi_kehamilan: bool | None = None
    preeklamsia: bool | None = None
    diabetes_gestasional: bool | None = None
    infeksi_hamil: bool | None = None
    perdarahan_hamil: bool | None = None
    ketuban_pecah_dini: bool | None = None
    merokok: bool | None = None
    paparan_asap_rokok: bool | None = None
    konsumsi_alkohol: bool | None = None
    obat_tertentu: bool | None = None
    obat_tertentu_ket: str | None = None
    # D. riwayat persalinan
    tanggal_persalinan: date | None = None
    jenis_persalinan: JenisPersalinan | None = None
    tempat_persalinan: str | None = None
    indikasi_prematur: list[str] | None = None
    indikasi_prematur_lainnya: str | None = None
    komplikasi_persalinan: list[str] | None = None
    komplikasi_lainnya: str | None = None
    apgar_menit_1: int | None = None
    apgar_menit_5: int | None = None
    # E. kondisi ibu setelah melahirkan
    kondisi_umum: KondisiUmum | None = None
    masih_dirawat: bool | None = None
    komplikasi_postpartum: bool | None = None
    dapat_berjalan: bool | None = None
    dapat_menyusui: bool | None = None


class MaternalResponse(MaternalCreate):
    maternal_record_id: uuid.UUID

    model_config = {"from_attributes": True}


# ---------- assignment ----------

class AssignmentInfo(BaseModel):
    assignment_id: uuid.UUID
    incubator_id: uuid.UUID
    incubator_no: str
    location: str | None
    assigned_at: datetime
    assigned_by_name: str | None = None
    # registration data (updates02)
    no_registrasi_nicu: str | None = None
    rumah_sakit: str | None = None
    ruang_nicu: str | None = None
    dpjp_name: str | None = None


# ---------- baby request ----------

class BabyCreate(BaseModel):
    # baby identity
    baby_name: str
    gender: GenderType
    birth_date: date
    birth_weight: Decimal | None = None    # grams
    birth_length: Decimal | None = None    # cm
    gestational_age: int | None = None     # weeks
    birth_type: str | None = None
    clinical_notes: str | None = None
    # extended identity (updates02)
    no_rm_bayi: str | None = None
    jam_lahir: time | None = None
    usia_masuk_nicu_jam: int | None = None
    lingkar_kepala: Decimal | None = None
    lingkar_dada: Decimal | None = None
    golongan_darah: BloodType | None = None
    # parent (created together)
    parent: ParentCreate
    # mother's medical record (optional)
    maternal: MaternalCreate | None = None
    # assignment / registration
    incubator_id: uuid.UUID
    rumah_sakit: str | None = None
    ruang_nicu: str | None = None
    dpjp_id: uuid.UUID | None = None       # a doctor (role=dokter)


class BabyUpdate(BaseModel):
    baby_name: str | None = None
    clinical_notes: str | None = None
    birth_weight: Decimal | None = None


# ---------- baby response ----------

class BabyResponse(BaseModel):
    baby_id: uuid.UUID
    baby_name: str
    gender: str
    birth_date: date
    birth_weight: Decimal | None
    birth_length: Decimal | None
    gestational_age: int | None
    birth_type: str | None
    clinical_notes: str | None
    no_rm_bayi: str | None = None
    jam_lahir: time | None = None
    usia_masuk_nicu_jam: int | None = None
    lingkar_kepala: Decimal | None = None
    lingkar_dada: Decimal | None = None
    golongan_darah: str | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class BabyDetailResponse(BabyResponse):
    age_in_days: int
    parent: ParentResponse | None = None
    maternal: MaternalResponse | None = None
    current_assignment: AssignmentInfo | None = None
    latest_vitals: "MonitoringSummary | None" = None


class MonitoringSummary(BaseModel):
    monitoring_id: uuid.UUID
    observation_time: datetime
    suhu_bayi: Decimal | None
    suhu_inkubator: Decimal | None
    kelembapan_inkubator: Decimal | None
    heart_rate: int | None
    respiratory_rate: int | None
    spo2: Decimal | None
    expression_score: int | None
    movement_score: int | None
    pain_score: int | None
    sleep_duration_min: int | None
    sleep_quality: int | None
    agitation_episodes: int | None
    catatan: str | None
    foto_url: str | None
    vital_status: str = "normal"  # "normal" | "warning"
