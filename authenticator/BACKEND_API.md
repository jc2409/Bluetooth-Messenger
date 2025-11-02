# Backend API - For Frontend Integration

## 🎯 What You Have

Two simple tools:

### 1️⃣ Collect Gesture (Call once per recording)

```python
from generate_gesture import generate_single_gesture

gesture_array = generate_single_gesture()
# Returns: numpy array, shape (160, 2)
# Time: ~4 seconds
# Actions: Records 4 seconds, normalizes, returns
```

**That's it.** Just records and returns the (160, 2) array.

---

### 2️⃣ Authenticate Gesture (Call once for verification)

```python
from authenticate_gesture import authenticate_against_gestures

is_authenticated, results = authenticate_against_gestures(
    gesture_list=stored_gestures,  # shape (N, 160, 2)
    test_gesture=new_gesture        # shape (160, 2)
)

# Returns:
# - is_authenticated: bool (True/False)
# - results: dict with details
```

**That's it.** Just compares and returns True/False.

---

## 📋 Complete Frontend Workflow

```python
import numpy as np
from generate_gesture import generate_single_gesture
from authenticate_gesture import authenticate_against_gestures

# ============================================
# PHASE 1: GENERATION (Frontend does the loop)
# ============================================

# Frontend asks user to record 3 times
gestures_collected = []
for attempt in range(3):
    print(f"Record attempt {attempt+1}/3")
    gesture = generate_single_gesture()  # Frontend calls 3 times
    gestures_collected.append(gesture)   # Frontend collects them

# Frontend saves the batch
gesture_name = "my_gesture"
batch = np.array(gestures_collected)    # Shape: (3, 160, 2)
np.save(f"gestures/{gesture_name}/batch.npy", batch)

# ============================================
# PHASE 2: AUTHENTICATION (Later)
# ============================================

# Frontend loads the stored gestures
stored = np.load(f"gestures/{gesture_name}/batch.npy")

# Frontend asks user to draw once
new_gesture = generate_single_gesture()  # Frontend calls once

# Backend compares
is_authenticated, results = authenticate_against_gestures(
    gesture_list=stored,
    test_gesture=new_gesture
)

# Result
if is_authenticated:
    print("✅ Access granted!")
else:
    print("❌ Access denied!")
```

---

## 🔧 That's All You Need

| Operation | Function | Input | Output |
|-----------|----------|-------|--------|
| **Collect** | `generate_single_gesture()` | None | `(160, 2)` array |
| **Verify** | `authenticate_against_gestures()` | gesture_list, test_gesture | `(bool, dict)` |

---

## 💡 Frontend Responsibilities

Frontend handles:
- ✅ Asking user to draw (3 times for generation, 1 time for auth)
- ✅ Looping the collection calls
- ✅ Creating folders and saving files
- ✅ Loading saved gestures
- ✅ Displaying results to user

Backend provides:
- ✅ `generate_single_gesture()` - collect one gesture
- ✅ `authenticate_against_gestures()` - compare gestures

---

## 📊 Data Flow

```
Frontend                          Backend
--------                          -------

For i in 1-3:
  Show countdown        ──────►   [4-second recording]
  Wait...               ◄──────   Return (160, 2) array
  Save to list

Later:

  Load batch.npy
  Show countdown        ──────►   [4-second recording]
  Wait...               ◄──────   Return (160, 2) array
  
  Call authenticate()   ──────►   Compare using DTW
  Wait...               ◄──────   Return True/False
  
  Show result
```

---

## 🎯 No Waiting/Looping on Backend

Backend is **stateless**:
- ❌ No loops
- ❌ No waiting for user input  
- ❌ No folder creation
- ❌ No file saving
- ✅ Just collect & compare

Frontend controls:
- ✅ When to call
- ✅ What to do with results
- ✅ Loop iterations
- ✅ File management

---

## 📝 Simple Example

```python
# Generation
from generate_gesture import generate_single_gesture
import numpy as np

print("Draw gesture 3 times...")
gestures = [generate_single_gesture() for _ in range(3)]
batch = np.array(gestures)
np.save("my_gesture.npy", batch)

# Authentication
from authenticate_gesture import authenticate_against_gestures

stored = np.load("my_gesture.npy")
new = generate_single_gesture()

authenticated, _ = authenticate_against_gestures(stored, new)
print("Authenticated!" if authenticated else "Failed!")
```

---

## ✨ Summary

**You now have:**

```python
# 1. Collect one gesture - returns (160, 2)
generate_single_gesture()

# 2. Authenticate - takes gesture_list and test_gesture, returns True/False
authenticate_against_gestures(gesture_list, test_gesture)
```

**That's literally it.** Frontend does everything else! 🚀
