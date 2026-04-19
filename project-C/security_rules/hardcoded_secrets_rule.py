import re

class HardcodedSecretsRule:
    def __init__(self):
        # Common terms associated with sensitive data
        self.secret_patterns = [
            r"password",
            r"secret",
            r"api[_\-]?key",
            r"token",
            r"credential"
        ]
        self.regex = re.compile('|'.join(self.secret_patterns), re.IGNORECASE)

    def check_node(self, node, code):
        """
        Detects hardcoded secrets by looking for string literals assigned to 
        variables with suspicious names.
        """
        # 1. Check in variable declarations (e.g., const char* pwd = "123")
        if node.type == 'declaration':
            for child in node.children:
                if child.type == 'init_declarator':
                    ident_node = None
                    for c in child.children:
                        if c.type == 'identifier':
                            ident_node = c
                        elif c.type == 'pointer_declarator':
                            for cc in c.children:
                                if cc.type == 'identifier':
                                    ident_node = cc
                    
                    if ident_node:
                        var_name = code[ident_node.start_byte:ident_node.end_byte].decode('utf-8', errors='ignore')
                        if self.regex.search(var_name):
                            # Name matches. Is it assigned a string?
                            for c in child.children:
                                if c.type == 'string_literal':
                                    return {
                                        "message": f"Hardcoded Secret Risk: Variable '{var_name}' is initialized with a hardcoded string literal.",
                                        "line": node.start_point[0],
                                        "type": "Security"
                                    }
                                    
        # 2. Check in assignments (e.g., pwd = "123")
        elif node.type == 'assignment_expression':
            if len(node.children) >= 3:
                left = node.children[0]
                right = node.children[2]
                if left.type == 'identifier':
                    var_name = code[left.start_byte:left.end_byte].decode('utf-8', errors='ignore')
                    if self.regex.search(var_name) and right.type == 'string_literal':
                        return {
                            "message": f"Hardcoded Secret Risk: Variable '{var_name}' is assigned a hardcoded string literal.",
                            "line": node.start_point[0],
                            "type": "Security"
                        }
        
        return None
