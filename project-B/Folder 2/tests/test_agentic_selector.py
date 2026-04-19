"""Unit tests for AgenticModelSelector."""
import sys
from pathlib import Path

# Add project root to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agentic_selector import AgenticModelSelector


class DummyModelManager:
    """Simple stub used by selector unit tests."""

    def __init__(self, metadata_list):
        self._metadata_list = metadata_list

    def get_all_models_metadata(self):
        return self._metadata_list


def test_selects_highest_accuracy_model():
    manager = DummyModelManager(
        [
            {"model_name": "svm", "accuracy": 0.71},
            {"model_name": "randomforest", "accuracy": 0.92},
        ]
    )
    selector = AgenticModelSelector(manager)

    result = selector.select_best_model({"function_length": 8, "cyclomatic_complexity": 2})

    assert result["model_name"] == "randomforest"
    assert result["score"] >= 0.0
    assert isinstance(result["reason"], str)


def test_handles_missing_feature_stats():
    manager = DummyModelManager(
        [
            {"model_name": "svm", "train_score": 0.75},
            {"model_name": "randomforest", "train_score": 0.90},
        ]
    )
    selector = AgenticModelSelector(manager)

    result = selector.select_best_model({"has_loop": 1, "function_length": 12})

    assert result["model_name"] == "randomforest"
    assert "feature stats" in result["reason"].lower()


def test_handles_empty_model_list():
    manager = DummyModelManager([])
    selector = AgenticModelSelector(manager)

    result = selector.select_best_model({"function_length": 5})

    assert result["model_name"] == "randomforest"
    assert result["score"] == 0.0


def test_returns_valid_output_schema():
    manager = DummyModelManager([{"model_name": "svm", "accuracy": 0.8}])
    selector = AgenticModelSelector(manager)

    result = selector.select_best_model({"function_length": 5})

    assert isinstance(result, dict)
    assert set(result.keys()) == {"model_name", "score", "reason"}
    assert isinstance(result["model_name"], str)
    assert isinstance(result["score"], float)
    assert isinstance(result["reason"], str)
