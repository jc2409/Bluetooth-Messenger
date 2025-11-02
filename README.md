# Bluetooth Messenger

A Bluetooth Low Energy (BLE) messenger system that enables iOS devices to communicate with each other through a Raspberry Pi server using the Nordic UART Service (NUS) protocol.

## Architecture

- **Server**: Raspberry Pi running Python-based BLE GATT server with multi-client relay support
- **Client**: iOS app built with SwiftUI and CoreBluetooth
- **Authenticator**: MPU6050 sensor integration for motion-based authentication

The system uses the Nordic UART Service (NUS) for bidirectional communication:
- Service UUID: `6e400001-b5a3-f393-e0a9-e50e24dcca9e`
- TX Characteristic (Server → Client): `6e400003-b5a3-f393-e0a9-e50e24dcca9e`
- RX Characteristic (Client → Server): `6e400002-b5a3-f393-e0a9-e50e24dcca9e`

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
- Multi-client BLE GATT server using BlueZ
- Nordic UART Service implementation
- Automatic message relay between connected clients
- Console input for server broadcasts
- Client subscription tracking
- Broadcast notifications to all connected devices

### Authenticator
- MPU6050 accelerometer and gyroscope sensor integration
- Real-time sensor data reading
- Motion-based authentication capability

## Requirements

### Raspberry Pi
- Raspberry Pi 3/4/Zero W (with built-in Bluetooth)
- Raspbian/Raspberry Pi OS
- Python 3.x
- BlueZ Bluetooth stack
- Required Python packages:
  - `dbus-python`
  - `PyGObject`
- Optional (for authenticator):
  - MPU6050 sensor module
  - `mpu6050-raspberrypi` Python package

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

3. **Run the multi-client server**:
```bash
cd server
sudo python3 multi_client_server.py
```

The server will:
- Start advertising as `rpi-gatt-server`
- Wait for iOS clients to connect
- Relay messages between all connected clients
- Accept typed messages from console to broadcast
- Track and display client subscription count

4. **Optional: Setup authenticator**:
```bash
cd authenticator
sudo pip3 install mpu6050-raspberrypi
python3 read_sensor_data.py
```

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
cd server
sudo python3 multi_client_server.py
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

### Server Console Broadcasting

On the Raspberry Pi, type messages in the console and press Enter to broadcast them to all connected iOS clients.

### Multi-Client Messaging

The server automatically relays messages between all connected clients:

1. Multiple iPhones can connect to the same Raspberry Pi server simultaneously
2. When any iPhone sends a message, the server receives it
3. The server automatically broadcasts the message to all connected clients
4. The server console displays subscriber count and message activity

**Note**: Messages are currently broadcast to all clients including the sender. The BLE GATT specification doesn't provide a way to exclude specific devices from notifications.

## Project Structure

```
Bluetooth-Messenger/
├── client/                           # iOS application
│   ├── client/
│   │   ├── BluetoothManager.swift   # BLE central manager
│   │   ├── ContentView.swift        # Main UI with chat interface
│   │   ├── clientApp.swift          # App entry point
│   │   └── Assets.xcassets/         # App icons and assets
│   └── client.xcodeproj/            # Xcode project files
├── server/                           # Raspberry Pi BLE server
│   ├── multi_client_server.py       # Multi-client relay server
│   └── pi-ble-uart-server/          # BLE GATT base implementation
├── authenticator/                    # Motion-based authentication
│   ├── read_sensor_data.py          # MPU6050 sensor reader
│   └── mpu6050/                     # Sensor library directory
└── README.md
```

## Code Overview

### iOS Client

#### client/client/BluetoothManager.swift
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

#### client/client/ContentView.swift
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

### Raspberry Pi Server

#### server/multi_client_server.py
Multi-client BLE GATT server implementation:

1. **TxCharacteristic**: Handles server-to-client notifications
   - Broadcasts messages to all subscribed clients
   - Tracks subscriber count
   - Accepts console input for server broadcasts

2. **RxCharacteristic**: Handles client-to-server writes
   - Receives messages from clients
   - Automatically relays to all connected clients via TX characteristic

3. **UartService**: Nordic UART Service implementation
   - Combines TX and RX characteristics
   - Manages bidirectional communication

4. **UartApplication**: GATT application wrapper
   - Registers services with BlueZ

5. **UartAdvertisement**: BLE advertisement
   - Advertises UART service UUID
   - Sets local name to `rpi-gatt-server`

### Authenticator

#### authenticator/read_sensor_data.py
MPU6050 sensor data reader:
- Reads accelerometer data (X, Y, Z axes)
- Reads gyroscope data (X, Y, Z axes)
- Continuous polling loop for real-time data
- Designed for motion-based authentication patterns

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

### Filter Message Echo

Currently, messages are broadcast to all clients including the sender. To prevent echo:
- Add client identification in the message protocol
- Track sender information in `RxCharacteristic.WriteValue()`
- Skip notification for the sending client in `TxCharacteristic.send_tx()`

Note: This requires modifications to both iOS and server code to include client identifiers.

### Add User Identification

Enhance the message format to include sender info:
1. **iOS** (`client/client/BluetoothManager.swift`):
   - Add username configuration
   - Prefix messages with `"username: message"` format
2. **Server** (`server/multi_client_server.py`):
   - Parse sender identification from message
   - Relay with sender info intact
3. **iOS** (`client/client/ContentView.swift`):
   - Parse and display sender name in message bubbles
   - Distinguish between different senders with colors

### Encryption

For secure messaging:
- Implement end-to-end encryption at the application layer
- Use AES-256 encryption before sending messages via BLE
- Implement secure key exchange during initial pairing
- Store encryption keys in iOS Keychain

### Integrate Authenticator

Connect motion-based authentication to the messaging system:
1. Read MPU6050 sensor data on Raspberry Pi
2. Define authentication gesture patterns
3. Validate user gestures before allowing message relay
4. Send authentication status to iOS clients

## Technical Details

### BLE Data Limits

- Maximum notification size: 20 bytes (BLE GATT limitation)
- Messages longer than 20 bytes are automatically chunked by iOS client
- iOS app handles reassembly transparently
- Server broadcasts complete messages to all clients

### Connection Parameters

- Scan timeout: None (manual stop)
- Connection interval: Default (determined by iOS)
- MTU: 23 bytes (20 bytes payload + 3 bytes overhead)
- Multiple simultaneous client connections supported

### Multi-Client Architecture

- Each BLE GATT characteristic is shared across all connected clients
- Notifications are automatically broadcast to all subscribed devices
- Server tracks subscriber count via `StartNotify()` callbacks
- Message relay happens at the application layer in `RxCharacteristic`

### Power Consumption

The app is designed for efficiency:
- Stops scanning when connected
- Uses notifications (not polling) for incoming messages
- Background mode enabled for persistent connections
- Server runs continuously with low idle power consumption

## License

This project is provided as-is for educational purposes.

## Contributing

Feel free to submit issues and enhancement requests!

## Resources

- [CoreBluetooth Documentation](https://developer.apple.com/documentation/corebluetooth)
- [BlueZ Documentation](http://www.bluez.org/)
- [Nordic UART Service Specification](https://developer.nordicsemi.com/nRF_Connect_SDK/doc/latest/nrf/libraries/bluetooth_services/services/nus.html)
