"""Tests for report generator and output formatter."""
import pytest
import sys
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime

# Add project root to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.reporting.report_generator import ReportGenerator, Issue
from src.reporting.formatter import OutputFormatter, OutputFormat


# ──────────────────────────────────────────────────────────
#  Issue Dataclass Tests
# ──────────────────────────────────────────────────────────

class TestIssue:
    """Tests for the Issue dataclass."""

    def test_create_issue_minimal(self):
        """Test creating issue with only required fields."""
        issue = Issue(file="a.py", line=1)
        assert issue.file == "a.py"
        assert issue.line == 1
        assert issue.severity == "MEDIUM"
        assert issue.suggestions == []

    def test_create_issue_full(self):
        """Test creating issue with all fields."""
        issue = Issue(
            file="app.py", line=42, column=5,
            type="hardcoded_secrets", severity="HIGH",
            confidence=0.95, explanation="Hardcoded password",
            description="Hardcoded password",
            recommendation="Use environment variables",
            category="security",
            risk_score=0.95,
            cwe="CWE-798", owasp="A02:2021",
            code_snippet="password = 'abc'",
            suggestions=["Use env vars"],
        )
        assert issue.severity == "HIGH"
        assert issue.confidence == 0.95
        assert len(issue.suggestions) == 1
        assert issue.category == "security"

    def test_suggestions_default_empty_list(self):
        """Test suggestions defaults to empty list, not None."""
        issue = Issue(file="a.py", line=1)
        assert issue.suggestions is not None
        assert isinstance(issue.suggestions, list)


# ──────────────────────────────────────────────────────────
#  ReportGenerator Tests
# ──────────────────────────────────────────────────────────

class TestReportGenerator:
    """Tests for ReportGenerator."""

    def _make_generator_with_issues(self):
        gen = ReportGenerator("Test Project")
        gen.add_issue(Issue(
            file="a.py", line=10, type="hardcoded_secrets",
            severity="HIGH", confidence=0.90,
            explanation="Password found",
            cwe="CWE-798", code_snippet="password = 'x'",
        ))
        gen.add_issue(Issue(
            file="b.py", line=20, type="sql_injection_risk",
            severity="HIGH", confidence=0.85,
            explanation="SQL injection",
        ))
        gen.add_issue(Issue(
            file="a.py", line=30, type="dead_code",
            severity="LOW", confidence=0.70,
            explanation="Unreachable code",
        ))
        return gen

    def test_init(self):
        """Test generator initializes correctly."""
        gen = ReportGenerator("My Project")
        assert gen.project_name == "My Project"
        assert gen.issues == []

    def test_add_issue(self):
        """Test adding a single issue."""
        gen = ReportGenerator()
        gen.add_issue(Issue(file="x.py", line=1))
        assert len(gen.issues) == 1

    def test_add_issues_from_dicts(self):
        """Test adding multiple issues from dicts."""
        gen = ReportGenerator()
        gen.add_issues([
            {"file": "a.py", "line": 1, "type": "dead_code"},
            {"file": "b.py", "line": 2, "type": "long_method"},
        ])
        assert len(gen.issues) == 2

    def test_set_scan_time(self):
        """Test setting scan times."""
        gen = ReportGenerator()
        start = datetime(2026, 1, 1, 12, 0, 0)
        end = datetime(2026, 1, 1, 12, 0, 5)
        gen.set_scan_time(start, end)
        assert gen.scan_start_time == start
        assert gen.scan_end_time == end

    # ── JSON report ──────────────────────────────────────

    def test_generate_json_valid(self):
        """Test JSON report is valid JSON."""
        gen = self._make_generator_with_issues()
        output = gen.generate_json()
        data = json.loads(output)
        assert isinstance(data, dict)

    def test_json_has_required_keys(self):
        """Test JSON report contains essential keys."""
        gen = self._make_generator_with_issues()
        data = json.loads(gen.generate_json())
        for key in ("project", "total_issues", "severity_summary", "issues"):
            assert key in data
        assert "risk_score" in data["issues"][0]
        assert "recommendation" in data["issues"][0]

    def test_json_total_issues_count(self):
        """Test total issues count is correct."""
        gen = self._make_generator_with_issues()
        data = json.loads(gen.generate_json())
        assert data["total_issues"] == 3

    def test_json_severity_summary(self):
        """Test severity summary counts are correct."""
        gen = self._make_generator_with_issues()
        data = json.loads(gen.generate_json())
        assert data["severity_summary"]["HIGH"] == 2
        assert data["severity_summary"]["LOW"] == 1

    def test_json_scan_duration(self):
        """Test scan duration is calculated correctly."""
        gen = self._make_generator_with_issues()
        start = datetime(2026, 1, 1, 0, 0, 0)
        end = datetime(2026, 1, 1, 0, 0, 2)
        gen.set_scan_time(start, end)
        data = json.loads(gen.generate_json())
        assert data["scan_duration_ms"] == 2000

    def test_json_empty_report(self):
        """Test JSON report with no issues."""
        gen = ReportGenerator()
        data = json.loads(gen.generate_json())
        assert data["total_issues"] == 0
        assert data["issues"] == []

    # ── Text report ──────────────────────────────────────

    def test_generate_text_not_empty(self):
        """Test text report produces output."""
        gen = self._make_generator_with_issues()
        text = gen.generate_text()
        assert len(text) > 0

    def test_text_contains_severity(self):
        """Test text report contains severity labels."""
        gen = self._make_generator_with_issues()
        text = gen.generate_text()
        assert "HIGH" in text
        assert "LOW" in text

    def test_text_contains_filename(self):
        """Test text report mentions filenames."""
        gen = self._make_generator_with_issues()
        text = gen.generate_text()
        assert "a.py" in text
        assert "b.py" in text

    def test_text_empty_report(self):
        """Test text report with no issues."""
        gen = ReportGenerator()
        text = gen.generate_text()
        assert "Total Issues: 0" in text

    # ── CSV report ───────────────────────────────────────

    def test_generate_csv_header(self):
        """Test CSV report has header row."""
        gen = self._make_generator_with_issues()
        csv_text = gen.generate_csv()
        first_line = csv_text.split('\n')[0]
        assert "File" in first_line
        assert "Severity" in first_line
        assert "RiskScore" in first_line

    def test_csv_row_count(self):
        """Test CSV has correct number of data rows."""
        gen = self._make_generator_with_issues()
        csv_text = gen.generate_csv()
        lines = [l for l in csv_text.strip().split('\n') if l.strip()]
        assert len(lines) == 4  # 1 header + 3 issues

    def test_csv_empty_report(self):
        """Test CSV report with no issues has only header."""
        gen = ReportGenerator()
        csv_text = gen.generate_csv()
        lines = [l for l in csv_text.strip().split('\n') if l.strip()]
        assert len(lines) == 1  # header only

    # ── save to file ─────────────────────────────────────

    def test_save_json(self):
        """Test saving JSON report to file."""
        gen = self._make_generator_with_issues()
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            tmp = f.name
        try:
            gen.save(tmp, format="json")
            data = json.loads(Path(tmp).read_text())
            assert data["total_issues"] == 3
        finally:
            os.unlink(tmp)

    def test_save_text(self):
        """Test saving text report to file."""
        gen = self._make_generator_with_issues()
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            tmp = f.name
        try:
            gen.save(tmp, format="text")
            content = Path(tmp).read_text()
            assert "HIGH" in content
        finally:
            os.unlink(tmp)

    def test_save_csv(self):
        """Test saving CSV report to file."""
        gen = self._make_generator_with_issues()
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            tmp = f.name
        try:
            gen.save(tmp, format="csv")
            content = Path(tmp).read_text()
            assert "File" in content
        finally:
            os.unlink(tmp)

    def test_save_unknown_format_raises(self):
        """Test saving with unknown format raises ValueError."""
        gen = ReportGenerator()
        with pytest.raises(ValueError):
            gen.save("out.xyz", format="xml")

    # ── get_summary ──────────────────────────────────────

    def test_get_summary(self):
        """Test summary dictionary."""
        gen = self._make_generator_with_issues()
        summary = gen.get_summary()
        assert summary["total_issues"] == 3
        assert summary["severity_summary"]["HIGH"] == 2
        assert summary["files_analyzed"] == 2

    def test_summary_type_counts(self):
        """Test type counts in summary."""
        gen = self._make_generator_with_issues()
        summary = gen.get_summary()
        assert "hardcoded_secrets" in summary["type_summary"]
        assert "sql_injection_risk" in summary["type_summary"]

    def test_summary_empty_report(self):
        """Test summary for empty report."""
        gen = ReportGenerator()
        summary = gen.get_summary()
        assert summary["total_issues"] == 0
        assert summary["files_analyzed"] == 0


# ──────────────────────────────────────────────────────────
#  OutputFormatter Tests
# ──────────────────────────────────────────────────────────

class TestOutputFormatter:
    """Tests for OutputFormatter."""

    SAMPLE_ISSUE = {
        "file": "app.py",
        "line": 10,
        "type": "hardcoded_secrets",
        "severity": "HIGH",
        "confidence": 0.95,
        "explanation": "Hardcoded password",
        "cwe": "CWE-798",
    }

    def test_format_issue_text(self):
        """Test text formatting of an issue."""
        text = OutputFormatter.format_issue(self.SAMPLE_ISSUE, "text")
        assert "[HIGH]" in text
        assert "app.py" in text

    def test_format_issue_json(self):
        """Test JSON formatting of an issue."""
        output = OutputFormatter.format_issue(self.SAMPLE_ISSUE, "json")
        data = json.loads(output)
        assert data["severity"] == "HIGH"

    def test_format_issue_csv(self):
        """Test CSV formatting of an issue."""
        csv_row = OutputFormatter.format_issue(self.SAMPLE_ISSUE, "csv")
        assert "app.py" in csv_row

    def test_format_issue_fallback(self):
        """Test fallback formatting for unknown format."""
        output = OutputFormatter.format_issue(self.SAMPLE_ISSUE, "unknown")
        assert "app.py" in output

    def test_format_table_with_issues(self):
        """Test ASCII table formatting."""
        issues = [self.SAMPLE_ISSUE]
        table = OutputFormatter.format_table(issues)
        assert "Code Smell Detection Results" in table
        # Column values may be truncated; just verify the table is nonempty
        assert len(table) > 100

    def test_format_table_empty(self):
        """Test ASCII table with no issues."""
        table = OutputFormatter.format_table([])
        assert "No issues found" in table

    def test_generate_html_report(self):
        """Test HTML report generation."""
        report_data = {
            "summary": {
                "total_issues": 1,
                "severity_summary": {"HIGH": 1, "MEDIUM": 0, "LOW": 0},
            },
            "issues": [self.SAMPLE_ISSUE],
        }
        html = OutputFormatter.generate_html_report(report_data)
        assert "<html>" in html
        assert "HIGH" in html
        assert "app.py" in html

    def test_html_empty_report(self):
        """Test HTML report with no issues."""
        report_data = {
            "summary": {"total_issues": 0, "severity_summary": {}},
            "issues": [],
        }
        html = OutputFormatter.generate_html_report(report_data)
        assert "<html>" in html


class TestOutputFormat:
    """Tests for OutputFormat enum."""

    def test_json_value(self):
        assert OutputFormat.JSON == "json"

    def test_text_value(self):
        assert OutputFormat.TEXT == "text"

    def test_csv_value(self):
        assert OutputFormat.CSV == "csv"

    def test_html_value(self):
        assert OutputFormat.HTML == "html"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
