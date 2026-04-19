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

print("--- Case 1: printf(var) ---")
dump_ast("void f() { printf(var); }")

print("\n--- Case 2: printf(\"%s\", var) ---")
dump_ast("void f() { printf(\"%s\", var); }")

print("\n--- Case 3: fprintf(stderr, var) ---")
dump_ast("void f() { fprintf(stderr, var); }")
