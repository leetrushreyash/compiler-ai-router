"""AST builder for parsing source code."""
import ast as python_ast
from pathlib import Path
from typing import Optional, Dict, Any, List
import json
import re


class ASTBuilder:
 
    
    def __init__(self, language: str = "python"):
 
        self.language = language.lower()
        self._use_builtin = (self.language == "python")
    
    
    def parse_file(self, filepath: str) -> Dict[str, Any]:
      
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        return self.parse_code(content, str(filepath))
    
    def parse_code(self, code: str, filename: str = "<string>") -> Dict[str, Any]:
        
        tree_data = {
            "filename": filename,
            "language": self.language,
            "code": code,
            "lines": code.split('\n'),
            "nodes": [],
            "errors": [],
        }
        
        if self._use_builtin and self.language == "python":
            try:
                tree = python_ast.parse(code, filename=filename)
                tree_data["nodes"] = self._extract_nodes_python_ast(tree, code)
            except SyntaxError as e:
                tree_data["errors"].append(str(e))
                tree_data["nodes"] = self._extract_nodes_fallback(code)
        else:
            # Fallback: basic regex-based tokenization for non-Python
            tree_data["nodes"] = self._extract_nodes_fallback(code)
        
        return tree_data
    
    def _extract_nodes_python_ast(self, tree: python_ast.AST, code: str) -> List[Dict[str, Any]]:
        
        nodes = []
        lines = code.split('\n')
        
        for node in python_ast.walk(tree):
            entry = None
            
            if isinstance(node, python_ast.FunctionDef):
                end_line = getattr(node, 'end_lineno', node.lineno)
                func_lines = lines[node.lineno - 1:end_line] if end_line else [lines[node.lineno - 1]]
                entry = {
                    "type": "function",
                    "line": node.lineno,
                    "column": node.col_offset,
                    "text": '\n'.join(func_lines)[:200],
                    "name": node.name,
                    "args": [a.arg for a in node.args.args],
                }
            elif isinstance(node, python_ast.AsyncFunctionDef):
                end_line = getattr(node, 'end_lineno', node.lineno)
                func_lines = lines[node.lineno - 1:end_line] if end_line else [lines[node.lineno - 1]]
                entry = {
                    "type": "function",
                    "line": node.lineno,
                    "column": node.col_offset,
                    "text": '\n'.join(func_lines)[:200],
                    "name": node.name,
                    "args": [a.arg for a in node.args.args],
                }
            elif isinstance(node, python_ast.ClassDef):
                entry = {
                    "type": "class",
                    "line": node.lineno,
                    "column": node.col_offset,
                    "text": lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                    "name": node.name,
                }
            elif isinstance(node, python_ast.Import):
                names = ', '.join(alias.name for alias in node.names)
                entry = {
                    "type": "import",
                    "line": node.lineno,
                    "column": node.col_offset,
                    "text": f"import {names}",
                }
            elif isinstance(node, python_ast.ImportFrom):
                names = ', '.join(alias.name for alias in node.names)
                entry = {
                    "type": "import",
                    "line": node.lineno,
                    "column": node.col_offset,
                    "text": f"from {node.module} import {names}",
                }
            elif isinstance(node, python_ast.Assign):
                line_text = lines[node.lineno - 1].strip() if node.lineno <= len(lines) else ""
                entry = {
                    "type": "assignment",
                    "line": node.lineno,
                    "column": node.col_offset,
                    "text": line_text[:100],
                }
            
            if entry:
                nodes.append(entry)
        
        return nodes
    
    def _extract_nodes_fallback(self, code: str) -> list:
 
        nodes = []
        lines = code.split('\n')
        
        patterns = {
            'function_def': (r'^\s*def\s+(\w+)', 'function'),
            'class_def': (r'^\s*class\s+(\w+)', 'class'),
            'import': (r'^\s*(?:import|from)\s+', 'import'),
            'assignment': (r'^\s*(\w+)\s*=', 'assignment'),
        }
        
        import re
        for i, line in enumerate(lines):
            for pattern_name, (pattern, node_type) in patterns.items():
                if re.search(pattern, line):
                    nodes.append({
                        "type": node_type,
                        "line": i + 1,
                        "column": 0,
                        "text": line.strip()[:100],
                    })
        
        return nodes


class ASTVisitor:
    
    
    def visit(self, node: Dict[str, Any]):
        """Visit a node in the AST."""
        method = f"visit_{node.get('type', 'unknown')}"
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)
    
    def generic_visit(self, node: Dict[str, Any]):
        """Default visitor method."""
        return node


class FunctionExtractor(ASTVisitor):
     
    
    def __init__(self):
        self.functions = []
    
    def visit_function(self, node: Dict[str, Any]):
        
        self.functions.append({
            "line": node.get("line"),
            "name": node.get("text", "").split('(')[0].replace('def ', '').strip(),
            "type": "function",
        })
        return node
    
    def visit_method(self, node: Dict[str, Any]):
        """Visit method definition."""
        self.functions.append({
            "line": node.get("line"),
            "name": node.get("text", ""),
            "type": "method",
        })
        return node
    
    def extract(self, nodes: list) -> list:
        """Extract functions from nodes list."""
        self.functions = []
        for node in nodes:
            if node.get("type") in ("function_definition", "method_declaration", "function"):
                self.functions.append(node)
        return self.functions


class ClassExtractor(ASTVisitor):
    """Extract class definitions from AST."""
    
    def __init__(self):
        self.classes = []
    
    def extract(self, nodes: list) -> list:
        """Extract classes from nodes list."""
        self.classes = []
        for node in nodes:
            if node.get("type") in ("class_definition", "class"):
                self.classes.append(node)
        return self.classes


if __name__ == "__main__":
    # Example usage
    builder = ASTBuilder("python")
    code = """
def hello(name):
    return f"Hello, {name}!"

class Calculator:
    def add(self, a, b):
        return a + b
"""
    result = builder.parse_code(code)
    print(json.dumps(result, indent=2))
