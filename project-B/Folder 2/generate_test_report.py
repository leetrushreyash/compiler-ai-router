"""Generate a detailed JSON test report with actual code smell findings.

Runs the rule engine + code smell detector on all sample files and produces
a report showing:
  - exact source file name
  - line number where the smell occurs
  - the actual source code line
  - the code smell name, severity, CWE, OWASP mapping
  - test suite results grouped by smell
"""
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# ── add project root so src imports work ──
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.rules.rule_engine import RuleEngine
from src.analyzer.static_analyzer import CodeSmellDetector
from src.config import CWE_MAPPING, OWASP_MAPPING, SmellType

# All 7 code smell categories
CODE_SMELL_INFO = {
    "hardcoded_secrets":      {"severity": "HIGH",   "cwe": "CWE-798",  "owasp": "A07:2021 - Identification & Authentication Failures"},
    "sql_injection_risk":     {"severity": "HIGH",   "cwe": "CWE-89",   "owasp": "A03:2021 - Injection"},
    "unsafe_deserialization": {"severity": "HIGH",   "cwe": "CWE-502",  "owasp": "A08:2021 - Software and Data Integrity Failures"},
    "null_pointer_risk":      {"severity": "MEDIUM", "cwe": "CWE-476",  "owasp": "A04:2021 - Insecure Design"},
    "dead_code":              {"severity": "LOW",    "cwe": "CWE-561",  "owasp": "A04:2021 - Insecure Design"},
    "god_object":             {"severity": "MEDIUM", "cwe": "CWE-710",  "owasp": "A04:2021 - Insecure Design"},
    "long_method":            {"severity": "LOW",    "cwe": "CWE-1080", "owasp": "A04:2021 - Insecure Design"},
}

# Keywords in test names → smell type
SMELL_KEYWORDS = {
    "hardcoded": "hardcoded_secrets", "secret": "hardcoded_secrets",
    "password": "hardcoded_secrets", "api_key": "hardcoded_secrets",
    "token": "hardcoded_secrets", "credential": "hardcoded_secrets",
    "sql": "sql_injection_risk", "injection": "sql_injection_risk",
    "deseriali": "unsafe_deserialization", "pickle": "unsafe_deserialization",
    "dead_code": "dead_code", "god_object": "god_object",
    "long_method": "long_method", "null_pointer": "null_pointer_risk",
}


def scan_files(directory: str) -> list:
    """Run rule engine + detector on every .py file and return findings."""
    engine = RuleEngine()
    detector = CodeSmellDetector()
    findings = []

    sample_dir = Path(directory)
    if not sample_dir.exists():
        return findings

    for py_file in sorted(sample_dir.glob("*.py")):
        code = py_file.read_text(encoding="utf-8", errors="ignore")
        filename = py_file.name

        # Rule engine findings (with line/code)
        rule_issues = engine.apply_rules(code, filename)
        for issue in rule_issues:
            info = CODE_SMELL_INFO.get(issue["type"], {})
            findings.append({
                "source_file": filename,
                "line_number": issue["line"],
                "column": issue.get("column", 0),
                "source_code": issue.get("code", ""),
                "code_smell": issue["type"],
                "rule_id": issue.get("rule_id", ""),
                "rule_name": issue.get("name", ""),
                "severity": issue["severity"],
                "confidence": issue["confidence"],
                "description": issue["description"],
                "cwe": info.get("cwe", ""),
                "owasp": info.get("owasp", ""),
            })

        # CodeSmellDetector findings
        detector_issues = detector.detect_smells(code, filename)
        for issue in detector_issues:
            # avoid duplicates that rule engine already caught
            dup = any(
                f["source_file"] == filename
                and f["line_number"] == issue.get("line", 0)
                and f["code_smell"] == issue.get("type", "")
                for f in findings
            )
            if dup:
                continue
            info = CODE_SMELL_INFO.get(issue.get("type", ""), {})
            findings.append({
                "source_file": filename,
                "line_number": issue.get("line", 0),
                "column": issue.get("column", 0),
                "source_code": issue.get("code", ""),
                "code_smell": issue.get("type", "unknown"),
                "rule_id": "",
                "rule_name": issue.get("name", ""),
                "severity": issue.get("severity", info.get("severity", "MEDIUM")),
                "confidence": issue.get("confidence", 0.0),
                "description": issue.get("description", ""),
                "cwe": info.get("cwe", ""),
                "owasp": info.get("owasp", ""),
            })

    return findings


def classify_test(nodeid: str) -> list:
    """Return which smell(s) a test name targets."""
    lower = nodeid.lower()
    matched = []
    for kw, smell in SMELL_KEYWORDS.items():
        if kw in lower and smell not in matched:
            matched.append(smell)
    return matched if matched else ["general"]


def generate_report(json_path: str, samples_dir: str) -> dict:
    """Build the enriched report with real findings + test results."""

    # ── 1. Scan sample files for real code smells ─────────────
    findings = scan_files(samples_dir)

    # Group findings by smell type
    findings_by_smell = {}
    for f in findings:
        smell = f["code_smell"]
        findings_by_smell.setdefault(smell, []).append(f)

    # Group findings by source file
    findings_by_file = {}
    for f in findings:
        findings_by_file.setdefault(f["source_file"], []).append(f)

    # ── 2. Load pytest results ────────────────────────────────
    raw_tests = []
    summary = {}
    duration = 0
    if Path(json_path).exists():
        with open(json_path) as fh:
            raw = json.load(fh)
        raw_tests = raw.get("tests", [])
        summary = raw.get("summary", {})
        duration = raw.get("duration", 0)

    # Enrich each test with smell info
    enriched_tests = []
    for t in raw_tests:
        nodeid = t.get("nodeid", "")
        parts = nodeid.split("::")
        smells = classify_test(nodeid)

        enriched_tests.append({
            "test_id": nodeid,
            "test_file": parts[0] if parts else "",
            "test_class": parts[1] if len(parts) >= 2 else "",
            "test_name": parts[-1] if parts else "",
            "outcome": t.get("outcome", "unknown"),
            "duration_seconds": round(t.get("call", {}).get("duration", 0), 6),
            "code_smells_tested": smells,
        })

    # ── 3. Build the report ───────────────────────────────────
    total_tests = summary.get("total", len(raw_tests))
    passed = summary.get("passed", 0)

    report = {
        "report_title": "ML-Driven Code Smell Detection Compiler — Full Report",
        "generated_at": datetime.now().isoformat(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",

        # ── Test summary ──
        "test_summary": {
            "total_tests": total_tests,
            "passed": passed,
            "failed": summary.get("failed", 0),
            "errors": summary.get("error", 0),
            "skipped": summary.get("skipped", 0),
            "duration_seconds": round(duration, 3),
            "pass_rate": f"{(passed / max(total_tests, 1)) * 100:.1f}%",
        },

        # ── Code smell findings (the main section the user asked for) ──
        "total_smells_found": len(findings),
        "smells_by_severity": {
            "HIGH":   len([f for f in findings if f["severity"] == "HIGH"]),
            "MEDIUM": len([f for f in findings if f["severity"] == "MEDIUM"]),
            "LOW":    len([f for f in findings if f["severity"] == "LOW"]),
        },

        # Per-smell breakdown with findings
        "code_smell_details": {
            smell_name: {
                **info,
                "total_found": len(findings_by_smell.get(smell_name, [])),
                "findings": [
                    {
                        "source_file": f["source_file"],
                        "line_number": f["line_number"],
                        "source_code": f["source_code"],
                        "rule_id": f["rule_id"],
                        "rule_name": f["rule_name"],
                        "confidence": f["confidence"],
                        "description": f["description"],
                    }
                    for f in findings_by_smell.get(smell_name, [])
                ],
            }
            for smell_name, info in CODE_SMELL_INFO.items()
        },

        # Per-file breakdown
        "findings_by_file": {
            fname: {
                "total_issues": len(issues),
                "issues": [
                    {
                        "line_number": f["line_number"],
                        "source_code": f["source_code"],
                        "code_smell": f["code_smell"],
                        "severity": f["severity"],
                        "confidence": f["confidence"],
                        "cwe": f["cwe"],
                        "owasp": f["owasp"],
                        "description": f["description"],
                    }
                    for f in sorted(issues, key=lambda x: x["line_number"])
                ],
            }
            for fname, issues in sorted(findings_by_file.items())
        },

        # All findings flat list
        "all_findings": findings,

        # Test results
        "tests": enriched_tests,
    }

    return report


if __name__ == "__main__":
    pytest_json = "test_results.json"
    samples = str(PROJECT_ROOT / "data" / "test_samples")
    output = "test_results.json"

    # Run pytest first if no JSON exists
    if not Path(pytest_json).exists():
        print("Running pytest first...")
        os.system(f'"{sys.executable}" -m pytest tests/ -v --json-report --json-report-file={pytest_json}')

    report = generate_report(pytest_json, samples)

    with open(output, "w") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))
