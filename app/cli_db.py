#!/usr/bin/env python3
import psycopg2
import sys
from tabulate import tabulate

SNMP_DB = {
    "host": "postgres",
    "dbname": "snmptraps",
    "user": "snmpuser",
    "password": "toor",
}

OSC_DB = {
    "host": "postgres",
    "dbname": "osc_database",
    "user": "osc_user",
    "password": "osc_pass",
}


def query(db_config, sql):
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    headers = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return headers, rows


def stats():
    print("\n==== SNMP STATS ====")

    headers, rows = query(SNMP_DB,
        "SELECT COUNT(*) AS total_traps FROM traps;")
    print(tabulate(rows, headers=headers, tablefmt="grid"))

    headers, rows = query(SNMP_DB,
        "SELECT COUNT(*) AS osc_los_traps FROM traps WHERE parsed->>'alarm_code'='OSC_LOS';")
    print(tabulate(rows, headers=headers, tablefmt="grid"))

    headers, rows = query(SNMP_DB,
        "SELECT COUNT(*) AS pending_forward FROM traps WHERE forwarded = FALSE;")
    print(tabulate(rows, headers=headers, tablefmt="grid"))

    print("\n==== OSC DB STATS ====")
    headers, rows = query(OSC_DB,
        "SELECT COUNT(*) AS osc_rows FROM osc_los_alarms;")
    print(tabulate(rows, headers=headers, tablefmt="grid"))


def pending():
    headers, rows = query(SNMP_DB, """
        SELECT id,
               parsed->>'alarm_code' AS alarm_code,
               parsed->>'state' AS state
        FROM traps
        WHERE forwarded = FALSE
        ORDER BY id DESC;
    """)
    print(tabulate(rows, headers=headers, tablefmt="grid"))


def osc():
    headers, rows = query(OSC_DB, """
        SELECT id, alarm_code, state, site
        FROM osc_los_alarms
        ORDER BY id DESC;
    """)
    print(tabulate(rows, headers=headers, tablefmt="grid"))


def recent(limit):
    headers, rows = query(SNMP_DB, f"""
        SELECT id,
               parsed->>'alarm_code' AS alarm_code,
               parsed->>'state' AS state,
               forwarded
        FROM traps
        ORDER BY id DESC
        LIMIT {limit};
    """)
    print(tabulate(rows, headers=headers, tablefmt="grid"))


def help_menu():
    print("""
Usage:
  python cli_db.py stats
  python cli_db.py pending
  python cli_db.py osc
  python cli_db.py recent <number>
""")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        help_menu()
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "stats":
        stats()
    elif cmd == "pending":
        pending()
    elif cmd == "osc":
        osc()
    elif cmd == "recent":
        if len(sys.argv) < 3:
            print("Provide limit number")
        else:
            recent(sys.argv[2])
    else:
        help_menu()