"""
Configuration management for the code smell detection compiler.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Set
from enum import Enum
import yaml
from pathlib import Path


class Severity(str, Enum):
    """Severity levels for code smells."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class SmellType(str, Enum):
    """Types of code smells to detect."""
    HARDCODED_SECRETS = "hardcoded_secrets"
    SQL_INJECTION_RISK = "sql_injection_risk"
    UNSAFE_DESERIALIZATION = "unsafe_deserialization"
    DEAD_CODE = "dead_code"
    GOD_OBJECT = "god_object"
    LONG_METHOD = "long_method"
    NULL_POINTER_RISK = "null_pointer_risk"


@dataclass
class SmellConfig:
    """Configuration for a specific code smell."""
    enabled: bool = True
    severity: Severity = Severity.MEDIUM
    confidence_threshold: float = 0.7
    rules: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class MLConfig:
    """Configuration for ML inference."""
    model_name: str = "randomforest"
    model_path: str = "data/models/model.pkl"
    confidence_threshold: float = 0.7
    use_ensemble: bool = False
    ensemble_models: List[str] = field(default_factory=lambda: ["randomforest", "svm"])


@dataclass
class AnalysisConfig:
    """Configuration for static analysis."""
    max_method_lines: int = 30
    max_class_complexity: int = 10
    detect_dead_code: bool = True
    detect_duplicate_code: bool = True
    control_flow_analysis: bool = True
    data_flow_analysis: bool = True


@dataclass
class ReportConfig:
    """Configuration for report generation."""
    format: str = "json"  # json, text, xml, csv
    include_code_snippets: bool = True
    include_cwe_mapping: bool = True
    include_owasp_mapping: bool = True
    include_suggestions: bool = True
    verbose: bool = False


@dataclass
class Config:
    """Main configuration class."""
    # Project settings
    project_name: str = "Code Smell Detector"
    version: str = "1.0.0"
    
    # Analysis settings
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    
    # ML settings
    ml: MLConfig = field(default_factory=MLConfig)
    
    # Report settings
    report: ReportConfig = field(default_factory=ReportConfig)
    
    # Enabled smells
    enabled_smells: Set[SmellType] = field(default_factory=lambda: set(SmellType))
    
    # Per-smell configuration
    smell_configs: Dict[SmellType, SmellConfig] = field(default_factory=dict)
    
    # Supported languages
    supported_languages: List[str] = field(default_factory=lambda: ["python", "java"])
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/code_smell_detector.log"

    def __post_init__(self):
        """Initialize smell configurations."""
        if not self.smell_configs:
            self._init_default_smell_configs()

    def _init_default_smell_configs(self):
        """Initialize default configurations for all smell types."""
        defaults = {
            SmellType.HARDCODED_SECRETS: SmellConfig(
                enabled=True,
                severity=Severity.HIGH,
                confidence_threshold=0.85,
                description="Hardcoded credentials or API keys"
            ),
            SmellType.SQL_INJECTION_RISK: SmellConfig(
                enabled=True,
                severity=Severity.HIGH,
                confidence_threshold=0.80,
                description="Dynamic SQL construction without parameterization"
            ),
            SmellType.UNSAFE_DESERIALIZATION: SmellConfig(
                enabled=True,
                severity=Severity.HIGH,
                confidence_threshold=0.82,
                description="Unsafe object deserialization patterns"
            ),
            SmellType.NULL_POINTER_RISK: SmellConfig(
                enabled=True,
                severity=Severity.MEDIUM,
                confidence_threshold=0.75,
                description="Potential null reference dereferences"
            ),
            SmellType.DEAD_CODE: SmellConfig(
                enabled=True,
                severity=Severity.LOW,
                confidence_threshold=0.70,
                description="Unreachable or unused code"
            ),
            SmellType.GOD_OBJECT: SmellConfig(
                enabled=True,
                severity=Severity.MEDIUM,
                confidence_threshold=0.72,
                description="Classes with too many responsibilities"
            ),
            SmellType.LONG_METHOD: SmellConfig(
                enabled=True,
                severity=Severity.LOW,
                confidence_threshold=0.65,
                description="Methods exceeding complexity thresholds"
            ),
        }
        self.smell_configs = defaults

    @classmethod
    def from_yaml(cls, path: str) -> "Config":
        """Load configuration from YAML file."""
        config_path = Path(path)
        if not config_path.exists():
            return cls()
        
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f) or {}
        
        # Parse nested dataclasses
        analysis_data = data.get('analysis', {})
        ml_data = data.get('ml', {})
        report_data = data.get('report', {})
        
        config = cls(
            project_name=data.get('project_name', cls.__dataclass_fields__['project_name'].default),
            version=data.get('version', cls.__dataclass_fields__['version'].default),
            analysis=AnalysisConfig(**analysis_data) if analysis_data else AnalysisConfig(),
            ml=MLConfig(**ml_data) if ml_data else MLConfig(),
            report=ReportConfig(**report_data) if report_data else ReportConfig(),
            supported_languages=data.get('supported_languages', ['python', 'java']),
            log_level=data.get('log_level', 'INFO'),
            log_file=data.get('log_file', 'logs/code_smell_detector.log'),
        )
        
        return config

    def to_yaml(self, path: str):
        """Save configuration to YAML file."""
        config_path = Path(path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'project_name': self.project_name,
            'version': self.version,
            'analysis': {
                'max_method_lines': self.analysis.max_method_lines,
                'max_class_complexity': self.analysis.max_class_complexity,
                'detect_dead_code': self.analysis.detect_dead_code,
                'control_flow_analysis': self.analysis.control_flow_analysis,
            },
            'ml': {
                'model_name': self.ml.model_name,
                'model_path': self.ml.model_path,
                'confidence_threshold': self.ml.confidence_threshold,
            },
            'report': {
                'format': self.report.format,
                'include_code_snippets': self.report.include_code_snippets,
                'include_cwe_mapping': self.report.include_cwe_mapping,
            },
            'supported_languages': self.supported_languages,
            'log_level': self.log_level,
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)


# Global config instance
_global_config: Config = Config()


def get_config() -> Config:
    """Get the global configuration instance."""
    return _global_config


def load_config(path: str) -> Config:
    """Load configuration from file."""
    global _global_config
    _global_config = Config.from_yaml(path)
    return _global_config


# CWE and OWASP mappings
CWE_MAPPING = {
    SmellType.HARDCODED_SECRETS: "CWE-798",
    SmellType.SQL_INJECTION_RISK: "CWE-89",
    SmellType.UNSAFE_DESERIALIZATION: "CWE-502",
    SmellType.NULL_POINTER_RISK: "CWE-476",
    SmellType.DEAD_CODE: "CWE-561",
    SmellType.GOD_OBJECT: "CWE-400",  # Uncontrolled Resource Consumption
    SmellType.LONG_METHOD: "CWE-400",
}

OWASP_MAPPING = {
    SmellType.HARDCODED_SECRETS: "A02:2021 - Cryptographic Failures",
    SmellType.SQL_INJECTION_RISK: "A03:2021 - Injection",
    SmellType.UNSAFE_DESERIALIZATION: "A08:2021 - Software and Data Integrity Failures",
    SmellType.NULL_POINTER_RISK: "A06:2021 - Vulnerable and Outdated Components",
    SmellType.DEAD_CODE: "A04:2021 - Insecure Design",
    SmellType.GOD_OBJECT: "A04:2021 - Insecure Design",
    SmellType.LONG_METHOD: "A04:2021 - Insecure Design",
}
