import os
import sys
from flask import Flask, render_template, request, jsonify

# Add the parent directory and codes directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'codes')))
from unified_analyzer import analyze_file

app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    code = data.get('code', '')

    if not code.strip():
        return jsonify({"error": "No code provided"}), 400

    # Write code to a temporary file
    temp_file = "temp_analysis.cpp"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(code)

        # Call the cutting-edge Unified AST Analyzer!
        ast_results = analyze_file(temp_file)

        if "error" in ast_results:
            return jsonify({"error": ast_results["error"]}), 500
            
        # Determine global status
        has_critical = any(f.get("overall_severity") in ["High", "Critical"] for f in ast_results.get("functions", []))

        return jsonify({
            "ast_results": ast_results,
            "is_smelly": has_critical
        })
        
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

if __name__ == '__main__':
    print("Starting Advanced AST Flask Server at http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
