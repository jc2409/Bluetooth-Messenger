import numpy as np
from pathlib import Path
from authenticate_gesture import authenticate_against_gestures

def test_authentication():
    """
    Test authentication using the actual authenticate_gesture.py function.
    This tests the EXACT same code that the frontend will call.
    
    Flow:
    1. Lists available gestures
    2. User selects one
    3. Loads CSV reference files
    4. Calls authenticate_against_gestures() (the backend function)
    5. Shows detailed debug results
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
    
    print(f"✓ Loaded {len(csv_files)} reference recordings from CSV files")
    
    reference_gestures = []
    for csv_file in csv_files:
        gesture_data = np.loadtxt(csv_file, delimiter=',', skiprows=1)
        reference_gestures.append(gesture_data)
    
    # Call the ACTUAL backend function (authenticate_gesture.py)
    print("\n📝 Now recording your gesture to test...")
    print("="*60)
    
    is_authenticated, results = authenticate_against_gestures(reference_gestures)
    
    # Display detailed results
    print("\n" + "="*60)
    print("📊 DETAILED DEBUG RESULTS")
    print("="*60)
    
    for result in results['dtw_results']:
        distance = result['distance']
        passed = result['passed']
        status = "✅ PASS" if passed else "❌ FAIL"
        
        diff = distance - results['threshold']
        diff_str = f"+{diff:.6f}" if diff >= 0 else f"{diff:.6f}"
        
        print(f"Reference {result['gesture_idx']}:")
        print(f"  Distance: {distance:.6f}")
        print(f"  Threshold: {results['threshold']:.6f}")
        print(f"  Difference: {diff_str}")
        print(f"  Result: {status}\n")
    
    # Final verdict
    print("="*60)
    print("📊 FINAL VERDICT")
    print("="*60)
    print(f"Matched: {results['passed_count']}/{results['total_count']} references")
    majority_threshold = results['total_count'] / 2.0
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
