"""Code smell pattern definitions and taxonomy."""
from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum


class SmellCategory(str, Enum):
    """Categories of code smells."""
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"


@dataclass
class SmellDefinition:
    """Definition of a code smell."""
    id: str
    name: str
    category: SmellCategory
    description: str
    cwe: str
    owasp: str
    indicators: List[str]
    severity: str  # HIGH, MEDIUM, LOW
    examples: List[str]
    remediation: str


class CodeSmellPatterns:
    """Pattern definitions for code smells."""
    
    @staticmethod
    def get_all_patterns() -> Dict[str, SmellDefinition]:
        """Get all code smell definitions."""
        return {
            "hardcoded_secrets": SmellDefinition(
                id="hardcoded_secrets",
                name="Hardcoded Secrets",
                category=SmellCategory.SECURITY,
                description="Credentials or sensitive data hardcoded in source code",
                cwe="CWE-798",
                owasp="A02:2021 - Cryptographic Failures",
                indicators=[
                    "password = '...'",
                    "api_key = '...'",
                    "token = '...'",
                    "secret = '...'",
                ],
                severity="HIGH",
                examples=[
                    "api_key = 'sk_live_1234567890'",
                    "db_password = 'admin123'",
                    "auth_token = 'Bearer eyJhbGc...'",
                ],
                remediation="Use environment variables or secrets management systems (e.g., AWS Secrets Manager, HashiCorp Vault)"
            ),
            
            "sql_injection_risk": SmellDefinition(
                id="sql_injection_risk",
                name="SQL Injection Risk",
                category=SmellCategory.SECURITY,
                description="Dynamic SQL construction without proper parameterization",
                cwe="CWE-89",
                owasp="A03:2021 - Injection",
                indicators=[
                    "query = 'SELECT * FROM users WHERE id = ' + id",
                    'execute(f"SELECT * FROM {table}")',
                    "query = 'SELECT * WHERE id = %s' % user_input",
                ],
                severity="HIGH",
                examples=[
                    "query = 'DELETE FROM users WHERE id = ' + user_id",
                    'execute("SELECT * FROM users WHERE email = " + email)',
                ],
                remediation="Use parameterized queries or prepared statements (e.g., db.execute(query, params))"
            ),
            
            "unsafe_deserialization": SmellDefinition(
                id="unsafe_deserialization",
                name="Unsafe Deserialization",
                category=SmellCategory.SECURITY,
                description="Unsafe deserialization of untrusted data",
                cwe="CWE-502",
                owasp="A08:2021 - Software and Data Integrity Failures",
                indicators=[
                    "pickle.loads(untrusted_data)",
                    "yaml.load(data)",
                    "eval(data)",
                ],
                severity="HIGH",
                examples=[
                    "obj = pickle.loads(user_input)",
                    "config = yaml.load(open('config.yml'))",
                ],
                remediation="Use safe deserialization methods (e.g., pickle.loads with restricted classes, json.loads)"
            ),
            
            "null_pointer_risk": SmellDefinition(
                id="null_pointer_risk",
                name="Null Pointer Risk",
                category=SmellCategory.RELIABILITY,
                description="Potential null reference exceptions",
                cwe="CWE-476",
                owasp="A06:2021 - Vulnerable and Outdated Components",
                indicators=[
                    "obj.method() without null check",
                    "dict[key] without key existence check",
                ],
                severity="MEDIUM",
                examples=[
                    "return data.get('user').get('name')",
                    "print(optional_object.property)",
                ],
                remediation="Always check for null/None before accessing members. Use safe navigation or getters."
            ),
            
            "dead_code": SmellDefinition(
                id="dead_code",
                name="Dead Code",
                category=SmellCategory.MAINTAINABILITY,
                description="Unreachable or unused code",
                cwe="CWE-561",
                owasp="A04:2021 - Insecure Design",
                indicators=[
                    "Code after return statement",
                    "Unused imports",
                    "Unused variables",
                ],
                severity="LOW",
                examples=[
                    "def func():\n    return 42\n    print('unreachable')",
                    "import os  # never used",
                ],
                remediation="Remove unreachable code and unused imports/variables to improve clarity"
            ),
            
            "god_object": SmellDefinition(
                id="god_object",
                name="God Object",
                category=SmellCategory.MAINTAINABILITY,
                description="Class with too many responsibilities",
                cwe="CWE-400",
                owasp="A04:2021 - Insecure Design",
                indicators=[
                    "Class with >20 public methods",
                    "Class with >500 lines",
                    "Multiple unrelated responsibilities",
                ],
                severity="MEDIUM",
                examples=[
                    "class UserManager: # handles auth, DB, email, logging",
                ],
                remediation="Refactor into smaller, focused classes following Single Responsibility Principle"
            ),
            
            "long_method": SmellDefinition(
                id="long_method",
                name="Long Method",
                category=SmellCategory.MAINTAINABILITY,
                description="Method exceeding recommended complexity/length",
                cwe="CWE-400",
                owasp="A04:2021 - Insecure Design",
                indicators=[
                    "Method length > 20 lines",
                    "Cyclomatic complexity > 10",
                    "Deeply nested code",
                ],
                severity="LOW",
                examples=[
                    "def process_data(...):\n    # 50+ lines of logic",
                ],
                remediation="Extract methods to improve readability and testability"
            ),
        }
    
    @staticmethod
    def get_pattern(smell_id: str) -> SmellDefinition:
        """Get a specific pattern by ID."""
        patterns = CodeSmellPatterns.get_all_patterns()
        return patterns.get(smell_id)
    
    @staticmethod
    def get_patterns_by_category(category: SmellCategory) -> List[SmellDefinition]:
        """Get patterns by category."""
        patterns = CodeSmellPatterns.get_all_patterns()
        return [p for p in patterns.values() if p.category == category]
    
    @staticmethod
    def get_security_patterns() -> List[SmellDefinition]:
        """Get security-related patterns."""
        return CodeSmellPatterns.get_patterns_by_category(SmellCategory.SECURITY)
    
    @staticmethod
    def get_maintainability_patterns() -> List[SmellDefinition]:
        """Get maintainability patterns."""
        return CodeSmellPatterns.get_patterns_by_category(SmellCategory.MAINTAINABILITY)
