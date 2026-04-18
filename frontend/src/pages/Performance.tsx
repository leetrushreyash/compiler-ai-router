import { useMemo } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Cell,
} from 'recharts';
import { Info, Timer } from 'lucide-react';
import type { AnalysisReport } from '../types';

interface Props {
  report: AnalysisReport | null;
}

const COLORS = ['#6366f1', '#22d3ee', '#f59e0b', '#ef4444', '#10b981', '#8b5cf6', '#f97316', '#ec4899'];

export default function Performance({ report }: Props) {
  if (!report?.energy?.phases) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500 gap-3">
        <Info size={40} />
        <p>Run analysis to see performance timeline.</p>
      </div>
    );
  }

  const phases = report.energy.phases;
  const total = report.energy.wall_time_s;

  const timeline = useMemo(() => {
    let cumulative = 0;
    return Object.entries(phases).map(([name, duration]) => {
      const start = cumulative;
      cumulative += duration;
      return { name, duration: +duration.toFixed(4), start: +start.toFixed(4), end: +cumulative.toFixed(4) };
    });
  }, [phases]);

  const barData = useMemo(
    () => Object.entries(phases).map(([name, duration]) => ({ name, duration: +duration.toFixed(4) })),
    [phases],
  );

  return (
    <div>
      <h2 className="text-2xl font-bold mb-1 flex items-center gap-2">
        <Timer size={22} className="text-cyan-400" /> Performance Timeline
      </h2>
      <p className="text-gray-400 text-sm mb-6">
        Pipeline phase breakdown · Total wall time: <span className="text-white font-mono">{total.toFixed(3)}s</span>
      </p>

      {/* Visual timeline bar */}
      <section className="mb-8">
        <h3 className="text-sm font-semibold text-gray-300 mb-3">Execution Timeline</h3>
        <div className="bg-surface-800 border border-gray-700/50 rounded-xl p-5">
          <div className="flex h-10 rounded-lg overflow-hidden">
            {timeline.map((phase, i) => {
              const pct = total > 0 ? (phase.duration / total) * 100 : 0;
              return (
                <div
                  key={phase.name}
                  className="relative group"
                  style={{ width: `${Math.max(pct, 1)}%`, backgroundColor: COLORS[i % COLORS.length] }}
                  title={`${phase.name}: ${phase.duration.toFixed(4)}s`}
                >
                  {pct > 8 && (
                    <span className="absolute inset-0 flex items-center justify-center text-[10px] font-bold text-white/90 truncate px-1">
                      {phase.name}
                    </span>
                  )}
                  {/* Tooltip on hover */}
                  <div className="absolute -top-12 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-xs px-2 py-1 rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                    {phase.name}: {phase.duration.toFixed(4)}s ({pct.toFixed(1)}%)
                  </div>
                </div>
              );
            })}
          </div>

          {/* Legend */}
          <div className="flex flex-wrap gap-3 mt-4">
            {timeline.map((phase, i) => (
              <span key={i} className="flex items-center gap-1.5 text-xs text-gray-300">
                <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                {phase.name}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Bar chart of durations */}
      <section className="mb-8">
        <h3 className="text-sm font-semibold text-gray-300 mb-3">Phase Duration</h3>
        <div className="bg-surface-800 border border-gray-700/50 rounded-xl p-5">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={barData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis type="number" stroke="#666" tick={{ fontSize: 11 }} label={{ value: 'Seconds', position: 'insideBottomRight', offset: -5, fill: '#888' }} />
              <YAxis type="category" dataKey="name" stroke="#666" tick={{ fontSize: 11 }} width={130} />
              <Tooltip contentStyle={{ background: '#1e1e2e', border: '1px solid #444' }} />
              <Bar dataKey="duration" radius={[0, 4, 4, 0]}>
                {barData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/* Detailed table */}
      <section>
        <h3 className="text-sm font-semibold text-gray-300 mb-3">Detail Breakdown</h3>
        <div className="bg-surface-800 border border-gray-700/50 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-700/50 text-gray-400 text-left">
                <th className="px-4 py-3">Phase</th>
                <th className="px-4 py-3">Start</th>
                <th className="px-4 py-3">End</th>
                <th className="px-4 py-3">Duration</th>
                <th className="px-4 py-3">% of Total</th>
              </tr>
            </thead>
            <tbody>
              {timeline.map((phase, i) => (
                <tr key={i} className="border-b border-gray-700/30 hover:bg-gray-700/20">
                  <td className="px-4 py-3 flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                    <span className="font-mono">{phase.name}</span>
                  </td>
                  <td className="px-4 py-3 font-mono text-gray-400">{phase.start.toFixed(4)}s</td>
                  <td className="px-4 py-3 font-mono text-gray-400">{phase.end.toFixed(4)}s</td>
                  <td className="px-4 py-3 font-mono text-white">{phase.duration.toFixed(4)}s</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-20 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${total > 0 ? (phase.duration / total) * 100 : 0}%`,
                            backgroundColor: COLORS[i % COLORS.length],
                          }}
                        />
                      </div>
                      <span className="text-xs text-gray-400">{total > 0 ? ((phase.duration / total) * 100).toFixed(1) : 0}%</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
