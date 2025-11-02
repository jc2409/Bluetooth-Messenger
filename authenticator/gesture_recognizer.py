#!/usr/bin/env python3
"""
Dummy Gesture Recognizer for Testing Authentication Pipeline

This is a placeholder that simulates gesture recognition.
Replace with actual implementation later.
"""

import time
import random
import math


class GestureRecognizer:
    """Dummy gesture recognizer for testing authentication flow."""

    def __init__(self):
        print("Gesture Recognizer initialized (DUMMY MODE)")

    def start_recording(self, duration_seconds=4.0):
        """Simulate recording for specified duration."""
        print(f"Recording gesture for {duration_seconds} seconds...")
        time.sleep(duration_seconds)
        # Return dummy sensor data
        return [{"data": "dummy"} for _ in range(int(duration_seconds * 50))]

    def register_gesture(self, username, sensor_data):
        """Create a dummy gesture template."""
        template = [random.random() for _ in range(10)]  # Dummy feature vector
        print(f"Registered gesture for {username}")
        return template, True

    def verify_gesture(self, username, sensor_data, stored_template):
        """Randomly return success/failure for testing."""
        # 70% chance of success for testing
        success = random.random() > 0.3
        confidence = random.uniform(0.6, 0.95) if success else random.uniform(0.3, 0.6)
        print(f"Verify {username}: {'PASS' if success else 'FAIL'} ({confidence:.2f})")
        return success, confidence

    def get_sensor_status(self):
        """Always return True for dummy."""
        return True
