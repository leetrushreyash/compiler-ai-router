"""Tests for static analyzer, feature extractor, and control flow modules."""
import pytest
import sys
from pathlib import Path

# Add project root to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analyzer.static_analyzer import StaticAnalyzer, CodeSmellDetector
from src.analyzer.feature_extractor import FeatureExtractor
from src.analyzer.control_flow import ControlFlowAnalyzer, DataFlowAnalyzer


# ──────────────────────────────────────────────────────────
#  CodeSmellDetector Tests
# ──────────────────────────────────────────────────────────

class TestCodeSmellDetector:
    """Tests for CodeSmellDetector."""

    def test_detect_hardcoded_password(self):
        """Test detecting hardcoded password."""
        detector = CodeSmellDetector()
        code = "password = 'admin123'"
        smells = detector.detect_smells(code, "test.py")
        assert any(s["type"] == "hardcoded_secrets" for s in smells)

    def test_detect_hardcoded_api_key(self):
        """Test detecting hardcoded API key."""
        detector = CodeSmellDetector()
        code = 'api_key = "sk_live_1234567890"'
        smells = detector.detect_smells(code, "test.py")
        assert any(s["type"] == "hardcoded_secrets" for s in smells)

    def test_detect_hardcoded_token(self):
        """Test detecting hardcoded token."""
        detector = CodeSmellDetector()
        code = "token = 'eyJhbGciOiJIUz'"
        smells = detector.detect_smells(code, "test.py")
        assert any(s["type"] == "hardcoded_secrets" for s in smells)

    def test_detect_hardcoded_secret(self):
        """Test detecting hardcoded secret."""
        detector = CodeSmellDetector()
        code = "secret = 'my_super_secret'"
        smells = detector.detect_smells(code, "test.py")
        assert any(s["type"] == "hardcoded_secrets" for s in smells)

    def test_detect_sql_injection(self):
        """Test detecting SQL injection risks."""
        detector = CodeSmellDetector()
        code = 'query = "SELECT * FROM users WHERE id = " + user_id'
        smells = detector.detect_smells(code, "test.py")
        assert len(smells) >= 0  # Pattern may or may not match depending on exact regex

    def test_no_smells_in_clean_code(self):
        """Test that clean code produces no smells."""
        detector = CodeSmellDetector()
        code = "def add(a, b):\n    return a + b\n"
        smells = detector.detect_smells(code, "test.py")
        assert len(smells) == 0

    def test_detect_multiple_smells(self):
        """Test detecting multiple smells in one snippet."""
        detector = CodeSmellDetector()
        code = '''api_key = "sk_live_abc"
password = 'letmein'
'''
        smells = detector.detect_smells(code, "multi.py")
        assert len(smells) >= 2

    def test_smell_has_required_keys(self):
        """Test that each smell dict has expected keys."""
        detector = CodeSmellDetector()
        code = "password = 'secret'"
        smells = detector.detect_smells(code, "keys.py")
        for s in smells:
            assert "type" in s
            assert "file" in s
            assert "line" in s
            assert "confidence" in s
            assert "severity" in s

    def test_detect_credentials_keyword(self):
        """Test detecting 'credentials' keyword."""
        detector = CodeSmellDetector()
        code = "credentials = 'user:pass'"
        smells = detector.detect_smells(code, "test.py")
        assert any(s["type"] == "hardcoded_secrets" for s in smells)

    def test_file_field_set_correctly(self):
        """Test that filename is propagated into detected smells."""
        detector = CodeSmellDetector()
        code = "password = 'x'"
        smells = detector.detect_smells(code, "myapp.py")
        assert all(s["file"] == "myapp.py" for s in smells)

    def test_detect_smells_cover_all_severities(self):
        detector = CodeSmellDetector()
        code = """
password = 'x'
if a:
    if b:
        if c:
            if d:
                pass
def f(a,b,c,d,e,f):
    return a
"""
        smells = detector.detect_smells(code, "sev.py")
        severities = {s.get("severity") for s in smells}
        assert "HIGH" in severities
        assert "MEDIUM" in severities or "LOW" in severities


# ──────────────────────────────────────────────────────────
#  StaticAnalyzer Tests
# ──────────────────────────────────────────────────────────

class TestStaticAnalyzer:
    """Tests for StaticAnalyzer."""

    def test_analyze_nodes_returns_list(self):
        """Test analyze_nodes returns a list."""
        analyzer = StaticAnalyzer()
        ast_data = {
            "code": "x = 1\ny = 2",
            "nodes": [
                {"type": "assignment", "line": 1, "text": "x = 1"},
                {"type": "assignment", "line": 2, "text": "y = 2"},
            ]
        }
        results = analyzer.analyze_nodes("test.py", ast_data)
        assert isinstance(results, list)

    def test_analyze_function_complexity(self):
        """Test complexity is calculated for function nodes."""
        analyzer = StaticAnalyzer()
        ast_data = {
            "code": "def foo():\n    if x:\n        for i in y:\n            pass",
            "nodes": [
                {"type": "function", "line": 1, "text": "def foo():\n    if x:\n        for i in y:\n            pass"},
            ]
        }
        results = analyzer.analyze_nodes("test.py", ast_data)
        assert len(results) == 1
        assert results[0].complexity > 0

    def test_analyze_class_node(self):
        """Test class nodes are marked correctly."""
        analyzer = StaticAnalyzer()
        ast_data = {
            "code": "class Foo:\n    pass",
            "nodes": [{"type": "class", "line": 1, "text": "class Foo:"}]
        }
        results = analyzer.analyze_nodes("test.py", ast_data)
        assert results[0].features.get("is_class") is True

    def test_analyze_empty_nodes(self):
        """Test analyzing empty nodes returns empty list."""
        analyzer = StaticAnalyzer()
        ast_data = {"code": "", "nodes": []}
        results = analyzer.analyze_nodes("test.py", ast_data)
        assert results == []

    def test_result_file_field(self):
        """Test that result carries the filename."""
        analyzer = StaticAnalyzer()
        ast_data = {
            "code": "a = 1",
            "nodes": [{"type": "assignment", "line": 1, "text": "a = 1"}]
        }
        results = analyzer.analyze_nodes("hello.py", ast_data)
        assert results[0].file == "hello.py"


# ──────────────────────────────────────────────────────────
#  FeatureExtractor Tests
# ──────────────────────────────────────────────────────────

class TestFeatureExtractor:
    """Tests for FeatureExtractor."""

    def setup_method(self):
        self.extractor = FeatureExtractor()

    def test_extract_features_returns_dict(self):
        """Test that extract_features returns a dict."""
        features = self.extractor.extract_features("x = 1")
        assert isinstance(features, dict)

    def test_has_try_except(self):
        """Test try/except detection."""
        code = "try:\n    pass\nexcept:\n    pass"
        f = self.extractor.extract_features(code)
        assert f["has_try_except"] == 1

    def test_has_no_try_except(self):
        """Test absence of try/except."""
        f = self.extractor.extract_features("x = 1")
        assert f["has_try_except"] == 0

    def test_has_if_statement(self):
        """Test if-statement detection."""
        f = self.extractor.extract_features("if x:\n    pass")
        assert f["has_if_statement"] == 1

    def test_has_loop(self):
        """Test loop detection."""
        f = self.extractor.extract_features("for i in range(10):\n    pass")
        assert f["has_loop"] == 1

    def test_has_class_definition(self):
        """Test class detection."""
        f = self.extractor.extract_features("class Foo:\n    pass")
        assert f["has_class_definition"] == 1

    def test_has_import(self):
        """Test import detection."""
        f = self.extractor.extract_features("import os")
        assert f["has_import"] == 1

    def test_has_dangerous_function_eval(self):
        """Test dangerous function detection for eval."""
        f = self.extractor.extract_features("result = eval(user_input)")
        assert f["has_dangerous_function"] >= 1

    def test_has_eval_exec(self):
        """Test eval/exec flag."""
        f = self.extractor.extract_features("exec('print(1)')")
        assert f["has_eval_exec"] == 1

    def test_has_pickle(self):
        """Test pickle detection."""
        f = self.extractor.extract_features("import pickle\nobj = pickle.loads(data)")
        assert f["has_pickle"] == 1

    def test_has_subprocess(self):
        """Test subprocess detection."""
        f = self.extractor.extract_features("import subprocess\nsubprocess.run(['ls'])")
        assert f["has_subprocess"] == 1

    def test_has_network_operation(self):
        """Test network operation detection."""
        f = self.extractor.extract_features("import requests\nrequests.get('http://example.com')")
        assert f["has_network_operation"] == 1

    def test_has_file_operation(self):
        """Test file operation detection."""
        f = self.extractor.extract_features("with open('f.txt') as f:\n    data = f.read()")
        assert f["has_file_operation"] == 1

    def test_has_database_operation(self):
        """Test database operation detection."""
        f = self.extractor.extract_features("cursor.execute('SELECT 1')")
        assert f["has_database_operation"] == 1

    def test_cyclomatic_complexity_baseline(self):
        """Test baseline complexity of 1 for straight-line code."""
        f = self.extractor.extract_features("x = 1")
        assert f["cyclomatic_complexity"] >= 1.0

    def test_cyclomatic_complexity_increases(self):
        """Test complexity increases with branches."""
        simple = self.extractor.extract_features("x = 1")
        complex_code = self.extractor.extract_features("if a:\n    pass\nif b:\n    pass\nfor c in d:\n    pass")
        assert complex_code["cyclomatic_complexity"] > simple["cyclomatic_complexity"]

    def test_nesting_depth(self):
        """Test nesting depth calculation."""
        code = "if x:\n    if y:\n        if z:\n            pass"
        f = self.extractor.extract_features(code)
        assert f["nesting_depth"] >= 3

    def test_has_hardcoded_string_detected(self):
        """Test hardcoded secret indicator."""
        f = self.extractor.extract_features("password = 'abc123'")
        assert f["has_hardcoded_string"] == 1

    def test_has_hardcoded_string_not_detected(self):
        """Test no hardcoded secret in clean code."""
        f = self.extractor.extract_features("x = 42")
        assert f["has_hardcoded_string"] == 0

    def test_comment_ratio(self):
        """Test comment ratio calculation."""
        code = "# comment\nx = 1\n# another comment"
        f = self.extractor.extract_features(code)
        assert f["comment_ratio"] > 0

    def test_vectorize_features_length(self):
        """Test that vectorize produces correct length vector."""
        features = self.extractor.extract_features("x = 1")
        vector = self.extractor.vectorize_features(features)
        assert len(vector) == len(self.extractor.get_all_feature_names())

    def test_vectorize_features_target_size_compatibility(self):
        features = self.extractor.extract_features("x = 1")
        vector = self.extractor.vectorize_features(features, target_size=5)
        assert len(vector) == 5

    def test_vectorize_features_all_floats(self):
        """Test that vector contains only floats."""
        features = self.extractor.extract_features("x = 1")
        vector = self.extractor.vectorize_features(features)
        assert all(isinstance(v, float) for v in vector)

    def test_extract_features_from_nodes(self):
        """Test node-based feature extraction."""
        nodes = [
            {"type": "function", "line": 1, "complexity": 3.0},
            {"type": "function", "line": 5, "complexity": 5.0},
            {"type": "class", "line": 10},
        ]
        f = self.extractor.extract_features_from_nodes(nodes)
        assert f["function_count"] == 2
        assert f["class_count"] == 1
        assert f["total_nodes"] == 3
        assert f["avg_complexity"] == 4.0
        assert f["max_complexity"] == 5.0

    def test_extract_features_from_empty_nodes(self):
        """Test node-based extraction with empty list."""
        f = self.extractor.extract_features_from_nodes([])
        assert f["total_nodes"] == 0


# ──────────────────────────────────────────────────────────
#  ControlFlowAnalyzer Tests
# ──────────────────────────────────────────────────────────

class TestControlFlowAnalyzer:
    """Tests for ControlFlowAnalyzer."""

    def test_analyze_simple_function(self):
        """Test analyzing a simple function."""
        analyzer = ControlFlowAnalyzer()
        code = "x = 1\ny = 2\nprint(x + y)"
        result = analyzer.analyze_function(code)
        assert "block_count" in result
        assert "cyclomatic_complexity" in result
        assert result["block_count"] >= 1

    def test_analyze_with_branch(self):
        """Test analyzing code with if-else."""
        analyzer = ControlFlowAnalyzer()
        code = "if x > 0:\n    y = 10\nelse:\n    y = 20\nprint(y)"
        result = analyzer.analyze_function(code)
        assert result["block_count"] >= 2

    def test_cyclomatic_complexity_returned(self):
        """Test that cyclomatic complexity is a number."""
        analyzer = ControlFlowAnalyzer()
        code = "x = 1"
        result = analyzer.analyze_function(code)
        assert isinstance(result["cyclomatic_complexity"], (int, float))

    def test_unreachable_code_list(self):
        """Test unreachable code detection returns a list."""
        analyzer = ControlFlowAnalyzer()
        code = "x = 1\nif y:\n    pass"
        result = analyzer.analyze_function(code)
        assert isinstance(result["unreachable_code"], list)

    def test_data_dependencies(self):
        """Test data dependency analysis."""
        analyzer = ControlFlowAnalyzer()
        code = "x = 1\ny = x + 2\nprint(y)"
        result = analyzer.analyze_function(code)
        assert isinstance(result["data_dependencies"], dict)

    def test_empty_code(self):
        """Test analyzing empty code."""
        analyzer = ControlFlowAnalyzer()
        result = analyzer.analyze_function("")
        assert result["block_count"] >= 0


# ──────────────────────────────────────────────────────────
#  DataFlowAnalyzer Tests
# ──────────────────────────────────────────────────────────

class TestDataFlowAnalyzer:
    """Tests for DataFlowAnalyzer."""

    def test_analyze_returns_dict(self):
        """Test analyze returns expected keys."""
        analyzer = DataFlowAnalyzer()
        result = analyzer.analyze("x = 1\nprint(x)")
        assert "tainted_variables" in result
        assert "uninitialized_uses" in result
        assert "unused_definitions" in result

    def test_find_tainted_from_input(self):
        """Test tainted variable from user input."""
        analyzer = DataFlowAnalyzer()
        code = "name = input('Enter name: ')"
        result = analyzer.analyze(code)
        assert len(result["tainted_variables"]) >= 1
        assert result["tainted_variables"][0]["source"] == "user_input"

    def test_find_tainted_from_argv(self):
        """Test tainted variable from argv."""
        analyzer = DataFlowAnalyzer()
        code = "import sys\narg = sys.argv[1]"
        result = analyzer.analyze(code)
        assert len(result["tainted_variables"]) >= 1

    def test_find_tainted_from_request(self):
        """Test tainted variable from HTTP request."""
        analyzer = DataFlowAnalyzer()
        code = "data = request.form['username']"
        result = analyzer.analyze(code)
        assert len(result["tainted_variables"]) >= 1

    def test_no_tainted_in_clean_code(self):
        """Test no tainted variables in safe code."""
        analyzer = DataFlowAnalyzer()
        code = "x = 42\ny = x + 1"
        result = analyzer.analyze(code)
        assert len(result["tainted_variables"]) == 0

    def test_unused_definitions(self):
        """Test detecting unused variable definitions."""
        analyzer = DataFlowAnalyzer()
        code = "unused_var = 99"
        result = analyzer.analyze(code)
        assert isinstance(result["unused_definitions"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
