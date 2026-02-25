#!/usr/bin/env sh
set -e

OPTIONS="/data/options.json"

# Read options
MAC=$(python3 -c "import json; d=json.load(open('$OPTIONS')); print(d['fountain_mac'])")
BROKER=$(python3 -c "import json; d=json.load(open('$OPTIONS')); print(d['mqtt_broker'])")
PORT=$(python3 -c "import json; d=json.load(open('$OPTIONS')); print(d['mqtt_port'])")
USER=$(python3 -c "import json; d=json.load(open('$OPTIONS')); print(d['mqtt_user'])")
PASS=$(python3 -c "import json; d=json.load(open('$OPTIONS')); print(d['mqtt_password'])")
LOGLEVEL=$(python3 -c "import json; d=json.load(open('$OPTIONS')); print(d.get('log_level', 'INFO'))")
INTERVAL=$(python3 -c "import json; d=json.load(open('$OPTIONS')); print(d.get('poll_interval', 60))")

echo "[PetKit BLE] Starte fuer Fontaene $MAC"
echo "[PetKit BLE] MQTT: $BROKER:$PORT (user: $USER)"
echo "[PetKit BLE] Poll-Intervall: ${INTERVAL}s"

# Auto-restart loop - BLE connections koennen abreissen
while true; do
    # BlueZ GATT-State komplett zuruecksetzen (loest Notify-Lock der alten Session)
    echo "[PetKit BLE] Setze BlueZ-State zurueck..."
    bluetoothctl disconnect "$MAC" 2>/dev/null || true
    bluetoothctl remove "$MAC" 2>/dev/null || true
    sleep 5

    echo "[PetKit BLE] Verbinde..."
    python3 /app/main.py \
        --address "$MAC" \
        --mqtt \
        --mqtt_broker "$BROKER" \
        --mqtt_port "$PORT" \
        --mqtt_user "$USER" \
        --mqtt_password "$PASS" \
        --heartbeat_interval "$INTERVAL" \
        --logging_level "$LOGLEVEL" || true

    echo "[PetKit BLE] Verbindung verloren, warte 30s..."
    sleep 30
done
