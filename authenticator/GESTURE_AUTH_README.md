# Gesture Authentication System

Refactored gesture authentication using real MPU6050 sensor data with DTW (Dynamic Time Warping) algorithm.

## 📁 File Structure

```
authenticator/
├── authenticator.py              # Core algorithms (DTW, TWED, etc.) - UNCHANGED
├── read_sensor_data.py           # Sensor interface - UNCHANGED
├── sensor_collector.py           # NEW - Collects & resamples sensor data to 160 points
├── generate_gesture.py           # NEW - Collects single gesture (call once per recording)
├── test_generation.py            # NEW - Collects 3 gestures and saves to folder
├── authenticate_gesture.py       # NEW - Authenticates against gesture list
├── example_usage.py              # NEW - Usage examples
└── gestures/                     # NEW - Stores trained gesture folders
    ├── circle/
    │   ├── gesture_1.npy        # Individual recording (160, 2)
    │   ├── gesture_2.npy
    │   ├── gesture_3.npy
    │   └── batch.npy            # All 3 together (3, 160, 2)
    └── wave/
        ├── gesture_1.npy
        ├── gesture_2.npy
        ├── gesture_3.npy
        └── batch.npy
```

## 🎯 Data Format

- **Duration**: 4 seconds per recording
- **Sample Rate**: 40Hz (collected via averaging)
- **Total Datapoints**: 160 points per recording
- **Coordinates**: (X, Y) from accelerometer
- **Shape**: Individual = (160, 2), Batch = (3, 160, 2)

## 🚀 Quick Start

### 1. Generate a New Gesture

```bash
python test_generation.py
# Input: gesture name (e.g., "circle")
# Records 3 examples, saves to gestures/circle/
```

**Output:**
- `gestures/circle/gesture_1.npy` - Individual recording 1
- `gestures/circle/gesture_2.npy` - Individual recording 2
- `gestures/circle/gesture_3.npy` - Individual recording 3
- `gestures/circle/batch.npy` - All 3 combined

### 2. Authenticate Against a Gesture

```bash
python authenticate_gesture.py
# Select gesture from list
# Draw the gesture
# Result: True/False (majority voting on 3 recordings)
```

### 3. Programmatic Usage

```python
import numpy as np
from authenticate_gesture import authenticate_against_gestures

# Load saved gesture
gesture_list = np.load("gestures/circle/batch.npy")  # Shape: (3, 160, 2)

# Authenticate (records new gesture and compares)
is_authenticated, results = authenticate_against_gestures(gesture_list)

print(f"Authenticated: {is_authenticated}")
print(f"Matched: {results['passed_count']}/{results['total_count']}")
```

## 📚 Module Overview

### `sensor_collector.py`
Handles sensor data collection and resampling.

```python
from sensor_collector import SensorCollector

collector = SensorCollector(duration=4, target_hz=40)
gesture_data = collector.collect_gesture(countdown=3)  # Returns (160, 2)
```

**Methods:**
- `collect_raw_data()` - Collects raw accelerometer readings for 4 seconds
- `resample_to_target_hz()` - Averages raw data to 160 points (40Hz)
- `collect_gesture()` - Full recording with countdown

### `generate_gesture.py`
Collects a single gesture recording.

```python
from generate_gesture import generate_single_gesture

gesture = generate_single_gesture()  # Returns (160, 2) normalized
```

**Returns:** Normalized gesture array, shape (160, 2)

### `test_generation.py`
Main entry point for creating gesture templates.

```python
from test_generation import test_generation

recordings, folder = test_generation()
# recordings: list of 3 arrays, each (160, 2)
# folder: Path to gestures/{gesture_name}/
```

**Features:**
- Asks for gesture name
- Collects 3 recordings
- Saves individual files + batch file
- Handles overwrites

### `authenticate_gesture.py`
Main authentication engine.

```python
from authenticate_gesture import authenticate_against_gestures

is_auth, results = authenticate_against_gestures(gesture_list)
```

**Parameters:**
- `gesture_list`: List/array of shape (N, 160, 2) - multiple gesture recordings

**Returns:**
- `is_authenticated`: Boolean result (True if > 50% match)
- `results`: Dictionary with detailed results
  - `dtw_results`: Per-gesture DTW scores
  - `passed_count`: Number that matched
  - `total_count`: Total comparisons
  - `authenticated`: Final result

**Authentication Logic:**
1. Collect user gesture (4 seconds, 160 points)
2. Compare against each gesture in the list using DTW
3. Count how many pass the threshold (0.055)
4. Return True if majority (> 50%) pass

## 🔧 Advanced Usage

### Load and Authenticate

```python
import numpy as np
from authenticate_gesture import authenticate_against_gestures

# Load saved gesture batch
batch = np.load("gestures/circle/batch.npy")  # Shape: (3, 160, 2)

# Can also load individual files
ind1 = np.load("gestures/circle/gesture_1.npy")  # Shape: (160, 2)
ind2 = np.load("gestures/circle/gesture_2.npy")
ind3 = np.load("gestures/circle/gesture_3.npy")

# Both work the same way
is_auth, results = authenticate_against_gestures(batch)
# or
is_auth, results = authenticate_against_gestures([ind1, ind2, ind3])
```

### Modify DTW Threshold

Edit the threshold in `authenticator.py`:

```python
SIMILARITY_THRESHOLD_DTW = 0.055  # Lower = stricter, Higher = more lenient
```

### Custom Resampling Rate

```python
from sensor_collector import SensorCollector

collector = SensorCollector(duration=4, target_hz=20)  # 80 points instead of 160
```

## 📊 Workflow Diagram

```
┌─────────────────────┐
│  test_generation.py │
│  (Ask 3 times)      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────┐
│ sensor_collector.py     │
│ (Collect & resample)    │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│ gestures/circle/        │
│ ├─ gesture_1.npy        │
│ ├─ gesture_2.npy        │
│ ├─ gesture_3.npy        │
│ └─ batch.npy            │
└────────────────────────┘

┌──────────────────────────────┐
│ authenticate_gesture.py      │
│ (Load batch & compare)       │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ sensor_collector.py          │
│ (Collect user gesture)       │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ authenticator.py (DTW)       │
│ Compare vs all 3 recordings  │
│ Majority voting: > 50%?      │
└──────────┬───────────────────┘
           │
           ▼
    ✅ True / ❌ False
```

## 🎮 Complete Example

```bash
# Step 1: Generate gesture
$ python test_generation.py
Enter gesture name: circle
Recording 1/3
Starting in 3...
🔴 Recording... (4 seconds)
✅ Recording complete! Collected 160 datapoints
✓ Recorded and normalized: shape (160, 2)
...
✅ Gesture 'circle' successfully generated!
   Location: gestures/circle
   Files: gesture_1.npy, gesture_2.npy, gesture_3.npy, batch.npy

# Step 2: Authenticate
$ python authenticate_gesture.py
📋 Available gestures:
  1. circle
Select gesture to authenticate (number): 1
🔍 Authenticating against gesture: 'circle'

📝 Recording one gesture...
Get ready to draw your gesture...
Starting in 3...
🔴 Recording... (4 seconds)
✅ Recording complete! Collected 160 datapoints

⏳ Comparing against gesture list...
  Gesture 1: 0.048291 [✓ PASS]
  Gesture 2: 0.052104 [✓ PASS]
  Gesture 3: 0.058234 [✗ FAIL]

📊 Results: 2/3 gestures matched
✅ AUTHENTICATION SUCCESSFUL!
   Majority of gestures matched (threshold: > 1.5)
```

## ⚙️ Configuration

All configuration in `authenticator.py`:

```python
# DTW threshold for single recording
SIMILARITY_THRESHOLD_DTW = 0.055

# Can be tuned based on your sensor data
# Lower = stricter (fewer false positives)
# Higher = more lenient (fewer false negatives)
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "No sensor found" | Check MPU6050 connection on I2C (0x68) |
| Always fails | Lower threshold in authenticator.py or record steadier gestures |
| Always passes | Raise threshold (more sensitive) |
| Inconsistent results | Sensor calibration needed; ensure consistent recording speed |

## 🔄 Integration with Frontend

The frontend can use this system like:

```python
# Generate phase (call 3 times from UI)
from generate_gesture import generate_single_gesture

for attempt in range(3):
    gesture = generate_single_gesture()
    # Save to list
    all_gestures.append(gesture)

# Save together
import numpy as np
batch = np.array(all_gestures)
np.save(f"gestures/{gesture_name}/batch.npy", batch)

# Authentication phase
from authenticate_gesture import authenticate_against_gestures

is_authenticated, _ = authenticate_against_gestures(batch)
return is_authenticated  # True/False to frontend
```

## 📝 Notes

- Each gesture is normalized independently before comparison
- Majority voting ensures robustness (not sensitive to one bad recording)
- DTW algorithm handles variations in speed/timing
- All data stored in efficient NumPy `.npy` format
