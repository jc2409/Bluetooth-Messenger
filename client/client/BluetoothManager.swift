//
//  BluetoothManager.swift
//  client
//
//  Bluetooth Low Energy manager for communicating with Raspberry Pi server
//

import Foundation
import CoreBluetooth
import Combine

class BluetoothManager: NSObject, ObservableObject {
    // UART Service UUIDs (Nordic UART Service compatible with Raspberry Pi)
    private let uartServiceUUID = CBUUID(string: "6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
    private let rxCharacteristicUUID = CBUUID(string: "6E400002-B5A3-F393-E0A9-E50E24DCCA9E")
    private let txCharacteristicUUID = CBUUID(string: "6E400003-B5A3-F393-E0A9-E50E24DCCA9E")

    // Core Bluetooth objects
    private var centralManager: CBCentralManager!
    private var connectedPeripheral: CBPeripheral?
    private var txCharacteristic: CBCharacteristic?
    private var rxCharacteristic: CBCharacteristic?

    // Published properties for UI updates
    @Published var isScanning = false
    @Published var isConnected = false
    @Published var discoveredDevices: [CBPeripheral] = []
    @Published var receivedMessages: [Message] = []
    @Published var connectionStatus = "Disconnected"

    // Authentication state
    @Published var isAuthenticated = false
    @Published var authState: AuthState = .notStarted
    @Published var username: String = ""
    @Published var countdownSeconds: Int = 0
    @Published var currentAttempt: Int = 0
    @Published var attemptsPassed: Int = 0
    @Published var authMessage: String = ""

    // Track recently sent messages to detect echoes
    private var recentlySentMessages: [(text: String, timestamp: Date)] = []
    private let echoTimeWindow: TimeInterval = 2.0  // 2 seconds

    // Connection monitoring
    private var connectionMonitorTimer: Timer?

    // Buffer for incoming message fragments
    private var messageBuffer: String = ""

    override init() {
        super.init()
        print("BluetoothManager: Initializing CBCentralManager")
        centralManager = CBCentralManager(delegate: self, queue: nil)
    }

    // MARK: - Public Methods

    func startScanning() {
        print("BluetoothManager: startScanning() called")
        print("BluetoothManager: Central state = \(centralManager.state.rawValue)")

        guard centralManager.state == .poweredOn else {
            print("BluetoothManager: Cannot scan - Bluetooth not powered on")
            connectionStatus = "Bluetooth not available"
            return
        }

        print("BluetoothManager: Clearing discovered devices and starting scan")
        discoveredDevices.removeAll()
        isScanning = true
        connectionStatus = "Scanning for devices..."

        print("BluetoothManager: Scanning for all BLE devices (no service filter)")
        print("BluetoothManager: Looking for UART service: \(uartServiceUUID)")

        // Scan for ALL devices (nil = no service filter)
        // This is more reliable as some devices don't advertise service UUIDs properly
        centralManager.scanForPeripherals(
            withServices: nil,
            options: [CBCentralManagerScanOptionAllowDuplicatesKey: false]
        )

        print("BluetoothManager: Scan started successfully")
    }

    func stopScanning() {
        centralManager.stopScan()
        isScanning = false
        if !isConnected {
            connectionStatus = "Scan stopped"
        }
    }

    func connect(to peripheral: CBPeripheral) {
        stopScanning()
        connectionStatus = "Connecting to \(peripheral.name ?? "device")..."
        centralManager.connect(peripheral, options: nil)
    }

    func disconnect() {
        print("🔌 Disconnecting...")
        stopConnectionMonitor()
        if let peripheral = connectedPeripheral {
            centralManager.cancelPeripheralConnection(peripheral)
        }
    }

    // MARK: - Connection Monitoring

    private func startConnectionMonitor() {
        stopConnectionMonitor()
        print("👁️ Starting connection monitor")
        connectionMonitorTimer = Timer.scheduledTimer(withTimeInterval: 5.0, repeats: true) { [weak self] _ in
            self?.checkConnectionState()
        }
    }

    private func stopConnectionMonitor() {
        connectionMonitorTimer?.invalidate()
        connectionMonitorTimer = nil
        print("👁️ Stopped connection monitor")
    }

    private func checkConnectionState() {
        guard let peripheral = connectedPeripheral else {
            print("⚠️ Connection monitor: No peripheral")
            return
        }

        let state = peripheral.state
        print("👁️ Connection state: \(state.rawValue) | isConnected: \(isConnected) | isAuth: \(isAuthenticated)")

        if state != .connected && isConnected {
            print("⚠️ Connection state mismatch! Peripheral state: \(state.rawValue), but isConnected=true")
            DispatchQueue.main.async {
                self.isConnected = false
                self.connectionStatus = "Connection lost"
            }
        }
    }

    func sendMessage(_ message: String) {
        guard isAuthenticated else {
            print("Cannot send message: not authenticated")
            return
        }

        // Format: MSG:username:message
        let formattedMessage = "MSG:\(username):\(message)"
        sendRawMessage(formattedMessage)

        // Add to local messages
        let newMessage = Message(text: message, isSent: true, timestamp: Date())
        DispatchQueue.main.async {
            self.receivedMessages.append(newMessage)
        }
    }

    // MARK: - Authentication Methods

    func submitUsername(_ name: String) {
        username = name
        authState = .waitingForResponse
        sendRawMessage("USERNAME:\(name)")
        print("Submitted username: \(name)")
    }

    func startGestureRecording() {
        sendRawMessage("READY_FOR_GESTURE:\(username)")
        print("Requested gesture recording")
    }

    private func sendRawMessage(_ message: String) {
        guard let peripheral = connectedPeripheral,
              let characteristic = rxCharacteristic else {
            print("❌ Cannot send message: not ready (peripheral: \(connectedPeripheral != nil), characteristic: \(rxCharacteristic != nil))")
            return
        }

        // Check if peripheral is still connected
        guard peripheral.state == .connected else {
            print("❌ Cannot send message: peripheral state is \(peripheral.state.rawValue)")
            return
        }

        // Add newline to mark end of message
        let messageWithNewline = message + "\n"
        guard let data = messageWithNewline.data(using: .utf8) else {
            print("❌ Cannot encode message")
            return
        }

        print("📤 Sending: \(message)")

        // BLE has a 20-byte limit for notifications, so we may need to split
        let maxLength = 20
        var offset = 0

        while offset < data.count {
            let chunkSize = min(maxLength, data.count - offset)
            let chunk = data.subdata(in: offset..<offset + chunkSize)
            peripheral.writeValue(chunk, for: characteristic, type: .withResponse)
            offset += chunkSize
        }

        print("Sent: \(message)")
    }

    private func handleAuthenticationMessage(_ message: String) {
        print("Auth message: \(message)")

        if message.starts(with: "AUTH_REQUIRED") {
            // Ignore AUTH_REQUIRED if already authenticated (prevents re-authentication on reconnect)
            guard !isAuthenticated else {
                print("Ignoring AUTH_REQUIRED - already authenticated")
                return
            }
            DispatchQueue.main.async {
                self.authState = .notStarted
                self.authMessage = "Please sign in with your first name"
            }
        } else if message.starts(with: "NEW_USER:") {
            let text = message.replacingOccurrences(of: "NEW_USER:", with: "")
            DispatchQueue.main.async {
                self.authState = .newUser
                self.authMessage = text
                self.currentAttempt = 0
                self.attemptsPassed = 0
            }
        } else if message.starts(with: "EXISTING_USER:") {
            let text = message.replacingOccurrences(of: "EXISTING_USER:", with: "")
            DispatchQueue.main.async {
                self.authState = .existingUser
                self.authMessage = text
                self.currentAttempt = 0
                self.attemptsPassed = 0
            }
        } else if message.starts(with: "RECORDING_START:") {
            let text = message.replacingOccurrences(of: "RECORDING_START:", with: "")
            DispatchQueue.main.async {
                self.authState = .recording
                self.authMessage = text
            }
        } else if message.starts(with: "ATTEMPT_RESULT:") {
            // Format: ATTEMPT_RESULT:1:success:1/3
            let parts = message.components(separatedBy: ":")
            if parts.count >= 4 {
                let attemptNum = Int(parts[1]) ?? 0  // Attempt number
                let result = parts[2] // "success" or "failed"
                let score = parts[3]  // "1/3"
                let scoreParts = score.components(separatedBy: "/")
                if scoreParts.count == 2, let passed = Int(scoreParts[0]) {
                    DispatchQueue.main.async {
                        self.authState = .verifying
                        self.currentAttempt = attemptNum  // Update current attempt!
                        self.attemptsPassed = passed
                        self.authMessage = "Attempt \(result == "success" ? "passed" : "failed")! (\(score))"
                    }
                }
            }
        } else if message.starts(with: "AUTH_SUCCESS:") {
            let name = message.replacingOccurrences(of: "AUTH_SUCCESS:", with: "")
            DispatchQueue.main.async {
                self.authState = .authenticated
                self.isAuthenticated = true
                self.authMessage = "Welcome \(name)!"
                self.connectionStatus = "Authenticated as \(name)"
            }
        } else if message.starts(with: "AUTH_FAILED:") {
            let reason = message.replacingOccurrences(of: "AUTH_FAILED:", with: "")
            DispatchQueue.main.async {
                self.authState = .failed
                self.isAuthenticated = false
                self.authMessage = reason
            }
        } else if message.starts(with: "ERROR:") {
            let error = message.replacingOccurrences(of: "ERROR:", with: "")
            DispatchQueue.main.async {
                self.authMessage = "Error: \(error)"
            }
        }
    }

    private func handleChatMessage(_ message: String) {
        // Format: MSG:username:text
        let parts = message.components(separatedBy: ":")
        if parts.count >= 3, parts[0] == "MSG" {
            let senderName = parts[1]
            let text = parts[2...].joined(separator: ":")

            // Don't show messages from ourselves
            if senderName != username {
                let newMessage = Message(text: "\(senderName): \(text)", isSent: false, timestamp: Date())
                DispatchQueue.main.async {
                    self.receivedMessages.append(newMessage)
                }
            }
        }
    }
}

// MARK: - CBCentralManagerDelegate

extension BluetoothManager: CBCentralManagerDelegate {
    func centralManagerDidUpdateState(_ central: CBCentralManager) {
        print("BluetoothManager: State changed to \(central.state.rawValue)")

        switch central.state {
        case .poweredOn:
            print("BluetoothManager: Bluetooth is powered on and ready")
            connectionStatus = "Bluetooth ready"
        case .poweredOff:
            print("BluetoothManager: Bluetooth is powered off")
            connectionStatus = "Bluetooth is off"
        case .unauthorized:
            print("BluetoothManager: Bluetooth is not authorized")
            if #available(iOS 13.1, *) {
                switch CBCentralManager.authorization {
                case .allowedAlways:
                    print("Authorization: allowedAlways")
                case .denied:
                    print("Authorization: DENIED - Check Settings")
                case .restricted:
                    print("Authorization: RESTRICTED")
                case .notDetermined:
                    print("Authorization: NOT DETERMINED")
                @unknown default:
                    print("Authorization: Unknown")
                }
            }
            connectionStatus = "Bluetooth not authorized"
        case .unsupported:
            print("BluetoothManager: Bluetooth is not supported on this device")
            connectionStatus = "Bluetooth not supported"
        case .resetting:
            print("BluetoothManager: Bluetooth is resetting")
            connectionStatus = "Bluetooth resetting"
        case .unknown:
            print("BluetoothManager: Bluetooth state is unknown")
            connectionStatus = "Bluetooth state unknown"
        @unknown default:
            print("BluetoothManager: Unknown Bluetooth state")
            connectionStatus = "Bluetooth unavailable"
        }
    }

    func centralManager(_ central: CBCentralManager, didDiscover peripheral: CBPeripheral,
                       advertisementData: [String: Any], rssi RSSI: NSNumber) {
        print("Discovered: \(peripheral.name ?? "Unknown") - \(peripheral.identifier)")
        print("Advertisement data: \(advertisementData)")
        print("RSSI: \(RSSI)")

        // Filter: Only show known devices with expected names
        let knownDeviceNames = ["raspberrypi", "rpi-gatt-server"]
        guard let deviceName = peripheral.name, knownDeviceNames.contains(deviceName) else {
            print("Skipping unknown device: \(peripheral.name ?? "nil")")
            return
        }

        // Add discovered peripheral if not already in list
        if !discoveredDevices.contains(where: { $0.identifier == peripheral.identifier }) {
            DispatchQueue.main.async {
                self.discoveredDevices.append(peripheral)
            }
        }
    }

    func centralManager(_ central: CBCentralManager, didConnect peripheral: CBPeripheral) {
        print("✅ CONNECTED to \(peripheral.name ?? "device")")
        connectionStatus = "Connected to \(peripheral.name ?? "device")"
        isConnected = true
        connectedPeripheral = peripheral
        peripheral.delegate = self
        peripheral.discoverServices([uartServiceUUID])

        // Start monitoring connection state
        startConnectionMonitor()
    }

    func centralManager(_ central: CBCentralManager, didDisconnectPeripheral peripheral: CBPeripheral, error: Error?) {
        print("⚠️ DISCONNECTED from \(peripheral.name ?? "device")")
        if let error = error {
            print("Disconnect error: \(error.localizedDescription)")
        }

        // Stop monitoring
        stopConnectionMonitor()
        connectionStatus = "Disconnected"
        isConnected = false
        isAuthenticated = false  // Reset authentication on disconnect
        authState = .notStarted
        connectedPeripheral = nil
        txCharacteristic = nil
        rxCharacteristic = nil
    }

    func centralManager(_ central: CBCentralManager, didFailToConnect peripheral: CBPeripheral, error: Error?) {
        connectionStatus = "Failed to connect: \(error?.localizedDescription ?? "Unknown error")"
        isConnected = false
    }
}

// MARK: - CBPeripheralDelegate

extension BluetoothManager: CBPeripheralDelegate {
    func peripheral(_ peripheral: CBPeripheral, didDiscoverServices error: Error?) {
        guard let services = peripheral.services else { return }

        for service in services {
            if service.uuid == uartServiceUUID {
                peripheral.discoverCharacteristics([txCharacteristicUUID, rxCharacteristicUUID], for: service)
            }
        }
    }

    func peripheral(_ peripheral: CBPeripheral, didDiscoverCharacteristicsFor service: CBService, error: Error?) {
        print("📍 didDiscoverCharacteristicsFor called")
        if let error = error {
            print("❌ Error discovering characteristics: \(error.localizedDescription)")
            return
        }

        guard let characteristics = service.characteristics else {
            print("❌ No characteristics found")
            return
        }

        for characteristic in characteristics {
            if characteristic.uuid == txCharacteristicUUID {
                // TX characteristic (receive from server)
                txCharacteristic = characteristic
                peripheral.setNotifyValue(true, for: characteristic)
                print("✅ Subscribed to TX characteristic (notifications enabled)")
            } else if characteristic.uuid == rxCharacteristicUUID {
                // RX characteristic (send to server)
                rxCharacteristic = characteristic
                print("✅ Found RX characteristic (ready to send)")
            }
        }

        if txCharacteristic != nil && rxCharacteristic != nil {
            connectionStatus = "Ready to chat!"
        }
    }

    func peripheral(_ peripheral: CBPeripheral, didUpdateValueFor characteristic: CBCharacteristic, error: Error?) {
        if let error = error {
            print("❌ Error receiving data: \(error.localizedDescription)")
            return
        }

        guard let data = characteristic.value,
              let fragment = String(data: data, encoding: .utf8) else {
            print("⚠️ Received data but cannot decode")
            return
        }

        print("📥 Received fragment: '\(fragment.trimmingCharacters(in: .whitespacesAndNewlines))'")

        // Append to buffer (messages may come in fragments)
        messageBuffer += fragment

        // Process complete messages (ending with newline)
        if messageBuffer.contains("\n") {
            let messages = messageBuffer.components(separatedBy: "\n")
            messageBuffer = messages.last ?? "" // Keep incomplete fragment

            for message in messages.dropLast() {
                let trimmedMessage = message.trimmingCharacters(in: .whitespaces)
                guard !trimmedMessage.isEmpty else { continue }

                print("📨 Received complete message: \(trimmedMessage)")

                // Route message based on prefix
                if trimmedMessage.starts(with: "MSG:") {
                    handleChatMessage(trimmedMessage)
                } else {
                    handleAuthenticationMessage(trimmedMessage)
                }
            }
        }
    }

    func peripheral(_ peripheral: CBPeripheral, didUpdateNotificationStateFor characteristic: CBCharacteristic, error: Error?) {
        if let error = error {
            print("❌ Error updating notification state: \(error.localizedDescription)")
            return
        }

        if characteristic.isNotifying {
            print("✅ Notifications ENABLED for \(characteristic.uuid)")
        } else {
            print("⚠️ Notifications DISABLED for \(characteristic.uuid) - This may cause disconnection!")
        }
    }

    func peripheral(_ peripheral: CBPeripheral, didWriteValueFor characteristic: CBCharacteristic, error: Error?) {
        if let error = error {
            print("❌ Write failed: \(error.localizedDescription)")
        } else {
            print("✅ Write confirmed for \(characteristic.uuid)")
        }
    }
}

// MARK: - Message Model

struct Message: Identifiable {
    let id = UUID()
    let text: String
    let isSent: Bool
    let timestamp: Date
}

// MARK: - Authentication State

enum AuthState {
    case notStarted
    case waitingForResponse
    case newUser
    case existingUser
    case countdown
    case recording
    case verifying
    case authenticated
    case failed
}
