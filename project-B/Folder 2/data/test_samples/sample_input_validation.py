"""Sample code demonstrating missing input validation."""

def process_user_age(age):
    """Missing input validation - no bounds check."""
    return age * 365  # Age could be negative or extremely large


def parse_config_value(config_dict, key):
    """Missing validation - no type checking."""
    value = config_dict[key]
    return int(value) + 10  # Could raise exception, no validation


def process_file_size(size_str):
    """Missing validation - no format check."""
    size = int(size_str)
    # No check for negative or overflow values
    return size


def set_user_role(user_id, role):
    """Missing validation - no permission check."""
    # No validation that role is valid
    update_database(f"UPDATE users SET role = '{role}' WHERE id = {user_id}")


def process_array_index(array, index):
    """Missing validation - no bounds check."""
    # No check if index is within array bounds
    return array[index]


def parse_url_parameter(param):
    """Missing validation - no sanitization."""
    # URL parameter used directly without sanitization
    return process_query(param)
