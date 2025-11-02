import numpy as np
from pathlib import Path
from generate_gesture import generate_single_gesture
import time

def test_generation():
    """
    Generate a new gesture template by collecting 3 recordings.
    Each recording is saved as a separate CSV file in authenticator/gestures/{gesture_name}/
    """
    
    # Create gestures directory if not exists
    gestures_dir = Path("gestures")
    gestures_dir.mkdir(exist_ok=True)
    
    gesture_name = input("Enter gesture name (e.g., 'circle', 'wave', 'zigzag'): ").strip()
    
    if not gesture_name:
        print("❌ Invalid gesture name!")
        return
    
    # Create gesture-specific folder
    gesture_folder = gestures_dir / gesture_name
    gesture_folder.mkdir(exist_ok=True)
    
    # Check if folder already has files
    existing_files = list(gesture_folder.glob("*.csv"))
    if existing_files:
        overwrite = input(f"Gesture '{gesture_name}' folder already has {len(existing_files)} file(s). Overwrite? (y/n): ")
        if overwrite.lower() != 'y':
            print("❌ Cancelled.")
            return
        # Delete existing files
        for f in existing_files:
            f.unlink()
    
    print(f"\n📝 Generating gesture: '{gesture_name}'")
    print("You will record 3 examples of this gesture.")
    print("Each recording is 4 seconds long.\n")
    
    gesture_recordings = []
    
    for attempt in range(1, 4):
        print(f"\n{'='*50}")
        print(f"Recording {attempt}/3")
        print(f"{'='*50}")
        
        # Collect one gesture
        gesture_data = generate_single_gesture()
        gesture_recordings.append(gesture_data)
        
        # Save as CSV
        gesture_file = gesture_folder / f"gesture_{attempt}.csv"
        np.savetxt(gesture_file, gesture_data, delimiter=',', fmt='%.6f', header='x,y', comments='')
        print(f"✓ Saved to {gesture_file}")
        
        if attempt < 3:
            print("\nPreparing for next recording...")
            time.sleep(2)
    
    print(f"\n✅ Gesture '{gesture_name}' successfully generated!")
    print(f"   Location: {gesture_folder}")
    print(f"   Files: gesture_1.csv, gesture_2.csv, gesture_3.csv")
    print(f"   Each file contains 160 datapoints (X, Y coordinates)")
    
    return gesture_recordings, gesture_folder


if __name__ == "__main__":
    test_generation()
