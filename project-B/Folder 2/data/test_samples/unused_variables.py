# Expected Smells:
# - unused_variables (MEDIUM)

"""Unused variable sample for deterministic medium-level maintainability detection."""


def compute_total(values):
    temporary_sum = 0
    never_used_flag = True
    unused_message = "debug-only"

    for value in values:
        temporary_sum += value

    final_total = temporary_sum
    return final_total
