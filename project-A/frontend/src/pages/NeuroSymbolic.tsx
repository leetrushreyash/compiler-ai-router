import { useMemo, useState } from 'react';
import { Fragment } from 'react';
import { Cpu, Info } from 'lucide-react';
import type { AnalysisReport } from '../types';

interface Props {
  report: AnalysisReport | null;
}

const bandColor: Record<string, string> = {
  very_high: 'bg-red-500/20 text-red-400 border-red-500/30',
  high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  moderate: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  low: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
};

export default function NeuroSymbolic({ report }: Props) {
  const [band, setBand] = useState('');

  if (!report?.neuro_symbolic_analysis) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500 gap-3">
        <Info size={40} />
        <p>Run an analysis first to view neuro-symbolic fusion results.</p>
      </div>
    );
  }

  const ns = report.neuro_symbolic_analysis;

  const rows = useMemo(() => {
    let items = [...ns.items];
    if (band) items = items.filter((i) => i.confidence_band === band);
    return items;
  }, [ns.items, band]);

  return (
    <div>
      <h2 className="text-2xl font-bold mb-1 flex items-center gap-2">
        <Cpu size={22} className="text-brand-500" /> Neuro-Symbolic Fusion
      </h2>
      <p className="text-gray-400 text-sm mb-6">
        Method: {ns.method} · Fuses symbolic rules, ML confidence, and correlation context.
      </p>

      <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-8">
        <Card label="Findings" value={ns.summary.count} color="text-brand-500" />
        <Card label="Very High" value={ns.summary.very_high} color="text-red-400" />
        <Card label="High" value={ns.summary.high} color="text-orange-400" />
        <Card label="Moderate" value={ns.summary.moderate} color="text-yellow-400" />
        <Card label="Low" value={ns.summary.low} color="text-blue-400" />
        <Card label="Avg Neuro-Symbolic Confidence (Calibrated)" value={`${(ns.summary.average_confidence * 100).toFixed(1)}%`} color="text-emerald-400" />
      </div>

      <div className="flex items-center gap-3 mb-4">
        <label className="text-sm text-gray-400">Confidence Band</label>
        <select
          value={band}
          onChange={(e) => setBand(e.target.value)}
          className="bg-surface-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-300"
        >
          <option value="">All</option>
          <option value="very_high">very_high</option>
          <option value="high">high</option>
          <option value="moderate">moderate</option>
          <option value="low">low</option>
        </select>
      </div>

      <div className="bg-surface-800 rounded-xl border border-gray-700/50 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-700/50 text-gray-400 text-left">
              <th className="px-4 py-3">Smell</th>
              <th className="px-4 py-3">File</th>
              <th className="px-4 py-3">Line</th>
              <th className="px-4 py-3">Band</th>
              <th className="px-4 py-3">Fusion</th>
              <th className="px-4 py-3">Symbolic</th>
              <th className="px-4 py-3">ML</th>
              <th className="px-4 py-3">Context</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((item, i) => (
              <Fragment key={`${item.file}-${item.smell_type}-${i}`}>
                <tr className="border-b border-gray-700/30 hover:bg-gray-700/20">
                  <td className="px-4 py-3 font-mono text-brand-400">{item.smell_type}</td>
                  <td className="px-4 py-3 text-gray-400">{item.file.split(/[\\/]/).pop()}</td>
                  <td className="px-4 py-3 text-gray-400">{item.line_number}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded border text-xs font-semibold ${bandColor[item.confidence_band] || ''}`}>
                      {item.confidence_band}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-white font-semibold">{(item.neuro_symbolic_confidence * 100).toFixed(1)}%</td>
                  <td className="px-4 py-3 text-gray-300">{(item.symbolic_score * 100).toFixed(1)}%</td>
                  <td className="px-4 py-3 text-gray-300">{(item.ml_score * 100).toFixed(1)}%</td>
                  <td className="px-4 py-3 text-gray-300">{(item.context_score * 100).toFixed(1)}%</td>
                </tr>
                <tr className="border-b border-gray-700/20">
                  <td colSpan={8} className="px-4 pb-3 text-xs text-gray-400">
                    {item.reasoning_trace.join(' | ')}
                  </td>
                </tr>
              </Fragment>
            ))}
          </tbody>
        </table>
        {rows.length === 0 && <p className="p-6 text-center text-gray-500">No items match this filter.</p>}
      </div>
    </div>
  );
}

function Card({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div className="bg-surface-800 border border-gray-700/50 rounded-xl p-4">
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
    </div>
  );
}
