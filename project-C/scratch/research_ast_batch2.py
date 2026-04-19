import tree_sitter_cpp
from tree_sitter import Language, Parser

def dump_ast(code):
    CPP_LANGUAGE = Language(tree_sitter_cpp.language())
    parser = Parser(CPP_LANGUAGE)
    tree = parser.parse(code.encode())
    
    def walk(node, depth=0):
        print(f"{'  ' * depth}{node.type}: {node.text.decode('utf-8') if node.child_count == 0 else ''}")
        for child in node.children:
            walk(child, depth + 1)
            
    walk(tree.root_node)

print("--- Double Free Case ---")
dump_ast("void f() { int* p = new int; delete p; delete p; }")

print("\n--- Use-After-Free Case ---")
dump_ast("void f() { int* p = new int; delete p; *p = 10; }")

print("\n--- Command Injection Case ---")
dump_ast("void f(char* cmd) { system(cmd); }")
