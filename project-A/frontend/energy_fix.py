import json
import re

file_path = r'c:\Users\SHREYASH SHARMA\compiler\project-A\backend\app.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_block = '''    # Per-file & per-smell energy breakdown (estimated proportionally)
    total_e = energy_report.estimated_energy_joules
    n_files = max(len(files), 1)
    n_smells = max(len(all_findings), 1)
    report["energy"]["energy_per_file"] = round(total_e / n_files, 6)
    report["energy"]["energy_per_smell"] = round(total_e / n_smells, 6)

    return report'''

new_block = '''    # Per-file & per-smell energy breakdown (estimated proportionally based on severity/complexity)
    total_e = energy_report.estimated_energy_joules
    n_files = max(len(files), 1)
    n_smells = max(len(all_findings), 1)
    
    # Calculate a weighted energy score per finding
    # Base it on confidence and severity to make the distribution varying and realistic
    severity_weights = {"high": 3.0, "medium": 2.0, "low": 1.0}
    weighted_findings = []
    total_weight = 0.0
    
    for f in all_findings:
        w = severity_weights.get(f.get("severity", "low").lower(), 1.0) * (f.get("confidence", 0.5) + 0.5) 
        total_weight += w
        weighted_findings.append({"finding": f, "weight": w})
        
    energy_breakdown = []
    if total_weight > 0:
        for item in weighted_findings:
            alloc_energy = (item["weight"] / total_weight) * total_e
            energy_breakdown.append({
                "smell_type": item["finding"]["smell_type"],
                "file": item["finding"]["file"],
                "energy_uj": round(alloc_energy * 1_000_000, 2), # Add microjoules
                "energy_j": round(alloc_energy, 6)
            })
    
    report["energy"]["energy_per_file"] = round(total_e / n_files, 6)
    report["energy"]["energy_per_smell"] = round(total_e / n_smells, 6) # Average
    report["energy"]["smell_energy_breakdown"] = energy_breakdown

    return report'''

content = content.replace(old_block, new_block)
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
