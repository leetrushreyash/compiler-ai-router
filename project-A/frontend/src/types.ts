/* ------------------------------------------------------------------ */
/* Shared TypeScript interfaces matching the backend JSON responses    */
/* ------------------------------------------------------------------ */

export interface Finding {
  file: string;
  line_number: number;
  smell_type: string;
  severity: string;
  confidence: number;
  suggested_fix: string;
}

export interface ShapEntry {
  feature: string;
  value: number;
  shap_value: number;
  direction: string;
}

export interface MLExplanation {
  smell_type: string;
  probability: number;
  prediction_source: string;
  shap_explanation: ShapEntry[];
  explanation_text: string;
  file: string;
}

export interface Refactoring {
  smell_type: string;
  description: string;
  original: string;
  refactored: string;
  diff: string;
  line_start: number;
  line_end: number;
  file: string;
}

export interface Hotspot {
  file: string;
  risk_score: number;
  smell_count: number;
  smells_present: string[];
}

export interface CorrelationAnalysis {
  correlation_matrix: Record<string, Record<string, number>>;
  hotspots: Hotspot[];
  interaction_graph_mermaid: string;
  summary: {
    total_files_analyzed: number;
    user_files_analyzed?: number;
    background_files?: number;
    smell_totals: Record<string, number>;
    user_smell_totals?: Record<string, number>;
    top_co_occurring_pairs: {
      pair: [string, string];
      co_occurrence_count: number;
      correlation: number;
      interaction_weight: number;
    }[];
    average_risk_score: number;
    max_risk_score: number;
  };
}

export interface PrioritizedFinding extends Finding {
  priority_score: number;
  priority_band: string;
  priority_reason: string;
}

export interface NeuroSymbolicItem {
  file: string;
  line_number: number;
  smell_type: string;
  severity: string;
  symbolic_score: number;
  ml_score: number;
  context_score: number;
  neuro_symbolic_confidence: number;
  confidence_band: 'very_high' | 'high' | 'moderate' | 'low';
  reasoning_trace: string[];
}

export interface NeuroSymbolicAnalysis {
  method: string;
  items: NeuroSymbolicItem[];
  summary: {
    count: number;
    very_high: number;
    high: number;
    moderate: number;
    low: number;
    average_confidence: number;
  };
}

export interface EnergyReport {
  wall_time_s: number;
  cpu_time_s: number;
  peak_memory_mb: number;
  avg_cpu_percent: number;
  estimated_energy_joules: number;
  rapl_available: boolean;
  rapl_energy_joules: number | null;
  readings: { t: number; cpu: number; mem: number }[];
  phases: Record<string, number>;
  energy_per_file: number;
  energy_per_smell: number;
  smell_energy_breakdown?: { smell_type: string; file: string; energy_uj: number; energy_j: number }[];
}

export interface AnalysisReport {
  findings: Finding[];
  sources?: Record<string, string>;
  refactorings?: Refactoring[];
  correlation_analysis?: CorrelationAnalysis;
  ml_explanations?: MLExplanation[];
  prioritized_findings?: PrioritizedFinding[];
  neuro_symbolic_analysis?: NeuroSymbolicAnalysis;
  energy?: EnergyReport;
}

export interface ExampleFile {
  name: string;
  path: string;
}
