import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.multioutput import MultiOutputClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from code_smell_compiler.ml_model.dataset import generate_dataset

ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = ROOT / "ml_model" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

def build_dataframe(samples, labels):
    df_x = pd.DataFrame(samples)
    df_y = pd.DataFrame(labels)
    return df_x.fillna(0), df_y.fillna(0)

def train_and_save(n_samples: int = 300):
    samples, labels = generate_dataset(n_samples)
    X, Y = build_dataframe(samples, labels)

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    rf = MultiOutputClassifier(RandomForestClassifier(n_estimators=50, random_state=42))
    lr = MultiOutputClassifier(LogisticRegression(max_iter=500))

    X_train, X_test, y_train, y_test = train_test_split(Xs, Y, test_size=0.2, random_state=42)

    rf.fit(X_train, y_train)
    lr.fit(X_train, y_train)

    joblib.dump({'rf': rf, 'lr': lr, 'scaler': scaler, 'features': list(X.columns)}, MODEL_DIR / "models.pkl")

    scores = {
        'rf_train': rf.score(X_train, y_train),
        'rf_test': rf.score(X_test, y_test),
        'lr_train': lr.score(X_train, y_train),
        'lr_test': lr.score(X_test, y_test),
    }
    with open(MODEL_DIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2)

    print("Models trained and saved to:", MODEL_DIR / "models.pkl")

if __name__ == '__main__':
    train_and_save(400)
