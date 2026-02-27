# PetKit BLE MQTT - Home Assistant Add-on

Direkte BLE-Verbindung zu PetKit CTW3/W5 Fontänen. Kein Cloud-Zugriff, kein Relay.

> **Hinweis:** Diese Version wurde primär für die **PetKit Eversweet Max 2 (CTW3_100)** entwickelt und getestet. Andere Geräte (W5 etc.) sollten weiterhin funktionieren, sind aber weniger getestet.

## Getestete Geräte

| Gerät | Modell-ID | Status |
| --- | --- | --- |
| PetKit Eversweet Max 2 | CTW3_100 | ✅ Primär unterstützt |
| PetKit W5 / andere | — | ⚠️ Ungetestet |

## Bekannte Einschränkungen (CTW3)

| Funktion | Status | Hinweis |
| --- | --- | --- |
| Filter-%, Filterzeit, Wassermenge | ✅ | |
| Modus (Normal / Smart Mode) | ✅ | |
| LED Ein/Aus, Helligkeit | ✅ | |
| Batterie-Prozent | ✅ | |
| Pet Drinking (Echtzeit-Sensor) | ✅ | |
| Pet Drinking Count (Sitzungen/Tag) | ✅ | Zählt Trinksitzungen, reset bei Add-on-Neustart |
| Letzte Trinksitzung (Timestamp) | ✅ | |
| Trinksitzung Dauer | ✅ | Genauigkeit ~±60s (abhängig vom Poll-Intervall) |
| Do Not Disturb | ✅ | |
| Run (Pumpe an/aus) | ⚠️ | Funktioniert möglicherweise nicht korrekt bei CTW3 |

## Bekannte Bugs

| Bug | Beschreibung | Workaround |
| --- | --- | --- |
| Erster Verbindungsversuch schlägt fehl | Nach einem Neustart schlägt der erste BLE-Verbindungsversuch mit `failed to discover services, device disconnected` fehl. BlueZ ist zu diesem Zeitpunkt noch nicht vollständig bereit. Das Add-on erkennt den Fehler, wartet 30 s und verbindet sich beim zweiten Versuch erfolgreich. | Keiner nötig — selbstheilend. |
| Pet Drinking Count reset nach Neustart | Der Trinksitzungs-Zähler wird nur im RAM gehalten und startet nach jedem Add-on- oder HA-Neustart bei 0. Langzeitstatistiken sind daher nur mit HA-internen Mitteln (z.B. `utility_meter`) möglich. | In HA einen `utility_meter` auf die Sensor-Entity anlegen, der nicht zurückgesetzt wird. |

## Funktionsweise

Das Add-on verbindet sich per Bluetooth Low Energy direkt mit der Fontäne und veröffentlicht Status und Steuerungsmöglichkeiten über MQTT. Home Assistant erkennt das Gerät automatisch über MQTT Discovery.

## Konfiguration

| Option | Beschreibung | Standard |
| --- | --- | --- |
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
