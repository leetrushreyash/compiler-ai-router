"""Sample code demonstrating dead code patterns."""

def calculate_total(items):
    """Function with unreachable code."""
    total = sum(items)
    return total
    print("This will never execute")
    return 0


def process_request(request_type):
    """Dead code after early return."""
    if request_type == "admin":
        return "Admin access granted"
        give_admin_privileges()  # Dead code


def validate_input(value):
    """Unreachable exception handler."""
    try:
        return int(value)
        raise ValueError("Invalid value")  # Dead code
    except ValueError:
        pass


redundant_variable = 42
redundant_variable = 100  # Previous assignment is unused


def unused_import_function():
    """Function with unused imports."""
    import json  # Imported but never used
    import os
    return os.getcwd()


def function_never_called():
    """This function is defined but never called."""
    return "Dead code"


if False:
    print("This code block will never execute")
    do_something_important()


def alternative_logic(x):
    """Dead code due to constant condition."""
    if True:
        return x
        return x * 2  # Unreachable
