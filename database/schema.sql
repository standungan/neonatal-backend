-- =============================================================================
-- Sistem Monitoring Bayi pada Inkubator
-- PostgreSQL DDL — schema.sql
-- =============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- ENUMS
-- =============================================================================

CREATE TYPE user_role AS ENUM ('admin', 'perawat', 'dokter');

CREATE TYPE incubator_status AS ENUM ('kosong', 'terisi', 'warning', 'tidak_tersedia');

CREATE TYPE assignment_status AS ENUM ('active', 'discharged');

CREATE TYPE gender_type AS ENUM ('laki_laki', 'perempuan');

-- =============================================================================
-- TABLE: users
-- =============================================================================

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role            user_role NOT NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- TABLE: incubators
-- =============================================================================

CREATE TABLE incubators (
    incubator_id    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incubator_no    VARCHAR(10) NOT NULL UNIQUE,
    location        VARCHAR(255),
    status          incubator_status NOT NULL DEFAULT 'kosong',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- TABLE: babies
-- =============================================================================

CREATE TABLE babies (
    baby_id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    baby_name           VARCHAR(255) NOT NULL,
    gender              gender_type NOT NULL,
    birth_date          DATE NOT NULL,
    birth_weight        NUMERIC(6, 2),       -- grams, e.g. 2400.00
    birth_length        NUMERIC(5, 1),       -- cm
    gestational_age     SMALLINT,            -- weeks
    birth_type          VARCHAR(100),        -- jenis kelahiran
    clinical_notes      TEXT,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- TABLE: parents
-- One-to-one with babies — each registered baby has exactly one parent record
-- =============================================================================

CREATE TABLE parents (
    parent_id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    baby_id                 UUID NOT NULL UNIQUE REFERENCES babies(baby_id) ON DELETE CASCADE,
    mother_name             VARCHAR(255),
    father_name             VARCHAR(255),
    mother_phone            VARCHAR(20),
    mother_medical_history  TEXT,
    birth_history           TEXT,
    delivery_history        TEXT,
    additional_notes        TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- TABLE: baby_incubator_assignments
-- Tracks which baby is/was in which incubator, with full history
-- =============================================================================

CREATE TABLE baby_incubator_assignments (
    assignment_id   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    baby_id         UUID NOT NULL REFERENCES babies(baby_id),
    incubator_id    UUID NOT NULL REFERENCES incubators(incubator_id),
    assigned_by     UUID NOT NULL REFERENCES users(id),
    assigned_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    discharged_at   TIMESTAMPTZ,
    status          assignment_status NOT NULL DEFAULT 'active'
);

-- Only one active assignment per incubator at a time
CREATE UNIQUE INDEX uq_active_incubator_assignment
    ON baby_incubator_assignments (incubator_id)
    WHERE status = 'active';

-- Only one active assignment per baby at a time
CREATE UNIQUE INDEX uq_active_baby_assignment
    ON baby_incubator_assignments (baby_id)
    WHERE status = 'active';

-- =============================================================================
-- TABLE: monitoring_records
-- Each record = one nurse observation session for a baby
-- =============================================================================

CREATE TABLE monitoring_records (
    monitoring_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    baby_id             UUID NOT NULL REFERENCES babies(baby_id),
    recorded_by         UUID NOT NULL REFERENCES users(id),
    observation_time    TIMESTAMPTZ NOT NULL,
    suhu_bayi           NUMERIC(4, 1),       -- °C, e.g. 36.8
    suhu_inkubator      NUMERIC(4, 1),       -- °C, e.g. 33.5
    kelembapan_inkubator NUMERIC(5, 2),      -- % RH (Pillar 7), e.g. 55.00
    heart_rate          SMALLINT,            -- bpm
    respiratory_rate    SMALLINT,            -- breaths/min (Pillar 1), normal 40–60
    spo2                NUMERIC(5, 2),       -- %, e.g. 98.00
    expression_score    SMALLINT CHECK (expression_score BETWEEN 1 AND 5),
    movement_score      SMALLINT CHECK (movement_score BETWEEN 1 AND 5),
    pain_score          SMALLINT CHECK (pain_score BETWEEN 0 AND 7),    -- Pillar 6 (NIPS), >=4 = pain
    sleep_duration_min  SMALLINT,            -- Pillar 5, minutes
    sleep_quality       SMALLINT CHECK (sleep_quality BETWEEN 1 AND 5), -- Pillar 5
    agitation_episodes  SMALLINT,            -- Pillar 5, count
    catatan             TEXT,
    foto_url            VARCHAR(500),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- TABLE: parent_involvement_records
-- Records nurse input of parent interaction with baby
-- skor_keterlibatan is stored (calculated in service layer before insert)
-- =============================================================================

CREATE TABLE parent_involvement_records (
    involvement_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    baby_id                 UUID NOT NULL REFERENCES babies(baby_id),
    recorded_by             UUID NOT NULL REFERENCES users(id),
    observation_time        TIMESTAMPTZ NOT NULL,
    durasi_menyusui         SMALLINT,            -- minutes (informational)
    durasi_interaksi        SMALLINT,            -- minutes (informational)
    -- Pillar 8 sub-domains, each rated 0–4 (0=tidak ada … 4=konsisten)
    presence_score                SMALLINT CHECK (presence_score BETWEEN 0 AND 4),
    physical_interaction_score    SMALLINT CHECK (physical_interaction_score BETWEEN 0 AND 4),
    feeding_participation_score   SMALLINT CHECK (feeding_participation_score BETWEEN 0 AND 4),
    care_participation_score      SMALLINT CHECK (care_participation_score BETWEEN 0 AND 4),
    knowledge_score               SMALLINT CHECK (knowledge_score BETWEEN 0 AND 4),
    communication_score           SMALLINT CHECK (communication_score BETWEEN 0 AND 4),
    emotional_readiness_score     SMALLINT CHECK (emotional_readiness_score BETWEEN 0 AND 4),
    discharge_readiness_score     SMALLINT CHECK (discharge_readiness_score BETWEEN 0 AND 4),
    catatan                 TEXT,
    skor_keterlibatan       SMALLINT CHECK (skor_keterlibatan BETWEEN 0 AND 100),  -- PEI, computed from domains
    kondisi_bayi            VARCHAR(255),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- TABLE: audit_logs
-- Immutable trail of all user actions
-- =============================================================================

CREATE TABLE audit_logs (
    log_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
    action          VARCHAR(50) NOT NULL,   -- LOGIN, CREATE, UPDATE, DELETE, EXPORT
    table_name      VARCHAR(100),
    record_id       UUID,
    ip_address      INET,
    details         JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- monitoring_records — most queried by baby + time
CREATE INDEX idx_monitoring_baby_time    ON monitoring_records (baby_id, observation_time DESC);
CREATE INDEX idx_monitoring_recorded_by  ON monitoring_records (recorded_by);

-- parent_involvement — queried by baby
CREATE INDEX idx_involvement_baby_time   ON parent_involvement_records (baby_id, observation_time DESC);

-- assignments — find active assignment for a baby or incubator quickly
CREATE INDEX idx_assignment_baby         ON baby_incubator_assignments (baby_id);
CREATE INDEX idx_assignment_incubator    ON baby_incubator_assignments (incubator_id);

-- audit_logs — queried by user and time
CREATE INDEX idx_audit_user_time         ON audit_logs (user_id, created_at DESC);
CREATE INDEX idx_audit_table_record      ON audit_logs (table_name, record_id);

-- =============================================================================
-- updated_at auto-update trigger
-- =============================================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_incubators_updated_at
    BEFORE UPDATE ON incubators
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_babies_updated_at
    BEFORE UPDATE ON babies
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_parents_updated_at
    BEFORE UPDATE ON parents
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
