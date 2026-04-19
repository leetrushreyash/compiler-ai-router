"""Sample clean code with best practices."""

import os
from typing import Optional, List, Dict
from dataclasses import dataclass


# Use environment variables for configuration
API_KEY = os.getenv('API_KEY')
DB_PASSWORD = os.getenv('DB_PASSWORD')


@dataclass
class User:
    """Represents a user."""
    username: str
    email: str


def authenticate_user(username: str, password: str) -> Optional[User]:
    """
    Authenticate user with parameterized query.
    
    Args:
        username: User's username
        password: User's password
        
    Returns:
        User object if authentication succeeds, None otherwise
    """
    # Use parameterized query to prevent SQL injection
    query = "SELECT * FROM users WHERE username = %s AND password = %s"
    user_data = execute_query(query, (username, password))
    
    if user_data:
        return User(username=user_data[0], email=user_data[1])
    
    return None


def process_json_config(config_json: str) -> Dict:
    """
    Process configuration with safe deserialization.
    
    Args:
        config_json: JSON configuration string
        
    Returns:
        Parsed configuration dictionary
    """
    import json
    # Use JSON for safe deserialization instead of pickle
    return json.loads(config_json)


def get_user_email(user: Optional[Dict]) -> Optional[str]:
    """
    Safely get user email with null checks.
    
    Args:
        user: User dictionary
        
    Returns:
        Email address or None if not available
    """
    if user is None:
        return None
    
    profile = user.get('profile')
    if profile is None:
        return None
    
    email_info = profile.get('email')
    if email_info is None:
        return None
    
    return email_info.get('address')


def calculate_sum(x: int, y: int) -> int:
    """
    Calculate sum of two numbers.
    
    Args:
        x: First number
        y: Second number
        
    Returns:
        Sum of x and y
    """
    return x + y


class UserAuthenticator:
    """Handles user authentication only - single responsibility."""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user."""
        return authenticate_user(username, password)
    
    def validate_password(self, password: str) -> bool:
        """Validate password strength."""
        return len(password) >= 8


class UserRepository:
    """Handles user database operations."""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def create_user(self, username: str, email: str) -> User:
        """Create a new user."""
        query = "INSERT INTO users VALUES (%s, %s)"
        self.db.execute(query, (username, email))
        return User(username=username, email=email)
    
    def get_user(self, username: str) -> Optional[User]:
        """Get user by username."""
        query = "SELECT username, email FROM users WHERE username = %s"
        result = self.db.execute(query, (username,))
        return User(*result) if result else None


def validate_and_process(items: List[str]) -> List[str]:
    """
    Validate and process list of items.
    
    Args:
        items: List of items to process
        
    Returns:
        Processed items
    """
    validated = []
    
    for item in items:
        if item and len(item) > 0:
            validated.append(item.strip())
    
    return validated


# Helper function
def execute_query(query: str, params: tuple = ()) -> Optional[List]:
    """Execute database query with parameters."""
    # This would use parameterized queries in production
    pass
