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

# Patch: dev.name kann None sein fuer namenlose BLE-Geraete
RUN sed -i 's/if any(supported_device in dev\.name/if dev.name and any(supported_device in dev.name/g' /app/PetkitW5BLEMQTT/ble_manager.py

# Make the library importable
RUN ln -s /app/PetkitW5BLEMQTT /usr/local/lib/python3.11/site-packages/PetkitW5BLEMQTT

COPY run.sh /run.sh
RUN chmod +x /run.sh

WORKDIR /app
CMD ["/run.sh"]
