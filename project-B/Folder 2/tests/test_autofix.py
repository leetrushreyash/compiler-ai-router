"""Tests for autofix full-code generation."""
import sys
from pathlib import Path

# Add project root to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.autofix import AutoFixer


def test_generate_fixed_code_returns_string():
    fixer = AutoFixer()
    source = "password = 'secret'\nprint(password)"
    issues = [
        {
            "type": "hardcoded_secrets",
            "line": 1,
            "code": "password = 'secret'",
            "confidence": 0.95,
            "severity": "HIGH",
        }
    ]

    fixed = fixer.generate_fixed_code(source, issues)
    assert isinstance(fixed, str)
    assert "os.environ.get" in fixed


def test_generate_fixed_code_safe_fallback():
    fixer = AutoFixer()
    source = "x = 1"
    fixed = fixer.generate_fixed_code(source, [])
    assert fixed == source


def test_fix_weak_crypto_rewrites_md5():
    fixer = AutoFixer()
    source = "import hashlib\nh = hashlib.md5(data).hexdigest()"
    issues = [
        {
            "type": "weak_crypto",
            "line": 2,
            "code": "h = hashlib.md5(data).hexdigest()",
            "confidence": 0.9,
            "severity": "HIGH",
        }
    ]

    fixed = fixer.generate_fixed_code(source, issues)
    assert "hashlib.sha256" in fixed
