# Expected Smells:
# - deep_nesting (MEDIUM)

"""Deep nesting sample for deterministic MEDIUM severity detection."""


def evaluate_orders(orders):
    approved = []
    for order in orders:
        if order.get("active"):
            for item in order.get("items", []):
                if item.get("price", 0) > 0:
                    for tag in item.get("tags", []):
                        if tag.startswith("priority"):
                            approved.append((order.get("id"), item.get("name"), tag))
    return approved
