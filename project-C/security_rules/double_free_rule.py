class DoubleFreeRule:
    def check_function(self, func_node, code):
        """
        Scan a function body for instances where a variable/expression is freed more than once.
        Supports complex expressions like 'delete obj->ptr;'
        """
        deleted_exprs = set()
        issues = []
        
        def extract_operand_text(node):
            # The operand of 'delete' is usually the second child
            # E.g., 'delete' is child[0], the expression is child[1]
            if len(node.children) >= 2:
                operand_node = node.children[1]
                # Return the literal source code text of the operand
                return code[operand_node.start_byte:operand_node.end_byte].decode('utf-8', errors='ignore').strip()
            return None

        def walk(node):
            if node.type == 'delete_expression':
                operand_text = extract_operand_text(node)
                
                if operand_text:
                    if operand_text in deleted_exprs:
                        issues.append({
                            "message": f"Double Free Risk: Expression '{operand_text}' is freed more than once.",
                            "line": node.start_point[0],
                            "type": "Security"
                        })
                    else:
                        deleted_exprs.add(operand_text)
                        
            for child in node.children:
                walk(child)
                
        walk(func_node)
        return issues
