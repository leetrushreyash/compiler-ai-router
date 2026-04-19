import tree_sitter_cpp
from tree_sitter import Language, Parser
import sys

def check_memory_leaks(node, source_code, leaks):
    if node.type == 'function_definition':
        news = 0
        deletes = 0
        
        def count_allocations(child_node):
            nonlocal news, deletes
            if child_node.type == 'new_expression':
                news += 1
            elif child_node.type == 'delete_expression':
                deletes += 1
            for child in child_node.children:
                count_allocations(child)
                
        count_allocations(node)
        
        if news > deletes:
            # Get the function name
            func_name = "Unknown Function"
            for child in node.children:
                if child.type == 'function_declarator':
                    id_node = child.children[0]
                    if id_node.type == 'identifier':
                        func_name = source_code[id_node.start_byte:id_node.end_byte].decode('utf-8')
                    break
            
            leaks.append({
                'function': func_name,
                'news': news,
                'deletes': deletes,
                'line': node.start_point[0] + 1
            })
            
    for child in node.children:
        check_memory_leaks(child, source_code, leaks)

def scan_leaks(filepath):
    CPP_LANGUAGE = Language(tree_sitter_cpp.language())
    parser = Parser(CPP_LANGUAGE)
    
    with open(filepath, 'rb') as f:
        code = f.read()
        
    tree = parser.parse(code)
    leaks = []
    check_memory_leaks(tree.root_node, code, leaks)
    
    print(f"--- Memory Leak Scan: {filepath} ---")
    if not leaks:
        print("No obvious function-scope memory leaks detected.")
    else:
        for leak in leaks:
            print(f"[LEAK WARNING] Line {leak['line']}: Function '{leak['function']}' allocates memory {leak['news']} time(s) but deletes {leak['deletes']} time(s).")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else 'security_test.cpp'
    scan_leaks(target)
