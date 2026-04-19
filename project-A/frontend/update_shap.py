import re

file_path = r'c:\Users\SHREYASH SHARMA\compiler\project-A\frontend\src\pages\Dashboard.tsx'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

new_block = '''      {/* SHAP Explanations */}
      {report.ml_explanations && report.ml_explanations.length > 0 && (
        <section className="mt-10 mb-8 border-t border-gray-300 pt-8">
          <h3 className="text-xl font-bold mb-1 text-gray-900 flex items-center gap-2">
            <Info className="text-brand-500" />
            AI Reasoning Details
          </h3>
          <p className="text-sm text-gray-500 mb-6">
            Our ML model explains exactly which parts of your code triggered these specific code smells.
          </p>
          <div className="space-y-4">
            {report.ml_explanations.map((ex, i) => {
              // Convert features like "ast_node_count" to "Ast Node Count"
              const formatFeature = (f: string) => f.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
              
              return (
                <div key={i} className="bg-surface-800 border border-gray-300 shadow-sm rounded-xl p-5">
                  
                  {/* Header row */}
                  <div className="flex flex-wrap items-center justify-between gap-3 mb-5 border-b border-gray-300/30 pb-4">
                    <div className="flex items-center gap-3">
                      <span className="font-mono bg-brand-50 text-brand-800 px-3 py-1 rounded-lg text-sm border border-brand-200 font-bold shadow-sm">
                        {ex.smell_type}
                      </span>
                      <span className="text-sm text-gray-600 font-semibold bg-gray-100 px-3 py-1 rounded-lg border border-gray-200">
                        {(ex.probability * 100).toFixed(0)}% Confidence
                      </span>
                    </div>
                    <span className="text-xs bg-gray-100 text-gray-500 px-3 py-1 rounded-full font-semibold border border-gray-200 uppercase tracking-wide">
                      Source: {ex.prediction_source === 'ml' ? 'Machine Learning' : ex.prediction_source}
                    </span>
                  </div>
                  
                  {/* SHAP specific attributes breakdown */}
                  <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">
                    Key Factors Impacting this Decision
                  </h4>
                  <div className="flex flex-col gap-2 mb-5">
                    {ex.shap_explanation.slice(0, 5).map((s, j) => {
                      const impact = (Math.abs(s.shap_value) * 100).toFixed(1);
                      const isPositive = s.shap_value > 0;
                      
                      return (
                        <div key={j} className="flex flex-col sm:flex-row sm:items-center justify-between border border-gray-200 bg-surface-900 rounded-lg px-4 py-2 gap-2">
                          <span className="text-sm text-gray-800 font-medium">{formatFeature(s.feature)}</span>
                          <span className={"text-xs font-bold px-2 py-1 rounded-md border " + (
                            isPositive
                              ? "text-red-700 bg-red-50 border-red-200"
                              : "text-green-700 bg-green-50 border-green-200"
                          )}>
                            {isPositive ? 'Increased' : 'Decreased'} likelihood by {impact}%
                          </span>
                        </div>
                      );
                    })}
                  </div>
                  
                  {/* Human-readable explanation text */}
                  <div className="bg-brand-50 rounded-lg p-3 border border-brand-100 flex gap-3 items-start">
                    <p className="text-sm text-brand-900 leading-relaxed font-medium">
                      {ex.explanation_text}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}'''

import re
match = re.search(r"\{/\* SHAP Explanations \*/\}.*?\}\s*\)\s*\}", content, flags=re.DOTALL)
if match:
    new_content = content[:match.start()] + new_block + content[match.end():]
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Replaced successfully')
else:
    print('Failed to match')
