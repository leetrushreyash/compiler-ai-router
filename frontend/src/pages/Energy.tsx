import { useMemo } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, Legend,
} from 'recharts';
import { Info, Zap } from 'lucide-react';
import type { AnalysisReport } from '../types';

interface Props {
  report: AnalysisReport | null;
}

const COLORS = ['#6366f1', '#22d3ee', '#f59e0b', '#ef4444', '#10b981', '#8b5cf6', '#f97316'];

export default function Energy({ report }: Props) {
  if (!report?.energy) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500 gap-3">
        <Info size={40} />
        <p>Run analysis to see energy metrics.</p>
      </div>
    );
  }

  const e = report.energy;

  // Phase breakdown for pie chart
  const phaseData = useMemo(
    () => Object.entries(e.phases).map(([name, time]) => ({ name, time: +time.toFixed(4) })),
    [e.phases],
  );

  // Time-series readings
  const timeData = useMemo(
    () => e.readings.map((r) => ({ t: r.t.toFixed(3), cpu: r.cpu, mem: r.mem })),
    [e.readings],
  );

  // Energy per smell type (estimated proportionally)
  const smellCounts = useMemo(() => {
    const map: Record<string, number> = {};
    report.findings.forEach((f) => { map[f.smell_type] = (map[f.smell_type] || 0) + 1; });
    return Object.entries(map).map(([type, count]) => ({
      type,
      count,
      energy: +((e.estimated_energy_joules / Math.max(report.findings.length, 1)) * count).toFixed(6),
    }));
  }, [report.findings, e]);

  return (
    <div>
      <h2 className="text-2xl font-bold mb-1 flex items-center gap-2">
        <Zap size={22} className="text-yellow-400" /> Energy Consumption
      </h2>
      <p className="text-gray-400 text-sm mb-6">
        {e.rapl_available
          ? 'Hardware-measured via Intel RAPL energy counters'
          : 'Software-estimated via CPU utilisation × TDP model (psutil)'}
      </p>

      {/* Methodology banner */}
      <div className="mb-6 bg-surface-800 border border-gray-700/50 rounded-xl p-4 flex items-start gap-3">
        <Zap size={18} className={e.rapl_available ? 'text-green-400 mt-0.5' : 'text-yellow-400 mt-0.5'} />
        <div>
          <p className="text-sm font-medium text-gray-200">
            {e.rapl_available ? 'Hardware Energy (Intel RAPL)' : 'Software Energy Estimation'}
          </p>
          <p className="text-xs text-gray-400 mt-1">
            {e.rapl_available
              ? 'Reading CPU package energy directly from /sys/class/powercap/intel-rapl registers. Accuracy: ±1%.'
              : 'Energy is estimated using: E = TDP × CPU_utilisation × time. This model uses psutil to sample real-time CPU load and multiplies by a conservative 15W TDP baseline. On Linux servers, the tool automatically upgrades to hardware-level Intel RAPL counters for ±1% accuracy.'}
          </p>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <Card label="Total Energy" value={`${e.estimated_energy_joules.toFixed(4)} J`} color="text-yellow-400" />
        <Card label="Wall Time" value={`${e.wall_time_s.toFixed(3)} s`} color="text-cyan-400" />
        <Card label="CPU Time" value={`${e.cpu_time_s.toFixed(3)} s`} color="text-brand-500" />
        <Card label="Peak Memory" value={`${e.peak_memory_mb.toFixed(1)} MB`} color="text-emerald-400" />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <Card label="Avg CPU %" value={`${e.avg_cpu_percent.toFixed(1)}%`} color="text-orange-400" />
        <Card label="Energy / File" value={`${e.energy_per_file.toFixed(6)} J`} color="text-purple-400" />
        <Card label="Energy / Smell" value={`${e.energy_per_smell.toFixed(6)} J`} color="text-pink-400" />
        <Card
          label="Measurement"
          value={e.rapl_available ? 'Hardware RAPL' : 'Software TDP'}
          color={e.rapl_available ? 'text-green-400' : 'text-yellow-400'}
        />
      </div>

      {/* Charts row */}
      <div className="grid lg:grid-cols-2 gap-6 mb-8">
        {/* CPU & Memory over time */}
        <ChartCard title="CPU & Memory over Time">
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={timeData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="t" stroke="#666" tick={{ fontSize: 11 }} label={{ value: 'Time (s)', position: 'insideBottomRight', offset: -5, fill: '#888' }} />
              <YAxis stroke="#666" tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ background: '#1e1e2e', border: '1px solid #444' }} />
              <Legend />
              <Line type="monotone" dataKey="cpu" name="CPU %" stroke="#6366f1" dot={false} />
              <Line type="monotone" dataKey="mem" name="Memory MB" stroke="#22d3ee" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Phase breakdown pie */}
        <ChartCard title="Phase Time Breakdown">
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie data={phaseData} dataKey="time" nameKey="name" cx="50%" cy="50%" outerRadius={90} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                {phaseData.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: '#7f7fcc', border: '1px solid #444' }} />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Energy per smell type bar chart */}
      <ChartCard title="Estimated Energy per Smell Type">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={smellCounts}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="type" stroke="#666" tick={{ fontSize: 11 }} angle={-30} textAnchor="end" height={80} />
            <YAxis stroke="#666" tick={{ fontSize: 11 }} label={{ value: 'Joules', angle: -90, position: 'insideLeft', fill: '#888' }} />
            <Tooltip contentStyle={{ background: '#1e1e2e', border: '1px solid #444' }} />
            <Bar dataKey="energy" fill="#6366f1" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  );
}

function Card({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div className="bg-surface-800 border border-gray-700/50 rounded-xl p-4">
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <p className={`text-xl font-bold ${color}`}>{value}</p>
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-surface-800 border border-gray-700/50 rounded-xl p-5">
      <h4 className="text-sm font-semibold text-gray-300 mb-4">{title}</h4>
      {children}
    </div>
  );
}
