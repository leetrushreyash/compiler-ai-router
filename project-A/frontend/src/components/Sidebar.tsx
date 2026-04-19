import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  Code2,
  LayoutDashboard,
  FileCode,
  GitCompare,
  Zap,
  Timer,
  Cpu,
  Wrench,
  ShieldCheck,
} from 'lucide-react';

interface Props {
  hasReport: boolean;
}

const links = [
  { to: '/', label: 'Analyze', icon: Code2 },
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, needsReport: true },
  { to: '/code', label: 'Code Viewer', icon: FileCode, needsReport: true },
  { to: '/correlations', label: 'Correlations', icon: GitCompare, needsReport: true },
  { to: '/energy', label: 'Energy', icon: Zap, needsReport: true },
  { to: '/performance', label: 'Performance', icon: Timer, needsReport: true },
  { to: '/neuro-symbolic', label: 'Neuro-Symbolic', icon: Cpu, needsReport: true },
  { to: '/refactoring', label: 'Refactoring', icon: Wrench, needsReport: true },
  { to: '/coverage', label: 'Coverage', icon: ShieldCheck, needsReport: true },
];

export default function Sidebar({ hasReport }: Props) {
  return (
    <aside className="w-60 flex-shrink-0 bg-surface-800 border-r border-gray-700/50 flex flex-col">
      {/* Brand */}
      <div className="px-5 py-5 border-b border-gray-700/50">
        <h1 className="text-lg font-bold tracking-tight text-brand-500">CodeSmell</h1>
        <p className="text-xs text-gray-400 mt-0.5">ML-Powered Compiler</p>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 space-y-1 px-3 overflow-auto">
        {links.map(({ to, label, icon: Icon, needsReport }) => {
          const disabled = needsReport && !hasReport;
          return (
            <NavLink
              key={to}
              to={disabled ? '#' : to}
              onClick={(e: React.MouseEvent) => disabled && e.preventDefault()}
              className={({ isActive }: { isActive: boolean }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors
                ${disabled ? 'text-gray-400 cursor-not-allowed' : ''}
                ${isActive && !disabled ? 'bg-brand-50 text-brand-700 font-medium border border-brand-200 shadow-sm' : ''}
                ${!isActive && !disabled ? 'text-gray-600 hover:bg-gray-800 hover:text-gray-900 border border-transparent' : ''}`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-gray-700/50 text-xs text-gray-500">
        v2.0 · Green Compiler
      </div>
    </aside>
  );
}
