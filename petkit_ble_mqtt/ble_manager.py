from bleak import BleakScanner, BleakClient
from .constants import Constants
from .utils import Utils
from .device import Device
import asyncio
import logging
import time

class BLEManager:
    # Reconnect back-off: doubles after every failed connect cycle, capped so a
    # permanently unreachable device does not spam BlueZ with connect attempts.
    RECONNECT_BACKOFF_MIN = 2
    RECONNECT_BACKOFF_MAX = 300

    def __init__(self, event_handler, commands, logger, callback=None):
        self.connected_devices = {}
        self.available_devices = {}
        self.connectiondata = {}
        self.logger = logger
        self.queue = asyncio.Queue(10)
        self.callback = callback
        self.device = False
        self.event_handler = event_handler
        self.commands = commands
        self.reconnect_delay = self.RECONNECT_BACKOFF_MIN
        # Monotonic time of the last notification received from the device.
        # Read by the watchdog thread in main.py to detect a wedged add-on.
        self.last_notification = time.monotonic()

    def is_connected(self, address):
        """True only if we hold a client for this address AND the transport is
        still up. BlueZ can drop the link without bleak raising anything, so the
        presence of a connected_devices entry alone is not proof of a live
        connection — checking client.is_connected catches the silent drop that
        otherwise surfaces as "Service Discovery has not been performed yet" on
        the next write."""
        client = self.connected_devices.get(address)
        return bool(client and client.is_connected)

    def _on_disconnect(self, client):
        """Registered with bleak so a dropped link is noticed immediately rather
        than at the next heartbeat write."""
        address = client.address
        self.logger.warning(f"Device {address} disconnected (BlueZ callback)")
        self.connected_devices.pop(address, None)
        self._drain_queue()

    async def scan(self):
        self.logger.info("Scanning for Petkit BLE devices...")
        devices = await BleakScanner.discover()
        # dev.name can be None for unnamed BLE devices
        self.available_devices = {dev.address: dev for dev in devices if dev.name and any(supported_device in dev.name for supported_device in Constants.SUPPORTED_DEVICES)}
        for address, device in self.available_devices.items():
            self.logger.info(f"Found device: {device.name} ({address})")
            self.connectiondata[address] = device
        return self.available_devices

    async def connect_device(self, address):
        if address in self.available_devices:
            for attempt in range(1, 4):
                self.logger.info(f"Connecting to {address}... (attempt {attempt}/3)")
                client = BleakClient(address, timeout=65.0,
                                     disconnected_callback=self._on_disconnect)
                try:
                    await client.connect()
                    # Short wait for BlueZ to finish propagating GATT service
                    # discovery internally — avoids "Service Discovery has not
                    # been performed yet" on cmd 200 (bleak calls get_services()
                    # inside connect() in modern versions, but BlueZ may not have
                    # resolved all characteristics yet when connect() returns).
                    await asyncio.sleep(1.5)
                    self.connected_devices[address] = client
                    self.logger.info(f"Connected to {address}")
                    await self.start_notifications(address, Constants.READ_UUID)
                    self.reconnect_delay = self.RECONNECT_BACKOFF_MIN
                    return True
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    # bleak's internal connect timeout can turn an external
                    # cancellation (e.g. from an outer asyncio.wait_for) into a
                    # TimeoutError. Retrying then swallows the cancellation and
                    # the outer timeout never takes effect — honour it here.
                    task = asyncio.current_task()
                    if task is not None and task.cancelling():
                        raise asyncio.CancelledError() from e
                    err = str(e)
                    if "NotPermitted" in err or "Notify acquired" in err:
                        wait = attempt * 10
                        self.logger.warning(f"BlueZ Notify lock held, waiting {wait}s before retry...")
                    elif "Not connected" in err:
                        wait = 5
                        self.logger.warning(f"BLE service discovery failed (Not connected), waiting {wait}s before retry...")
                    else:
                        # Every other error is retried too rather than raised.
                        # Propagating here kills the message_consumer task that
                        # owns reconnection, leaving the add-on permanently dead
                        # with no BLE activity and no further log output.
                        wait = attempt * 5
                        self.logger.warning(
                            f"Connect attempt {attempt}/3 failed ({type(e).__name__}: {e}), "
                            f"waiting {wait}s before retry..."
                        )
                    try:
                        await client.disconnect()
                    except Exception:
                        pass
                    if address in self.connected_devices:
                        del self.connected_devices[address]
                    await asyncio.sleep(wait)
            self.logger.error(f"Could not connect to {address} after 3 attempts")
            return False
        else:
            # Not in the cached scan results — re-scan once. The cache is filled
            # at startup only, so a device that was briefly out of range (or an
            # adapter that was reset) would otherwise never be reachable again.
            self.logger.warning(f"Device {address} not in scan cache, re-scanning...")
            try:
                await asyncio.wait_for(self.scan(), timeout=60.0)
            except Exception as e:
                self.logger.error(f"Re-scan failed: {e}")
                return False

            if address in self.available_devices:
                return await self.connect_device(address)

            self.logger.error(f"Device {address} not found after re-scan")
            return False

    async def disconnect_device(self, address):
        if address in self.connected_devices:
            self.logger.info(f"Disconnecting from {address}...")
            client = self.connected_devices[address]

            # Tear-down on an already-dead link raises; swallow those errors so
            # the client is always removed from the registry. Leaving a stale
            # entry behind makes is_connected()/message_consumer believe the
            # device is still usable and blocks any reconnect.
            try:
                if client.is_connected:
                    await asyncio.wait_for(client.stop_notify(Constants.READ_UUID), timeout=5.0)
            except Exception as e:
                self.logger.debug(f"stop_notify during disconnect failed (ignored): {e}")

            try:
                await asyncio.wait_for(client.disconnect(), timeout=10.0)
            except Exception as e:
                self.logger.debug(f"disconnect failed (ignored): {e}")

            self.connected_devices.pop(address, None)
            self.logger.info(f"Disconnected from {address}")
            return True
        else:
            self.logger.error(f"Device {address} not connected")
            return False

    async def read_characteristic(self, address, characteristic_uuid):
        if address in self.connected_devices:
            self.logger.info(f"Reading characteristic {characteristic_uuid} from {address}")
            client = self.connected_devices[address]
            data = await asyncio.wait_for(
                client.read_gatt_char(characteristic_uuid),
                timeout=10.0
            )
            self.logger.info(f"Read data: {data}")
            return data
        else:
            self.logger.error(f"Device {address} not connected")
            return None

    async def write_characteristic(self, address, characteristic_uuid, data):
        if self.is_connected(address):
            client = self.connected_devices[address]

            try:
                self.logger.info(f"Writing to characteristic {characteristic_uuid} on {address}")

                await asyncio.wait_for(
                    client.write_gatt_char(characteristic_uuid, data),
                    timeout=5.0
                )

                self.logger.info("Write complete")
                return True

            except asyncio.TimeoutError:
                self.logger.error(f"Write timeout on {address}, disconnecting...")
                await self.disconnect_device(address)
                return False

            except Exception as e:
                self.logger.error(f"Write failed: {e}, disconnecting...")
                await self.disconnect_device(address)
                return False

        else:
            # Drop a stale client so message_consumer reconnects instead of
            # retrying writes against a dead handle forever.
            if address in self.connected_devices:
                self.logger.warning(f"Device {address} link is down, dropping stale client")
                await self.disconnect_device(address)
            else:
                self.logger.error(f"Device {address} not connected")
            return False

    async def start_notifications(self, address, characteristic_uuid):
        if address in self.connected_devices:
            self.logger.info(f"Starting notifications for {characteristic_uuid} on {address}")
            client = self.connected_devices[address]
            await asyncio.wait_for(
                client.start_notify(characteristic_uuid, self._handle_notification_wrapper),
                timeout=20.0
            )
            self.logger.info(f"Notifications started for {characteristic_uuid} on {address}")
            return True
        else:
            self.logger.error(f"Device {address} not connected")
            return False

    async def _handle_notification_wrapper(self, sender, data):
        self.last_notification = time.monotonic()
        self.logger.debug(f"RAW BLE NOTIFICATION: hex={data.hex()} bytes={list(data)}")
        await self.event_handler.handle_notification(sender, data)

    async def stop_notifications(self, address, characteristic_uuid):
        if address in self.connected_devices:
            self.logger.info(f"Stopping notifications for {characteristic_uuid} on {address}")
            client = self.connected_devices[address]
            await client.stop_notify(characteristic_uuid)
            self.logger.info(f"Notifications stopped for {characteristic_uuid} on {address}")
            return True
        else:
            self.logger.error(f"Device {address} not connected")
            return False

    async def heartbeat(self, interval):
        while True:
            if not self.connected_devices:
                await asyncio.sleep(5)
                continue
            for address in list(self.connected_devices.keys()):
                # Skip a device whose link is already down — message_consumer
                # owns the reconnect. Queueing commands onto a dead link only
                # fills the queue with work that will be drained anyway.
                if not self.is_connected(address):
                    self.logger.debug(f"Skipping heartbeat for {address}: link is down")
                    continue
                try:
                    await self.commands.get_battery()  # To update voltage
                    await self.commands.get_device_update()

                    if self.queue.qsize() > 10:
                        raise Exception("Queue size over threshold. Disconnecting...")

                except Exception as e:
                    self.logger.error(f"Error during heartbeat: {e}")
                    self.logger.info(f"Disconnecting {address} — message_consumer will reconnect")
                    await self.disconnect_device(address)
            await asyncio.sleep(interval)

    def _drain_queue(self):
        drained = 0
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
                drained += 1
            except asyncio.QueueEmpty:
                break
        if drained:
            self.logger.info(f"Drained {drained} stale commands from queue after disconnect")

    async def message_consumer(self, address, characteristic_uuid):
        while True:
            # Check the live link, not just the registry entry — a silently
            # dropped BlueZ connection leaves the entry in place and would
            # otherwise send us into an endless connect/one-good-write/fail loop.
            if not self.is_connected(address):
                self.logger.warning(
                    f"Device {address} not connected. Draining queue and "
                    f"reconnecting in {self.reconnect_delay}s..."
                )
                self._drain_queue()
                await asyncio.sleep(self.reconnect_delay)

                if await self.connect_device(address):
                    # connect_device() resets reconnect_delay on success.
                    await self._reinitialize_after_reconnect()
                else:
                    self.reconnect_delay = min(self.reconnect_delay * 2,
                                               self.RECONNECT_BACKOFF_MAX)
                    self.logger.warning(
                        f"Reconnect to {address} failed, next attempt in "
                        f"{self.reconnect_delay}s"
                    )
                continue

            message = await self.queue.get()
            await self.write_characteristic(address, characteristic_uuid, message)
            self.queue.task_done()

    async def _reinitialize_after_reconnect(self):
        """Re-run the init handshake after an unplanned reconnect.

        A fresh BLE link starts unauthenticated: the device only answers status
        commands once cmd 73/86 have completed. Without this the reconnect
        succeeds but every subsequent heartbeat returns nothing useful.
        """
        device = getattr(self.commands, "device", None)

        if device is not None:
            device.initialization_state = False
            device.device_initialized = False

        # Hard cap: init_device_connection() contains unbounded retry loops that
        # never return if the device stops answering mid-handshake. Without this
        # the consumer task would hang and no reconnect could ever be attempted.
        try:
            await asyncio.wait_for(self.commands.init_device_connection(), timeout=90.0)
            self.logger.info("Re-initialized device after reconnect")
        except asyncio.TimeoutError:
            self.logger.error("Re-initialization timed out after 90s, forcing reconnect")
            await self.disconnect_device(self.commands.device.mac)
        except Exception as e:
            # Link may be up but unauthenticated — drop it so the next loop
            # iteration reconnects instead of polling a device that won't answer.
            self.logger.error(f"Re-initialization after reconnect failed: {e}, forcing reconnect")
            await self.disconnect_device(self.commands.device.mac)

    async def message_producer(self, message):
        await self.queue.put(message)
