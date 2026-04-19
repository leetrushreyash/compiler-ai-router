"""Web frontend for the ML-Driven Code Smell Detection Compiler."""
from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, List
import re

from flask import Flask, jsonify, render_template, request

from .analyzer import FeatureExtractor
from .ml.model_manager import ModelManager
from .rules import RuleEngine
from .rules.rule_engine import HybridAnalyzer
from .agentic_selector import AgenticModelSelector
from .autofix import AutoFixer


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_SAMPLES_DIR = PROJECT_ROOT / "data" / "test_samples"


class AnalyzerService:
    """Encapsulates analysis operations used by the web API."""

    def __init__(self):
        self.rule_engine = RuleEngine()
        self.feature_extractor = FeatureExtractor()
        self.auto_fixer = AutoFixer()
        self._model_cache: Dict[str, Any] = {}

    def _get_model(self, model_name: str):
        if model_name in self._model_cache:
            return self._model_cache[model_name]

        manager = ModelManager(str(PROJECT_ROOT / "data" / "models"))
        manager.load(model_name)
        model = manager.get_model(model_name)
        self._model_cache[model_name] = model
        return model

    def _load_model_metadata(self) -> Dict[str, Dict[str, Any]]:
        metadata: Dict[str, Dict[str, Any]] = {}
        model_root = PROJECT_ROOT / "data" / "models"

        for model_name in ("randomforest", "svm"):
            metadata_path = model_root / f"{model_name}_metadata.json"
            if not metadata_path.exists():
                continue

            try:
                metadata[model_name] = json.loads(metadata_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue

        return metadata

    def _build_agentic_actions(self, features: Dict[str, Any], selected_model: str) -> List[str]:
        actions = [
            f"Run ML-assisted analysis with {selected_model}.",
            "Explain the highest-risk findings first.",
            "Compare the scan against bundled sample files to spot recurring smells.",
        ]

        if features.get("has_hardcoded_string"):
            actions.append("Prioritize secret cleanup and credential rotation suggestions.")
        if features.get("has_database_operation"):
            actions.append("Inspect SQL construction for parameterization opportunities.")
        if features.get("has_eval_exec") or features.get("has_pickle") or features.get("has_subprocess"):
            actions.append("Review dangerous runtime APIs for safer alternatives.")
        if features.get("has_class_definition"):
            actions.append("Check whether the class can be split into smaller responsibilities.")

        return actions[:5]

    def recommend_model(self, code: str, source_label: str = "inline_input.py", features: Dict[str, Any] | None = None) -> Dict[str, Any]:
        if features is None:
            features = self.feature_extractor.extract_features(code)

        metadata = self._load_model_metadata()
        scores = {"randomforest": 0.0, "svm": 0.0}
        reasons = {"randomforest": [], "svm": []}

        def add_score(model_name: str, points: float, reason: str) -> None:
            scores[model_name] += points
            reasons[model_name].append(reason)

        rf_meta = metadata.get("randomforest", {})
        svm_meta = metadata.get("svm", {})

        if rf_meta:
            add_score(
                "randomforest",
                0.16,
                f"randomforest is trained on {rf_meta.get('samples_trained', 0)} sample(s)",
            )
            if float(rf_meta.get("train_score", 0.0)) >= 0.9:
                add_score("randomforest", 0.06, "randomforest has the stronger stored training score")

        if svm_meta:
            add_score(
                "svm",
                0.08,
                f"svm is available with {svm_meta.get('samples_trained', 0)} sample(s)",
            )
            if float(svm_meta.get("train_score", 0.0)) >= 0.75:
                add_score("svm", 0.03, "svm has a usable stored training score")

        complexity = float(features.get("cyclomatic_complexity", 0.0))
        function_length = float(features.get("function_length", 0.0))
        nesting_depth = float(features.get("nesting_depth", 0.0))
        security_signals = sum(
            1
            for name in (
                "has_dangerous_function",
                "has_database_operation",
                "has_network_operation",
                "has_file_operation",
                "has_eval_exec",
                "has_pickle",
                "has_subprocess",
            )
            if float(features.get(name, 0.0)) > 0
        )

        if complexity >= 8:
            add_score("randomforest", 0.24, "higher cyclomatic complexity favors tree-based splits")
        elif complexity <= 3:
            add_score("svm", 0.18, "simple control flow fits a compact separator")

        if nesting_depth >= 3:
            add_score("randomforest", 0.16, "deep nesting suggests non-linear interactions")

        if function_length >= 30:
            add_score("randomforest", 0.14, "longer code benefits from broader feature interactions")
        elif function_length <= 12:
            add_score("svm", 0.12, "short code is easier to separate with a margin-based model")

        if security_signals >= 2:
            add_score("randomforest", 0.17, "multiple security signals are better handled by an ensemble")

        if features.get("has_class_definition"):
            add_score("randomforest", 0.08, "class-based code tends to have mixed patterns")

        if features.get("has_hardcoded_string"):
            add_score("randomforest", 0.06, "literal-heavy code often needs broader context")

        if features.get("has_loop"):
            add_score("randomforest", 0.04, "loop-heavy code often has more interactions")

        if complexity <= 2 and nesting_depth <= 1 and function_length <= 8 and not features.get("has_class_definition"):
            add_score("svm", 0.10, "very compact straight-line code is a good SVM fit")

        if float(features.get("comment_ratio", 0.0)) > 0.18 and function_length <= 18:
            add_score("svm", 0.04, "heavily commented small snippets tend to stay simple")

        heuristic_model = max(scores, key=scores.get)
        alternative_model = "svm" if heuristic_model == "randomforest" else "randomforest"
        score_gap = scores[heuristic_model] - scores[alternative_model]
        heuristic_confidence = round(min(0.95, max(0.55, 0.55 + score_gap)), 2)

        selected_model = heuristic_model
        confidence = heuristic_confidence
        reason_text = " ".join(reasons[heuristic_model][:3]) or "The code shape most closely matches this model."
        selector_result = None

        # Agentic enhancement: use metadata-driven selector when feature stats exist.
        try:
            manager = ModelManager(str(PROJECT_ROOT / "data" / "models"))
            selector = AgenticModelSelector(manager)
            selector_result = selector.select_best_model(features)
            metadata_list = manager.get_all_models_metadata()
            has_feature_stats = any(
                isinstance(m.get("feature_stats"), dict) and bool(m.get("feature_stats"))
                for m in metadata_list
            )

            if has_feature_stats and selector_result.get("model_name") in {"randomforest", "svm"}:
                selected_model = selector_result["model_name"]
                confidence = round(float(selector_result.get("score", confidence)), 2)
                reason_text = selector_result.get("reason", reason_text)
            elif selector_result:
                reason_text = (
                    f"{reason_text} Metadata feature stats unavailable, so heuristic recommendation "
                    f"is preferred over accuracy-only selector output."
                )
        except Exception:
            # Keep deterministic heuristic output if selector setup fails.
            selector_result = None

        key_features = {
            "cyclomatic_complexity": round(complexity, 2),
            "function_length": round(function_length, 2),
            "nesting_depth": round(nesting_depth, 2),
            "security_signals": security_signals,
            "has_class_definition": bool(features.get("has_class_definition")),
            "has_hardcoded_string": bool(features.get("has_hardcoded_string")),
        }

        return {
            "source": source_label,
            "recommended_model": selected_model,
            "alternative_model": alternative_model,
            "confidence": confidence,
            "reason": reason_text,
            "why_selected": reasons[heuristic_model][:3],
            "scores": {name: round(score, 3) for name, score in scores.items()},
            "feature_snapshot": key_features,
            "agentic_actions": self._build_agentic_actions(features, selected_model),
            "training_metadata": metadata,
            "agentic_selector": selector_result,
        }

    def resolve_model_name(
        self,
        model_name: str,
        code: str,
        source_label: str = "inline_input.py",
        features: Dict[str, Any] | None = None,
    ) -> tuple[str, Dict[str, Any]]:
        recommendation = self.recommend_model(code, source_label=source_label, features=features)
        normalized = (model_name or "").strip().lower()
        if normalized in {"", "auto", "best", "agentic"}:
            return recommendation["recommended_model"], recommendation

        if normalized not in {"randomforest", "svm"}:
            return recommendation["recommended_model"], recommendation

        return normalized, recommendation

    def _normalize_issue(self, raw_issue: Dict[str, Any], source_label: str) -> Dict[str, Any]:
        return {
            "rule_id": raw_issue.get("rule_id", "ML_000"),
            "type": raw_issue.get("type", "unknown"),
            "name": raw_issue.get("name", raw_issue.get("type", "unknown").replace("_", " ").title()),
            "file": raw_issue.get("file", source_label),
            "line": int(raw_issue.get("line", 1)),
            "column": int(raw_issue.get("column", 0)),
            "code": raw_issue.get("code", "").strip(),
            "confidence": float(raw_issue.get("confidence", 0.0)),
            "severity": raw_issue.get("severity", "MEDIUM"),
            "description": raw_issue.get("description", "Potential issue detected"),
            "recommendation": raw_issue.get("recommendation", ""),
            "category": raw_issue.get("category", ""),
            "source": raw_issue.get("source", "rule"),
        }

    def _severity_weight(self, severity: str) -> float:
        weights = {
            "HIGH": 1.0,
            "MEDIUM": 0.7,
            "LOW": 0.4,
            "INFO": 0.2,
        }
        return weights.get(severity.upper(), 0.5)

    def _line_reachability_factor(self, code_lines: List[str], line_number: int) -> float:
        if line_number <= 0 or line_number > len(code_lines):
            return 0.7

        current_line = code_lines[line_number - 1].strip()
        if not current_line:
            return 0.5

        # Heuristic: lines immediately after return/raise/break/continue in same block are less reachable.
        if line_number > 1:
            previous = code_lines[line_number - 2].strip()
            if re.match(r"^(return|raise|break|continue)\b", previous):
                return 0.35

        # Heuristic: dead code patterns are likely less reachable by nature.
        if "unreachable" in current_line.lower() or "never execute" in current_line.lower():
            return 0.3

        return 1.0

    def _extract_matched_tokens(self, raw_issue: Dict[str, Any], line_text: str) -> List[str]:
        matched_tokens = []
        lowered = line_text.lower()

        token_candidates = [
            "password",
            "api_key",
            "token",
            "secret",
            "execute",
            "select",
            "insert",
            "update",
            "delete",
            "pickle",
            "eval",
            "exec",
            "subprocess",
            "os.system",
        ]

        for token in token_candidates:
            if token in lowered:
                matched_tokens.append(token)

        if not matched_tokens and raw_issue.get("code"):
            words = re.findall(r"[A-Za-z_]+", raw_issue.get("code", ""))
            matched_tokens.extend(words[:3])

        return matched_tokens[:6]

    def _enhance_issue(self, raw_issue: Dict[str, Any], source_label: str, code_lines: List[str]) -> Dict[str, Any]:
        normalized = self._normalize_issue(raw_issue, source_label)
        line_number = normalized["line"]
        severity = normalized["severity"]
        confidence = normalized["confidence"]
        reachability_factor = self._line_reachability_factor(code_lines, line_number)
        severity_weight = self._severity_weight(severity)
        risk_score = round(float(raw_issue.get("risk_score", severity_weight * confidence * reachability_factor)), 4)

        line_text = ""
        if 0 < line_number <= len(code_lines):
            line_text = code_lines[line_number - 1]

        normalized["reachability_factor"] = reachability_factor
        normalized["severity_weight"] = severity_weight
        normalized["risk_score"] = risk_score
        normalized["trigger_pattern"] = raw_issue.get("rule_id", normalized["type"])
        normalized["matched_tokens"] = self._extract_matched_tokens(raw_issue, line_text)
        normalized["why_flagged"] = normalized["description"]
        return {
            **normalized,
        }

    def _build_source_metrics(self, features: Dict[str, Any], issue_count: int) -> Dict[str, Any]:
        return {
            "cyclomatic_complexity": float(features.get("cyclomatic_complexity", 0.0)),
            "function_length": float(features.get("function_length", 0.0)),
            "nesting_depth": float(features.get("nesting_depth", 0.0)),
            "local_variable_count": float(features.get("local_variable_count", 0.0)),
            "issue_density": round(issue_count / max(float(features.get("function_length", 1.0)), 1.0), 4),
        }

    def analyze_source(
        self,
        code: str,
        source_label: str,
        min_confidence: float = 0.7,
        min_severity: str = "LOW",
        use_ml: bool = False,
        model_name: str = "randomforest",
        include_fixed_code: bool = False,
    ) -> Dict[str, Any]:
        started = datetime.now()
        code_lines = code.splitlines()
        features = self.feature_extractor.extract_features(code)
        issues = self.rule_engine.apply_rules(code, source_label)
        severity_rank = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "INFO": 0}
        min_rank = severity_rank.get(str(min_severity or "LOW").upper(), 1)

        if use_ml:
            model = self._get_model(model_name)
            hybrid = HybridAnalyzer(self.rule_engine, model)
            ml_issues = hybrid._apply_ml(features, source_label)
            for issue in ml_issues:
                issue["source"] = "ml"
            issues.extend(ml_issues)

        normalized = []
        for issue in issues:
            if float(issue.get("confidence", 0.0)) < min_confidence:
                continue
            sev = str(issue.get("severity", "LOW")).upper()
            if severity_rank.get(sev, 1) < min_rank:
                continue
            normalized.append(self._enhance_issue(issue, source_label, code_lines))

        normalized.sort(key=lambda item: (item["file"], -item["risk_score"], item["line"]))
        ended = datetime.now()
        result = {
            "source": source_label,
            "scan_duration_ms": int((ended - started).total_seconds() * 1000),
            "issues": normalized,
            "metrics": self._build_source_metrics(features, issue_count=len(normalized)),
        }
        if include_fixed_code:
            result["fixed_code"] = self.auto_fixer.generate_fixed_code(code, normalized)
        return result


def _list_sample_files() -> List[Dict[str, Any]]:
    if not TEST_SAMPLES_DIR.exists():
        return []

    sample_files = []
    for filepath in sorted(TEST_SAMPLES_DIR.glob("*.py")):
        try:
            code = filepath.read_text(encoding="utf-8", errors="ignore")
            lines = code.splitlines()
            sample_files.append(
                {
                    "name": filepath.name,
                    "relative_path": str(filepath.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                    "line_count": len(lines),
                    "preview": "\n".join(lines[:8]),
                }
            )
        except OSError:
            continue

    return sample_files


def _validate_sample_selection(selected_files: List[str]) -> List[Path]:
    valid_paths: List[Path] = []
    root_resolved = TEST_SAMPLES_DIR.resolve()

    for item in selected_files:
        candidate = (TEST_SAMPLES_DIR / item).resolve()
        if candidate.suffix != ".py":
            continue

        try:
            candidate.relative_to(root_resolved)
        except ValueError:
            continue

        if candidate.exists() and candidate.is_file():
            valid_paths.append(candidate)

    return valid_paths


def _build_summary(
    issues: List[Dict[str, Any]],
    files_analyzed: int,
    scan_duration_ms: int,
    source_metrics: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    severity_summary = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    type_summary: Dict[str, int] = {}
    risk_scores: List[float] = []

    for issue in issues:
        severity = issue.get("severity", "INFO")
        issue_type = issue.get("type", "unknown")

        if severity not in severity_summary:
            severity_summary[severity] = 0
        severity_summary[severity] += 1

        type_summary[issue_type] = type_summary.get(issue_type, 0) + 1
        risk_scores.append(float(issue.get("risk_score", 0.0)))

    complexity_summary = {
        "avg_cyclomatic_complexity": 0.0,
        "avg_function_length": 0.0,
        "avg_nesting_depth": 0.0,
        "avg_issue_density": 0.0,
    }
    if source_metrics:
        count = max(len(source_metrics), 1)
        complexity_summary = {
            "avg_cyclomatic_complexity": round(sum(m.get("cyclomatic_complexity", 0.0) for m in source_metrics) / count, 2),
            "avg_function_length": round(sum(m.get("function_length", 0.0) for m in source_metrics) / count, 2),
            "avg_nesting_depth": round(sum(m.get("nesting_depth", 0.0) for m in source_metrics) / count, 2),
            "avg_issue_density": round(sum(m.get("issue_density", 0.0) for m in source_metrics) / count, 4),
        }

    risk_summary = {
        "avg_risk_score": round(sum(risk_scores) / max(len(risk_scores), 1), 2),
        "max_risk_score": round(max(risk_scores) if risk_scores else 0.0, 2),
    }

    return {
        "files_analyzed": files_analyzed,
        "total_issues": len(issues),
        "severity_summary": severity_summary,
        "type_summary": type_summary,
        "scan_duration_ms": scan_duration_ms,
        "risk_summary": risk_summary,
        "complexity_summary": complexity_summary,
    }


def _build_severity_breakdown(issues: List[Dict[str, Any]]) -> Dict[str, int]:
    breakdown = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    for issue in issues:
        sev = str(issue.get("severity", "INFO")).upper()
        if sev not in breakdown:
            breakdown[sev] = 0
        breakdown[sev] += 1
    return breakdown


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "web" / "templates"),
        static_folder=str(Path(__file__).parent / "web" / "static"),
    )
    service = AnalyzerService()

    @app.get("/")
    def index():
        samples = _list_sample_files()
        return render_template("index.html", sample_count=len(samples))

    @app.get("/api/test-files")
    def get_test_files():
        return jsonify({"files": _list_sample_files()})

    @app.post("/api/recommend-model")
    def recommend_model():
        payload = request.get_json(silent=True) or {}
        code = payload.get("code", "")
        source_name = payload.get("filename", "inline_input.py")

        if not code.strip():
            return jsonify({"error": "Code input is empty."}), 400

        recommendation = service.recommend_model(code, source_name)
        return jsonify(recommendation)

    @app.post("/api/analyze/code")
    def analyze_code():
        payload = request.get_json(silent=True) or {}
        code = payload.get("code", "")
        source_name = payload.get("filename", "inline_input.py")
        min_confidence = float(payload.get("min_confidence", 0.7))
        min_severity = str(payload.get("min_severity", "LOW")).upper()
        use_ml = bool(payload.get("use_ml", False))
        model_name = payload.get("model_name", "randomforest")
        apply_fixes = bool(payload.get("apply_fixes", False))

        if not code.strip():
            return jsonify({"error": "Code input is empty."}), 400

        try:
            resolved_model_name, recommendation = service.resolve_model_name(model_name, code, source_name)
            result = service.analyze_source(
                code=code,
                source_label=source_name,
                min_confidence=min_confidence,
                min_severity=min_severity,
                use_ml=use_ml,
                model_name=resolved_model_name,
                include_fixed_code=apply_fixes,
            )
        except Exception as exc:  # pragma: no cover - defensive API handling
            return jsonify({"error": f"Analysis failed: {exc}"}), 500

        summary = _build_summary(
            result["issues"],
            files_analyzed=1,
            scan_duration_ms=result["scan_duration_ms"],
            source_metrics=[result.get("metrics", {})],
        )
        return jsonify(
            {
                "summary": summary,
                "issues": result["issues"],
                "fixed_code": result.get("fixed_code", code),
                "severity_breakdown": _build_severity_breakdown(result["issues"]),
                "sources": [source_name],
                "sources_data": [{"source": source_name, "code": code}],
                "source_metrics": [result.get("metrics", {})],
                "selected_model": resolved_model_name,
                "model_recommendation": recommendation,
            }
        )

    @app.post("/api/analyze/files")
    def analyze_files():
        payload = request.get_json(silent=True) or {}
        selected = payload.get("files", [])
        min_confidence = float(payload.get("min_confidence", 0.7))
        min_severity = str(payload.get("min_severity", "LOW")).upper()
        use_ml = bool(payload.get("use_ml", False))
        model_name = payload.get("model_name", "randomforest")

        selected_paths = _validate_sample_selection(selected)
        if not selected_paths:
            return jsonify({"error": "No valid sample files selected."}), 400

        combined_code = "\n\n".join(
            file_path.read_text(encoding="utf-8", errors="ignore") for file_path in selected_paths
        )
        resolved_model_name, recommendation = service.resolve_model_name(
            model_name,
            combined_code,
            "selected_files",
        )

        all_issues: List[Dict[str, Any]] = []
        sources_data: List[Dict[str, str]] = []
        source_metrics: List[Dict[str, Any]] = []
        started = datetime.now()

        for file_path in selected_paths:
            code = file_path.read_text(encoding="utf-8", errors="ignore")
            source_label = str(file_path.relative_to(PROJECT_ROOT)).replace("\\", "/")
            result = service.analyze_source(
                code=code,
                source_label=source_label,
                min_confidence=min_confidence,
                min_severity=min_severity,
                use_ml=use_ml,
                model_name=resolved_model_name,
            )
            all_issues.extend(result["issues"])
            sources_data.append({"source": source_label, "code": code})
            source_metrics.append(result.get("metrics", {}))

        ended = datetime.now()
        duration = int((ended - started).total_seconds() * 1000)
        all_issues.sort(key=lambda item: (item["file"], -item["risk_score"], item["line"]))
        summary = _build_summary(
            all_issues,
            files_analyzed=len(selected_paths),
            scan_duration_ms=duration,
            source_metrics=source_metrics,
        )

        sources = [str(path.relative_to(PROJECT_ROOT)).replace("\\", "/") for path in selected_paths]
        return jsonify(
            {
                "summary": summary,
                "issues": all_issues,
                "severity_breakdown": _build_severity_breakdown(all_issues),
                "sources": sources,
                "sources_data": sources_data,
                "source_metrics": source_metrics,
                "selected_model": resolved_model_name,
                "model_recommendation": recommendation,
            }
        )

    return app


def main():
    app = create_app()
    app.run(host="127.0.0.1", port=5002, debug=False)


if __name__ == "__main__":
    main()
