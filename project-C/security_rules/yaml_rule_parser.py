import yaml
import os

class YamlRule:
    def __init__(self, yaml_path):
        with open(yaml_path, 'r') as f:
            self.config = yaml.safe_load(f)

    def check_node(self, node, code):
        node_type = self.config.get('node_type')
        if node.type == node_type:
            match_cfg = self.config.get('match', {})
            child_idx = match_cfg.get('child_index', 0)
            child_type = match_cfg.get('child_type', 'identifier')
            
            if len(node.children) > child_idx:
                target_node = node.children[child_idx]
                if target_node.type == child_type:
                    node_text = code[target_node.start_byte:target_node.end_byte].decode('utf-8', errors='ignore')
                    
                    if node_text in match_cfg.get('in', []):
                        message = self.config.get('message', '').replace('{matched_text}', node_text)
                        
                        issue = {
                            "message": message,
                            "line": target_node.start_point[0],
                            "type": self.config.get('type', 'Security')
                        }
                        
                        fix_cfg = self.config.get('fix', None)
                        if fix_cfg and node_text in fix_cfg:
                            issue["fix"] = {
                                "start_line": target_node.start_point[0],
                                "start_col": target_node.start_point[1],
                                "end_line": target_node.end_point[0],
                                "end_col": target_node.end_point[1],
                                "replacement": fix_cfg[node_text]
                            }
                            
                        return issue
        return None

def load_yaml_rules(yaml_dir):
    rules = []
    if not os.path.exists(yaml_dir):
        return rules
        
    for filename in os.listdir(yaml_dir):
        if filename.endswith('.yaml') or filename.endswith('.yml'):
            filepath = os.path.join(yaml_dir, filename)
            rules.append(YamlRule(filepath))
            
    return rules
