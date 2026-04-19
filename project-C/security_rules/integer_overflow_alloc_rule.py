class IntegerOverflowAllocRule:
    def check_node(self, node, code):
        """
        Detects Memory Allocations where the size uses uncontrolled arithmetic.
        """
        # We look for init_declarator (e.g. char* x = new char[...])
        # or assignment_expression (e.g. x = new char[...])
        
        target_name = "<unknown object>"
        new_expr_node = None
        
        if node.type == 'init_declarator':
            for c in node.children:
                if c.type in ['identifier']:
                    target_name = code[c.start_byte:c.end_byte].decode('utf-8', errors='ignore')
                elif c.type == 'pointer_declarator':
                    for gc in c.children:
                        if gc.type == 'identifier':
                            target_name = code[gc.start_byte:gc.end_byte].decode('utf-8', errors='ignore')
                
                if c.type == 'new_expression':
                    new_expr_node = c
                    
        elif node.type == 'assignment_expression':
            if len(node.children) >= 3:
                left = node.children[0]
                right = node.children[2]
                if left.type == 'identifier':
                    target_name = code[left.start_byte:left.end_byte].decode('utf-8', errors='ignore')
                if right.type == 'new_expression':
                    new_expr_node = right

        if new_expr_node:
            for child in new_expr_node.children:
                if child.type == 'new_declarator':
                    for c in child.children:
                        if c.type == 'binary_expression':
                            operator_node = c.children[1] if len(c.children) > 1 else None
                            if operator_node:
                                op_text = code[operator_node.start_byte:operator_node.end_byte].decode('utf-8', errors='ignore')
                                if op_text in ['*', '+']:
                                    return {
                                        "message": f"Integer Overflow/Memory Corruption Risk: Dynamic allocation size for '{target_name}' uses arithmetic ('{op_text}') without explicit bounds checking.",
                                        "line": node.start_point[0],
                                        "type": "Security"
                                    }
        return None
