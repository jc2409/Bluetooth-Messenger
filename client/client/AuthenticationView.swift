//
//  AuthenticationView.swift
//  client
//
//  Gesture-based authentication view
//

import SwiftUI

struct AuthenticationView: View {
    @ObservedObject var bluetoothManager: BluetoothManager
    @State private var firstName: String = ""
    @State private var showingGesturePrompt = false

    var body: some View {
        VStack(spacing: 24) {
            // Header
            VStack(spacing: 12) {
                Image(systemName: "hand.wave.fill")
                    .font(.system(size: 60))
                    .foregroundColor(.blue)

                Text("Welcome!")
                    .font(.largeTitle)
                    .fontWeight(.bold)

                Text("Sign in with gesture authentication")
                    .font(.subheadline)
                    .foregroundColor(.secondary)
            }
            .padding(.top, 60)

            Spacer()

            // Authentication State Display
            if bluetoothManager.authState != .notStarted && bluetoothManager.authState != .waitingForResponse {
                authStateView
            } else {
                // Username input
                usernameInputView
            }

            Spacer()

            // Status message
            if !bluetoothManager.authMessage.isEmpty {
                Text(bluetoothManager.authMessage)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal)
            }
        }
        .padding()
        .onAppear {
            // Prevent screen from sleeping during authentication
            UIApplication.shared.isIdleTimerDisabled = true
        }
        .onDisappear {
            // Re-enable screen sleep when leaving authentication
            UIApplication.shared.isIdleTimerDisabled = false
        }
    }

    // MARK: - Subviews

    var usernameInputView: some View {
        VStack(spacing: 16) {
            Text("Enter your first name")
                .font(.headline)

            TextField("First name", text: $firstName)
                .textFieldStyle(RoundedBorderTextFieldStyle())
                .autocapitalization(.words)
                .disableAutocorrection(true)
                .frame(maxWidth: 300)

            Button(action: {
                guard !firstName.isEmpty else { return }
                bluetoothManager.submitUsername(firstName)
            }) {
                Text("Continue")
                    .fontWeight(.semibold)
                    .foregroundColor(.white)
                    .frame(maxWidth: 300)
                    .padding()
                    .background(firstName.isEmpty ? Color.gray : Color.blue)
                    .cornerRadius(10)
            }
            .disabled(firstName.isEmpty || bluetoothManager.authState == .waitingForResponse)
        }
    }

    var authStateView: some View {
        VStack(spacing: 24) {
            // Show different UI based on auth state
            switch bluetoothManager.authState {
            case .newUser, .existingUser:
                gesturePromptView
            case .recording:
                recordingView
            case .verifying:
                verifyingView
            case .failed:
                failedView
            default:
                EmptyView()
            }
        }
    }

    var gesturePromptView: some View {
        VStack(spacing: 20) {
            Image(systemName: "hand.raised.fill")
                .font(.system(size: 50))
                .foregroundColor(.orange)

            Text(bluetoothManager.authState == .newUser ? "Register Your Gesture" : "Verify Your Identity")
                .font(.title2)
                .fontWeight(.bold)

            if bluetoothManager.authState == .newUser {
                Text("You'll record your gesture 3 times on the Raspberry Pi")
                    .font(.body)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal)
            } else {
                Text("Perform your gesture once on the Raspberry Pi.\nIt will be compared against your 3 registered gestures.")
                    .font(.body)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal)
            }

            Button(action: {
                bluetoothManager.startGestureRecording()
            }) {
                Text("Start")
                    .fontWeight(.semibold)
                    .foregroundColor(.white)
                    .frame(maxWidth: 300)
                    .padding()
                    .background(Color.orange)
                    .cornerRadius(10)
            }
        }
    }

    var recordingView: some View {
        VStack(spacing: 20) {
            Image(systemName: "display")
                .font(.system(size: 60))
                .foregroundColor(.blue)
                .padding()

            Text("Watch Raspberry Pi")
                .font(.title2)
                .fontWeight(.bold)

            ProgressView()
                .padding()

            Text(bluetoothManager.authMessage)
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)

            VStack(spacing: 8) {
                Text("Follow the countdown and instructions")
                    .font(.caption)
                    .foregroundColor(.secondary)
                Text("on the Raspberry Pi screen")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
    }

    var verifyingView: some View {
        VStack(spacing: 20) {
            ProgressView()
                .scaleEffect(2)
                .padding()

            Text("Verifying...")
                .font(.title2)
                .fontWeight(.bold)

            Text("Comparing your gesture against registered samples")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
        }
    }

    var failedView: some View {
        VStack(spacing: 20) {
            Image(systemName: "xmark.circle.fill")
                .font(.system(size: 60))
                .foregroundColor(.red)

            Text("Authentication Failed")
                .font(.title2)
                .fontWeight(.bold)

            Text(bluetoothManager.authMessage.isEmpty ? "Your gesture did not match" : bluetoothManager.authMessage)
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)

            Button(action: {
                // Reset and try again
                bluetoothManager.authState = .existingUser
                bluetoothManager.authMessage = "Ready to try again"
            }) {
                Text("Try Again")
                    .fontWeight(.semibold)
                    .foregroundColor(.white)
                    .frame(maxWidth: 300)
                    .padding()
                    .background(Color.blue)
                    .cornerRadius(10)
            }
        }
    }
}

#Preview {
    AuthenticationView(bluetoothManager: BluetoothManager())
}
