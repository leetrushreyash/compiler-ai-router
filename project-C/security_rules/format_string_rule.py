class FormatStringRule:
    def __init__(self):
        # Functions where the first argument (index 0) is the format string
        self.FORMAT_FUNCS_IDX0 = ['printf', 'vprintf', 'scanf', 'vscanf', 'printf_s', 'scanf_s']
        # Functions where the second argument (index 1) is the format string
        self.FORMAT_FUNCS_IDX1 = ['fprintf', 'sprintf', 'vfprintf', 'vsprintf', 'fscanf', 'sscanf']
        # Functions where the third argument (index 2) is the format string
        self.FORMAT_FUNCS_IDX2 = ['snprintf', 'vsnprintf']

    def check_node(self, node, code):
        """
        Detect printf(var) vs printf("%s", var)
        """
        if node.type == 'call_expression':
            func_id_node = node.children[0]
            if func_id_node.type == 'identifier':
                func_name = code[func_id_node.start_byte:func_id_node.end_byte].decode('utf-8', errors='ignore')
                
                # Determine which argument should be the literal format string
                target_idx = -1
                if func_name in self.FORMAT_FUNCS_IDX0: target_idx = 0
                elif func_name in self.FORMAT_FUNCS_IDX1: target_idx = 1
                elif func_name in self.FORMAT_FUNCS_IDX2: target_idx = 2
                
                if target_idx != -1:
                    # Get the argument list
                    arg_list_node = None
                    for child in node.children:
                        if child.type == 'argument_list':
                            arg_list_node = child
                            break
                    
                    if arg_list_node:
                        # Filter out punctuation children (parens, commas) to get actual args
                        args = [c for c in arg_list_node.children if c.type not in ['(', ')', ',']]
                        
                        if len(args) > target_idx:
                            fmt_arg = args[target_idx]
                            # If the format argument is NOT a string literal, it's a risk
                            if fmt_arg.type != 'string_literal':
                                return {
                                    "message": f"Format String Risk: Function '{func_name}' uses non-literal format string. Potential vulnerability if argument is user-controlled.",
                                    "line": fmt_arg.start_point[0],
                                    "type": "Security"
                                }
        return None
