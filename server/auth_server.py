#!/usr/bin/env python3
"""
Authenticated Multi-client BLE UART Server

Server with gesture-based authentication. Users must authenticate before
they can send/receive chat messages.
"""

import os
import sys
import dbus
import dbus.mainloop.glib
from gi.repository import GLib
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pi-ble-uart-server'))

from example_advertisement import Advertisement
from example_advertisement import register_ad_cb, register_ad_error_cb
from example_gatt_server import Service, Characteristic
from example_gatt_server import register_app_cb, register_app_error_cb
from auth_manager import AuthenticationManager

BLUEZ_SERVICE_NAME = 'org.bluez'
DBUS_OM_IFACE = 'org.freedesktop.DBus.ObjectManager'
LE_ADVERTISING_MANAGER_IFACE = 'org.bluez.LEAdvertisingManager1'
GATT_MANAGER_IFACE = 'org.bluez.GattManager1'
GATT_CHRC_IFACE = 'org.bluez.GattCharacteristic1'
UART_SERVICE_UUID = '6e400001-b5a3-f393-e0a9-e50e24dcca9e'
UART_RX_CHARACTERISTIC_UUID = '6e400002-b5a3-f393-e0a9-e50e24dcca9e'
UART_TX_CHARACTERISTIC_UUID = '6e400003-b5a3-f393-e0a9-e50e24dcca9e'
LOCAL_NAME = 'rpi-gatt-server'
mainloop = None

# Global authentication manager
auth_manager = None


class TxCharacteristic(Characteristic):
    """TX Characteristic - sends data from server to client (notifications)"""

    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, UART_TX_CHARACTERISTIC_UUID,
                                ['notify'], service)
        self.notifying = False
        self.subscriber_count = 0
        # Disable console input for now (can re-enable for admin messages)
        # GLib.io_add_watch(sys.stdin, GLib.IO_IN, self.on_console_input)

    def send_tx(self, message):
        """Send message to ALL subscribed clients"""
        if not self.notifying:
            print('Warning: No clients subscribed')
            return

        # Ensure message ends with newline
        if not message.endswith('\n'):
            message += '\n'

        value = []
        for c in message:
            value.append(dbus.Byte(c.encode()))

        print(f'→ Broadcasting: {message.strip()}')
        self.PropertiesChanged(GATT_CHRC_IFACE, {'Value': value}, [])

    def StartNotify(self):
        """Called when a client subscribes"""
        self.subscriber_count += 1
        self.notifying = True
        print(f'✓ Client subscribed (total: {self.subscriber_count})')

        # Send authentication required message
        self.send_tx('AUTH_REQUIRED')

    def StopNotify(self):
        """Called when a client unsubscribes"""
        global auth_manager

        if self.subscriber_count > 0:
            self.subscriber_count -= 1
        if self.subscriber_count == 0:
            self.notifying = False
        print(f'✗ Client unsubscribed (remaining: {self.subscriber_count})')

        # Clean up all authentication sessions when client disconnects
        # Note: We can't track individual clients in BLE GATT, so we clear all sessions
        if auth_manager and self.subscriber_count == 0:
            print("→ Cleaning up authentication sessions")
            auth_manager.sessions.clear()


class RxCharacteristic(Characteristic):
    """RX Characteristic - receives data from client"""

    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, UART_RX_CHARACTERISTIC_UUID,
                                ['write'], service)
        self.service = service
        self.message_buffer = ""  # Buffer for incoming message fragments

    def WriteValue(self, value, options):
        """Handle incoming message from client"""
        global auth_manager

        try:
            fragment = bytearray(value).decode()
            self.message_buffer += fragment

            # Check if we have a complete message (ends with newline)
            if '\n' in self.message_buffer:
                messages = self.message_buffer.split('\n')
                self.message_buffer = messages[-1]  # Keep incomplete fragment

                # Process each complete message
                for message in messages[:-1]:
                    message = message.strip()
                    if not message:
                        continue

                    print(f'← Received: {message}')

                    # Parse protocol message
                    if message.startswith('USERNAME:'):
                        self._handle_username(message)
                    elif message.startswith('READY_FOR_GESTURE'):
                        self._handle_gesture_ready(message)
                    elif message.startswith('MSG:'):
                        self._handle_chat_message(message)
                    else:
                        print(f'Unknown message format: {message}')

        except Exception as e:
            print(f'Error handling message: {e}')

    def _handle_username(self, message):
        """Handle USERNAME:name message"""
        global auth_manager

        try:
            _, username = message.split(':', 1)
            username = username.strip()

            # Use username as device_id (since we can't get actual device ID in GATT)
            device_id = username.lower()

            # Create session if needed
            if not auth_manager.get_session(device_id):
                auth_manager.create_session(device_id)

            # Handle username
            result = auth_manager.handle_username(device_id, username)

            if result['status'] == 'new_user':
                self.service.tx_characteristic.send_tx(f"NEW_USER:{result['message']}")
            elif result['status'] == 'existing_user':
                self.service.tx_characteristic.send_tx(f"EXISTING_USER:{result['message']}")
            elif result['status'] == 'error':
                self.service.tx_characteristic.send_tx(f"ERROR:{result['message']}")

        except Exception as e:
            print(f'Error handling username: {e}')
            self.service.tx_characteristic.send_tx(f'ERROR:Invalid username format')

    def _handle_gesture_ready(self, message):
        """Handle READY_FOR_GESTURE message - start countdown and recording"""
        global auth_manager

        try:
            # Extract username if included, otherwise use last username
            parts = message.split(':', 1)
            if len(parts) > 1:
                username = parts[1].strip()
                device_id = username.lower()
            else:
                # Need to track which user this is from
                # For now, this is a limitation - we'll handle it in iOS by always sending username
                print('Warning: READY_FOR_GESTURE without username')
                return

            session = auth_manager.get_session(device_id)
            if not session or not session.username:
                self.service.tx_characteristic.send_tx('ERROR:Please send username first')
                return

            # Start countdown and recording in a separate thread to not block
            GLib.timeout_add(100, self._do_gesture_recording, device_id)

        except Exception as e:
            print(f'Error in gesture ready: {e}')

    def _do_gesture_recording(self, device_id):
        """Perform gesture recording and authentication"""
        global auth_manager

        try:
            session = auth_manager.get_session(device_id)
            if not session:
                return False

            attempt_num = session.current_attempt + 1

            # Notify iOS that recording is starting
            # Note: The actual countdown and recording happens inside the gesture functions
            # (generate_single_gesture for registration, authenticate_against_gestures for verification)
            # These functions print countdown on RPi console
            if session.is_new_user:
                self.service.tx_characteristic.send_tx(
                    f'RECORDING_START:Will collect 3 gesture samples. Follow prompts on Raspberry Pi.'
                )
            else:
                self.service.tx_characteristic.send_tx(
                    f'RECORDING_START:Attempt {attempt_num}/3. Perform gesture on Raspberry Pi.'
                )

            # Update session state
            success = auth_manager.start_gesture_recording(device_id)

            if success:
                # Process the gesture (this is where actual recording happens)
                result = auth_manager.process_gesture_attempt(device_id)

                # Check for errors in result
                if 'error' in result:
                    self.service.tx_characteristic.send_tx(f"ERROR:{result['error']}")
                    return False

                # For new users, registration happens all at once
                if session.is_new_user:
                    if result.get('auth_success', False):
                        self.service.tx_characteristic.send_tx(f"AUTH_SUCCESS:{session.username}")
                    else:
                        self.service.tx_characteristic.send_tx(f"AUTH_FAILED:Registration failed")
                else:
                    # For existing users, send attempt result
                    status = 'success' if result.get('success', False) else 'failed'
                    self.service.tx_characteristic.send_tx(
                        f"ATTEMPT_RESULT:{result.get('attempt_number', 0)}:{status}:"
                        f"{result.get('total_passed', 0)}/{result.get('total_attempts', 0)}"
                    )

                    # Check if authentication is complete
                    if result.get('auth_complete', False):
                        if result.get('auth_success', False):
                            self.service.tx_characteristic.send_tx(f"AUTH_SUCCESS:{session.username}")
                        else:
                            self.service.tx_characteristic.send_tx(
                                f"AUTH_FAILED:Only {result.get('total_passed', 0)}/3 attempts passed"
                            )
            else:
                self.service.tx_characteristic.send_tx('ERROR:Recording failed')

        except Exception as e:
            print(f'Error in gesture recording: {e}')
            import traceback
            traceback.print_exc()
            self.service.tx_characteristic.send_tx(f'ERROR:{str(e)}')

        return False  # Don't repeat this timer

    def _handle_chat_message(self, message):
        """Handle MSG:username:text message"""
        global auth_manager

        try:
            # Parse: MSG:username:message_text
            parts = message.split(':', 2)
            if len(parts) < 3:
                print('Invalid message format')
                return

            username = parts[1].strip()
            msg_text = parts[2].strip()
            device_id = username.lower()

            # Check authentication
            if not auth_manager.is_authenticated(device_id):
                self.service.tx_characteristic.send_tx('ERROR:Not authenticated')
                return

            # Broadcast message to all clients
            broadcast_msg = f'MSG:{username}:{msg_text}'
            self.service.tx_characteristic.send_tx(broadcast_msg)
            print(f'💬 {username}: {msg_text}')

        except Exception as e:
            print(f'Error handling chat message: {e}')


class UartService(Service):
    def __init__(self, bus, index):
        Service.__init__(self, bus, index, UART_SERVICE_UUID, True)
        self.tx_characteristic = TxCharacteristic(bus, 0, self)
        self.rx_characteristic = RxCharacteristic(bus, 1, self)
        self.add_characteristic(self.tx_characteristic)
        self.add_characteristic(self.rx_characteristic)


class Application(dbus.service.Object):
    def __init__(self, bus):
        self.path = '/'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service(self, service):
        self.services.append(service)

    @dbus.service.method(DBUS_OM_IFACE, out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        response = {}
        for service in self.services:
            response[service.get_path()] = service.get_properties()
            chrcs = service.get_characteristics()
            for chrc in chrcs:
                response[chrc.get_path()] = chrc.get_properties()
        return response


class UartApplication(Application):
    def __init__(self, bus):
        Application.__init__(self, bus)
        self.add_service(UartService(bus, 0))


class UartAdvertisement(Advertisement):
    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, 'peripheral')
        self.add_service_uuid(UART_SERVICE_UUID)
        self.add_local_name(LOCAL_NAME)
        self.include_tx_power = True


def find_adapter(bus):
    remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, '/'),
                                DBUS_OM_IFACE)
    objects = remote_om.GetManagedObjects()
    for o, props in objects.items():
        if LE_ADVERTISING_MANAGER_IFACE in props and GATT_MANAGER_IFACE in props:
            return o
    return None


def main():
    global mainloop, auth_manager

    print('╔═══════════════════════════════════════════════╗')
    print('║   Authenticated BLE UART Server              ║')
    print('║   Gesture-based authentication required      ║')
    print('╚═══════════════════════════════════════════════╝\n')

    # Initialize authentication manager
    auth_manager = AuthenticationManager(user_db_file="users.json")
    print(f'Registered users: {len(auth_manager.user_db.get_all_users())}')
    if auth_manager.user_db.get_all_users():
        print(f'Users: {", ".join(auth_manager.user_db.get_all_users())}\n')

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    adapter = find_adapter(bus)
    if not adapter:
        print('BLE adapter not found')
        return

    service_manager = dbus.Interface(
        bus.get_object(BLUEZ_SERVICE_NAME, adapter),
        GATT_MANAGER_IFACE)
    ad_manager = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, adapter),
                                 LE_ADVERTISING_MANAGER_IFACE)

    app = UartApplication(bus)
    adv = UartAdvertisement(bus, 0)

    mainloop = GLib.MainLoop()

    service_manager.RegisterApplication(app.get_path(), {},
                                         reply_handler=register_app_cb,
                                         error_handler=register_app_error_cb)
    ad_manager.RegisterAdvertisement(adv.get_path(), {},
                                      reply_handler=register_ad_cb,
                                      error_handler=register_ad_error_cb)

    print('Server running. Waiting for connections...\n')

    try:
        mainloop.run()
    except KeyboardInterrupt:
        adv.Release()
        print('\n\nServer shutting down...')


if __name__ == '__main__':
    main()
