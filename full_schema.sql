-- ==========================================================
-- CLEAN SCHEMA (NO DUMP ARTIFACTS)
-- ==========================================================

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

-- ✅ IMPORTANT: ensure correct schema
SET search_path TO public;

-- ==========================================================
-- TABLE: traps
-- ==========================================================

CREATE TABLE IF NOT EXISTS traps (
    id BIGSERIAL PRIMARY KEY,
    received_at TIMESTAMP NOT NULL,
    sender TEXT,
    raw JSONB,
    parsed JSONB,
    forwarded BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_traps_received ON traps(received_at);
CREATE INDEX IF NOT EXISTS idx_traps_raw_gin ON traps USING gin(raw);
CREATE INDEX IF NOT EXISTS idx_traps_parsed_gin ON traps USING gin(parsed);

-- ==========================================================
-- TABLE: active_alarms
-- ==========================================================

CREATE TABLE IF NOT EXISTS active_alarms (
    alarm_id BIGSERIAL PRIMARY KEY,
    first_seen TIMESTAMP NOT NULL,
    last_seen TIMESTAMP NOT NULL,
    site TEXT,
    device_type TEXT,
    source TEXT,
    alarm_code TEXT,
    severity TEXT,
    description TEXT,
    device_time TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_active_alarm
ON active_alarms (site, device_type, source, alarm_code);

CREATE INDEX IF NOT EXISTS idx_active_lookup
ON active_alarms (site, device_type, source, alarm_code);

-- ==========================================================
-- TABLE: historical_alarms
-- ==========================================================

CREATE TABLE IF NOT EXISTS historical_alarms (
    alarm_id BIGINT,
    first_seen TIMESTAMP NOT NULL,
    last_seen TIMESTAMP NOT NULL,
    recovery_time TIMESTAMP NOT NULL,
    site TEXT,
    device_type TEXT,
    source TEXT,
    alarm_code TEXT,
    severity TEXT,
    description TEXT,
    device_time TEXT
);

CREATE INDEX IF NOT EXISTS idx_hist_recovery
ON historical_alarms (recovery_time);

-- ==========================================================
-- FUNCTION: process_alarm_row
-- ==========================================================

CREATE OR REPLACE FUNCTION process_alarm_row(
    p_received_at TIMESTAMP,
    p_site TEXT,
    p_device_type TEXT,
    p_source TEXT,
    p_alarm_code TEXT,
    p_severity TEXT,
    p_description TEXT,
    p_state TEXT,
    p_device_time TEXT
)
RETURNS VOID AS
$$
DECLARE
    v_alarm_id BIGINT;
BEGIN

    -- ================= FAULT =================
    IF p_state = 'Fault' THEN

        INSERT INTO active_alarms (
            first_seen, last_seen,
            site, device_type, source,
            alarm_code, severity,
            description, device_time
        )
        VALUES (
            p_received_at, p_received_at,
            p_site, p_device_type, p_source,
            p_alarm_code, p_severity,
            p_description, p_device_time
        )
        ON CONFLICT (site, device_type, source, alarm_code)
        DO UPDATE SET
            last_seen   = p_received_at,
            severity    = p_severity,
            description = p_description,
            device_time = p_device_time;

    END IF;

    -- ================= RECOVERY =================
    IF p_state = 'Recovery' THEN

        SELECT alarm_id INTO v_alarm_id
        FROM active_alarms
        WHERE site = p_site
          AND device_type = p_device_type
          AND source = p_source
          AND alarm_code = p_alarm_code;

        IF FOUND THEN

            INSERT INTO historical_alarms
            SELECT alarm_id,
                   first_seen,
                   last_seen,
                   p_received_at,
                   site,
                   device_type,
                   source,
                   alarm_code,
                   severity,
                   description,
                   device_time
            FROM active_alarms
            WHERE alarm_id = v_alarm_id;

            DELETE FROM active_alarms
            WHERE alarm_id = v_alarm_id;

        END IF;

    END IF;

END;
$$ LANGUAGE plpgsql;