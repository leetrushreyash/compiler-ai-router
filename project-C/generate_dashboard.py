import os
import sys
import json
import subprocess

def generate_dashboard(target_file):
    print(f"Generating telemetry for {target_file}...")
    
    analyzer_path = os.path.join(os.path.dirname(__file__), 'codes', 'unified_analyzer.py')
    
    try:
        # Run the analyzer
        result = subprocess.run(['python', analyzer_path, target_file], capture_output=True, text=True, check=True)
        raw_output = result.stdout
        
        # Extract the JSON payload
        start_idx = raw_output.find('{')
        if start_idx == -1:
            print("Failed to find JSON data inside output!")
            return
            
        json_str = raw_output[start_idx:]
        data = json.loads(json_str)
        
    except Exception as e:
        print(f"Failed to generate telemetry metrics: {e}")
        return

    # Prepare data arrays for Chart.js
    func_names = []
    complexity = []
    max_depth = []
    ast_nodes = []
    
    for f in data.get('functions', []):
        func_names.append(f['name'])
        metrics = f.get('ast_metrics', {})
        complexity.append(metrics.get('cyclomatic_complexity', 1))
        max_depth.append(metrics.get('max_depth', 0))
        ast_nodes.append(metrics.get('total_ast_nodes', 0))

    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AST Analysis Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg-light: #f8fafc;
                --panel-bg: #ffffff;
                --text-dark: #0f172a;
                --text-muted: #64748b;
                --accent: #4f46e5;
                --success: #10b981;
                --danger: #ef4444;
                --border-light: #e2e8f0;
            }}
            body {{
                font-family: 'Inter', sans-serif;
                background-color: var(--bg-light);
                color: var(--text-dark);
                margin: 0;
                padding: 40px;
                display: flex;
                flex-direction: column;
                align-items: center;
            }}
            h1 {{
                font-weight: 800;
                font-size: 2.5rem;
                margin-bottom: 5px;
                color: var(--text-dark);
                text-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }}
            .subtitle {{
                color: var(--text-muted);
                margin-bottom: 40px;
                font-weight: 400;
            }}
            .dashboard-grid {{
                display: grid;
                grid-template-columns: 1fr;
                gap: 30px;
                width: 100%;
                max-width: 900px;
            }}
            .card {{
                background-color: var(--panel-bg);
                border-radius: 12px;
                padding: 25px;
                box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
                border: 1px solid var(--border-light);
            }}
            .card h2 {{
                margin-top: 0;
                font-size: 1.2rem;
                color: var(--text-dark);
                font-weight: 600;
                border-bottom: 1px solid var(--border-light);
                padding-bottom: 15px;
                margin-bottom: 20px;
            }}
            .chart-container {{
                position: relative;
                height: 400px;
                width: 100%;
            }}
        </style>
    </head>
    <body>
        <h1>Compiler Toolchain Analytics</h1>
        <div class="subtitle">Analyzing cyclomatic complexity flows for {target_file}</div>

        <div class="dashboard-grid">
            <!-- Bar Chart Card -->
            <div class="card">
                <h2>Cyclomatic Complexity Ranking</h2>
                <div class="chart-container">
                    <canvas id="barChart"></canvas>
                </div>
            </div>

            <!-- Scatter Chart Card -->
            <div class="card">
                <h2>Complexity vs AST Bloat</h2>
                <div class="chart-container">
                    <canvas id="scatterChart"></canvas>
                </div>
            </div>
        </div>

        <script>
            // Data bindings dynamically populated via Python!
            const labels = {json.dumps(func_names)};
            const complexityData = {json.dumps(complexity)};
            const astNodesData = {json.dumps(ast_nodes)};

            // Global Defaults for Chart.js Light Mode
            Chart.defaults.color = '#64748b';
            Chart.defaults.borderColor = '#e2e8f0';

            // 1. Setup Bar Chart
            new Chart(document.getElementById('barChart'), {{
                type: 'bar',
                data: {{
                    labels: labels,
                    datasets: [{{
                        label: 'Cyclomatic Complexity',
                        data: complexityData,
                        backgroundColor: 'rgba(79, 70, 229, 0.8)',
                        borderColor: '#4f46e5',
                        borderWidth: 1,
                        borderRadius: 4
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{ legend: {{ display: false }} }},
                    scales: {{
                        y: {{ beginAtZero: true, suggestedMax: 10 }}
                    }}
                }}
            }});

            // 2. Setup Scatter Chart
            const scatterData = labels.map((label, i) => ({{
                x: astNodesData[i],
                y: complexityData[i]
            }}));
            
            new Chart(document.getElementById('scatterChart'), {{
                type: 'scatter',
                data: {{
                    datasets: [{{
                        label: 'Functions',
                        data: scatterData,
                        backgroundColor: '#10b981',
                        pointRadius: 6,
                        pointHoverRadius: 8
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{ title: {{ display: true, text: 'Total AST Nodes (Bloat)' }} }},
                        y: {{ title: {{ display: true, text: 'Cyclomatic Complexity' }} }}
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """

    output_path = os.path.join(os.path.dirname(__file__), 'ast_report.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_template)
        
    print(f"Gorgeous AST metrics dashboard generated successfully!")
    print(f"Open: {output_path} in your web browser.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python generate_dashboard.py <cpp_file>")
    else:
        generate_dashboard(sys.argv[1])
