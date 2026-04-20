import axios from 'axios';
import type { AnalysisReport, ExampleFile } from './types';

const api = axios.create({ baseURL: '/api' });

export async function fetchExamples(): Promise<ExampleFile[]> {
  const res = await api.get('/examples');
  return res.data.examples;
}

export async function fetchExampleCode(filename: string): Promise<string> {
  const res = await api.get(`/examples/${filename}`);
  return res.data.code;
}

export async function analyzeCode(
  code: string,
  filename: string = 'untitled.py',
): Promise<AnalysisReport> {
  const res = await api.post('/analyze/code', { code, filename });
  return res.data;
}

export async function analyzeUpload(files: File[]): Promise<AnalysisReport> {
  const form = new FormData();
  files.forEach((f) => form.append('files', f));
  const res = await api.post('/analyze/upload', form);
  return res.data;
}

export async function analyzeExamples(filenames: string[]): Promise<AnalysisReport> {
  const res = await api.post('/analyze/examples', { filenames });
  return res.data;
}

export async function fetchSecurityAudit(code: string, filename: string = 'untitled.py'): Promise<any[]> {
  const res = await api.post('/cross-project/security', { code, filename });
  return res.data.security_issues;
}
