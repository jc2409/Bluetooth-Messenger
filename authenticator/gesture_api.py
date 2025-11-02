"""
Simple API for gesture authentication system.
Use this for easy integration with frontend or other applications.
"""

import numpy as np
from pathlib import Path
from sensor_collector import SensorCollector
from authenticate_gesture import authenticate_against_gestures
from authenticator import normalize_series


class GestureAPI:
    """
    High-level API for gesture authentication.
    """
    
    def __init__(self, gestures_dir="gestures"):
        self.gestures_dir = Path(gestures_dir)
        self.gestures_dir.mkdir(exist_ok=True)
        self.collector = SensorCollector(duration=4, target_hz=40)
    
    def collect_gesture(self, countdown=3):
        """
        Collect a single gesture recording.
        
        Returns:
            np.ndarray: Normalized gesture, shape (160, 2)
        """
        return self.collector.collect_gesture(countdown=countdown)
    
    def generate_gesture_template(self, gesture_name, num_recordings=3):
        """
        Generate a new gesture template by collecting multiple recordings.
        
        Args:
            gesture_name (str): Name of the gesture (e.g., 'circle')
            num_recordings (int): Number of recordings to collect (default 3)
        
        Returns:
            tuple: (recordings_list, gesture_folder_path)
        """
        gesture_folder = self.gestures_dir / gesture_name
        gesture_folder.mkdir(exist_ok=True)
        
        recordings = []
        
        for i in range(num_recordings):
            print(f"\n{'='*50}")
            print(f"Recording {i+1}/{num_recordings}")
            print(f"{'='*50}")
            
            gesture_data = self.collect_gesture()
            recordings.append(gesture_data)
            
            # Save individual file
            gesture_file = gesture_folder / f"gesture_{i+1}.npy"
            np.save(gesture_file, gesture_data)
            print(f"✓ Saved to {gesture_file.name}")
        
        # Save batch
        batch_array = np.array(recordings)
        batch_file = gesture_folder / "batch.npy"
        np.save(batch_file, batch_array)
        
        print(f"\n✅ Gesture '{gesture_name}' generated!")
        print(f"   Folder: {gesture_folder}")
        print(f"   Shape: {batch_array.shape}")
        
        return recordings, gesture_folder
    
    def authenticate(self, gesture_name=None, gesture_list=None):
        """
        Authenticate against a saved gesture or provided gesture list.
        
        Args:
            gesture_name (str): Name of saved gesture to load
            gesture_list (list/array): Alternative - provide gestures directly
        
        Returns:
            tuple: (is_authenticated: bool, results: dict)
        """
        
        # Load gesture list if name provided
        if gesture_name and gesture_list is None:
            batch_file = self.gestures_dir / gesture_name / "batch.npy"
            
            if not batch_file.exists():
                print(f"❌ Gesture '{gesture_name}' not found!")
                return False, {}
            
            gesture_list = np.load(batch_file)
            print(f"🔐 Loaded gesture: {gesture_name}")
        
        if gesture_list is None:
            print("❌ No gesture provided!")
            return False, {}
        
        # Authenticate
        return authenticate_against_gestures(gesture_list)
    
    def list_gestures(self):
        """
        List all available gesture templates.
        
        Returns:
            list: Names of available gestures
        """
        gesture_folders = [d.name for d in self.gestures_dir.iterdir() if d.is_dir()]
        return sorted(gesture_folders)
    
    def delete_gesture(self, gesture_name):
        """
        Delete a gesture template.
        
        Args:
            gesture_name (str): Name of gesture to delete
        
        Returns:
            bool: True if successful
        """
        import shutil
        
        gesture_folder = self.gestures_dir / gesture_name
        
        if not gesture_folder.exists():
            print(f"❌ Gesture '{gesture_name}' not found!")
            return False
        
        try:
            shutil.rmtree(gesture_folder)
            print(f"✓ Deleted gesture: {gesture_name}")
            return True
        except Exception as e:
            print(f"❌ Error deleting gesture: {e}")
            return False
    
    def load_gesture(self, gesture_name):
        """
        Load a gesture batch file.
        
        Args:
            gesture_name (str): Name of gesture
        
        Returns:
            np.ndarray: Gesture data, shape (N, 160, 2)
        """
        batch_file = self.gestures_dir / gesture_name / "batch.npy"
        
        if not batch_file.exists():
            print(f"❌ Gesture '{gesture_name}' not found!")
            return None
        
        return np.load(batch_file)
    
    def save_gesture_custom(self, gesture_name, recordings):
        """
        Save custom gesture recordings.
        
        Args:
            gesture_name (str): Name for this gesture
            recordings (list/array): Gesture arrays, each shape (160, 2)
        
        Returns:
            Path: Folder path
        """
        gesture_folder = self.gestures_dir / gesture_name
        gesture_folder.mkdir(exist_ok=True)
        
        # Convert to list if array
        if isinstance(recordings, np.ndarray):
            recordings = [recordings[i] for i in range(len(recordings))]
        
        for i, recording in enumerate(recordings, 1):
            gesture_file = gesture_folder / f"gesture_{i}.npy"
            np.save(gesture_file, recording)
        
        # Save batch
        batch_array = np.array(recordings)
        batch_file = gesture_folder / "batch.npy"
        np.save(batch_file, batch_array)
        
        print(f"✓ Saved gesture: {gesture_name}")
        return gesture_folder


# Convenience functions for quick access
api = GestureAPI()


def generate_gesture(gesture_name, num_recordings=3):
    """Quick function to generate a gesture template."""
    return api.generate_gesture_template(gesture_name, num_recordings)


def authenticate(gesture_name=None, gesture_list=None):
    """Quick function to authenticate."""
    return api.authenticate(gesture_name, gesture_list)


def list_gestures():
    """List available gestures."""
    return api.list_gestures()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("GESTURE API - QUICK TEST")
    print("="*60)
    
    # Show available gestures
    gestures = list_gestures()
    print(f"\nAvailable gestures: {gestures if gestures else 'None'}")
    
    choice = input("\n1. Generate new gesture\n2. Authenticate\nSelect (1 or 2): ").strip()
    
    if choice == "1":
        name = input("Gesture name: ").strip()
        if name:
            generate_gesture(name, num_recordings=3)
    
    elif choice == "2":
        gestures = list_gestures()
        if gestures:
            print("\nAvailable gestures:")
            for i, g in enumerate(gestures, 1):
                print(f"  {i}. {g}")
            idx = int(input("Select (number): ")) - 1
            if 0 <= idx < len(gestures):
                is_auth, results = authenticate(gestures[idx])
        else:
            print("No gestures available. Generate one first.")
