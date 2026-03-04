import json
from typing import List, Dict, Any

def make_report(findings: List[Dict[str, Any]]) -> str:
    return json.dumps(findings, indent=2)

def format_finding(file: str, line: int, smell_type: str, severity: str, confidence: float, suggested_fix: str) -> Dict[str, Any]:
    return {
        "file": file,
        "line_number": line,
        "smell_type": smell_type,
        "severity": severity,
        "confidence": round(float(confidence), 3),
        "suggested_fix": suggested_fix,
    }
