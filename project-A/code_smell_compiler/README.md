# ML-Driven Code Smell Detection Compiler

Project scaffold for a compiler-style static analysis system with AST traversal and ML-based detection.

Supported smells (rule-based + ML):
- Hardcoded secrets
- Unsafe eval/exec
- Exception swallowing
- Deep nesting / nested loops
- Long method
- Duplicate code blocks
- God class
- Feature envy
- Data class

## Four Novel Features

### Novelty 1: Auto-Refactoring Engine with Code Diff Generation
Generates concrete refactored code patches (unified diffs) for every detected smell.
No existing tool (Pylint, SonarQube, Radon) produces ready-to-apply code patches.
Supports: long_method → extract helper, exception_swallowing → inject logging,
data_class → @dataclass conversion, feature_envy → move method, god_class → split
by attribute affinity, hardcoded_secrets → os.environ, eval → ast.literal_eval, etc.

### Novelty 2: Smell Co-occurrence & Interaction Graph
Analyses how code smells interact at the project level using Phi-coefficient
correlation, weighted interaction amplification, composite risk scoring, and
Mermaid-syntax interaction graphs. No existing tool performs this analysis.

### Novelty 3: Explainable ML Predictions with SHAP + Stacking Ensemble
Combines RandomForest + LogisticRegression in a stacking ensemble with a meta-learner.
Every ML prediction includes SHAP-based feature attribution explaining *why* a smell
was flagged. Reports per-smell precision/recall/F1 instead of just aggregate accuracy.

### Novelty 4: Risk-Aware Smell Prioritization
Ranks all detected smells using a blended score that accounts for severity, intrinsic
smell weight, model confidence, and file-level risk (co-occurrence amplification).
Outputs P0–P3 bands with rationale to triage what to fix first.

## Usage

1. Install dependencies:

```bash
pip install -r code_smell_compiler/requirements.txt
```

2. Train models (with explainable ML):

```bash
python train_model.py
```

3. Run analysis with all novelties:

```bash
python -m code_smell_compiler.main examples --use-ml --refactor --correlate --explain
```

### CLI flags:
| Flag | Description |
|------|-------------|
| `--use-ml` | Enable ML-based predictions |
| `--refactor` | **[Novelty 1]** Generate auto-refactoring patches |
| `--correlate` | **[Novelty 2]** Run smell co-occurrence analysis |
| `--explain` | **[Novelty 3]** Show SHAP-based ML explanations |
| `--prioritize` | **[Novelty 4]** Rank smells with risk-aware priority bands |
| `--output FILE` | Write full JSON report to a file (default: report.json) |

Samples that intentionally trigger smells (in `examples/`):
- `bad_example.py`: hardcoded secret, exception swallowing, unsafe eval/exec
- `long_method_example.py`: long method
- `god_class_example.py`: god class
- `feature_envy_example.py`: feature envy
- `data_class_example.py`: data class

Training artifacts are written to `ml_model/models/` (`models.pkl`, `metrics.json`).
