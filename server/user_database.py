#!/usr/bin/env python3
"""
User Database Manager for Gesture-Based Authentication

Manages user profiles and gesture templates stored in JSON format.
"""

import json
import os
from datetime import datetime
from typing import Optional, Dict, List


class UserDatabase:
    """Manages user data and gesture templates."""

    def __init__(self, db_file="users.json"):
        """
        Initialize user database.

        Args:
            db_file: Path to JSON file storing user data
        """
        self.db_file = db_file
        self.users = self._load_database()

    def _load_database(self) -> Dict:
        """Load user database from JSON file."""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading database: {e}")
                return {}
        return {}

    def _save_database(self):
        """Save user database to JSON file."""
        try:
            with open(self.db_file, 'w') as f:
                json.dump(self.users, f, indent=2)
        except Exception as e:
            print(f"Error saving database: {e}")

    def user_exists(self, username: str) -> bool:
        """Check if user exists in database."""
        return username.lower() in self.users

    def register_user(self, username: str, gesture_list: List) -> bool:
        """
        Register a new user with their gesture samples.

        Args:
            username: User's first name
            gesture_list: List of gesture arrays (numpy arrays converted to lists)
                         Each array is shape (160, 2) with X, Y coordinates

        Returns:
            True if registration successful, False if user already exists
        """
        username_lower = username.lower()

        if self.user_exists(username):
            print(f"Registration failed: User '{username}' already exists")
            return False

        # Convert numpy arrays to lists for JSON serialization
        serializable_gestures = []
        for gesture in gesture_list:
            if hasattr(gesture, 'tolist'):  # numpy array
                serializable_gestures.append(gesture.tolist())
            else:  # already a list
                serializable_gestures.append(gesture)

        self.users[username_lower] = {
            "username": username,  # Keep original capitalization
            "gesture_list": serializable_gestures,
            "num_gestures": len(serializable_gestures),
            "created_at": datetime.now().isoformat(),
            "last_login": None
        }

        self._save_database()
        print(f"User '{username}' registered with {len(serializable_gestures)} gesture samples")
        return True

    def get_gesture_list(self, username: str) -> Optional[List]:
        """
        Get stored gesture list for user.

        Args:
            username: User's first name

        Returns:
            List of gesture arrays or None if user doesn't exist
        """
        username_lower = username.lower()
        if username_lower in self.users:
            import numpy as np
            # Convert lists back to numpy arrays for gesture recognition
            gesture_data = self.users[username_lower].get("gesture_list")
            if gesture_data:
                return [np.array(g) for g in gesture_data]
        return None

    def update_last_login(self, username: str):
        """Update the last login timestamp for user."""
        username_lower = username.lower()
        if username_lower in self.users:
            self.users[username_lower]["last_login"] = datetime.now().isoformat()
            self._save_database()

    def get_user_info(self, username: str) -> Optional[Dict]:
        """Get all information for a user."""
        username_lower = username.lower()
        return self.users.get(username_lower)

    def get_all_users(self) -> List[str]:
        """Get list of all registered usernames."""
        return [user["username"] for user in self.users.values()]


# Test the database
if __name__ == "__main__":
    print("=== User Database Test ===\n")

    db = UserDatabase("test_users.json")

    # Test registration
    print("Registering users...")
    db.register_user("John", [0.1, 0.2, 0.3, 0.4])
    db.register_user("Jane", [0.5, 0.6, 0.7, 0.8])

    # Test duplicate
    print("\nTrying duplicate registration...")
    db.register_user("john", [0.9, 0.8, 0.7, 0.6])  # Should fail (case-insensitive)

    # Test user exists
    print(f"\nJohn exists: {db.user_exists('John')}")
    print(f"Bob exists: {db.user_exists('Bob')}")

    # Test get template
    print(f"\nJohn's template: {db.get_gesture_template('john')}")

    # Test get all users
    print(f"\nAll users: {db.get_all_users()}")

    # Cleanup
    if os.path.exists("test_users.json"):
        os.remove("test_users.json")
        print("\nTest database cleaned up")
