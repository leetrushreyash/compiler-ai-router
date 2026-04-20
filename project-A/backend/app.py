"""
FastAPI backend wrapper for the Code Smell Compiler CLI.
Exposes REST endpoints consumed by the React dashboard.
"""

import sys
import os
import json
import tempfile
import shutil
from pathlib import Path
from typing import Optional, List, Dict

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ── Make the project root importable ──────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code_smell_compiler.parser.parser import parse_file_to_ast
from code_smell_compiler.feature_extraction.extractor import extract_features
from code_smell_compiler.static_analyzer.rule_based import rule_based_findings
from code_smell_compiler.ml_model.model_utils import load_models
from code_smell_compiler.reporting.report import format_finding
from code_smell_compiler.reporting.prioritization import prioritize_findings
from code_smell_compiler.refactoring.engine import generate_refactorings
from code_smell_compiler.correlation.analyzer import full_correlation_analysis
from code_smell_compiler.ml_model.explainable import explain_prediction
from code_smell_compiler.neuro_symbolic import build_neuro_symbolic_analysis
import requests
from backend.energy import EnergyCollector

# ══════════════════════════════════════════════════════════════════════════
# Security Cross-Project Integration
# ══════════════════════════════════════════════════════════════════════════
def get_security_verdict(code_text: str, filename: str) -> list:
    """Fetch security evaluation from Project C."""
    try:
        response = requests.post(
            "http://localhost:5001/api/cross-project/security", 
            json={"code": code_text, "filename": filename},
            timeout=5
        )
        if response.status_code == 200:
            return response.json().get("security_issues", [])
    except Exception as e:
        return [{"error": "Project C (Security Service) is offline or failed", "details": str(e)}]
    return [{"error": f"Project C returned status {response.status_code if 'response' in locals() else 'Unknown'}"}]

# ══════════════════════════════════════════════════════════════════════════
# App setup
# ══════════════════════════════════════════════════════════════════════════
app = FastAPI(
    title="Code Smell Compiler API",
    version="2.0.0",
    description="ML-Powered Code Smell Detection, Auto-Refactoring & Energy Analytics",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pre-load ML models once at startup
_models_obj = None
# Background corpus: pre-extracted features from data/ samples for robust
# correlation analysis even when the user submits a single file.
_background_features: Dict[str, Dict] = {}


@app.on_event("startup")
def _load_ml():
    global _models_obj, _background_features
    try:
        _models_obj = load_models()
    except Exception as exc:
        print(f"[WARN] ML models not loaded: {exc}")
    # Pre-extract features from the 400 synthetic samples in data/
    data_dir = PROJECT_ROOT / "data"
    if data_dir.is_dir():
        import time
        t0 = time.time()
        for p in sorted(data_dir.glob("*.py")):
            try:
                tree, _ = parse_file_to_ast(str(p))
                feats, _ = extract_features(tree)
                _background_features[str(p)] = feats
            except Exception:
                pass
        print(f"[INFO] Background corpus: {len(_background_features)} files in {time.time()-t0:.2f}s")


# ══════════════════════════════════════════════════════════════════════════
# Request / Response schemas
# ══════════════════════════════════════════════════════════════════════════
class CodePayload(BaseModel):
    code: str
    filename: str = "untitled.py"


class AnalysisOptions(BaseModel):
    use_ml: bool = True
    refactor: bool = True
    correlate: bool = True
    explain: bool = True
    prioritize: bool = True


class ExamplesPayload(BaseModel):
    filenames: List[str]
    options: AnalysisOptions = AnalysisOptions()


# ══════════════════════════════════════════════════════════════════════════
# Core analysis helper (reused by every endpoint)
# ══════════════════════════════════════════════════════════════════════════

def _analyze_single_file(
    filepath: Path,
    models_obj,
    enable_refactoring: bool,
    collector: Optional[EnergyCollector] = None,
):
    """Return (findings, features, refactorings, explanations) for one file."""
    if collector:
        collector.begin_phase("parsing")
    tree, src = parse_file_to_ast(str(filepath))

    if collector:
        collector.begin_phase("feature_extraction")
    features, locations = extract_features(tree)

    findings = []
    refactorings = []
    explanations = []

    # Rule-based
    if collector:
        collector.begin_phase("rule_based_detection")
    rb = rule_based_findings(features, locations)
    for r in rb:
        ln = r.get("line", 1)
        findings.append(
            format_finding(
                str(filepath), ln, r["smell_type"], r["severity"], r["confidence"], r["suggested_fix"]
            )
        )

    # ML-based
    if models_obj is not None:
        if collector:
            collector.begin_phase("ml_inference")
        scaler = models_obj.get("scaler")
        rf = models_obj.get("rf")
        feats_order = models_obj.get("features")
        try:
            import pandas as pd
            df = pd.DataFrame([features])
            df = df.reindex(columns=feats_order, fill_value=0)
            xs = scaler.transform(df)
        except Exception:
            x = [features.get(f, 0) for f in feats_order]
            xs = scaler.transform([x])

        probs_rf = rf.predict_proba(xs)
        for i, feat in enumerate(feats_order):
            try:
                prob = float(probs_rf[i][0][1])
            except Exception:
                prob = 0.0
            if prob > 0.5:
                locs = locations.get(feat) or []
                ln = locs[0] if locs else 1
                findings.append(
                    format_finding(str(filepath), ln, feat, "medium", prob, "See rule-based suggested fix.")
                )

        if collector:
            collector.begin_phase("shap_explanation")
        explanations = explain_prediction(features, models_obj)

    # Refactoring
    if enable_refactoring:
        if collector:
            collector.begin_phase("refactoring")
        refactorings = generate_refactorings(src, features, locations)

    if collector:
        collector.end_phase()

    return findings, features, refactorings, explanations


def _run_full_analysis(files: List[Path], options: AnalysisOptions):
    """Run the full pipeline with energy measurement and return the report dict."""
    collector = EnergyCollector()
    collector.start()

    models_obj = _models_obj if options.use_ml or options.explain else None

    all_findings = []
    all_features = {}
    all_refactorings = []
    all_explanations = []
    file_sources = {}
    failed_files = []

    for p in files:
        try:
            findings, features, refactorings, explanations = _analyze_single_file(
                p, models_obj, enable_refactoring=options.refactor, collector=collector
            )
        except Exception as exc:
            failed_files.append({"file": str(p), "error": str(exc)})
            try:
                file_sources[str(p)] = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                file_sources[str(p)] = ""
            continue
        # read source for code viewer
        try:
            file_sources[str(p)] = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            file_sources[str(p)] = ""

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

    # De-duplicate findings: the same (file, smell_type) can be reported
    # by both rule-based and ML inference.
    all_findings = _dedupe_findings(all_findings)

    report: dict = {"findings": all_findings, "sources": file_sources}

    if failed_files:
        report["failed_files"] = failed_files

    if options.refactor:
        report["refactorings"] = all_refactorings

    if options.correlate and all_features:
        collector.begin_phase("correlation")
        # Merge user features with pre-computed background corpus for
        # statistically robust correlation even with a single file.
        merged_features = {**_background_features, **all_features}
        corr_result = full_correlation_analysis(merged_features)
        # Tag the report with how many user vs background files were used
        corr_result["summary"]["user_files_analyzed"] = len(all_features)
        corr_result["summary"]["background_files"] = len(_background_features)
        # Compute smell totals from only the user's files (not the corpus)
        from code_smell_compiler.correlation.analyzer import SMELL_BASE_WEIGHT
        user_totals = {}
        for s in SMELL_BASE_WEIGHT:
            user_totals[s] = sum(1 for f in all_features.values() if f.get(s))
        corr_result["summary"]["user_smell_totals"] = user_totals
        # Filter hotspots to only include user files
        user_paths = set(all_features.keys())
        corr_result["hotspots"] = [
            h for h in corr_result["hotspots"] if h["file"] in user_paths
        ]
        report["correlation_analysis"] = corr_result
        collector.end_phase()

    if options.explain and all_explanations:
        report["ml_explanations"] = all_explanations

    if options.prioritize and all_findings:
        report["prioritized_findings"] = prioritize_findings(all_findings, all_features)

    # Neuro-symbolic fusion (rule evidence + ML confidence + correlation context)
    report["neuro_symbolic_analysis"] = build_neuro_symbolic_analysis(
        findings=all_findings,
        all_features=all_features,
        ml_explanations=all_explanations,
        correlation_analysis=report.get("correlation_analysis"),
    )

    # Energy report
    energy_report = collector.stop()
    report["energy"] = energy_report.to_dict()

    # Per-file & per-smell energy breakdown (estimated proportionally based on severity/complexity)
    total_e = energy_report.estimated_energy_joules
    n_files = max(len(files), 1)
    n_smells = max(len(all_findings), 1)
    
    # Calculate a weighted energy score per finding
    # Base it on confidence and severity to make the distribution varying and realistic
    severity_weights = {"high": 3.0, "medium": 2.0, "low": 1.0}
    weighted_findings = []
    total_weight = 0.0
    
    for f in all_findings:
        w = severity_weights.get(f.get("severity", "low").lower(), 1.0) * (f.get("confidence", 0.5) + 0.5) 
        total_weight += w
        weighted_findings.append({"finding": f, "weight": w})
        
    energy_breakdown = []
    if total_weight > 0:
        for item in weighted_findings:
            alloc_energy = (item["weight"] / total_weight) * total_e
            energy_breakdown.append({
                "smell_type": item["finding"]["smell_type"],
                "file": item["finding"]["file"],
                "energy_uj": round(alloc_energy * 1_000_000, 2), # Add microjoules
                "energy_j": round(alloc_energy, 6)
            })
    
    report["energy"]["energy_per_file"] = round(total_e / n_files, 6)
    report["energy"]["energy_per_smell"] = round(total_e / n_smells, 6) # Average
    report["energy"]["smell_energy_breakdown"] = energy_breakdown

    return report


def _dedupe_findings(findings: List[dict]) -> List[dict]:
    """Merge duplicate smells per file to avoid double-counting (rule + ML)."""

    def sev_rank(sev: str) -> int:
        order = {"low": 1, "medium": 2, "high": 3}
        return order.get((sev or "").lower(), 0)

    merged: Dict[tuple, dict] = {}
    for f in findings or []:
        file_path = f.get("file")
        smell = f.get("smell_type")
        if not file_path or not smell:
            continue
        key = (file_path, smell)

        if key not in merged:
            merged[key] = dict(f)
            continue

        cur = merged[key]

        # Severity: keep the stronger one
        if sev_rank(f.get("severity")) > sev_rank(cur.get("severity")):
            cur["severity"] = f.get("severity")

        # Confidence: keep the max
        try:
            cur_conf = float(cur.get("confidence", 0.0))
        except Exception:
            cur_conf = 0.0
        try:
            new_conf = float(f.get("confidence", 0.0))
        except Exception:
            new_conf = 0.0
        if new_conf > cur_conf:
            cur["confidence"] = round(new_conf, 3)

        # Line: prefer an actual location (positive line) and choose the earliest
        try:
            cur_ln = int(cur.get("line_number", 0) or 0)
        except Exception:
            cur_ln = 0
        try:
            new_ln = int(f.get("line_number", 0) or 0)
        except Exception:
            new_ln = 0
        if cur_ln <= 0 and new_ln > 0:
            cur["line_number"] = new_ln
        elif cur_ln > 0 and new_ln > 0:
            cur["line_number"] = min(cur_ln, new_ln)

        # Suggested fix: prefer non-generic fix text
        cur_fix = str(cur.get("suggested_fix", "") or "")
        new_fix = str(f.get("suggested_fix", "") or "")
        generic = "See rule-based suggested fix."
        if (cur_fix == generic and new_fix and new_fix != generic) or (not cur_fix and new_fix):
            cur["suggested_fix"] = new_fix

        merged[key] = cur

    return list(merged.values())


# ══════════════════════════════════════════════════════════════════════════
# REST Endpoints
# ══════════════════════════════════════════════════════════════════════════

@app.get("/api/health")
def health():
    return {"status": "ok", "ml_loaded": _models_obj is not None}


@app.get("/api/examples")
def list_examples():
    """Return available example files."""
    examples_dir = PROJECT_ROOT / "examples"
    if not examples_dir.is_dir():
        return {"examples": []}
    files = sorted(examples_dir.glob("*.py"))
    return {
        "examples": [
            {"name": f.name, "path": str(f.relative_to(PROJECT_ROOT))}
            for f in files
        ]
    }


@app.get("/api/examples/{filename}")
def get_example(filename: str):
    """Return source code of an example file."""
    filepath = PROJECT_ROOT / "examples" / filename
    if not filepath.is_file():
        raise HTTPException(404, "Example not found")
    return {"filename": filename, "code": filepath.read_text(encoding="utf-8", errors="replace")}


@app.post("/api/analyze/code")
def analyze_code(payload: CodePayload):
    """Analyze pasted code."""
    options = AnalysisOptions()
    tmp = tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w", encoding="utf-8")
    try:
        tmp.write(payload.code)
        tmp.close()
        report = _run_full_analysis([Path(tmp.name)], options)
        # Remap temp path to user-friendly name
        report = _remap_paths(report, {tmp.name: payload.filename})
        return JSONResponse(report)
    finally:
        os.unlink(tmp.name)


@app.post("/api/analyze/upload")
async def analyze_upload(
    files: List[UploadFile] = File(...),
    use_ml: bool = Form(True),
    refactor: bool = Form(True),
    correlate: bool = Form(True),
    explain: bool = Form(True),
    prioritize: bool = Form(True),
):
    """Analyze uploaded file(s)."""
    options = AnalysisOptions(
        use_ml=use_ml, refactor=refactor, correlate=correlate, explain=explain, prioritize=prioritize
    )
    tmpdir = tempfile.mkdtemp()
    path_map = {}
    try:
        paths = []
        for uf in files:
            dest = Path(tmpdir) / (uf.filename or "file.py")
            dest.write_bytes(await uf.read())
            paths.append(dest)
            path_map[str(dest)] = uf.filename or "file.py"

        report = _run_full_analysis(paths, options)
        report = _remap_paths(report, path_map)
        return JSONResponse(report)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


@app.post("/api/analyze/examples")
def analyze_examples(payload: ExamplesPayload):
    """Analyze selected example files."""
    paths = []
    for fn in payload.filenames:
        p = PROJECT_ROOT / "examples" / fn
        if p.is_file():
            paths.append(p)
    if not paths:
        raise HTTPException(400, "No valid example files selected")
    report = _run_full_analysis(paths, payload.options)
    return JSONResponse(report)


@app.post("/api/cross-project/security")
def cross_project_security(payload: CodePayload):
    """Explicitly proxy code to Project C for Security evaluation when requested."""
    if not payload.code.strip():
        raise HTTPException(400, "Code input is empty.")
    
    security_eval = get_security_verdict(payload.code, payload.filename)
    return JSONResponse({"security_issues": security_eval})


# ── Helpers ───────────────────────────────────────────────────────────────

def _remap_paths(report: dict, mapping: dict) -> dict:
    """Replace temp file paths with user-friendly names."""
    raw = json.dumps(report)
    for old, new in mapping.items():
        raw = raw.replace(old.replace("\\", "\\\\"), new)
        raw = raw.replace(old.replace("\\", "/"), new)
        raw = raw.replace(old, new)
    return json.loads(raw)


# ══════════════════════════════════════════════════════════════════════════
# Run
# ══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)
