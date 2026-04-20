import { useState } from 'react';
import { fetchSecurityAudit } from '../api';
import { ShieldCheck, Loader2, AlertTriangle, ShieldAlert } from 'lucide-react';
import type { AnalysisReport } from '../types';

interface Props {
  report: AnalysisReport | null;
}

export default function Security({ report }: Props) {
  const [securityIssues, setSecurityIssues] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!report || !report.sources) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500 gap-3">
        <ShieldCheck size={40} />
        <p>Run analysis first to perform a security audit.</p>
      </div>
    );
  }

  const handleAudit = async () => {
    setLoading(true);
    setError(null);
    setSecurityIssues(null);

    // Get the first available source file to analyze
    const firstFilename = Object.keys(report.sources || {})[0];
    const sourceCode = report.sources ? report.sources[firstFilename] : '';

    if (!sourceCode) {
      setError('No source code available to analyze.');
      setLoading(false);
      return;
    }

    try {
      const issues = await fetchSecurityAudit(sourceCode, firstFilename);
      setSecurityIssues(issues);
    } catch (err: any) {
      setError(err.response?.data?.error || err.message || 'Security check failed. Is Project C running?');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto pb-10">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <ShieldCheck size={26} className="text-emerald-400" /> Security Audit
          </h2>
          <p className="text-gray-400 text-sm mt-1">
            Deep security evaluation powered natively by Project C's analysis engine.
          </p>
        </div>
        
        <button
          onClick={handleAudit}
          disabled={loading}
          className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-medium transition-colors"
        >
          {loading ? <Loader2 className="animate-spin" size={18} /> : <ShieldAlert size={18} />}
          {loading ? 'Auditing...' : 'Run Security Audit'}
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-900/30 border border-red-500/30 text-red-400 mb-6 flex items-start gap-3">
          <AlertTriangle className="mt-0.5 flex-shrink-0" size={18} />
          <p>{error}</p>
        </div>
      )}

      {!securityIssues && !loading && !error && (
        <div className="flex flex-col items-center justify-center p-16 border border-dashed border-gray-700/50 rounded-2xl bg-surface-800/50">
          <ShieldAlert className="text-gray-500 mb-4" size={48} />
          <p className="text-gray-300 text-lg font-medium mb-1">Audit Not Started</p>
          <p className="text-gray-500 text-sm">Click the button above to route this code to Project C for evaluation.</p>
        </div>
      )}

      {securityIssues && securityIssues.length === 0 && (
        <div className="flex flex-col items-center justify-center p-12 border border-emerald-500/30 rounded-2xl bg-emerald-900/10">
          <ShieldCheck className="text-emerald-400 mb-4" size={48} />
          <p className="text-emerald-300 text-lg font-medium mb-1">No Security Issues Found</p>
          <p className="text-emerald-500/70 text-sm">Project C's engine returned a clean bill of health.</p>
        </div>
      )}

      {securityIssues && securityIssues.length > 0 && (
        <div className="space-y-4">
          <div className="mb-4">
            <span className="px-3 py-1 bg-red-900/30 text-red-400 border border-red-500/30 rounded-full text-sm font-semibold">
              {securityIssues.length} Vulnerabilit{securityIssues.length === 1 ? 'y' : 'ies'} Detected
            </span>
          </div>

          {securityIssues.map((issue, idx) => (
            <div key={idx} className="p-5 rounded-xl border border-red-500/30 bg-surface-800">
              <div className="flex items-center gap-3 mb-2">
                <AlertTriangle className="text-red-400" size={20} />
                <h3 className="font-semibold text-gray-200">{issue.type || 'Unknown Vulnerability'}</h3>
                <span className="ml-auto text-xs font-semibold px-2 py-1 rounded bg-red-500/20 text-red-300 border border-red-400/20">
                  {issue.severity || 'Critical'}
                </span>
              </div>
              <p className="text-gray-400 text-sm mb-3">
                {issue.description || issue.error || 'A dangerous pattern was detected by the polyglot rules engine.'}
              </p>
              {issue.function && (
                <div className="mt-4 pt-4 border-t border-gray-700/50">
                  <p className="text-xs text-gray-500 font-mono">Found in block/function: <span className="text-brand-400">{issue.function}</span></p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
