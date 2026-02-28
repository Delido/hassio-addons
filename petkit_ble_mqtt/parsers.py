from .utils import Utils

class Parsers:
    # Get Battery Synchronization
    @staticmethod
    def device_battery(data, alias):
        return {
            "voltage": ((data[0] * 16 * 16) + (data[1] & 255)) / 1000.0,  # Magic borrowed from Petkit
            "battery": data[2]
        }

    # Init data
    @staticmethod
    def device_init(data, alias):
        return {"serial": Utils.bytes_to_long(data[7:11])}

    # Synchronize data
    @staticmethod
    def device_synchronization(data, alias):
        return {"device_initialized": data[0]}

    # Device Information
    @staticmethod
    def device_firmware(data, alias):
        # Extract the firmware version - supposedly
        # According to the com.petkit.oversea app, the Hardware is actually [0] while firmware is [1]
        # they are however presented as v[0].[1] in the actual app
        firmware = float(f"{data[0]}.{data[1]}")

        return {"firmware": firmware }

    # Get device state
    @staticmethod
    def device_state(data, alias):
        """Decode device state frame (command 210) for Petkit devices.
        Args:
            data: Raw bytearray from the device
            alias: Device model identifier ('CTW3' or others)
        Returns:
            Dictionary with decoded device state information
        """
        if alias == "CTW3":
            # CTW3 specific decoding (26+ byte frame)
            if len(data) < 26:
                return {"error": "Insufficient data length for CTW3"}
            # Decode CTW3 specific data
            return {
                "power_status": data[0],  # 0=off, 1=on
                "suspend_status": data[1],  # Suspension status
                "mode": data[2],  # Current operation mode
                "electric_status": data[3],  # Power supply status
                "dnd_state": data[4],  # DND at night enabled
                "warning_breakdown": data[5],  # Hardware failure warning
                "warning_water_missing": data[6],  # Water shortage warning
                "low_battery": data[7],  # Low battery warning
                "warning_filter": data[8],  # Filter replacement warning
                "pump_runtime": Utils.bytes_to_integer(data[9:13]), # Pump run time in seconds (bytes 9-12, 4-byte integer)
                "filter_percentage": data[13],  # Filter life percentage (0-100)
                "running_status": data[14],  # Current running state
                "pump_runtime_today": Utils.bytes_to_integer(data[15:19]), # Today's pump run time in seconds (bytes 15-18, 4-byte integer)
                "detect_status": data[19],  # Cat presence detection status
                "supply_voltage": Utils.bytes_to_short(data[20:22]),  # Voltage readings mV
                "battery_voltage": Utils.bytes_to_short(data[22:24]),  # Voltage readings mV
                "battery_percentage": data[24],  # Battery percentage (0-100)
                "module_status": data[25],  # Module communication status
            }
        else:
            # Default decoding for other Petkit devices (12+ byte frame)
            return {
                "power_status": data[0],  # Power state
                "mode": data[1],  # Operation mode
                "dnd_state": data[2],  # Do Not Disturb status
                "warning_breakdown": data[3],  # Malfunction warning
                "warning_water_missing": data[4],  # Water shortage warning
                "warning_filter": data[5],  # Filter warning
                "pump_runtime": Utils.bytes_to_integer(data[6:10]),  # Pump runtime
                "filter_percentage": Utils.byte_to_integer(data[10]) / 100,  # Filter %
                "running_status": Utils.byte_to_integer(data[11]),  # Running state
            }

    # Get device configuration
    @staticmethod
    def device_configuration(data, alias):
        if alias == "CTW3":
            # CTW3 specific decoding (10+ byte frame)
            battery_working_time = Utils.bytes_to_short(data[2:4])
            battery_sleep_time = Utils.bytes_to_short(data[4:6])

            is_locked = 0
            if len(data) > 9:
                is_locked = data[9]

            return {
                "smart_time_on": data[0],  # Minutes (from 1 to 60 minutes)
                "smart_time_off": data[1],  # Minutes (from 1 to 60 minutes)
                "battery_working_time": battery_working_time, # ???
                "battery_time_on": Utils.minutes_to_timestamp(battery_working_time), # Minutes:Seconds (from 15seconds to 5 minutes)
                "battery_sleep_time": battery_sleep_time,  # Minutes
                "battery_time_off": Utils.minutes_to_timestamp(battery_sleep_time),  # Minutes:Seconds (from 1min to 180minutes)
                "led_switch": data[6],  # 0 or 1 (off/on)
                "led_brightness": data[7],  # From 1 to 3 (1=low, 2=medium, 3=high)
                "do_not_disturb_switch": data[8],  # 0 or 1 (off/on)
                "is_locked": is_locked,  # ???
            }
        else:
            # Default decoding for other Petkit devices (14+ byte frame)
            led_light_time_on = Utils.bytes_to_short(data[4:6])
            led_light_time_off = Utils.bytes_to_short(data[6:8])
            do_not_disturb_time_on = Utils.bytes_to_short(data[9:11])
            do_not_disturb_time_off = Utils.bytes_to_short(data[11:13])

            return {
                "smart_time_on": data[0],
                "smart_time_off": data[1],
                "led_switch": data[2],
                "led_brightness": data[3],
                "led_light_time_on": led_light_time_on,
                "led_light_time_on_readable": Utils.minutes_to_timestamp(led_light_time_on),
                "led_on_byte1": data[4],
                "led_on_byte2": data[5],
                "led_light_time_off": led_light_time_off,
                "led_light_time_off_readable": Utils.minutes_to_timestamp(led_light_time_off),
                "led_off_byte1": data[6],
                "led_off_byte2": data[7],
                "do_not_disturb_switch": data[8],
                "do_not_disturb_time_on": do_not_disturb_time_on,
                "do_not_disturb_time_on_readable": Utils.minutes_to_timestamp(do_not_disturb_time_on),
                "dnd_on_byte1": data[9],
                "dnd_on_byte2": data[10],
                "do_not_disturb_time_off": do_not_disturb_time_off,
                "do_not_disturb_time_off_readable": Utils.minutes_to_timestamp(do_not_disturb_time_off),
                "dnd_off_byte1": data[11],
                "dnd_off_byte2": data[12],
                "is_locked": data[13] if len(data) > 13 else None,
            }

    # Get device ID and serial
    @staticmethod
    def device_identifiers(data, alias):
        device_id_bytes, device_id = Utils.extract_device_id(data)
        serial = Utils.extract_serial_number(data)

        return {
            "device_id": device_id,
            "device_id_bytes": device_id_bytes,
            "serial": serial,
        }

    # Status
    @staticmethod
    def device_status(data, alias):
        if alias == "CTW3":
            # CTW3 comprehensive status (cmd 230) mirrors CTW3 device_state (cmd 210) layout
            # for the first 26 state bytes, confirmed by observing generic parser
            # misreading data[10] (pump_runtime byte) as filter_percentage (shows 2% not 93%)
            if len(data) < 20:
                return {"error": "Insufficient data length for CTW3 status"}

            mode = data[2]
            filter_percentage = data[13] / 100.0
            pump_runtime = Utils.bytes_to_integer(data[9:13])
            pump_runtime_today = Utils.bytes_to_integer(data[15:19])

            # smart_time_on/off: read from packet tail if present, else 0.
            # With time_on=0 the guard in calculate_remaining_filter_time fires:
            #   math.ceil(filter_percentage * 60.0) → e.g. ceil(0.93 * 60) = 56 days ✓
            smart_time_on = data[26] if len(data) > 26 else 0
            smart_time_off = data[27] if len(data) > 27 else 0

            filter_time_left, purified_water, purified_water_today, energy_consumed = Utils.calculate_values(
                mode, filter_percentage, smart_time_on, smart_time_off, alias, pump_runtime_today, pump_runtime
            )

            result = {
                "power_status": data[0],
                "suspend_status": data[1],
                "mode": mode,
                "electric_status": data[3],
                "dnd_state": data[4],
                "warning_breakdown": data[5],
                "warning_water_missing": data[6],
                "low_battery": data[7],
                "warning_filter": data[8],
                "pump_runtime": pump_runtime,
                "filter_percentage": filter_percentage,
                "running_status": data[14],
                "pump_runtime_today": pump_runtime_today,
                "pet_drinking": data[19],  # Cat presence / drinking detection
                "smart_time_on": smart_time_on,
                "smart_time_off": smart_time_off,
                "pump_runtime_readable": Utils.get_timestamp_days(pump_runtime),
                "pump_runtime_today_readable": Utils.get_timestamp_hours(pump_runtime_today),
                "filter_time_left": filter_time_left,
                "purified_water": purified_water,
                "purified_water_today": purified_water_today,
                "energy_consumed": energy_consumed,
            }

            if len(data) >= 25:
                result["supply_voltage"] = Utils.bytes_to_short(data[20:22])
                result["battery_voltage"] = Utils.bytes_to_short(data[22:24])
                result["battery_percentage"] = data[24]

            return result

        else:
            mode = data[1]
            filter_percentage = Utils.byte_to_integer(data[10]) / 100
            smart_time_on = data[16]
            smart_time_off = data[17]
            alias = alias
            pump_runtime_today = Utils.bytes_to_integer(data[12:16])
            pump_runtime = Utils.bytes_to_integer(data[6:10])

            filter_time_left, purified_water, purified_water_today, energy_consumed = Utils.calculate_values(mode, filter_percentage, smart_time_on, smart_time_off, alias, pump_runtime_today, pump_runtime)

            led_light_time_on = Utils.bytes_to_short(data[20:22])
            led_light_time_off = Utils.bytes_to_short(data[22:24])
            do_not_disturb_time_on = Utils.bytes_to_short(data[25:27])
            do_not_disturb_time_off = Utils.bytes_to_short(data[27:29])

            return {
                "power_status": data[0],
                "mode": mode,
                "dnd_state": data[2],
                "warning_breakdown": data[3],
                "warning_water_missing": data[4],
                "warning_filter": data[5],
                "pump_runtime": pump_runtime,
                "filter_percentage": filter_percentage,
                "running_status": Utils.byte_to_integer(data[11]),
                "pump_runtime_today": pump_runtime_today,
                "smart_time_on": smart_time_on,
                "smart_time_off": smart_time_off,
                "led_switch": data[18],
                "led_brightness": data[19],
                "led_light_time_on": led_light_time_on,
                "led_light_time_on_readable": Utils.minutes_to_timestamp(led_light_time_on),
                "led_on_byte1": data[20],
                "led_on_byte2": data[21],
                "led_light_time_off": led_light_time_off,
                "led_light_time_off_readable": Utils.minutes_to_timestamp(led_light_time_off),
                "led_off_byte1": data[22],
                "led_off_byte2": data[23],
                "do_not_disturb_switch": data[24],
                "do_not_disturb_time_on": do_not_disturb_time_on,
                "do_not_disturb_time_on_readable": Utils.minutes_to_timestamp(do_not_disturb_time_on),
                "dnd_on_byte1": data[25],
                "dnd_on_byte2": data[26],
                "do_not_disturb_time_off": do_not_disturb_time_off,
                "do_not_disturb_time_off_readable": Utils.minutes_to_timestamp(do_not_disturb_time_off),
                "dnd_off_byte1": data[27],
                "dnd_off_byte2": data[28],
                "pump_runtime_readable": Utils.get_timestamp_days(pump_runtime),
                "pump_runtime_today_readable": Utils.get_timestamp_hours(pump_runtime_today),
                "filter_time_left": filter_time_left,
                "purified_water": purified_water,
                "purified_water_today": purified_water_today,
                "energy_consumed": energy_consumed,
            }

    # CMD 212: last pet drinking session duration
    # byte[0] = status (0x01 = OK)
    # byte[4] = duration in ~6-second units (confirmed via BLE sniff:
    #           6 units × 6s = 36s ≈ 35s measured session)
    @staticmethod
    def device_last_session(data, alias):
        if len(data) < 5 or data[0] != 1:
            return {}
        return {"last_pet_drinking_duration": data[4] * 6}
