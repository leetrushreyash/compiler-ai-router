"""ML model definitions and creation."""
from typing import Any, Optional
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib


def create_model(model_type: str = "randomforest") -> Any:
    
    if model_type == "randomforest":
        return Pipeline([
            ('scaler', StandardScaler()),
            ('clf', RandomForestClassifier(
                n_estimators=100,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            ))
        ])
    
    elif model_type == "svm":
        return Pipeline([
            ('scaler', StandardScaler()),
            ('clf', SVC(
                kernel='rbf',
                C=1.0,
                gamma='scale',
                probability=True,
                random_state=42
            ))
        ])
    
    else:
        raise ValueError(f"Unknown model type: {model_type}")


def load_model(path: str) -> Any:
  
    try:
        model = joblib.load(path)
        return model
    except Exception as e:
        raise RuntimeError(f"Failed to load model from {path}: {e}")


def save_model(model: Any, path: str):
   
    try:
        joblib.dump(model, path)
    except Exception as e:
        raise RuntimeError(f"Failed to save model to {path}: {e}")


class EnsembleModel:
 
    
    def __init__(self, models: dict):
  
         
        self.models = models
    
    def predict(self, X):
         
        predictions = []
        for model in self.models.values():
            predictions.append(model.predict(X))
        
        # Majority voting
        import numpy as np
        predictions = np.array(predictions)
        result = np.apply_along_axis(lambda x: np.bincount(x).argmax(), axis=0, arr=predictions)
        return result
    
    def predict_proba(self, X):
        
        probas = []
        for model in self.models.values():
            if hasattr(model, 'predict_proba'):
                probas.append(model.predict_proba(X))
        
        if not probas:
            return None
        
        import numpy as np
        return np.mean(probas, axis=0)


class AdaptiveModel:
     
    
    def __init__(self, base_model: Any):
       
        self.base_model = base_model
        self.cache = {}
    
    def predict(self, X):
        
        # Convert to hashable format
        key = str(X)
        
        if key in self.cache:
            return self.cache[key]
        
        prediction = self.base_model.predict(X)
        self.cache[key] = prediction
        return prediction
    
    def update(self, X, y):
        
        self.base_model.fit(X, y)
        self.cache.clear()
