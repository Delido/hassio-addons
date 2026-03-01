import logging
from datetime import datetime, timezone
from .utils import Utils
from .parsers import Parsers

class EventHandlers:
    def __init__(self, device, commands, logger, callback=None):
        self.logger = logger
        self.device = device
        self.callback = callback

        # Registry of command values to handler methods
        self.handlers = {
            66: Parsers.device_battery,
            #73: Parsers.device_init,
            86: Parsers.device_synchronization,
            200: Parsers.device_firmware,
            210: Parsers.device_state,
            211: Parsers.device_configuration,
            212: Parsers.device_last_session,
            213: Parsers.device_identifiers,
            230: Parsers.device_status,
        }

        # Messages we want to forward
        self.forward_messages = [
            220,
            221,
            230
        ]

    async def handle_notification(self, sender, message):
        parsed_data = Utils.parse_bytearray(message)
        cmd = parsed_data['cmd']
        self.logger.info(f"Received command {cmd}")

        self.logger.debug(f"Parsed data:\n{parsed_data}")

        data = None

        if cmd in self.handlers:
            handler = self.handlers[cmd]
            data = handler(parsed_data['data'], self.device.alias)
            self.logger.debug(f"Parsed data\n{data}")

            # Update config
            if cmd in [86, 200, 213]:
                self.device.info = data

            # Update status — for cmd 230 detect pet_drinking 0→nonzero transition
            if cmd in [66, 210, 211, 212, 230]:
                if cmd == 230:
                    prev_pet_drinking = self.device._pet_drinking

                self.device.status = data

                if cmd == 230:
                    new_pet_drinking = self.device._pet_drinking
                    now = datetime.now(timezone.utc)
                    # Minimum duration: state must be 1 for at least this long to count as a session
                    min_session_seconds = 10

                    if prev_pet_drinking == 0 and new_pet_drinking != 0:
                        # 0→1: start tracking, but don't count yet
                        if self.device._drinking_session_start is None:
                            self.device._drinking_session_start = now
                            self.logger.info("Pet drinking: state=1, session started (pending confirmation)")
                        else:
                            self.logger.debug("Pet drinking: 0→1 with active session, continuing")

                    elif prev_pet_drinking != 0 and new_pet_drinking == 0:
                        # 1→0: session ended — count only if duration >= minimum
                        if self.device._drinking_session_start is not None:
                            duration = int((now - self.device._drinking_session_start).total_seconds())
                            if duration >= min_session_seconds:
                                self.device._pet_drinking_count += 1
                                self.device._last_pet_drinking = now.isoformat()
                                self.device._last_pet_drinking_duration = duration
                                self.logger.info(
                                    f"Pet drinking session confirmed (duration={duration}s,"
                                    f" count={self.device._pet_drinking_count})"
                                )
                            else:
                                self.logger.info(
                                    f"Pet drinking: too short ({duration}s < {min_session_seconds}s), not counted"
                                )
                            self.device._drinking_session_start = None

        if self.callback and cmd in self.forward_messages:
            self.callback(self.device.mac_readable, self.device.status)

        return parsed_data
