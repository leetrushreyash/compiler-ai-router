"""Tests for rule engine and pattern definitions."""
import pytest
import sys
from pathlib import Path

# Add project root to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rules.rule_engine import RuleEngine, Rule, HybridAnalyzer
from src.rules.patterns import CodeSmellPatterns, SmellCategory


# ──────────────────────────────────────────────────────────
#  RuleEngine Tests
# ──────────────────────────────────────────────────────────

class TestRuleEngine:
    """Tests for the RuleEngine."""

    def setup_method(self):
        self.engine = RuleEngine()

    def test_init_has_rules(self):
        """Test engine initializes with built-in rules."""
        assert len(self.engine.rules) > 0

    def test_apply_rules_returns_list(self):
        """Test apply_rules returns a list."""
        issues = self.engine.apply_rules("x = 1", "test.py")
        assert isinstance(issues, list)

    # ── Hardcoded secrets ────────────────────────────────

    def test_detect_hardcoded_password(self):
        """Test detecting hardcoded password."""
        code = "password = 'admin123'"
        issues = self.engine.apply_rules(code, "test.py")
        assert any(i["rule_id"] == "SECRET_001" for i in issues)

    def test_detect_hardcoded_api_key(self):
        """Test detecting hardcoded API key."""
        code = "api_key = 'sk_live_12345678'"
        issues = self.engine.apply_rules(code, "test.py")
        assert any(i["rule_id"] == "SECRET_002" for i in issues)

    def test_no_secrets_in_clean_code(self):
        """Test clean code triggers no secret rules."""
        code = "def add(a, b):\n    return a + b"
        issues = self.engine.apply_rules(code, "clean.py")
        secret_issues = [i for i in issues if "SECRET" in i["rule_id"]]
        assert len(secret_issues) == 0

    # ── SQL Injection ────────────────────────────────────

    def test_detect_sql_concat(self):
        """Test detecting SQL string concatenation."""
        code = 'query = "SELECT * FROM users WHERE id = " + user_id'
        issues = self.engine.apply_rules(code, "test.py")
        sql_issues = [i for i in issues if i["type"] == "sql_injection_risk"]
        assert len(sql_issues) >= 1

    def test_detect_sql_format(self):
        """Test detecting SQL with .format()."""
        code = 'cursor.execute("SELECT * FROM t WHERE id = {}".format(uid))'
        issues = self.engine.apply_rules(code, "test.py")
        sql_issues = [i for i in issues if i["type"] == "sql_injection_risk"]
        assert len(sql_issues) >= 1

    # ── Issue structure ──────────────────────────────────

    def test_issue_has_required_keys(self):
        """Test issue dictionaries contain all required keys."""
        code = "password = 'secret'"
        issues = self.engine.apply_rules(code, "app.py")
        required_keys = {"rule_id", "type", "name", "file", "line",
                         "column", "code", "confidence", "severity", "description"}
        for issue in issues:
            assert required_keys.issubset(issue.keys())

    def test_issue_has_extended_keys(self):
        """Test issue dictionaries contain extended metadata keys."""
        issues = self.engine.apply_rules("password = 'x'", "app.py")
        for issue in issues:
            assert "recommendation" in issue
            assert "category" in issue
            assert "risk_score" in issue
            assert 0.0 <= float(issue["risk_score"]) <= 1.0

    def test_issue_file_field(self):
        """Test that issue carries the correct filename."""
        issues = self.engine.apply_rules("password = 'x'", "myfile.py")
        assert all(i["file"] == "myfile.py" for i in issues)

    def test_issue_severity_is_valid(self):
        """Test severity values are HIGH, MEDIUM, or LOW."""
        code = "password = 'x'\napi_key = 'y'"
        issues = self.engine.apply_rules(code, "test.py")
        for i in issues:
            assert i["severity"] in ("HIGH", "MEDIUM", "LOW")

    def test_issue_confidence_range(self):
        """Test confidence is between 0 and 1."""
        issues = self.engine.apply_rules("password = 'x'", "test.py")
        for i in issues:
            assert 0 <= i["confidence"] <= 1

    # ── add / remove rules ───────────────────────────────

    def test_add_rule(self):
        """Test adding a custom rule."""
        initial_count = len(self.engine.rules)
        custom = Rule(
            rule_id="CUSTOM_001",
            smell_type="custom_smell",
            name="Custom Rule",
            pattern=r"TODO",
            confidence=0.50,
            description="Found a TODO",
            severity="LOW",
        )
        self.engine.add_rule(custom)
        assert len(self.engine.rules) == initial_count + 1

    def test_added_rule_fires(self):
        """Test that an added rule actually detects matches."""
        custom = Rule(
            rule_id="CUSTOM_002",
            smell_type="custom",
            name="Debug Print",
            pattern=r"print\s*\(",
            confidence=0.60,
            description="Debug print found",
            severity="LOW",
        )
        self.engine.add_rule(custom)
        issues = self.engine.apply_rules("print('debug')", "t.py")
        assert any(i["rule_id"] == "CUSTOM_002" for i in issues)

    def test_remove_rule(self):
        """Test removing a rule by ID."""
        self.engine.remove_rule("SECRET_001")
        ids = [r.rule_id for r in self.engine.rules]
        assert "SECRET_001" not in ids

    def test_remove_nonexistent_rule_safe(self):
        """Test removing a rule that doesn't exist doesn't crash."""
        initial = len(self.engine.rules)
        self.engine.remove_rule("NONEXISTENT_999")
        assert len(self.engine.rules) == initial

    # ── edge cases ───────────────────────────────────────

    def test_empty_code(self):
        """Test applying rules to empty code."""
        issues = self.engine.apply_rules("", "empty.py")
        assert isinstance(issues, list)

    def test_multiline_code(self):
        """Test rules work across multiline code."""
        code = '''
db_password = "root"
config = {"host": "localhost"}
'''
        issues = self.engine.apply_rules(code, "cfg.py")
        assert isinstance(issues, list)

    def test_detect_command_injection(self):
        code = "os.system(user_input)"
        issues = self.engine.apply_rules(code, "cmd.py")
        assert any(i["type"] == "command_injection" for i in issues)

    def test_detect_weak_crypto(self):
        code = "import hashlib\nh = hashlib.md5(data).hexdigest()"
        issues = self.engine.apply_rules(code, "crypto.py")
        assert any(i["type"] == "weak_crypto" for i in issues)

    def test_detect_too_many_parameters(self):
        code = "def f(a,b,c,d,e,f):\n    return a"
        issues = self.engine.apply_rules(code, "params.py")
        assert any(i["type"] == "too_many_parameters" for i in issues)


# ──────────────────────────────────────────────────────────
#  HybridAnalyzer Tests
# ──────────────────────────────────────────────────────────

class TestHybridAnalyzer:
    """Tests for HybridAnalyzer."""

    def test_analyze_without_ml(self):
        """Test hybrid analyzer with rules only (no ML model)."""
        engine = RuleEngine()
        hybrid = HybridAnalyzer(engine, ml_model=None)
        issues = hybrid.analyze("password = 'x'", {}, "test.py")
        assert isinstance(issues, list)
        assert len(issues) >= 1

    def test_deduplication(self):
        """Test that issues are deduplicated by file/line/type."""
        engine = RuleEngine()
        hybrid = HybridAnalyzer(engine)
        # Even if the same line matches multiple patterns, dedup should reduce
        issues = hybrid.analyze("password = 'x'", {}, "test.py")
        keys = [(i["file"], i["line"], i["type"]) for i in issues]
        assert len(keys) == len(set(keys))


# ──────────────────────────────────────────────────────────
#  CodeSmellPatterns Tests
# ──────────────────────────────────────────────────────────

class TestCodeSmellPatterns:
    """Tests for smell pattern definitions."""

    def test_get_all_patterns(self):
        """Test all patterns are returned."""
        patterns = CodeSmellPatterns.get_all_patterns()
        assert isinstance(patterns, dict)
        assert len(patterns) >= 7

    def test_pattern_has_required_fields(self):
        """Test each pattern definition has essential fields."""
        patterns = CodeSmellPatterns.get_all_patterns()
        for name, defn in patterns.items():
            assert defn.id == name
            assert defn.severity in ("HIGH", "MEDIUM", "LOW")
            assert len(defn.cwe) > 0
            assert len(defn.owasp) > 0
            assert len(defn.remediation) > 0

    def test_get_pattern_by_id(self):
        """Test retrieving a specific pattern."""
        p = CodeSmellPatterns.get_pattern("hardcoded_secrets")
        assert p is not None
        assert p.name == "Hardcoded Secrets"

    def test_get_pattern_nonexistent(self):
        """Test retrieving a non-existent pattern returns None."""
        assert CodeSmellPatterns.get_pattern("nonexistent") is None

    def test_get_security_patterns(self):
        """Test retrieving security category patterns."""
        sec = CodeSmellPatterns.get_security_patterns()
        assert len(sec) >= 3
        assert all(p.category == SmellCategory.SECURITY for p in sec)

    def test_get_maintainability_patterns(self):
        """Test retrieving maintainability patterns."""
        maint = CodeSmellPatterns.get_maintainability_patterns()
        assert len(maint) >= 2
        assert all(p.category == SmellCategory.MAINTAINABILITY for p in maint)

    def test_all_categories_covered(self):
        """Test that at least SECURITY and MAINTAINABILITY categories exist."""
        patterns = CodeSmellPatterns.get_all_patterns()
        categories = {p.category for p in patterns.values()}
        assert SmellCategory.SECURITY in categories
        assert SmellCategory.MAINTAINABILITY in categories


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
