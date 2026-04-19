"""Rule engine for hybrid ML + rule-based detection."""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re


@dataclass
class Rule:
    """Represents a detection rule."""
    rule_id: str
    smell_type: str
    name: str
    pattern: str
    confidence: float
    description: str
    severity: str
    category: str = "maintainability"
    recommendation: str = ""


class RuleEngine:
    """Engine for rule-based code smell detection."""
    
    def __init__(self):
        self.rules = self._init_rules()
    
    def _init_rules(self) -> List[Rule]:
        """Initialize detection rules."""
        return [
            # Hardcoded secrets rules
            Rule(
                rule_id="SECRET_001",
                smell_type="hardcoded_secrets",
                name="Hardcoded Password",
                pattern=r"password\s*=\s*['\"](?!.*\{|\$\{).*['\"]",
                confidence=0.95,
                description="Hardcoded password literal detected",
                severity="HIGH",
                category="security",
                recommendation="Move secrets to environment variables or a secrets manager.",
            ),
            Rule(
                rule_id="SECRET_002",
                smell_type="hardcoded_secrets",
                name="Hardcoded API Key",
                pattern=r"(?:api_key|apiKey|API_KEY)\s*=\s*['\"](?!.*\{|\$\{).*['\"]",
                confidence=0.92,
                description="Hardcoded API key detected",
                severity="HIGH",
                category="security",
                recommendation="Store API keys outside source code and rotate exposed keys.",
            ),
            Rule(
                rule_id="SECRET_003",
                smell_type="hardcoded_secrets",
                name="Hardcoded Token",
                pattern=r"(?:token|auth_token|access_token)\s*=\s*['\"](?:[a-zA-Z0-9]{32,})['\"]",
                confidence=0.88,
                description="Hardcoded authentication token detected",
                severity="HIGH",
                category="security",
                recommendation="Use short-lived tokens loaded from secure runtime config.",
            ),
            
            # SQL Injection rules
            Rule(
                rule_id="SQL_001",
                smell_type="sql_injection_risk",
                name="Dynamic SQL String Concatenation",
                pattern=r'(?:SELECT|INSERT|UPDATE|DELETE).*\+|f["\'].*\{|\%.*\)',
                confidence=0.85,
                description="Dynamic SQL with string concatenation",
                severity="HIGH",
                category="security",
                recommendation="Use parameterized SQL queries with bound parameters.",
            ),
            Rule(
                rule_id="SQL_002",
                smell_type="sql_injection_risk",
                name="String Format SQL",
                pattern=r'execute\s*\(.*\.format\s*\(|execute\s*\(.*%\s*\)',
                confidence=0.80,
                description="SQL query built with string formatting",
                severity="HIGH",
                category="security",
                recommendation="Avoid format/f-string SQL construction; use placeholders and params.",
            ),

            # High severity security rules
            Rule(
                rule_id="CMD_001",
                smell_type="command_injection",
                name="Potential Command Injection",
                pattern=r'(?:os\.system|subprocess\.(?:run|Popen|call)|shell\s*=\s*True)',
                confidence=0.90,
                description="Potential command injection sink detected",
                severity="HIGH",
                category="security",
                recommendation="Avoid shell invocation with user input; use argument lists and validation.",
            ),
            Rule(
                rule_id="FILE_001",
                smell_type="insecure_file_handling",
                name="Insecure File Handling",
                pattern=r'open\s*\(\s*[^,\)]*\)',
                confidence=0.78,
                description="File open operation may be unsafe without path validation",
                severity="HIGH",
                category="security",
                recommendation="Validate file paths and enforce allow-lists before opening files.",
            ),
            Rule(
                rule_id="CRYPTO_001",
                smell_type="weak_crypto",
                name="Weak Crypto Algorithm",
                pattern=r'hashlib\.(?:md5|sha1)\s*\(',
                confidence=0.93,
                description="Weak cryptographic hash function detected",
                severity="HIGH",
                category="security",
                recommendation="Use hashlib.sha256 or stronger algorithm.",
            ),
            Rule(
                rule_id="DESER_001",
                smell_type="unsafe_deserialization",
                name="Unsafe Deserialization",
                pattern=r'(?:pickle\.(?:load|loads)|eval\s*\()',
                confidence=0.91,
                description="Unsafe deserialization or dynamic evaluation detected",
                severity="HIGH",
                category="security",
                recommendation="Use safe parsers (e.g., json.loads) and avoid eval.",
            ),
            
            # Null pointer rules
            Rule(
                rule_id="NULL_001",
                smell_type="null_pointer_risk",
                name="Unchecked Member Access",
                pattern=r'^\s*(?!if|and|or).*\.\w+\s*[^=]',
                confidence=0.65,
                description="Member access without null check",
                severity="MEDIUM",
                category="reliability",
                recommendation="Guard against None before member access.",
            ),

            # Medium severity rules
            Rule(
                rule_id="GOD_001",
                smell_type="god_object",
                name="God Object Candidate",
                pattern=r'^\s*class\s+\w+\s*[:\(]',
                confidence=0.60,
                description="Class may contain too many responsibilities",
                severity="MEDIUM",
                category="maintainability",
                recommendation="Split responsibilities into smaller cohesive classes.",
            ),
            
            # Dead code rules
            Rule(
                rule_id="DEAD_001",
                smell_type="dead_code",
                name="Unreachable Code After Return",
                pattern=r'return.*\n\s+\w',
                confidence=0.90,
                description="Code after return statement",
                severity="LOW",
                category="maintainability",
                recommendation="Remove unreachable statements after return/break/raise.",
            ),
            
            # Code quality rules
            Rule(
                rule_id="QUALITY_001",
                smell_type="long_method",
                name="Method Exceeds Line Limit",
                pattern=None,  # Checked in analyzer
                confidence=0.70,
                description="Method/function exceeds recommended length",
                severity="LOW",
                category="maintainability",
                recommendation="Split the method into smaller focused helper methods.",
            ),
        ]
    
    def apply_rules(self, code: str, filename: str = "") -> List[Dict[str, Any]]:
        """
        Apply all rules to code.
        
        Args:
            code: Source code to check
            filename: Optional filename for context
            
        Returns:
            List of detected issues
        """
        issues = []
        lines = code.split('\n')
        
        for rule in self.rules:
            if rule.pattern is None:
                continue
            
            try:
                pattern = re.compile(rule.pattern, re.IGNORECASE | re.MULTILINE)
                
                for line_num, line in enumerate(lines, 1):
                    match = pattern.search(line)
                    if match:
                        issues.append({
                            "rule_id": rule.rule_id,
                            "type": rule.smell_type,
                            "name": rule.name,
                            "file": filename,
                            "line": line_num,
                            "column": match.start(),
                            "code": line.strip(),
                            "confidence": rule.confidence,
                            "severity": rule.severity,
                            "description": rule.description,
                            "recommendation": rule.recommendation,
                            "category": rule.category,
                            "risk_score": self._risk_score(rule.severity, rule.confidence),
                        })
            except Exception as e:
                # Pattern error, skip rule
                pass
        
        issues.extend(self._apply_structural_rules(code, filename))
        return issues

    def _risk_score(self, severity: str, confidence: float) -> float:
        weights = {"LOW": 0.35, "MEDIUM": 0.65, "HIGH": 1.0}
        return round(min(1.0, max(0.0, weights.get(severity.upper(), 0.5) * float(confidence))), 4)

    def _make_issue(
        self,
        rule_id: str,
        smell_type: str,
        name: str,
        filename: str,
        line: int,
        code: str,
        confidence: float,
        severity: str,
        description: str,
        recommendation: str,
        category: str,
        column: int = 0,
    ) -> Dict[str, Any]:
        return {
            "rule_id": rule_id,
            "type": smell_type,
            "name": name,
            "file": filename,
            "line": line,
            "column": column,
            "code": code,
            "confidence": confidence,
            "severity": severity,
            "description": description,
            "recommendation": recommendation,
            "category": category,
            "risk_score": self._risk_score(severity, confidence),
        }

    def _apply_structural_rules(self, code: str, filename: str) -> List[Dict[str, Any]]:
        """Apply heuristics that are easier to compute structurally than regex-only."""
        issues: List[Dict[str, Any]] = []
        lines = code.splitlines()

        # LOW: duplicate_code heuristic (exact repeated significant lines)
        counts: Dict[str, int] = {}
        first_line: Dict[str, int] = {}
        for idx, raw in enumerate(lines, 1):
            stripped = raw.strip()
            if len(stripped) < 12 or stripped.startswith("#"):
                continue
            counts[stripped] = counts.get(stripped, 0) + 1
            first_line.setdefault(stripped, idx)
        for snippet, count in counts.items():
            if count >= 3:
                issues.append(
                    self._make_issue(
                        "DUP_001",
                        "duplicate_code",
                        "Potential Duplicate Code",
                        filename,
                        first_line[snippet],
                        snippet[:160],
                        0.68,
                        "LOW",
                        "Repeated code line pattern detected",
                        "Extract repeated logic into a shared helper function.",
                        "maintainability",
                    )
                )

        # Track class/function blocks by indentation
        class_stack: List[Dict[str, Any]] = []
        function_stack: List[Dict[str, Any]] = []

        # MEDIUM: deep_nesting
        max_indent = 0
        for idx, raw in enumerate(lines, 1):
            if not raw.strip():
                continue
            indent = (len(raw) - len(raw.lstrip(" "))) // 4
            max_indent = max(max_indent, indent)

            # Pop exited blocks
            while class_stack and indent <= class_stack[-1]["indent"] and raw.strip().startswith(("class ", "def ")):
                class_stack.pop()
            while function_stack and indent <= function_stack[-1]["indent"] and raw.strip().startswith(("def ", "class ")):
                function_stack.pop()

            stripped = raw.strip()

            # Class handling for god_object / large_class
            class_match = re.match(r'^class\s+(\w+)\s*[:\(]', stripped)
            if class_match:
                class_stack.append(
                    {
                        "name": class_match.group(1),
                        "indent": indent,
                        "line": idx,
                        "methods": 0,
                        "assignments": 0,
                    }
                )
                continue

            func_match = re.match(r'^def\s+(\w+)\s*\((.*?)\)\s*:', stripped)
            if func_match:
                params = [p.strip() for p in func_match.group(2).split(",") if p.strip()]
                function_stack.append(
                    {
                        "name": func_match.group(1),
                        "indent": indent,
                        "line": idx,
                        "start": idx,
                        "params": params,
                    }
                )
                if class_stack and indent > class_stack[-1]["indent"]:
                    class_stack[-1]["methods"] += 1

                # LOW: too_many_parameters
                if len([p for p in params if p != "self"]) > 5:
                    issues.append(
                        self._make_issue(
                            "PARAM_001",
                            "too_many_parameters",
                            "Too Many Parameters",
                            filename,
                            idx,
                            stripped,
                            0.72,
                            "LOW",
                            "Function has more than 5 parameters",
                            "Group related parameters into a data object.",
                            "maintainability",
                        )
                    )
                continue

            # Class assignment count
            if class_stack and indent > class_stack[-1]["indent"] and re.search(r'\b\w+\s*=', stripped):
                class_stack[-1]["assignments"] += 1

        # Finalize function length checks using parsed boundaries
        for i, raw in enumerate(lines):
            pass
        func_defs = list(re.finditer(r'^\s*def\s+(\w+)\s*\((.*?)\)\s*:', code, re.MULTILINE))
        for idx, match in enumerate(func_defs):
            start_pos = match.start()
            start_line = code[:start_pos].count("\n") + 1
            end_line = len(lines)
            if idx + 1 < len(func_defs):
                end_line = code[:func_defs[idx + 1].start()].count("\n")
            body_len = max(0, end_line - start_line)
            if body_len > 30:
                snippet = lines[start_line - 1].strip() if start_line - 1 < len(lines) else match.group(0)
                issues.append(
                    self._make_issue(
                        "LONG_001",
                        "long_method",
                        "Long Method",
                        filename,
                        start_line,
                        snippet,
                        0.73,
                        "LOW",
                        "Function length exceeds recommended threshold",
                        "Extract parts of the method into smaller helpers.",
                        "maintainability",
                    )
                )

        # Class-level summary rules
        class_defs = list(re.finditer(r'^\s*class\s+(\w+)\s*[:\(]', code, re.MULTILINE))
        for idx, match in enumerate(class_defs):
            start_line = code[:match.start()].count("\n") + 1
            end_line = len(lines)
            if idx + 1 < len(class_defs):
                end_line = code[:class_defs[idx + 1].start()].count("\n")
            block = "\n".join(lines[start_line - 1:end_line])
            method_count = len(re.findall(r'^\s*def\s+\w+\s*\(', block, re.MULTILINE))
            attr_count = len(re.findall(r'\bself\.\w+\s*=', block))

            if method_count + attr_count > 20:
                issues.append(
                    self._make_issue(
                        "CLASS_001",
                        "large_class",
                        "Large Class",
                        filename,
                        start_line,
                        lines[start_line - 1].strip(),
                        0.70,
                        "LOW",
                        "Class has many methods/attributes",
                        "Split class responsibilities into smaller units.",
                        "maintainability",
                    )
                )

            if method_count >= 8:
                issues.append(
                    self._make_issue(
                        "GOD_002",
                        "god_object",
                        "God Object",
                        filename,
                        start_line,
                        lines[start_line - 1].strip(),
                        0.74,
                        "MEDIUM",
                        "Class appears to own too many behaviors",
                        "Refactor class into focused collaborators.",
                        "maintainability",
                    )
                )

        if max_indent > 3:
            nested_line = next(
                (i + 1 for i, raw in enumerate(lines) if ((len(raw) - len(raw.lstrip(" "))) // 4) > 3 and raw.strip()),
                1,
            )
            nested_code = lines[nested_line - 1].strip() if nested_line - 1 < len(lines) else ""
            issues.append(
                self._make_issue(
                    "NEST_001",
                    "deep_nesting",
                    "Deep Nesting",
                    filename,
                    nested_line,
                    nested_code,
                    0.77,
                    "MEDIUM",
                    "Code nesting depth is greater than 3",
                    "Use guard clauses and extract nested logic.",
                    "maintainability",
                )
            )

        # MEDIUM: unused_variables heuristic
        defined: Dict[str, int] = {}
        for idx, raw in enumerate(lines, 1):
            for var in re.findall(r'\b([a-zA-Z_]\w*)\s*=', raw):
                if var not in defined and not var.startswith("_"):
                    defined[var] = idx
        for var, line in defined.items():
            uses = len(re.findall(rf'\b{re.escape(var)}\b', code))
            if uses <= 1:
                snippet = lines[line - 1].strip() if line - 1 < len(lines) else var
                issues.append(
                    self._make_issue(
                        "UNUSED_001",
                        "unused_variables",
                        "Unused Variable",
                        filename,
                        line,
                        snippet,
                        0.71,
                        "MEDIUM",
                        "Variable is assigned but never used",
                        "Remove unused assignments or use the variable meaningfully.",
                        "maintainability",
                    )
                )

        return issues
    
    def add_rule(self, rule: Rule):
        """Add a new detection rule."""
        self.rules.append(rule)
    
    def remove_rule(self, rule_id: str):
        """Remove a rule by ID."""
        self.rules = [r for r in self.rules if r.rule_id != rule_id]


class HybridAnalyzer:
    """Combines rule-based and ML-based detection."""
    
    def __init__(self, rule_engine: RuleEngine, ml_model: Any = None):
        """
        Initialize hybrid analyzer.
        
        Args:
            rule_engine: Rule engine instance
            ml_model: Optional ML model for predictions
        """
        self.rule_engine = rule_engine
        self.ml_model = ml_model
    
    def analyze(self, code: str, features: Dict[str, Any], 
                filename: str = "") -> List[Dict[str, Any]]:
        """
        Analyze code using both rules and ML.
        
        Args:
            code: Source code
            features: Extracted features
            filename: Optional filename
            
        Returns:
            Combined detections
        """
        issues = []
        
        # Apply rules (high confidence)
        rule_issues = self.rule_engine.apply_rules(code, filename)
        issues.extend(rule_issues)
        
        # Apply ML if available
        if self.ml_model:
            ml_issues = self._apply_ml(features, filename)
            issues.extend(ml_issues)
        
        # Deduplicate and merge results
        issues = self._merge_issues(issues)
        
        return issues
    
    def _apply_ml(self, features: Dict[str, Any], filename: str) -> List[Dict[str, Any]]:
        """Apply ML model for prediction using trained model."""
        issues = []
        try:
            from ..analyzer.feature_extractor import FeatureExtractor
            import numpy as np
            
            extractor = FeatureExtractor()
            target_size = getattr(self.ml_model, "n_features_in_", None)
            feature_vector = extractor.vectorize_features(features, target_size=target_size)
            X = np.array([feature_vector])
            
            result = self.ml_model.predict(X)
            predictions = result if isinstance(result, (list, np.ndarray)) else result.get("predictions", [])
            
            # Map prediction indices back to smell labels
            label_map = {
                0: "hardcoded_secrets",
                1: "sql_injection_risk",
                2: "unsafe_deserialization",
                3: "null_pointer_risk",
                4: "dead_code",
                5: "clean",
                6: "god_object",
                7: "long_method",
            }
            
            severity_map = {
                "hardcoded_secrets": "HIGH",
                "sql_injection_risk": "HIGH",
                "unsafe_deserialization": "HIGH",
                "null_pointer_risk": "MEDIUM",
                "dead_code": "LOW",
                "god_object": "MEDIUM",
                "long_method": "LOW",
            }
            
            # Get probabilities if available
            probas = None
            if hasattr(self.ml_model, 'predict_proba'):
                try:
                    probas = self.ml_model.predict_proba(X)
                except Exception:
                    probas = None
            
            for idx, pred in enumerate(predictions):
                pred_int = int(pred)
                smell_type = label_map.get(pred_int, f"unknown_{pred_int}")
                
                if smell_type == "clean":
                    continue
                
                confidence = 0.75
                if probas is not None and len(probas) > idx:
                    confidence = float(np.max(probas[idx]))
                
                issues.append({
                    "rule_id": f"ML_{smell_type.upper()[:10]}",
                    "type": smell_type,
                    "name": f"ML Detected: {smell_type.replace('_', ' ').title()}",
                    "file": filename,
                    "line": 1,
                    "column": 0,
                    "code": "",
                    "confidence": confidence,
                    "severity": severity_map.get(smell_type, "MEDIUM"),
                    "description": f"ML model detected {smell_type.replace('_', ' ')} pattern",
                    "recommendation": "Review this finding and apply secure coding best practices.",
                    "category": "security" if "injection" in smell_type or "secret" in smell_type or "deserialization" in smell_type else "maintainability",
                    "risk_score": self.rule_engine._risk_score(severity_map.get(smell_type, "MEDIUM"), confidence),
                    "source": "ml_model",
                })
        except Exception as e:
            # ML prediction failed — fall back silently
            pass
        
        return issues
    
    def _merge_issues(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge and deduplicate issues."""
        seen = set()
        merged = []
        
        for issue in issues:
            key = (issue.get("file"), issue.get("line"), issue.get("type"))
            if key not in seen:
                seen.add(key)
                merged.append(issue)
        
        return merged


if __name__ == "__main__":
    # Example usage
    engine = RuleEngine()
    code = """
api_key = 'sk_live_1234567890'
password = 'admin123'
query = "SELECT * FROM users WHERE id = " + user_id
"""
    issues = engine.apply_rules(code, "test.py")
    for issue in issues:
        print(f"{issue['line']}: {issue['name']} - {issue['description']}")
