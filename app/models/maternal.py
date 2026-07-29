import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MaternalRecord(Base):
    """Mother's structured medical record (updates02 — Rekam Jejak Ibu Bayi).

    1:1 with a baby. Mother name/phone stay in `parents`; this holds the fuller
    obstetric/pregnancy/delivery record. All fields nullable — filled as far as
    known at registration time.
    """

    __tablename__ = "maternal_records"

    maternal_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    baby_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("babies.baby_id", ondelete="CASCADE"),
        unique=True, nullable=False,
    )

    # ── A. Identitas ibu (name/phone live in parents) ──────────────────────────
    no_rm_ibu: Mapped[str | None] = mapped_column(String(50))
    umur_ibu: Mapped[int | None] = mapped_column(SmallInteger)
    pendidikan: Mapped[str | None] = mapped_column(
        Enum("tidak_sekolah", "sd", "smp", "sma", "diploma", "s1", "s2", "s3",
             name="pendidikan_type")
    )
    pekerjaan: Mapped[str | None] = mapped_column(String(100))
    alamat: Mapped[str | None] = mapped_column(Text)
    golongan_darah: Mapped[str | None] = mapped_column(
        Enum("A", "B", "AB", "O", name="blood_type")
    )

    # ── B. Riwayat obstetri ────────────────────────────────────────────────────
    kehamilan_ke: Mapped[int | None] = mapped_column(SmallInteger)
    jumlah_persalinan_hidup: Mapped[int | None] = mapped_column(SmallInteger)
    riwayat_abortus: Mapped[bool | None] = mapped_column(Boolean)
    riwayat_prematur: Mapped[bool | None] = mapped_column(Boolean)
    riwayat_bblr: Mapped[bool | None] = mapped_column(Boolean)
    riwayat_bayi_meninggal: Mapped[bool | None] = mapped_column(Boolean)

    # ── C. Riwayat kehamilan saat ini ──────────────────────────────────────────
    usia_kehamilan_lahir: Mapped[int | None] = mapped_column(SmallInteger)
    jenis_kehamilan: Mapped[str | None] = mapped_column(
        Enum("tunggal", "kembar", name="jenis_kehamilan")
    )
    anc_rutin: Mapped[bool | None] = mapped_column(Boolean)
    jumlah_anc: Mapped[int | None] = mapped_column(SmallInteger)
    hipertensi_kehamilan: Mapped[bool | None] = mapped_column(Boolean)
    preeklamsia: Mapped[bool | None] = mapped_column(Boolean)
    diabetes_gestasional: Mapped[bool | None] = mapped_column(Boolean)
    infeksi_hamil: Mapped[bool | None] = mapped_column(Boolean)
    perdarahan_hamil: Mapped[bool | None] = mapped_column(Boolean)
    ketuban_pecah_dini: Mapped[bool | None] = mapped_column(Boolean)
    merokok: Mapped[bool | None] = mapped_column(Boolean)
    paparan_asap_rokok: Mapped[bool | None] = mapped_column(Boolean)
    konsumsi_alkohol: Mapped[bool | None] = mapped_column(Boolean)
    obat_tertentu: Mapped[bool | None] = mapped_column(Boolean)
    obat_tertentu_ket: Mapped[str | None] = mapped_column(Text)

    # ── D. Riwayat persalinan ──────────────────────────────────────────────────
    tanggal_persalinan: Mapped[date | None] = mapped_column(Date)
    jenis_persalinan: Mapped[str | None] = mapped_column(
        Enum("normal", "sc", "vakum", "forceps", name="jenis_persalinan")
    )
    tempat_persalinan: Mapped[str | None] = mapped_column(String(150))
    indikasi_prematur: Mapped[list | None] = mapped_column(JSONB)          # list[str]
    indikasi_prematur_lainnya: Mapped[str | None] = mapped_column(Text)
    komplikasi_persalinan: Mapped[list | None] = mapped_column(JSONB)      # list[str]
    komplikasi_lainnya: Mapped[str | None] = mapped_column(Text)
    apgar_menit_1: Mapped[int | None] = mapped_column(SmallInteger)
    apgar_menit_5: Mapped[int | None] = mapped_column(SmallInteger)

    # ── E. Kondisi ibu setelah melahirkan ──────────────────────────────────────
    kondisi_umum: Mapped[str | None] = mapped_column(
        Enum("baik", "cukup", "buruk", name="kondisi_umum")
    )
    masih_dirawat: Mapped[bool | None] = mapped_column(Boolean)
    komplikasi_postpartum: Mapped[bool | None] = mapped_column(Boolean)
    dapat_berjalan: Mapped[bool | None] = mapped_column(Boolean)
    dapat_menyusui: Mapped[bool | None] = mapped_column(Boolean)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    baby: Mapped["Baby"] = relationship(back_populates="maternal_record")
