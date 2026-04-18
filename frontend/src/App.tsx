import { Routes, Route } from 'react-router-dom';
import { useState } from 'react';
import Sidebar from './components/Sidebar';
import CodeInput from './pages/CodeInput';
import Dashboard from './pages/Dashboard';
import CodeViewer from './pages/CodeViewer';
import Correlations from './pages/Correlations';
import Energy from './pages/Energy';
import Performance from './pages/Performance';
import Refactoring from './pages/Refactoring';
import Coverage from './pages/Coverage';
import NeuroSymbolic from './pages/NeuroSymbolic';
import type { AnalysisReport } from './types';

export default function App() {
  const [report, setReport] = useState<AnalysisReport | null>(null);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar hasReport={!!report} />
      <main className="flex-1 overflow-auto bg-surface-900 p-6">
        <Routes>
          <Route path="/" element={<CodeInput onReport={setReport} />} />
          <Route path="/dashboard" element={<Dashboard report={report} />} />
          <Route path="/code" element={<CodeViewer report={report} />} />
          <Route path="/correlations" element={<Correlations report={report} />} />
          <Route path="/energy" element={<Energy report={report} />} />
          <Route path="/performance" element={<Performance report={report} />} />
          <Route path="/neuro-symbolic" element={<NeuroSymbolic report={report} />} />
          <Route path="/refactoring" element={<Refactoring report={report} />} />
          <Route path="/coverage" element={<Coverage report={report} />} />
        </Routes>
      </main>
    </div>
  );
}
