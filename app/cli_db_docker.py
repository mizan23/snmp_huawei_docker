#!/usr/bin/env python3
import psycopg2
from tabulate import tabulate
from shutil import get_terminal_size
import re

# ANSI colors
RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"

SNMP_DB = {
    "host": "postgres",
    "dbname": "snmptraps",
    "user": "your_db_username",
    "password": "your_db_password",
}


# Strip ANSI for alignment
def strip_ansi(s):
    return re.sub(r'\x1b\[[0-9;]*m', '', s)


def color_state(state):
    if state == "Fault":
        return f"{RED}{state}{RESET}"
    elif state == "Recovery":
        return f"{GREEN}{state}{RESET}"
    return state


def query(sql):
    conn = psycopg2.connect(**SNMP_DB)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    headers = [desc[0] for desc in cur.description]

    # Apply color to state column
    if "state" in headers:
        idx = headers.index("state")
        rows = [
            tuple(color_state(v) if i == idx else v for i, v in enumerate(row))
            for row in rows
        ]

    cur.close()
    conn.close()

    return tabulate(rows, headers=headers, tablefmt="grid").split("\n")


def pad_line(line, width):
    visible_len = len(strip_ansi(line))
    return line + " " * max(0, width - visible_len)


def merge_3_columns(col1, col2, col3, width):
    w1 = int(width * 0.25)
    w2 = int(width * 0.30)
    w3 = width - w1 - w2 - 6

    max_lines = max(len(col1), len(col2), len(col3))
    output = []

    for i in range(max_lines):
        c1 = col1[i] if i < len(col1) else ""
        c2 = col2[i] if i < len(col2) else ""
        c3 = col3[i] if i < len(col3) else ""

        line = (
            pad_line(c1, w1) + " | " +
            pad_line(c2, w2) + " | " +
            pad_line(c3, w3)
        )
        output.append(line)

    return "\n".join(output)


def main():
    width = get_terminal_size((160, 20)).columns

    print("=" * width)
    print("SNMP ALARM DASHBOARD".center(width))
    print("=" * width)

    # ---------------- COLUMN 1 ----------------
    total = query("SELECT COUNT(*) AS total_traps FROM traps;")

    state = query("""
        SELECT parsed->>'state' AS state, COUNT(*) 
        FROM traps GROUP BY state;
    """)

    col1 = (
        ["--- OVERVIEW ---"] + total +
        [""] +
        ["--- STATE ---"] + state
    )

    # ---------------- COLUMN 2 ----------------
    # Rate based on last N IDs (no created_at needed)
    rate = query("""
        SELECT 
            (SELECT COUNT(*) FROM traps 
             WHERE id > (SELECT MAX(id) - 50 FROM traps)
            ) AS last_batch,
            COUNT(*) AS total
        FROM traps;
    """)

    top_alarms = query("""
        SELECT parsed->>'alarm_code' AS alarm_code, COUNT(*) 
        FROM traps
        GROUP BY alarm_code
        ORDER BY COUNT(*) DESC
        LIMIT 10;
    """)

    col2 = (
        ["--- ALARM RATE ---"] + rate +
        [""] +
        ["--- TOP ALARMS ---"] + top_alarms
    )

    # ---------------- COLUMN 3 ----------------
    last_traps = query("""
        SELECT id,
               parsed->>'alarm_code' AS alarm_code,
               parsed->>'state' AS state,
               forwarded
        FROM traps
        ORDER BY id DESC
        LIMIT 15;
    """)

    col3 = ["--- LAST TRAPS ---"] + last_traps

    # ---------------- MERGE ----------------
    print(merge_3_columns(col1, col2, col3, width))

    print("=" * width)


if __name__ == "__main__":
    main()