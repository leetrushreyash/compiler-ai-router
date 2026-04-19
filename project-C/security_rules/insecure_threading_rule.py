class InsecureThreadingRule:
    def check_function(self, func_node, code):
        """
        Detects functions that utilize threads but fail to include any form of locking mechanism, 
        potentially exposing data to race conditions.
        """
        uses_thread = False
        uses_lock = False
        
        def walk(node):
            nonlocal uses_thread, uses_lock
            if node.type == 'type_identifier' or node.type == 'identifier':
                text = code[node.start_byte:node.end_byte].decode('utf-8', errors='ignore')
                if text == 'thread':
                    uses_thread = True
                elif text in ['mutex', 'lock_guard', 'unique_lock']:
                    uses_lock = True
            
            for child in node.children:
                walk(child)
                
        walk(func_node)
        
        if uses_thread and not uses_lock:
            return [{
                "message": f"Insecure Threading Risk: std::thread is spawned but no synchronization (mutex/lock_guard) is detected in this scope. Potential race condition.",
                "line": func_node.start_point[0],
                "type": "Security"
            }]
        return []
