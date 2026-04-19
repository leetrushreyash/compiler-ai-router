"""Sample code demonstrating race condition vulnerabilities."""

import os
import threading


shared_counter = 0


def increment_counter():
    """Race condition - shared state without locking."""
    global shared_counter
    temp = shared_counter
    temp += 1
    shared_counter = temp  # TOCTOU issue


def check_and_create_file(filename):
    """Race condition - file check-then-act."""
    if not os.path.exists(filename):
        # Between check and create, another thread might create it
        open(filename, 'w').write("data")


def update_user_balance(user_id, amount):
    """Race condition - read-modify-write without locking."""
    balance = get_balance(user_id)
    new_balance = balance + amount
    set_balance(user_id, new_balance)
    # Another thread could modify balance between read and write


class BankAccount:
    """Class with race condition in deposit method."""
    def __init__(self, balance):
        self.balance = balance
    
    def deposit(self, amount):
        """Unsafe deposit - race condition."""
        temp = self.balance
        temp += amount
        self.balance = temp


def delete_and_log(filename):
    """Race condition - file state changes between operations."""
    if os.path.exists(filename):
        # File could be deleted by another process
        with open(filename) as f:
            content = f.read()
    os.remove(filename)
