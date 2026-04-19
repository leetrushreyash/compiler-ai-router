"""Demo runner for test samples covering newly added smell detections."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from src.analyzer.feature_extractor import FeatureExtractor
from src.autofix import AutoFixer
from src.ml.model_manager import ModelManager
from src.rules.rule_engine import HybridAnalyzer
from src.rules.rule_engine import RuleEngine
from src.webapp import AnalyzerService


ROOT = Path(__file__).resolve().parent
SAMPLES_DIR = ROOT / "data" / "test_samples"
USE_ML = True


def severity_breakdown(issues: List[Dict]) -> Dict[str, int]:
    breakdown = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    for issue in issues:
        sev = str(issue.get("severity", "INFO")).upper()
        if sev not in breakdown:
            breakdown[sev] = 0
        breakdown[sev] += 1
    return breakdown


def print_section(title: str):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def run_demo():
    if not SAMPLES_DIR.exists():
        raise FileNotFoundError(f"Samples folder not found: {SAMPLES_DIR}")

    rule_engine = RuleEngine()
    feature_extractor = FeatureExtractor()
    fixer = AutoFixer()
    analyzer_service = AnalyzerService()

    model_manager = None
    model_cache = {}

    if USE_ML:
        try:
            model_manager = ModelManager(str(ROOT / "data" / "models"))
        except Exception as exc:
            print(f"[WARN] ML selector unavailable: {exc}")
            model_manager = None

    sample_files = sorted(
        [path for path in SAMPLES_DIR.glob("*.py") if path.name != "__init__.py"]
    )

    print_section("Demo: New Test Samples")
    print(f"Found {len(sample_files)} sample file(s) in {SAMPLES_DIR}")

    for sample_path in sample_files:
        code = sample_path.read_text(encoding="utf-8")
        features = feature_extractor.extract_features(code)
        issues = rule_engine.apply_rules(code, sample_path.name)

        selected_model = "N/A"
        if USE_ML and model_manager is not None:
            try:
                recommendation = analyzer_service.recommend_model(
                    code, sample_path.name, features
                )
                selected_model = recommendation.get("recommended_model", "randomforest")

                if selected_model not in model_cache:
                    model_manager.load(selected_model)
                    model_cache[selected_model] = model_manager.get_model(selected_model)

                ml_model = model_cache.get(selected_model)
                if ml_model is not None:
                    hybrid = HybridAnalyzer(rule_engine, ml_model)
                    issues.extend(hybrid._apply_ml(features, sample_path.name))
            except Exception as exc:
                selected_model = f"ML unavailable ({exc})"

        smell_types = sorted({issue.get("type", "unknown") for issue in issues})
        breakdown = severity_breakdown(issues)
        autofix_available = any(issue.get("type") in fixer.fixers for issue in issues)

        print("\n" + "-" * 78)
        print(f"File: {sample_path.name}")
        print(f"Detected smells ({len(smell_types)}): {', '.join(smell_types) if smell_types else 'none'}")
        print(
            "Severity breakdown: "
            f"HIGH={breakdown.get('HIGH', 0)} | "
            f"MEDIUM={breakdown.get('MEDIUM', 0)} | "
            f"LOW={breakdown.get('LOW', 0)}"
        )
        print(f"Selected ML model: {selected_model}")
        print(f"Autofix available: {'yes' if autofix_available else 'no'}")

    print_section("Autofix Before/After Demo")
    for target in ("hardcoded_secret.py", "weak_crypto.py"):
        path = SAMPLES_DIR / target
        if not path.exists():
            continue

        original = path.read_text(encoding="utf-8")
        target_issues = rule_engine.apply_rules(original, target)
        fixed = fixer.generate_fixed_code(original, target_issues)

        print("\n" + "-" * 78)
        print(f"File: {target}")
        print("Before snippet:")
        print("\n".join(original.splitlines()[:8]))
        print("\nAfter snippet:")
        print("\n".join(fixed.splitlines()[:8]))


if __name__ == "__main__":
    run_demo()
