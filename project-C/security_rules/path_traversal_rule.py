class PathTraversalRule:
    def __init__(self):
        self.FILE_FUNCS = ['fopen', 'open']
    
    def check_node(self, node, code):
        """
        Detects file operations where the path parameter is dynamic, 
        potentially allowing Path Traversal directory escaping (e.g. ../../etc/passwd).
        """
        if node.type == 'call_expression':
            func_name = None
            func_id_node = node.children[0]
            
            # Simple call: fopen(path, ...)
            if func_id_node.type == 'identifier':
                func_name = code[func_id_node.start_byte:func_id_node.end_byte].decode('utf-8', errors='ignore')
            # Method call: file.open(path)
            elif func_id_node.type == 'field_expression':
                if len(func_id_node.children) >= 3:
                    field = func_id_node.children[2]
                    if field.type == 'field_identifier':
                        func_name = code[field.start_byte:field.end_byte].decode('utf-8', errors='ignore')
                        
            if func_name in self.FILE_FUNCS:
                for child in node.children:
                    if child.type == 'argument_list':
                        args = [c for c in child.children if c.type not in ['(', ')', ',']]
                        if args:
                            path_arg = args[0]
                            # If the path is not a literal string, it might be tampered with.
                            if path_arg.type not in ['string_literal', 'concatenated_string']:
                                return {
                                    "message": f"Path Traversal Risk: File operation '{func_name}' restricts a dynamic or non-literal path variable. Ensure path is sanitized.",
                                    "line": path_arg.start_point[0],
                                    "type": "Security"
                                }
        return None
