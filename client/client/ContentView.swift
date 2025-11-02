//
//  ContentView.swift
//  client
//
//  Created by Jaehyung Choi on 01/11/2025.
//

import SwiftUI
import CoreBluetooth

struct ContentView: View {
    @StateObject private var bluetoothManager = BluetoothManager()
    @State private var messageText = ""
    @State private var showDeviceList = false

    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                // Status bar
                HStack {
                    Circle()
                        .fill(bluetoothManager.isConnected ? Color.green : Color.red)
                        .frame(width: 10, height: 10)

                    Text(bluetoothManager.connectionStatus)
                        .font(.caption)
                        .foregroundColor(.secondary)

                    Spacer()

                    if bluetoothManager.isScanning {
                        ProgressView()
                            .scaleEffect(0.8)
                    }
                }
                .padding()
                .background(Color(.systemGray6))

                // Messages list
                ScrollViewReader { proxy in
                    ScrollView {
                        LazyVStack(spacing: 12) {
                            ForEach(bluetoothManager.receivedMessages) { message in
                                MessageBubble(message: message)
                                    .id(message.id)
                            }
                        }
                        .padding()
                    }
                    .onChange(of: bluetoothManager.receivedMessages.count) { _ in
                        if let lastMessage = bluetoothManager.receivedMessages.last {
                            withAnimation {
                                proxy.scrollTo(lastMessage.id, anchor: .bottom)
                            }
                        }
                    }
                }

                Divider()

                // Message input
                HStack(spacing: 12) {
                    TextField("Type a message...", text: $messageText)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                        .disabled(!bluetoothManager.isConnected)

                    Button(action: sendMessage) {
                        Image(systemName: "paperplane.fill")
                            .foregroundColor(.white)
                            .frame(width: 40, height: 40)
                            .background(bluetoothManager.isConnected && !messageText.isEmpty ? Color.blue : Color.gray)
                            .clipShape(Circle())
                    }
                    .disabled(!bluetoothManager.isConnected || messageText.isEmpty)
                }
                .padding()
            }
            .navigationTitle("BLE Messenger")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Menu {
                        if bluetoothManager.isConnected {
                            Button(role: .destructive, action: {
                                bluetoothManager.disconnect()
                            }) {
                                Label("Disconnect", systemImage: "wifi.slash")
                            }
                        } else {
                            Button(action: {
                                showDeviceList = true
                                bluetoothManager.startScanning()
                            }) {
                                Label("Connect to Device", systemImage: "antenna.radiowaves.left.and.right")
                            }
                        }

                        Button(action: {
                            bluetoothManager.receivedMessages.removeAll()
                        }) {
                            Label("Clear Messages", systemImage: "trash")
                        }
                    } label: {
                        Image(systemName: "ellipsis.circle")
                    }
                }
            }
            .sheet(isPresented: $showDeviceList) {
                DeviceListView(bluetoothManager: bluetoothManager, isPresented: $showDeviceList)
            }
        }
    }

    private func sendMessage() {
        guard !messageText.isEmpty else { return }
        bluetoothManager.sendMessage(messageText)
        messageText = ""
    }
}

struct MessageBubble: View {
    let message: Message

    var body: some View {
        HStack {
            if message.isSent {
                Spacer()
            }

            VStack(alignment: message.isSent ? .trailing : .leading, spacing: 4) {
                Text(message.text)
                    .padding(12)
                    .background(message.isSent ? Color.blue : Color(.systemGray5))
                    .foregroundColor(message.isSent ? .white : .primary)
                    .cornerRadius(16)

                Text(message.timestamp, style: .time)
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }

            if !message.isSent {
                Spacer()
            }
        }
    }
}

struct DeviceListView: View {
    @ObservedObject var bluetoothManager: BluetoothManager
    @Binding var isPresented: Bool

    var body: some View {
        NavigationView {
            List {
                if bluetoothManager.discoveredDevices.isEmpty {
                    VStack(spacing: 16) {
                        Image(systemName: "antenna.radiowaves.left.and.right")
                            .font(.largeTitle)
                            .foregroundColor(.secondary)
                        Text("Scanning for devices...")
                            .foregroundColor(.secondary)
                        ProgressView()
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                } else {
                    ForEach(bluetoothManager.discoveredDevices, id: \.identifier) { device in
                        Button(action: {
                            bluetoothManager.connect(to: device)
                            isPresented = false
                        }) {
                            HStack {
                                Image(systemName: "antenna.radiowaves.left.and.right")
                                    .foregroundColor(.blue)

                                VStack(alignment: .leading) {
                                    Text(device.name ?? "Unknown Device")
                                        .font(.headline)
                                    Text(device.identifier.uuidString)
                                        .font(.caption)
                                        .foregroundColor(.secondary)
                                }

                                Spacer()

                                Image(systemName: "chevron.right")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                        .buttonStyle(PlainButtonStyle())
                    }
                }
            }
            .navigationTitle("Available Devices")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("Cancel") {
                        bluetoothManager.stopScanning()
                        isPresented = false
                    }
                }

                ToolbarItem(placement: .navigationBarTrailing) {
                    if bluetoothManager.isScanning {
                        Button("Stop") {
                            bluetoothManager.stopScanning()
                        }
                    } else {
                        Button("Scan") {
                            bluetoothManager.startScanning()
                        }
                    }
                }
            }
        }
    }
}

#Preview {
    ContentView()
}
