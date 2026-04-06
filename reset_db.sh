#!/bin/bash

echo "Clearing SNMP DB..."
docker exec -it snmp_postgres psql -U snmpuser -d snmptraps -c \
"TRUNCATE TABLE traps RESTART IDENTITY CASCADE;"

echo "Clearing OSC DB..."
docker exec -it snmp_postgres psql -U osc_user -d osc_database -c \
"TRUNCATE TABLE osc_los_alarms RESTART IDENTITY CASCADE;"

echo "Done."
