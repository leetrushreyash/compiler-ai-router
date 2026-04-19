"""Sample code demonstrating weak cryptography practices."""

import hashlib
import random


def hash_password(password):
    """Vulnerable password hashing - no salt."""
    # MD5 is weak for passwords
    return hashlib.md5(password.encode()).hexdigest()


def encrypt_sensitive_data(data):
    """Vulnerable encryption - hardcoded key."""
    from cryptography.fernet import Fernet
    key = "hardcoded_key_12345678901234567"
    cipher = Fernet(key)
    return cipher.encrypt(data.encode())


def generate_token():
    """Vulnerable token generation - weak randomness."""
    # Random module is not cryptographically secure
    return str(random.randint(0, 99999))


def hash_user_id(user_id):
    """Vulnerable hashing - insecure algorithm."""
    # Using simple hash function
    return hash(user_id)


def create_session_id():
    """Vulnerable session ID - predictable."""
    import time
    return hashlib.md5(str(time.time()).encode()).hexdigest()
