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

            Text(bluetoothManager.authState == .newUser ? "Register Your Gesture" : "Perform Your Gesture")
                .font(.title2)
                .fontWeight(.bold)

            Text("You'll perform your gesture on the Raspberry Pi device")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)

            Text("Attempts: \(bluetoothManager.currentAttempt)/3")
                .font(.caption)
                .foregroundColor(.secondary)

            if bluetoothManager.attemptsPassed > 0 {
                Text("Passed: \(bluetoothManager.attemptsPassed)/3")
                    .font(.caption)
                    .foregroundColor(.green)
                    .fontWeight(.semibold)
            }

            Button(action: {
                bluetoothManager.startGestureRecording()
            }) {
                Text(bluetoothManager.currentAttempt == 0 ? "Start" : "Try Again")
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
            ProgressView()
                .scaleEffect(2)
                .padding()

            Text("Recording...")
                .font(.title2)
                .fontWeight(.bold)

            Text(bluetoothManager.authMessage)
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)

            Text("Follow the prompts on the Raspberry Pi")
                .font(.caption)
                .foregroundColor(.secondary)
        }
    }

    var verifyingView: some View {
        VStack(spacing: 20) {
            Image(systemName: bluetoothManager.attemptsPassed >= 2 ? "checkmark.circle.fill" : "")
                .font(.system(size: 60))
                .foregroundColor(bluetoothManager.attemptsPassed >= 2 ? .green : .orange)

            Text("Verifying...")
                .font(.title2)
                .fontWeight(.bold)

            Text("Passed: \(bluetoothManager.attemptsPassed)/3")
                .font(.headline)
                .foregroundColor(bluetoothManager.attemptsPassed >= 2 ? .green : .orange)

            if bluetoothManager.currentAttempt < 3 && bluetoothManager.attemptsPassed < 2 {
                Button(action: {
                    bluetoothManager.startGestureRecording()
                }) {
                    Text("Next Attempt")
                        .fontWeight(.semibold)
                        .foregroundColor(.white)
                        .frame(maxWidth: 300)
                        .padding()
                        .background(Color.orange)
                        .cornerRadius(10)
                }
                .padding(.top)
            }
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

            Text("Only \(bluetoothManager.attemptsPassed)/3 attempts passed")
                .font(.body)
                .foregroundColor(.secondary)

            Button(action: {
                // Reset and try again
                firstName = ""
                bluetoothManager.authState = .notStarted
                bluetoothManager.authMessage = ""
                bluetoothManager.currentAttempt = 0
                bluetoothManager.attemptsPassed = 0
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
