"""Tests for AST parser module."""
import pytest
import sys
import os
import tempfile
from pathlib import Path

# Add project root to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.parser.ast_builder import ASTBuilder, ASTVisitor, FunctionExtractor, ClassExtractor
from src.parser.code_extractor import CodeExtractor


# ──────────────────────────────────────────────────────────
#  ASTBuilder Tests
# ──────────────────────────────────────────────────────────

class TestASTBuilder:
    """Tests for ASTBuilder."""

    def test_init_python(self):
        """Test initializing builder for Python."""
        builder = ASTBuilder("python")
        assert builder.language == "python"

    def test_init_case_insensitive(self):
        """Test language name is case-insensitive."""
        builder = ASTBuilder("Python")
        assert builder.language == "python"

    def test_parse_simple_python_code(self):
        """Test parsing simple Python code."""
        builder = ASTBuilder("python")
        code = """
def hello(name):
    return f"Hello, {name}!"

class Calculator:
    def add(self, a, b):
        return a + b
"""
        result = builder.parse_code(code, "test.py")

        assert result["filename"] == "test.py"
        assert result["language"] == "python"
        assert len(result["nodes"]) > 0

    def test_parse_empty_code(self):
        """Test parsing empty code."""
        builder = ASTBuilder("python")
        result = builder.parse_code("", "empty.py")

        assert result["filename"] == "empty.py"
        assert isinstance(result["nodes"], list)
        assert isinstance(result["errors"], list)

    def test_parse_detects_functions(self):
        """Test that functions are detected as nodes."""
        builder = ASTBuilder("python")
        code = "def foo():\n    pass\ndef bar(x):\n    return x"
        result = builder.parse_code(code)
        func_nodes = [n for n in result["nodes"] if n["type"] == "function"]
        assert len(func_nodes) == 2

    def test_parse_detects_classes(self):
        """Test that classes are detected as nodes."""
        builder = ASTBuilder("python")
        code = "class Dog:\n    pass\nclass Cat:\n    pass"
        result = builder.parse_code(code)
        class_nodes = [n for n in result["nodes"] if n["type"] == "class"]
        assert len(class_nodes) == 2

    def test_parse_detects_imports(self):
        """Test that imports are detected."""
        builder = ASTBuilder("python")
        code = "import os\nfrom pathlib import Path"
        result = builder.parse_code(code)
        import_nodes = [n for n in result["nodes"] if n["type"] == "import"]
        assert len(import_nodes) == 2

    def test_parse_detects_assignments(self):
        """Test that assignments are detected."""
        builder = ASTBuilder("python")
        code = "x = 1\ny = 2"
        result = builder.parse_code(code)
        assign_nodes = [n for n in result["nodes"] if n["type"] == "assignment"]
        assert len(assign_nodes) == 2

    def test_parse_code_lines_stored(self):
        """Test that lines are stored in result."""
        builder = ASTBuilder("python")
        code = "a = 1\nb = 2\nc = 3"
        result = builder.parse_code(code)
        assert result["lines"] == ["a = 1", "b = 2", "c = 3"]

    def test_parse_code_preserves_code(self):
        """Test that raw code is stored in result."""
        builder = ASTBuilder("python")
        code = "x = 42"
        result = builder.parse_code(code)
        assert result["code"] == code

    def test_parse_syntax_error_handled(self):
        """Test that syntax errors are caught gracefully."""
        builder = ASTBuilder("python")
        code = "def broken(\n    pass"
        result = builder.parse_code(code)
        # Should not crash; errors list may be populated
        assert isinstance(result["nodes"], list)

    def test_parse_file(self):
        """Test parsing from an actual file."""
        builder = ASTBuilder("python")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def greet():\n    print('hi')\n")
            f.flush()
            tmp = f.name
        try:
            result = builder.parse_file(tmp)
            assert result["language"] == "python"
            func_nodes = [n for n in result["nodes"] if n["type"] == "function"]
            assert len(func_nodes) == 1
        finally:
            os.unlink(tmp)

    def test_parse_file_not_found(self):
        """Test FileNotFoundError for missing file."""
        builder = ASTBuilder("python")
        with pytest.raises(FileNotFoundError):
            builder.parse_file("nonexistent_file_xyz.py")

    def test_parse_complex_code(self):
        """Test parsing code with mixed constructs."""
        builder = ASTBuilder("python")
        code = """
import os
from sys import argv

class Engine:
    def run(self, args):
        for a in args:
            if a:
                print(a)

def main():
    e = Engine()
    e.run(argv)
"""
        result = builder.parse_code(code, "complex.py")
        types = {n["type"] for n in result["nodes"]}
        assert "import" in types
        assert "class" in types
        assert "function" in types

    def test_function_node_has_name(self):
        """Test that function nodes include 'name' key."""
        builder = ASTBuilder("python")
        code = "def my_func(a, b):\n    return a + b"
        result = builder.parse_code(code)
        func_nodes = [n for n in result["nodes"] if n["type"] == "function"]
        assert len(func_nodes) == 1
        assert func_nodes[0]["name"] == "my_func"

    def test_class_node_has_name(self):
        """Test that class nodes include 'name' key."""
        builder = ASTBuilder("python")
        code = "class MyClass:\n    pass"
        result = builder.parse_code(code)
        cls = [n for n in result["nodes"] if n["type"] == "class"]
        assert len(cls) == 1
        assert cls[0]["name"] == "MyClass"

    def test_fallback_for_java(self):
        """Test fallback regex parsing for non-Python language."""
        builder = ASTBuilder("java")
        code = "class Main {\n  void run() {}\n}"
        result = builder.parse_code(code)
        assert result["language"] == "java"
        assert isinstance(result["nodes"], list)


# ──────────────────────────────────────────────────────────
#  ASTVisitor Tests
# ──────────────────────────────────────────────────────────

class TestASTVisitor:
    """Tests for ASTVisitor base class."""

    def test_generic_visit(self):
        """Test default visitor returns node unchanged."""
        visitor = ASTVisitor()
        node = {"type": "unknown_type", "line": 1}
        result = visitor.visit(node)
        assert result == node


# ──────────────────────────────────────────────────────────
#  FunctionExtractor Tests
# ──────────────────────────────────────────────────────────

class TestFunctionExtractor:
    """Tests for FunctionExtractor."""

    def test_extract_functions(self):
        """Test extracting function nodes."""
        extractor = FunctionExtractor()
        nodes = [
            {"type": "function", "line": 1, "text": "def foo():"},
            {"type": "assignment", "line": 5, "text": "x = 1"},
            {"type": "function", "line": 10, "text": "def bar(x):"},
        ]
        functions = extractor.extract(nodes)
        assert len(functions) == 2

    def test_extract_no_functions(self):
        """Test extracting from nodes without functions."""
        extractor = FunctionExtractor()
        nodes = [
            {"type": "assignment", "line": 1, "text": "x = 1"},
            {"type": "import", "line": 2, "text": "import os"},
        ]
        functions = extractor.extract(nodes)
        assert len(functions) == 0

    def test_extract_function_definition_type(self):
        """Test function_definition type is also recognized."""
        extractor = FunctionExtractor()
        nodes = [{"type": "function_definition", "line": 1, "text": "def baz():"}]
        assert len(extractor.extract(nodes)) == 1

    def test_extract_empty_list(self):
        """Test extracting from empty nodes list."""
        extractor = FunctionExtractor()
        assert extractor.extract([]) == []


# ──────────────────────────────────────────────────────────
#  ClassExtractor Tests
# ──────────────────────────────────────────────────────────

class TestClassExtractor:
    """Tests for ClassExtractor."""

    def test_extract_classes(self):
        """Test extracting class nodes."""
        extractor = ClassExtractor()
        nodes = [
            {"type": "class", "line": 1, "text": "class Foo:"},
            {"type": "function", "line": 5, "text": "def bar():"},
            {"type": "class_definition", "line": 10, "text": "class Baz:"},
        ]
        classes = extractor.extract(nodes)
        assert len(classes) == 2

    def test_extract_no_classes(self):
        """Test extracting when no classes present."""
        extractor = ClassExtractor()
        nodes = [{"type": "function", "line": 1, "text": "def foo():"}]
        assert len(extractor.extract(nodes)) == 0


# ──────────────────────────────────────────────────────────
#  CodeExtractor Tests
# ──────────────────────────────────────────────────────────

class TestCodeExtractor:
    """Tests for CodeExtractor."""

    def test_get_line_range(self):
        """Test retrieving a line range from a file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("line1\nline2\nline3\nline4\nline5\n")
            f.flush()
            tmp = f.name
        try:
            snippet = CodeExtractor.get_line_range(tmp, 2, 4, context_lines=0)
            assert "line2" in snippet
            assert "line4" in snippet
        finally:
            os.unlink(tmp)

    def test_get_line_range_file_not_found(self):
        """Test graceful handling of missing file."""
        snippet = CodeExtractor.get_line_range("no_such_file.py", 1, 1)
        assert "File not found" in snippet

    def test_get_exact_line(self):
        """Test getting a single specific line."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("alpha\nbeta\ngamma\n")
            f.flush()
            tmp = f.name
        try:
            line = CodeExtractor.get_exact_line(tmp, 2)
            assert line is not None
            assert "beta" in line
        finally:
            os.unlink(tmp)

    def test_get_exact_line_file_not_found(self):
        """Test None returned for missing file."""
        assert CodeExtractor.get_exact_line("no_such_file.py", 1) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
