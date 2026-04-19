"""Sample code with security best practices."""

import os
import logging
from typing import Optional, Dict, List
from dataclasses import dataclass
from contextlib import contextmanager
import sqlite3


# Configure secure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Use environment variables for sensitive data
DATABASE_URL = os.getenv('DATABASE_URL')
API_KEY = os.getenv('API_KEY')


@dataclass
class User:
    """User data class."""
    username: str
    email: str


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> Optional[User]:
    """
    Securely authenticate user with parameterized queries.
    
    Args:
        username: User's username
        password: User's password
        
    Returns:
        User object if authentication succeeds, None otherwise
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Use parameterized query to prevent SQL injection
        cursor.execute(
            "SELECT username, email FROM users WHERE username = ? AND password_hash = ?",
            (username, hash_password(password))
        )
        result = cursor.fetchone()
        
        if result:
            logger.info(f"User {username} authenticated successfully")
            return User(username=result[0], email=result[1])
        
        logger.warning(f"Failed authentication attempt for {username}")
        return None


def hash_password(password: str) -> str:
    """Hash password securely."""
    import hashlib
    import secrets
    
    salt = secrets.token_hex(16)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${pwdhash.hex()}"


def validate_user_input(user_input: str) -> bool:
    """Validate and sanitize user input."""
    if not user_input:
        return False
    
    if len(user_input) > 255:
        return False
    
    # Check for dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', ';']
    if any(char in user_input for char in dangerous_chars):
        return False
    
    return True


def safe_file_read(filename: str) -> Optional[str]:
    """Safely read file with proper error handling."""
    try:
        # Validate filename to prevent path traversal
        if '..' in filename or filename.startswith('/'):
            logger.error(f"Attempted path traversal: {filename}")
            return None
        
        with open(filename, 'r') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"File not found: {filename}")
        return None
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        return None


def secure_token_generation() -> str:
    """Generate cryptographically secure token."""
    import secrets
    return secrets.token_urlsafe(32)
