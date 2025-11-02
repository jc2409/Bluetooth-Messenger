import numpy as np
from sensor_collector import SensorCollector
from authenticator import normalize_series

def generate_single_gesture():
    """
    Collect a single gesture recording and return normalized data.
    Frontend will call this multiple times and handle the loop.
    
    Returns: numpy array of shape (160, 2) - normalized X, Y coordinates
    """
    collector = SensorCollector(duration=4, target_hz=40)
    
    print("\n📝 Recording one gesture...")
    gesture_data = collector.collect_gesture(countdown=3)
    
    # Normalize the gesture
    normalized = normalize_series(gesture_data)
    
    print(f"✓ Recorded and normalized: shape {normalized.shape}")
    return normalized

if __name__ == "__main__":
    # Simple test - collect one gesture
    gesture = generate_single_gesture()
    print(f"\nGesture shape: {gesture.shape}")
    print(f"First few points: {gesture[:5]}")
