"""Quick script to pretty-print findings from test_results.json."""
import json

d = json.load(open("test_results.json"))
findings = d["all_findings"]

print("=" * 90)
print(f"  CODE SMELL FINDINGS — {len(findings)} total across {len(d['findings_by_file'])} files")
print("=" * 90)

for i, f in enumerate(findings[:25], 1):
    print(json.dumps({
        "#": i,
        "source_file": f["source_file"],
        "line_number": f["line_number"],
        "source_code": f["source_code"],
        "code_smell": f["code_smell"],
        "severity": f["severity"],
        "confidence": f["confidence"],
        "cwe": f["cwe"],
        "description": f["description"],
    }, indent=2))
    print()

if len(findings) > 25:
    print(f"... showing 25 of {len(findings)} total findings")
    print(f"    Full report: test_results.json")
