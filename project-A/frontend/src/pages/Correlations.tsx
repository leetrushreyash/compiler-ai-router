import { useMemo } from 'react';
import { Info, BarChart3, GitBranch, AlertTriangle, TrendingUp } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ScatterChart, Scatter, ZAxis,
  AreaChart, Area, CartesianGrid, Legend,
} from 'recharts';
import type { AnalysisReport } from '../types';

interface Props {
  report: AnalysisReport | null;
}

/* ── colour palette ─────────────────────────────────────────────── */
const CHART_COLORS = [
  '#6c5ce7', '#00cec9', '#fd79a8', '#ffeaa7',
  '#55efc4', '#fab1a0', '#74b9ff', '#a29bfe',
  '#ff7675', '#fdcb6e', '#81ecec', '#e17055',
];

const corrColor = (v: number) => {
  if (v >= 0.7) return '#ff6b6b';
  if (v >= 0.4) return '#f9ca24';
  if (v >= 0.1) return '#55efc4';
  if (v >= -0.1) return '#636e72';
  return '#74b9ff';
};

/* ── custom tooltip ─────────────────────────────────────────────── */
const DarkTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-xs shadow-xl">
      <p className="text-gray-300 font-semibold mb-1">{label}</p>
      {payload.map((p: any, i: number) => (
        <p key={i} style={{ color: p.color }}>
          {p.name}: <span className="font-bold">{typeof p.value === 'number' ? p.value.toFixed(3) : p.value}</span>
        </p>
      ))}
    </div>
  );
};

export default function Correlations({ report }: Props) {
  if (!report?.correlation_analysis) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500 gap-3">
        <Info size={40} />
        <p>Run analysis with correlation enabled to view this page.</p>
      </div>
    );
  }

  const corr = report.correlation_analysis;
  const smells = Object.keys(corr.correlation_matrix);

  /* ── derived datasets ──────────────────────────────────────────── */

  // 1. Smell frequency data – prefer user-only totals over corpus-wide
  const smellFreqData = useMemo(() =>
    Object.entries(corr.summary.user_smell_totals || corr.summary.smell_totals || {})
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count),
    [corr],
  );

  // 2. Radar data (normalised by max for spider chart)
  const radarData = useMemo(() => {
    const max = Math.max(...smellFreqData.map((d) => d.count), 1);
    return smellFreqData.map((d) => ({
      smell: d.name.replace(/_/g, ' '),
      frequency: d.count,
      normalised: +((d.count / max) * 100).toFixed(1),
    }));
  }, [smellFreqData]);

  // 3. Edge list (upper triangle)
  const edges = useMemo(() => {
    const e: { source: string; target: string; weight: number }[] = [];
    for (let i = 0; i < smells.length; i++) {
      for (let j = i + 1; j < smells.length; j++) {
        const w = corr.correlation_matrix[smells[i]][smells[j]];
        if (Math.abs(w) > 0.05) {
          e.push({ source: smells[i], target: smells[j], weight: w });
        }
      }
    }
    return e.sort((a, b) => Math.abs(b.weight) - Math.abs(a.weight));
  }, [corr, smells]);

  // 4. Co-occurrence pairs bar data
  const coOccurData = useMemo(() =>
    corr.summary.top_co_occurring_pairs.map((p) => ({
      pair: `${p.pair[0]} ↔ ${p.pair[1]}`,
      coOccurrences: p.co_occurrence_count,
      correlation: +p.correlation.toFixed(3),
      weight: +p.interaction_weight.toFixed(3),
    })),
    [corr],
  );

  // 5. Hotspot risk bar data
  const hotspotBarData = useMemo(() =>
    [...corr.hotspots]
      .sort((a, b) => b.risk_score - a.risk_score)
      .slice(0, 15)
      .map((h) => ({
        file: h.file.split('/').pop() || h.file,
        fullPath: h.file,
        risk: h.risk_score,
        smells: h.smell_count,
      })),
    [corr],
  );

  // 6. Correlation distribution histogram
  const corrHistData = useMemo(() => {
    const bins: Record<string, number> = {
      '< -0.5': 0, '-0.5–0': 0, '0–0.2': 0,
      '0.2–0.5': 0, '0.5–0.8': 0, '0.8–1.0': 0,
    };
    for (let i = 0; i < smells.length; i++) {
      for (let j = i + 1; j < smells.length; j++) {
        const v = corr.correlation_matrix[smells[i]][smells[j]];
        if (v < -0.5) bins['< -0.5']++;
        else if (v < 0) bins['-0.5–0']++;
        else if (v < 0.2) bins['0–0.2']++;
        else if (v < 0.5) bins['0.2–0.5']++;
        else if (v < 0.8) bins['0.5–0.8']++;
        else bins['0.8–1.0']++;
      }
    }
    return Object.entries(bins).map(([range, count]) => ({ range, count }));
  }, [corr, smells]);

  // 7. Scatter data – each pair plotted by correlation vs co-occurrence weight
  const scatterData = useMemo(() =>
    corr.summary.top_co_occurring_pairs.map((p) => ({
      pair: `${p.pair[0]} ↔ ${p.pair[1]}`,
      correlation: +p.correlation.toFixed(3),
      coOccurrences: p.co_occurrence_count,
      weight: +p.interaction_weight.toFixed(3),
    })),
    [corr],
  );

  return (
    <div>
      <h2 className="text-2xl font-bold mb-1">Smell Correlations</h2>
      <p className="text-gray-400 text-sm mb-6">
        Co-occurrence analysis across {corr.summary.total_files_analyzed} files
        {corr.summary.background_files
          ? ` (${corr.summary.user_files_analyzed ?? '?'} submitted + ${corr.summary.background_files} background corpus)`
          : ''}
        .
      </p>

      {/* ── Summary cards ──────────────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <Card label="Files Analyzed" value={corr.summary.total_files_analyzed} icon={<BarChart3 size={16} className="text-brand-400" />} />
        <Card label="Avg Risk Score" value={corr.summary.average_risk_score.toFixed(1)} icon={<TrendingUp size={16} className="text-yellow-400" />} />
        <Card label="Max Risk Score" value={corr.summary.max_risk_score.toFixed(1)} icon={<AlertTriangle size={16} className="text-red-400" />} />
        <Card label="Co-occurring Pairs" value={corr.summary.top_co_occurring_pairs.length} icon={<GitBranch size={16} className="text-cyan-400" />} />
      </div>

      {/* ── 1. Smell Frequency + Radar  ────────────────────────────── */}
      <div className="grid lg:grid-cols-2 gap-6 mb-8">
        {/* Bar chart */}
        <section className="bg-surface-800 border border-gray-700/50 rounded-xl p-5">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <BarChart3 size={18} className="text-brand-400" /> Smell Frequency
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={smellFreqData} layout="vertical" margin={{ left: 10, right: 20 }}>
              <XAxis type="number" tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <YAxis
                type="category" dataKey="name" width={130}
                tick={{ fill: '#9ca3af', fontSize: 11 }}
                tickFormatter={(v: string) => v.replace(/_/g, ' ')}
              />
              <Tooltip content={<DarkTooltip />} />
              <Bar dataKey="count" radius={[0, 6, 6, 0]}>
                {smellFreqData.map((_, i) => (
                  <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </section>

        {/* Radar chart */}
        <section className="bg-surface-800 border border-gray-700/50 rounded-xl p-5">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <TrendingUp size={18} className="text-cyan-400" /> Smell Radar
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="70%">
              <PolarGrid stroke="#374151" />
              <PolarAngleAxis dataKey="smell" tick={{ fill: '#9ca3af', fontSize: 10 }} />
              <PolarRadiusAxis tick={{ fill: '#6b7280', fontSize: 10 }} />
              <Radar name="Frequency %" dataKey="normalised" stroke="#6c5ce7" fill="#6c5ce7" fillOpacity={0.35} />
            </RadarChart>
          </ResponsiveContainer>
        </section>
      </div>

      {/* ── 2. Co-occurrence Pairs Bar Chart ───────────────────────── */}
      {coOccurData.length > 0 && (
        <section className="bg-surface-800 border border-gray-700/50 rounded-xl p-5 mb-8">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <GitBranch size={18} className="text-pink-400" /> Co-occurrence Strength
          </h3>
          <ResponsiveContainer width="100%" height={Math.max(250, coOccurData.length * 40)}>
            <BarChart data={coOccurData} layout="vertical" margin={{ left: 10, right: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis type="number" tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <YAxis
                type="category" dataKey="pair" width={200}
                tick={{ fill: '#9ca3af', fontSize: 10 }}
              />
              <Tooltip content={<DarkTooltip />} />
              <Legend wrapperStyle={{ color: '#9ca3af', fontSize: 12 }} />
              <Bar dataKey="coOccurrences" name="Co-occurrences" fill="#fd79a8" radius={[0, 4, 4, 0]} />
              <Bar dataKey="weight" name="Interaction Weight" fill="#74b9ff" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </section>
      )}

      {/* ── 3. Correlation vs Co-occurrence Scatter ─────────────────── */}
      {scatterData.length > 0 && (
        <section className="bg-surface-800 border border-gray-400 shadow-sm rounded-xl p-5 mb-8">
          <h3 className="text-lg font-semibold mb-2 flex items-center gap-2 text-gray-100">
            <TrendingUp size={18} className="text-brand-500" /> Correlation vs Co-occurrence Analysis
          </h3>
          <div className="bg-brand-50 border border-brand-200 rounded-lg p-4 mb-4">
            <h4 className="text-sm font-bold text-brand-800 mb-1">What does this chart mean?</h4>
            <p className="text-sm text-gray-300 leading-relaxed mb-2">
              This chart visualizes the relationship between how often two code smells happen to appear in the same file (<span className="font-semibold text-gray-100">Co-occurrences</span>, Y-axis) vs whether they actually have a mathematical statistical relationship (<span className="font-semibold text-gray-100">Correlation</span>, X-axis).
            </p>
            <ul className="text-xs text-gray-300 list-disc pl-5 space-y-1">
              <li><strong className="text-gray-100">Top-Right (Danger Zone):</strong> Smells that happen heavily together AND are statistically linked. Fixing one might fix the other.</li>
              <li><strong className="text-gray-100">Top-Left:</strong> Smells that appear in the same files often by pure coincidence, but don't mathematically drive each other.</li>
              <li><strong className="text-gray-100">Bubble Size:</strong> The overall priority/weight of the interaction. Larger bubbles represent highly toxic pairings.</li>
            </ul>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart margin={{ left: 10, right: 20, top: 10, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                type="number" dataKey="correlation" name="Correlation"
                tick={{ fill: '#9ca3af', fontSize: 11 }}
                label={{ value: 'Correlation', position: 'bottom', fill: '#6b7280', fontSize: 11 }}
              />
              <YAxis
                type="number" dataKey="coOccurrences" name="Co-occurrences"
                tick={{ fill: '#9ca3af', fontSize: 11 }}
                label={{ value: 'Co-occurrences', angle: -90, position: 'insideLeft', fill: '#6b7280', fontSize: 11 }}
              />
              <ZAxis type="number" dataKey="weight" range={[60, 400]} name="Weight" />
              <Tooltip
                content={({ active, payload }: any) => {
                  if (!active || !payload?.length) return null;
                  const d = payload[0].payload;
                  return (
                    <div className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-xs shadow-xl">
                      <p className="text-gray-200 font-semibold">{d.pair}</p>
                      <p className="text-cyan-400">Correlation: {d.correlation}</p>
                      <p className="text-pink-400">Co-occurrences: {d.coOccurrences}</p>
                      <p className="text-yellow-400">Weight: {d.weight}</p>
                    </div>
                  );
                }}
              />
              <Scatter data={scatterData} fill="#6c5ce7">
                {scatterData.map((d, i) => (
                  <Cell key={i} fill={corrColor(d.correlation)} />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </section>
      )}

      {/* ── 4. Correlation Distribution Histogram ──────────────────── */}
      <section className="bg-surface-800 border border-gray-400 shadow-sm rounded-xl p-5 mb-8">
        <h3 className="text-lg font-semibold mb-2 flex items-center gap-2 text-gray-100">
          <BarChart3 size={18} className="text-brand-500" /> Correlation Distribution
        </h3>
        <p className="text-sm text-gray-200 mb-4 bg-brand-50 border border-brand-200 p-3 rounded-lg leading-relaxed">
          <strong className="text-gray-100 tracking-wide uppercase text-xs block mb-1">What am I looking at?</strong>
          This area chart shows a summary of ALL code smell pairs and how strongly they are connected mathematically. 
          Are most pairs completely unrelated (bulge in the middle near 0)? Or are there massive clusters of smells that always drag each other down (bulge on the right near 0.8–1.0)? 
          A bulge near 1.0 means your codebase suffers strictly from cascading code smell "chain reactions."
        </p>
        <ResponsiveContainer width="100%" height={250}>
          <AreaChart data={corrHistData} margin={{ left: 10, right: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="range" tick={{ fill: '#9ca3af', fontSize: 11 }} />
            <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
            <Tooltip content={<DarkTooltip />} />
            <Area
              type="monotone" dataKey="count" name="Pairs"
              stroke="#55efc4" fill="#55efc4" fillOpacity={0.25}
            />
          </AreaChart>
        </ResponsiveContainer>
      </section>

      {/* ── 5. Hotspot Risk Scores ─────────────────────────────────── */}
      {hotspotBarData.length > 0 && (
        <section className="bg-surface-800 border border-gray-700/50 rounded-xl p-5 mb-8">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <AlertTriangle size={18} className="text-red-400" /> Hotspot Risk Scores
          </h3>
          <ResponsiveContainer width="100%" height={Math.max(200, hotspotBarData.length * 36)}>
            <BarChart data={hotspotBarData} layout="vertical" margin={{ left: 10, right: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis type="number" tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <YAxis
                type="category" dataKey="file" width={140}
                tick={{ fill: '#9ca3af', fontSize: 10 }}
              />
              <Tooltip
                content={({ active, payload }: any) => {
                  if (!active || !payload?.length) return null;
                  const d = payload[0].payload;
                  return (
                    <div className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-xs shadow-xl">
                      <p className="text-gray-200 font-semibold font-mono">{d.fullPath}</p>
                      <p className="text-red-400">Risk Score: {d.risk}</p>
                      <p className="text-yellow-400">Distinct Smells: {d.smells}</p>
                    </div>
                  );
                }}
              />
              <Bar dataKey="risk" name="Risk Score" radius={[0, 6, 6, 0]}>
                {hotspotBarData.map((d, i) => (
                  <Cell key={i} fill={d.risk > 20 ? '#ff6b6b' : d.risk > 10 ? '#f9ca24' : '#55efc4'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </section>
      )}

      {/* ── 6. Hotspot File Cards ──────────────────────────────────── */}
      <section className="mb-8">
        <h3 className="text-lg font-semibold mb-3">Hotspot Files</h3>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {corr.hotspots.map((h, i) => (
            <div
              key={i}
              className="bg-surface-800 border border-gray-700/50 rounded-xl p-4"
            >
              <p className="font-mono text-sm text-gray-200 truncate">{h.file}</p>
              <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                <span>
                  Risk:{' '}
                  <span className={h.risk_score > 20 ? 'text-red-400 font-bold' : 'text-yellow-400 font-bold'}>
                    {h.risk_score}
                  </span>
                </span>
                <span>Smells: {h.smell_count}</span>
              </div>
              <div className="flex flex-wrap gap-1 mt-2">
                {h.smells_present.map((s) => (
                  <span key={s} className="bg-gray-700 text-gray-300 text-xs px-2 py-0.5 rounded-full">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── 7. Correlation Matrix heatmap ──────────────────────────── */}
      <section className="mb-8">
        <h3 className="text-lg font-semibold mb-3">Correlation Matrix</h3>
        <div className="overflow-auto">
          <table className="text-xs">
            <thead>
              <tr>
                <th />
                {smells.map((s) => (
                  <th key={s} className="px-2 py-1 text-gray-400 font-mono truncate max-w-[80px] -rotate-45 origin-bottom-left">
                    {s}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {smells.map((row) => (
                <tr key={row}>
                  <td className="pr-2 py-1 text-gray-400 font-mono text-right whitespace-nowrap">{row}</td>
                  {smells.map((col) => {
                    const v = corr.correlation_matrix[row][col];
                    const bg =
                      v === 1 ? 'bg-brand-600/50' :
                      v > 0.5 ? 'bg-red-500/40' :
                      v > 0 ? 'bg-yellow-500/20' :
                      v < -0.15 ? 'bg-blue-500/20' : 'bg-gray-800';
                    return (
                      <td key={col} className={`px-2 py-1 text-center rounded ${bg}`} title={`${row} ↔ ${col}: ${v.toFixed(2)}`}>
                        {v.toFixed(2)}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* ── 8. Strongest Pairs list ────────────────────────────────── */}
      <section>
        <h3 className="text-lg font-semibold mb-3">Strongest Co-occurring Pairs</h3>
        <div className="space-y-2">
          {edges.slice(0, 10).map((edge, i) => (
            <div
              key={i}
              className="flex items-center gap-3 bg-surface-800 border border-gray-700/50 rounded-lg px-4 py-2 text-sm"
            >
              <span className="font-mono text-brand-400">{edge.source}</span>
              <span className="text-gray-500">↔</span>
              <span className="font-mono text-brand-400">{edge.target}</span>
              <span className="ml-auto">
                <span
                  className={`px-2 py-0.5 rounded text-xs font-bold ${
                    edge.weight > 0 ? 'bg-red-500/20 text-red-400' : 'bg-blue-500/20 text-blue-400'
                  }`}
                >
                  {edge.weight > 0 ? '+' : ''}{edge.weight.toFixed(3)}
                </span>
              </span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function Card({ label, value, icon }: { label: string; value: string | number; icon?: React.ReactNode }) {
  return (
    <div className="bg-surface-800 border border-gray-700/50 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-1">
        {icon}
        <p className="text-xs text-gray-400">{label}</p>
      </div>
      <p className="text-2xl font-bold text-gray-100">{value}</p>
    </div>
  );
}
