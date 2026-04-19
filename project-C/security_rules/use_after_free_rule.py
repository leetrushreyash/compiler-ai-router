class UseAfterFreeRule:
    def check_function(self, func_node, code):
        """
        Scan a function body for usages of a variable/expression after it has been deleted.
        Uses robust expression extraction and AST position tracking.
        """
        deleted_exprs = {} # maps operand_text to the end_byte of its first delete_expression
        issues = []
        
        def extract_operand_text(node):
            if len(node.children) >= 2:
                operand_node = node.children[1]
                return code[operand_node.start_byte:operand_node.end_byte].decode('utf-8', errors='ignore').strip()
            return None

        # Pass 1: Find all deletes and their locations
        def walk_for_deletes(node):
            if node.type == 'delete_expression':
                operand_text = extract_operand_text(node)
                if operand_text:
                    # We record when the first delete operation finishes
                    if operand_text not in deleted_exprs:
                        deleted_exprs[operand_text] = node.end_byte

            for child in node.children:
                walk_for_deletes(child)

        walk_for_deletes(func_node)
        
        if not deleted_exprs:
            return []

        # Pass 2: Find usages that occur AFTER the delete
        def walk_for_usages(node):
            # Check if this node represents a usage. We look at identifiers or field expressions.
            if node.type in ['identifier', 'field_expression', 'subscript_expression']:
                node_text = code[node.start_byte:node.end_byte].decode('utf-8', errors='ignore').strip()
                
                if node_text in deleted_exprs:
                    delete_byte = deleted_exprs[node_text]
                    
                    # If this usage occurs strictly after the delete expression
                    if node.start_byte > delete_byte:
                        issues.append({
                            "message": f"Use-After-Free Risk: Expression '{node_text}' is accessed after being freed.",
                            "line": node.start_point[0],
                            "type": "Security"
                        })
                        # Remove from tracking to avoid duplicate warnings
                        del deleted_exprs[node_text]
                        # Return early to not process children of this matched expression
                        return 
                        
            # Only recurse if we didn't just match a complex expression (to avoid duplicate nested triggers)
            for child in node.children:
                walk_for_usages(child)

        walk_for_usages(func_node)
        return issues
