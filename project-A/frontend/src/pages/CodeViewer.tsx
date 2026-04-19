import { useMemo, useState } from 'react';
import Editor from '@monaco-editor/react';
import { Info } from 'lucide-react';
import type { AnalysisReport } from '../types';

interface Props {
  report: AnalysisReport | null;
}

export default function CodeViewer({ report }: Props) {
  if (!report) {
    return <Empty />;
  }

  const files = useMemo(() => {
    const s = report.sources || {};
    return Object.keys(s).length > 0
      ? Object.entries(s).map(([path, code]) => ({ path, code }))
      : [];
  }, [report.sources]);

  const [selected, setSelected] = useState(files[0]?.path || '');
  const currentCode = useMemo(() => files.find((f) => f.path === selected)?.code || '', [files, selected]);

  // Gather line decorations for this file's smells
  const decorations = useMemo(() => {
    if (!report.findings) return [];
    return report.findings
      .filter((f) => f.file === selected || selected.endsWith(f.file))
      .map((f) => ({
        range: { startLineNumber: f.line_number, startColumn: 1, endLineNumber: f.line_number, endColumn: 1 },
        options: {
          isWholeLine: true,
          className: 'bg-red-500/10',
          glyphMarginClassName: 'bg-red-500 rounded-full',
          hoverMessage: { value: `**${f.smell_type}** (${f.severity}) — ${f.suggested_fix}` },
        },
      }));
  }, [report.findings, selected]);

  if (files.length === 0) {
    return (
      <div className="text-gray-500 flex flex-col items-center justify-center h-full gap-3">
        <Info size={40} />
        <p>No source files available. Re-run analysis to view code.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 mb-4">
        <label className="text-sm text-gray-400">File:</label>
        <select
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          className="bg-surface-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-300 max-w-md"
        >
          {files.map((f) => (
            <option key={f.path} value={f.path}>
              {f.path}
            </option>
          ))}
        </select>

        {/* Legend */}
        <span className="ml-auto text-xs text-gray-500 flex items-center gap-1">
          <span className="inline-block w-3 h-3 rounded-full bg-red-500/40" /> = smell detected on line
        </span>
      </div>

      <div className="flex-1 rounded-xl overflow-hidden border border-gray-700/50">
        <Editor
          height="100%"
          language="python"
          theme="light"
          value={currentCode}
          options={{
            readOnly: true,
            minimap: { enabled: true },
            fontSize: 13,
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            glyphMargin: true,
          }}
          onMount={(editor) => {
            editor.createDecorationsCollection(decorations as any);
          }}
        />
      </div>
    </div>
  );
}

function Empty() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-gray-500 gap-3">
      <Info size={40} />
      <p>Run an analysis first to view code.</p>
    </div>
  );
}
