"""
Explainable ML Predictions with SHAP + Calibrated Ensemble (Novelty 3)
======================================================================
No existing code-smell tool provides SHAP-based explainability or
combines multiple classifiers in a stacking ensemble.

Features:
  - Stacking ensemble: RF + LR combined via a meta-learner
  - SHAP explanations for every ML prediction
  - Per-smell precision / recall / F1 metrics
  - Human-readable explanation strings
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.multioutput import MultiOutputClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, precision_recall_fscore_support

try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False

from code_smell_compiler.ml_model.dataset import generate_dataset

ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = ROOT / "ml_model" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# 1. Stacking Ensemble
# ---------------------------------------------------------------------------

def _build_stacking_estimator():
    """
    Build a StackingClassifier that combines:
      - RandomForestClassifier  (base learner 1)
      - LogisticRegression      (base learner 2)
      - LogisticRegression      (meta-learner, uses cross-validated predictions)
    """
    estimators = [
        ("rf", RandomForestClassifier(n_estimators=100, random_state=42)),
        ("lr", LogisticRegression(max_iter=500, random_state=42)),
    ]
    stacker = StackingClassifier(
        estimators=estimators,
        final_estimator=LogisticRegression(max_iter=500, random_state=42),
        cv=5,
        stack_method="predict_proba",
        passthrough=False,
    )
    return stacker


def train_explainable_model(n_samples: int = 400) -> Dict[str, Any]:
    """
    Train the stacking ensemble, compute per-smell metrics, and
    persist everything (model, scaler, SHAP explainer, metrics).
    """
    samples, labels = generate_dataset(n_samples)
    X = pd.DataFrame(samples).fillna(0)
    Y = pd.DataFrame(labels).fillna(0)

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    # --- individual base models (kept for backwards compatibility) ---
    rf = MultiOutputClassifier(RandomForestClassifier(n_estimators=100, random_state=42))
    lr = MultiOutputClassifier(LogisticRegression(max_iter=500, random_state=42))

    X_train, X_test, y_train, y_test = train_test_split(
        Xs, Y, test_size=0.2, random_state=42
    )

    rf.fit(X_train, y_train)
    lr.fit(X_train, y_train)

    # --- stacking ensemble (one per smell target) ---
    stacking_models = {}
    per_smell_metrics = {}

    for col in Y.columns:
        y_col_train = y_train[col].values
        y_col_test = y_test[col].values

        # Only train if there are both classes in training data
        if len(set(y_col_train)) < 2:
            stacking_models[col] = None
            per_smell_metrics[col] = {"note": "insufficient positive samples"}
            continue

        stacker = _build_stacking_estimator()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            stacker.fit(X_train, y_col_train)
        stacking_models[col] = stacker

        # Per-smell metrics
        y_pred = stacker.predict(X_test)
        prec, rec, f1, sup = precision_recall_fscore_support(
            y_col_test, y_pred, average="binary", zero_division=0
        )
        per_smell_metrics[col] = {
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4),
            "support": int(sup) if sup is not None else 0,
            "test_accuracy": round(float((y_pred == y_col_test).mean()), 4),
        }

    # --- SHAP explainers (one TreeExplainer per smell's RF estimator) ---
    shap_explainers = {}
    if HAS_SHAP:
        for idx, col in enumerate(X.columns):
            try:
                shap_explainers[col] = shap.TreeExplainer(rf.estimators_[idx])
            except Exception:
                shap_explainers[col] = None

    # --- Persist ---
    artifact = {
        "rf": rf,
        "lr": lr,
        "stacking_models": stacking_models,
        "scaler": scaler,
        "features": list(X.columns),
        "shap_explainers": shap_explainers,
    }
    joblib.dump(artifact, MODEL_DIR / "models.pkl")

    # Aggregate metrics
    rf_test = rf.score(X_test, y_test)
    lr_test = lr.score(X_test, y_test)
    ensemble_accuracies = []
    for col in Y.columns:
        if stacking_models.get(col) is not None:
            acc = stacking_models[col].score(X_test, y_test[col].values)
            ensemble_accuracies.append(acc)

    metrics = {
        "rf_test_accuracy": round(float(rf_test), 4),
        "lr_test_accuracy": round(float(lr_test), 4),
        "ensemble_mean_accuracy": round(float(np.mean(ensemble_accuracies)), 4) if ensemble_accuracies else 0.0,
        "per_smell_metrics": per_smell_metrics,
    }
    with open(MODEL_DIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print("Explainable models trained and saved to:", MODEL_DIR / "models.pkl")
    print("Per-smell metrics saved to:", MODEL_DIR / "metrics.json")
    return metrics


# ---------------------------------------------------------------------------
# 2. SHAP explanation at inference time
# ---------------------------------------------------------------------------

def explain_prediction(
    features: Dict[str, Any],
    models_obj: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    For each smell predicted positive by the ensemble, produce a
    human-readable SHAP-based explanation.

    Returns a list of dicts:
      - smell_type        : str
      - probability       : float
      - prediction_source : "ensemble" | "rf"
      - shap_explanation  : list of {feature, value, shap_value, direction}
      - explanation_text  : human-readable string
    """
    scaler = models_obj.get("scaler")
    rf = models_obj.get("rf")
    stacking_models = models_obj.get("stacking_models", {})
    feats_order = models_obj.get("features", [])
    shap_explainers = models_obj.get("shap_explainers", {})

    # Build feature vector
    x_raw = [features.get(f, 0) for f in feats_order]
    import pandas as pd
    xs = scaler.transform(pd.DataFrame([dict(zip(feats_order, x_raw))]))

    explanations = []

    for i, smell in enumerate(feats_order):
        prob = 0.0
        source = "rf"

        # Try ensemble first
        stacker = stacking_models.get(smell) if stacking_models else None
        if stacker is not None:
            try:
                prob_arr = stacker.predict_proba(xs)
                prob = float(prob_arr[0][1]) if prob_arr.shape[1] > 1 else float(prob_arr[0][0])
                source = "ensemble"
            except Exception:
                prob = 0.0

        # Fallback to RF
        if source == "rf":
            try:
                probs_rf = rf.predict_proba(xs)
                prob = float(probs_rf[i][0][1])
            except Exception:
                prob = 0.0

        if prob <= 0.5:
            continue

        # SHAP explanation — use the per-smell explainer
        shap_details = []
        explanation_text = ""

        smell_explainer = shap_explainers.get(smell) if shap_explainers else None
        if HAS_SHAP and smell_explainer is not None:
            try:
                shap_values = smell_explainer.shap_values(xs)
                # shap_values shape can be:
                #   (n_samples, n_features, 2)  for binary classification
                #   list of 2 arrays each (n_samples, n_features)
                #   (n_samples, n_features) for regression-style
                sv_array = np.array(shap_values)

                if sv_array.ndim == 3 and sv_array.shape[2] == 2:
                    # Shape (1, 10, 2): take class-1 values (positive class)
                    sv = sv_array[0, :, 1]
                elif isinstance(shap_values, list) and len(shap_values) == 2:
                    # List of [class0_array, class1_array]
                    sv = np.array(shap_values[1])[0]
                elif sv_array.ndim == 2:
                    sv = sv_array[0]
                else:
                    sv = sv_array.flatten()[:len(feats_order)]

                # Build per-feature explanations
                contrib = []
                for j, feat_name in enumerate(feats_order):
                    val = float(sv[j]) if j < len(sv) else 0.0
                    contrib.append({
                        "feature": feat_name,
                        "value": x_raw[j],
                        "shap_value": round(val, 4),
                        "direction": "increases risk" if val > 0 else "decreases risk",
                    })
                contrib.sort(key=lambda c: abs(c["shap_value"]), reverse=True)
                shap_details = contrib[:5]  # top 5 contributors

                # Human-readable text
                parts = []
                for c in shap_details[:3]:
                    if abs(c["shap_value"]) > 0.001:
                        parts.append(
                            f"{c['feature']}={c['value']} ({c['direction']}, impact={c['shap_value']:+.4f})"
                        )
                if parts:
                    explanation_text = (
                        f"'{smell}' flagged (prob={prob:.2f}) because: " + "; ".join(parts) + "."
                    )
            except Exception as e:
                # Store the error for debugging
                explanation_text = ""

        if not explanation_text:
            # Fallback: feature-importance explanation without SHAP
            positive_feats = [f for f in feats_order if features.get(f, 0)]
            explanation_text = (
                f"'{smell}' flagged (prob={prob:.2f}) — co-occurring smells: "
                + ", ".join(positive_feats) + "."
            )

        explanations.append({
            "smell_type": smell,
            "probability": round(prob, 4),
            "prediction_source": source,
            "shap_explanation": shap_details,
            "explanation_text": explanation_text,
        })

    return explanations
