class UninitializedVariableRule:
    def check_function(self, func_node, code):
        """
        Scan a function for local variables that are declared without initialization 
        and used before being expressly assigned.
        """
        uninit_vars = set()
        issues = []
        
        def walk(node):
            if node.type == 'declaration':
                # e.g., 'int x;' will have an 'identifier' node child
                for child in node.children:
                    if child.type == 'identifier':
                        var_name = code[child.start_byte:child.end_byte].decode('utf-8', errors='ignore')
                        uninit_vars.add(var_name)
                        
            elif node.type == 'assignment_expression':
                # An assignment updates a value. To be perfectly accurate, we must 
                # evaluate the right hand side first (e.g. x = x + 1 uses x before assigning)
                if len(node.children) >= 3:
                    right = node.children[2]
                    walk(right)
                    
                    left = node.children[0]
                    if left.type == 'identifier':
                        var_name = code[left.start_byte:left.end_byte].decode('utf-8', errors='ignore')
                        if var_name in uninit_vars:
                            uninit_vars.remove(var_name)
                    return # skip normal children iteration since we handled it
                
            elif node.type == 'identifier':
                var_name = code[node.start_byte:node.end_byte].decode('utf-8', errors='ignore')
                if var_name in uninit_vars:
                    issues.append({
                        "message": f"Uninitialized Variable Risk: Variable '{var_name}' is used before being given a value, which may lead to undefined behavior or info leaks.",
                        "line": node.start_point[0],
                        "type": "Security"
                    })
                    uninit_vars.remove(var_name) # Avoid logging multiple times for the same variable
                    
            for child in node.children:
                walk(child)
                
        walk(func_node)
        return issues
