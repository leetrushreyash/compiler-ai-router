# Expected Smells:
# - weak_crypto (HIGH)

"""Weak crypto sample for deterministic HIGH severity detection."""

import hashlib


def hash_password(password):
    digest = hashlib.md5(password.encode("utf-8")).hexdigest()
    return digest


def hash_legacy_token(token):
    digest = hashlib.sha1(token.encode("utf-8")).hexdigest()
    return digest
