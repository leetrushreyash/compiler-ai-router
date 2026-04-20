import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import json
import pickle
import pandas as pd
import tree_sitter_cpp
from tree_sitter import Language, Parser

from security_rules import run_security_scans

# --- Load the ML Model (Global Cache) ---
MODEL = None
def get_model():
    global MODEL
    if MODEL is None:
        try:
            model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                     'archive_non_ast', 'models', 'stacking_code_smell_model.pkl')
            with open(model_path, 'rb') as f:
                MODEL = pickle.load(f)
        except Exception as e:
            print(f"Warning: Could not load code smell model: {e}")
    return MODEL

def analyze_file(filepath):
    CPP_LANGUAGE = Language(tree_sitter_cpp.language())
    parser = Parser(CPP_LANGUAGE)
    
    with open(filepath, 'rb') as f:
        code = f.read()
        
    tree = parser.parse(code)
    root = tree.root_node
    
    # Collect all function AST nodes
    functions = []
    def find_functions(node):
        if node.type in ['function_definition']:
            functions.append(node)
        for child in node.children:
            find_functions(child)
    find_functions(root)
    
    # Load model
    model = get_model()
    
    output_data = {
        "file": filepath,
        "functions": []
    }
    
    for func_node in functions:
        # --- 1. AST Feature Extraction ---
        total_nodes = 0
        if_nodes = 0
        loop_nodes = 0
        max_depth = 0
        param_count = 0
        
        def traverse_and_extract(node, current_depth):
            nonlocal total_nodes, if_nodes, loop_nodes, max_depth, param_count
            total_nodes += 1
            max_depth = max(max_depth, current_depth)
            
            if node.type == 'if_statement':
                if_nodes += 1
            elif node.type in ['for_statement', 'while_statement', 'do_statement']:
                loop_nodes += 1
            elif node.type == 'parameter_list':
                # Count only the actual parameters, ignoring commas etc.
                param_count = sum(1 for c in node.children if c.type in ['parameter_declaration', 'variadic_parameter_declaration'])
                
            for child in node.children:
                traverse_and_extract(child, current_depth + 1)
                
        traverse_and_extract(func_node, 1)
        
        # --- 2. ML Code Smell Prediction ---
        is_smelly = False
        prob_smelly = 0.0
        classification = "Clean"
        
        if model:
            try:
                # Prepare features as expected by the model
                X = pd.DataFrame([{
                    'AST_TotalNodes': total_nodes,
                    'AST_IfCount': if_nodes,
                    'AST_LoopCount': loop_nodes,
                    'AST_MaxDepth': max_depth
                }])
                
                prediction = model.predict(X)[0]
                is_smelly = bool(prediction == 1)
                prob_smelly = model.predict_proba(X)[0][1]
                
                if is_smelly:
                    # Heuristic-based classification based on structural triggers
                    if max_depth > 15:
                        classification = "Deeply Nested Code"
                    elif total_nodes > 250:
                        classification = "God Method / Giant Blob"
                    elif if_nodes > 8:
                        classification = "Spaghetti Code / Complex Branching"
                    elif loop_nodes > 4:
                        classification = "Excessive Looping"
                    elif param_count > 5:
                        classification = "Long Parameter List"
                    else:
                        classification = "General Code Smell"
                
                # Rule-based fallback: Even if ML missed it, we flag long param lists explicitly
                if not is_smelly and param_count > 5:
                    is_smelly = True
                    classification = "Long Parameter List"
                    prob_smelly = 0.8  # Assign a baseline high probability for explicit rules
            except Exception as e:
                print(f"Prediction error for {func_node}: {e}")

        # --- 3. Severity Determination ---
        if not is_smelly:
            smell_severity = "None"
        elif prob_smelly > 0.85:
            smell_severity = "Critical"
        elif prob_smelly > 0.70:
            smell_severity = "High"
        elif prob_smelly > 0.60:
            smell_severity = "Medium"
        else:
            smell_severity = "Low"
            
        # Combine Security Severity
        security_issues = run_security_scans(func_node, code)
        sec_severity = "High" if security_issues else "None"
        
        # Final Severity (Highest of both)
        severity_map = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1, "None": 0}
        final_severity_name = smell_severity
        if severity_map.get(sec_severity, 0) > severity_map.get(smell_severity, 0):
            final_severity_name = sec_severity
            
        # Get cleaner function name
        func_sig = code[func_node.start_byte:func_node.end_byte].decode('utf-8', errors='ignore')
        name_line = func_sig.split('{')[0].strip()
        func_name = name_line.split('(')[0].split()[-1] if '(' in name_line else name_line
        
        output_data["functions"].append({
            "name": func_name,
            "line": func_node.start_point[0], 
            "overall_severity": final_severity_name,
            "code_smell": {
                "is_smelly": is_smelly,
                "classification": classification,
                "probability_score": round(prob_smelly * 100, 2),
                "metrics": {
                    "total_ast_nodes": total_nodes,
                    "max_depth": max_depth,
                    "if_count": if_nodes,
                    "loop_count": loop_nodes,
                    "param_count": param_count
                }
            },
            "security": {
                "has_vulnerabilities": len(security_issues) > 0,
                "issues": security_issues
            },
            "ast_metrics": {  # Retain for backward compatibility if needed
                "total_ast_nodes": total_nodes,
                "max_depth": max_depth,
                "if_count": if_nodes,
                "loop_count": loop_nodes,
                "param_count": param_count,
                "cyclomatic_complexity": 1 + if_nodes + loop_nodes
            }
        })
        
    return output_data

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else '../tests/security_test.cpp'
    import json
    print(json.dumps(analyze_file(target), indent=4))
