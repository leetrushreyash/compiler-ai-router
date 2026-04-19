import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import json
import tree_sitter_cpp
from tree_sitter import Language, Parser

from security_rules import run_security_scans

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
    
    # (ML model loading removed as part of AST isolation)
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
        
        def traverse_and_extract(node, current_depth):
            nonlocal total_nodes, if_nodes, loop_nodes, max_depth
            total_nodes += 1
            max_depth = max(max_depth, current_depth)
            
            if node.type == 'if_statement':
                if_nodes += 1
            elif node.type in ['for_statement', 'while_statement', 'do_statement']:
                loop_nodes += 1
                
            for child in node.children:
                traverse_and_extract(child, current_depth + 1)
                
        traverse_and_extract(func_node, 1)
        
        # (ML Code Smell prediction removed - pure AST analysis only)
            
        # --- 4. Security Vulnerability Scan (Modular) ---
        security_issues = run_security_scans(func_node, code)
            
        sec_severity = "High" if security_issues else "None"
            
        # Get cleaner function name
        func_sig = code[func_node.start_byte:func_node.end_byte].decode('utf-8', errors='ignore')
        name_line = func_sig.split('{')[0].strip()
        func_name = name_line.split('(')[0].split()[-1] if '(' in name_line else name_line
        
        output_data["functions"].append({
            "name": func_name,
            "line": func_node.start_point[0], # 0-indexed line for VS Code
            "overall_severity": sec_severity,
            "ast_metrics": {
                "total_ast_nodes": total_nodes,
                "max_depth": max_depth,
                "if_count": if_nodes,
                "loop_count": loop_nodes
            },
            "security": {
                "has_vulnerabilities": len(security_issues) > 0,
                "issues": security_issues
            }
        })
        
    return output_data

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else '../tests/security_test.cpp'
    import json
    print(json.dumps(analyze_file(target), indent=4))
