import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, Play, FileCode, ClipboardPaste } from 'lucide-react';
import { analyzeCode, analyzeUpload, analyzeExamples, fetchExamples } from '../api';
import type { AnalysisReport, ExampleFile } from '../types';

interface Props {
  onReport: (r: AnalysisReport) => void;
}

type Mode = 'paste' | 'upload' | 'examples';

export default function CodeInput({ onReport }: Props) {
  const navigate = useNavigate();
  const [mode, setMode] = useState<Mode>('paste');
  const [code, setCode] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [examples, setExamples] = useState<ExampleFile[]>([]);
  const [selectedExamples, setSelectedExamples] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchExamples().then(setExamples).catch(() => {});
  }, []);

  const toggleExample = (name: string) => {
    setSelectedExamples((prev: string[]) =>
      prev.includes(name) ? prev.filter((n: string) => n !== name) : [...prev, name],
    );
  };

  const handleAnalyze = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      let report: AnalysisReport;
      if (mode === 'paste') {
        if (!code.trim()) { setError('Paste some Python code first.'); setLoading(false); return; }
        report = await analyzeCode(code);
      } else if (mode === 'upload') {
        if (files.length === 0) { setError('Select at least one file.'); setLoading(false); return; }
        report = await analyzeUpload(files);
      } else {
        if (selectedExamples.length === 0) { setError('Select at least one example.'); setLoading(false); return; }
        report = await analyzeExamples(selectedExamples);
      }
      onReport(report);
      navigate('/dashboard');
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      const msg = Array.isArray(detail) ? detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ') : detail;
      setError(typeof msg === 'string' ? msg : err.message || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  }, [mode, code, files, selectedExamples, onReport, navigate]);

  const tabs: { key: Mode; label: string; icon: any }[] = [
    { key: 'paste', label: 'Paste Code', icon: ClipboardPaste },
    { key: 'upload', label: 'Upload Files', icon: Upload },
    { key: 'examples', label: 'Examples', icon: FileCode },
  ];

  return (
    <div className="max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-1">Analyze Code</h2>
      <p className="text-gray-400 text-sm mb-6">
        Paste code, upload files, or pick from built-in examples.
      </p>

      {/* Mode tabs */}
      <div className="flex gap-2 mb-6">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setMode(key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors
              ${mode === key
                ? 'bg-brand-600 text-white'
                : 'bg-surface-800 text-gray-300 hover:bg-gray-700/60'}`}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </div>

      {/* Paste mode */}
      {mode === 'paste' && (
        <textarea
          value={code}
          onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setCode(e.target.value)}
          placeholder="# Paste your Python code here..."
          className="w-full h-80 bg-surface-800 border border-gray-700 rounded-xl p-4 text-sm font-mono text-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
        />
      )}

      {/* Upload mode */}
      {mode === 'upload' && (
        <div className="bg-surface-800 border-2 border-dashed border-gray-600 rounded-xl p-10 text-center">
          <Upload className="mx-auto mb-3 text-gray-400" size={40} />
          <p className="text-gray-300 mb-3">Drag & drop Python files here, or click to browse</p>
          <input
            type="file"
            accept=".py"
            multiple
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFiles(Array.from(e.target.files || []))}
            className="block mx-auto text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-brand-600 file:text-white file:cursor-pointer"
          />
          {files.length > 0 && (
            <p className="mt-3 text-sm text-brand-500">{files.length} file(s) selected</p>
          )}
        </div>
      )}

      {/* Examples mode */}
      {mode === 'examples' && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {examples.map((ex: ExampleFile) => {
            const sel = selectedExamples.includes(ex.name);
            return (
              <button
                key={ex.name}
                onClick={() => toggleExample(ex.name)}
                className={`p-3 rounded-xl border text-sm text-left transition-colors
                  ${sel
                    ? 'border-brand-500 bg-brand-600/20 text-brand-400'
                    : 'border-gray-700 bg-surface-800 text-gray-300 hover:border-gray-500'}`}
              >
                <FileCode size={16} className="mb-1" />
                {ex.name}
              </button>
            );
          })}
          {examples.length === 0 && (
            <p className="col-span-3 text-gray-500 text-sm">No example files found.</p>
          )}
        </div>
      )}

      {/* Error */}
      {error && <p className="mt-4 text-red-400 text-sm">{error}</p>}

      {/* Analyze button */}
      <button
        onClick={handleAnalyze}
        disabled={loading}
        className="mt-6 flex items-center gap-2 px-6 py-3 rounded-xl bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-semibold transition-colors"
      >
        <Play size={18} />
        {loading ? 'Analyzing…' : 'Run Analysis'}
      </button>
    </div>
  );
}
