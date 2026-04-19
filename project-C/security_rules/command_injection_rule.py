class CommandInjectionRule:
    def __init__(self):
        # Common C/C++ functions that execute OS commands or processes
        self.CMD_FUNCTIONS = ['system', 'popen', 'execl', 'execle', 'execlp', 'execv', 'execvp', 'execvpe']

    def check_node(self, node, code):
        """
        Detects calls to command execution functions where the command string is not a literal.
        Extends coverage to check variable concatenation and dynamic structures.
        """
        if node.type == 'call_expression':
            func_id_node = node.children[0]
            
            # Ensure it's a direct function call (not a complex function pointer)
            if func_id_node.type == 'identifier':
                func_name = code[func_id_node.start_byte:func_id_node.end_byte].decode('utf-8', errors='ignore')
                
                if func_name in self.CMD_FUNCTIONS:
                    arg_list_node = None
                    for child in node.children:
                        if child.type == 'argument_list':
                            arg_list_node = child
                            break
                    
                    if arg_list_node:
                        # Extract arguments, ignoring punctuation like commas and parentheses
                        args = [c for c in arg_list_node.children if c.type not in ['(', ')', ',']]
                        
                        if args:
                            first_arg = args[0]
                            
                            # A literal string is safe. Anything else (identifier, binary_expression, call_expression) 
                            # is potentially constructed from untrusted user input, causing Command Injection.
                            if first_arg.type not in ['string_literal', 'concatenated_string']:
                                return {
                                    "message": f"Command Injection Risk: Function '{func_name}' is called with a dynamic or non-literal command. Ensure input is sanitized.",
                                    "line": first_arg.start_point[0],
                                    "type": "Security"
                                }
        return None
