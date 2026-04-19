class NullPointerDereferenceRule:
    def check_function(self, func_node, code):
        """
        Scan a function body for pointers initialized to null and dereferenced without reassignment.
        """
        known_nulls = set()
        issues = []
        
        def walk(node):
            # 1. Track variables initialized to null
            if node.type == 'declaration':
                for child in node.children:
                    if child.type == 'init_declarator':
                        declarator = None
                        is_null = False
                        for c in child.children:
                            if c.type in ['pointer_declarator', 'identifier']:
                                declarator = c
                            if c.type == 'null': # tree-sitter detects 'nullptr' as 'null' node
                                is_null = True
                            if c.type == 'identifier':
                                ident_text = code[c.start_byte:c.end_byte].decode('utf-8', errors='ignore')
                                if ident_text == 'NULL':
                                    is_null = True
                                
                        if declarator and is_null:
                            ident = None
                            if declarator.type == 'pointer_declarator':
                                for cc in declarator.children:
                                    if cc.type == 'identifier':
                                        ident = code[cc.start_byte:cc.end_byte].decode('utf-8', errors='ignore')
                            elif declarator.type == 'identifier':
                                ident = code[declarator.start_byte:declarator.end_byte].decode('utf-8', errors='ignore')
                            
                            if ident:
                                known_nulls.add(ident)
            
            # 2. Track reassignments: if a known null var is reassigned, it might not be null anymore
            elif node.type == 'assignment_expression':
                left_node = node.children[0]
                if left_node.type == 'identifier':
                    ident = code[left_node.start_byte:left_node.end_byte].decode('utf-8', errors='ignore')
                    if ident in known_nulls:
                        known_nulls.remove(ident)
            
            # 3. Check for dereference
            elif node.type in ['pointer_expression', 'field_expression']:
                ident_node = None
                if node.type == 'pointer_expression' and len(node.children) >= 2:
                    ident_node = node.children[1] # e.g. *ptr -> ptr
                elif node.type == 'field_expression' and len(node.children) >= 1:
                    ident_node = node.children[0] # e.g. ptr->field -> ptr
                
                if ident_node and ident_node.type == 'identifier':
                    ident = code[ident_node.start_byte:ident_node.end_byte].decode('utf-8', errors='ignore')
                    if ident in known_nulls:
                        issues.append({
                            "message": f"Null Pointer Dereference Risk: Variable '{ident}' is known to be null when dereferenced.",
                            "line": node.start_point[0],
                            "type": "Security"
                        })
                        known_nulls.remove(ident) # avoid duplicate flags for same pointer
            
            for child in node.children:
                walk(child)

        walk(func_node)
        return issues
