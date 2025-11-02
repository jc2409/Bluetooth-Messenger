"""
Example usage of the new gesture authentication system.

Workflow:
1. Run test_generation.py to create gesture templates
2. Use authenticate_gesture.py to verify against saved gestures
3. Or use this example for programmatic access
"""

import numpy as np
from pathlib import Path
from test_generation import test_generation
from authenticate_gesture import authenticate_against_gestures


def example_workflow():
    """
    Complete workflow example:
    1. Generate a gesture (collect 3 recordings)
    2. Authenticate against those recordings
    """
    
    print("\n" + "="*60)
    print("GESTURE AUTHENTICATION SYSTEM - EXAMPLE WORKFLOW")
    print("="*60)
    
    # Step 1: Generate gesture template
    print("\n📝 STEP 1: Generate Gesture Template")
    print("-" * 60)
    
    recordings, gesture_folder = test_generation()
    
    if recordings is None:
        print("❌ Generation failed!")
        return
    
    # recordings is a list of 3 gesture arrays, each shape (160, 2)
    print(f"\n✓ Generated {len(recordings)} recordings")
    
    # Step 2: Authenticate using the generated gestures
    print("\n🔐 STEP 2: Authenticate Against Generated Gestures")
    print("-" * 60)
    
    is_authenticated, results = authenticate_against_gestures(recordings)
    
    print(f"\n{'='*60}")
    print("FINAL RESULT")
    print(f"{'='*60}")
    
    if is_authenticated:
        print("✅ AUTHENTICATION SUCCESSFUL!")
    else:
        print("❌ AUTHENTICATION FAILED!")
    
    print(f"Details: {results['passed_count']}/{results['total_count']} gestures matched")


def example_load_and_authenticate():
    """
    Example: Load a previously saved gesture and authenticate against it.
    """
    
    print("\n" + "="*60)
    print("LOAD & AUTHENTICATE EXAMPLE")
    print("="*60)
    
    gestures_dir = Path("gestures")
    
    # List available gestures
    gesture_folders = [d for d in gestures_dir.iterdir() if d.is_dir()]
    
    if not gesture_folders:
        print("❌ No gesture folders found!")
        return
    
    print("\nAvailable gestures:")
    for i, folder in enumerate(gesture_folders, 1):
        print(f"  {i}. {folder.name}")
    
    idx = int(input("\nSelect gesture (number): ")) - 1
    gesture_folder = gesture_folders[idx]
    
    # Load batch file
    batch_file = gesture_folder / "batch.npy"
    
    if batch_file.exists():
        gesture_list = np.load(batch_file)  # Shape: (3, 160, 2)
        print(f"\n✓ Loaded {gesture_folder.name} - {gesture_list.shape}")
        
        # Authenticate
        print("\nAuthenticating...")
        is_authenticated, results = authenticate_against_gestures(gesture_list)
        
        return is_authenticated
    else:
        print("❌ No batch file found!")
        return False


if __name__ == "__main__":
    # Choose which example to run
    print("\n1. Full workflow (generate then authenticate)")
    print("2. Load and authenticate existing gesture")
    
    choice = input("\nSelect (1 or 2): ").strip()
    
    if choice == "1":
        example_workflow()
    elif choice == "2":
        example_load_and_authenticate()
    else:
        print("❌ Invalid choice!")
