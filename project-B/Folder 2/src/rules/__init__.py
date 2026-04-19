"""Package initialization for rules module."""
from .rule_engine import RuleEngine
from .patterns import CodeSmellPatterns

__all__ = ["RuleEngine", "CodeSmellPatterns"]
