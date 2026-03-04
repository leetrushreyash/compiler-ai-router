from typing import List, Dict, Any

SMELL_SEVERITY = {
    "long_method": "medium",
    "deep_nesting": "medium",
    "nested_loops": "medium",
    "unsafe_eval_exec": "high",
    "hardcoded_secrets": "high",
    "exception_swallowing": "low",
    "duplicate_code_blocks": "low",
    "god_class": "high",
    "feature_envy": "medium",
    "data_class": "low",
}

SMELL_FIX = {
    "long_method": "Refactor into smaller methods or helpers.",
    "deep_nesting": "Reduce nesting by early returns or helper functions.",
    "nested_loops": "Refactor nested loops or use comprehensions/iterators.",
    "unsafe_eval_exec": "Avoid eval/exec; use safer alternatives.",
    "hardcoded_secrets": "Move secrets to environment variables or a secrets manager.",
    "exception_swallowing": "Handle exceptions explicitly or log them.",
    "duplicate_code_blocks": "Deduplicate code by extracting shared functions.",
    "god_class": "Split class responsibilities into smaller cohesive classes.",
    "feature_envy": "Move the method closer to the data it uses or pass data in.",
    "data_class": "Add behavior or consolidate data into richer domain objects.",
}

def rule_based_findings(features: Dict[str, Any], locations: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    findings = []
    locations = locations or {}
    for k, v in features.items():
        if v:
            locs = locations.get(k) or []
            if not locs:
                locs = [-1]
            for ln in locs:
                findings.append({
                    "smell_type": k,
                    "severity": SMELL_SEVERITY.get(k, "medium"),
                    "suggested_fix": SMELL_FIX.get(k, "Refactor"),
                    "confidence": 1.0,
                    "line": ln,
                })
    return findings
