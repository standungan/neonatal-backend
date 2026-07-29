"""maternal record + expanded NICU intake fields

Adds the fuller baby-registration / NICU-intake dataset (updates02):
  - extra baby identity columns (no RM, jam lahir, usia masuk NICU, lingkar
    kepala/dada, golongan darah)
  - registration columns on the assignment (no registrasi NICU, rumah sakit,
    ruang NICU, DPJP)
  - a new maternal_records table holding the mother's structured medical record
    (identitas, riwayat obstetri, riwayat kehamilan, riwayat persalinan with two
    JSONB checklists, kondisi ibu pasca-lahir)

Everything is nullable so existing rows and the current registration flow keep
working. Parents keeps mother name/phone; maternal_records holds the record.

Revision ID: b8e4f1c02a37
Revises: f6d1b3a8e290
Create Date: 2026-07-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b8e4f1c02a37"
down_revision: Union[str, None] = "f6d1b3a8e290"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ── Enum types (created once, reused across columns) ───────────────────────────
blood_type = postgresql.ENUM("A", "B", "AB", "O", name="blood_type")
pendidikan_type = postgresql.ENUM(
    "tidak_sekolah", "sd", "smp", "sma", "diploma", "s1", "s2", "s3",
    name="pendidikan_type",
)
jenis_persalinan = postgresql.ENUM("normal", "sc", "vakum", "forceps", name="jenis_persalinan")
kondisi_umum = postgresql.ENUM("baik", "cukup", "buruk", name="kondisi_umum")
jenis_kehamilan = postgresql.ENUM("tunggal", "kembar", name="jenis_kehamilan")

_ENUMS = [blood_type, pendidikan_type, jenis_persalinan, kondisi_umum, jenis_kehamilan]


def upgrade() -> None:
    bind = op.get_bind()
    for e in _ENUMS:
        e.create(bind, checkfirst=True)

    # column-level references must not try to re-create the type
    blood = postgresql.ENUM(name="blood_type", create_type=False)

    # ── babies: extra identity fields ──────────────────────────────────────────
    op.add_column("babies", sa.Column("no_rm_bayi", sa.String(50), nullable=True))
    op.add_column("babies", sa.Column("jam_lahir", sa.Time(), nullable=True))
    op.add_column("babies", sa.Column("usia_masuk_nicu_jam", sa.SmallInteger(), nullable=True))
    op.add_column("babies", sa.Column("lingkar_kepala", sa.Numeric(4, 1), nullable=True))
    op.add_column("babies", sa.Column("lingkar_dada", sa.Numeric(4, 1), nullable=True))
    op.add_column("babies", sa.Column("golongan_darah", blood, nullable=True))

    # ── assignment: registration / admission fields ────────────────────────────
    op.add_column(
        "baby_incubator_assignments",
        sa.Column("no_registrasi_nicu", sa.String(30), nullable=True),
    )
    op.create_unique_constraint(
        "uq_assignment_no_registrasi_nicu",
        "baby_incubator_assignments",
        ["no_registrasi_nicu"],
    )
    op.add_column("baby_incubator_assignments", sa.Column("rumah_sakit", sa.String(150), nullable=True))
    op.add_column("baby_incubator_assignments", sa.Column("ruang_nicu", sa.String(100), nullable=True))
    op.add_column(
        "baby_incubator_assignments",
        sa.Column("dpjp_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_assignment_dpjp",
        "baby_incubator_assignments",
        "users",
        ["dpjp_id"],
        ["id"],
    )

    # ── maternal_records: the mother's structured medical record ───────────────
    op.create_table(
        "maternal_records",
        sa.Column("maternal_record_id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("baby_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("babies.baby_id", ondelete="CASCADE"), nullable=False, unique=True),
        # A. identitas ibu (extras; name/phone stay in parents)
        sa.Column("no_rm_ibu", sa.String(50)),
        sa.Column("umur_ibu", sa.SmallInteger()),
        sa.Column("pendidikan", postgresql.ENUM(name="pendidikan_type", create_type=False)),
        sa.Column("pekerjaan", sa.String(100)),
        sa.Column("alamat", sa.Text()),
        sa.Column("golongan_darah", postgresql.ENUM(name="blood_type", create_type=False)),
        # B. riwayat obstetri
        sa.Column("kehamilan_ke", sa.SmallInteger()),
        sa.Column("jumlah_persalinan_hidup", sa.SmallInteger()),
        sa.Column("riwayat_abortus", sa.Boolean()),
        sa.Column("riwayat_prematur", sa.Boolean()),
        sa.Column("riwayat_bblr", sa.Boolean()),
        sa.Column("riwayat_bayi_meninggal", sa.Boolean()),
        # C. riwayat kehamilan saat ini
        sa.Column("usia_kehamilan_lahir", sa.SmallInteger()),
        sa.Column("jenis_kehamilan", postgresql.ENUM(name="jenis_kehamilan", create_type=False)),
        sa.Column("anc_rutin", sa.Boolean()),
        sa.Column("jumlah_anc", sa.SmallInteger()),
        sa.Column("hipertensi_kehamilan", sa.Boolean()),
        sa.Column("preeklamsia", sa.Boolean()),
        sa.Column("diabetes_gestasional", sa.Boolean()),
        sa.Column("infeksi_hamil", sa.Boolean()),
        sa.Column("perdarahan_hamil", sa.Boolean()),
        sa.Column("ketuban_pecah_dini", sa.Boolean()),
        sa.Column("merokok", sa.Boolean()),
        sa.Column("paparan_asap_rokok", sa.Boolean()),
        sa.Column("konsumsi_alkohol", sa.Boolean()),
        sa.Column("obat_tertentu", sa.Boolean()),
        sa.Column("obat_tertentu_ket", sa.Text()),
        # D. riwayat persalinan
        sa.Column("tanggal_persalinan", sa.Date()),
        sa.Column("jenis_persalinan", postgresql.ENUM(name="jenis_persalinan", create_type=False)),
        sa.Column("tempat_persalinan", sa.String(150)),
        sa.Column("indikasi_prematur", postgresql.JSONB()),          # list[str]
        sa.Column("indikasi_prematur_lainnya", sa.Text()),
        sa.Column("komplikasi_persalinan", postgresql.JSONB()),      # list[str]
        sa.Column("komplikasi_lainnya", sa.Text()),
        sa.Column("apgar_menit_1", sa.SmallInteger()),
        sa.Column("apgar_menit_5", sa.SmallInteger()),
        # E. kondisi ibu setelah melahirkan
        sa.Column("kondisi_umum", postgresql.ENUM(name="kondisi_umum", create_type=False)),
        sa.Column("masih_dirawat", sa.Boolean()),
        sa.Column("komplikasi_postpartum", sa.Boolean()),
        sa.Column("dapat_berjalan", sa.Boolean()),
        sa.Column("dapat_menyusui", sa.Boolean()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("maternal_records")
    op.drop_constraint("fk_assignment_dpjp", "baby_incubator_assignments", type_="foreignkey")
    op.drop_column("baby_incubator_assignments", "dpjp_id")
    op.drop_column("baby_incubator_assignments", "ruang_nicu")
    op.drop_column("baby_incubator_assignments", "rumah_sakit")
    op.drop_constraint("uq_assignment_no_registrasi_nicu", "baby_incubator_assignments", type_="unique")
    op.drop_column("baby_incubator_assignments", "no_registrasi_nicu")
    for col in ("golongan_darah", "lingkar_dada", "lingkar_kepala", "usia_masuk_nicu_jam", "jam_lahir", "no_rm_bayi"):
        op.drop_column("babies", col)

    bind = op.get_bind()
    for e in reversed(_ENUMS):
        e.drop(bind, checkfirst=True)
