#!/usr/bin/env python3

import os
import json
import binascii
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import psycopg2

from pysnmp.entity import engine, config
from pysnmp.carrier.asyncore.dgram import udp
from pysnmp.entity.rfc3413 import ntfrcv


# ==========================================================
# CONFIG
# ==========================================================

TZ = ZoneInfo("Asia/Dhaka")

LISTEN_IP = "0.0.0.0"
LISTEN_PORT = 2323

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "postgres"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

SNMP_USER = "snmpuser"
AUTH_KEY = "Fiber@Huawei@9800"
PRIV_KEY = "Fiber@Huawei@9800"

HUAWEI_ENGINE_ID = b"\x80\x00\x13\x70\x01\xc0\xa8\x2a\x05"


# ==========================================================
# DB CONNECTION
# ==========================================================

def get_connection():
    while True:
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            print("✅ DB connected")
            return conn
        except Exception as e:
            print("⏳ Waiting for DB...", e)
            time.sleep(2)


# ==========================================================
# SNMP ENGINE
# ==========================================================

snmpEngine = engine.SnmpEngine()

config.addV3User(
    snmpEngine,
    SNMP_USER,
    config.usmHMAC192SHA256AuthProtocol,
    AUTH_KEY,
    config.usmAesCfb128Protocol,
    PRIV_KEY,
    securityEngineId=HUAWEI_ENGINE_ID
)

config.addVacmUser(
    snmpEngine,
    3,
    SNMP_USER,
    "authPriv",
    readSubTree=(1,3,6),
    writeSubTree=(1,3,6),
    notifySubTree=(1,3,6)
)

config.addTransport(
    snmpEngine,
    udp.domainName,
    udp.UdpTransport().openServerMode((LISTEN_IP, LISTEN_PORT))
)

config.addContext(snmpEngine, "")


# ==========================================================
# HELPERS
# ==========================================================

def normalize_state(raw_state):
    if raw_state:
        raw_state = str(raw_state).strip().lower()
        if raw_state in ("fault", "1", "alarm", "active"):
            return "Fault"
        if raw_state in ("recovery", "clear", "cleared", "normal", "0"):
            return "Recovery"
    return "Fault"


def get_value(vars_list, oid):
    for v in vars_list:
        if v["oid"] == oid:
            return v["value"]
    return None


def decode_hex_description(val):
    if not val or not isinstance(val, str):
        return val
    if val.startswith("0x"):
        try:
            return bytes.fromhex(val[2:]).decode("utf-8", errors="replace")
        except:
            return val
    return val


def is_snmp_agent_trap(vars_list):
    for v in vars_list:
        if v["oid"] == "1.3.6.1.4.1.2011.2.15.1" and v["value"] == "SNMP Agent":
            return True
    return False


# ==========================================================
# CALLBACK (FIXED)
# ==========================================================

def cbFun(snmpEngine, stateReference, contextEngineId, contextName, varBinds, cbCtx):

    try:
        conn = get_connection()
        cur = conn.cursor()

        transportDomain, transportAddress = snmpEngine.msgAndPduDsp.getTransportInfo(stateReference)
        sender_ip = transportAddress[0]

        received_at = datetime.now(TZ).replace(tzinfo=None)

        vars_list = [{"oid": str(oid), "value": val.prettyPrint()} for oid, val in varBinds]

        if is_snmp_agent_trap(vars_list):
            print(f"[IGNORED] SNMP Agent trap from {sender_ip}")
            return

        # ================= FULL EXTRACTION =================

        site        = get_value(vars_list, "1.3.6.1.4.1.2011.2.15.1.7.1.1.0")
        device_type = get_value(vars_list, "1.3.6.1.4.1.2011.2.15.1.7.1.2.0")
        source      = get_value(vars_list, "1.3.6.1.4.1.2011.2.15.1.7.1.3.0")
        device_time = get_value(vars_list, "1.3.6.1.4.1.2011.2.15.1.7.1.5.0")

        raw_description = get_value(vars_list, "1.3.6.1.4.1.2011.2.15.1.7.1.6.0")
        description     = decode_hex_description(raw_description)

        severity   = get_value(vars_list, "1.3.6.1.4.1.2011.2.15.1.7.1.7.0")
        alarm_text = get_value(vars_list, "1.3.6.1.4.1.2011.2.15.1.7.1.8.0")
        raw_state  = get_value(vars_list, "1.3.6.1.4.1.2011.2.15.1.7.1.10.0")

        event_id   = get_value(vars_list, "1.3.6.1.4.1.2011.2.15.1.7.1.13.0")
        alarm_code = get_value(vars_list, "1.3.6.1.4.1.2011.2.15.1.7.1.24.0")

        state = normalize_state(raw_state)

        # ================= DB =================

        cur.execute("""
            INSERT INTO traps (received_at, sender, raw, parsed)
            VALUES (%s, %s, %s, %s)
        """, (
            received_at,
            sender_ip,
            json.dumps(vars_list),
            json.dumps({
                "site": site,
                "device_type": device_type,
                "source": source,
                "alarm_code": alarm_code,
                "alarm_text": alarm_text,
                "severity": severity,
                "state": state,
                "event_id": event_id
            })
        ))

        if all([site, device_type, source, alarm_code, state]):
            cur.execute("""
                SELECT process_alarm_row(
                    %s,%s,%s,%s,%s,%s,%s,%s,%s
                )
            """, (
                received_at,
                site,
                device_type,
                source,
                alarm_code,
                severity,
                description,
                state,
                device_time,
            ))

        conn.commit()
        print(f"[OK] {state} | {alarm_code} | {site} | EventID={event_id}")

    except Exception as e:
        print("❌ ERROR:", e)

    finally:
        try:
            cur.close()
            conn.close()
        except:
            pass


# ==========================================================
# START
# ==========================================================

ntfrcv.NotificationReceiver(snmpEngine, cbFun)

print(f"Listening for SNMP traps on {LISTEN_IP}:{LISTEN_PORT}")

snmpEngine.transportDispatcher.jobStarted(1)
snmpEngine.transportDispatcher.runDispatcher()