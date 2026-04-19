"""Validation tests for newly added demo sample files."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add project root to path for direct imports.
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rules.rule_engine import RuleEngine


SAMPLES_DIR = Path(__file__).parent.parent / "data" / "test_samples"

EXPECTED = {
    "simple_sql_injection.py": {
        "sql_injection_risk": "HIGH",
    },
    "hardcoded_secret.py": {
        "hardcoded_secrets": "HIGH",
    },
    "long_method.py": {
        "long_method": "LOW",
    },
    "god_object.py": {
        "god_object": "MEDIUM",
    },
    "deep_nesting.py": {
        "deep_nesting": "MEDIUM",
    },
    "weak_crypto.py": {
        "weak_crypto": "HIGH",
    },
    "unused_variables.py": {
        "unused_variables": "MEDIUM",
    },
    "complex_mixed_smells.py": {
        "sql_injection_risk": "HIGH",
        "hardcoded_secrets": "HIGH",
        "weak_crypto": "HIGH",
        "deep_nesting": "MEDIUM",
        "long_method": "LOW",
    },
    "clean_code.py": {},
}


def _issue_map(issues):
    result = {}
    for issue in issues:
        smell_type = issue.get("type")
        severity = issue.get("severity")
        if not smell_type:
            continue
        result.setdefault(smell_type, set()).add(severity)
    return result


def test_new_sample_files_exist():
    for filename in EXPECTED:
        assert (SAMPLES_DIR / filename).exists(), f"Missing sample file: {filename}"


@pytest.mark.parametrize("filename,expected", EXPECTED.items())
def test_samples_trigger_expected_smells(filename, expected):
    rule_engine = RuleEngine()
    code = (SAMPLES_DIR / filename).read_text(encoding="utf-8")
    issues = rule_engine.apply_rules(code, filename)

    if filename == "clean_code.py":
        assert len(issues) == 0
        return

    assert len(issues) > 0, f"Expected at least one issue for {filename}"
    detected = _issue_map(issues)

    for smell, severity in expected.items():
        assert smell in detected, f"Missing smell '{smell}' in {filename}"
        assert severity in detected[smell], (
            f"Expected severity '{severity}' for smell '{smell}' in {filename}, "
            f"got {sorted(detected[smell])}"
        )
