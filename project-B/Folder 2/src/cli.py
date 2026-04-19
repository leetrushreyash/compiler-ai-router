"""Command-line interface for the code smell detector."""
import click
from pathlib import Path
from typing import Optional
import sys
from datetime import datetime

from .parser import ASTBuilder
from .analyzer import StaticAnalyzer, FeatureExtractor
from .analyzer.control_flow import ControlFlowAnalyzer, DataFlowAnalyzer
from .rules import RuleEngine
from .ml.model_manager import ModelManager
from .reporting import ReportGenerator
from .config import get_config, load_config
from .agentic_selector import AgenticModelSelector


@click.group()
@click.option('--config', type=click.Path(), help='Path to config file')
@click.pass_context
def cli(ctx, config):
    """ML-Driven Code Smell Detection Compiler."""
    ctx.ensure_object(dict)
    
    if config:
        ctx.obj['config'] = load_config(config)
    else:
        ctx.obj['config'] = get_config()


@cli.command()
@click.option('--input', '-i', type=click.Path(exists=True), required=True, 
              help='Input file or directory to analyze')
@click.option('--output', '-o', type=click.Path(), default='report.json',
              help='Output report file')
@click.option('--format', '-f', type=click.Choice(['json', 'text', 'csv', 'html']),
              default='json', help='Output format')
@click.option('--model', type=str, default='auto',
              help='ML model to use (randomforest, svm, auto)')
@click.option('--use-rules', is_flag=True, default=True,
              help='Enable rule-based detection')
@click.option('--use-ml', is_flag=True, default=False,
              help='Enable ML-based detection')
@click.option('--autofix', is_flag=True, default=False,
              help='Include auto-fix suggestions in report')
@click.option('--apply-fixes', is_flag=True, default=False,
              help='Generate corrected *_fixed.py files')
@click.option('--min-confidence', type=float, default=0.7,
              help='Minimum confidence threshold')
@click.option('--min-severity', type=click.Choice(['LOW', 'MEDIUM', 'HIGH'], case_sensitive=False), default='LOW',
              help='Minimum severity threshold to include in report')
@click.option('--language', type=str, default='python',
              help='Source language (python, java)')
@click.option('--recursive', is_flag=True, default=False,
              help='Recursively analyze subdirectories')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def analyze(ctx, input, output, format, model, use_rules, use_ml, autofix,
            apply_fixes, min_confidence, min_severity, language, recursive, verbose):
    """Analyze code for smells and vulnerabilities."""
    config = ctx.obj['config']
    
    try:
        # Collect files to analyze
        input_path = Path(input)
        files_to_analyze = []
        
        if input_path.is_file():
            files_to_analyze = [input_path]
        elif input_path.is_dir():
            pattern = '**/*.py' if recursive else '*.py'
            files_to_analyze = list(input_path.glob(pattern))
        
        if not files_to_analyze:
            click.echo(f"No files found to analyze", err=True)
            sys.exit(1)
        
        if verbose:
            click.echo(f"Analyzing {len(files_to_analyze)} file(s)...", err=True)
        
        # Initialize components
        parser = ASTBuilder(language)
        analyzer = StaticAnalyzer()
        feature_extractor = FeatureExtractor()
        rule_engine = RuleEngine()
        report = ReportGenerator()
        
        # Optionally initialize ML selector/manager
        model_manager = None
        selector = None
        loaded_ml_models = {}
        if use_ml:
            try:
                model_manager = ModelManager()
                selector = AgenticModelSelector(model_manager)
            except Exception as e:
                click.echo(f"  Warning: Could not initialize ML manager: {e}", err=True)
                click.echo("  Falling back to rule-based analysis only.", err=True)
                use_ml = False
        
        # Optionally initialize auto-fixer
        fixer = None
        if autofix or apply_fixes:
            from .autofix import AutoFixer
            fixer = AutoFixer()

        severity_rank = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
        selected_min_severity = str(min_severity or "LOW").upper()
        
        start_time = datetime.now()
        
        # Analyze each file
        total_issues = 0
        for filepath in files_to_analyze:
            try:
                if verbose:
                    click.echo(f"  Analyzing: {filepath}", err=True)
                
                # Parse code
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()
                
                ast_data = parser.parse_code(code, str(filepath))
                
                file_issues_raw = []
                
                # Apply rule-based detection
                if use_rules:
                    rule_issues = rule_engine.apply_rules(code, str(filepath))
                    file_issues_raw.extend(rule_issues)
                
                # Apply ML detection if enabled and model loaded
                if use_ml and model_manager is not None and selector is not None:
                    try:
                        from .rules.rule_engine import HybridAnalyzer
                        selected_model_name = model
                        features = feature_extractor.extract_features(code)

                        if not selected_model_name or str(selected_model_name).lower() in ("auto", "", "none"):
                            selection = selector.select_best_model(features)
                            selected_model_name = selection.get("model_name", "randomforest")
                            if verbose:
                                click.echo(
                                    f"    Agentic selector chose '{selected_model_name}' "
                                    f"(score={selection.get('score', 0):.3f}): {selection.get('reason', '')}",
                                    err=True,
                                )

                        if selected_model_name not in loaded_ml_models:
                            try:
                                model_manager.load(selected_model_name)
                            except Exception as load_err:
                                if selected_model_name != "randomforest":
                                    click.echo(
                                        f"    Warning: Could not load model '{selected_model_name}': {load_err}",
                                        err=True,
                                    )
                                    click.echo("    Falling back to 'randomforest'.", err=True)
                                    selected_model_name = "randomforest"
                                    model_manager.load(selected_model_name)
                                else:
                                    raise

                            loaded_ml_models[selected_model_name] = model_manager.get_model(selected_model_name)

                        ml_model = loaded_ml_models.get(selected_model_name)
                        if ml_model is None:
                            raise RuntimeError(f"Loaded model '{selected_model_name}' is unavailable")

                        hybrid = HybridAnalyzer(rule_engine, ml_model)
                        ml_issues = hybrid._apply_ml(features, str(filepath))
                        file_issues_raw.extend(ml_issues)
                    except Exception as e:
                        if verbose:
                            click.echo(f"    ML error: {e}", err=True)
                
                for issue in file_issues_raw:
                    issue_severity = str(issue.get('severity', 'LOW')).upper()
                    if issue.get('confidence', 0.0) >= min_confidence and severity_rank.get(issue_severity, 1) >= severity_rank.get(selected_min_severity, 1):
                        from .reporting.report_generator import Issue
                        
                        suggestions = []
                        fixed_code_value = ""
                        if fixer:
                            fix = fixer.suggest_fix(issue, code)
                            if fix.get("fixed_code"):
                                suggestions.append(f"Auto-fix: {fix['fixed_code']}")
                                fixed_code_value = str(fix.get("fixed_code", ""))
                            if fix.get("explanation"):
                                suggestions.append(fix['explanation'])
                            if fix.get("imports_needed"):
                                suggestions.append(f"Add imports: {', '.join(fix['imports_needed'])}")
                        
                        report.add_issue(
                            Issue(
                                file=str(filepath),
                                line=issue['line'],
                                type=issue['type'],
                                severity=issue_severity,
                                confidence=issue['confidence'],
                                explanation=issue['description'],
                                description=issue.get('description', ''),
                                recommendation=issue.get('recommendation', ''),
                                category=issue.get('category', ''),
                                risk_score=float(issue.get('risk_score', 0.0)),
                                cwe=issue.get('cwe', ''),
                                owasp=issue.get('owasp', ''),
                                code_snippet=issue.get('code', ''),
                                fixed_code=fixed_code_value,
                                suggestions=suggestions if suggestions else [],
                            )
                        )
                        total_issues += 1

                if apply_fixes and fixer is not None:
                    try:
                        filtered_for_fix = [
                            issue for issue in file_issues_raw
                            if issue.get('confidence', 0.0) >= min_confidence
                            and severity_rank.get(str(issue.get('severity', 'LOW')).upper(), 1) >= severity_rank.get(selected_min_severity, 1)
                        ]
                        fixed_code = fixer.generate_fixed_code(code, filtered_for_fix)
                        fixed_path = filepath.with_name(f"{filepath.stem}_fixed{filepath.suffix}")
                        with open(fixed_path, 'w', encoding='utf-8') as out_f:
                            out_f.write(fixed_code)
                        if verbose:
                            click.echo(f"    Wrote fixed code: {fixed_path}", err=True)
                    except Exception as fix_err:
                        if verbose:
                            click.echo(f"    Auto-fix generation warning: {fix_err}", err=True)
            
            except Exception as e:
                click.echo(f"Error analyzing {filepath}: {e}", err=True)
                if verbose:
                    import traceback
                    click.echo(traceback.format_exc(), err=True)
        
        end_time = datetime.now()
        report.set_scan_time(start_time, end_time)
        
        # Save report
        report.save(output, format=format)
        
        # Print summary
        summary = report.get_summary()
        click.echo(f"\nAnalysis complete!")
        click.echo(f"Total issues found: {summary['total_issues']}")
        click.echo(f"  HIGH: {summary['severity_summary']['HIGH']}")
        click.echo(f"  MEDIUM: {summary['severity_summary']['MEDIUM']}")
        click.echo(f"  LOW: {summary['severity_summary']['LOW']}")
        click.echo(f"Report saved to: {output}")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


@cli.command()
@click.option('--data', type=click.Path(exists=True), required=True,
              help='Path to training data (JSON)')
@click.option('--model', type=str, default='randomforest',
              help='Model to train (randomforest, svm)')
@click.option('--output-dir', type=click.Path(), default='data/models',
              help='Output directory for trained models')
@click.option('--test-split', type=float, default=0.2,
              help='Test set proportion')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def train(ctx, data, model, output_dir, test_split, verbose):
    """Train ML models on labeled code samples."""
    from .ml.training import TrainingPipeline, DataLoader
    
    try:
        if verbose:
            click.echo(f"Loading training data from {data}", err=True)
        
        # Load data
        loader = DataLoader()
        samples, labels = loader.load_json(data)
        
        if not samples:
            click.echo("No training samples found", err=True)
            sys.exit(1)
        
        if verbose:
            click.echo(f"Loaded {len(samples)} samples", err=True)
        
        # Train pipeline
        pipeline = TrainingPipeline(output_dir)
        feature_extractor = FeatureExtractor()
        
        # Prepare the dataset from raw samples
        X, y, label_names = pipeline.prepare_dataset(samples, feature_extractor)
        
        if verbose:
            click.echo(f"Prepared {X.shape[0]} samples with {X.shape[1]} features", err=True)
            click.echo(f"Labels: {label_names}", err=True)
            click.echo(f"Training {model} model...", err=True)
        
        results = pipeline.train_and_evaluate(
            X=X,
            y=y,
            model_name=model,
            test_size=test_split
        )
        
        click.echo(f"\nTraining complete!")
        click.echo(f"Model: {model}")
        click.echo(f"Accuracy: {results['evaluation']['accuracy']:.2%}")
        click.echo(f"Precision: {results['evaluation']['precision']:.2%}")
        click.echo(f"Recall: {results['evaluation']['recall']:.2%}")
        click.echo(f"F1-Score: {results['evaluation']['f1_score']:.2%}")
        click.echo(f"Model saved to: {output_dir}/{model}.pkl")
        
    except Exception as e:
        click.echo(f"Training error: {e}", err=True)
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


@cli.command()
@click.option('--host', type=str, default='127.0.0.1', show_default=True,
              help='Host to bind the frontend server')
@click.option('--port', type=int, default=5000, show_default=True,
              help='Port to run the frontend server')
def serve(host, port):
    """Run the web dashboard frontend."""
    from .webapp import create_app

    app = create_app()
    click.echo(f"Starting frontend at http://{host}:{port}")
    app.run(host=host, port=port, debug=False)


@cli.command()
@click.option('--input', '-i', type=click.Path(exists=True), required=True,
              help='Code file to test')
@click.option('--model', type=str, default='randomforest',
              help='ML model to use')
@click.option('--model-path', type=click.Path(), default='data/models',
              help='Path to trained models')
@click.pass_context
def predict(ctx, input, model, model_path):
    """Make predictions on code using trained model."""
    try:
        # Load code
        with open(input, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Extract features
        from .analyzer.feature_extractor import FeatureExtractor
        feature_extractor = FeatureExtractor()
        features = feature_extractor.extract_features(code)
        manager = ModelManager(model_path)
        manager.load(model)
        loaded_model = manager.get_model(model)
        target_size = getattr(loaded_model, 'n_features_in_', None)
        feature_vector = feature_extractor.vectorize_features(features, target_size=target_size)
        
        # Load and predict
        manager = ModelManager(model_path)
        
        import numpy as np
        result = manager.predict(
            np.array([feature_vector]),
            model_name=model,
            return_proba=True
        )
        
        click.echo(f"Prediction: {result['predictions'][0]}")
        if 'probabilities' in result:
            click.echo(f"Confidence: {result['probabilities'][0]}")
        
    except Exception as e:
        click.echo(f"Prediction error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def info(ctx):
    """Show configuration and system information."""
    config = ctx.obj['config']
    
    click.echo("Code Smell Detection Compiler - System Information")
    click.echo(f"Version: {config.version}")
    click.echo(f"Project: {config.project_name}")
    click.echo(f"Supported Languages: {', '.join(config.supported_languages)}")
    click.echo(f"ML Model: {config.ml.model_name}")
    click.echo(f"Report Format: {config.report.format}")
    click.echo(f"Log Level: {config.log_level}")


# ==================================================================
# evaluate — train, evaluate, and compare ML models with charts
# ==================================================================
@cli.command()
@click.option('--data', type=click.Path(exists=True), required=True,
              help='Path to training data (JSON)')
@click.option('--models', type=str, default='randomforest,svm',
              help='Comma-separated model names to compare')
@click.option('--output-dir', type=click.Path(), default='data/evaluation',
              help='Output directory for evaluation artefacts')
@click.option('--cv', type=int, default=5, help='Cross-validation folds')
@click.option('--plot', is_flag=True, default=True,
              help='Generate evaluation plots (confusion matrix, ROC, comparison)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def evaluate(ctx, data, models, output_dir, cv, plot, verbose):
    """Evaluate and compare ML models with detailed metrics and charts."""
    from .ml.training import TrainingPipeline, DataLoader
    from .ml.evaluation import ModelEvaluator
    from .ml.models import create_model
    import numpy as np
    from sklearn.model_selection import train_test_split

    try:
        model_names = [m.strip() for m in models.split(',')]
        click.echo(f"Evaluating models: {', '.join(model_names)}")

        # Load & prepare data
        loader = DataLoader()
        samples, _ = loader.load_json(data)
        feature_extractor = FeatureExtractor()
        pipeline = TrainingPipeline(output_dir)
        X, y, label_names = pipeline.prepare_dataset(samples, feature_extractor)
        click.echo(f"Dataset: {X.shape[0]} samples, {X.shape[1]} features, {len(label_names)} classes")
        click.echo(f"Classes: {label_names}")

        evaluator = ModelEvaluator(output_dir)

        # 1) Cross-validation comparison
        click.echo("\n--- Cross-Validation Comparison ---")
        comparison = evaluator.compare_models(X, y, model_names, cv=cv)
        for name, res in comparison.items():
            if 'error' in res:
                click.echo(f"  {name}: ERROR — {res['error']}")
            else:
                click.echo(
                    f"  {name}: Accuracy={res['accuracy_mean']:.2%} ± {res['accuracy_std']:.2%}  "
                    f"F1={res['f1_mean']:.2%}  Precision={res['precision_mean']:.2%}  "
                    f"Recall={res['recall_mean']:.2%}"
                )

        # 2) Train/test split → per-model detailed metrics + ROC
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y if len(set(y)) > 1 else None
        )

        for name in model_names:
            click.echo(f"\n--- Detailed Evaluation: {name} ---")
            try:
                model = create_model(name)
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)

                metrics = evaluator.compute_metrics(y_test, y_pred, label_names)
                click.echo(f"  Accuracy : {metrics['accuracy']:.2%}")
                click.echo(f"  Precision: {metrics['precision_weighted']:.2%}")
                click.echo(f"  Recall   : {metrics['recall_weighted']:.2%}")
                click.echo(f"  F1       : {metrics['f1_weighted']:.2%}")

                if plot:
                    cm_path = evaluator.plot_confusion_matrix(
                        metrics['confusion_matrix'], label_names,
                        title=f"Confusion Matrix — {name}",
                        filename=f"confusion_matrix_{name}.png",
                    )
                    click.echo(f"  Confusion matrix saved: {cm_path}")

                # ROC (needs predict_proba)
                if hasattr(model, 'predict_proba'):
                    y_proba = model.predict_proba(X_test)
                    roc = evaluator.compute_roc_auc(y_test, y_proba, label_names)
                    click.echo(f"  Macro AUC: {roc.get('macro_auc', 0):.3f}")
                    if plot:
                        roc_path = evaluator.plot_roc_curves(
                            roc,
                            title=f"ROC Curves — {name}",
                            filename=f"roc_curves_{name}.png",
                        )
                        click.echo(f"  ROC curves saved: {roc_path}")
            except Exception as e:
                click.echo(f"  Error evaluating {name}: {e}")
                if verbose:
                    import traceback
                    click.echo(traceback.format_exc())

        # 3) Comparison bar chart
        if plot:
            cmp_path = evaluator.plot_model_comparison(comparison)
            if cmp_path:
                click.echo(f"\nModel comparison chart saved: {cmp_path}")

        # 4) Save JSON report
        full_report = {"comparison": comparison, "label_names": label_names}
        rpt_path = evaluator.save_evaluation_report(full_report)
        click.echo(f"Evaluation report saved: {rpt_path}")

    except Exception as e:
        click.echo(f"Evaluation error: {e}", err=True)
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


# ==================================================================
# git-scan — analyse smell history across commits
# ==================================================================
@cli.command('git-scan')
@click.option('--repo', '-r', type=click.Path(exists=True), default='.',
              help='Path to Git repository')
@click.option('--branch', '-b', type=str, default='HEAD',
              help='Branch or ref to scan')
@click.option('--max-commits', '-n', type=int, default=20,
              help='Maximum commits to scan')
@click.option('--output-dir', type=click.Path(), default='data/evaluation',
              help='Output directory')
@click.option('--plot', is_flag=True, default=True,
              help='Generate timeline chart')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def git_scan(repo, branch, max_commits, output_dir, plot, verbose):
    """Scan Git history to track code smell evolution over commits."""
    from .git_integration import GitAnalyzer

    try:
        click.echo(f"Scanning Git repository: {repo}")
        analyzer = GitAnalyzer(repo)

        timeline_data = analyzer.scan_history(branch, max_commits, verbose)

        click.echo(f"\nScanned {timeline_data['commits_scanned']} commits")

        # Print summary table
        click.echo("\n  Commit   | Issues | HIGH | MED  | LOW  | Message")
        click.echo("  " + "-" * 70)
        for entry in timeline_data.get("timeline", []):
            if "error" in entry:
                click.echo(f"  {entry['hash']}  | ERROR: {entry['error'][:40]}")
            else:
                sc = entry.get("severity_counts", {})
                click.echo(
                    f"  {entry['hash']}  | {entry['total_issues']:>5}  | "
                    f"{sc.get('HIGH', 0):>4} | {sc.get('MEDIUM', 0):>4} | "
                    f"{sc.get('LOW', 0):>4} | {entry['message'][:30]}"
                )

        # Save JSON
        json_path = analyzer.save_timeline(timeline_data, output_dir)
        click.echo(f"\nTimeline JSON saved: {json_path}")

        # Plot
        if plot:
            chart_path = analyzer.plot_timeline(timeline_data, output_dir)
            if chart_path:
                click.echo(f"Timeline chart saved: {chart_path}")
            types_path = analyzer.plot_smell_types_timeline(timeline_data, output_dir)
            if types_path:
                click.echo(f"Smell types chart saved: {types_path}")

    except Exception as e:
        click.echo(f"Git scan error: {e}", err=True)
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


# ==================================================================
# autofix — generate fixes for detected issues
# ==================================================================
@cli.command()
@click.option('--input', '-i', type=click.Path(exists=True), required=True,
              help='Input file to analyse and fix')
@click.option('--output', '-o', type=click.Path(), default=None,
              help='Output file for fixed code (default: print to stdout)')
@click.option('--apply', is_flag=True, default=False,
              help='Overwrite input file with fixed code')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def autofix(input, output, apply, verbose):
    """Generate auto-fix suggestions for detected code smells."""
    from .autofix import AutoFixer

    try:
        with open(input, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()

        engine = RuleEngine()
        issues = engine.apply_rules(code, input)

        if not issues:
            click.echo("No issues found — code is clean!")
            return

        click.echo(f"Found {len(issues)} issue(s). Generating fixes...\n")

        fixer = AutoFixer()
        fixes = fixer.suggest_fixes_for_file(issues, code)

        for fix in fixes:
            stype = fix.get("smell_type", "unknown")
            line = fix.get("line", "?")
            click.echo(f"[{stype}] Line {line}:")
            click.echo(f"  Original : {fix.get('original_code', '')[:80]}")
            if fix.get("fixed_code"):
                click.echo(f"  Fixed    : {fix['fixed_code'][:80]}")
            click.echo(f"  Explain  : {fix.get('explanation', '')[:120]}")
            if fix.get("imports_needed"):
                click.echo(f"  Imports  : {', '.join(fix['imports_needed'])}")
            click.echo()

        if apply or output:
            fixed_code = fixer.apply_fixes(code, fixes)
            target = input if apply else output
            with open(target, 'w', encoding='utf-8') as f:
                f.write(fixed_code)
            click.echo(f"Fixed code written to: {target}")

    except Exception as e:
        click.echo(f"Autofix error: {e}", err=True)
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
