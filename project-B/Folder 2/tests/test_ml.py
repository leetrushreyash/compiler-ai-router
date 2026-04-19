"""Tests for ML models, model manager, and training pipeline."""
import pytest
import sys
import os
import json
import tempfile
import numpy as np
from pathlib import Path

# Add project root to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ml.models import create_model, save_model, load_model, EnsembleModel
from src.ml.model_manager import ModelManager
from src.ml.training import DataLoader, TrainingPipeline
from src.analyzer.feature_extractor import FeatureExtractor


# ──────────────────────────────────────────────────────────
#  create_model Tests
# ──────────────────────────────────────────────────────────

class TestCreateModel:
    """Tests for create_model factory."""

    def test_create_randomforest(self):
        """Test creating a RandomForest pipeline."""
        model = create_model("randomforest")
        assert model is not None
        assert hasattr(model, "fit")
        assert hasattr(model, "predict")

    def test_create_svm(self):
        """Test creating an SVM pipeline."""
        model = create_model("svm")
        assert model is not None
        assert hasattr(model, "fit")

    def test_create_unknown_raises(self):
        """Test that unknown model type raises ValueError."""
        with pytest.raises(ValueError):
            create_model("unknown_model_xyz")


# ──────────────────────────────────────────────────────────
#  save/load model Tests
# ──────────────────────────────────────────────────────────

class TestSaveLoadModel:
    """Tests for save_model and load_model."""

    def test_save_and_load(self):
        """Test round-trip save and load of a trained model."""
        model = create_model("randomforest")
        X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
        y = np.array([0, 1, 0, 1])
        model.fit(X, y)

        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
            tmp = f.name
        try:
            save_model(model, tmp)
            loaded = load_model(tmp)
            preds = loaded.predict(X)
            assert len(preds) == 4
        finally:
            os.unlink(tmp)

    def test_load_nonexistent_raises(self):
        """Test loading from missing path raises RuntimeError."""
        with pytest.raises(RuntimeError):
            load_model("nonexistent_model.pkl")


# ──────────────────────────────────────────────────────────
#  EnsembleModel Tests
# ──────────────────────────────────────────────────────────

class TestEnsembleModel:
    """Tests for EnsembleModel."""

    def _train_models(self):
        X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
        y = np.array([0, 1, 0, 1])
        rf = create_model("randomforest")
        svm = create_model("svm")
        rf.fit(X, y)
        svm.fit(X, y)
        return {"rf": rf, "svm": svm}, X, y

    def test_ensemble_predict(self):
        """Test ensemble voting prediction."""
        models, X, _ = self._train_models()
        ensemble = EnsembleModel(models)
        preds = ensemble.predict(X)
        assert len(preds) == 4

    def test_ensemble_predict_proba(self):
        """Test ensemble probability averaging."""
        models, X, _ = self._train_models()
        ensemble = EnsembleModel(models)
        proba = ensemble.predict_proba(X)
        assert proba is not None
        assert proba.shape[0] == 4


# ──────────────────────────────────────────────────────────
#  ModelManager Tests
# ──────────────────────────────────────────────────────────

class TestModelManager:
    """Tests for ModelManager."""

    def test_init_creates_directory(self):
        """Test model directory is created on init."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "models")
            manager = ModelManager(path)
            assert os.path.isdir(path)

    def test_train_model(self):
        """Test training a model through the manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModelManager(tmpdir)
            X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
            y = np.array([0, 1, 0, 1])
            result = manager.train(X, y, model_name="randomforest")
            assert "train_score" in result
            assert result["samples_trained"] == 4

    def test_evaluate_model(self):
        """Test evaluating a trained model."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModelManager(tmpdir)
            X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
            y = np.array([0, 1, 0, 1])
            manager.train(X, y, model_name="randomforest")
            result = manager.evaluate(X, y, model_name="randomforest")
            assert "accuracy" in result
            assert "precision" in result
            assert "recall" in result
            assert "f1_score" in result

    def test_evaluate_untrained_raises(self):
        """Test evaluating an untrained model raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModelManager(tmpdir)
            X = np.array([[1, 2]])
            y = np.array([0])
            with pytest.raises(ValueError):
                manager.evaluate(X, y, model_name="nonexistent")

    def test_predict(self):
        """Test making predictions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModelManager(tmpdir)
            X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
            y = np.array([0, 1, 0, 1])
            manager.train(X, y, model_name="randomforest")
            result = manager.predict(X, model_name="randomforest")
            assert "predictions" in result
            assert len(result["predictions"]) == 4

    def test_predict_with_proba(self):
        """Test predictions with probability."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModelManager(tmpdir)
            X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
            y = np.array([0, 1, 0, 1])
            manager.train(X, y, model_name="randomforest")
            result = manager.predict(X, model_name="randomforest", return_proba=True)
            assert "probabilities" in result or "probabilities_error" in result

    def test_predict_untrained_raises(self):
        """Test predicting with untrained model raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModelManager(tmpdir)
            X = np.array([[1, 2]])
            with pytest.raises(ValueError):
                manager.predict(X, model_name="nonexistent")

    def test_save_and_load_model(self):
        """Test saving and reloading a model through the manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModelManager(tmpdir)
            X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
            y = np.array([0, 1, 0, 1])
            manager.train(X, y, model_name="randomforest")
            manager.save("randomforest")

            # New manager, load from disk
            manager2 = ModelManager(tmpdir)
            manager2.load("randomforest")
            result = manager2.predict(X, model_name="randomforest")
            assert len(result["predictions"]) == 4

    def test_load_nonexistent_raises(self):
        """Test loading a model that doesn't exist raises FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModelManager(tmpdir)
            with pytest.raises(FileNotFoundError):
                manager.load("nonexistent_model")

    def test_get_model(self):
        """Test get_model returns model or None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModelManager(tmpdir)
            assert manager.get_model("randomforest") is None
            X = np.array([[1, 2], [3, 4]])
            y = np.array([0, 1])
            manager.train(X, y, model_name="randomforest")
            assert manager.get_model("randomforest") is not None


# ──────────────────────────────────────────────────────────
#  DataLoader Tests
# ──────────────────────────────────────────────────────────

class TestDataLoader:
    """Tests for DataLoader."""

    def test_load_json(self):
        """Test loading training data from JSON."""
        data = {
            "samples": [
                {"code": "password = 'x'", "label": "hardcoded_secrets"},
                {"code": "x = 1", "label": "clean"},
            ]
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            tmp = f.name
        try:
            samples, labels = DataLoader.load_json(tmp)
            assert len(samples) == 2
            assert labels == ["hardcoded_secrets", "clean"]
        finally:
            os.unlink(tmp)

    def test_load_json_empty(self):
        """Test loading JSON with no samples."""
        data = {"samples": []}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            tmp = f.name
        try:
            samples, labels = DataLoader.load_json(tmp)
            assert len(samples) == 0
        finally:
            os.unlink(tmp)

    def test_load_project_training_data(self):
        """Test loading the actual project training data file."""
        path = Path(__file__).parent.parent / "data" / "training_data.json"
        if path.exists():
            samples, labels = DataLoader.load_json(str(path))
            assert len(samples) > 0
            assert len(labels) == len(samples)


# ──────────────────────────────────────────────────────────
#  TrainingPipeline Tests
# ──────────────────────────────────────────────────────────

class TestTrainingPipeline:
    """Tests for TrainingPipeline."""

    def test_prepare_dataset(self):
        """Test preparing dataset from code samples."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = TrainingPipeline(tmpdir)
            extractor = FeatureExtractor()
            samples = [
                {"code": "password = 'x'", "label": "hardcoded_secrets"},
                {"code": "x = 1\ny = 2", "label": "clean"},
                {"code": "import os", "label": "clean"},
            ]
            X, y, label_names = pipeline.prepare_dataset(samples, extractor)
            assert X.shape[0] == 3
            assert X.shape[1] == len(extractor.get_all_feature_names())
            assert len(y) == 3
            assert "hardcoded_secrets" in label_names
            assert "clean" in label_names

    def test_prepare_dataset_skips_empty_code(self):
        """Test that samples with empty code are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = TrainingPipeline(tmpdir)
            extractor = FeatureExtractor()
            samples = [
                {"code": "", "label": "empty"},
                {"code": "x = 1", "label": "clean"},
            ]
            X, y, label_names = pipeline.prepare_dataset(samples, extractor)
            assert X.shape[0] == 1

    def test_train_and_evaluate(self):
        """Test full training and evaluation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = TrainingPipeline(tmpdir)
            extractor = FeatureExtractor()
            samples = [
                {"code": "password = 'secret123'", "label": "hardcoded_secrets"},
                {"code": "api_key = 'sk_live_abc'", "label": "hardcoded_secrets"},
                {"code": "token = 'tok_test_xyz'", "label": "hardcoded_secrets"},
                {"code": "x = 1\ny = 2\nz = x + y", "label": "clean"},
                {"code": "def add(a,b): return a+b", "label": "clean"},
                {"code": "result = sum([1,2,3])", "label": "clean"},
                {"code": "import os\nprint(os.getcwd())", "label": "clean"},
                {"code": "for i in range(10): print(i)", "label": "clean"},
            ]
            X, y, label_names = pipeline.prepare_dataset(samples, extractor)
            results = pipeline.train_and_evaluate(X, y, model_name="randomforest", test_size=0.25)
            assert "evaluation" in results
            assert "accuracy" in results["evaluation"]
            assert "training_feature_list" in results["training"]
            assert "feature_stats" in results["training"]

    def test_training_log(self):
        """Test training log is populated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = TrainingPipeline(tmpdir)
            extractor = FeatureExtractor()
            # Need at least 10 samples so cv=5 has enough per class
            samples = [
                {"code": "password = 'x'", "label": "bad"},
                {"code": "x = 1", "label": "good"},
                {"code": "y = 2", "label": "good"},
                {"code": "secret = 'abc'", "label": "bad"},
                {"code": "a = 1\nb = 2", "label": "good"},
                {"code": "tok = 'xyz'", "label": "bad"},
                {"code": "c = 3\nd = 4", "label": "good"},
                {"code": "api_key = 'k'", "label": "bad"},
                {"code": "e = 5\nf = 6", "label": "good"},
                {"code": "pw = '123'", "label": "bad"},
            ]
            X, y, _ = pipeline.prepare_dataset(samples, extractor)
            pipeline.train_and_evaluate(X, y, model_name="randomforest", test_size=0.25)
            assert len(pipeline.training_log) == 1

    def test_save_training_log(self):
        """Test saving training log to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = TrainingPipeline(tmpdir)
            pipeline.training_log = [{"model": "test", "accuracy": 0.9}]
            log_path = os.path.join(tmpdir, "log.json")
            pipeline.save_training_log(log_path)
            assert os.path.exists(log_path)
            data = json.loads(Path(log_path).read_text())
            assert len(data) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
