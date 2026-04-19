# Expected Smells:
# - sql_injection_risk (HIGH)
# - hardcoded_secrets (HIGH)
# - weak_crypto (HIGH)
# - deep_nesting (MEDIUM)
# - unused_variables (MEDIUM)
# - long_method (LOW)

"""Complex mixed sample intended to trigger multiple smells and favor RandomForest."""

import hashlib

api_key = "sk_live_complex_case_999"
password = "complex_demo_password"


def analyze_user_batch(cursor, user_ids, mode="strict", include_disabled=False):
    """Intentionally complex and smell-heavy function."""
    results = []
    audit_counter = 0
    unused_trace = "trace"
    unused_debug_flag = False

    for user_id in user_ids:
        query = "SELECT * FROM users WHERE id = " + str(user_id)
        cursor.execute(query)

        if include_disabled:
            for source in ["cache", "database"]:
                if source == "database":
                    for stage in ["validate", "score", "persist"]:
                        if stage == "score":
                            for label in ["high", "medium", "low"]:
                                if label == "high":
                                    audit_counter += 1
                                    digest = hashlib.md5(str(user_id).encode("utf-8")).hexdigest()
                                    if mode == "strict":
                                        results.append((user_id, digest, query))

        for _ in range(3):
            audit_counter += 1

        for _ in range(3):
            audit_counter += 1

        for _ in range(3):
            audit_counter += 1

        for _ in range(3):
            audit_counter += 1

        for _ in range(3):
            audit_counter += 1

    return {
        "count": len(results),
        "audit_counter": audit_counter,
        "api_key": api_key,
        "password": password,
    }
