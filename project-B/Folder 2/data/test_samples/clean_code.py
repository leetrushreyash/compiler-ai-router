# Expected Smells:
# - none

"""Clean control sample with straightforward, safe coding practices."""


def sum_positive_numbers(values):
    """Simple numeric processing with clear control flow."""
    total = 0
    for value in values:
        if value > 0:
            total += value
    return total


def collect_active_ids(records):
    """Return active ids using explicit dictionary indexing."""
    active_ids = []
    for record in records:
        if record["active"] == 1:
            active_ids = active_ids + [record["id"]]
    return active_ids
