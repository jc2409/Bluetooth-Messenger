# Files Overview

## 📊 Complete File Structure

```
authenticator/
│
├── 🔧 CORE MODULES (Refactored for Real Sensor Data)
│   ├── sensor_collector.py        ✅ NEW - Collects & resamples sensor data to 160 points
│   ├── generate_gesture.py        ✅ NEW - Collects single gesture (for loop-based generation)
│   ├── test_generation.py         ✅ NEW - Collects 3 gestures, saves to folder (MAIN GENERATOR)
│   ├── authenticate_gesture.py    ✅ NEW - Authenticates against gesture list (MAIN AUTHENTICATOR)
│   ├── gesture_api.py             ✅ NEW - High-level API wrapper for easy integration
│   ├── authenticator.py           📝 UNCHANGED - Core algorithms (DTW, TWED, HMM)
│   └── read_sensor_data.py        📝 UNCHANGED - Sensor interface for MPU6050
│
├── 📚 DOCUMENTATION
│   ├── GESTURE_AUTH_README.md     ✅ NEW - Comprehensive system documentation
│   ├── IMPLEMENTATION_SUMMARY.md  ✅ NEW - Architecture & changes overview
│   ├── QUICK_REFERENCE.md         ✅ NEW - Quick start guide & common tasks
│   ├── FILES_OVERVIEW.md          ✅ NEW - This file
│   └── example_usage.py           ✅ NEW - Usage examples & code samples
│
├── 🗂️ DATA STORAGE
│   └── gestures/                  ✅ AUTO-CREATED - Gesture templates
│       ├── circle/
│       │   ├── gesture_1.npy      (160, 2) - Individual recording
│       │   ├── gesture_2.npy      (160, 2)
│       │   ├── gesture_3.npy      (160, 2)
│       │   └── batch.npy          (3, 160, 2) - All combined
│       └── wave/
│           └── ...
│
├── 🔩 HARDWARE INTERFACE
│   ├── mpu6050/                   - MPU6050 sensor library
│   └── read_sensor_data.py        - Wrapper functions
```

## 📋 File Dependencies

```
sensor_collector.py
    ↓ (uses)
read_sensor_data.py ← Sensor interface
    ↓ (uses)
MPU6050 (hardware)

generate_gesture.py
    ↓ (uses)
sensor_collector.py
authenticator.normalize_series()

test_generation.py
    ↓ (uses)
generate_gesture.py
    ↓ (uses)
sensor_collector.py

authenticate_gesture.py
    ↓ (uses)
sensor_collector.py
authenticator.normalize_series()
authenticator.dtw_distance()

gesture_api.py
    ↓ (uses)
sensor_collector.py
authenticate_gesture.py
test_generation.py (indirectly)
authenticator.normalize_series()
```

## 🎯 What Each File Does

### Core Modules

#### `sensor_collector.py` - Data Collection & Resampling
**Purpose:** Handles all raw sensor data collection and processing
**Key Class:** `SensorCollector`
**Main Method:** `collect_gesture(countdown=3)` → (160, 2)
**Features:**
- Collects 4-second raw data from MPU6050
- Automatically resamples to 40Hz (160 points)
- Returns normalized-ready data
- Includes countdown timer

**When to Use:**
- All data collection needs
- Create your own collection loops
- Customize collection parameters

---

#### `generate_gesture.py` - Single Gesture Collection
**Purpose:** Collect and normalize one gesture recording
**Key Function:** `generate_single_gesture()` → (160, 2) normalized
**Features:**
- Calls SensorCollector.collect_gesture()
- Applies normalization
- Returns ready-to-save array
- Called once per recording

**When to Use:**
- Frontend integration (call in loop)
- Manual generation control
- Custom collection workflows

---

#### `test_generation.py` - Template Generator (3x)
**Purpose:** Main entry point for creating gesture templates
**Key Function:** `test_generation()` → (recordings, folder)
**Features:**
- Asks for gesture name
- Collects 3 recordings automatically
- Saves individual files + batch
- Handles overwrite confirmation
- Creates folder structure

**When to Use:**
- Command-line: `python test_generation.py`
- Creating new gesture templates
- Batch generation from code

**Output:**
```
gestures/circle/
├── gesture_1.npy
├── gesture_2.npy
├── gesture_3.npy
└── batch.npy
```

---

#### `authenticate_gesture.py` - Authentication Engine
**Purpose:** Compares new gesture against stored gestures
**Key Function:** `authenticate_against_gestures(gesture_list)` → (bool, dict)
**Features:**
- Collects new gesture from user
- Compares against all stored gestures using DTW
- Implements majority voting (> 50%)
- Returns detailed results
- Interactive mode available

**When to Use:**
- Command-line: `python authenticate_gesture.py`
- Backend authentication
- Detailed result analysis

**Returns:**
```python
is_authenticated (bool)
results (dict) {
    'dtw_results': [...],      # Per-gesture comparison
    'passed_count': int,
    'total_count': int,
    'authenticated': bool
}
```

---

#### `gesture_api.py` - High-Level API
**Purpose:** Simple, unified interface for all operations
**Key Class:** `GestureAPI`
**Methods:**
- `generate_gesture_template(name, num_recordings)` - Create template
- `authenticate(gesture_name, gesture_list)` - Verify gesture
- `list_gestures()` - Get all available
- `load_gesture(name)` - Load saved gesture
- `delete_gesture(name)` - Remove template
- `save_gesture_custom(name, recordings)` - Save manually

**When to Use:**
- Frontend integration
- Clean, simple code
- Error handling
- Any high-level operation

**Convenience Functions:**
```python
from gesture_api import generate_gesture, authenticate, list_gestures
```

---

#### `authenticator.py` - Core Algorithms
**Purpose:** Mathematical algorithms for gesture comparison
**Key Functions:**
- `normalize_series(series)` - Normalize gesture
- `dtw_distance(s1, s2)` - DTW comparison
- `twed_distance(s1, s2)` - TWED comparison
- `shape_dtw_distance(s1, s2)` - Shape-aware DTW
- `hmm_distance(refs, test)` - Hidden Markov Model

**Configuration:**
```python
SIMILARITY_THRESHOLD_DTW = 0.055      # Primary threshold
SIMILARITY_THRESHOLD_TWED = 0.30
SIMILARITY_THRESHOLD_SHAPEDTW = 0.12
SIMILARITY_THRESHOLD_HMM = -1.25
HMM_N_STATES = 3
```

**When to Use:**
- Direct algorithm access
- Tuning thresholds
- Understanding algorithms
- Multi-algorithm voting

---

#### `read_sensor_data.py` - Sensor Interface
**Purpose:** Wrapper around MPU6050 sensor
**Key Function:** `read_sensor_data()` → (accel_dict, gyro_dict)
**Returns:**
```python
accel = {'x': float, 'y': float, 'z': float}
gyro = {'x': float, 'y': float, 'z': float}
```

**When to Use:**
- Low-level sensor access
- Debugging sensor data
- Custom sensor operations

---

### Documentation

#### `GESTURE_AUTH_README.md` - Comprehensive Guide
**Contains:**
- Complete system overview
- Architecture explanation
- Detailed usage for each module
- Configuration options
- Troubleshooting guide
- Integration examples

**Read When:**
- Learning the system
- Deep understanding needed
- Troubleshooting issues

---

#### `IMPLEMENTATION_SUMMARY.md` - Changes & Architecture
**Contains:**
- What changed from old system
- Before/after architecture
- Data flow diagrams
- File structure
- Configuration reference
- Frontend integration example

**Read When:**
- Understanding refactoring
- Comparing old vs new
- Architecture decisions

---

#### `QUICK_REFERENCE.md` - Common Tasks
**Contains:**
- 30-second start
- Common code snippets
- CLI commands
- Troubleshooting table
- Pro tips
- Quick function reference

**Read When:**
- Quick lookup needed
- Trying common task
- Fast implementation

---

#### `example_usage.py` - Code Examples
**Contains:**
- Complete workflow example
- Load and authenticate example
- Usage of all main functions
- Error handling
- Commented code

**Run With:**
```bash
python example_usage.py
# Interactive menu with 2 examples
```

---

#### `FILES_OVERVIEW.md` - This File
**Purpose:** Understand all files and relationships
**Contains:**
- File structure
- Dependencies
- Purpose of each file
- When to use each

---

## 🔄 Common Workflows

### Workflow 1: Generate & Authenticate (CLI)
```
Start
  ↓
python test_generation.py
  ├─ collect 3 times
  ├─ normalize each
  └─ save to gestures/name/
  ↓
python authenticate_gesture.py
  ├─ load batch
  ├─ collect new
  ├─ DTW compare
  └─ majority vote
  ↓
Result (True/False)
```

### Workflow 2: Programmatic Integration
```
Code
  ↓
from gesture_api import generate_gesture, authenticate
  ↓
generate_gesture("circle", num_recordings=3)
  ├─ calls test_generation()
  ├─ saves to gestures/circle/
  └─ returns recordings, folder
  ↓
is_auth, results = authenticate("circle")
  ├─ loads batch
  ├─ calls authenticate_against_gestures()
  └─ returns bool + details
  ↓
Result + Analysis
```

### Workflow 3: Frontend Integration
```
Frontend
  ↓
for each gesture {
  gesture = generate_single_gesture()
  # User records once (4 seconds)
  save_to_list(gesture)
}
  ↓
batch = np.array(all_gestures)
np.save("gestures/name/batch.npy", batch)
  ↓
Later: authenticate(batch)
  ↓
Result
```

## 🎯 File Selection Guide

**Choose based on your need:**

| Need | File | Function |
|------|------|----------|
| Collect raw data | `sensor_collector.py` | `SensorCollector` |
| Collect one gesture | `generate_gesture.py` | `generate_single_gesture()` |
| Generate template (3x) | `test_generation.py` | `test_generation()` |
| Authenticate gesture | `authenticate_gesture.py` | `authenticate_against_gestures()` |
| Easy API | `gesture_api.py` | `GestureAPI` class |
| Compare algorithms | `authenticator.py` | `dtw_distance()` etc |
| Low-level sensor | `read_sensor_data.py` | `read_sensor_data()` |
| Learn system | `GESTURE_AUTH_README.md` | — |
| Understand changes | `IMPLEMENTATION_SUMMARY.md` | — |
| Quick help | `QUICK_REFERENCE.md` | — |
| Code examples | `example_usage.py` | — |

## 🚀 Getting Started Path

1. **First Time?**
   - Read: `QUICK_REFERENCE.md` (2 min)
   - Try: `python test_generation.py` (12 sec)
   - Try: `python authenticate_gesture.py` (8 sec)

2. **Want Details?**
   - Read: `GESTURE_AUTH_README.md` (10 min)
   - Read: `IMPLEMENTATION_SUMMARY.md` (8 min)

3. **Ready to Code?**
   - Read: `gesture_api.py` code (5 min)
   - Copy examples from: `example_usage.py`
   - Start integrating!

4. **Troubleshooting?**
   - Check: `QUICK_REFERENCE.md` troubleshooting section
   - Check: `GESTURE_AUTH_README.md` FAQ

## 📊 Import Dependencies

```
Standard Library
├── numpy
├── pathlib
├── time
└── importlib

Internal Modules
├── read_sensor_data.py
├── sensor_collector.py
├── generate_gesture.py
├── test_generation.py
└── authenticator.py

External Packages
├── dtaidistance (for DTW)
├── hmmlearn (for HMM)
├── sklearn (required by hmmlearn)
└── mpu6050 library
```

## ✨ Summary

- **7 new Python modules** for real sensor integration
- **4 documentation files** for comprehensive guides
- **1 original algorithm file** unchanged for compatibility
- **Gesture folder** auto-created for template storage

All work together to provide:
✅ Sensor data collection & resampling
✅ Gesture template generation (3 recordings)
✅ DTW-based authentication with majority voting
✅ Simple API for easy integration
✅ Complete documentation & examples
