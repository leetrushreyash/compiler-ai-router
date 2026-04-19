import tree_sitter_cpp
from tree_sitter import Language, Parser
import sys

BANNED_FUNCTIONS = ['strcpy', 'strcat', 'sprintf', 'gets', 'scanf']

def extract_calls(node, source_code, found_issues):
    # A function call node in tree-sitter-cpp is typically 'call_expression'
    # Its first child is usually the identifier
    if node.type == 'call_expression':
        # Get the identifier part of the call expression
        func_id_node = node.children[0]
        if func_id_node.type == 'identifier':
            func_name = source_code[func_id_node.start_byte:func_id_node.end_byte].decode('utf-8')
            if func_name in BANNED_FUNCTIONS:
                found_issues.append({
                    'function': func_name,
                    'line': func_id_node.start_point[0] + 1
                })
    
    for child in node.children:
        extract_calls(child, source_code, found_issues)

def scan_file(filepath):
    CPP_LANGUAGE = Language(tree_sitter_cpp.language())
    parser = Parser(CPP_LANGUAGE)
    
    with open(filepath, 'rb') as f:
        code = f.read()
        
    tree = parser.parse(code)
    issues = []
    extract_calls(tree.root_node, code, issues)
    
    print(f"--- Security Scan: {filepath} ---")
    if not issues:
        print("No banned functions found.")
    else:
        for issue in issues:
            print(f"[SECURITY WARNING] Line {issue['line']}: Usage of banned/unsafe function '{issue['function']}'.")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else 'security_test.cpp'
    scan_file(target)
