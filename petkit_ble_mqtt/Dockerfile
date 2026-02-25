FROM python:3.11-alpine

# System deps for bleak/dbus
RUN apk add --no-cache \
    git \
    dbus \
    bluez \
    bluez-libs \
    gcc \
    musl-dev \
    python3-dev

# Python deps
RUN pip install --no-cache-dir bleak paho-mqtt

# Clone PetkitW5BLEMQTT library
RUN git clone https://github.com/slespersen/PetkitW5BLEMQTT.git /app

# Make the library importable
RUN ln -s /app/PetkitW5BLEMQTT /usr/local/lib/python3.11/site-packages/PetkitW5BLEMQTT

# Patched ble_manager: None-check fuer dev.name + reconnect bei Write-Fehler
COPY ble_manager.py /app/PetkitW5BLEMQTT/ble_manager.py

# Patched utils.py: Division-by-zero Guard fuer SMART-Modus (time_on=0)
COPY utils.py /app/PetkitW5BLEMQTT/utils.py

# Patched parsers.py: CTW3-Branch in device_status() - korrekte Byte-Offsets + pet_drinking
COPY parsers.py /app/PetkitW5BLEMQTT/parsers.py

# Patched device.py: _pet_drinking Attribut + Status-Key Whitelist
COPY device.py /app/PetkitW5BLEMQTT/device.py

# Patched mqtt_payloads.py: pet_drinking Entity fuer CTW3
COPY mqtt_payloads.py /app/PetkitW5BLEMQTT/mqtt_payloads.py

# Patched main.py: konfigurierbares heartbeat_interval
COPY main.py /app/main.py

COPY run.sh /run.sh
RUN chmod +x /run.sh

WORKDIR /app
CMD ["/run.sh"]
