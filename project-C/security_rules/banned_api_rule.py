class BannedApiRule:
    def __init__(self):
        self.BANNED_FUNCTIONS = ['strcpy', 'strcat', 'sprintf', 'gets', 'scanf']

    def check_node(self, node, code):
        """
        Check if a node is an insecure function call.
        """
        if node.type == 'call_expression':
            func_id_node = node.children[0]
            if func_id_node.type == 'identifier':
                func_name = code[func_id_node.start_byte:func_id_node.end_byte].decode('utf-8', errors='ignore')
                if func_name in self.BANNED_FUNCTIONS:
                    return {
                        "message": f"Buffer/Format Risk: Banned function '{func_name}' used.",
                        "line": func_id_node.start_point[0],
                        "type": "Security"
                    }
        return None
