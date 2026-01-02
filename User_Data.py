import json
import os
from datetime import datetime

class UserDataManager:
    def __init__(self, file_path="user_data.json"):
        self.file_path = file_path
        self.users = self._load_users()

    def _load_users(self):
        """Load users from JSON file"""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def _save_users(self):
        """Save users to JSON file"""
        with open(self.file_path, 'w') as f:
            json.dump(self.users, f, indent=4)

    def add_user(self, username, password):
     if username in self.users:
        return False, "Username already exists"

     self.users[username] = {
        'password': password,
        'points': 0,
        'quiz_stats': {'total_attempts': 0, 'correct_answers': 0},
        'activity_log': [],
        'created_recipes': [],
        'completed_events': [],
        'saved_menus': [],
        'inventory': {},
        'leftovers': [],
        'leftover_ingredients': [],
        'generated_recipes': [],
        'friends': [],  # Initialize empty friends list
        'achievements': []
     }
     self._save_users()
     return True, "User created successfully"

    def verify_user(self, username, password):
        """Verify user credentials"""
        if username in self.users:
            if self.users[username]['password'] == password:
                return True, "Login successful"
            return False, "Incorrect password"
        return False, "User not found"

    def get_user_data(self, username):
        """Get user data"""
        return self.users.get(username)

    def update_user_data(self, username, data):
        """Update user data"""
        if username in self.users:
            self.users[username].update(data)
            self._save_users()
            return True, "User data updated"
        return False, "User not found"
    

    def add_friend(self, user, friend):
        """Add friend to user's friend list"""
        if user in self.users and friend in self.users:
            if 'friends' not in self.users[user]:
                self.users[user]['friends'] = []
            if friend not in self.users[user]['friends']:
                self.users[user]['friends'].append(friend)
                self._save_users()
                return True, f"Added {friend} as friend"
        return False, "Failed to add friend"

    def get_leaderboard(self):
        """Get sorted leaderboard of all users"""
        leaderboard = []
        for username, data in self.users.items():
            leaderboard.append({
                'username': username,
                'points': data.get('points', 0),
                'achievements': len(data.get('achievements', [])),
                'quiz_accuracy': self._calculate_accuracy(data.get('quiz_stats', {}))
            })
        return sorted(leaderboard, key=lambda x: (x['points'], x['achievements']), reverse=True)
    
    def _calculate_accuracy(self, quiz_stats):
        total = quiz_stats.get('total_attempts', 0)
        correct = quiz_stats.get('correct_answers', 0)
        return (correct / total * 100) if total > 0 else 0