import tree_sitter_cpp
from tree_sitter import Language, Parser

def parse_cpp_file(filepath):
    # Initialize the C++ language configuration
    CPP_LANGUAGE = Language(tree_sitter_cpp.language())
    parser = Parser(CPP_LANGUAGE)
    
    # Read the C++ file
    with open(filepath, 'rb') as file:
        cpp_code = file.read()
        
    # Generate the Abstract Syntax Tree
    tree = parser.parse(cpp_code)
    root_node = tree.root_node
    
    # Print the raw S-expression (LISP-like AST string)
    print("--- RAW AST (S-Expression) ---")
    print(str(root_node))
    print("\n--- AST Traversing (Finding If Statements) ---")
    
    # Let's count all the if statements recursively
    if_count = 0
    
    def traverse(node):
        nonlocal if_count
        if node.type == 'if_statement':
            if_count += 1
            print(f"Found 'if_statement' at line {node.start_point[0] + 1}")
            
        for child in node.children:
            traverse(child)
            
    traverse(root_node)
    print(f"\nTotal if statements found: {if_count}")

if __name__ == "__main__":
    parse_cpp_file('dummy.cpp')
