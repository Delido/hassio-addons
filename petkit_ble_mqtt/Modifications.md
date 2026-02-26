# Library Modifications for PetKit Eversweet Max 2 (CTW3_100)

This document describes all patches applied on top of the upstream
[PetkitW5BLEMQTT](https://github.com/slespersen/PetkitW5BLEMQTT) library
to support the **PetKit Eversweet Max 2 (CTW3_100)** fountain.

---

## `ble_manager.py`

### 1. `None`-check for device name during scan
During BLE scanning, `dev.name` can be `None` for devices that do not
advertise a name. The upstream code attempted a string comparison without
guarding against this, causing a `TypeError`. Added an explicit `None`
check before comparing the name.

### 2. Retry on `Notify acquired` error
BlueZ sometimes holds a GATT notification lock from a previous session.
When `connect_device()` encounters a `NotPermitted` / `Notify acquired`
BleakError, the code now waits `attempt × 10 s` and retries (up to 3
attempts) instead of crashing.

### 3. Retry on `Not connected` error during reconnect
During a reconnect triggered by `device_initialized = False`, bleak's
internal `_get_services()` call can fail with `BleakError: Not connected`
because the connection has not yet been fully established. Added `"Not
connected"` as a retryable condition with a 5 s back-off.

### 4. Reconnect on BLE write error
If `write_characteristic()` raises an exception (e.g. because the device
dropped the connection mid-session), the manager now disconnects, removes
the cached connection, and reconnects before retrying the write.

---

## `utils.py`

### Division-by-zero guard for Smart Mode (`time_on = 0`)
`calculate_remaining_filter_time()` divided by `smart_time_on` to compute
filter life in Smart Mode. When `time_on` is `0` (e.g. because the CTW3
status packet does not always carry the smart-time fields), this raised a
`ZeroDivisionError`. Added a guard that falls back to the Normal-Mode
formula when `time_on == 0`, which correctly yields
`ceil(filter_percentage * 60)` days.

---

## `parsers.py`

### CTW3 branch in `device_status()` (command 230)
The generic parser assumed a W5-style 18-byte layout for command 230.
The CTW3 packet is 26+ bytes with a different field layout — extra fields
(`suspend_status`, `electric_status`, `low_battery`, `detect_status`,
voltage readings) shift every subsequent byte offset by 3 or more.

Without this fix, the generic parser read `data[10]` (a pump-runtime byte
with value `2`) as `filter_percentage`, reporting 2 % instead of the real
93 %. Correct CTW3 byte offsets:

| Field | CTW3 offset | Generic offset |
|---|---|---|
| `mode` | `data[2]` | `data[1]` |
| `filter_percentage` | `data[13] / 100.0` | `data[10] / 100` |
| `pump_runtime` | `data[9:13]` (4 B) | `data[6:10]` (4 B) |
| `pump_runtime_today` | `data[15:19]` (4 B) | `data[12:16]` (4 B) |
| `running_status` | `data[14]` | `data[11]` |
| `pet_drinking` | `data[19]` | — |
| `supply_voltage` | `data[20:22]` | — |
| `battery_voltage` | `data[22:24]` | — |
| `battery_percentage` | `data[24]` | — |
| `smart_time_on/off` | `data[26]/data[27]` (if present) | `data[16]/data[17]` |

When `smart_time_on/off` bytes are absent (short packet), they default to
`0`, which triggers the division-by-zero guard in `utils.py`.

---

## `device.py`

### New attributes for CTW3 sensors
Added the following attributes to `__init__` so the `status.setter`
whitelist accepts them without raising `KeyError`:

- `_pet_drinking = 0` — cat-presence / drinking detection byte
- `_pet_drinking_count = 0` — running count of 0→1 drinking transitions
- `_last_pet_drinking = None` — UTC ISO-8601 timestamp of last event
- `_battery_percentage = 0` — battery percentage (CTW3 `data[24]`)
- `_supply_voltage = 0`, `_battery_voltage = 0` — raw voltage readings
- `_suspend_status = 0`, `_electric_status = 0`, `_module_status = 0`,
  `_detect_status = 0` — CTW3-specific state fields

All new attributes are also exposed through the `status` property getter so
they appear in every MQTT state publish.

### CTW3-specific `config` property
`device.config` is used by `mqtt_callback.py` to build the payload for
command 221 (set device configuration). The generic format places
`led_switch` at byte index 2; the CTW3 format requires it at byte index 6
(preceded by 4 battery-timing bytes). A CTW3 branch was added:

```
[smart_time_on, smart_time_off,
 battery_working_high, battery_working_low,
 battery_sleep_high,  battery_sleep_low,
 led_switch, led_brightness, dnd_switch, is_locked]
```

---

## `commands.py`

### Polling wait for `device_initialized` (race condition fix)
`init_device_connection()` sent command 86 (sync) and then checked
`device_initialized` after a fixed `asyncio.sleep(0.75)`. The BLE
notification carrying the command-86 response typically arrives after
~1 s, so the check fired before `device_initialized` was set, causing a
spurious second init cycle (forced disconnect + reconnect).

Added a polling loop that waits up to 3 s (6 × 0.5 s) for
`device_initialized` to become truthy before executing the check.

---

## `event_handlers.py`

### Pet drinking event detection (0→1 transition)
The upstream handler updated `device.status` from the command-230 payload
but did not track drinking events over time.

Before applying `device.status = data` for command 230, the previous
`_pet_drinking` value is saved. After the update, if the value transitioned
from `0` to non-zero:

1. `device._pet_drinking_count` is incremented.
2. `device._last_pet_drinking` is set to the current UTC time in ISO-8601
   format (`datetime.now(timezone.utc).isoformat()`).

This mirrors the behaviour of the official PetKit app, which accumulates
multiple drinking sessions per day.

---

## `mqtt_callback.py`

### Optimistic state updates for config keys
After sending a command-221 (set config) BLE write, the device responds
with a command-221 notification that re-publishes the current state via
MQTT. Without this fix, the internal `_led_switch` / `_led_brightness` /
`_do_not_disturb_switch` values were still stale when the publish fired,
causing Home Assistant to immediately revert the UI toggle.

Before calling `set_device_config()`, the relevant attribute is now updated
optimistically on the device object (e.g. `device._led_switch = value`).

### Optimistic update for `state` and `mode`
Same issue for command-220 (set mode). `_running_status` and `_mode` are
updated before the BLE write.

### Use `power_status` instead of `running_status` for mode changes
In Smart Mode the pump cycles on and off. During the off-phase,
`running_status = 0`. Sending `set_device_mode(running_status=0, mode=2)`
told the device to stop rather than change mode. Changed to use
`power_status` (always `1` while the device is powered on) for mode-change
commands.

---

## `mqtt_payloads.py`

### `battery` binary sensor — added `payload_on` / `payload_off`
HA binary sensors compare the raw value against the strings `"ON"` /
`"OFF"` by default. The battery field is an integer (`0` or `1`), so the
sensor always showed *Unknown*. Added `"payload_on": 1, "payload_off": 0`.

### New `battery_percentage` sensor
Exposes the CTW3 `battery_percentage` field (0–100 %) as a dedicated HA
sensor with `device_class: battery` and `unit_of_measurement: %`.

### New `pet_drinking` binary sensor
Exposes the instantaneous cat-presence detection byte from the command-230
packet with `payload_on: 1, payload_off: 0`.

### New `pet_drinking_count` sensor
Incremental counter of drinking events (`state_class: total_increasing`).
Resets on add-on restart.

### New `last_pet_drinking` sensor
UTC ISO-8601 timestamp of the most recent detected drinking event
(`device_class: timestamp`). Shows *Unknown* until the first event is
detected.

---

## `main.py`

### Configurable `heartbeat_interval`
The upstream `main.py` hard-coded the BLE keep-alive / poll interval.
Changed to read `poll_interval` from the add-on options (via the
`/data/options.json` file written by Home Assistant) and pass it as the
`heartbeat_interval` argument, defaulting to 60 s.
