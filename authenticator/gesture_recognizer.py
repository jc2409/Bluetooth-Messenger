#!/usr/bin/env python3
"""
Gesture Recognizer for Authentication Pipeline

Integrates with generate_gesture.py and authenticate_gesture.py
for real MPU6050 sensor-based gesture recognition.
"""

try:
    import numpy as np
    from generate_gesture import generate_single_gesture
    from authenticate_gesture import authenticate_against_gestures
    REAL_GESTURE_AVAILABLE = True
    print("✓ Real gesture modules loaded successfully")
except ImportError as e:
    print(f"❌ Failed to import real gesture modules: {e}")
    print("Falling back to DUMMY MODE for testing")
    REAL_GESTURE_AVAILABLE = False
    import time
    import random


class GestureRecognizer:
    """Gesture recognizer - uses real MPU6050 if available, otherwise dummy mode."""

    def __init__(self):
        self.real_mode = REAL_GESTURE_AVAILABLE

        if self.real_mode:
            print("Gesture Recognizer initialized (MPU6050 MODE)")
            print("Using real sensor with DTW authentication")
        else:
            print("Gesture Recognizer initialized (DUMMY MODE)")
            print("Install gesture modules to use real authentication")

    def register_gesture(self, username, num_samples=3):
        """
        Register a new user by collecting multiple gesture samples.

        Args:
            username: User's first name
            num_samples: Number of gesture samples to collect (default 3)

        Returns:
            tuple: (gesture_list, success)
                - gesture_list: List of numpy arrays (160, 2) for each sample
                - success: True if all samples collected successfully
        """
        if self.real_mode:
            # Real MPU6050 mode
            print(f"\n=== Registering gestures for {username} ===")
            print(f"Will collect {num_samples} gesture samples")

            gesture_list = []

            for i in range(num_samples):
                try:
                    print(f"\n--- Sample {i+1}/{num_samples} ---")
                    gesture_array = generate_single_gesture(countdown=0)  # No countdown - handled by BLE

                    # Verify shape is correct (160, 2)
                    if gesture_array.shape != (160, 2):
                        print(f"❌ Invalid gesture shape: {gesture_array.shape}")
                        return None, False

                    gesture_list.append(gesture_array)
                    print(f"✓ Sample {i+1} recorded successfully")

                except Exception as e:
                    print(f"❌ Error recording gesture {i+1}: {e}")
                    return None, False

            print(f"\n✅ Registration complete: {len(gesture_list)} gestures recorded")
            return gesture_list, True
        else:
            # Dummy mode for testing
            print(f"DUMMY: Registering {username} (simulating {num_samples} samples)")
            time.sleep(2)
            import numpy as np
            # Create dummy gesture data
            gesture_list = [np.random.rand(160, 2) for _ in range(num_samples)]
            print(f"DUMMY: Registration complete")
            return gesture_list, True

    def verify_gesture(self, username, stored_gestures):
        """
        Verify user by comparing new gesture against stored gestures.

        Args:
            username: User's first name
            stored_gestures: List of numpy arrays from registration

        Returns:
            tuple: (match, confidence)
                - match: True if authentication passed (majority vote)
                - confidence: Ratio of passed gestures (0.0 to 1.0)
        """
        if self.real_mode:
            # Real MPU6050 mode
            print(f"\n=== Authenticating {username} ===")
            print(f"Comparing against {len(stored_gestures)} stored gestures")

            try:
                # Use authenticate_against_gestures which handles recording and comparison
                is_authenticated, results = authenticate_against_gestures(stored_gestures, countdown=0)  # No countdown - handled by BLE

                # Calculate confidence as ratio of passed gestures
                passed_count = results.get('passed_count', 0)
                total_count = results.get('total_count', 1)
                confidence = passed_count / total_count if total_count > 0 else 0.0

                print(f"\n{'✅ AUTHENTICATED' if is_authenticated else '❌ FAILED'}")
                print(f"Confidence: {confidence:.2%} ({passed_count}/{total_count} passed)")

                return is_authenticated, confidence

            except Exception as e:
                print(f"❌ Error during verification: {e}")
                return False, 0.0
        else:
            # Dummy mode for testing - 70% success rate
            print(f"DUMMY: Verifying {username}")
            time.sleep(2)
            success = random.random() > 0.3
            confidence = random.uniform(0.6, 0.95) if success else random.uniform(0.3, 0.6)
            print(f"DUMMY: {'PASS' if success else 'FAIL'} ({confidence:.2f})")
            return success, confidence

    def get_sensor_status(self):
        """Check if MPU6050 sensor is available."""
        if self.real_mode:
            try:
                from sensor_collector import SensorCollector
                return True
            except Exception as e:
                print(f"Sensor not available: {e}")
                return False
        else:
            return True  # Dummy mode always "available"
