import os
import pandas as pd
import tree_sitter_cpp
from tree_sitter import Language, Parser

def extract_features():
    print("Loading CSV...")
    # Read the original labels and locations
    df = pd.read_csv('../extracted_dataset/labeled_cpp_dataset.csv')
    
    # Initialize parser
    CPP_LANGUAGE = Language(tree_sitter_cpp.language())
    parser = Parser(CPP_LANGUAGE)
    
    # Group by FileName to avoid parsing the same file 100 times
    grouped = df.groupby('FileName')
    
    results = []
    
    print("Parsing files and extracting AST features...")
    for filename, group in grouped:
        filepath = None
        for root_dir, dirs, files in os.walk('../extracted_dataset/cpp_dataset_folder'):
            if filename in files:
                filepath = os.path.join(root_dir, filename)
                break
                
        if not filepath:
            print(f"Skipping {filename}: Not found anywhere in cpp_dataset_folder")
            continue
            
        with open(filepath, 'rb') as f:
            code = f.read()
            
        tree = parser.parse(code)
        root = tree.root_node
        
        # We will do a generic walk to collect all function AST nodes
        # so we can quickly match them.
        functions = []
        
        def find_functions(node):
            if node.type in ['function_definition']:
                functions.append(node)
            for child in node.children:
                find_functions(child)
                
        find_functions(root)
        
        for idx, row in group.iterrows():
            full_method = str(row['MethodName'])
            # e.g., CFlockingFlyer::IsLeader -> IsLeader
            method_short = full_method.split('::')[-1] if '::' in full_method else full_method
            
            # Find the best matching AST node (approximate by finding the identifier)
            target_node = None
            for func_node in functions:
                # Get the code slice for the function to see if it matches
                func_code = code[func_node.start_byte:func_node.end_byte].decode('utf-8', errors='ignore')
                if method_short in func_code.split('(')[0]: # Match name roughly
                    target_node = func_node
                    break
                    
            if target_node:
                # Structural Metrics
                total_nodes = 0
                if_nodes = 0
                loop_nodes = 0
                max_depth = 0
                param_count = 0
                
                def extract_structural(node, current_depth):
                    nonlocal total_nodes, if_nodes, loop_nodes, max_depth, param_count
                    total_nodes += 1
                    max_depth = max(max_depth, current_depth)
                    
                    if node.type == 'if_statement':
                        if_nodes += 1
                    elif node.type in ['for_statement', 'while_statement', 'do_statement']:
                        loop_nodes += 1
                    elif node.type == 'parameter_list':
                        param_count = sum(1 for c in node.children if c.type in ['parameter_declaration', 'variadic_parameter_declaration'])
                        
                    for child in node.children:
                        extract_structural(child, current_depth + 1)
                        
                extract_structural(target_node, 1)
                
                results.append({
                    'FileName': filename,
                    'MethodName': full_method,
                    'AST_TotalNodes': total_nodes,
                    'AST_IfCount': if_nodes,
                    'AST_LoopCount': loop_nodes,
                    'AST_MaxDepth': max_depth,
                    'AST_ParamCount': param_count,
                    'Smell_Label': row['Smell_Label']
                })

    
    final_df = pd.DataFrame(results)
    print(f"Extraction complete! Found ASTs for {len(final_df)} methods.")
    out_path = 'ast_features_dataset.csv'
    final_df.to_csv(out_path, index=False)
    print(f"Saved AST features to {out_path}")

if __name__ == "__main__":
    extract_features()
