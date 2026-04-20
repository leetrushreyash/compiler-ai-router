
import tree_sitter_cpp
from tree_sitter import Language, Parser

def inspect_params(filepath):
    CPP_LANGUAGE = Language(tree_sitter_cpp.language())
    parser = Parser(CPP_LANGUAGE)
    
    with open(filepath, 'rb') as file:
        code = file.read()
        
    tree = parser.parse(code)
    root = tree.root_node
    
    def find_functions(node):
        if node.type == 'function_definition':
            print(f"\nFunction: {node.type}")
            # Look for declarator
            declarator = node.child_by_field_name('declarator')
            if declarator:
                print(f"  Declarator: {declarator.type}")
                # Look for parameter_list
                # Sometimes it is nested inside other declarators (like pointer_declarator)
                param_list = None
                def search_param_list(n):
                    nonlocal param_list
                    if n.type == 'parameter_list':
                        param_list = n
                        return
                    for child in n.children:
                        search_param_list(child)
                
                search_param_list(declarator)
                
                if param_list:
                    print(f"  Found Parameter List: {param_list.type}")
                    param_count = sum(1 for c in param_list.children if c.type in ['parameter_declaration', 'variadic_parameter_declaration'])
                    print(f"  Parameter Count: {param_count}")
                    for p in param_list.children:
                        if p.type == 'parameter_declaration':
                            print(f"    Param: {p.type} -> {code[p.start_byte:p.end_byte].decode()}")

        for child in node.children:
            find_functions(child)

    find_functions(root)

if __name__ == "__main__":
    inspect_params('c:\\Users\\aksha\\OneDrive\\Desktop\\Compiler Design\\ast_analysis\\scratch\\test_params.cpp')
