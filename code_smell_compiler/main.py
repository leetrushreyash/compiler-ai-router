import sys
import os
import json
from pathlib import Path
import argparse
from code_smell_compiler.parser.parser import parse_file_to_ast
from code_smell_compiler.feature_extraction.extractor import extract_features
from code_smell_compiler.static_analyzer.rule_based import rule_based_findings
from code_smell_compiler.ml_model.model_utils import load_models
from code_smell_compiler.reporting.report import format_finding, make_report
from code_smell_compiler.reporting.prioritization import prioritize_findings

# --- Novelty imports ---
from code_smell_compiler.refactoring.engine import generate_refactorings
from code_smell_compiler.correlation.analyzer import full_correlation_analysis
from code_smell_compiler.ml_model.explainable import explain_prediction


def analyze_file(path: Path, models_obj=None, enable_refactoring=False):
    """Analyze a single file and return (findings, features, refactorings, explanations)."""
    tree, src = parse_file_to_ast(str(path))
    features, locations = extract_features(tree)
    findings = []
    refactorings = []
    explanations = []

    # ── Rule-based findings (include exact lines) ──
    rb = rule_based_findings(features, locations)
    for r in rb:
        ln = r.get("line", 1)
        findings.append(format_finding(str(path), ln, r["smell_type"], r["severity"], r["confidence"], r["suggested_fix"]))

    # ── ML-based findings with explainability (Novelty 3) ──
    if models_obj is not None:
        scaler = models_obj.get('scaler')
        rf = models_obj.get('rf')
        feats_order = models_obj.get('features')
        try:
            import pandas as pd
            df = pd.DataFrame([features])
            df = df.reindex(columns=feats_order, fill_value=0)
            xs = scaler.transform(df)
        except Exception:
            x = [features.get(f, 0) for f in feats_order]
            xs = scaler.transform([x])

        # Standard RF predictions
        probs_rf = rf.predict_proba(xs)
        for i, feat in enumerate(feats_order):
            try:
                prob = float(probs_rf[i][0][1])
            except Exception:
                prob = 0.0
            if prob > 0.5:
                locs = locations.get(feat) or []
                ln = locs[0] if locs else 1
                findings.append(format_finding(str(path), ln, feat, "medium", prob, "See rule-based suggested fix."))

        # SHAP-based explanations (Novelty 3)
        explanations = explain_prediction(features, models_obj)

    # ── Auto-refactoring (Novelty 1) ──
    if enable_refactoring:
        refactorings = generate_refactorings(src, features, locations)

    return findings, features, refactorings, explanations


def main():
    parser = argparse.ArgumentParser(
        description="ML-Driven Code Smell Detection Compiler with Auto-Refactoring & Explainability"
    )
    parser.add_argument("path", help="file or folder to analyze")
    parser.add_argument("--use-ml", action="store_true", help="Enable ML-based predictions")
    parser.add_argument("--refactor", action="store_true", help="[Novelty 1] Generate auto-refactoring patches")
    parser.add_argument("--correlate", action="store_true", help="[Novelty 2] Run smell co-occurrence analysis")
    parser.add_argument("--explain", action="store_true", help="[Novelty 3] Show SHAP-based ML explanations")
    parser.add_argument("--prioritize", action="store_true", help="[Novelty 4] Prioritize smells with risk-aware triage")
    parser.add_argument("--output", type=str, default=None, help="Write full report to this JSON file")
    args = parser.parse_args()

    target = Path(args.path)
    models_obj = None
    if args.use_ml or args.explain:
        models_obj = load_models()

    all_findings = []
    all_features = {}      # {filename: features_dict}
    all_refactorings = []
    all_explanations = []
    priority_ranking = []

    files = list(target.rglob("*.py")) if target.is_dir() else [target]

    for p in files:
        findings, features, refactorings, explanations = analyze_file(
            p, models_obj, enable_refactoring=args.refactor
        )
        all_findings.extend(findings)
        all_features[str(p)] = features
        if refactorings:
            for r in refactorings:
                r["file"] = str(p)
            all_refactorings.extend(refactorings)
        if explanations:
            for e in explanations:
                e["file"] = str(p)
            all_explanations.extend(explanations)

    # ── Build full report ──
    report: dict = {"findings": all_findings}

    # Novelty 1: Auto-refactoring
    if args.refactor:
        report["refactorings"] = all_refactorings
        print(f"\n{'='*60}")
        print(f"  AUTO-REFACTORING ENGINE  ({len(all_refactorings)} patches generated)")
        print(f"{'='*60}")
        for r in all_refactorings:
            print(f"\n[{r['smell_type']}] {r.get('file', '?')} (lines {r['line_start']}-{r['line_end']})")
            print(f"  {r['description']}")
            print(f"  Diff:\n{r['diff']}")

    # Novelty 2: Correlation analysis
    if args.correlate and len(all_features) > 0:
        correlation_report = full_correlation_analysis(all_features)
        report["correlation_analysis"] = correlation_report
        summary = correlation_report["summary"]
        print(f"\n{'='*60}")
        print(f"  SMELL CO-OCCURRENCE ANALYSIS  ({summary['total_files_analyzed']} files)")
        print(f"{'='*60}")
        print(f"  Average risk score : {summary['average_risk_score']}")
        print(f"  Max risk score     : {summary['max_risk_score']}")
        print(f"  Smell totals       : {json.dumps(summary['smell_totals'], indent=4)}")
        if summary["top_co_occurring_pairs"]:
            print(f"  Top co-occurring pairs:")
            for pair in summary["top_co_occurring_pairs"][:5]:
                print(f"    {pair['pair'][0]} + {pair['pair'][1]}: "
                      f"count={pair['co_occurrence_count']}, "
                      f"corr={pair['correlation']:.3f}, "
                      f"interaction_weight={pair['interaction_weight']}")
        print(f"\n  Hotspot files (top 5):")
        for h in correlation_report["hotspots"][:5]:
            print(f"    {h['file']}: risk={h['risk_score']}, smells={h['smells_present']}")
        print(f"\n  Mermaid Interaction Graph:")
        print(correlation_report["interaction_graph_mermaid"])

    # Novelty 3: Explainable ML
    if args.explain and all_explanations:
        report["ml_explanations"] = all_explanations
        print(f"\n{'='*60}")
        print(f"  EXPLAINABLE ML PREDICTIONS  ({len(all_explanations)} explanations)")
        print(f"{'='*60}")
        for e in all_explanations:
            print(f"\n  [{e['smell_type']}] {e.get('file', '?')} — prob={e['probability']:.3f} ({e['prediction_source']})")
            print(f"    {e['explanation_text']}")
            if e.get("shap_explanation"):
                print(f"    SHAP contributions:")
                for s in e["shap_explanation"][:3]:
                    print(f"      {s['feature']}={s['value']}  →  impact={s['shap_value']:+.4f} ({s['direction']})")

    # Novelty 4: Smell prioritization
    if args.prioritize and all_findings:
        priority_ranking = prioritize_findings(all_findings, all_features)
        report["prioritized_findings"] = priority_ranking
        print(f"\n{'='*60}")
        print(f"  PRIORITIZED FINDINGS  (top {min(10, len(priority_ranking))} of {len(priority_ranking)})")
        print(f"{'='*60}")
        for p in priority_ranking[:10]:
            print(f"\n  [{p['priority_band']}] {p['smell_type']} @ {p.get('file', '?')}:{p.get('line_number', '?')}")
            print(f"    score={p['priority_score']}  reason: {p['priority_reason']}")

    # Standard findings output
    print(f"\n{'='*60}")
    print(f"  FINDINGS  ({len(all_findings)} total)")
    print(f"{'='*60}")
    print(make_report(all_findings))

    # Write full report to file
    output_path = args.output or "report.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\nFull report written to: {output_path}")


if __name__ == '__main__':
    main()
