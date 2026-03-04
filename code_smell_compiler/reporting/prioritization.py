"""
Smell prioritization & triage utility (Novelty 4)
=================================================
Ranks findings by a blended score that accounts for:
  - Declared severity (low/medium/high)
  - Smell intrinsic weight (from co-occurrence research)
  - Model confidence
  - File-level risk (if features provided)

Output: sorted findings with `priority_score`, `priority_band`, and rationale.
"""
from __future__ import annotations

from typing import Dict, List, Any

from code_smell_compiler.correlation.analyzer import SMELL_BASE_WEIGHT, compute_risk_score

# Severity levels mapped to numeric weight for scoring
SEVERITY_WEIGHT: Dict[str, float] = {"low": 1.0, "medium": 2.0, "high": 3.0}


def _priority_band(score: float) -> str:
    if score >= 9.0:
        return "P0-critical"
    if score >= 6.0:
        return "P1-high"
    if score >= 3.0:
        return "P2-medium"
    return "P3-low"


def _priority_reason(finding: Dict[str, Any], score: float, file_risk: float, smell_weight: float) -> str:
    severity = finding.get("severity", "medium")
    conf = round(float(finding.get("confidence", 0.5)), 3)
    parts = [f"severity={severity}", f"confidence={conf}"]
    if smell_weight != 1.0:
        parts.append(f"smell_weight={smell_weight}")
    if file_risk > 0:
        parts.append(f"file_risk={file_risk}")
    parts.append(f"score={score}")
    return "; ".join(parts)


def _compute_score(finding: Dict[str, Any], file_risk: float) -> float:
    """Compute blended priority score for a single finding."""
    severity_w = SEVERITY_WEIGHT.get(finding.get("severity", "medium"), 2.0)
    smell_w = SMELL_BASE_WEIGHT.get(finding.get("smell_type", ""), 1.0)
    conf = max(0.0, min(1.0, float(finding.get("confidence", 0.5))))

    # Base combines severity and intrinsic smell weight; confidence scales it.
    base = (severity_w + 0.6 * smell_w) * (0.7 + 0.6 * conf)

    # File risk amplifies: risk in [0,100] → multiplier in [1,2]
    risk_multiplier = 1.0 + (max(file_risk, 0.0) / 100.0)

    return round(base * risk_multiplier, 3), smell_w


def prioritize_findings(
    findings: List[Dict[str, Any]],
    file_features: Dict[str, Dict[str, Any]] | None = None,
) -> List[Dict[str, Any]]:
    """
    Attach priority metadata and return findings sorted by descending priority.

    Parameters
    ----------
    findings : list of finding dicts
    file_features : optional {filename: features} for file-level risk boosting
    """
    per_file_risk: Dict[str, float] = {}
    if file_features:
        per_file_risk = {path: compute_risk_score(feats) for path, feats in file_features.items()}

    prioritized = []
    for f in findings:
        file_risk = per_file_risk.get(f.get("file", ""), 0.0)
        score, smell_w = _compute_score(f, file_risk)
        prioritized.append({
            **f,
            "priority_score": score,
            "priority_band": _priority_band(score),
            "priority_reason": _priority_reason(f, score, file_risk, smell_w),
        })

    prioritized.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
    return prioritized
