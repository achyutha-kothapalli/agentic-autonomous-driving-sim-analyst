const metricLabels = [
  ["run_count", "Simulation Runs"],
  ["collision_rate", "Collision Rate"],
  ["intervention_rate", "Intervention Rate"],
  ["average_risk_score", "Average Risk"],
];

function pct(value) {
  return `${Math.round(value * 100)}%`;
}

function renderList(target, items) {
  document.getElementById(target).innerHTML = items.map((item) => `<li>${item}</li>`).join("");
}

function renderMetrics(report) {
  document.getElementById("metrics").innerHTML = metricLabels.map(([key, label]) => {
    const value = key.includes("rate") ? pct(report[key]) : report[key];
    return `<article class="metric"><span>${label}</span><strong>${value}</strong></article>`;
  }).join("");
}

function renderRuns(report) {
  document.getElementById("runs").innerHTML = report.run_summaries.map((run) => `
    <article class="run">
      <div>
        <h3>${run.run_id}</h3>
        <dl>
          <div><dt>Risk score</dt><dd>${run.risk_score}</dd></div>
          <div><dt>Min TTC</dt><dd>${run.min_time_to_collision_s ?? "n/a"}s</dd></div>
          <div><dt>Min distance</dt><dd>${run.min_obstacle_distance_m}m</dd></div>
          <div><dt>Max lane dev.</dt><dd>${run.max_lane_deviation_m}m</dd></div>
          <div><dt>Brake events</dt><dd>${run.brake_events}</dd></div>
          <div><dt>Interventions</dt><dd>${run.interventions}</dd></div>
        </dl>
        <ul>${run.primary_findings.map((item) => `<li>${item}</li>`).join("")}</ul>
      </div>
      <span class="badge ${run.risk_level}">${run.risk_level}</span>
    </article>
  `).join("");
}

function renderSynthesis(synthesis) {
  document.getElementById("synthesis").innerHTML = `
    <span class="provider">${synthesis.provider}</span>
    <p class="decision">${synthesis.release_decision}</p>
    <p>${synthesis.executive_summary}</p>
    <h3>Agent steps</h3>
    <ul>${synthesis.agent_steps.map((step) => `<li>${step.name}: ${step.role}</li>`).join("")}</ul>
    <h3>Human-AI handoff</h3>
    <ul>${synthesis.human_ai_handoff.map((item) => `<li>${item}</li>`).join("")}</ul>
  `;
}

function renderReport(report, synthesis) {
  renderMetrics(report);
  renderRuns(report);
  renderSynthesis(synthesis);
  renderList("risks", report.top_risks);
  renderList("recommendations", report.recommendations);
  renderList("governance", report.governance_checks);
}

async function loadSampleDashboard() {
  const [reportResponse, synthesisResponse] = await Promise.all([
    fetch("/api/report"),
    fetch("/api/agentic-report"),
  ]);
  const report = await reportResponse.json();
  const synthesis = await synthesisResponse.json();

  document.getElementById("source-label").textContent = "Using bundled sample trace.";
  renderReport(report, synthesis);
}

async function analyzeUploadedFile(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch("/api/report/upload", {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Upload failed.");
  }
  const report = await response.json();
  const synthesis = localSynthesisFromReport(report);

  document.getElementById("source-label").textContent = `Using uploaded file: ${file.name}`;
  renderReport(report, synthesis);
}

function localSynthesisFromReport(report) {
  const worstRun = report.run_summaries[0];
  const releaseDecision = report.collision_rate > 0
    ? "Block release until collision runs are reviewed"
    : "Review uploaded trace before release discussion";

  return {
    provider: "browser local synthesis",
    release_decision: releaseDecision,
    executive_summary: `${report.scenario} has ${report.run_count} simulation runs. The highest risk run is ${worstRun.run_id} with a ${worstRun.risk_level} risk level and a risk score of ${worstRun.risk_score}.`,
    agent_steps: [
      { name: "Trace Analyst", role: "Summarize uploaded simulation data." },
      { name: "Safety Risk", role: "Identify risk signals from the uploaded trace." },
      { name: "Governance", role: "Prepare traceability and release checks." },
      { name: "Release Review", role: "Support the human decision owner." },
    ],
    human_ai_handoff: [
      "The system ranks the uploaded runs; the human safety engineer owns the final release decision.",
      "Validation engineers should review the highest risk uploaded run before accepting the analysis.",
    ],
  };
}

document.getElementById("upload-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = document.getElementById("trace-file").files[0];
  if (!file) {
    document.getElementById("source-label").textContent = "Choose a CSV file first.";
    return;
  }
  try {
    await analyzeUploadedFile(file);
  } catch (error) {
    document.getElementById("source-label").textContent = error.message;
  }
});

document.getElementById("reset-sample").addEventListener("click", () => {
  document.getElementById("trace-file").value = "";
  loadSampleDashboard();
});

loadSampleDashboard().catch((error) => {
  document.querySelector("main").innerHTML = `<section class="panel"><h2>Unable to load report</h2><p>${error}</p></section>`;
});
