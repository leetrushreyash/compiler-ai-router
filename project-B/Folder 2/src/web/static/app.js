const modeButtons = document.querySelectorAll(".mode-btn");
const navLinks = document.querySelectorAll(".nav-link");
const modePanels = {
  code: document.getElementById("codeMode"),
  samples: document.getElementById("samplesMode"),
};

const elements = {
  sampleList: document.getElementById("sampleList"),
  sampleCount: document.getElementById("sampleCount"),
  selectAllBtn: document.getElementById("selectAllBtn"),
  clearAllBtn: document.getElementById("clearAllBtn"),
  analyzeCodeBtn: document.getElementById("analyzeCodeBtn"),
  analyzeFilesBtn: document.getElementById("analyzeFilesBtn"),
  recommendModelBtn: document.getElementById("recommendModelBtn"),
  codeInput: document.getElementById("codeInput"),
  virtualFilename: document.getElementById("virtualFilename"),
  minConfidence: document.getElementById("minConfidence"),
  useMl: document.getElementById("useMl"),
  modelName: document.getElementById("modelName"),
  kpiFiles: document.getElementById("kpiFiles"),
  kpiTotal: document.getElementById("kpiTotal"),
  kpiHigh: document.getElementById("kpiHigh"),
  kpiMedium: document.getElementById("kpiMedium"),
  kpiLow: document.getElementById("kpiLow"),
  barHigh: document.getElementById("barHigh"),
  barMedium: document.getElementById("barMedium"),
  barLow: document.getElementById("barLow"),
  resultsBody: document.getElementById("resultsBody"),
  scanMeta: document.getElementById("scanMeta"),
  sampleItemTemplate: document.getElementById("sampleItemTemplate"),
  vulnCards: document.getElementById("vulnCards"),
  viewerSourceSelect: document.getElementById("viewerSourceSelect"),
  codeViewer: document.getElementById("codeViewer"),
  historyList: document.getElementById("historyList"),
  severityPieChart: document.getElementById("severityPieChart"),
  smellBarChart: document.getElementById("smellBarChart"),
  complexityCyclomatic: document.getElementById("complexityCyclomatic"),
  complexityLength: document.getElementById("complexityLength"),
  complexityNesting: document.getElementById("complexityNesting"),
  complexityDensity: document.getElementById("complexityDensity"),
  riskAverage: document.getElementById("riskAverage"),
  riskMaximum: document.getElementById("riskMaximum"),
  explainWhy: document.getElementById("explainWhy"),
  explainTrigger: document.getElementById("explainTrigger"),
  explainTokens: document.getElementById("explainTokens"),
  explainReachability: document.getElementById("explainReachability"),
  agentModelTitle: document.getElementById("agentModelTitle"),
  agentModelReason: document.getElementById("agentModelReason"),
  agentSuggestions: document.getElementById("agentSuggestions"),
};

const storageKey = "code-smell-scan-history-v1";
let sampleFiles = [];
let currentIssues = [];
let currentSourcesData = [];
let historyItems = [];
let severityPie = null;
let smellBar = null;
let lastModelRecommendation = null;

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function setActiveMode(mode) {
  modeButtons.forEach((btn) => btn.classList.toggle("active", btn.dataset.mode === mode));
  Object.entries(modePanels).forEach(([name, panel]) => {
    panel.classList.toggle("active", name === mode);
  });
}

function activateNavByHash() {
  const hash = window.location.hash || "#section-dashboard";
  navLinks.forEach((link) => {
    link.classList.toggle("active", link.getAttribute("href") === hash);
  });
}

modeButtons.forEach((button) => {
  button.addEventListener("click", () => setActiveMode(button.dataset.mode));
});

navLinks.forEach((link) => {
  link.addEventListener("click", () => {
    navLinks.forEach((item) => item.classList.remove("active"));
    link.classList.add("active");
  });
});

window.addEventListener("hashchange", activateNavByHash);

function getSettings() {
  return {
    min_confidence: Number(elements.minConfidence.value || 0.7),
    use_ml: elements.useMl.checked,
    model_name: elements.modelName.value,
  };
}

function renderModelRecommendation(recommendation = null, selectedModel = null, applyToSelect = false) {
  const fallbackActions = [
    "Paste code and click Suggest best model to preview the agent choice.",
    "Run the scan to see the recommendation applied to the findings.",
    "Use the explainability panel to inspect each flagged line.",
  ];

  if (!recommendation) {
    elements.agentModelTitle.textContent = "Auto-select model";
    elements.agentModelReason.textContent = "Paste code and the frontend will choose the best ML model from the code profile.";
    elements.agentSuggestions.innerHTML = fallbackActions.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
    lastModelRecommendation = null;
    return;
  }

  const recommendedModel = recommendation.recommended_model || selectedModel || "auto";
  const chosenModel = selectedModel || recommendation.selected_model || recommendedModel;
  const confidence = recommendation.confidence !== undefined ? `${Math.round(Number(recommendation.confidence) * 100)}%` : "";
  const selectedText = chosenModel && chosenModel !== recommendedModel ? ` Selected for this scan: ${chosenModel}.` : "";

  elements.agentModelTitle.textContent = `Recommended ${recommendedModel}${confidence ? ` (${confidence})` : ""}`;
  elements.agentModelReason.textContent = `${recommendation.reason || "The code profile supports this model."}${selectedText}`;

  const actions = Array.isArray(recommendation.agentic_actions) && recommendation.agentic_actions.length
    ? recommendation.agentic_actions
    : fallbackActions;

  elements.agentSuggestions.innerHTML = actions
    .map((item) => `<li>${escapeHtml(item)}</li>`)
    .join("");

  if (applyToSelect) {
    elements.modelName.value = recommendedModel;
  }

  lastModelRecommendation = recommendation;
}

async function requestModelRecommendation(applyToSelect = false) {
  const code = elements.codeInput.value;
  const filename = elements.virtualFilename.value.trim() || "inline_input.py";

  if (!code.trim()) {
    alert("Paste code before asking for a model recommendation.");
    return null;
  }

  const data = await callApi("/api/recommend-model", {
    code,
    filename,
  });

  renderModelRecommendation(data, data.recommended_model, applyToSelect);
  return data;
}

function renderSampleFiles() {
  elements.sampleList.innerHTML = "";

  if (!sampleFiles.length) {
    elements.sampleList.innerHTML = "<p style='padding:10px;margin:0;'>No sample files found.</p>";
    return;
  }

  sampleFiles.forEach((file) => {
    const fragment = elements.sampleItemTemplate.content.cloneNode(true);
    const label = fragment.querySelector(".sample-item");
    const checkbox = fragment.querySelector(".sample-checkbox");
    const name = fragment.querySelector(".sample-name");
    const meta = fragment.querySelector(".sample-meta");
    const preview = fragment.querySelector(".sample-preview");

    checkbox.value = file.name;
    name.textContent = file.name;
    meta.textContent = `${file.relative_path} | ${file.line_count} lines`;
    preview.textContent = file.preview || "(no preview)";
    label.title = file.relative_path;

    elements.sampleList.appendChild(fragment);
  });

  elements.sampleCount.textContent = String(sampleFiles.length);
}

function selectedFiles() {
  return Array.from(document.querySelectorAll(".sample-checkbox:checked")).map((item) => item.value);
}

function setButtonLoading(button, loadingText, isLoading) {
  if (isLoading) {
    button.dataset.originalText = button.textContent;
    button.textContent = loadingText;
    button.disabled = true;
  } else {
    button.textContent = button.dataset.originalText || button.textContent;
    button.disabled = false;
  }
}

function updateDashboard(summary, sources = []) {
  const severitySummary = summary.severity_summary || {};
  const high = severitySummary.HIGH || 0;
  const medium = severitySummary.MEDIUM || 0;
  const low = severitySummary.LOW || 0;
  const total = summary.total_issues || 0;

  elements.kpiFiles.textContent = String(summary.files_analyzed || 0);
  elements.kpiTotal.textContent = String(total);
  elements.kpiHigh.textContent = String(high);
  elements.kpiMedium.textContent = String(medium);
  elements.kpiLow.textContent = String(low);

  const denominator = Math.max(total, 1);
  elements.barHigh.style.width = `${(high / denominator) * 100}%`;
  elements.barMedium.style.width = `${(medium / denominator) * 100}%`;
  elements.barLow.style.width = `${(low / denominator) * 100}%`;

  const sourcePreview = sources.length ? ` Sources: ${sources.slice(0, 3).join(", ")}${sources.length > 3 ? "..." : ""}` : "";
  elements.scanMeta.textContent = `Scan finished in ${summary.scan_duration_ms}ms.${sourcePreview}`;

  const complexitySummary = summary.complexity_summary || {};
  const riskSummary = summary.risk_summary || {};
  elements.complexityCyclomatic.textContent = Number(complexitySummary.avg_cyclomatic_complexity || 0).toFixed(2);
  elements.complexityLength.textContent = Number(complexitySummary.avg_function_length || 0).toFixed(2);
  elements.complexityNesting.textContent = Number(complexitySummary.avg_nesting_depth || 0).toFixed(2);
  elements.complexityDensity.textContent = Number(complexitySummary.avg_issue_density || 0).toFixed(4);
  elements.riskAverage.textContent = Number(riskSummary.avg_risk_score || 0).toFixed(2);
  elements.riskMaximum.textContent = Number(riskSummary.max_risk_score || 0).toFixed(2);
}

function destroyChart(instance) {
  if (instance && typeof instance.destroy === "function") {
    instance.destroy();
  }
}

function renderCharts(summary) {
  if (!window.Chart) {
    return;
  }

  const severity = summary.severity_summary || {};
  const typeSummary = summary.type_summary || {};

  destroyChart(severityPie);
  destroyChart(smellBar);

  severityPie = new Chart(elements.severityPieChart, {
    type: "pie",
    data: {
      labels: ["HIGH", "MEDIUM", "LOW"],
      datasets: [
        {
          data: [severity.HIGH || 0, severity.MEDIUM || 0, severity.LOW || 0],
          backgroundColor: ["#c7392f", "#936f00", "#197f53"],
          borderColor: "#ffffff",
          borderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: "bottom" },
      },
    },
  });

  const smellEntries = Object.entries(typeSummary).sort((a, b) => b[1] - a[1]).slice(0, 8);
  smellBar = new Chart(elements.smellBarChart, {
    type: "bar",
    data: {
      labels: smellEntries.map(([label]) => label),
      datasets: [
        {
          label: "Occurrences",
          data: smellEntries.map(([, value]) => value),
          backgroundColor: "#3d7af0",
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        y: { beginAtZero: true, ticks: { precision: 0 } },
      },
      plugins: {
        legend: { display: false },
      },
    },
  });
}

function renderVulnerabilityCards(typeSummary = {}) {
  const entries = Object.entries(typeSummary).sort((a, b) => b[1] - a[1]);
  if (!entries.length) {
    elements.vulnCards.innerHTML = "<div class='vuln-card'><div class='vuln-title'>No vulnerabilities</div><div class='vuln-count'>0</div></div>";
    return;
  }

  elements.vulnCards.innerHTML = entries
    .map(([type, count]) => {
      return `
        <article class="vuln-card">
          <div class="vuln-title">${escapeHtml(type)}</div>
          <div class="vuln-count">${count}</div>
        </article>
      `;
    })
    .join("");
}

function renderIssues(issues) {
  if (!issues.length) {
    elements.resultsBody.innerHTML = "<tr class='empty-row'><td colspan='8'>No issues found for this scan.</td></tr>";
    return;
  }

  elements.resultsBody.innerHTML = issues
    .map((issue, index) => {
      const confidence = `${Math.round((issue.confidence || 0) * 100)}%`;
      const severity = escapeHtml(issue.severity || "INFO");
      const riskScore = Number(issue.risk_score || 0).toFixed(2);
      const type = escapeHtml(issue.type || "unknown");
      const file = escapeHtml(issue.file || "unknown");
      const line = escapeHtml(issue.line || "-");
      const trigger = escapeHtml(issue.trigger_pattern || "-");
      const description = escapeHtml(issue.description || "-");

      return `
        <tr data-index="${index}">
          <td><span class="sev-pill sev-${severity}">${severity}</span></td>
          <td>${riskScore}</td>
          <td>${type}</td>
          <td>${file}</td>
          <td>${line}</td>
          <td>${trigger}</td>
          <td>${confidence}</td>
          <td>${description}</td>
        </tr>
      `;
    })
    .join("");

  elements.resultsBody.querySelectorAll("tr[data-index]").forEach((row) => {
    row.addEventListener("click", () => {
      const idx = Number(row.getAttribute("data-index"));
      renderExplainability(issues[idx]);
    });
  });

  renderExplainability(issues[0]);
}

function renderExplainability(issue) {
  if (!issue) {
    elements.explainWhy.textContent = "Select a finding row to inspect explanation.";
    elements.explainTrigger.textContent = "-";
    elements.explainTokens.textContent = "-";
    elements.explainReachability.textContent = "-";
    return;
  }

  elements.explainWhy.textContent = issue.why_flagged || issue.description || "-";
  elements.explainTrigger.textContent = issue.trigger_pattern || "-";
  const tokens = Array.isArray(issue.matched_tokens) ? issue.matched_tokens.join(", ") : "-";
  elements.explainTokens.textContent = tokens || "-";
  const reach = issue.reachability_factor !== undefined ? Number(issue.reachability_factor).toFixed(2) : "-";
  elements.explainReachability.textContent = reach;
}

function getIssuesBySource(sourceName) {
  return currentIssues.filter((issue) => issue.file === sourceName);
}

function severityClass(severity) {
  if (severity === "HIGH") {
    return "sev-high";
  }
  if (severity === "MEDIUM") {
    return "sev-medium";
  }
  return "sev-low";
}

function severityRank(severity) {
  if (severity === "HIGH") {
    return 3;
  }
  if (severity === "MEDIUM") {
    return 2;
  }
  if (severity === "LOW") {
    return 1;
  }
  return 0;
}

function renderCodeViewer(sourceName) {
  const sourceEntry = currentSourcesData.find((item) => item.source === sourceName);
  if (!sourceEntry) {
    elements.codeViewer.innerHTML = "";
    return;
  }

  const lineSeverity = {};
  getIssuesBySource(sourceName).forEach((issue) => {
    const line = Number(issue.line || 0);
    if (line <= 0) {
      return;
    }

    const current = lineSeverity[line];
    const incoming = issue.severity || "LOW";
    if (!current || severityRank(incoming) > severityRank(current)) {
      lineSeverity[line] = incoming;
    }
  });

  const lines = String(sourceEntry.code || "").split("\n");
  elements.codeViewer.innerHTML = lines
    .map((lineText, idx) => {
      const lineNo = idx + 1;
      const sev = lineSeverity[lineNo];
      const className = sev ? ` ${severityClass(sev)}` : "";
      return `
        <div class="code-line${className}">
          <span class="line-no">${lineNo}</span>
          <span class="line-code">${escapeHtml(lineText || " ")}</span>
        </div>
      `;
    })
    .join("");
}

function refreshViewerSourceOptions() {
  elements.viewerSourceSelect.innerHTML = "";
  if (!currentSourcesData.length) {
    elements.viewerSourceSelect.innerHTML = "<option value=''>No source loaded</option>";
    elements.codeViewer.innerHTML = "";
    return;
  }

  currentSourcesData.forEach((source) => {
    const option = document.createElement("option");
    option.value = source.source;
    option.textContent = source.source;
    elements.viewerSourceSelect.appendChild(option);
  });

  renderCodeViewer(currentSourcesData[0].source);
}

elements.viewerSourceSelect.addEventListener("change", (event) => {
  renderCodeViewer(event.target.value);
});

function pushHistory(summary, sources) {
  const entry = {
    timestamp: new Date().toISOString(),
    files: summary.files_analyzed || 0,
    total: summary.total_issues || 0,
    high: summary.severity_summary?.HIGH || 0,
    medium: summary.severity_summary?.MEDIUM || 0,
    low: summary.severity_summary?.LOW || 0,
    sources: sources || [],
  };

  historyItems = [entry, ...historyItems].slice(0, 12);
  try {
    localStorage.setItem(storageKey, JSON.stringify(historyItems));
  } catch (error) {
    // Keep in-memory history if storage fails.
  }

  renderHistory();
}

function renderHistory() {
  if (!historyItems.length) {
    elements.historyList.innerHTML = "<p class='empty-history'>No scans yet.</p>";
    return;
  }

  elements.historyList.innerHTML = historyItems
    .map((item) => {
      const when = new Date(item.timestamp).toLocaleString();
      const sources = (item.sources || []).slice(0, 2).join(", ");
      return `
        <article class="history-item">
          <strong>${item.total} issues across ${item.files} file(s)</strong>
          <small>${when} | HIGH ${item.high} | MEDIUM ${item.medium} | LOW ${item.low}</small>
          <small>${escapeHtml(sources)}${(item.sources || []).length > 2 ? " ..." : ""}</small>
        </article>
      `;
    })
    .join("");
}

function loadHistory() {
  try {
    const raw = localStorage.getItem(storageKey);
    historyItems = raw ? JSON.parse(raw) : [];
  } catch (error) {
    historyItems = [];
  }

  renderHistory();
}

function applyAnalysisData(data) {
  const summary = data.summary || { severity_summary: {}, type_summary: {} };
  const sources = data.sources || [];
  currentIssues = data.issues || [];
  currentSourcesData = data.sources_data || [];

  updateDashboard(summary, sources);
  renderVulnerabilityCards(summary.type_summary || {});
  renderCharts(summary);
  renderIssues(currentIssues);
  refreshViewerSourceOptions();
  pushHistory(summary, sources);
  renderModelRecommendation(data.model_recommendation || null, data.selected_model || null, false);

  window.location.hash = "#section-dashboard";
  activateNavByHash();
}

async function callApi(path, payload) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Unknown error");
  }

  return data;
}

async function loadSampleFiles() {
  const response = await fetch("/api/test-files");
  const data = await response.json();
  sampleFiles = data.files || [];
  renderSampleFiles();
}

elements.analyzeCodeBtn.addEventListener("click", async () => {
  const code = elements.codeInput.value;
  const filename = elements.virtualFilename.value.trim() || "inline_input.py";

  if (!code.trim()) {
    alert("Paste code before running analysis.");
    return;
  }

  setButtonLoading(elements.analyzeCodeBtn, "Analyzing...", true);
  try {
    const data = await callApi("/api/analyze/code", {
      code,
      filename,
      ...getSettings(),
    });

    applyAnalysisData(data);
  } catch (error) {
    alert(error.message);
  } finally {
    setButtonLoading(elements.analyzeCodeBtn, "", false);
  }
});

elements.analyzeFilesBtn.addEventListener("click", async () => {
  const files = selectedFiles();
  if (!files.length) {
    alert("Select at least one sample file.");
    return;
  }

  setButtonLoading(elements.analyzeFilesBtn, "Scanning files...", true);
  try {
    const data = await callApi("/api/analyze/files", {
      files,
      ...getSettings(),
    });

    applyAnalysisData(data);
  } catch (error) {
    alert(error.message);
  } finally {
    setButtonLoading(elements.analyzeFilesBtn, "", false);
  }
});

elements.recommendModelBtn.addEventListener("click", async () => {
  setButtonLoading(elements.recommendModelBtn, "Thinking...", true);
  try {
    await requestModelRecommendation(true);
  } catch (error) {
    alert(error.message);
  } finally {
    setButtonLoading(elements.recommendModelBtn, "", false);
  }
});

elements.selectAllBtn.addEventListener("click", () => {
  document.querySelectorAll(".sample-checkbox").forEach((checkbox) => {
    checkbox.checked = true;
  });
});

elements.clearAllBtn.addEventListener("click", () => {
  document.querySelectorAll(".sample-checkbox").forEach((checkbox) => {
    checkbox.checked = false;
  });
});

loadSampleFiles().catch((error) => {
  elements.sampleList.innerHTML = `<p style='padding:10px;margin:0;color:#a40000;'>Failed to load samples: ${escapeHtml(error.message)}</p>`;
});

loadHistory();
renderModelRecommendation(null);
activateNavByHash();
