"""Report generation and output formatting."""
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import asdict, dataclass


@dataclass
class Issue:
    """Represents a detected code smell issue."""
    file: str
    line: int
    column: int = 0
    type: str = ""
    severity: str = "MEDIUM"
    confidence: float = 0.0
    explanation: str = ""
    description: str = ""
    recommendation: str = ""
    category: str = ""
    risk_score: float = 0.0
    fixed_code: str = ""
    cwe: str = ""
    owasp: str = ""
    code_snippet: str = ""
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []
        if not self.description:
            self.description = self.explanation


class ReportGenerator:
    """Generate analysis reports in multiple formats."""
    
    def __init__(self, project_name: str = "Code Smell Detector"):
        """
        Initialize report generator.
        
        Args:
            project_name: Name of the project being analyzed
        """
        self.project_name = project_name
        self.issues: List[Issue] = []
        self.scan_start_time = None
        self.scan_end_time = None
    
    def add_issue(self, issue: Issue):
        """Add an issue to the report."""
        self.issues.append(issue)
    
    def add_issues(self, issues: List[Dict[str, Any]]):
        """Add multiple issues from dictionaries."""
        for issue_dict in issues:
            issue = Issue(**issue_dict)
            self.add_issue(issue)
    
    def set_scan_time(self, start_time: datetime, end_time: datetime):
        """Set scan timing."""
        self.scan_start_time = start_time
        self.scan_end_time = end_time
    
    def generate_json(self) -> str:
        """Generate JSON report."""
        scan_duration_ms = 0
        if self.scan_start_time and self.scan_end_time:
            scan_duration_ms = int((self.scan_end_time - self.scan_start_time).total_seconds() * 1000)
        
        # Organize issues by file
        issues_by_file = {}
        for issue in self.issues:
            if issue.file not in issues_by_file:
                issues_by_file[issue.file] = []
            issues_by_file[issue.file].append(asdict(issue))
        
        # Calculate summary
        severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
        for issue in self.issues:
            severity = issue.severity
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        report = {
            "project": self.project_name,
            "timestamp": datetime.now().isoformat(),
            "scan_duration_ms": scan_duration_ms,
            "files_analyzed": list(issues_by_file.keys()),
            "total_issues": len(self.issues),
            "severity_summary": severity_counts,
            "issues_by_file": issues_by_file,
            "issues": [asdict(issue) for issue in sorted(
                self.issues,
                key=lambda x: (x.file, x.line)
            )],
        }
        
        return json.dumps(report, indent=2, default=str)
    
    def generate_text(self) -> str:
        """Generate human-readable text report."""
        lines = []
        lines.append("=" * 80)
        lines.append(f"Code Smell Detection Report - {self.project_name}")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().isoformat()}")
        lines.append(f"Total Issues: {len(self.issues)}")
        lines.append("")
        
        # Summary by severity
        severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for issue in self.issues:
            if issue.severity in severity_counts:
                severity_counts[issue.severity] += 1
        
        lines.append("Severity Summary:")
        lines.append(f"  HIGH:   {severity_counts['HIGH']:3d}")
        lines.append(f"  MEDIUM: {severity_counts['MEDIUM']:3d}")
        lines.append(f"  LOW:    {severity_counts['LOW']:3d}")
        lines.append("")
        
        # Group by file
        issues_by_file = {}
        for issue in self.issues:
            if issue.file not in issues_by_file:
                issues_by_file[issue.file] = []
            issues_by_file[issue.file].append(issue)
        
        # Report per file
        for filepath in sorted(issues_by_file.keys()):
            file_issues = issues_by_file[filepath]
            lines.append("-" * 80)
            lines.append(f"File: {filepath} ({len(file_issues)} issues)")
            lines.append("-" * 80)
            
            for issue in sorted(file_issues, key=lambda x: x.line):
                lines.append(f"  [{issue.severity}] Line {issue.line}: {issue.type}")
                lines.append(f"    Confidence: {issue.confidence:.2%}")
                lines.append(f"    {issue.explanation}")
                if issue.category:
                    lines.append(f"    Category: {issue.category}")
                if issue.risk_score:
                    lines.append(f"    Risk Score: {issue.risk_score:.3f}")
                if issue.recommendation:
                    lines.append(f"    Recommendation: {issue.recommendation}")
                if issue.cwe:
                    lines.append(f"    CWE: {issue.cwe}")
                if issue.code_snippet:
                    lines.append(f"    Code: {issue.code_snippet[:60]}")
                if issue.suggestions:
                    lines.append(f"    Fix: {issue.suggestions[0]}")
                if issue.fixed_code:
                    lines.append(f"    Fixed Code: {issue.fixed_code[:60]}")
                lines.append("")
        
        lines.append("=" * 80)
        return "\n".join(lines)
    
    def generate_csv(self) -> str:
        """Generate CSV report."""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "File", "Line", "Column", "Type", "Severity", "Confidence",
            "Category", "RiskScore", "Recommendation", "CWE", "OWASP", "Explanation", "FixedCode"
        ])
        
        # Rows
        for issue in self.issues:
            writer.writerow([
                issue.file,
                issue.line,
                issue.column,
                issue.type,
                issue.severity,
                f"{issue.confidence:.2%}",
                issue.category,
                f"{issue.risk_score:.4f}",
                issue.recommendation,
                issue.cwe,
                issue.owasp,
                issue.explanation,
                issue.fixed_code,
            ])
        
        return output.getvalue()
    
    def save(self, filepath: str, format: str = "json"):
        """
        Save report to file.
        
        Args:
            filepath: Path to save report
            format: Report format (json, text, csv)
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            content = self.generate_json()
        elif format == "text":
            content = self.generate_text()
        elif format == "csv":
            content = self.generate_csv()
        else:
            raise ValueError(f"Unknown format: {format}")
        
        with open(filepath, 'w') as f:
            f.write(content)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get report summary."""
        severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
        type_counts = {}
        
        for issue in self.issues:
            if issue.severity in severity_counts:
                severity_counts[issue.severity] += 1
            
            if issue.type not in type_counts:
                type_counts[issue.type] = 0
            type_counts[issue.type] += 1
        
        return {
            "total_issues": len(self.issues),
            "severity_summary": severity_counts,
            "type_summary": type_counts,
            "files_analyzed": len(set(i.file for i in self.issues)),
        }


if __name__ == "__main__":
    # Example usage
    generator = ReportGenerator("Example Project")
    
    issue1 = Issue(
        file="app.py",
        line=42,
        type="hardcoded_secrets",
        severity="HIGH",
        confidence=0.94,
        explanation="Hardcoded API key detected",
        cwe="CWE-798",
        owasp="A02:2021",
        code_snippet="api_key = 'sk_live_...'",
        suggestions=["Use environment variables", "Rotate the key"]
    )
    
    generator.add_issue(issue1)
    
    print(generator.generate_json())
