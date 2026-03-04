"""
Smell Co-occurrence & Interaction Graph (Novelty 2)
====================================================
Analyses how code smells interact at the file and project level.
No existing tool (Pylint, SonarQube, Radon) performs this analysis.

Produces:
  - Correlation matrix   : which smells tend to co-occur
  - Composite risk score  : weighted score considering smell interactions
  - Hotspot ranking       : files ranked by danger
  - Mermaid interaction graph : visual dependency diagram
"""

from __future__ import annotations

import math
from typing import Dict, List, Any, Tuple, Optional

# Defined smell interaction weights (empirically motivated by SE research):
# When two smells co-occur, the combined risk is amplified by this factor.
INTERACTION_WEIGHTS: Dict[Tuple[str, str], float] = {
    ("god_class", "feature_envy"): 1.8,
    ("god_class", "long_method"): 1.6,
    ("god_class", "data_class"): 1.5,
    ("long_method", "deep_nesting"): 1.5,
    ("long_method", "nested_loops"): 1.4,
    ("deep_nesting", "nested_loops"): 1.3,
    ("hardcoded_secrets", "unsafe_eval_exec"): 2.0,  # security-critical
    ("exception_swallowing", "unsafe_eval_exec"): 1.7,
    ("duplicate_code_blocks", "long_method"): 1.4,
    ("feature_envy", "data_class"): 1.6,
}

# Base severity weights per smell
SMELL_BASE_WEIGHT: Dict[str, float] = {
    "long_method": 2.0,
    "deep_nesting": 2.0,
    "nested_loops": 1.5,
    "unsafe_eval_exec": 4.0,
    "hardcoded_secrets": 4.0,
    "exception_swallowing": 1.5,
    "duplicate_code_blocks": 1.5,
    "god_class": 3.5,
    "feature_envy": 2.5,
    "data_class": 1.0,
}


def _pair_key(a: str, b: str) -> Tuple[str, str]:
    """Canonical ordered pair."""
    return (min(a, b), max(a, b))


# ---------------------------------------------------------------------------
# Correlation matrix
# ---------------------------------------------------------------------------

def compute_correlation_matrix(
    all_features: List[Dict[str, Any]],
) -> Dict[str, Dict[str, float]]:
    """
    Given a list of per-file feature dicts ({smell: 0|1}), compute the
    Phi coefficient (Matthews) correlation between every pair of smells.

    Returns a nested dict  smell_a → smell_b → correlation_value.
    """
    smells = sorted(SMELL_BASE_WEIGHT.keys())
    n = len(all_features)
    if n == 0:
        return {s: {t: 0.0 for t in smells} for s in smells}

    # Precompute counts
    counts = {s: sum(1 for f in all_features if f.get(s)) for s in smells}
    joint = {}
    for i, a in enumerate(smells):
        for b in smells[i:]:
            joint[_pair_key(a, b)] = sum(
                1 for f in all_features if f.get(a) and f.get(b)
            )

    matrix: Dict[str, Dict[str, float]] = {}
    for a in smells:
        matrix[a] = {}
        for b in smells:
            if a == b:
                matrix[a][b] = 1.0
                continue
            n11 = joint.get(_pair_key(a, b), 0)
            n10 = counts[a] - n11
            n01 = counts[b] - n11
            n00 = n - n11 - n10 - n01
            denom = math.sqrt(
                (n11 + n10) * (n11 + n01) * (n00 + n10) * (n00 + n01)
            )
            if denom == 0:
                phi = 0.0
            else:
                phi = (n11 * n00 - n10 * n01) / denom
            matrix[a][b] = round(phi, 4)
    return matrix


# ---------------------------------------------------------------------------
# Composite risk score
# ---------------------------------------------------------------------------

def compute_risk_score(features: Dict[str, Any]) -> float:
    """
    Weighted risk score for a single file.  Takes into account:
      1. Base severity of each present smell
      2. Interaction amplification when co-occurring smells are present
    """
    present = [s for s, v in features.items() if v and s in SMELL_BASE_WEIGHT]
    if not present:
        return 0.0

    # Base score
    base = sum(SMELL_BASE_WEIGHT.get(s, 1.0) for s in present)

    # Interaction amplification
    amplification = 1.0
    for i, a in enumerate(present):
        for b in present[i + 1:]:
            key = _pair_key(a, b)
            w = INTERACTION_WEIGHTS.get(key, 1.0)
            amplification *= w

    score = base * amplification
    # Normalise to 0-100 scale (cap at 100)
    normalised = min(100.0, score * 2.5)
    return round(normalised, 2)


# ---------------------------------------------------------------------------
# Hotspot ranking
# ---------------------------------------------------------------------------

def rank_hotspots(
    file_features: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Given {filename: features_dict}, return files ranked by descending risk.
    Each entry: {file, risk_score, smell_count, smells_present}.
    """
    ranked = []
    for path, features in file_features.items():
        present = [s for s, v in features.items() if v and s in SMELL_BASE_WEIGHT]
        ranked.append({
            "file": path,
            "risk_score": compute_risk_score(features),
            "smell_count": len(present),
            "smells_present": present,
        })
    ranked.sort(key=lambda x: x["risk_score"], reverse=True)
    return ranked


# ---------------------------------------------------------------------------
# Mermaid graph generation
# ---------------------------------------------------------------------------

def generate_interaction_graph(
    all_features: List[Dict[str, Any]],
    threshold: float = 0.15,
) -> str:
    """
    Generate a Mermaid-syntax graph showing smell co-occurrence relationships.
    Edges are drawn between smells whose Phi correlation exceeds `threshold`.
    """
    matrix = compute_correlation_matrix(all_features)
    smells = sorted(matrix.keys())

    lines = ["graph LR"]
    # Nodes with styling
    for s in smells:
        weight = SMELL_BASE_WEIGHT.get(s, 1.0)
        if weight >= 3.5:
            lines.append(f'    {s}["{s}"]:::high')
        elif weight >= 2.0:
            lines.append(f'    {s}["{s}"]:::medium')
        else:
            lines.append(f'    {s}["{s}"]:::low')

    # Edges
    seen = set()
    for a in smells:
        for b in smells:
            if a >= b:
                continue
            pair = _pair_key(a, b)
            if pair in seen:
                continue
            seen.add(pair)
            phi = matrix[a][b]
            if abs(phi) >= threshold:
                w = INTERACTION_WEIGHTS.get(pair, 1.0)
                label = f"{phi:+.2f}"
                if w > 1.0:
                    lines.append(f'    {a} =="x{w} | {label}"==> {b}')
                else:
                    lines.append(f'    {a} --"{label}"--> {b}')

    # Styling
    lines.append("    classDef high fill:#ff6b6b,stroke:#c0392b,color:#fff")
    lines.append("    classDef medium fill:#f9ca24,stroke:#f39c12,color:#333")
    lines.append("    classDef low fill:#6ab04c,stroke:#27ae60,color:#fff")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Full analysis
# ---------------------------------------------------------------------------

def full_correlation_analysis(
    file_features: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Run the complete co-occurrence analysis pipeline.

    Parameters
    ----------
    file_features : {filename: {smell: 0|1, ...}, ...}

    Returns
    -------
    dict with keys:
      - correlation_matrix : nested dict
      - hotspots           : ranked list of files
      - interaction_graph  : Mermaid-syntax string
      - summary            : aggregate statistics
    """
    all_feats = list(file_features.values())

    matrix = compute_correlation_matrix(all_feats)
    hotspots = rank_hotspots(file_features)
    graph = generate_interaction_graph(all_feats)

    # Summary statistics
    total_files = len(all_feats)
    smell_totals = {}
    for s in SMELL_BASE_WEIGHT:
        smell_totals[s] = sum(1 for f in all_feats if f.get(s))

    # Top co-occurring pairs
    top_pairs = []
    smells = sorted(SMELL_BASE_WEIGHT.keys())
    for i, a in enumerate(smells):
        for b in smells[i + 1:]:
            co_count = sum(1 for f in all_feats if f.get(a) and f.get(b))
            if co_count > 0:
                top_pairs.append({
                    "pair": [a, b],
                    "co_occurrence_count": co_count,
                    "correlation": matrix[a][b],
                    "interaction_weight": INTERACTION_WEIGHTS.get(_pair_key(a, b), 1.0),
                })
    top_pairs.sort(key=lambda x: x["co_occurrence_count"], reverse=True)

    avg_risk = sum(h["risk_score"] for h in hotspots) / max(1, len(hotspots))

    return {
        "correlation_matrix": matrix,
        "hotspots": hotspots,
        "interaction_graph_mermaid": graph,
        "summary": {
            "total_files_analyzed": total_files,
            "smell_totals": smell_totals,
            "top_co_occurring_pairs": top_pairs[:10],
            "average_risk_score": round(avg_risk, 2),
            "max_risk_score": hotspots[0]["risk_score"] if hotspots else 0,
        },
    }
