# Gesture-Based Authentication System

## Overview

The Bluetooth Messenger now includes gesture-based authentication using the MPU6050 sensor connected to the Raspberry Pi. Users must authenticate before they can access the chat service.

## Architecture

```
iOS Client ←→ BLE UART ←→ Raspberry Pi Server ←→ MPU6050 Sensor
                                ↓
                         Gesture Recognizer
                                ↓
                         User Database
```

## Authentication Flow

### New User Registration

1. User enters their first name in iOS app
2. iOS sends `USERNAME:name` to server
3. Server checks database → User doesn't exist
4. Server responds `NEW_USER:message`
5. iOS shows "Register Your Gesture" screen
6. User taps "Start" button
7. iOS sends `READY_FOR_GESTURE:name`
8. Server sends countdown: `COUNTDOWN:3`, `COUNTDOWN:2`, `COUNTDOWN:1`
9. iOS displays countdown animation
10. Server sends `RECORDING:1` and starts MPU6050 recording (4 seconds)
11. User performs gesture on Raspberry Pi
12. Server processes gesture and creates template
13. Server responds `AUTH_SUCCESS:name`
14. iOS transitions to chat interface

### Existing User Login

1. User enters their first name in iOS app
2. iOS sends `USERNAME:name` to server
3. Server checks database → User exists
4. Server responds `EXISTING_USER:message`
5. iOS shows "Perform Your Gesture" screen
6. User taps "Start" button
7. iOS sends `READY_FOR_GESTURE:name`
8. Server performs countdown and recording (same as above)
9. **Server verifies gesture against stored template**
10. Server sends `ATTEMPT_RESULT:1:success/failed:X/3`
11. **Repeat steps 7-10 for up to 3 attempts**
12. If 2 or more attempts pass:
    - Server sends `AUTH_SUCCESS:name`
    - iOS transitions to chat
13. If less than 2 attempts pass:
    - Server sends `AUTH_FAILED:Only X/3 attempts passed`
    - iOS shows failure screen with retry option

## Protocol Messages

### Client → Server

- `USERNAME:name` - Submit first name for authentication
- `READY_FOR_GESTURE:name` - Ready to perform gesture
- `MSG:username:message` - Send chat message (only after authenticated)

### Server → Client

- `AUTH_REQUIRED` - Authentication needed (sent on connection)
- `NEW_USER:message` - Username not found, prepare for registration
- `EXISTING_USER:message` - Username found, prepare for verification
- `COUNTDOWN:3/2/1` - Countdown before recording starts
- `RECORDING:attempt_number` - Recording in progress
- `ATTEMPT_RESULT:attempt:success/failed:passed/total` - Result of attempt
- `AUTH_SUCCESS:username` - Authentication successful
- `AUTH_FAILED:reason` - Authentication failed
- `ERROR:message` - Error occurred
- `MSG:username:message` - Chat message from authenticated user

## Testing the System

### Prerequisites

1. **Raspberry Pi Setup:**
   ```bash
   cd server
   sudo python3 auth_server.py
   ```

2. **iOS App:**
   - Open `client/client.xcodeproj` in Xcode
   - Build and run on physical iPhone
   - (Bluetooth doesn't work in simulator)

### Test Case 1: New User Registration

1. Launch iOS app
2. Tap "Connect" and select `rpi-gatt-server`
3. Enter first name (e.g., "Alice")
4. Tap "Continue"
5. Should see "Register Your Gesture" screen
6. Tap "Start"
7. Should see countdown: 3, 2, 1
8. Should see "Recording gesture..." for 4 seconds
9. Should see "Authentication successful!"
10. Should transition to chat interface

**Server Console Output:**
```
✓ Client subscribed (total: 1)
→ Broadcasting: AUTH_REQUIRED
← Received: USERNAME:Alice
New user registration: Alice
→ Broadcasting: NEW_USER:Welcome Alice! Please perform your gesture...
← Received: READY_FOR_GESTURE:Alice
--- Attempt 1/3 for Alice ---
Recording gesture for 4.0 seconds...
Recording complete. Captured ~200 samples.
Registered gesture for Alice
→ Broadcasting: ATTEMPT_RESULT:1:success:1/1
→ Broadcasting: AUTH_SUCCESS:Alice
```

### Test Case 2: Existing User Login (Success)

1. Launch iOS app and connect
2. Enter "Alice" (existing user)
3. Tap "Continue"
4. Should see "Perform Your Gesture" screen
5. Perform 3 gesture attempts
6. If 2+ pass, should authenticate successfully

**Expected Server Output:**
```
Existing user login: Alice
--- Attempt 1/3 for Alice ---
Verify Alice: PASS (0.75)
Attempt 1: PASS (confidence: 0.75) - Total: 1/1
--- Attempt 2/3 for Alice ---
Verify Alice: PASS (0.82)
Attempt 2: PASS (confidence: 0.82) - Total: 2/2
→ Broadcasting: AUTH_SUCCESS:Alice
```

### Test Case 3: Failed Authentication

1. Launch iOS app and connect
2. Enter existing username
3. Perform 3 gesture attempts
4. If less than 2 pass (in dummy mode, this is random):
   - Should see "Authentication Failed" screen
   - Should show "Only X/3 attempts passed"
   - Should have "Try Again" button

### Test Case 4: Chat After Authentication

1. Authenticate successfully (either registration or login)
2. Should see chat interface with title "Chat - YourName"
3. Type a message and send
4. On server console:
   ```
   ← Received: MSG:Alice:Hello!
   💬 Alice: Hello!
   → Broadcasting: MSG:Alice:Hello!
   ```
5. Connect second iPhone and authenticate as different user
6. Both users should see each other's messages with sender names

## File Structure

```
server/
├── auth_server.py              # Main authenticated server
├── auth_manager.py             # Authentication state machine
├── user_database.py            # User data storage
├── multi_client_server.py      # Original server (no auth)
└── users.json                  # User database (created automatically)

authenticator/
├── gesture_recognizer.py       # Gesture recognition interface (dummy)
└── read_sensor_data.py         # MPU6050 data reader

client/client/
├── BluetoothManager.swift      # BLE + Auth protocol handler
├── AuthenticationView.swift    # Authentication UI
├── ContentView.swift           # Main app with auth check
└── clientApp.swift             # App entry point
```

## User Database Format

`server/users.json`:
```json
{
  "alice": {
    "username": "Alice",
    "gesture_template": [0.1, 0.2, 0.3, ...],
    "created_at": "2025-11-02T12:00:00",
    "last_login": "2025-11-02T13:30:00"
  },
  "bob": {
    "username": "Bob",
    "gesture_template": [0.5, 0.6, 0.7, ...],
    "created_at": "2025-11-02T12:15:00",
    "last_login": "2025-11-02T14:00:00"
  }
}
```

## Current Limitations

1. **Dummy Gesture Recognition:** The `gesture_recognizer.py` currently uses random success/failure for testing. Replace with actual ML/signal processing implementation.

2. **Username as Device ID:** Since BLE GATT doesn't provide device identification, we use username as the session identifier. This means:
   - Two users with same name cannot connect simultaneously
   - If connection drops, user must re-authenticate

3. **No Session Persistence:** Authentication state is lost on disconnect. Future enhancement could add token-based session resumption.

4. **Message Echo:** All authenticated users receive all messages, including their own. The iOS app filters out messages from self.

## Next Steps

1. **Implement Real Gesture Recognition:**
   - Replace `authenticator/gesture_recognizer.py` with actual implementation
   - Use DTW (Dynamic Time Warping) or ML models
   - Tune threshold for acceptance

2. **Integrate MPU6050:**
   - Ensure MPU6050 is connected to Raspberry Pi
   - Test `authenticator/read_sensor_data.py`
   - Feed real sensor data to gesture recognizer

3. **Enhance Security:**
   - Add gesture template encryption
   - Implement rate limiting (prevent brute force)
   - Add session tokens

4. **Improve UX:**
   - Add haptic feedback on iOS during recording
   - Show gesture quality feedback
   - Add tutorial for first-time users

## Troubleshooting

### iOS App Issues

**"Please sign in with your first name" stuck:**
- Check server console for AUTH_REQUIRED message
- Ensure server is running with `sudo python3 auth_server.py`
- Try disconnecting and reconnecting

**Countdown not appearing:**
- Check server console for COUNTDOWN messages
- Verify iOS received READY_FOR_GESTURE confirmation
- Check Bluetooth connection strength

**Authentication always fails:**
- This is expected with dummy recognizer (random)
- Check `gesture_recognizer.py` verify_gesture() method
- Adjust success probability for testing

### Server Issues

**ImportError: No module named 'auth_manager':**
```bash
cd server
python3 -c "import auth_manager"  # Test import
```

**"BLE adapter not found":**
```bash
sudo systemctl restart bluetooth
sudo hciconfig hci0 up
```

**User database not saving:**
- Check write permissions in server directory
- Look for `users.json` file creation
- Check server console for error messages

## Testing Checklist

- [ ] New user can register with gesture
- [ ] Existing user can login with 2/3 attempts passing
- [ ] Authentication fails with < 2/3 attempts
- [ ] Countdown displays correctly (3, 2, 1)
- [ ] Recording shows for 4 seconds
- [ ] Attempt counter shows correctly (X/3)
- [ ] Chat only accessible after authentication
- [ ] Messages display sender name
- [ ] Multiple users can authenticate simultaneously
- [ ] Disconnect resets authentication state
- [ ] User database persists across server restarts

## Questions or Issues?

If you encounter problems:
1. Check server console output for errors
2. Check iOS console in Xcode for debug messages
3. Verify BLE connection is stable
4. Ensure authentication state machine is in correct state
5. Test with dummy recognizer before adding real gesture recognition
