"""Agentic model selector for choosing the best ML model per input features."""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class AgenticModelSelector:
    """Select the best available ML model using metadata and feature similarity."""

    def __init__(self, model_manager):
        """Initialize selector with an existing ModelManager instance."""
        self.model_manager = model_manager

    def select_best_model(self, features: dict) -> dict:
        """Select best model for the given extracted features.

        Returns:
            {
                "model_name": str,
                "score": float,
                "reason": str,
            }
        """
        metadata_list = self.model_manager.get_all_models_metadata()

        if not metadata_list:
            return {
                "model_name": "randomforest",
                "score": 0.0,
                "reason": "No model metadata found; falling back to default model randomforest.",
            }

        best = None
        best_score = -1.0
        best_reason = ""

        for metadata in metadata_list:
            model_name = str(metadata.get("model_name") or metadata.get("name") or "").strip() or "unknown"
            accuracy = self._extract_accuracy(metadata)
            feature_similarity = self._calculate_feature_similarity(features, metadata)

            if feature_similarity is None:
                score = accuracy
                reason = (
                    f"Selected {model_name} based on available accuracy only "
                    f"({accuracy:.3f}); feature stats were unavailable."
                )
            else:
                score = (0.6 * accuracy) + (0.4 * feature_similarity)
                reason = (
                    f"Selected {model_name} due to strong combined score from "
                    f"accuracy ({accuracy:.3f}) and feature similarity ({feature_similarity:.3f})."
                )

            if score > best_score:
                best = model_name
                best_score = score
                best_reason = reason

        if best is None:
            return {
                "model_name": "randomforest",
                "score": 0.0,
                "reason": "Could not determine best model; falling back to default model randomforest.",
            }

        return {
            "model_name": best,
            "score": round(float(best_score), 4),
            "reason": best_reason,
        }

    @staticmethod
    def _extract_accuracy(metadata: Dict[str, Any]) -> float:
        """Extract an accuracy-like value from model metadata."""
        candidates = [
            metadata.get("accuracy"),
            metadata.get("train_score"),
            metadata.get("score"),
        ]
        for value in candidates:
            if isinstance(value, (int, float)):
                return max(0.0, min(1.0, float(value)))
        return 0.0

    def _calculate_feature_similarity(self, features: Dict[str, Any], metadata: Dict[str, Any]) -> Optional[float]:
        """Calculate feature similarity using metadata feature stats when available.

        Returns value in [0, 1] or None when stats are unavailable.
        """
        feature_stats = metadata.get("feature_stats")
        if not isinstance(feature_stats, dict) or not feature_stats:
            return None

        similarities: List[float] = []

        for name, value in features.items():
            if not isinstance(value, (int, float)):
                continue

            mean_std = self._resolve_mean_std(feature_stats, name)
            if mean_std is None:
                continue

            mean, std = mean_std
            scale = max(abs(float(std)), 1e-6)
            distance = abs(float(value) - float(mean)) / scale
            similarities.append(max(0.0, 1.0 - min(distance, 1.0)))

        if not similarities:
            return None

        return float(sum(similarities) / len(similarities))

    @staticmethod
    def _resolve_mean_std(feature_stats: Dict[str, Any], feature_name: str) -> Optional[tuple]:
        """Resolve mean/std for a feature from different metadata shapes."""
        direct = feature_stats.get(feature_name)
        if isinstance(direct, dict):
            mean = direct.get("mean")
            std = direct.get("std")
            if isinstance(mean, (int, float)) and isinstance(std, (int, float)):
                return float(mean), float(std)

        means = feature_stats.get("means")
        stds = feature_stats.get("stds")
        if isinstance(means, dict) and isinstance(stds, dict):
            mean = means.get(feature_name)
            std = stds.get(feature_name)
            if isinstance(mean, (int, float)) and isinstance(std, (int, float)):
                return float(mean), float(std)

        return None
