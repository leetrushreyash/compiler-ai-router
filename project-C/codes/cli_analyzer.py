import sys
import json
import os
from static_analyzer import MetricExtractor
from dsl_parser import evaluate_dsl

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No file provided"}))
        return

    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(json.dumps({"error": f"File not found: {file_path}"}))
        return

    extractor = MetricExtractor(file_path)
    metrics = extractor.extract_metrics()
    
    # Needs absolute path to rules.dsl since this might run from anywhere
    script_dir = os.path.dirname(os.path.abspath(__file__))
    rules_path = os.path.join(script_dir, "rules.dsl")
    
    smells = evaluate_dsl(rules_path, metrics)
    
    output = {
        "metrics": metrics,
        "smells": smells,
        "is_smelly": len(smells) > 0
    }
    
    # IMPORTANT: The VS Code extension reads from STDOUT, so just print the JSON
    print(json.dumps(output))

if __name__ == "__main__":
    main()
