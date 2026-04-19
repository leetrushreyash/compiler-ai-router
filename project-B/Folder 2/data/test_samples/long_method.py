# Expected Smells:
# - long_method (LOW)
# - duplicate_code (LOW)

"""Long method sample (>30 lines) for deterministic LOW severity detection."""


def process_records(records):
    """Intentionally long and repetitive processing routine."""
    output = []
    total = 0

    for item in records:
        value = int(item)
        total += value
        output.append(value)

    for item in records:
        value = int(item)
        total += value
        output.append(value)

    for item in records:
        value = int(item)
        total += value
        output.append(value)

    for item in records:
        value = int(item)
        total += value
        output.append(value)

    for item in records:
        value = int(item)
        total += value
        output.append(value)

    for item in records:
        value = int(item)
        total += value
        output.append(value)

    average = total / max(len(output), 1)
    maximum = max(output) if output else 0
    minimum = min(output) if output else 0

    return {
        "count": len(output),
        "total": total,
        "average": average,
        "max": maximum,
        "min": minimum,
    }
