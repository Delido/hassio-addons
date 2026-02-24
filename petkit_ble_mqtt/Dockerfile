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

# Patched ble_manager: None-check fuer dev.name + get_services() nach connect + reconnect bei Write-Fehler
COPY ble_manager.py /app/PetkitW5BLEMQTT/ble_manager.py

COPY run.sh /run.sh
RUN chmod +x /run.sh

WORKDIR /app
CMD ["/run.sh"]
