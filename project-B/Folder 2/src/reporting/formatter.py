"""Output formatting utilities."""
from typing import List, Dict, Any
from enum import Enum


class OutputFormat(str, Enum):
    """Output format options."""
    JSON = "json"
    TEXT = "text"
    CSV = "csv"
    HTML = "html"
    SARIF = "sarif"


class OutputFormatter:
    """Format analysis results for different output types."""
    
    @staticmethod
    def format_issue(issue: Dict[str, Any], format: str = "text") -> str:
        """
        Format a single issue.
        
        Args:
            issue: Issue dictionary
            format: Output format
            
        Returns:
            Formatted issue string
        """
        if format == "text":
            return OutputFormatter._format_issue_text(issue)
        elif format == "json":
            import json
            return json.dumps(issue, indent=2)
        elif format == "csv":
            return OutputFormatter._format_issue_csv(issue)
        else:
            return str(issue)
    
    @staticmethod
    def _format_issue_text(issue: Dict[str, Any]) -> str:
        """Format issue as text."""
        lines = []
        lines.append(f"[{issue.get('severity', 'MEDIUM')}] {issue.get('file', '?')}:{issue.get('line', '?')}")
        lines.append(f"  Type: {issue.get('type', 'unknown')}")
        lines.append(f"  Explanation: {issue.get('explanation', '')}")
        if issue.get('confidence'):
            lines.append(f"  Confidence: {issue['confidence']:.1%}")
        if issue.get('cwe'):
            lines.append(f"  CWE: {issue['cwe']}")
        return "\n".join(lines)
    
    @staticmethod
    def _format_issue_csv(issue: Dict[str, Any]) -> str:
        """Format issue as CSV row."""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            issue.get('file', ''),
            issue.get('line', ''),
            issue.get('type', ''),
            issue.get('severity', ''),
            issue.get('confidence', ''),
            issue.get('explanation', ''),
        ])
        return output.getvalue().strip()
    
    @staticmethod
    def format_table(issues: List[Dict[str, Any]]) -> str:
        """
        Format issues as ASCII table.
        
        Args:
            issues: List of issues
            
        Returns:
            Formatted table string
        """
        if not issues:
            return "No issues found."
        
        lines = []
        lines.append("")
        lines.append("┌─────────────────────────────────────────────────────────────────────────────┐")
        lines.append("│ Code Smell Detection Results                                                │")
        lines.append("├──────────┬──────────────────────────────┬──────────┬─────────┬──────────────┤")
        lines.append("│ Severity │ File:Line                    │ Type     │ Conf.   │ Description  │")
        lines.append("├──────────┼──────────────────────────────┼──────────┼─────────┼──────────────┤")
        
        for issue in issues:
            severity = issue.get('severity', 'MEDIUM')[:3]
            file_line = f"{issue.get('file', '?')}:{issue.get('line', '?')}"[:28]
            smell_type = issue.get('type', 'unknown')[:8]
            conf = f"{issue.get('confidence', 0):.0%}" if issue.get('confidence') else "N/A"
            description = issue.get('explanation', '')[:12]
            
            lines.append(
                f"│ {severity:<8} │ {file_line:<28} │ {smell_type:<8} │ {conf:>5} │ {description:<12} │"
            )
        
        lines.append("└──────────┴──────────────────────────────┴──────────┴─────────┴──────────────┘")
        
        return "\n".join(lines)
    
    @staticmethod
    def generate_html_report(report_data: Dict[str, Any]) -> str:
        """Generate HTML report."""
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Code Smell Detection Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        .summary { background: #f5f5f5; padding: 10px; margin: 20px 0; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background: #4CAF50; color: white; }
        tr:nth-child(even) { background: #f9f9f9; }
        .HIGH { color: #d32f2f; font-weight: bold; }
        .MEDIUM { color: #f57c00; font-weight: bold; }
        .LOW { color: #388e3c; }
    </style>
</head>
<body>
    <h1>Code Smell Detection Report</h1>
"""
        
        # Add summary
        summary = report_data.get('summary', {})
        html += f"""
    <div class="summary">
        <h2>Summary</h2>
        <p>Total Issues: <strong>{summary.get('total_issues', 0)}</strong></p>
        <p>HIGH: {summary.get('severity_summary', {}).get('HIGH', 0)} | 
           MEDIUM: {summary.get('severity_summary', {}).get('MEDIUM', 0)} | 
           LOW: {summary.get('severity_summary', {}).get('LOW', 0)}</p>
    </div>
"""
        
        # Add issues table
        html += """
    <table>
        <tr>
            <th>File</th>
            <th>Line</th>
            <th>Type</th>
            <th>Severity</th>
            <th>Confidence</th>
            <th>Explanation</th>
        </tr>
"""
        
        for issue in report_data.get('issues', []):
            severity = issue.get('severity', 'MEDIUM')
            html += f"""
        <tr>
            <td>{issue.get('file', '')}</td>
            <td>{issue.get('line', '')}</td>
            <td>{issue.get('type', '')}</td>
            <td class="{severity}">{severity}</td>
            <td>{issue.get('confidence', 0):.0%}</td>
            <td>{issue.get('explanation', '')}</td>
        </tr>
"""
        
        html += """
    </table>
</body>
</html>
"""
        return html
