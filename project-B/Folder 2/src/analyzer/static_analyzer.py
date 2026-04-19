"""Static analysis engine for AST traversal and feature extraction."""
import re
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field


@dataclass
class AnalysisResult:
    """Result of static analysis on a code snippet."""
    file: str
    line: int
    column: int = 0
    node_type: str = ""
    complexity: float = 0.0
    length: int = 0
    features: Dict[str, Any] = field(default_factory=dict)


class StaticAnalyzer:
    """Performs static analysis on AST nodes."""
    
    def __init__(self):
        self.results: List[AnalysisResult] = []
        self.function_complexity: Dict[str, float] = {}
        self.class_sizes: Dict[str, int] = {}
    
    def analyze_nodes(self, filename: str, ast_data: Dict[str, Any]) -> List[AnalysisResult]:
        """
        Analyze AST nodes and extract features.
        
        Args:
            filename: Source file being analyzed
            ast_data: AST data from parser
            
        Returns:
            List of analysis results
        """
        self.results = []
        code = ast_data.get("code", "")
        nodes = ast_data.get("nodes", [])
        lines = code.split('\n')
        
        # Analyze each node
        for node in nodes:
            result = self._analyze_node(filename, node, code, lines)
            if result:
                self.results.append(result)
        
        return self.results
    
    def _analyze_node(
        self, 
        filename: str, 
        node: Dict[str, Any], 
        code: str, 
        lines: List[str]
    ) -> Optional[AnalysisResult]:
        """Analyze a single node."""
        node_type = node.get("type", "")
        line = node.get("line", 0)
        
        result = AnalysisResult(
            file=filename,
            line=line,
            node_type=node_type,
        )
        
        # Extract text
        text = node.get("text", "")
        result.length = len(text)
        
        # Calculate metrics
        if node_type in ("function", "function_definition", "method"):
            result.complexity = self._calculate_complexity(text)
            result.features["is_function"] = True
        elif node_type in ("class", "class_definition"):
            result.features["is_class"] = True
        
        return result
    
    def _calculate_complexity(self, code_text: str) -> float:
        """Calculate cyclomatic complexity approximation."""
        complexity = 1.0
        
        # Count control flow statements
        keywords = ["if ", "elif ", "else:", "for ", "while ", "except", "and ", "or "]
        for keyword in keywords:
            complexity += code_text.count(keyword) * 0.5
        
        # Count nested levels
        max_indent = 0
        for line in code_text.split('\n'):
            indent = len(line) - len(line.lstrip())
            max_indent = max(max_indent, indent)
        
        complexity += (max_indent // 4) * 0.3
        return round(complexity, 2)


class CodeSmellDetector:
    """Detects specific code smells through pattern matching."""
    
    def __init__(self):
        self.patterns = self._init_patterns()
    
    def _init_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Initialize code smell detection patterns."""
        return {
            "hardcoded_secrets": [
                re.compile(r"password\s*=\s*['\"].*['\"]", re.IGNORECASE),
                re.compile(r"api_key\s*=\s*['\"].*['\"]", re.IGNORECASE),
                re.compile(r"token\s*=\s*['\"].*['\"]", re.IGNORECASE),
                re.compile(r"secret\s*=\s*['\"].*['\"]", re.IGNORECASE),
                re.compile(r"credentials\s*=\s*['\"].*['\"]", re.IGNORECASE),
            ],
            "sql_injection_risk": [
                re.compile(r'execute\s*\(\s*["\'].*\{.*\}.*["\']', re.IGNORECASE),
                re.compile(r'query\s*=\s*["\'].*\+.*["\']', re.IGNORECASE),
                re.compile(r'SELECT\s+.*WHERE.*\+', re.IGNORECASE),
                re.compile(r'execute\s*\(.*format\s*\(', re.IGNORECASE),
                re.compile(r'execute\s*\(.*f["\'].*\{', re.IGNORECASE),
            ],
            "null_pointer_risk": [
                re.compile(r'.*\..*\(.*\)(?!\s*if|\s*and)', re.IGNORECASE),
                re.compile(r'if\s+(\w+)\s*:\s*.*\1\.', re.IGNORECASE),
            ],
            "dead_code": [
                re.compile(r'^\s*#.*unused', re.IGNORECASE),
                re.compile(r'^\s*return.*\n\s+.*\n', re.IGNORECASE),
            ],
            "weak_crypto": [
                re.compile(r'hashlib\.(md5|sha1)\s*\(', re.IGNORECASE),
            ],
            "command_injection": [
                re.compile(r'os\.system\s*\(', re.IGNORECASE),
                re.compile(r'subprocess\.(run|call|Popen).*shell\s*=\s*True', re.IGNORECASE),
            ],
            "deep_nesting": [
                re.compile(r'^\s{16,}(if|for|while|try)\b', re.IGNORECASE),
            ],
            "too_many_parameters": [
                re.compile(r'def\s+\w+\s*\((?:[^\)]*,){5,}[^\)]*\)\s*:', re.IGNORECASE),
            ],
        }

    def _severity_for(self, smell_type: str) -> str:
        mapping = {
            "hardcoded_secrets": "HIGH",
            "sql_injection_risk": "HIGH",
            "weak_crypto": "HIGH",
            "command_injection": "HIGH",
            "null_pointer_risk": "MEDIUM",
            "deep_nesting": "MEDIUM",
            "dead_code": "LOW",
            "too_many_parameters": "LOW",
        }
        return mapping.get(smell_type, "MEDIUM")
    
    def detect_smells(self, code: str, filename: str) -> List[Dict[str, Any]]:
        """
        Detect code smells in given code.
        
        Args:
            code: Source code to analyze
            filename: Source file name
            
        Returns:
            List of detected smells
        """
        smells = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for smell_type, patterns in self.patterns.items():
                for pattern in patterns:
                    if pattern.search(line):
                        smells.append({
                            "type": smell_type,
                            "file": filename,
                            "line": line_num,
                            "code": line.strip(),
                            "confidence": 0.7,
                            "severity": self._severity_for(smell_type),
                        })
        
        return smells


if __name__ == "__main__":
    # Example usage
    detector = CodeSmellDetector()
    test_code = """
api_key = "sk_live_1234567890"
password = 'admin123'
query = "SELECT * FROM users WHERE id = " + user_id
"""
    smells = detector.detect_smells(test_code, "test.py")
    for smell in smells:
        print(smell)
