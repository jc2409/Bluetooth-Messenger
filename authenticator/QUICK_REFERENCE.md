# Quick Reference - Gesture Authentication

## 🚀 30-Second Start

```bash
cd authenticator

# Generate a gesture
python test_generation.py
# → Enter name → Record 3 times → Saved!

# Authenticate against it
python authenticate_gesture.py
# → Select gesture → Draw once → ✅ or ❌
```

## 📚 Common Tasks

### Generate Gesture (CLI)
```bash
python test_generation.py
# Input: gesture name (e.g., "circle")
# Records 3 examples (4 seconds each)
# Saves to: gestures/circle/batch.npy
```

### Authenticate (CLI)
```bash
python authenticate_gesture.py
# Select from list → Draw gesture → Result
```

### Generate in Code
```python
from gesture_api import generate_gesture
generate_gesture("circle", num_recordings=3)
```

### Authenticate in Code
```python
from gesture_api import authenticate
is_auth, results = authenticate("circle")
if is_auth:
    print("✅ Authenticated!")
else:
    print("❌ Failed!")
```

### List All Gestures
```python
from gesture_api import list_gestures
gestures = list_gestures()
print(gestures)  # ['circle', 'wave', 'zigzag']
```

### Load Gesture Data
```python
import numpy as np
batch = np.load("gestures/circle/batch.npy")
print(batch.shape)  # (3, 160, 2)
```

### Direct Array Authentication
```python
from gesture_api import authenticate
import numpy as np

batch = np.load("gestures/circle/batch.npy")
is_auth, _ = authenticate(gesture_list=batch)
```

### Delete Gesture
```python
from gesture_api import GestureAPI
api = GestureAPI()
api.delete_gesture("circle")
```

## 🔧 Tuning

### Change DTW Threshold
Edit `authenticator.py`:
```python
SIMILARITY_THRESHOLD_DTW = 0.055  # Lower = stricter
```

### Change Recording Duration
Edit `sensor_collector.py`:
```python
SensorCollector(duration=5, target_hz=40)  # 5 seconds
```

### Change Resampling Rate
Edit `sensor_collector.py`:
```python
SensorCollector(duration=4, target_hz=20)  # 80 points instead of 160
```

### Change Number of Recordings
When generating:
```python
api.generate_gesture_template("circle", num_recordings=5)  # 5 instead of 3
```

## 📊 Data Shapes

| Operation | Input Shape | Output Shape |
|-----------|-------------|--------------|
| Single collection | — | `(160, 2)` |
| Batch (3 recordings) | — | `(3, 160, 2)` |
| DTW comparison | `(160, 2)` + `(160, 2)` | `float` (distance) |

## 🎯 Majority Voting

Authentication passes if **> 50%** of stored gestures match:
- 1 recording: needs 1/1 (100%)
- 2 recordings: needs 2/2 (100%)
- 3 recordings: needs 2/3 (67%) ← **Recommended**
- 4 recordings: needs 3/4 (75%)

**Note:** 3 recordings is the sweet spot - tolerates 1 bad match.

## 🗂️ File Structure

```
authenticator/
├── authenticator.py              # Core algorithms
├── read_sensor_data.py          # Sensor interface
├── sensor_collector.py          # Collection & resampling
├── generate_gesture.py          # Single gesture
├── test_generation.py           # Main generator (3x)
├── authenticate_gesture.py      # Main authenticator
├── gesture_api.py               # High-level API
├── example_usage.py             # Examples
├── GESTURE_AUTH_README.md       # Full documentation
├── IMPLEMENTATION_SUMMARY.md    # Architecture details
└── gestures/
    ├── circle/
    │   ├── gesture_1.npy
    │   ├── gesture_2.npy
    │   ├── gesture_3.npy
    │   └── batch.npy
    └── wave/
        └── ...
```

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| ImportError | Check imports at top of files |
| "No sensor found" | Check I2C connection (address 0x68) |
| Always authenticates | Lower threshold in authenticator.py |
| Never authenticates | Raise threshold or record more steadily |
| File not found | Run `python test_generation.py` first |

## 🔐 What Gets Saved

When you run `test_generation.py` with name "circle":

```
gestures/circle/
├── gesture_1.npy    ← Individual recording 1 (160, 2)
├── gesture_2.npy    ← Individual recording 2 (160, 2)
├── gesture_3.npy    ← Individual recording 3 (160, 2)
└── batch.npy        ← All 3 together (3, 160, 2)
```

All files contain **normalized** gesture data (mean=0, std=1).

## 💡 Pro Tips

1. **Create multiple gesture types** for multi-factor authentication:
   ```python
   from gesture_api import generate_gesture
   generate_gesture("circle")
   generate_gesture("wave")
   generate_gesture("zigzag")
   ```

2. **Check authentication details**:
   ```python
   is_auth, results = authenticate("circle")
   print(results['dtw_results'])  # See each comparison
   ```

3. **Record gestures consistently** for best results:
   - Same speed each time
   - Same path/shape
   - Stable hand position

4. **Adjust threshold per gesture** if needed (create variants):
   ```python
   generate_gesture("circle_strict")
   # Manually reduce batch if too sensitive
   ```

## 📞 Modules at a Glance

| Module | Purpose | Main Function |
|--------|---------|----------------|
| `sensor_collector.py` | Raw data collection | `SensorCollector.collect_gesture()` |
| `generate_gesture.py` | Single recording | `generate_single_gesture()` |
| `test_generation.py` | 3-recording template | `test_generation()` |
| `authenticate_gesture.py` | Authentication engine | `authenticate_against_gestures()` |
| `gesture_api.py` | High-level API | `GestureAPI` class |
| `authenticator.py` | Algorithms | `dtw_distance()`, `normalize_series()` |

## 🚀 Next Steps

1. ✅ Run `python test_generation.py` to create first gesture
2. ✅ Run `python authenticate_gesture.py` to test
3. ✅ Integrate into your frontend using `gesture_api.py`
4. ✅ Tune threshold if needed
5. ✅ Create additional gestures for security

---

**Need help?** Check:
- `GESTURE_AUTH_README.md` for full documentation
- `IMPLEMENTATION_SUMMARY.md` for architecture details
- `example_usage.py` for code examples
