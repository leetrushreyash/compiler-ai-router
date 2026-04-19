import sys

file_path = r'c:\Users\SHREYASH SHARMA\compiler\project-A\frontend\src\pages\Dashboard.tsx'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_block = '''      {/* SHAP Explanations */}
      {report.ml_explanations && report.ml_explanations.length > 0 && (
        <section className="mt-8">
          <h3 className="text-lg font-semibold mb-3">SHAP Explanations</h3>
          <div className="space-y-3">
            {report.ml_explanations.map((ex, i) => (
              <div key={i} className="bg-surface-800 border border-gray-700/50 rounded-xl p-4">
                <div className="flex items-center gap-3 mb-2">
                  <span className="font-mono text-brand-400">{ex.smell_type}</span>
                  <span className="text-xs text-gray-400">
                    prob={ex.probability.toFixed(2)} Â· {ex.prediction_source}
                  </span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {ex.shap_explanation.slice(0, 5).map((s, j) => (
                    <span
                      key={j}
                      className={	ext-xs px-2 py-1 rounded-full border }
                    >
                      {s.feature}: {s.shap_value > 0 ? '+' : ''}{s.shap_value.toFixed(4)}
                    </span>
                  ))}
                </div>
                <p className="text-xs text-gray-400 mt-2">{ex.explanation_text}</p>
              </div>
            ))}
          </div>
        </section>
      )}'''

new_block = '''      {/* Explainable AI / SHAP Explanations */}
      {report.ml_explanations && report.ml_explanations.length > 0 && (
        <section className="mt-10 mb-8 border-t border-gray-400 pt-8">
          <h3 className="text-xl font-bold mb-1 text-gray-900 flex items-center gap-2">
            <Info className="text-brand-500" />
            AI Reasoning Details
          </h3>
          <p className="text-sm text-gray-500 mb-6">
            Our ML model explicitly explains which parts of your code triggered this flagged smell.
          </p>
          <div className="space-y-4">
            {report.ml_explanations.map((ex, i) => {
              const formatFeature = (f: string) => f.split('_').map((w: string) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
              
              return (
                <div key={i} className="bg-surface-800 border border-gray-400 shadow-sm rounded-xl p-5">
                  <div className="flex flex-wrap items-center justify-between gap-3 mb-5 border-b border-gray-400 pb-4">
                    <div className="flex items-center gap-3">
                      <span className="font-mono bg-brand-50 text-brand-800 px-3 py-1 rounded-lg text-sm border border-brand-300 font-bold shadow-sm">
                        {ex.smell_type}
                      </span>
                      <span className="text-sm text-gray-700 font-semibold bg-gray-200 px-3 py-1 rounded-lg border border-gray-400">
                        Confidence: {(ex.probability * 100).toFixed(0)}%
                      </span>
                    </div>
                    <span className="text-xs bg-gray-200 text-gray-600 px-3 py-1 rounded-full font-semibold border border-gray-400 uppercase tracking-wide">
                      Source: {ex.prediction_source === 'ml' ? 'Machine Learning' : ex.prediction_source}
                    </span>
                  </div>
                  
                  <h4 className="text-xs font-bold text-gray-600 uppercase tracking-wider mb-3">
                    Key Factors Impacting this Decision
                  </h4>
                  <div className="flex flex-col gap-2 mb-5">
                    {ex.shap_explanation.slice(0, 5).map((s, j) => {
                      const impact = (Math.abs(s.shap_value) * 100).toFixed(1);
                      const isPositive = s.shap_value > 0;
                      
                      return (
                        <div key={j} className="flex flex-col sm:flex-row sm:items-center justify-between border border-gray-300 bg-surface-900 rounded-lg px-4 py-2 gap-2">
                          <span className="text-sm text-gray-900 font-medium">{formatFeature(s.feature)}</span>
                          <span className={"text-xs font-bold px-2 py-1 rounded-md border " + (
                            isPositive
                              ? "text-red-700 bg-red-100 border-red-300"
                              : "text-green-700 bg-green-100 border-green-300"
                          )}>
                            {isPositive ? 'Increased' : 'Decreased'} likelihood by {impact}%
                          </span>
                        </div>
                      );
                    })}
                  </div>
                  
                  <div className="bg-brand-50 rounded-lg p-4 border border-brand-200 flex gap-3 items-start">
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

if old_block in content:
    new_content = content.replace(old_block, new_block)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Success")
else:
    print("Could not find the block to replace")
