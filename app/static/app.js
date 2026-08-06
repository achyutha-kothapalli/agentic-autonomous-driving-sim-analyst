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

async function loadDashboard() {
  const [reportResponse, synthesisResponse] = await Promise.all([
    fetch("/api/report"),
    fetch("/api/agentic-report"),
  ]);
  const report = await reportResponse.json();
  const synthesis = await synthesisResponse.json();

  renderMetrics(report);
  renderRuns(report);
  renderSynthesis(synthesis);
  renderList("risks", report.top_risks);
  renderList("recommendations", report.recommendations);
  renderList("governance", report.governance_checks);
}

loadDashboard().catch((error) => {
  document.querySelector("main").innerHTML = `<section class="panel"><h2>Unable to load report</h2><p>${error}</p></section>`;
});
