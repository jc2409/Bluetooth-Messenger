import numpy as np
from sensor_collector import SensorCollector
from authenticator import (
    normalize_series,
    dtw_distance,
    SIMILARITY_THRESHOLD_DTW
)

def authenticate_against_gestures(gesture_list):
    """
    Authenticate a new gesture recording against a list of gesture arrays.

    Args:
        gesture_list: List of numpy arrays, each shape (160, 2)
                      These are the stored gesture recordings to compare against

    Returns:
        tuple: (is_authenticated: bool, results: dict with details)
    """

    if not gesture_list or len(gesture_list) == 0:
        print("❌ No gestures provided for authentication!")
        return False, {}

    # Collect test gesture from user
    collector = SensorCollector(duration=4, target_hz=40)
    print("🔴 Recording... (4 seconds)")
    test_gesture = collector.collect_gesture(countdown=3)
    test_normalized = normalize_series(test_gesture)
    
    print("\n⏳ Comparing against gesture list...")
    
    # Compare against each gesture in the list using DTW
    dtw_results = []
    
    for i, reference_gesture in enumerate(gesture_list, 1):
        reference_normalized = normalize_series(reference_gesture)
        distance = dtw_distance(reference_normalized, test_normalized)
        passed = distance <= SIMILARITY_THRESHOLD_DTW
        dtw_results.append({
            "gesture_idx": i,
            "distance": distance,
            "passed": passed
        })
        
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  Gesture {i}: {distance:.6f} [{status}]")
    
    # Majority voting (> 50%)
    passed_count = sum(1 for r in dtw_results if r["passed"])
    total_count = len(dtw_results)
    majority_threshold = (total_count / 2.0)
    
    is_authenticated = passed_count > majority_threshold
    
    results = {
        "dtw_results": dtw_results,
        "passed_count": passed_count,
        "total_count": total_count,
        "threshold": SIMILARITY_THRESHOLD_DTW,
        "authenticated": is_authenticated
    }
    
    print(f"\n📊 Results: {passed_count}/{total_count} gestures matched")
    
    if is_authenticated:
        print("✅ AUTHENTICATION SUCCESSFUL!")
        print(f"   Majority of gestures matched (threshold: > {majority_threshold})")
    else:
        print("❌ AUTHENTICATION FAILED!")
        print(f"   Not enough gestures matched (got {passed_count}, needed > {majority_threshold})")
    
    return is_authenticated, results


def authenticate_interactive():
    """Interactive mode - load gestures from CSV files and authenticate."""
    from pathlib import Path
    
    gestures_dir = Path("gestures")
    
    if not gestures_dir.exists() or not list(gestures_dir.glob("*/gesture_*.csv")):
        print("❌ No saved gestures found in gestures/ directory!")
        print("Run test_generation.py first to create gesture templates.")
        return False
    
    # List available gestures (folders)
    gesture_folders = sorted([d for d in gestures_dir.iterdir() if d.is_dir()])
    print("\n📋 Available gestures:")
    for i, f in enumerate(gesture_folders, 1):
        print(f"  {i}. {f.name}")
    
    choice = input("\nSelect gesture to authenticate (number): ").strip()
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(gesture_folders):
            gesture_folder = gesture_folders[idx]
            gesture_name = gesture_folder.name
        else:
            print("❌ Invalid selection!")
            return False
    except ValueError:
        print("❌ Invalid input!")
        return False
    
    # Load gesture CSV files
    print(f"\n🔍 Authenticating against gesture: '{gesture_name}'")
    gesture_files = sorted(gesture_folder.glob("gesture_*.csv"))
    
    if not gesture_files:
        print("❌ No gesture files found!")
        return False
    
    gesture_list = []
    for csv_file in gesture_files:
        gesture_data = np.loadtxt(csv_file, delimiter=',', skiprows=1)
        gesture_list.append(gesture_data)
    
    print(f"✓ Loaded {len(gesture_list)} gesture recordings")
    
    is_authenticated, results = authenticate_against_gestures(gesture_list)
    return is_authenticated


if __name__ == "__main__":
    authenticate_interactive()
