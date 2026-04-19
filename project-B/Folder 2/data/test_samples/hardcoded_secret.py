# Expected Smells:
# - hardcoded_secrets (HIGH)

"""Hardcoded credentials sample for deterministic HIGH severity detection."""

api_key = "sk_live_demo_key_123456"
password = "super_secret_password"
auth_token = "abcdefghijklmnopqrstuvwxyz123456"


def connect_service():
    return {
        "api_key": api_key,
        "password": password,
        "auth_token": auth_token,
    }
