"""Model management for training and inference."""
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from pathlib import Path
import json


class ModelManager:
    """Manages model lifecycle: training, evaluation, and inference."""
    
    def __init__(self, model_path: str = "data/models"):
        """
        Initialize model manager.
        
        Args:
            model_path: Path to store/load models
        """
        self.model_path = Path(model_path)
        self.model_path.mkdir(parents=True, exist_ok=True)
        self.models = {}
        self.metadata = {}
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray, 
              model_name: str = "randomforest", **kwargs) -> Dict[str, Any]:
        """
        Train a model.
        
        Args:
            X_train: Training features
            y_train: Training labels
            model_name: Name of model to train
            **kwargs: Additional model parameters
            
        Returns:
            Training results
        """
        from .models import create_model
        
        model = create_model(model_name)
        
        # Train model
        model.fit(X_train, y_train)
        
        # Store model
        self.models[model_name] = model
        
        # Calculate metrics
        train_score = model.score(X_train, y_train)
        
        results = {
            "model_name": model_name,
            "train_score": train_score,
            "samples_trained": len(X_train),
            "features": X_train.shape[1],
        }

        training_feature_list = kwargs.get("training_feature_list")
        if isinstance(training_feature_list, list) and training_feature_list:
            results["training_feature_list"] = training_feature_list

        feature_stats = kwargs.get("feature_stats")
        if isinstance(feature_stats, dict) and feature_stats:
            results["feature_stats"] = feature_stats
        
        self.metadata[model_name] = results
        
        return results
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray, 
                 model_name: str = "randomforest") -> Dict[str, Any]:
        """
        Evaluate a trained model.
        
        Args:
            X_test: Test features
            y_test: Test labels
            model_name: Name of model to evaluate
            
        Returns:
            Evaluation metrics
        """
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' not found")
        
        model = self.models[model_name]
        
        # Basic metrics
        test_score = model.score(X_test, y_test)
        predictions = model.predict(X_test)
        
        # Calculate detailed metrics
        from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
        
        try:
            precision = precision_score(y_test, predictions, average='weighted', zero_division=0)
            recall = recall_score(y_test, predictions, average='weighted', zero_division=0)
            f1 = f1_score(y_test, predictions, average='weighted', zero_division=0)
            cm = confusion_matrix(y_test, predictions).tolist()
        except Exception as e:
            precision = recall = f1 = 0.0
            cm = []
        
        results = {
            "model_name": model_name,
            "accuracy": test_score,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "confusion_matrix": cm,
            "samples_tested": len(X_test),
        }
        
        return results
    
    def predict(self, X: np.ndarray, model_name: str = "randomforest",
                return_proba: bool = False) -> Dict[str, Any]:
        """
        Make predictions using a trained model.
        
        Args:
            X: Feature vectors to predict
            model_name: Name of model to use
            return_proba: Whether to return probabilities
            
        Returns:
            Predictions and optional probabilities
        """
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' not found")
        
        model = self.models[model_name]
        
        predictions = model.predict(X)
        
        result = {
            "model_name": model_name,
            "predictions": predictions.tolist(),
        }
        
        if return_proba and hasattr(model, 'predict_proba'):
            try:
                probabilities = model.predict_proba(X)
                result["probabilities"] = probabilities.tolist()
            except Exception as e:
                result["probabilities_error"] = str(e)
        
        return result
    
    def save(self, model_name: str):
        """Save a trained model to disk."""
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' not found")
        
        from .models import save_model
        
        model = self.models[model_name]
        path = self.model_path / f"{model_name}.pkl"
        
        save_model(model, str(path))
        
        # Save metadata
        metadata_path = self.model_path / f"{model_name}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(self.metadata.get(model_name, {}), f, indent=2)
    
    def load(self, model_name: str):
        """Load a trained model from disk."""
        from .models import load_model
        
        path = self.model_path / f"{model_name}.pkl"
        
        if not path.exists():
            raise FileNotFoundError(f"Model file not found: {path}")
        
        model = load_model(str(path))
        self.models[model_name] = model
        
        # Load metadata if exists
        metadata_path = self.model_path / f"{model_name}_metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                self.metadata[model_name] = json.load(f)
        
        return model
    
    def get_model(self, model_name: str) -> Any:
        """Get a model by name."""
        return self.models.get(model_name)

    def get_all_models_metadata(self) -> List[Dict[str, Any]]:
        """Return metadata for all available models.

        Scans the model directory for files matching "*_metadata.json" so that
        newly added models are picked up automatically.
        """
        metadata_list: List[Dict[str, Any]] = []

        for metadata_path in sorted(self.model_path.glob("*_metadata.json")):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except Exception:
                continue

            if not isinstance(metadata, dict):
                continue

            model_name = metadata.get("model_name")
            if not model_name:
                stem = metadata_path.stem
                if stem.endswith("_metadata"):
                    model_name = stem[:-9]
                else:
                    model_name = stem
                metadata["model_name"] = model_name

            metadata_list.append(metadata)

        return metadata_list


class PredictionAggregator:
    """Aggregate predictions from multiple models."""
    
    @staticmethod
    def ensemble_predict(predictions: List[np.ndarray], 
                        probabilities: Optional[List[np.ndarray]] = None,
                        method: str = "voting") -> Tuple[np.ndarray, np.ndarray]:
        """
        Aggregate predictions from multiple models.
        
        Args:
            predictions: List of prediction arrays
            probabilities: List of probability arrays
            method: Aggregation method (voting, averaging)
            
        Returns:
            Final predictions and confidence scores
        """
        predictions = np.array(predictions)
        
        if method == "voting":
            # Majority voting
            final_pred = np.apply_along_axis(
                lambda x: np.bincount(x.astype(int)).argmax(),
                axis=0,
                arr=predictions
            )
        elif method == "averaging" and probabilities:
            # Probability averaging — pick class with highest average probability
            proba_arrays = np.array(probabilities)
            avg_proba = np.mean(proba_arrays, axis=0)
            final_pred = np.argmax(avg_proba, axis=1)
        else:
            # Fallback to voting
            final_pred = np.apply_along_axis(
                lambda x: np.bincount(x.astype(int)).argmax(),
                axis=0,
                arr=predictions
            )
        
        # Calculate confidence
        if probabilities:
            proba_arrays = np.array(probabilities)
            confidence = np.max(np.mean(proba_arrays, axis=0), axis=1)
        else:
            # Use voting agreement ratio as confidence
            n_models = len(predictions)
            agreement = np.apply_along_axis(
                lambda x: np.max(np.bincount(x.astype(int))) / n_models,
                axis=0,
                arr=predictions
            )
            confidence = agreement
        
        return final_pred, confidence
