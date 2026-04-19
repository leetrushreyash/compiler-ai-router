"""ML evaluation module — confusion matrix, ROC curves, model comparison."""
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import json
from pathlib import Path


class ModelEvaluator:
    """Comprehensive evaluation of ML models with visualisation helpers."""

    def __init__(self, output_dir: str = "data/evaluation"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Core metrics
    # ------------------------------------------------------------------
    def compute_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        label_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Compute precision, recall, F1, accuracy and confusion matrix.

        Args:
            y_true: Ground-truth labels
            y_pred: Predicted labels
            label_names: Optional human-readable label names

        Returns:
            Dictionary of evaluation metrics
        """
        from sklearn.metrics import (
            accuracy_score,
            precision_score,
            recall_score,
            f1_score,
            confusion_matrix,
            classification_report,
        )

        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, average="weighted", zero_division=0)
        rec = recall_score(y_true, y_pred, average="weighted", zero_division=0)
        f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)
        cm = confusion_matrix(y_true, y_pred)

        # Per-class metrics
        prec_per = precision_score(y_true, y_pred, average=None, zero_division=0)
        rec_per = recall_score(y_true, y_pred, average=None, zero_division=0)
        f1_per = f1_score(y_true, y_pred, average=None, zero_division=0)

        report_str = classification_report(
            y_true, y_pred, target_names=label_names, zero_division=0
        )

        return {
            "accuracy": float(acc),
            "precision_weighted": float(prec),
            "recall_weighted": float(rec),
            "f1_weighted": float(f1),
            "confusion_matrix": cm.tolist(),
            "per_class_precision": prec_per.tolist(),
            "per_class_recall": rec_per.tolist(),
            "per_class_f1": f1_per.tolist(),
            "label_names": label_names or [],
            "classification_report": report_str,
        }

    # ------------------------------------------------------------------
    # ROC / AUC (one-vs-rest)
    # ------------------------------------------------------------------
    def compute_roc_auc(
        self,
        y_true: np.ndarray,
        y_proba: np.ndarray,
        label_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Compute ROC curves and AUC for each class (one vs rest).

        Args:
            y_true: Ground-truth labels (integer-encoded)
            y_proba: Predicted probabilities, shape (n_samples, n_classes)
            label_names: Optional class names

        Returns:
            Dictionary with per-class fpr/tpr/auc and macro-average AUC
        """
        from sklearn.metrics import roc_curve, auc
        from sklearn.preprocessing import label_binarize

        classes = sorted(set(y_true))
        n_classes = len(classes)

        if n_classes < 2:
            return {"error": "Need at least 2 classes for ROC"}

        y_bin = label_binarize(y_true, classes=classes)

        # For binary classification label_binarize returns shape (n, 1)
        if y_bin.shape[1] == 1:
            y_bin = np.hstack([1 - y_bin, y_bin])

        roc_data: Dict[str, Any] = {"per_class": {}, "macro_auc": 0.0}
        all_auc = []

        for i, cls in enumerate(classes):
            cls_name = label_names[i] if label_names and i < len(label_names) else str(cls)
            fpr, tpr, thresholds = roc_curve(y_bin[:, i], y_proba[:, i])
            roc_auc = float(auc(fpr, tpr))
            all_auc.append(roc_auc)
            roc_data["per_class"][cls_name] = {
                "fpr": fpr.tolist(),
                "tpr": tpr.tolist(),
                "auc": roc_auc,
            }

        roc_data["macro_auc"] = float(np.mean(all_auc))
        return roc_data

    # ------------------------------------------------------------------
    # Cross-validation comparison of multiple models
    # ------------------------------------------------------------------
    def compare_models(
        self,
        X: np.ndarray,
        y: np.ndarray,
        model_names: Optional[List[str]] = None,
        cv: int = 5,
    ) -> Dict[str, Any]:
        """Train and cross-validate multiple models, returning comparison metrics.

        Args:
            X: Feature matrix
            y: Label array
            model_names: List of model types to compare (default: RF + SVM)
            cv: Number of CV folds

        Returns:
            Dictionary keyed by model name with cv scores
        """
        from sklearn.model_selection import cross_val_score, cross_validate
        from ..ml.models import create_model

        if model_names is None:
            model_names = ["randomforest", "svm"]

        actual_cv = min(cv, len(X))
        if actual_cv < 2:
            actual_cv = 2

        results: Dict[str, Any] = {}

        for name in model_names:
            try:
                model = create_model(name)
                scoring = {
                    "accuracy": "accuracy",
                    "f1_weighted": "f1_weighted",
                    "precision_weighted": "precision_weighted",
                    "recall_weighted": "recall_weighted",
                }

                cv_results = cross_validate(
                    model, X, y, cv=actual_cv, scoring=scoring, return_train_score=True
                )

                results[name] = {
                    "accuracy_mean": float(np.mean(cv_results["test_accuracy"])),
                    "accuracy_std": float(np.std(cv_results["test_accuracy"])),
                    "f1_mean": float(np.mean(cv_results["test_f1_weighted"])),
                    "f1_std": float(np.std(cv_results["test_f1_weighted"])),
                    "precision_mean": float(np.mean(cv_results["test_precision_weighted"])),
                    "recall_mean": float(np.mean(cv_results["test_recall_weighted"])),
                    "train_accuracy_mean": float(np.mean(cv_results["train_accuracy"])),
                    "fold_scores": cv_results["test_accuracy"].tolist(),
                }
            except Exception as e:
                results[name] = {"error": str(e)}

        return results

    # ------------------------------------------------------------------
    # Visualisation (matplotlib) — save to files
    # ------------------------------------------------------------------
    def plot_confusion_matrix(
        self,
        cm: List[List[int]],
        label_names: Optional[List[str]] = None,
        title: str = "Confusion Matrix",
        filename: str = "confusion_matrix.png",
    ) -> str:
        """Generate and save a confusion-matrix heatmap.

        Returns:
            Absolute path to saved image
        """
        import matplotlib
        matplotlib.use("Agg")  # non-interactive backend
        import matplotlib.pyplot as plt
        import seaborn as sns

        cm_array = np.array(cm)
        fig, ax = plt.subplots(figsize=(max(6, len(cm_array)), max(5, len(cm_array) - 1)))

        sns.heatmap(
            cm_array,
            annot=True,
            fmt="d",
            cmap="Blues",
            xticklabels=label_names or "auto",
            yticklabels=label_names or "auto",
            ax=ax,
        )
        ax.set_xlabel("Predicted Label")
        ax.set_ylabel("True Label")
        ax.set_title(title)
        plt.tight_layout()

        out_path = self.output_dir / filename
        fig.savefig(str(out_path), dpi=150)
        plt.close(fig)
        return str(out_path)

    def plot_roc_curves(
        self,
        roc_data: Dict[str, Any],
        title: str = "ROC Curves (One-vs-Rest)",
        filename: str = "roc_curves.png",
    ) -> str:
        """Plot ROC curves for all classes and save.

        Returns:
            Path to saved image
        """
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(8, 6))

        for cls_name, data in roc_data.get("per_class", {}).items():
            ax.plot(
                data["fpr"],
                data["tpr"],
                label=f"{cls_name} (AUC={data['auc']:.2f})",
            )

        ax.plot([0, 1], [0, 1], "k--", label="Random (AUC=0.50)")
        ax.set_xlabel("False Positive Rate")
        ax.set_ylabel("True Positive Rate")
        ax.set_title(f"{title}  —  Macro AUC={roc_data.get('macro_auc', 0):.2f}")
        ax.legend(loc="lower right", fontsize=8)
        plt.tight_layout()

        out_path = self.output_dir / filename
        fig.savefig(str(out_path), dpi=150)
        plt.close(fig)
        return str(out_path)

    def plot_model_comparison(
        self,
        comparison: Dict[str, Any],
        filename: str = "model_comparison.png",
    ) -> str:
        """Bar chart comparing models across metrics.

        Returns:
            Path to saved image
        """
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        model_keys = [k for k in comparison if "error" not in comparison[k]]
        if not model_keys:
            return ""

        metrics = ["accuracy_mean", "f1_mean", "precision_mean", "recall_mean"]
        metric_labels = ["Accuracy", "F1", "Precision", "Recall"]

        x = np.arange(len(metric_labels))
        width = 0.8 / len(model_keys)

        fig, ax = plt.subplots(figsize=(10, 6))

        for i, model in enumerate(model_keys):
            vals = [comparison[model].get(m, 0) for m in metrics]
            bars = ax.bar(x + i * width, vals, width, label=model)
            # Add value labels on bars
            for bar, val in zip(bars, vals):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.01,
                    f"{val:.2f}",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                )

        ax.set_xlabel("Metric")
        ax.set_ylabel("Score")
        ax.set_title("Model Comparison (Cross-Validated)")
        ax.set_xticks(x + width * (len(model_keys) - 1) / 2)
        ax.set_xticklabels(metric_labels)
        ax.set_ylim(0, 1.15)
        ax.legend()
        plt.tight_layout()

        out_path = self.output_dir / filename
        fig.savefig(str(out_path), dpi=150)
        plt.close(fig)
        return str(out_path)

    # ------------------------------------------------------------------
    # Save full evaluation report as JSON
    # ------------------------------------------------------------------
    def save_evaluation_report(
        self, report: Dict[str, Any], filename: str = "evaluation_report.json"
    ) -> str:
        """Persist evaluation report to JSON."""
        out_path = self.output_dir / filename
        # Strip non-serialisable data (numpy arrays are already converted above)
        with open(out_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        return str(out_path)
