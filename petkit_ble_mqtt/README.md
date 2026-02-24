# PetKit BLE MQTT - Home Assistant Add-on

Direkte BLE-Verbindung zu PetKit CTW3/W5 Fontänen. Kein Cloud-Zugriff, kein Relay.

## Funktionsweise

Das Add-on verbindet sich per Bluetooth Low Energy direkt mit der Fontäne und veröffentlicht Status und Steuerungsmöglichkeiten über MQTT. Home Assistant erkennt das Gerät automatisch über MQTT Discovery.

## Konfiguration

| Option | Beschreibung | Standard |
|---|---|---|
| `fountain_mac` | BLE MAC-Adresse der Fontäne | `A4:C1:38:52:34:98` |
| `mqtt_broker` | Hostname des MQTT-Brokers | `core-mosquitto` |
| `mqtt_port` | Port des MQTT-Brokers | `1883` |
| `mqtt_user` | MQTT-Benutzername | `mqtt` |
| `mqtt_password` | MQTT-Passwort | |
| `poll_interval` | Abfrageintervall in Sekunden | `60` |
| `log_level` | Log-Level | `INFO` |

## Voraussetzungen

- Bluetooth-Adapter am Home Assistant Host
- MQTT-Broker (z.B. Mosquitto Add-on)

## Herkunft & Lizenz

Dieses Add-on basiert auf der [PetkitW5BLEMQTT](https://github.com/slespersen/PetkitW5BLEMQTT) Library von [@slespersen](https://github.com/slespersen).

Die originale Library steht unter der dort angegebenen Lizenz. Dieses Add-on-Wrapper-Projekt steht unter der [MIT License](https://github.com/Delido/hassio-addons/blob/main/LICENSE).
