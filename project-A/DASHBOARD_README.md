# Code Smell Compiler — Web Dashboard

A modern web interface for the ML-Powered Code Smell Compiler with energy consumption visualization.

## Architecture

```
CLI Tool (code_smell_compiler/)
       ↓
FastAPI Backend (backend/)   ← wraps the CLI, adds energy measurement
       ↓
REST API (/api/*)
       ↓
React Dashboard (frontend/) ← TypeScript + TailwindCSS + Recharts + Monaco
```

## Quick Start

### 1. Install backend dependencies

```bash
cd compiler
pip install -r backend/requirements.txt
```

> Make sure the main project dependencies are already installed:
> `pip install -r code_smell_compiler/requirements.txt`

### 2. Start the backend

```bash
cd compiler
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.
Swagger docs at `http://localhost:8000/docs`.

### 3. Install frontend dependencies

```bash
cd compiler/frontend
npm install
```

### 4. Start the frontend

```bash
cd compiler/frontend
npm run dev
```

The dashboard will open at `http://localhost:3000`.
It proxies `/api/*` requests to the backend automatically.

## Pages

| Page | Description |
|------|-------------|
| **Analyze** | Paste code, upload files, or pick from examples |
| **Dashboard** | Smell findings table with filters, sort, SHAP explanations, priority bands |
| **Code Viewer** | Monaco editor with line-level smell highlighting |
| **Correlations** | Correlation matrix heatmap, hotspot files, co-occurring smell pairs |
| **Energy** | CPU/memory time-series, phase pie chart, energy-per-smell bar chart |
| **Performance** | Pipeline phase timeline (parsing → detection → ML → refactoring) |
| **Refactoring** | Side-by-side before/after code preview with unified diff |
| **Coverage** | File health heatmap showing clean vs. affected lines |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/examples` | List example files |
| GET | `/api/examples/{filename}` | Get example source code |
| POST | `/api/analyze/code` | Analyze pasted code |
| POST | `/api/analyze/upload` | Analyze uploaded file(s) |
| POST | `/api/analyze/examples` | Analyze selected examples |

## Energy Measurement

- **Linux with Intel RAPL**: Direct hardware energy readings in micro-joules.
- **Windows / macOS**: Estimated via `CPU utilisation × TDP model` using `psutil`.
- Displayed metrics: Total energy (J), energy per file, energy per smell, phase breakdown.

## Tech Stack

- **Frontend**: React 18, TypeScript, Vite, TailwindCSS, Recharts, Monaco Editor, Lucide Icons
- **Backend**: Python FastAPI, psutil, Intel RAPL (Linux)
- **ML**: scikit-learn Stacking Ensemble, SHAP
