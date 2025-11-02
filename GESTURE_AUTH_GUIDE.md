# Real Gesture Authentication System Guide

## Overview

The authentication system now uses **real MPU6050 sensor data** with **DTW (Dynamic Time Warping)** algorithm for gesture recognition.

## Updated Architecture

```
iOS App → BLE → Raspberry Pi Server → Auth Manager → Gesture Recognizer
                                                            ↓
                                                    generate_gesture.py
                                                    authenticate_gesture.py
                                                            ↓
                                                    MPU6050 Sensor
                                                    DTW Algorithm
```

## Key Changes from Previous Version

### 1. **Registration Flow (New Users)**
**OLD:** Single dummy gesture
**NEW:** 3 real gesture samples with MPU6050

- User enters first name on iOS
- iOS shows "Register Your Gesture" screen
- User taps "Start" once
- **Raspberry Pi automatically collects 3 gesture samples:**
  - Sample 1: Countdown (3,2,1) → Record 4 seconds
  - Sample 2: Countdown (3,2,1) → Record 4 seconds
  - Sample 3: Countdown (3,2,1) → Record 4 seconds
- Each sample is 160 data points (X, Y coordinates)
- All 3 samples saved to database
- User authenticated immediately

### 2. **Verification Flow (Existing Users)**
**OLD:** 3 random attempts
**NEW:** 3 real gesture attempts with DTW comparison

- User enters first name on iOS
- iOS shows "Perform Your Gesture" screen
- User gets 3 attempts (needs 2 to pass):
  - **Each attempt:**
    - User taps button on iOS
    - Countdown on Raspberry Pi (3,2,1)
    - Record 4 seconds from MPU6050
    - Compare using DTW against all 3 saved samples
    - Majority voting (>50% match) = attempt passes
  - **Need 2/3 attempts to authenticate**

### 3. **Data Storage**
**Format:** `server/users.json`
```json
{
  "alice": {
    "username": "Alice",
    "gesture_list": [
      [[x1, y1], [x2, y2], ..., [x160, y160]],  // Sample 1
      [[x1, y1], [x2, y2], ..., [x160, y160]],  // Sample 2
      [[x1, y1], [x2, y2], ..., [x160, y160]]   // Sample 3
    ],
    "num_gestures": 3,
    "created_at": "2025-11-02T15:30:00",
    "last_login": "2025-11-02T16:00:00"
  }
}
```

## Running the System

### Prerequisites

1. **MPU6050 Sensor Connected to Raspberry Pi**
   - Ensure sensor is wired correctly (SDA, SCL, VCC, GND)
   - Test with: `sudo i2cdetect -y 1` (should show 0x68)

2. **Required Python Files in `authenticator/`:**
   - `sensor_collector.py` - Collects MPU6050 data
   - `authenticator.py` - DTW algorithm and normalization
   - `generate_gesture.py` - Gesture collection function
   - `authenticate_gesture.py` - Gesture verification function
   - `gesture_recognizer.py` - Wrapper class (updated)

### Starting the Server

```bash
cd /path/to/Bluetooth-Messenger/server
sudo python3 auth_server.py
```

**Expected Output:**
```
╔═══════════════════════════════════════════════╗
║   Authenticated BLE UART Server              ║
║   Gesture-based authentication required      ║
╚═══════════════════════════════════════════════╝

Gesture Recognizer initialized (MPU6050 MODE)
Using real sensor with DTW authentication
Authentication Manager initialized
Registered users: 0
Server running. Waiting for connections...
```

### Using the iOS App

1. **Build and Install:**
   - Open `client/client.xcodeproj` in Xcode
   - Build and run on physical iPhone
   - Connect to `rpi-gatt-server`

2. **New User Registration:**
   ```
   1. Enter first name (e.g., "Alice")
   2. Tap "Continue"
   3. See "Register Your Gesture" screen
   4. Tap "Start"
   5. Follow prompts on Raspberry Pi screen
   6. Perform gesture 3 times when prompted
   7. Wait for "Authentication successful!"
   8. Chat interface appears
   ```

3. **Existing User Login:**
   ```
   1. Enter first name (e.g., "Alice")
   2. Tap "Continue"
   3. See "Perform Your Gesture" screen
   4. Tap "Start" for attempt 1
   5. Perform gesture on Raspberry Pi
   6. See result (Pass/Fail)
   7. If needed, repeat for attempts 2 and 3
   8. If 2+ attempts pass → Chat interface
   ```

## Raspberry Pi Console During Authentication

### Registration (New User "Alice")
```
← Received: USERNAME:Alice
New user registration: Alice
→ Broadcasting: NEW_USER:Welcome Alice! Please perform your gesture...
← Received: READY_FOR_GESTURE:Alice
→ Broadcasting: RECORDING_START:Will collect 3 gesture samples...

=== Registering gestures for Alice ===
Will collect 3 gesture samples

--- Sample 1/3 ---
📝 Recording one gesture...
(3 second countdown happens here)
🔴 Recording... (4 seconds)
✓ Recorded and normalized: shape (160, 2)
✓ Sample 1 recorded successfully

--- Sample 2/3 ---
📝 Recording one gesture...
(3 second countdown happens here)
🔴 Recording... (4 seconds)
✓ Recorded and normalized: shape (160, 2)
✓ Sample 2 recorded successfully

--- Sample 3/3 ---
📝 Recording one gesture...
(3 second countdown happens here)
🔴 Recording... (4 seconds)
✓ Recorded and normalized: shape (160, 2)
✓ Sample 3 recorded successfully

✅ Registration complete: 3 gestures recorded
User 'Alice' registered with 3 gesture samples
→ Broadcasting: AUTH_SUCCESS:Alice
```

### Verification (Existing User "Alice")
```
← Received: USERNAME:Alice
Existing user login: Alice
→ Broadcasting: EXISTING_USER:Welcome back Alice! ...
← Received: READY_FOR_GESTURE:Alice

--- Attempt 1/3 for Alice ---
→ Broadcasting: RECORDING_START:Attempt 1/3. Perform gesture...

=== Authenticating Alice ===
Comparing against 3 stored gestures
🔴 Recording... (4 seconds)
(Countdown happens here)

⏳ Comparing against gesture list...
  Gesture 1: 0.045231 [✓ PASS]
  Gesture 2: 0.038745 [✓ PASS]
  Gesture 3: 0.052341 [✓ PASS]

📊 Results: 3/3 gestures matched
✅ AUTHENTICATION SUCCESSFUL!
   Majority of gestures matched (threshold: > 1.5)

✅ AUTHENTICATED
Confidence: 100% (3/3 passed)
Attempt 1: PASS (confidence: 100%) - Total: 1/1
→ Broadcasting: ATTEMPT_RESULT:1:success:1/1

(User can do 2 more attempts or finish here)
→ Broadcasting: AUTH_SUCCESS:Alice
```

## Protocol Messages

### Server → iOS

| Message | When | Purpose |
|---------|------|---------|
| `AUTH_REQUIRED` | On connection | Prompt for authentication |
| `NEW_USER:msg` | Unknown username | Start registration |
| `EXISTING_USER:msg` | Known username | Start verification |
| `RECORDING_START:msg` | Gesture recording begins | Show status on iOS |
| `ATTEMPT_RESULT:N:success/failed:X/3` | After each attempt | Show pass/fail |
| `AUTH_SUCCESS:name` | Authentication passed | Enter chat |
| `AUTH_FAILED:reason` | Authentication failed | Show error |
| `ERROR:msg` | Error occurred | Show error |
| `MSG:name:text` | Chat message | Display message |

### iOS → Server

| Message | When | Purpose |
|---------|------|---------|
| `USERNAME:name\n` | After entering name | Submit username |
| `READY_FOR_GESTURE:name\n` | User taps "Start" | Begin gesture recording |
| `MSG:name:text\n` | Send chat message | Send message |

## File Structure

```
server/
├── auth_server.py          # Main server (UPDATED)
├── auth_manager.py         # Auth state machine (UPDATED)
├── user_database.py        # User storage (UPDATED)
└── users.json              # User data (generated)

authenticator/
├── gesture_recognizer.py   # Wrapper class (UPDATED)
├── generate_gesture.py     # YOUR FILE - gesture collection
├── authenticate_gesture.py # YOUR FILE - gesture verification
├── sensor_collector.py     # YOUR FILE - MPU6050 interface
├── authenticator.py        # YOUR FILE - DTW algorithm
└── read_sensor_data.py     # (optional) standalone sensor test

client/client/
├── BluetoothManager.swift  # BLE + Protocol (UPDATED)
├── AuthenticationView.swift # Auth UI (UPDATED)
└── ContentView.swift       # Main app
```

## Troubleshooting

### iOS App Issues

**"Recording..." stuck:**
- Check Raspberry Pi console for errors
- Ensure MPU6050 is connected
- Check server is running and not crashed

**Authentication always fails:**
- Check DTW threshold in `authenticate_gesture.py`
- Ensure gesture is consistent
- Try registering again with clearer gestures

### Server Issues

**ImportError for generate_gesture:**
```bash
cd authenticator
python3 -c "from generate_gesture import generate_single_gesture"
```

**ImportError for sensor_collector:**
- Ensure all your gesture files are in `authenticator/`
- Check file names match imports

**MPU6050 not found:**
```bash
sudo i2cdetect -y 1  # Should show 0x68
sudo apt-get install i2c-tools python3-smbus
```

**"No module named 'numpy'":**
```bash
sudo pip3 install numpy
```

### DTW Threshold Tuning

If authentication is too strict or too lenient, adjust in `authenticator/authenticate_gesture.py`:

```python
SIMILARITY_THRESHOLD_DTW = 0.05  # Lower = stricter, Higher = more lenient
```

## Testing Checklist

- [ ] MPU6050 sensor responding (`sudo i2cdetect -y 1`)
- [ ] Server starts without import errors
- [ ] iOS app connects to `rpi-gatt-server`
- [ ] New user can register (sees 3 countdowns on RPi)
- [ ] Registration saves to `users.json`
- [ ] Existing user can login with correct gesture
- [ ] 2/3 attempts passing authenticates user
- [ ] < 2/3 attempts fails authentication
- [ ] Chat works after authentication
- [ ] Messages show sender names

## Key Differences from Dummy Mode

| Aspect | Dummy Mode | Real Gesture Mode |
|--------|-----------|-------------------|
| Sensor | Simulated | Real MPU6050 |
| Countdown | On iOS | On Raspberry Pi console |
| Recording | Fake delay | Real 4-second capture |
| Comparison | Random | DTW algorithm |
| Success Rate | 70% random | Based on gesture match |
| Data Storage | 10 random floats | 3x(160x2) arrays |
| Registration | Instant | ~40 seconds (3 samples) |
| Verification | <1 second | ~15 seconds per attempt |

## Performance Notes

- **Registration time:** ~40 seconds (3 samples × ~13 seconds each)
- **Verification time:** ~15 seconds per attempt
- **Countdown:** 3 seconds before each recording
- **Recording:** 4 seconds per gesture
- **Processing:** 1-2 seconds for DTW comparison

## Next Steps

1. **Test the system** with real gestures
2. **Tune DTW threshold** if needed
3. **Train users** on consistent gesture patterns
4. **Monitor** false acceptance/rejection rates
5. **Optimize** recording duration if needed

## Support

If you encounter issues:
1. Check server console output
2. Verify MPU6050 connection
3. Test gesture functions standalone
4. Check iOS console in Xcode
5. Verify all imports work

---

**Ready to test!** Start the server and iOS app, then follow the authentication flow.
