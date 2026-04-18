import { useMemo, useState } from 'react';
import { AlertTriangle, Filter, ArrowUpDown, Info } from 'lucide-react';
import type { AnalysisReport } from '../types';

interface Props {
  report: AnalysisReport | null;
}

const severityColor: Record<string, string> = {
  high: 'text-red-400 bg-red-500/10 border-red-500/30',
  medium: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30',
  low: 'text-green-400 bg-green-500/10 border-green-500/30',
};

const bandColor: Record<string, string> = {
  P0: 'bg-red-500',
  P1: 'bg-orange-500',
  P2: 'bg-yellow-500',
  P3: 'bg-blue-500',
};

export default function Dashboard({ report }: Props) {
  const [filterSmell, setFilterSmell] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('');
  const hasNeuro = !!report?.neuro_symbolic_analysis?.items?.length;
  const [sortKey, setSortKey] = useState<'confidence' | 'severity' | 'smell_type' | 'neuro'>('neuro');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  if (!report) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500 gap-3">
        <Info size={40} />
        <p>Run an analysis first to see results here.</p>
      </div>
    );
  }

  const smellTypes = useMemo(
    () => [...new Set(report.findings.map((f) => f.smell_type))],
    [report.findings],
  );

  const findings = useMemo(() => {
    const nsIndex = new Map<string, number>();
    for (const item of report.neuro_symbolic_analysis?.items || []) {
      const key = `${item.file}|${item.smell_type}`;
      const current = nsIndex.get(key) ?? 0;
      if (item.neuro_symbolic_confidence > current) {
        nsIndex.set(key, item.neuro_symbolic_confidence);
      }
    }

    let data = [...report.findings];
    if (filterSmell) data = data.filter((f) => f.smell_type === filterSmell);
    if (filterSeverity) data = data.filter((f) => f.severity === filterSeverity);
    data.sort((a, b) => {
      let v = 0;
      if (sortKey === 'confidence') v = a.confidence - b.confidence;
      else if (sortKey === 'neuro') {
        const na = nsIndex.get(`${a.file}|${a.smell_type}`) ?? 0;
        const nb = nsIndex.get(`${b.file}|${b.smell_type}`) ?? 0;
        v = na - nb;
      }
      else if (sortKey === 'severity') {
        const ord: Record<string, number> = { high: 3, medium: 2, low: 1 };
        v = (ord[a.severity] || 0) - (ord[b.severity] || 0);
      } else v = a.smell_type.localeCompare(b.smell_type);
      return sortDir === 'desc' ? -v : v;
    });
    return data.map((f) => ({
      ...f,
      neuro_score: nsIndex.get(`${f.file}|${f.smell_type}`) ?? null,
    }));
  }, [report.findings, report.neuro_symbolic_analysis, filterSmell, filterSeverity, sortKey, sortDir]);

  const toggleSort = (key: typeof sortKey) => {
    if (sortKey === key) setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('desc'); }
  };

  // Summary metrics
  const totalSmells = report.findings.length;
  const highCount = report.findings.filter((f) => f.severity === 'high').length;
  const filesAnalyzed = new Set(report.findings.map((f) => f.file)).size || 1;

  return (
    <div>
      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <SummaryCard label="Total Smells" value={totalSmells} color="text-brand-500" />
        <SummaryCard label="High Severity" value={highCount} color="text-red-400" />
        <SummaryCard label="Files Analyzed" value={filesAnalyzed} color="text-cyan-400" />
        <SummaryCard
          label="Avg Detection Confidence"
          value={
            totalSmells
              ? `${(report.findings.reduce((s, f) => s + f.confidence, 0) / totalSmells * 100).toFixed(0)}%`
              : '—'
          }
          color="text-emerald-400"
        />
      </div>

      {hasNeuro && report.neuro_symbolic_analysis && (
        <div className="mb-8 bg-surface-800 border border-gray-700/50 rounded-xl p-4 text-sm text-gray-300">
          Re-ranking is using neuro-symbolic confidence by default. Average neuro-symbolic confidence (calibrated):{' '}
          <span className="text-brand-500 font-semibold">
            {(report.neuro_symbolic_analysis.summary.average_confidence * 100).toFixed(1)}%
          </span>
        </div>
      )}

      {/* Prioritized findings band */}
      {report.prioritized_findings && report.prioritized_findings.length > 0 && (
        <section className="mb-8">
          <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
            <AlertTriangle size={18} className="text-yellow-400" /> Priority Ranking
          </h3>
          <div className="flex flex-wrap gap-2">
            {report.prioritized_findings.slice(0, 10).map((p, i) => (
              <span
                key={i}
                className={`${bandColor[p.priority_band] || 'bg-gray-600'} text-white text-xs font-bold px-3 py-1 rounded-full`}
              >
                {p.priority_band} · {p.smell_type} · {p.file.split(/[\\/]/).pop()}:{p.line_number}
              </span>
            ))}
          </div>
        </section>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-4 items-center">
        <Filter size={16} className="text-gray-400" />
        <select
          value={filterSmell}
          onChange={(e) => setFilterSmell(e.target.value)}
          className="bg-surface-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-300"
        >
          <option value="">All Smell Types</option>
          {smellTypes.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <select
          value={filterSeverity}
          onChange={(e) => setFilterSeverity(e.target.value)}
          className="bg-surface-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-300"
        >
          <option value="">All Severities</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      {/* Table */}
      <div className="bg-surface-800 rounded-xl border border-gray-700/50 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-700/50 text-gray-400 text-left">
              <Th label="Smell Type" sortKey="smell_type" current={sortKey} dir={sortDir} onClick={toggleSort} />
              <Th label="Severity" sortKey="severity" current={sortKey} dir={sortDir} onClick={toggleSort} />
              <th className="px-4 py-3">File</th>
              <th className="px-4 py-3">Line</th>
              {hasNeuro && <Th label="Neuro" sortKey="neuro" current={sortKey} dir={sortDir} onClick={toggleSort} />}
              <Th label="Confidence" sortKey="confidence" current={sortKey} dir={sortDir} onClick={toggleSort} />
              <th className="px-4 py-3">Suggested Fix</th>
            </tr>
          </thead>
          <tbody>
            {findings.map((f, i) => (
              <tr key={i} className="border-b border-gray-700/30 hover:bg-gray-700/20 transition-colors">
                <td className="px-4 py-3 font-mono">{f.smell_type}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded border text-xs font-semibold ${severityColor[f.severity] || ''}`}>
                    {f.severity}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-400">{f.file.split(/[\\/]/).pop()}</td>
                <td className="px-4 py-3 text-gray-400">{f.line_number}</td>
                {hasNeuro && (
                  <td className="px-4 py-3 text-gray-300 font-semibold">
                    {f.neuro_score == null ? '—' : `${(f.neuro_score * 100).toFixed(1)}%`}
                  </td>
                )}
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-16 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-brand-500 rounded-full"
                        style={{ width: `${(f.confidence * 100).toFixed(0)}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-400">{(f.confidence * 100).toFixed(0)}%</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-gray-300 max-w-xs truncate">{f.suggested_fix}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {findings.length === 0 && (
          <p className="p-6 text-center text-gray-500">No findings match current filters.</p>
        )}
      </div>

      {/* SHAP Explanations */}
      {report.ml_explanations && report.ml_explanations.length > 0 && (
        <section className="mt-8">
          <h3 className="text-lg font-semibold mb-3">SHAP Explanations</h3>
          <div className="space-y-3">
            {report.ml_explanations.map((ex, i) => (
              <div key={i} className="bg-surface-800 border border-gray-700/50 rounded-xl p-4">
                <div className="flex items-center gap-3 mb-2">
                  <span className="font-mono text-brand-400">{ex.smell_type}</span>
                  <span className="text-xs text-gray-400">
                    prob={ex.probability.toFixed(2)} · {ex.prediction_source}
                  </span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {ex.shap_explanation.slice(0, 5).map((s, j) => (
                    <span
                      key={j}
                      className={`text-xs px-2 py-1 rounded-full border ${
                        s.shap_value > 0
                          ? 'border-red-500/40 text-red-400 bg-red-500/10'
                          : 'border-green-500/40 text-green-400 bg-green-500/10'
                      }`}
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
      )}
    </div>
  );
}

/* ── Helpers ─────────────────────────────────────────────────────────── */
function SummaryCard({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div className="bg-surface-800 border border-gray-700/50 rounded-xl p-4">
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
    </div>
  );
}

function Th({
  label, sortKey, current, dir, onClick,
}: {
  label: string; sortKey: string; current: string; dir: string; onClick: (k: any) => void;
}) {
  return (
    <th
      className="px-4 py-3 cursor-pointer select-none hover:text-gray-200 transition-colors"
      onClick={() => onClick(sortKey)}
    >
      <span className="flex items-center gap-1">
        {label}
        <ArrowUpDown size={12} className={current === sortKey ? 'text-brand-500' : 'text-gray-600'} />
      </span>
    </th>
  );
}
