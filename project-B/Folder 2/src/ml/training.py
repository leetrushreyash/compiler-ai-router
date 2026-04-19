"""Training pipeline for ML models."""
from typing import Dict, List, Tuple, Any, Optional
import json
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler


class DataLoader:
 
    
    @staticmethod
    def load_json(filepath: str) -> Tuple[List[Dict], List[str]]:
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        samples = data.get("samples", [])
        labels = [s.get("label", "unknown") for s in samples]
        
        return samples, labels
    
    @staticmethod
    def load_csv(filepath: str) -> Tuple[np.ndarray, np.ndarray]:
       
        import pandas as pd
        
        df = pd.read_csv(filepath)
        
        # Last column assumed to be label
        X = df.iloc[:, :-1].values
        y = df.iloc[:, -1].values
        
        return X, y


class TrainingPipeline:
     
    
    def __init__(self, output_dir: str = "data/models"):
       
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.training_log = []
    
    def prepare_dataset(self, 
                       samples: List[Dict[str, Any]],
                       feature_extractor: Any) -> Tuple[np.ndarray, np.ndarray, List[str]]:
     
        features_list = []
        labels = []
        label_to_idx = {}
        label_idx = 0
        
        all_feature_names = (
            feature_extractor.get_all_feature_names()
            if hasattr(feature_extractor, "get_all_feature_names")
            else list(getattr(feature_extractor, "feature_names", []))
        )
        self._last_training_feature_list = all_feature_names

        for sample in samples:
            code = sample.get("code", "")
            label = sample.get("label", "unknown")
            
            if not code:
                continue
            
            # Extract features
            features = feature_extractor.extract_features(code)
            feature_vector = feature_extractor.vectorize_features(features)
            features_list.append(feature_vector)
            
            # Map label to index
            if label not in label_to_idx:
                label_to_idx[label] = label_idx
                label_idx += 1
            
            labels.append(label_to_idx[label])
        
        X = np.array(features_list)
        y = np.array(labels)
        label_names = list(label_to_idx.keys())

        if len(features_list) > 0 and all_feature_names:
            X_arr = np.array(features_list)
            means = X_arr.mean(axis=0)
            stds = X_arr.std(axis=0)
            self._last_feature_stats = {
                name: {
                    "mean": float(means[idx]),
                    "std": float(stds[idx]) if float(stds[idx]) > 0 else 1.0,
                }
                for idx, name in enumerate(all_feature_names[: X_arr.shape[1]])
            }
        else:
            self._last_feature_stats = {}
        
        return X, y, label_names
    
    def train_and_evaluate(self,
                          X: np.ndarray,
                          y: np.ndarray,
                          model_name: str = "randomforest",
                          test_size: float = 0.2,
                          random_state: int = 42) -> Dict[str, Any]:
       
        from .model_manager import ModelManager
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        # Train
        manager = ModelManager(str(self.output_dir))
        train_result = manager.train(
            X_train,
            y_train,
            model_name=model_name,
            training_feature_list=getattr(self, "_last_training_feature_list", []),
            feature_stats=getattr(self, "_last_feature_stats", {}),
        )
        
        # Evaluate
        eval_result = manager.evaluate(X_test, y_test, model_name=model_name)
        
        # Cross-validation
        model = manager.get_model(model_name)
        cv_scores = cross_val_score(model, X, y, cv=5)
        
        # Save model
        manager.save(model_name)
        
        # Compile results
        results = {
            "model_name": model_name,
            "training": train_result,
            "evaluation": eval_result,
            "cross_validation": {
                "scores": cv_scores.tolist(),
                "mean": cv_scores.mean(),
                "std": cv_scores.std(),
            },
            "dataset_size": len(X),
            "train_size": len(X_train),
            "test_size": len(X_test),
        }
        
        self.training_log.append(results)
        
        return results
    
    def save_training_log(self, filepath: str = None):
        """Save training results to file."""
        if filepath is None:
            filepath = self.output_dir / "training_log.json"
        
        with open(filepath, 'w') as f:
            json.dump(self.training_log, f, indent=2)
    
    def run_full_pipeline(self,
                         data_file: str,
                         feature_extractor: Any,
                         model_names: List[str] = None) -> Dict[str, Any]:
     
        if model_names is None:
            model_names = ["randomforest", "svm"]
        
        # Load data
        loader = DataLoader()
        samples, _ = loader.load_json(data_file)
        
        # Prepare dataset
        X, y, label_names = self.prepare_dataset(samples, feature_extractor)
        
        # Train models
        results = {
            "models": {},
            "label_names": label_names,
        }
        
        for model_name in model_names:
            try:
                result = self.train_and_evaluate(X, y, model_name=model_name)
                results["models"][model_name] = result
            except Exception as e:
                results["models"][model_name] = {"error": str(e)}
        
        self.save_training_log()
        
        return results


class HyperparameterTuner:
    """Tune hyperparameters using grid search with cross-validation."""
    
    # Default parameter grids per model type
    DEFAULT_GRIDS = {
        "randomforest": {
            "clf__n_estimators": [50, 100, 200],
            "clf__max_depth": [5, 10, 15, None],
            "clf__min_samples_split": [2, 5, 10],
            "clf__min_samples_leaf": [1, 2, 4],
        },
        "svm": {
            "clf__C": [0.1, 1.0, 10.0],
            "clf__kernel": ["rbf", "linear"],
            "clf__gamma": ["scale", "auto"],
        },
    }
    
    @staticmethod
    def grid_search(X: np.ndarray,
                   y: np.ndarray,
                   model_type: str = "randomforest",
                   param_grid: Dict = None,
                   cv: int = 3) -> Dict[str, Any]:
        """Run grid search with cross-validation.
        
        Args:
            X: Feature matrix
            y: Label array
            model_type: Type of model (randomforest, svm)
            param_grid: Custom parameter grid (uses defaults if None)
            cv: Number of cross-validation folds
        
        Returns:
            Dictionary with best params, best score, and all results
        """
        from sklearn.model_selection import GridSearchCV
        from .models import create_model
        
        model = create_model(model_type)
        
        if param_grid is None:
            param_grid = HyperparameterTuner.DEFAULT_GRIDS.get(model_type, {})
        
        # If not enough samples for cv folds, reduce cv
        n_samples = len(X)
        actual_cv = min(cv, n_samples)
        if actual_cv < 2:
            actual_cv = 2
        
        grid = GridSearchCV(
            estimator=model,
            param_grid=param_grid,
            cv=actual_cv,
            scoring="f1_weighted",
            n_jobs=-1,
            error_score=0.0,
            refit=True,
        )
        
        grid.fit(X, y)
        
        return {
            "best_params": grid.best_params_,
            "best_score": grid.best_score_,
            "best_model": grid.best_estimator_,
            "cv_results": {
                "mean_scores": grid.cv_results_["mean_test_score"].tolist(),
                "std_scores": grid.cv_results_["std_test_score"].tolist(),
                "params": [str(p) for p in grid.cv_results_["params"]],
            },
        }


if __name__ == "__main__":
    # Example usage
    from ..analyzer.feature_extractor import FeatureExtractor
    
    pipeline = TrainingPipeline()
    extractor = FeatureExtractor()
    
    # Example samples (would come from JSON file)
    samples = [
        {"code": "api_key = 'secret123'", "label": "hardcoded_secrets"},
        {"code": "x = 1\ny = 2\nz = x + y", "label": "clean"},
    ]
    
    # Prepare and train
    X, y, labels = pipeline.prepare_dataset(samples, extractor)
    print(f"Dataset shape: {X.shape}")
    print(f"Labels: {labels}")
