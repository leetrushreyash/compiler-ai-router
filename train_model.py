"""
Training entry point.
Now uses the explainable model training pipeline (Novelty 3)
which includes stacking ensemble + SHAP + per-smell metrics.
Falls back to basic training if SHAP is not installed.
"""
import sys

def main():
    try:
        from code_smell_compiler.ml_model.explainable import train_explainable_model
        print("Training with Explainable ML pipeline (stacking ensemble + SHAP)...")
        metrics = train_explainable_model(400)
        print("\nTraining complete. Metrics:")
        import json
        print(json.dumps(metrics, indent=2))
    except Exception as e:
        print(f"Explainable training failed ({e}), falling back to basic training...")
        from code_smell_compiler.ml_model.train import train_and_save
        train_and_save(400)

if __name__ == '__main__':
    main()
