import { useState, useMemo } from 'react';
import Editor from '@monaco-editor/react';
import { Info, Wrench } from 'lucide-react';
import type { AnalysisReport } from '../types';

interface Props {
  report: AnalysisReport | null;
}

export default function Refactoring({ report }: Props) {
  if (!report?.refactorings || report.refactorings.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500 gap-3">
        <Info size={40} />
        <p>No refactoring patches available. Run analysis with refactoring enabled.</p>
      </div>
    );
  }

  const [selected, setSelected] = useState(0);
  const r = report.refactorings[selected];

  return (
    <div className="flex flex-col h-full">
      <h2 className="text-2xl font-bold mb-1 flex items-center gap-2">
        <Wrench size={22} className="text-orange-400" /> Refactoring Preview
      </h2>
      <p className="text-gray-400 text-sm mb-4">
        {report.refactorings.length} patch(es) generated · Before & After diff view
      </p>

      {/* Patch selector */}
      <div className="flex flex-wrap gap-2 mb-4">
        {report.refactorings.map((ref, i) => (
          <button
            key={i}
            onClick={() => setSelected(i)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors
              ${selected === i
                ? 'border-brand-300 bg-brand-50 text-brand-700 shadow-sm'
                 : 'border-gray-600 bg-surface-800 text-gray-400 hover:bg-gray-700 hover:text-gray-100 hover:border-gray-500'}`}
          >
            {ref.smell_type} · {ref.file.split(/[\\/]/).pop()}
          </button>
        ))}
      </div>

      {/* Patch description */}
      <div className="bg-surface-800 border border-gray-700/50 rounded-xl p-4 mb-4">
        <p className="text-sm text-gray-200 font-medium">{r.description}</p>
        <p className="text-xs text-gray-500 mt-1">
          {r.file} · Lines {r.line_start}–{r.line_end}
        </p>
      </div>

      {/* Side-by-side editors */}
      <div className="flex-1 grid grid-cols-2 gap-4 min-h-0">
        <div className="flex flex-col min-h-0">
          <span className="text-xs text-red-400 font-semibold mb-1 px-1">BEFORE (Original)</span>
          <div className="flex-1 rounded-xl overflow-hidden border border-red-500/30">
            <Editor
              height="100%"
              language="python"
              theme="vs-dark"
              value={r.original}
              options={{ readOnly: true, minimap: { enabled: false }, fontSize: 12, lineNumbers: 'on', scrollBeyondLastLine: false }}
            />
          </div>
        </div>
        <div className="flex flex-col min-h-0">
          <span className="text-xs text-green-400 font-semibold mb-1 px-1">AFTER (Refactored)</span>
          <div className="flex-1 rounded-xl overflow-hidden border border-green-500/30">
            <Editor
              height="100%"
              language="python"
              theme="vs-dark"
              value={r.refactored}
              options={{ readOnly: true, minimap: { enabled: false }, fontSize: 12, lineNumbers: 'on', scrollBeyondLastLine: false }}
            />
          </div>
        </div>
      </div>

      {/* Diff output */}
      <details className="mt-4">
        <summary className="text-sm text-gray-400 cursor-pointer hover:text-white transition-colors">
          View Unified Diff
        </summary>
        <pre className="mt-2 bg-surface-800 border border-gray-700/50 rounded-xl p-4 text-xs font-mono text-gray-300 overflow-auto max-h-60 whitespace-pre-wrap">
          {r.diff}
        </pre>
      </details>
    </div>
  );
}

