"""Feature extraction for ML model training and inference."""
import re
from typing import Dict, List, Any, Tuple
from collections import Counter


class FeatureExtractor:
    """Extract features from AST and code for ML models."""
    
    def __init__(self):
        self.feature_names = self._init_feature_names()
        self.additional_feature_names = self._init_additional_feature_names()
    
    def _init_feature_names(self) -> List[str]:
        """Initialize list of feature names."""
        return [
            # Syntactic features
            "has_try_except",
            "has_if_statement",
            "has_loop",
            "has_function_call",
            "has_class_definition",
            "has_import",
            "has_string_literal",
            "has_numeric_literal",
            
            # Security-related features
            "has_assignment",
            "has_equals_comparison",
            "has_regex",
            "has_dangerous_function",
            "has_network_operation",
            "has_file_operation",
            "has_database_operation",
            "has_eval_exec",
            "has_pickle",
            "has_subprocess",
            
            # Complexity features
            "function_length",
            "nesting_depth",
            "argument_count",
            "local_variable_count",
            "cyclomatic_complexity",
            
            # Code smell indicators
            "has_hardcoded_string",
            "has_magic_number",
            "consecutive_assignments",
            "comment_ratio",
            "identifier_length_avg",
        ]

    def _init_additional_feature_names(self) -> List[str]:
        """Initialize additive features for richer analysis/training."""
        return [
            "avg_line_length",
            "deep_nesting_count",
            "try_except_count",
            "api_call_count",
            "duplicate_block_count",
            "function_with_many_params_count",
            "global_var_count",
            "assert_count",
            "list_comprehension_count",
            "dict_comprehension_count",
        ]
    
    def extract_features(self, code: str) -> Dict[str, Any]:
        """
        Extract features from source code.
        
        Args:
            code: Source code to analyze
            
        Returns:
            Dictionary of extracted features
        """
        features = {}
        
        # Syntactic features
        features["has_try_except"] = 1 if re.search(r'\btry\b|\bexcept\b', code) else 0
        features["has_if_statement"] = 1 if re.search(r'\bif\b|\belif\b|\belse\b', code) else 0
        features["has_loop"] = 1 if re.search(r'\bfor\b|\bwhile\b', code) else 0
        features["has_function_call"] = 1 if re.search(r'\w+\s*\(', code) else 0
        features["has_class_definition"] = 1 if re.search(r'\bclass\s+\w+', code) else 0
        features["has_import"] = 1 if re.search(r'\b(?:import|from)\b', code) else 0
        features["has_string_literal"] = code.count('"') + code.count("'")
        features["has_numeric_literal"] = len(re.findall(r'\d+\.?\d*', code))
        
        # Security features
        features["has_assignment"] = len(re.findall(r'=(?!=)', code))
        features["has_equals_comparison"] = code.count('==')
        features["has_regex"] = 1 if re.search(r're\.|regex', code) else 0
        
        dangerous_funcs = ['eval', 'exec', 'pickle', 'os.system', 'subprocess', 'input']
        features["has_dangerous_function"] = sum(1 for f in dangerous_funcs if f in code.lower())
        
        features["has_network_operation"] = 1 if re.search(r'socket|urllib|requests|http', code, re.I) else 0
        features["has_file_operation"] = 1 if re.search(r'open\(|read|write|file', code, re.I) else 0
        features["has_database_operation"] = 1 if re.search(r'sql|cursor|execute|query', code, re.I) else 0
        features["has_eval_exec"] = 1 if re.search(r'\b(eval|exec)\s*\(', code) else 0
        features["has_pickle"] = 1 if 'pickle' in code.lower() else 0
        features["has_subprocess"] = 1 if 'subprocess' in code.lower() else 0
        
        # Complexity features
        lines = code.split('\n')
        features["function_length"] = len([l for l in lines if l.strip()])
        features["nesting_depth"] = self._calculate_nesting_depth(code)
        features["argument_count"] = len(re.findall(r',(?![^()]*\))', code))
        features["local_variable_count"] = len(set(re.findall(r'\b[a-z_]\w*\s*=', code)))
        features["cyclomatic_complexity"] = self._calculate_cyclomatic_complexity(code)
        
        # Code smell indicators
        features["has_hardcoded_string"] = 1 if self._has_hardcoded_secrets(code) else 0
        features["has_magic_number"] = len(re.findall(r'(?<![a-zA-Z0-9])[0-9]{2,}(?![a-zA-Z0-9])', code))
        features["consecutive_assignments"] = self._count_consecutive_assignments(code)
        features["comment_ratio"] = self._calculate_comment_ratio(code)
        features["identifier_length_avg"] = self._calculate_identifier_length(code)

        # Additive feature metrics (kept backward-compatible for existing models)
        features["avg_line_length"] = self._calculate_avg_line_length(code)
        features["deep_nesting_count"] = 1 if features["nesting_depth"] > 3 else 0
        features["try_except_count"] = len(re.findall(r'\btry\b|\bexcept\b', code))
        features["api_call_count"] = len(re.findall(r'\b(requests|httpx|urllib)\.', code, re.I))
        features["duplicate_block_count"] = self._count_duplicate_blocks(code)
        features["function_with_many_params_count"] = self._count_functions_with_many_params(code)
        features["global_var_count"] = self._count_module_level_assignments(code)
        features["assert_count"] = len(re.findall(r'^\s*assert\b', code, re.MULTILINE))
        features["list_comprehension_count"] = len(re.findall(r'\[[^\]]+\bfor\b[^\]]+\]', code, re.S))
        features["dict_comprehension_count"] = len(re.findall(r'\{[^\}]+\bfor\b[^\}]+\}', code, re.S))
        
        return features
    
    def extract_features_from_nodes(self, nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract features from AST nodes."""
        features = {}
        
        # Count node types
        type_counts = Counter(n.get("type", "") for n in nodes)
        features["function_count"] = type_counts.get("function", 0) + type_counts.get("function_definition", 0)
        features["class_count"] = type_counts.get("class", 0) + type_counts.get("class_definition", 0)
        features["total_nodes"] = len(nodes)
        
        # Calculate metrics
        if nodes:
            complexities = [n.get("complexity", 0) for n in nodes if "complexity" in n]
            features["avg_complexity"] = sum(complexities) / len(complexities) if complexities else 0
            features["max_complexity"] = max(complexities) if complexities else 0
        
        return features
    
    def _calculate_nesting_depth(self, code: str) -> int:
        """Calculate maximum nesting depth."""
        max_depth = 0
        current_depth = 0
        
        for line in code.split('\n'):
            indent = len(line) - len(line.lstrip())
            current_depth = indent // 4
            max_depth = max(max_depth, current_depth)
        
        return max_depth
    
    def _calculate_cyclomatic_complexity(self, code: str) -> float:
        """Calculate cyclomatic complexity."""
        complexity = 1.0
        
        complexity += len(re.findall(r'\bif\b', code))
        complexity += len(re.findall(r'\belif\b', code))
        complexity += len(re.findall(r'\belse\b', code))
        complexity += len(re.findall(r'\bfor\b', code))
        complexity += len(re.findall(r'\bwhile\b', code))
        complexity += len(re.findall(r'\bexcept\b', code))
        complexity += len(re.findall(r'\band\b|\bor\b', code)) * 0.5
        
        return round(complexity, 2)
    
    def _has_hardcoded_secrets(self, code: str) -> bool:
        """Check for hardcoded secrets patterns."""
        patterns = [
            r"password\s*=\s*['\"]",
            r"api_key\s*=\s*['\"]",
            r"token\s*=\s*['\"]",
            r"secret\s*=\s*['\"]",
        ]
        return any(re.search(p, code, re.I) for p in patterns)
    
    def _count_consecutive_assignments(self, code: str) -> int:
        """Count lines with consecutive assignments."""
        lines = code.split('\n')
        count = 0
        
        for i in range(len(lines) - 1):
            if '=' in lines[i] and '=' in lines[i + 1]:
                count += 1
        
        return count
    
    def _calculate_comment_ratio(self, code: str) -> float:
        """Calculate ratio of comment lines to total lines."""
        lines = code.split('\n')
        if not lines:
            return 0.0
        
        comment_lines = len([l for l in lines if l.strip().startswith('#')])
        return comment_lines / len(lines)
    
    def _calculate_identifier_length(self, code: str) -> float:
        """Calculate average identifier length."""
        identifiers = re.findall(r'\b[a-zA-Z_]\w*\b', code)
        if not identifiers:
            return 0.0
        
        return sum(len(id_) for id_ in identifiers) / len(identifiers)
    
    def vectorize_features(self, features: Dict[str, Any], target_size: int = None) -> List[float]:
        """
        Convert feature dictionary to vector for ML model.
        
        Args:
            features: Dictionary of features
            
        Returns:
            Feature vector as list of floats
        """
        vector = []
        for feature_name in self.get_all_feature_names():
            value = features.get(feature_name, 0)
            vector.append(float(value))

        # Compatibility mode for older persisted models.
        if target_size is not None and target_size > 0:
            if len(vector) > target_size:
                vector = vector[:target_size]
            elif len(vector) < target_size:
                vector.extend([0.0] * (target_size - len(vector)))
        
        return vector

    def get_all_feature_names(self) -> List[str]:
        """Return full feature order used by latest training runs."""
        return self.feature_names + self.additional_feature_names

    def _calculate_avg_line_length(self, code: str) -> float:
        lines = code.split('\n')
        if not lines:
            return 0.0
        return sum(len(line) for line in lines) / len(lines)

    def _count_duplicate_blocks(self, code: str) -> int:
        lines = [line.strip() for line in code.split('\n') if line.strip() and not line.strip().startswith('#')]
        if len(lines) < 6:
            return 0

        seen = {}
        duplicates = 0
        for i in range(len(lines) - 2):
            block = "\n".join(lines[i:i + 3])
            if block in seen:
                duplicates += 1
            else:
                seen[block] = i
        return duplicates

    def _count_functions_with_many_params(self, code: str, threshold: int = 5) -> int:
        matches = re.findall(r'def\s+\w+\s*\(([^\)]*)\)', code)
        count = 0
        for args in matches:
            params = [a.strip() for a in args.split(',') if a.strip() and a.strip() != 'self']
            if len(params) > threshold:
                count += 1
        return count

    def _count_module_level_assignments(self, code: str) -> int:
        count = 0
        for line in code.split('\n'):
            if not line.strip() or line.strip().startswith('#'):
                continue
            if line.startswith((' ', '\t')):
                continue
            if re.search(r'\b\w+\s*=(?!=)', line):
                count += 1
        return count


if __name__ == "__main__":
    # Example usage
    extractor = FeatureExtractor()
    code = """
def process_data(items):
    result = []
    for item in items:
        if item:
            result.append(item.upper())
    return result
"""
    features = extractor.extract_features(code)
    print(features)
