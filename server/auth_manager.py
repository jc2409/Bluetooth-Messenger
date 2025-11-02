#!/usr/bin/env python3
"""
Authentication Manager

Handles gesture-based authentication flow with state management.
Requires 2 out of 3 gesture attempts to pass for authentication.
"""

import sys
import os
from enum import Enum
from typing import Optional, Dict, Callable

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'authenticator'))

from gesture_recognizer import GestureRecognizer
from user_database import UserDatabase


class AuthState(Enum):
    """Authentication states for each client."""
    UNAUTHENTICATED = "unauthenticated"
    WAITING_USERNAME = "waiting_username"
    COUNTDOWN = "countdown"
    RECORDING = "recording"
    VERIFYING = "verifying"
    AUTHENTICATED = "authenticated"


class AuthSession:
    """Represents an authentication session for a client."""

    def __init__(self):
        self.state = AuthState.UNAUTHENTICATED
        self.username = None
        self.is_new_user = False
        self.attempts = []  # List of (success, confidence) tuples
        self.current_attempt = 0
        self.max_attempts = 3
        self.gesture_data = None


class AuthenticationManager:
    """Manages authentication flow for all connected clients."""

    def __init__(self, user_db_file="users.json"):
        """
        Initialize authentication manager.

        Args:
            user_db_file: Path to user database JSON file
        """
        self.user_db = UserDatabase(user_db_file)
        self.gesture_recognizer = GestureRecognizer()
        self.sessions: Dict[str, AuthSession] = {}  # device_id -> AuthSession

        print("Authentication Manager initialized")
        print(f"Registered users: {len(self.user_db.get_all_users())}")

    def create_session(self, device_id: str) -> AuthSession:
        """Create a new authentication session for a device."""
        session = AuthSession()
        session.state = AuthState.WAITING_USERNAME
        self.sessions[device_id] = session
        return session

    def get_session(self, device_id: str) -> Optional[AuthSession]:
        """Get existing session for device."""
        return self.sessions.get(device_id)

    def remove_session(self, device_id: str):
        """Remove session when device disconnects."""
        if device_id in self.sessions:
            del self.sessions[device_id]
            print(f"Session removed for device {device_id}")

    def handle_username(self, device_id: str, username: str) -> Dict:
        """
        Handle username submission from client.

        Returns:
            Dictionary with response information:
            {
                'status': 'new_user' | 'existing_user' | 'error',
                'message': str,
                'username': str
            }
        """
        # Always create fresh session for new authentication attempt
        if device_id in self.sessions:
            print(f"Resetting existing session for {device_id}")
            self.remove_session(device_id)

        session = self.create_session(device_id)

        # Validate username
        username = username.strip()
        if not username or len(username) < 2:
            return {
                'status': 'error',
                'message': 'Username must be at least 2 characters'
            }

        session.username = username
        session.is_new_user = not self.user_db.user_exists(username)

        # RESET attempt counter for new authentication
        session.current_attempt = 0
        session.attempts = []

        if session.is_new_user:
            print(f"New user registration: {username}")
            return {
                'status': 'new_user',
                'message': f'Welcome {username}! Please perform your gesture on the device to register.',
                'username': username
            }
        else:
            print(f"Existing user login: {username}")
            return {
                'status': 'existing_user',
                'message': f'Welcome back {username}! Please perform your gesture to sign in.',
                'username': username
            }

    def start_gesture_recording(self, device_id: str, countdown_callback: Optional[Callable] = None) -> bool:
        """
        Start gesture recording for a session.

        Note: The actual countdown and recording happens inside the gesture recognizer functions
        (generate_single_gesture for registration, authenticate_against_gestures for verification)

        Args:
            device_id: Device identifier
            countdown_callback: Optional callback function(seconds_remaining) - NOT USED ANYMORE

        Returns:
            True if session is ready for gesture recording
        """
        session = self.get_session(device_id)
        if not session or not session.username:
            return False

        session.current_attempt += 1
        print(f"\n--- Attempt {session.current_attempt}/{session.max_attempts} for {session.username} ---")

        session.state = AuthState.RECORDING
        # Note: Actual recording happens in process_gesture_attempt()

        return True

    def process_gesture_attempt(self, device_id: str) -> Dict:
        """
        Process a gesture attempt (registration or verification).

        For registration: Collects 3 gesture samples automatically
        For verification: Records 1 gesture and compares against stored gestures

        Returns:
            Dictionary with attempt result:
            {
                'attempt_number': int,
                'success': bool,
                'confidence': float,
                'total_passed': int,
                'total_attempts': int,
                'auth_complete': bool,
                'auth_success': bool,
                'message': str
            }
        """
        session = self.get_session(device_id)
        if not session:
            return {'error': 'No session found'}

        session.state = AuthState.VERIFYING

        if session.is_new_user:
            # Registration: collect 3 gesture samples
            # The gesture_recognizer.register_gesture() handles:
            # - Collecting 3 samples with countdown for each
            # - Recording 4 seconds per sample
            # - Returning list of 3 numpy arrays (160, 2)

            print(f"Starting registration for {session.username}")
            gesture_list, success = self.gesture_recognizer.register_gesture(
                session.username,
                num_samples=3
            )

            if success and gesture_list:
                # Save all 3 gesture samples to database
                self.user_db.register_user(session.username, gesture_list)
                session.state = AuthState.AUTHENTICATED
                self.user_db.update_last_login(session.username)

                return {
                    'attempt_number': 1,
                    'success': True,
                    'confidence': 1.0,
                    'total_passed': 1,
                    'total_attempts': 1,
                    'auth_complete': True,
                    'auth_success': True,
                    'message': f'Registration successful! {len(gesture_list)} gesture samples saved. Welcome {session.username}!'
                }
            else:
                return {
                    'attempt_number': 1,
                    'success': False,
                    'confidence': 0.0,
                    'total_passed': 0,
                    'total_attempts': 1,
                    'auth_complete': True,
                    'auth_success': False,
                    'message': 'Registration failed. Please try again.'
                }

        else:
            # Verification: compare new gesture against all stored gestures
            # The gesture_recognizer.verify_gesture() handles:
            # - Recording 1 new gesture (4 seconds with countdown)
            # - Comparing against all stored gestures using DTW
            # - Returning (match, confidence) based on majority voting

            stored_gestures = self.user_db.get_gesture_list(session.username)

            if not stored_gestures:
                return {'error': 'No gestures found for user'}

            print(f"Verifying attempt {session.current_attempt} for {session.username}")
            print(f"Comparing against {len(stored_gestures)} stored gestures")

            match, confidence = self.gesture_recognizer.verify_gesture(
                session.username,
                stored_gestures
            )

            # Record attempt result
            session.attempts.append((match, confidence))
            total_passed = sum(1 for success, _ in session.attempts if success)

            print(f"Attempt {session.current_attempt}: {'PASS' if match else 'FAIL'} "
                  f"(confidence: {confidence:.2%}) - Total: {total_passed}/{session.current_attempt}")

            # Check if authentication is complete
            auth_complete = session.current_attempt >= session.max_attempts
            auth_success = total_passed >= 2  # Need 2 out of 3

            if auth_complete:
                if auth_success:
                    session.state = AuthState.AUTHENTICATED
                    self.user_db.update_last_login(session.username)
                    message = f'Authentication successful! Welcome back {session.username}! ({total_passed}/3 attempts passed)'
                else:
                    session.state = AuthState.UNAUTHENTICATED
                    message = f'Authentication failed. Only {total_passed}/3 attempts passed. Please try again.'
            else:
                message = f'Attempt {session.current_attempt}: {"PASS" if match else "FAIL"}. Continue...'

            return {
                'attempt_number': session.current_attempt,
                'success': match,
                'confidence': confidence,
                'total_passed': total_passed,
                'total_attempts': session.current_attempt,
                'auth_complete': auth_complete,
                'auth_success': auth_success if auth_complete else False,
                'message': message
            }

    def is_authenticated(self, device_id: str) -> bool:
        """Check if a device is authenticated."""
        session = self.get_session(device_id)
        return session and session.state == AuthState.AUTHENTICATED

    def get_username(self, device_id: str) -> Optional[str]:
        """Get username for an authenticated device."""
        session = self.get_session(device_id)
        if session and session.state == AuthState.AUTHENTICATED:
            return session.username
        return None

    def reset_session(self, device_id: str):
        """Reset authentication session (for retry)."""
        if device_id in self.sessions:
            session = self.sessions[device_id]
            session.state = AuthState.WAITING_USERNAME
            session.username = None
            session.attempts = []
            session.current_attempt = 0
            session.gesture_data = None
            print(f"Session reset for device {device_id}")


# Test the authentication manager
if __name__ == "__main__":
    print("=== Authentication Manager Test ===\n")

    # Create test database
    auth_mgr = AuthenticationManager("test_auth_users.json")

    # Simulate device connection
    device_id = "test_device_001"

    # Test new user registration
    print("--- Test 1: New User Registration ---")
    auth_mgr.create_session(device_id)
    result = auth_mgr.handle_username(device_id, "Alice")
    print(f"Result: {result}")

    if result['status'] == 'new_user':
        auth_mgr.start_gesture_recording(device_id, lambda s: print(f"Countdown: {s}"))
        attempt_result = auth_mgr.process_gesture_attempt(device_id)
        print(f"Registration result: {attempt_result}")

    # Test existing user verification
    print("\n--- Test 2: Existing User Verification ---")
    device_id2 = "test_device_002"
    auth_mgr.create_session(device_id2)
    result = auth_mgr.handle_username(device_id2, "Alice")
    print(f"Result: {result}")

    if result['status'] == 'existing_user':
        # Perform 3 attempts
        for i in range(3):
            auth_mgr.start_gesture_recording(device_id2, lambda s: print(f"Countdown: {s}"))
            attempt_result = auth_mgr.process_gesture_attempt(device_id2)
            print(f"\nAttempt {i+1} result: {attempt_result}")

            if attempt_result.get('auth_complete'):
                print(f"\nFinal result: {'SUCCESS' if attempt_result['auth_success'] else 'FAILED'}")
                break

    # Check authentication status
    print(f"\nDevice {device_id} authenticated: {auth_mgr.is_authenticated(device_id)}")
    print(f"Device {device_id2} authenticated: {auth_mgr.is_authenticated(device_id2)}")

    # Cleanup
    import os
    if os.path.exists("test_auth_users.json"):
        os.remove("test_auth_users.json")
        print("\nTest database cleaned up")
