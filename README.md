# Bluetooth Messenger

A Bluetooth Low Energy (BLE) messenger system that enables iOS devices to communicate with each other through a Raspberry Pi server using the Nordic UART Service (NUS) protocol.

## Architecture

- **Server**: Raspberry Pi running Python-based BLE GATT server
- **Client**: iOS app built with SwiftUI and CoreBluetooth

The system uses the Nordic UART Service (NUS) for bidirectional communication:
- Service UUID: `6E400001-B5A3-F393-E0A9-E50E24DCCA9E`
- TX Characteristic (Server → Client): `6E400003-B5A3-F393-E0A9-E50E24DCCA9E`
- RX Characteristic (Client → Server): `6E400002-B5A3-F393-E0A9-E50E24DCCA9E`

## Features

### iOS Client
- Scan for BLE devices advertising the UART service
- Connect to Raspberry Pi server
- Send and receive text messages
- Real-time connection status
- iMessage-style chat interface
- Auto-scrolling message list
- Bluetooth state monitoring

### Server (Raspberry Pi)
- BLE GATT server using BlueZ
- Nordic UART Service implementation
- Bidirectional message relay
- Console input for server messages
- Support for multiple characteristics

## Requirements

### Raspberry Pi
- Raspberry Pi 3/4/Zero W (with built-in Bluetooth)
- Raspbian/Raspberry Pi OS
- Python 3.x
- BlueZ Bluetooth stack
- Required Python packages:
  - `dbus-python`
  - `PyGObject`

### iOS
- iOS 14.0 or later
- Xcode 14.0 or later
- Physical iOS device (Bluetooth doesn't work in simulator)

## Setup Instructions

### Raspberry Pi Server Setup

1. **Install dependencies**:
```bash
sudo apt-get update
sudo apt-get install python3-pip python3-dbus libglib2.0-dev
sudo pip3 install dbus-python PyGObject
```

2. **Enable Bluetooth**:
```bash
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
```

3. **Run the UART server**:
```bash
cd server
sudo python3 uart_peripheral.py
```

The server will:
- Start advertising as `rpi-gatt-server`
- Wait for iOS clients to connect
- Accept typed messages from console
- Display received messages from clients

### iOS App Setup

1. **Open the project**:
```bash
cd client
open client.xcodeproj
```

2. **Configure signing**:
   - Select your development team in Xcode
   - Update the bundle identifier if needed

3. **Add Info.plist to target**:
   - In Xcode, select the `client` target
   - Go to "Build Settings"
   - Search for "Info.plist File"
   - Set the path to `client/Info.plist`

4. **Build and run**:
   - Connect your iOS device
   - Select your device as the build target
   - Click Run (⌘R)

## Usage

### Starting a Conversation

1. **Start the Raspberry Pi server**:
```bash
sudo python3 uart_peripheral.py
```

2. **Open the iOS app** on your device

3. **Connect to the server**:
   - Tap the menu button (⋯) in the top right
   - Select "Connect to Device"
   - Wait for `rpi-gatt-server` to appear
   - Tap on it to connect

4. **Send messages**:
   - Type your message in the text field
   - Tap the send button
   - Messages appear in blue (sent) or gray (received)

### Server Console Messages

On the Raspberry Pi, type messages in the console and press Enter to send them to all connected iOS clients.

### Multi-User Setup

To enable communication between multiple iPhone users through the Raspberry Pi:

1. Each iPhone connects to the same Raspberry Pi server
2. Messages sent from any iPhone go to the server
3. The server can relay messages to all connected devices
4. Currently, the server displays received messages in console

**Note**: The current implementation shows received messages on the server console. To relay messages between iPhones, you would need to modify `uart_peripheral.py` to broadcast received messages to all connected clients.

## Project Structure

```
Bluetooth-Messenger/
├── client/                    # iOS application
│   ├── client/
│   │   ├── BluetoothManager.swift    # BLE central manager
│   │   ├── ContentView.swift         # Main UI
│   │   ├── clientApp.swift          # App entry point
│   │   └── Info.plist               # Bluetooth permissions
│   └── client.xcodeproj
├── server/                    # Raspberry Pi server
│   ├── uart_peripheral.py    # UART service implementation
│   ├── example_gatt_server.py # GATT server base classes
│   └── example_advertisement.py # BLE advertisement
└── README.md
```

## Code Overview

### BluetoothManager.swift

The `BluetoothManager` class handles all BLE operations:
- **Central Manager**: Scans for and connects to peripherals
- **Service Discovery**: Finds the UART service and characteristics
- **Data Transfer**: Sends/receives messages with automatic chunking
- **State Management**: Publishes connection and message state

Key methods:
- `startScanning()`: Begin BLE scan for UART service
- `connect(to:)`: Connect to a specific peripheral
- `sendMessage(_:)`: Send text message (auto-chunks to 20 bytes)
- `disconnect()`: Close connection

### ContentView.swift

SwiftUI interface with three main components:

1. **ContentView**: Main chat interface
   - Status indicator and connection info
   - Scrollable message list
   - Message input field
   - Menu for connection and settings

2. **MessageBubble**: Individual message display
   - Color-coded by sender (blue for sent, gray for received)
   - Timestamp display
   - iMessage-style layout

3. **DeviceListView**: Device selection sheet
   - Lists discovered BLE devices
   - Shows device names and UUIDs
   - Connect button for each device

## Troubleshooting

### iOS App Issues

**Bluetooth permission denied**:
- Check Settings → Privacy → Bluetooth
- Ensure the app has permission enabled

**Can't find Raspberry Pi**:
- Ensure the server is running with `sudo`
- Check that Bluetooth is enabled on both devices
- Make sure devices are within range (~10 meters)

**Connection fails**:
- Restart the server
- Toggle Bluetooth off/on on iOS
- Check Raspberry Pi Bluetooth status: `sudo systemctl status bluetooth`

### Raspberry Pi Issues

**"BLE adapter not found"**:
```bash
sudo systemctl restart bluetooth
sudo hciconfig hci0 up
```

**Permission errors**:
- Always run the server with `sudo`
- BlueZ requires root privileges for advertising

**Messages not received**:
- Check that notifications are enabled on TX characteristic
- Verify the iOS app subscribed successfully (check console logs)

## Extending the App

### Message Relay Between Users

To relay messages between multiple iPhone users, modify `uart_peripheral.py`:

```python
class RxCharacteristic(Characteristic):
    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, UART_RX_CHARACTERISTIC_UUID,
                                ['write'], service)
        self.service = service

    def WriteValue(self, value, options):
        message = bytearray(value).decode()
        print('remote: {}'.format(message))
        # Relay to all connected clients via TX characteristic
        if hasattr(self.service, 'tx_characteristic'):
            self.service.tx_characteristic.send_tx(message + '\n')
```

### Add User Identification

Modify the message format to include sender info:
- iOS: Send `"username: message"`
- Server: Parse and relay with sender identification
- iOS: Display sender name in UI

### Encryption

For secure messaging:
- Implement encryption at the application layer
- Use AES encryption before sending messages
- Exchange keys during initial pairing

## Technical Details

### BLE Data Limits

- Maximum notification size: 20 bytes
- Messages longer than 20 bytes are automatically chunked
- iOS app handles reassembly transparently

### Connection Parameters

- Scan timeout: None (manual stop)
- Connection interval: Default (set by iOS)
- MTU: 23 bytes (20 bytes payload)

### Power Consumption

The app is designed for efficiency:
- Stops scanning when connected
- Uses notifications (not polling)
- Background mode enabled for persistent connections

## License

This project is provided as-is for educational purposes.

## Contributing

Feel free to submit issues and enhancement requests!

## Resources

- [CoreBluetooth Documentation](https://developer.apple.com/documentation/corebluetooth)
- [BlueZ Documentation](http://www.bluez.org/)
- [Nordic UART Service Specification](https://developer.nordicsemi.com/nRF_Connect_SDK/doc/latest/nrf/libraries/bluetooth_services/services/nus.html)
