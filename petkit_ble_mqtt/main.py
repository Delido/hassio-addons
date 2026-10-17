import argparse
import asyncio
import logging
import os
import threading
import time
from PetkitW5BLEMQTT import BLEManager, Constants, Device, EventHandlers, Commands, Logger, MQTTClient, MQTTCallback, MQTTPayloads, Utils

class Manager:
    # Minimum time without any BLE notification before the watchdog kills the
    # process. Must comfortably exceed one full reconnect cycle (3 connect
    # attempts with 65s timeouts plus back-off).
    STALL_TIMEOUT_MIN = 900

    def __init__(self, address, mqtt_enabled=False, mqtt_settings=None, logging_level=logging.INFO, heartbeat_interval=60):
        self.address = address
        self.device = Device(self.address)
        self.heartbeat_interval = heartbeat_interval

        self.setup_logging(logging_level)
        self.logger = logging.getLogger(f"PetkitW5BLEMQTT-{self.device.mac_readable}")
        debug = logging_level == logging.DEBUG  # Determine if debug logging is enabled

        # Correct order of instantiation
        self.commands = Commands(ble_manager=None, device=self.device, logger=self.logger)
        self.event_handlers = EventHandlers(device=self.device, commands=self.commands, logger=self.logger)
        self.ble_manager = BLEManager(event_handler=self.event_handlers, commands=self.commands, logger=self.logger)
        self.ble_manager.manager = self

        # Update ble_manager in commands now that it is created
        self.commands.ble_manager = self.ble_manager

        self.mqtt_client = None
        self.mqtt_callback = None
        self.mqtt_payloads = None

        if mqtt_enabled and mqtt_settings:
            self.mqtt_client = MQTTClient(logger=self.logger, **mqtt_settings)
            self.mqtt_client.connect()
            self.event_handlers.callback = self.mqtt_client.publish_state

    def start_stall_watchdog(self):
        """Last line of defence, independent of asyncio.

        Whatever wedges the add-on — a swallowed cancellation, a hung BlueZ
        call, a blocked event loop — the visible symptom is the same: no more
        notifications from the device. This thread hard-exits the process once
        that has lasted too long, so run.sh starts a fresh one. It runs outside
        the event loop on purpose: an in-loop watchdog dies with the loop.
        """
        stall_timeout = max(self.STALL_TIMEOUT_MIN, 10 * self.heartbeat_interval)

        def watch():
            while True:
                time.sleep(30)
                silent = time.monotonic() - self.ble_manager.last_notification
                if silent > stall_timeout:
                    self.logger.error(
                        f"Watchdog: no data from device for {int(silent)}s "
                        f"(limit {stall_timeout}s) — exiting for restart"
                    )
                    try:
                        if self.mqtt_client:
                            self.mqtt_client.publish_availability(self.device.mac_readable, "offline")
                    except Exception:
                        pass
                    logging.shutdown()
                    os._exit(1)

        threading.Thread(target=watch, name="stall-watchdog", daemon=True).start()

    def setup_logging(self, logging_level):
        logging.basicConfig(level=logging_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    async def run(self, address):
        self.start_stall_watchdog()

        await self.ble_manager.scan()

        self.logger.info(f"Connecting...")

        if not await self.ble_manager.connect_device(address):
            self.logger.error(f"Initial connection to {address} failed — exiting for supervisor restart")
            return

        self.logger.info(f"Connected.")

        # Start the producer and consumer tasks
        consumer = asyncio.create_task(self.ble_manager.message_consumer(address, Constants.WRITE_UUID))
        heartbeat = None

        # Init the device
        self.commands.init_device_data()

        try:
            # Connect to the device. Bounded so a device that stops answering
            # mid-handshake cannot wedge startup indefinitely.
            await asyncio.wait_for(self.commands.init_device_connection(), timeout=120.0)

            # Initialize the heartbeat with configurable interval
            heartbeat = asyncio.create_task(self.ble_manager.heartbeat(self.heartbeat_interval))

            if self.mqtt_client and self.mqtt_client.connected:
                # Setup the MQTT payloads
                self.mqtt_payloads = MQTTPayloads(device=self.device)

                # Tell MQTTClient which identifier to use for availability
                self.mqtt_client.set_identifier(self.device.mac_readable)

                self.logger.info(f"Sending payloads...")

                # Setup the MQTT callback function
                self.mqtt_callback = MQTTCallback(device=self.device, commands=self.commands)

                # Generate discovery payloads
                discovery_payloads = self.mqtt_payloads.discovery()

                # Post discovery payloads
                self.mqtt_client.publish_discovery(discovery_payloads)

                # Subscribe to the command topic
                self.mqtt_client.subscribe(f"PetkitMQTT/{self.device.mac_readable}/command")

                # Setup the callback function for handling messages
                self.mqtt_client.set_on_message(self.mqtt_callback.delegate)

                # Post online to availability topic
                self.mqtt_client.publish_availability(self.device.mac_readable, "online")

            # Watchdog: if either background task dies (unhandled exception or
            # cancellation) the add-on would otherwise sit in this loop forever
            # with no BLE traffic and no log output — looking alive to the
            # supervisor while doing nothing. Exiting lets run.sh restart us.
            while True:
                for name, task in (("message_consumer", consumer),
                                   ("heartbeat", heartbeat)):
                    if task is not None and task.done():
                        exc = task.exception() if not task.cancelled() else None
                        if exc is not None:
                            self.logger.error(f"Task {name} died: {exc!r}")
                        else:
                            self.logger.error(f"Task {name} exited unexpectedly")
                        raise RuntimeError(f"Background task {name} is no longer running")
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            # Handling cleanup on keyboard interrupt
            self.logger.info("Interrupted, cleaning up...")
        finally:
            # Cancel background tasks before tearing down the connection — a
            # still-running message_consumer would otherwise immediately
            # reconnect the device we are about to disconnect.
            for task in (consumer, heartbeat):
                if task is not None and not task.done():
                    task.cancel()
            for task in (consumer, heartbeat):
                if task is not None:
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                    except Exception as e:
                        self.logger.debug(f"Task raised during cleanup (ignored): {e}")

            try:
                await self.ble_manager.disconnect_device(address)
            except Exception as e:
                self.logger.debug(f"Disconnect during cleanup failed (ignored): {e}")

            if self.mqtt_client:
                self.mqtt_client.publish_availability(self.device.mac_readable, "offline")
                self.mqtt_client.disconnect()

    async def restart_run(self, address=None):
        if address is None:
            address = self.address

        self.logger.info("Restarting run function due to inactivity.")

        # Reset initialization_state and software_version
        self.device.initialization_state = False
        self.device.info = {'software_version': None}

        await self.run(address)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BLE Manager")
    parser.add_argument("--address", type=str, required=True, help="BLE device address")
    parser.add_argument("--mqtt", action='store_true', help="Enable MQTT")
    parser.add_argument("--mqtt_broker", type=str, help="MQTT broker address")
    parser.add_argument("--mqtt_port", default=1883, type=int, help="MQTT broker port")
    parser.add_argument("--mqtt_user", type=str, help="MQTT username")
    parser.add_argument("--mqtt_password", type=str, help="MQTT password")
    parser.add_argument("--heartbeat_interval", type=int, default=60, help="Heartbeat interval in seconds")
    parser.add_argument("--logging_level", type=str, default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    args = parser.parse_args()

    mqtt_settings = {
        "client_id": f"PetkitW5BLEMQTTClient-{args.address.replace(':','')}",
        "broker": args.mqtt_broker,
        "port": args.mqtt_port,
        "username": args.mqtt_user,
        "password": args.mqtt_password
    } if args.mqtt else None

    logging_level = getattr(logging, args.logging_level.upper(), logging.INFO)

    manager = Manager(
        args.address,
        mqtt_enabled=args.mqtt,
        mqtt_settings=mqtt_settings,
        logging_level=logging_level,
        heartbeat_interval=args.heartbeat_interval
    )
    asyncio.run(manager.run(args.address))
