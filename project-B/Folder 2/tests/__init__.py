"""Test suite initialization."""
import pytest
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
import sys
sys.path.insert(0, str(src_path))
