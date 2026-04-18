import joblib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "ml_model" / "models" / "models.pkl"

def load_models() -> Any:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(str(MODEL_PATH) + " not found. Run training first.")
    obj = joblib.load(MODEL_PATH)
    return obj
