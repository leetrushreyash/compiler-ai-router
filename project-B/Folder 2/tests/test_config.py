"""Tests for configuration management."""
import pytest
import sys
import os
import tempfile
from pathlib import Path

# Add project root to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import (
    Config, AnalysisConfig, MLConfig, ReportConfig,
    SmellConfig, Severity, SmellType,
    get_config, load_config,
    CWE_MAPPING, OWASP_MAPPING,
)


# ──────────────────────────────────────────────────────────
#  Enum Tests
# ──────────────────────────────────────────────────────────

class TestSeverity:
    """Tests for Severity enum."""

    def test_values(self):
        assert Severity.HIGH == "HIGH"
        assert Severity.MEDIUM == "MEDIUM"
        assert Severity.LOW == "LOW"
        assert Severity.INFO == "INFO"

    def test_iteration(self):
        names = [s.value for s in Severity]
        assert "HIGH" in names
        assert "LOW" in names


class TestSmellType:
    """Tests for SmellType enum."""

    def test_all_smell_types(self):
        expected = {
            "hardcoded_secrets", "sql_injection_risk",
            "unsafe_deserialization", "dead_code",
            "god_object", "long_method", "null_pointer_risk",
        }
        actual = {s.value for s in SmellType}
        assert expected == actual

    def test_string_value(self):
        assert SmellType.HARDCODED_SECRETS == "hardcoded_secrets"


# ──────────────────────────────────────────────────────────
#  Dataclass Config Tests
# ──────────────────────────────────────────────────────────

class TestSmellConfig:
    """Tests for SmellConfig dataclass."""

    def test_defaults(self):
        sc = SmellConfig()
        assert sc.enabled is True
        assert sc.severity == Severity.MEDIUM
        assert sc.confidence_threshold == 0.7

    def test_custom(self):
        sc = SmellConfig(enabled=False, severity=Severity.HIGH, confidence_threshold=0.9)
        assert sc.enabled is False
        assert sc.severity == Severity.HIGH


class TestAnalysisConfig:
    """Tests for AnalysisConfig dataclass."""

    def test_defaults(self):
        ac = AnalysisConfig()
        assert ac.max_method_lines == 30
        assert ac.max_class_complexity == 10
        assert ac.detect_dead_code is True
        assert ac.control_flow_analysis is True


class TestMLConfig:
    """Tests for MLConfig dataclass."""

    def test_defaults(self):
        mc = MLConfig()
        assert mc.model_name == "randomforest"
        assert mc.confidence_threshold == 0.7
        assert mc.use_ensemble is False
        assert "randomforest" in mc.ensemble_models


class TestReportConfig:
    """Tests for ReportConfig dataclass."""

    def test_defaults(self):
        rc = ReportConfig()
        assert rc.format == "json"
        assert rc.include_code_snippets is True
        assert rc.include_cwe_mapping is True


# ──────────────────────────────────────────────────────────
#  Config Tests
# ──────────────────────────────────────────────────────────

class TestConfig:
    """Tests for the main Config class."""

    def test_default_config(self):
        """Test default config values."""
        cfg = Config()
        assert cfg.project_name == "Code Smell Detector"
        assert cfg.version == "1.0.0"
        assert "python" in cfg.supported_languages
        assert cfg.log_level == "INFO"

    def test_default_smell_configs_populated(self):
        """Test that smell configs are auto-populated."""
        cfg = Config()
        assert len(cfg.smell_configs) == len(SmellType)

    def test_smell_config_severities(self):
        """Test specific smell config severities."""
        cfg = Config()
        assert cfg.smell_configs[SmellType.HARDCODED_SECRETS].severity == Severity.HIGH
        assert cfg.smell_configs[SmellType.DEAD_CODE].severity == Severity.LOW

    def test_from_yaml_nonexistent_file(self):
        """Test loading from non-existent YAML returns defaults."""
        cfg = Config.from_yaml("nonexistent_config_xyz.yaml")
        assert cfg.project_name == "Code Smell Detector"

    def test_from_yaml_real_config(self):
        """Test loading the project's config.yaml."""
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            cfg = Config.from_yaml(str(config_path))
            assert cfg.project_name == "Code Smell Detection Compiler"
            assert cfg.version == "1.0.0"

    def test_from_yaml_custom(self):
        """Test loading from a custom YAML."""
        yaml_content = """
project_name: "Test Project"
version: "2.0.0"
log_level: "DEBUG"
supported_languages:
  - python
analysis:
  max_method_lines: 50
ml:
  model_name: "svm"
  confidence_threshold: 0.8
report:
  format: "text"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            tmp = f.name
        try:
            cfg = Config.from_yaml(tmp)
            assert cfg.project_name == "Test Project"
            assert cfg.version == "2.0.0"
            assert cfg.log_level == "DEBUG"
            assert cfg.analysis.max_method_lines == 50
            assert cfg.ml.model_name == "svm"
            assert cfg.ml.confidence_threshold == 0.8
            assert cfg.report.format == "text"
        finally:
            os.unlink(tmp)

    def test_to_yaml_and_reload(self):
        """Test round-trip save/load of config."""
        cfg = Config(project_name="Round Trip", version="3.0.0", log_level="WARNING")
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as f:
            tmp = f.name
        try:
            cfg.to_yaml(tmp)
            loaded = Config.from_yaml(tmp)
            assert loaded.project_name == "Round Trip"
            assert loaded.version == "3.0.0"
            assert loaded.log_level == "WARNING"
        finally:
            os.unlink(tmp)


# ──────────────────────────────────────────────────────────
#  Global config functions
# ──────────────────────────────────────────────────────────

class TestGlobalConfig:
    """Tests for get_config and load_config."""

    def test_get_config_returns_config(self):
        """Test get_config returns a Config instance."""
        cfg = get_config()
        assert isinstance(cfg, Config)

    def test_load_config_from_yaml(self):
        """Test load_config updates global config."""
        config_path = Path(__file__).parent.parent / "config.yaml"
        if config_path.exists():
            cfg = load_config(str(config_path))
            assert isinstance(cfg, Config)
            assert cfg.project_name == "Code Smell Detection Compiler"


# ──────────────────────────────────────────────────────────
#  CWE / OWASP Mapping Tests
# ──────────────────────────────────────────────────────────

class TestMappings:
    """Tests for CWE and OWASP mappings."""

    def test_all_smell_types_have_cwe(self):
        """Test every SmellType has a CWE mapping."""
        for smell in SmellType:
            assert smell in CWE_MAPPING

    def test_all_smell_types_have_owasp(self):
        """Test every SmellType has an OWASP mapping."""
        for smell in SmellType:
            assert smell in OWASP_MAPPING

    def test_cwe_format(self):
        """Test CWE values follow CWE-NNN format."""
        for cwe in CWE_MAPPING.values():
            assert cwe.startswith("CWE-")

    def test_owasp_format(self):
        """Test OWASP values contain year reference."""
        for owasp in OWASP_MAPPING.values():
            assert "2021" in owasp

    def test_specific_mappings(self):
        """Test specific known mappings."""
        assert CWE_MAPPING[SmellType.HARDCODED_SECRETS] == "CWE-798"
        assert CWE_MAPPING[SmellType.SQL_INJECTION_RISK] == "CWE-89"
        assert "Injection" in OWASP_MAPPING[SmellType.SQL_INJECTION_RISK]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
