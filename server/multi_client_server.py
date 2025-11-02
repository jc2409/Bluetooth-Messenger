#!/usr/bin/env python3
"""
Multi-client BLE UART server for iPhone-to-iPhone messaging via Raspberry Pi.

This server acts as a message relay between multiple connected iPhone clients.
Each client has its own connection, and messages are broadcast to all OTHER clients
(not echoed back to the sender).
"""

import sys
import dbus
import dbus.mainloop.glib
from gi.repository import GLib
from example_advertisement import Advertisement
from example_advertisement import register_ad_cb, register_ad_error_cb
from example_gatt_server import Service, Characteristic
from example_gatt_server import register_app_cb, register_app_error_cb

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

# Global list to track all connected clients
connected_clients = []


class TxCharacteristic(Characteristic):
    """TX Characteristic - sends data from server to client (notifications)"""

    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, UART_TX_CHARACTERISTIC_UUID,
                                ['notify'], service)
        self.notifying = False
        self.client_id = None  # Track which client this characteristic belongs to
        GLib.io_add_watch(sys.stdin, GLib.IO_IN, self.on_console_input)

    def on_console_input(self, fd, condition):
        """Handle console input from server admin"""
        s = fd.readline()
        if s.isspace():
            pass
        else:
            # Broadcast server message to all connected clients
            print(f'Server broadcasting: {s.strip()}')
            broadcast_message(s, source_client=None)
        return True

    def send_tx(self, s):
        """Send message to this specific client"""
        if not self.notifying:
            return
        value = []
        for c in s:
            value.append(dbus.Byte(c.encode()))
        self.PropertiesChanged(GATT_CHRC_IFACE, {'Value': value}, [])

    def StartNotify(self):
        if self.notifying:
            return
        self.notifying = True
        print(f'Client {self.client_id} started notifications')
        # Register this client as connected
        if self not in connected_clients:
            connected_clients.append(self)
            print(f'Total connected clients: {len(connected_clients)}')

    def StopNotify(self):
        if not self.notifying:
            return
        self.notifying = False
        print(f'Client {self.client_id} stopped notifications')
        # Unregister this client
        if self in connected_clients:
            connected_clients.remove(self)
            print(f'Total connected clients: {len(connected_clients)}')


class RxCharacteristic(Characteristic):
    """RX Characteristic - receives data from client to server (writes)"""

    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, UART_RX_CHARACTERISTIC_UUID,
                                ['write'], service)
        self.service = service

    def WriteValue(self, value, options):
        message = bytearray(value).decode()
        sender_tx = self.service.tx_characteristic

        print(f'Received from client {sender_tx.client_id}: {message}')

        # Broadcast to all OTHER clients (not the sender)
        broadcast_message(message, source_client=sender_tx)


def broadcast_message(message, source_client=None):
    """
    Broadcast a message to all connected clients except the source.

    Args:
        message (str): The message to broadcast
        source_client (TxCharacteristic): The TX characteristic of the sender
                                          (None if message is from server)
    """
    recipients = 0
    for client_tx in connected_clients:
        if client_tx != source_client:  # Don't send back to sender
            client_tx.send_tx(message)
            recipients += 1

    if source_client:
        print(f'Relayed message to {recipients} other client(s)')
    else:
        print(f'Broadcast server message to {recipients} client(s)')


class UartService(Service):
    def __init__(self, bus, index):
        Service.__init__(self, bus, index, UART_SERVICE_UUID, True)
        self.tx_characteristic = TxCharacteristic(bus, 0, self)
        self.rx_characteristic = RxCharacteristic(bus, 1, self)

        # Assign a unique ID to this characteristic pair
        import uuid
        self.tx_characteristic.client_id = str(uuid.uuid4())[:8]

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
        print('Skip adapter:', o)
    return None


def main():
    global mainloop
    print('=== Multi-Client BLE UART Server ===')
    print('This server relays messages between connected iPhone clients.')
    print('Type messages here to broadcast to all clients.')
    print('=====================================\n')

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
    try:
        mainloop.run()
    except KeyboardInterrupt:
        adv.Release()
        print('\nServer shutting down...')


if __name__ == '__main__':
    main()
