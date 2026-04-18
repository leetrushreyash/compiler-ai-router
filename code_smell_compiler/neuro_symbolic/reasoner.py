from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Tuple


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _confidence_band(score: float) -> str:
    if score >= 0.85:
        return "very_high"
    if score >= 0.7:
        return "high"
    if score >= 0.5:
        return "moderate"
    return "low"


def _build_ml_prob_index(ml_explanations: List[Dict[str, Any]]) -> Dict[Tuple[str, str], float]:
    index: Dict[Tuple[str, str], float] = {}
    for exp in ml_explanations or []:
        file_path = exp.get("file", "")
        smell = exp.get("smell_type", "")
        prob = _clip01(exp.get("probability", 0.0))
        if file_path and smell:
            index[(file_path, smell)] = max(index.get((file_path, smell), 0.0), prob)
    return index


def _avg_positive_corr_with_file_smells(
    smell: str,
    file_features: Dict[str, Any],
    correlation_matrix: Dict[str, Dict[str, float]],
) -> float:
    present = [s for s, v in file_features.items() if v]
    if smell not in correlation_matrix or not present:
        return 0.0

    vals: List[float] = []
    for other in present:
        if other == smell:
            continue
        corr = float(correlation_matrix.get(smell, {}).get(other, 0.0))
        if corr > 0:
            vals.append(corr)

    if not vals:
        return 0.0

    # Map rough correlation range [-1, 1] to [0, 1], but only positive kept.
    return _clip01(sum(vals) / len(vals))


def build_neuro_symbolic_analysis(
    findings: List[Dict[str, Any]],
    all_features: Dict[str, Dict[str, Any]],
    ml_explanations: List[Dict[str, Any]],
    correlation_analysis: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Build a neuro-symbolic reasoning layer by fusing:
      1) symbolic evidence (rule confidence + feature presence)
      2) learned evidence (ML probability from SHAP explanation entries)
      3) contextual evidence (correlation support from co-occurring smells)
    """
    corr_matrix = (correlation_analysis or {}).get("correlation_matrix", {})
    ml_prob_index = _build_ml_prob_index(ml_explanations)

    grouped: Dict[Tuple[str, str], Dict[str, Any]] = defaultdict(dict)
    for f in findings or []:
        key = (f.get("file", ""), f.get("smell_type", ""))
        if not key[0] or not key[1]:
            continue
        existing_conf = float(grouped[key].get("rule_confidence", 0.0))
        grouped[key] = {
            "file": key[0],
            "smell_type": key[1],
            "line_number": f.get("line_number", grouped[key].get("line_number", 1)),
            "rule_confidence": max(existing_conf, _clip01(f.get("confidence", 0.0))),
            "severity": f.get("severity", grouped[key].get("severity", "medium")),
        }

    items: List[Dict[str, Any]] = []
    for (file_path, smell), base in grouped.items():
        file_feats = all_features.get(file_path, {})
        feature_present = bool(file_feats.get(smell, 0))

        symbolic_score = 0.6 * (1.0 if feature_present else 0.0) + 0.4 * base["rule_confidence"]
        ml_score = ml_prob_index.get((file_path, smell), 0.0)
        context_score = _avg_positive_corr_with_file_smells(smell, file_feats, corr_matrix)

        # Adaptive fusion weights:
        # if ML evidence missing, rely more on symbolic + context.
        if ml_score > 0:
            fused = 0.45 * symbolic_score + 0.4 * ml_score + 0.15 * context_score
        else:
            fused = 0.75 * symbolic_score + 0.25 * context_score

        fused = _clip01(fused)

        trace = [
            f"Symbolic: feature_present={feature_present}, rule_confidence={base['rule_confidence']:.3f}",
            f"Neural/ML: probability={ml_score:.3f}",
            f"Context: avg_positive_correlation={context_score:.3f}",
            f"Fusion: neuro_symbolic_confidence={fused:.3f}",
        ]

        items.append({
            "file": file_path,
            "line_number": base["line_number"],
            "smell_type": smell,
            "severity": base["severity"],
            "symbolic_score": round(symbolic_score, 4),
            "ml_score": round(ml_score, 4),
            "context_score": round(context_score, 4),
            "neuro_symbolic_confidence": round(fused, 4),
            "confidence_band": _confidence_band(fused),
            "reasoning_trace": trace,
        })

    items.sort(key=lambda x: x["neuro_symbolic_confidence"], reverse=True)

    summary = {
        "count": len(items),
        "very_high": sum(1 for x in items if x["confidence_band"] == "very_high"),
        "high": sum(1 for x in items if x["confidence_band"] == "high"),
        "moderate": sum(1 for x in items if x["confidence_band"] == "moderate"),
        "low": sum(1 for x in items if x["confidence_band"] == "low"),
        "average_confidence": round(sum(x["neuro_symbolic_confidence"] for x in items) / max(1, len(items)), 4),
    }

    return {
        "method": "weighted_symbolic_ml_context_fusion_v1",
        "items": items,
        "summary": summary,
    }
