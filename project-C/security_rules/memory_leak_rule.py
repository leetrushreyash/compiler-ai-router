class MemoryLeakRule:
    def check_function(self, func_node, code):
        """
        Scan a function body for allocated objects that are never deleted.
        """
        allocations = {} # map identifier to line number
        deletes = set()
        
        def extract_ident(target_node):
            if target_node.type == 'identifier':
                return code[target_node.start_byte:target_node.end_byte].decode('utf-8', errors='ignore')
            elif target_node.type == 'pointer_declarator':
                for child in target_node.children:
                    if child.type == 'identifier':
                        return code[child.start_byte:child.end_byte].decode('utf-8', errors='ignore')
            return None

        def walk(node):
            if node.type == 'init_declarator':
                is_new = any(c.type == 'new_expression' for c in node.children)
                if is_new:
                    ident_str = None
                    for c in node.children:
                        if c.type in ['identifier', 'pointer_declarator']:
                            ident_str = extract_ident(c)
                    if ident_str:
                        allocations[ident_str] = node.start_point[0]
                    else:
                        allocations["<unknown object>"] = node.start_point[0]
                        
            elif node.type == 'assignment_expression':
                if len(node.children) >= 3 and node.children[2].type == 'new_expression':
                    ident_str = extract_ident(node.children[0])
                    if ident_str:
                        allocations[ident_str] = node.start_point[0]
                    else:
                        allocations["<unknown object>"] = node.start_point[0]
                        
            elif node.type == 'delete_expression':
                if len(node.children) >= 2:
                    operand = node.children[1]
                    if operand.type == 'identifier':
                        ident_str = code[operand.start_byte:operand.end_byte].decode('utf-8', errors='ignore')
                        deletes.add(ident_str)

            for child in node.children:
                walk(child)
                
        walk(func_node)
        
        issues = []
        for alloc_str, line in allocations.items():
            if alloc_str not in deletes and alloc_str != "<unknown object>":
                issues.append({
                    "message": f"Memory Leak Risk: Object '{alloc_str}' is dynamically allocated but never deleted.",
                    "line": line + 1,
                    "type": "Security"
                })
            elif alloc_str == "<unknown object>" and len(deletes) < len(allocations):
                issues.append({
                    "message": f"Memory Leak Risk: A dynamically allocated object is never deleted.",
                    "line": line + 1,
                    "type": "Security"
                })
                
        return issues
