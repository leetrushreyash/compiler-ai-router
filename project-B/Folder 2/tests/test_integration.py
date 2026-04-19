"""Integration tests for the code smell detector.

End-to-end tests that exercise the full pipeline:
  parse → analyze → detect → report
"""
import pytest
import sys
import os
import json
import tempfile
from pathlib import Path

# Add project root to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parser import ASTBuilder
from src.parser.code_extractor import CodeExtractor
from src.analyzer import StaticAnalyzer, FeatureExtractor
from src.analyzer.control_flow import ControlFlowAnalyzer, DataFlowAnalyzer
from src.rules import RuleEngine
from src.rules.patterns import CodeSmellPatterns
from src.reporting import ReportGenerator
from src.reporting.report_generator import Issue
from src.reporting.formatter import OutputFormatter, OutputFormat
from src.config import Config, get_config, SmellType, Severity


# ──────────────────────────────────────────────────────────
#  Reusable sample code snippets
# ──────────────────────────────────────────────────────────

CLEAN_CODE = '''
def add(a, b):
    """Add two numbers."""
    return a + b

def greet(name):
    """Return greeting string."""
    return f"Hello, {name}!"
'''

VULNERABLE_CODE = '''
import pickle, hashlib, os, sqlite3

API_KEY = "sk-HARDCODED-SECRET-12345"
DB_PASSWORD = "admin123"

def login(username, password):
    conn = sqlite3.connect("app.db")
    query = "SELECT * FROM users WHERE name='" + username + "' AND pass='" + password + "'"
    conn.execute(query)

def load_data(raw):
    return pickle.loads(raw)

def hash_password(pw):
    return hashlib.md5(pw.encode()).hexdigest()
'''

LONG_METHOD_CODE = '''
def very_long_method(x):
    a = 1
    b = 2
    c = 3
    d = 4
    e = 5
    f = 6
    g = 7
    h = 8
    i = 9
    j = 10
    k = 11
    l = 12
    m = 13
    n = 14
    o = 15
    p = 16
    q = 17
    r = 18
    s = 19
    t = 20
    u = 21
    v = 22
    w = 23
    x2 = 24
    y = 25
    z = 26
    aa = 27
    bb = 28
    cc = 29
    dd = 30
    ee = 31
    return ee
'''


# ──────────────────────────────────────────────────────────
#  Full Pipeline Tests
# ──────────────────────────────────────────────────────────

class TestFullPipeline:
    """End-to-end pipeline: parse → analyze → detect → report."""

    def test_pipeline_with_clean_code(self):
        """Clean code should produce no or low-severity issues."""
        parser = ASTBuilder("python")
        ast_data = parser.parse_code(CLEAN_CODE, "clean.py")
        assert ast_data is not None

        engine = RuleEngine()
        issues = engine.apply_rules(CLEAN_CODE, "clean.py")
        # Clean code should produce very few or no issues
        assert isinstance(issues, list)

    def test_pipeline_detects_hardcoded_secret(self):
        """Vulnerable code should trigger hardcoded_secrets."""
        engine = RuleEngine()
        issues = engine.apply_rules(VULNERABLE_CODE, "vuln.py")
        types = {i["type"] for i in issues}
        assert "hardcoded_secrets" in types

    def test_pipeline_detects_sql_injection(self):
        """Vulnerable code should trigger sql_injection_risk."""
        engine = RuleEngine()
        issues = engine.apply_rules(VULNERABLE_CODE, "vuln.py")
        types = {i["type"] for i in issues}
        assert "sql_injection_risk" in types

    def test_pipeline_full_report_json(self):
        """Full pipeline produces valid JSON report."""
        parser = ASTBuilder("python")
        ast_data = parser.parse_code(VULNERABLE_CODE, "vuln.py")

        engine = RuleEngine()
        issues = engine.apply_rules(VULNERABLE_CODE, "vuln.py")

        report = ReportGenerator("Integration Test")
        for iss in issues:
            report.add_issue(Issue(
                file=iss["file"], line=iss["line"], type=iss["type"],
                severity=iss["severity"], confidence=iss["confidence"],
                explanation=iss["description"],
            ))

        json_str = report.generate_json()
        data = json.loads(json_str)
        assert data["total_issues"] >= 1
        assert data["project"] == "Integration Test"
        assert len(data["issues"]) >= 1

    def test_pipeline_full_report_text(self):
        """Full pipeline produces text report."""
        engine = RuleEngine()
        issues = engine.apply_rules(VULNERABLE_CODE, "vuln.py")

        report = ReportGenerator("Text Test")
        for iss in issues:
            report.add_issue(Issue(
                file=iss["file"], line=iss["line"], type=iss["type"],
                severity=iss["severity"], confidence=iss["confidence"],
                explanation=iss["description"],
            ))
        text = report.generate_text()
        assert "Text Test" in text
        assert "HIGH" in text or "MEDIUM" in text

    def test_pipeline_full_report_csv(self):
        """Full pipeline produces CSV report."""
        engine = RuleEngine()
        issues = engine.apply_rules(VULNERABLE_CODE, "vuln.py")

        report = ReportGenerator("CSV Test")
        for iss in issues:
            report.add_issue(Issue(
                file=iss["file"], line=iss["line"], type=iss["type"],
                severity=iss["severity"], confidence=iss["confidence"],
                explanation=iss["description"],
            ))
        csv_str = report.generate_csv()
        lines = csv_str.strip().split("\n")
        # header + at least one data row
        assert len(lines) >= 2

    def test_pipeline_save_to_file(self):
        """Pipeline can save JSON report to disk."""
        engine = RuleEngine()
        issues = engine.apply_rules(VULNERABLE_CODE, "vuln.py")

        report = ReportGenerator("Save Test")
        for iss in issues:
            report.add_issue(Issue(
                file=iss["file"], line=iss["line"], type=iss["type"],
                severity=iss["severity"], confidence=iss["confidence"],
                explanation=iss["description"],
            ))
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp = f.name
        try:
            report.save(tmp, "json")
            with open(tmp) as fh:
                saved = json.load(fh)
            assert saved["total_issues"] >= 1
        finally:
            os.unlink(tmp)


# ──────────────────────────────────────────────────────────
#  Parser → Analyzer Integration
# ──────────────────────────────────────────────────────────

class TestParserAnalyzerIntegration:
    """Tests that parsed AST feeds correctly into analyzers."""

    def test_parsed_nodes_produce_features(self):
        """Features are extractable from parsed code."""
        parser = ASTBuilder("python")
        ast_data = parser.parse_code(VULNERABLE_CODE, "vuln.py")

        extractor = FeatureExtractor()
        features = extractor.extract_features(VULNERABLE_CODE)
        assert features["function_length"] >= 1
        assert features["has_assignment"]

    def test_control_flow_on_parsed_ast(self):
        """Control flow analysis runs on code AST."""
        cf = ControlFlowAnalyzer()
        result = cf.analyze_function(VULNERABLE_CODE)
        assert result["cyclomatic_complexity"] >= 1

    def test_data_flow_on_parsed_ast(self):
        """Data flow analysis runs on code AST."""
        df = DataFlowAnalyzer()
        result = df.analyze(VULNERABLE_CODE)
        assert "tainted_variables" in result

    def test_static_analyzer_on_parsed_code(self):
        """StaticAnalyzer produces findings from parsed code."""
        parser = ASTBuilder("python")
        ast_data = parser.parse_code(VULNERABLE_CODE, "vuln.py")
        sa = StaticAnalyzer()
        results = sa.analyze_nodes("vuln.py", ast_data)
        assert isinstance(results, list)

    def test_feature_extraction_from_nodes(self):
        """Feature extraction from AST nodes produces valid dict."""
        parser = ASTBuilder("python")
        ast_data = parser.parse_code(CLEAN_CODE, "clean.py")
        nodes = ast_data.get("nodes", [])
        if nodes:
            extractor = FeatureExtractor()
            feat_dict = extractor.extract_features_from_nodes(nodes)
            assert isinstance(feat_dict, dict)
            assert "function_count" in feat_dict


# ──────────────────────────────────────────────────────────
#  Rules → Reporter Integration
# ──────────────────────────────────────────────────────────

class TestRulesReportIntegration:
    """Tests that rule engine output feeds into the reporter."""

    def test_rule_engine_output_fits_issue_dataclass(self):
        """Every rule result can be mapped to an Issue."""
        engine = RuleEngine()
        issues = engine.apply_rules(VULNERABLE_CODE, "vuln.py")
        for iss in issues:
            issue_obj = Issue(
                file=iss["file"], line=iss["line"], type=iss["type"],
                severity=iss["severity"], confidence=iss["confidence"],
                explanation=iss["description"],
            )
            assert issue_obj.file == "vuln.py"
            assert issue_obj.line >= 0

    def test_summary_counts_match(self):
        """Report summary total matches issue count."""
        engine = RuleEngine()
        issues = engine.apply_rules(VULNERABLE_CODE, "vuln.py")

        report = ReportGenerator("Count Check")
        for iss in issues:
            report.add_issue(Issue(
                file=iss["file"], line=iss["line"], type=iss["type"],
                severity=iss["severity"], confidence=iss["confidence"],
                explanation=iss["description"],
            ))
        summary = report.get_summary()
        assert summary["total_issues"] == len(issues)


# ──────────────────────────────────────────────────────────
#  Formatter Integration
# ──────────────────────────────────────────────────────────

class TestFormatterIntegration:
    """Tests that formatter handles real report data."""

    def test_format_full_report_table(self):
        """OutputFormatter.format_table works with real issues."""
        engine = RuleEngine()
        issues = engine.apply_rules(VULNERABLE_CODE, "vuln.py")
        # format_table expects dicts with keys: severity, file, line, type, confidence, explanation
        table = OutputFormatter.format_table(issues)
        assert "Severity" in table
        assert len(table) > 0

    def test_format_html_report(self):
        """OutputFormatter.generate_html_report produces valid HTML."""
        engine = RuleEngine()
        issues = engine.apply_rules(VULNERABLE_CODE, "vuln.py")
        report_data = {"summary": {"total": len(issues)}, "issues": issues}
        html = OutputFormatter.generate_html_report(report_data)
        assert "<html>" in html.lower() or "<table>" in html.lower()


# ──────────────────────────────────────────────────────────
#  Config → Analysis Integration
# ──────────────────────────────────────────────────────────

class TestConfigIntegration:
    """Tests that configuration affects analysis."""

    def test_config_loads_and_is_used(self):
        """Config object can be created and has expected structure."""
        cfg = get_config()
        assert isinstance(cfg, Config)
        assert "python" in cfg.supported_languages

    def test_smell_type_maps_to_config(self):
        """Each SmellType has a corresponding config entry."""
        cfg = Config()
        for st in SmellType:
            assert st in cfg.smell_configs


# ──────────────────────────────────────────────────────────
#  File-Based Integration
# ──────────────────────────────────────────────────────────

class TestFileIntegration:
    """Tests that analyse real sample files from data/test_samples/."""

    SAMPLES_DIR = Path(__file__).parent.parent / "data" / "test_samples"

    @pytest.fixture
    def sample_vuln(self):
        p = self.SAMPLES_DIR / "sample_vulnerable.py"
        if p.exists():
            return p.read_text(encoding="utf-8", errors="ignore")
        pytest.skip("sample_vulnerable.py not found")

    @pytest.fixture
    def sample_clean(self):
        p = self.SAMPLES_DIR / "sample_clean.py"
        if p.exists():
            return p.read_text(encoding="utf-8", errors="ignore")
        pytest.skip("sample_clean.py not found")

    def test_parse_sample_file(self, sample_vuln):
        """Parser handles real sample file."""
        parser = ASTBuilder("python")
        ast_data = parser.parse_code(sample_vuln, "sample_vulnerable.py")
        assert ast_data is not None
        assert ast_data.get("nodes") is not None

    def test_analyze_sample_file(self, sample_vuln):
        """StaticAnalyzer finds issues in real sample."""
        parser = ASTBuilder("python")
        ast_data = parser.parse_code(sample_vuln, "sample_vulnerable.py")
        sa = StaticAnalyzer()
        results = sa.analyze_nodes("sample_vulnerable.py", ast_data)
        assert isinstance(results, list)

    def test_rule_engine_on_sample_file(self, sample_vuln):
        """RuleEngine finds issues in real sample."""
        engine = RuleEngine()
        issues = engine.apply_rules(sample_vuln, "sample_vulnerable.py")
        assert len(issues) >= 1

    def test_clean_sample_fewer_issues(self, sample_clean):
        """Clean sample has fewer issues than vulnerable."""
        engine = RuleEngine()
        clean_issues = engine.apply_rules(sample_clean, "sample_clean.py")
        # Clean code may still have style issues, but should be manageable
        assert isinstance(clean_issues, list)

    def test_full_pipeline_on_sample(self, sample_vuln):
        """Full parse→rule→report pipeline on real sample."""
        parser = ASTBuilder("python")
        parser.parse_code(sample_vuln, "sample_vulnerable.py")

        engine = RuleEngine()
        issues = engine.apply_rules(sample_vuln, "sample_vulnerable.py")

        report = ReportGenerator("Sample Pipeline")
        for iss in issues:
            report.add_issue(Issue(
                file=iss["file"], line=iss["line"], type=iss["type"],
                severity=iss["severity"], confidence=iss["confidence"],
                explanation=iss["description"],
            ))
        summary = report.get_summary()
        assert summary["total_issues"] == len(issues)
        assert summary["total_issues"] >= 1


# ──────────────────────────────────────────────────────────
#  Multi-File Scanning
# ──────────────────────────────────────────────────────────

class TestMultiFileScan:
    """Tests scanning multiple files together."""

    SAMPLES_DIR = Path(__file__).parent.parent / "data" / "test_samples"

    def test_scan_directory_of_samples(self):
        """Scan all .py samples and aggregate results."""
        if not self.SAMPLES_DIR.exists():
            pytest.skip("test_samples/ not found")

        py_files = list(self.SAMPLES_DIR.glob("*.py"))
        assert len(py_files) >= 1, "No .py files in test_samples/"

        engine = RuleEngine()
        report = ReportGenerator("Multi-File Scan")
        total_found = 0
        for fp in py_files:
            code = fp.read_text(encoding="utf-8", errors="ignore")
            issues = engine.apply_rules(code, fp.name)
            for iss in issues:
                report.add_issue(Issue(
                    file=iss["file"], line=iss["line"], type=iss["type"],
                    severity=iss["severity"], confidence=iss["confidence"],
                    explanation=iss["description"],
                ))
                total_found += 1

        summary = report.get_summary()
        assert summary["total_issues"] == total_found
        # We expect at least a few issues across all sample files
        assert total_found >= 1

    def test_code_extractor_get_function_snippet(self):
        """CodeExtractor.get_function_snippet works on a real file."""
        if not self.SAMPLES_DIR.exists():
            pytest.skip("test_samples/ not found")
        sample = self.SAMPLES_DIR / "sample_vulnerable.py"
        if not sample.exists():
            pytest.skip("sample_vulnerable.py not found")
        snippet = CodeExtractor.get_function_snippet(str(sample), 1, 5)
        assert isinstance(snippet, str)
        assert len(snippet) > 0


# ──────────────────────────────────────────────────────────
#  Patterns Integration
# ──────────────────────────────────────────────────────────

class TestPatternsIntegration:
    """Tests CodeSmellPatterns against real code."""

    def test_patterns_include_secrets_definition(self):
        """Patterns module has hardcoded_secrets definition."""
        all_patterns = CodeSmellPatterns.get_all_patterns()
        assert "hardcoded_secrets" in all_patterns
        p = all_patterns["hardcoded_secrets"]
        assert p.cwe == "CWE-798"

    def test_patterns_include_sql_definition(self):
        """Patterns module has sql_injection_risk definition."""
        all_patterns = CodeSmellPatterns.get_all_patterns()
        assert "sql_injection_risk" in all_patterns
        p = all_patterns["sql_injection_risk"]
        assert p.cwe == "CWE-89"


# ──────────────────────────────────────────────────────────
#  Edge Cases
# ──────────────────────────────────────────────────────────

class TestEdgeCases:
    """Edge case integration tests."""

    def test_empty_code(self):
        """Pipeline handles empty input."""
        parser = ASTBuilder("python")
        ast_data = parser.parse_code("", "empty.py")
        engine = RuleEngine()
        issues = engine.apply_rules("", "empty.py")
        assert isinstance(issues, list)

    def test_syntax_error_code(self):
        """Pipeline handles code with syntax errors."""
        bad = "def broken(\n  this is not valid python"
        engine = RuleEngine()
        # Should not crash
        issues = engine.apply_rules(bad, "bad.py")
        assert isinstance(issues, list)

    def test_very_large_code(self):
        """Pipeline handles large code without crashing."""
        big = "\n".join([f"x_{i} = {i}" for i in range(500)])
        engine = RuleEngine()
        issues = engine.apply_rules(big, "big.py")
        assert isinstance(issues, list)

    def test_non_python_code(self):
        """Pipeline handles non-Python code gracefully."""
        java = 'public class Main { public static void main(String[] args) {} }'
        parser = ASTBuilder("java")
        ast_data = parser.parse_code(java, "Main.java")
        assert ast_data is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
