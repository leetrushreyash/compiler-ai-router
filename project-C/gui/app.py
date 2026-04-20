import os
import sys
from flask import Flask, render_template, request, jsonify

# Add the parent directory and codes directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'codes')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'project-A')))

from unified_analyzer import analyze_file
from backend.energy import EnergyCollector

app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    
    # Normalize input to a batch format
    batch = data.get('batch', [])
    if 'code' in data and data['code'].strip():
        batch = [{'filename': 'main.cpp', 'code': data['code']}]
        
    if not batch:
        return jsonify({"error": "No code provided"}), 400

    batch_results = []
    has_critical = False
    
    for item in batch:
        code = item.get('code', '')
        filename = item.get('filename', 'temp.cpp')
        
        if not code.strip():
            continue
            
        # Write to temporary file
        temp_file = "temp_analysis_" + os.path.basename(filename)
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(code)
                
            ast_results = analyze_file(temp_file)
            
            if "error" in ast_results:
                return jsonify({"error": ast_results["error"]}), 500
                
            # Check for criticals
            if any(f.get("overall_severity") in ["High", "Critical"] for f in ast_results.get("functions", [])):
                has_critical = True
                
            batch_results.append({
                "filename": filename,
                "ast_results": ast_results
            })
            
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    return jsonify({
        "batch_results": batch_results,
        "is_smelly": has_critical
    })

@app.route('/api/cross-project/energy', methods=['POST'])
def get_energy_from_project_a():
    data = request.json or {}
    code = data.get("code", "")
    filename = data.get("filename", "inline_input.cpp")
    
    if not code.strip():
        return jsonify({"error": "Code input is empty."}), 400

    temp_file = "temp_energy_" + os.path.basename(filename)
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(code)
            
        collector = EnergyCollector()
        collector.start()
        collector.begin_phase("parsing")
        
        ast_results = analyze_file(temp_file)
        
        collector.end_phase()
        energy_report = collector.stop()
        energy_data = energy_report.to_dict()
        
        n_smells = 0
        if "functions" in ast_results:
            for fn in ast_results["functions"]:
                if fn.get("security", {}).get("has_vulnerabilities"):
                    n_smells += len(fn["security"].get("issues", []))
                if fn.get("code_smell", {}).get("is_smelly"):
                    n_smells += 1
                    
        total_e = energy_data.get("estimated_energy_joules", 0.0)
        energy_data["energy_per_file"] = total_e
        energy_data["energy_per_smell"] = round(total_e / max(n_smells, 1), 6)
        
        return jsonify({"energy": energy_data})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

if __name__ == '__main__':
    print("Starting Advanced AST Flask Server at http://127.0.0.1:5001")
    app.run(debug=True, port=5001)
