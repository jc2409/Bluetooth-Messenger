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
        if let peripheral = connectedPeripheral {
            centralManager.cancelPeripheralConnection(peripheral)
        }
    }

    func sendMessage(_ message: String) {
        guard let peripheral = connectedPeripheral,
              let characteristic = rxCharacteristic,
              let data = message.data(using: .utf8) else {
            return
        }

        // BLE has a 20-byte limit for notifications, so we may need to split
        let maxLength = 20
        var offset = 0

        while offset < data.count {
            let chunkSize = min(maxLength, data.count - offset)
            let chunk = data.subdata(in: offset..<offset + chunkSize)
            peripheral.writeValue(chunk, for: characteristic, type: .withResponse)
            offset += chunkSize
        }

        // Add to local messages
        let newMessage = Message(text: message, isSent: true, timestamp: Date())
        DispatchQueue.main.async {
            self.receivedMessages.append(newMessage)
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

        // Add discovered peripheral if not already in list
        if !discoveredDevices.contains(where: { $0.identifier == peripheral.identifier }) {
            DispatchQueue.main.async {
                self.discoveredDevices.append(peripheral)
            }
        }
    }

    func centralManager(_ central: CBCentralManager, didConnect peripheral: CBPeripheral) {
        connectionStatus = "Connected to \(peripheral.name ?? "device")"
        isConnected = true
        connectedPeripheral = peripheral
        peripheral.delegate = self
        peripheral.discoverServices([uartServiceUUID])
    }

    func centralManager(_ central: CBCentralManager, didDisconnectPeripheral peripheral: CBPeripheral, error: Error?) {
        connectionStatus = "Disconnected"
        isConnected = false
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
        guard let characteristics = service.characteristics else { return }

        for characteristic in characteristics {
            if characteristic.uuid == txCharacteristicUUID {
                // TX characteristic (receive from server)
                txCharacteristic = characteristic
                peripheral.setNotifyValue(true, for: characteristic)
                print("Subscribed to TX characteristic")
            } else if characteristic.uuid == rxCharacteristicUUID {
                // RX characteristic (send to server)
                rxCharacteristic = characteristic
                print("Found RX characteristic")
            }
        }

        if txCharacteristic != nil && rxCharacteristic != nil {
            connectionStatus = "Ready to chat!"
        }
    }

    func peripheral(_ peripheral: CBPeripheral, didUpdateValueFor characteristic: CBCharacteristic, error: Error?) {
        guard let data = characteristic.value,
              let message = String(data: data, encoding: .utf8) else {
            return
        }

        // Received message from server
        let newMessage = Message(text: message, isSent: false, timestamp: Date())
        DispatchQueue.main.async {
            self.receivedMessages.append(newMessage)
        }
    }

    func peripheral(_ peripheral: CBPeripheral, didUpdateNotificationStateFor characteristic: CBCharacteristic, error: Error?) {
        if let error = error {
            print("Error updating notification state: \(error.localizedDescription)")
            return
        }

        if characteristic.isNotifying {
            print("Notifications enabled for \(characteristic.uuid)")
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
