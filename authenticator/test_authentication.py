import numpy as np
from pathlib import Path
from sensor_collector import SensorCollector
from authenticator import (
    normalize_series,
    dtw_distance,
    SIMILARITY_THRESHOLD_DTW
)

def test_authentication():
    """
    Test authentication with debug output.
    1. Lists available gestures
    2. User selects one
    3. Countdown and records new gesture
    4. Compares against 3 reference gestures
    5. Shows detailed results (pass/fail, scores, threshold)
    """
    
    gestures_dir = Path("gestures")
    
    # Check if gestures directory exists
    if not gestures_dir.exists():
        print("❌ No gestures/ directory found!")
        return False
    
    # List available gesture folders
    gesture_folders = sorted([d for d in gestures_dir.iterdir() if d.is_dir()])
    
    if not gesture_folders:
        print("❌ No gestures found in gestures/ directory!")
        print("Run test_generation.py first to create gestures.")
        return False
    
    # Display available gestures
    print("\n" + "="*60)
    print("📋 AVAILABLE GESTURES")
    print("="*60)
    for i, folder in enumerate(gesture_folders, 1):
        csv_files = list(folder.glob("gesture_*.csv"))
        print(f"{i}. {folder.name} ({len(csv_files)} recordings)")
    
    # Get user selection
    choice = input("\nSelect gesture to test (number): ").strip()
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(gesture_folders):
            selected_folder = gesture_folders[idx]
            gesture_name = selected_folder.name
        else:
            print("❌ Invalid selection!")
            return False
    except ValueError:
        print("❌ Invalid input!")
        return False
    
    # Load reference CSV files
    print(f"\n🔐 Testing gesture: '{gesture_name}'")
    print("="*60)
    
    csv_files = sorted(selected_folder.glob("gesture_*.csv"))
    
    if not csv_files:
        print("❌ No gesture recordings found!")
        return False
    
    print(f"✓ Loaded {len(csv_files)} reference recordings")
    
    reference_gestures = []
    for csv_file in csv_files:
        gesture_data = np.loadtxt(csv_file, delimiter=',', skiprows=1)
        reference_gestures.append(gesture_data)
    
    # Collect new test gesture
    print("\n📝 Now record your gesture to test...")
    print("="*60)
    
    collector = SensorCollector(duration=4, target_hz=40)
    test_gesture = collector.collect_gesture(countdown=3)
    
    # Normalize test gesture
    test_normalized = normalize_series(test_gesture)
    
    # Compare against each reference
    print("\n" + "="*60)
    print("🔍 AUTHENTICATION RESULTS")
    print("="*60)
    print(f"Threshold: {SIMILARITY_THRESHOLD_DTW:.6f}\n")
    
    results = []
    passed_count = 0
    
    for i, reference_gesture in enumerate(reference_gestures, 1):
        reference_normalized = normalize_series(reference_gesture)
        distance = dtw_distance(reference_normalized, test_normalized)
        passed = distance <= SIMILARITY_THRESHOLD_DTW
        
        if passed:
            passed_count += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        results.append({
            "index": i,
            "distance": distance,
            "passed": passed
        })
        
        # Show result with comparison to threshold
        diff = distance - SIMILARITY_THRESHOLD_DTW
        diff_str = f"+{diff:.6f}" if diff >= 0 else f"{diff:.6f}"
        
        print(f"Reference {i}:")
        print(f"  Distance: {distance:.6f}")
        print(f"  Threshold: {SIMILARITY_THRESHOLD_DTW:.6f}")
        print(f"  Difference: {diff_str}")
        print(f"  Result: {status}\n")
    
    # Final verdict
    total = len(reference_gestures)
    majority_threshold = total / 2.0
    is_authenticated = passed_count > majority_threshold
    
    print("="*60)
    print("📊 FINAL VERDICT")
    print("="*60)
    print(f"Matched: {passed_count}/{total} references")
    print(f"Required: > {majority_threshold} (majority)")
    print()
    
    if is_authenticated:
        print("✅✅✅ AUTHENTICATION SUCCESSFUL! ✅✅✅")
    else:
        print("❌❌❌ AUTHENTICATION FAILED! ❌❌❌")
    
    print("="*60 + "\n")
    
    return is_authenticated


if __name__ == "__main__":
    test_authentication()
