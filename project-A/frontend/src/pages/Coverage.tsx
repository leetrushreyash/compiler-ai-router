import { useMemo } from 'react';
import { Info, ShieldCheck } from 'lucide-react';
import type { AnalysisReport } from '../types';

interface Props {
  report: AnalysisReport | null;
}

export default function Coverage({ report }: Props) {
  if (!report) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500 gap-3">
        <Info size={40} />
        <p>Run analysis to view coverage metrics.</p>
      </div>
    );
  }

  // Simulate coverage-like metrics from what we have (smell coverage per file)
  const fileCoverage = useMemo(() => {
    const sources = report.sources || {};
    return Object.entries(sources).map(([file, code]) => {
      const totalLines = code.split('\n').length;
      const smellLines = new Set(
        report.findings.filter((f) => f.file === file || file.endsWith(f.file)).map((f) => f.line_number),
      );
      const coveredLines = smellLines.size;
      const coveragePct = totalLines > 0 ? ((totalLines - coveredLines) / totalLines) * 100 : 100;
      return { file, totalLines, smellLines: coveredLines, coveragePct: +coveragePct.toFixed(1) };
    });
  }, [report]);

  const avgCoverage =
    fileCoverage.length > 0
      ? +(fileCoverage.reduce((s, f) => s + f.coveragePct, 0) / fileCoverage.length).toFixed(1)
      : 100;

  return (
    <div>
      <h2 className="text-2xl font-bold mb-1 flex items-center gap-2">
        <ShieldCheck size={22} className="text-emerald-400" /> Code Health Coverage
      </h2>
      <p className="text-gray-400 text-sm mb-6">
        Lines affected by smells vs clean lines per file.
      </p>

      {/* Summary */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
        <Card
          label="Avg Clean Coverage"
          value={`${avgCoverage}%`}
          color={avgCoverage > 80 ? 'text-green-400' : avgCoverage > 50 ? 'text-yellow-400' : 'text-red-400'}
        />
        <Card label="Files Analyzed" value={fileCoverage.length} color="text-cyan-400" />
        <Card
          label="Total Smell Lines"
          value={fileCoverage.reduce((s, f) => s + f.smellLines, 0)}
          color="text-red-400"
        />
      </div>

      {/* File heatmap */}
      <section>
        <h3 className="text-sm font-semibold text-gray-300 mb-3">File Health Heatmap</h3>
        <div className="space-y-3">
          {fileCoverage.map((fc) => (
            <div key={fc.file} className="bg-surface-800 border border-gray-700/50 rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-sm text-gray-200 truncate max-w-xs">
                  {fc.file.split(/[\\/]/).pop()}
                </span>
                <span
                  className={`text-sm font-bold ${
                    fc.coveragePct > 90 ? 'text-green-400' : fc.coveragePct > 70 ? 'text-yellow-400' : 'text-red-400'
                  }`}
                >
                  {fc.coveragePct}% clean
                </span>
              </div>
              {/* Bar */}
              <div className="w-full h-3 bg-gray-700 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${
                    fc.coveragePct > 90
                      ? 'bg-green-500'
                      : fc.coveragePct > 70
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                  }`}
                  style={{ width: `${fc.coveragePct}%` }}
                />
              </div>
              <div className="flex gap-4 text-xs text-gray-500 mt-1.5">
                <span>{fc.totalLines} total lines</span>
                <span>{fc.smellLines} lines with smells</span>
              </div>
            </div>
          ))}
        </div>
      </section>
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
