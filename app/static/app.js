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

function renderVariants(variants) {
  const target = document.getElementById("variants");
  target.innerHTML = variants.map((variant) => `
    <article class="variant">
      <div>
        <h3>${variant.name}</h3>
        <span class="priority ${variant.priority}">${variant.priority}</span>
      </div>
      <p>${variant.rationale}</p>
      <h4>Parameter changes</h4>
      <ul>${variant.parameter_changes.map((item) => `<li>${item}</li>`).join("")}</ul>
      <h4>Acceptance criteria</h4>
      <ul>${variant.acceptance_criteria.map((item) => `<li>${item}</li>`).join("")}</ul>
    </article>
  `).join("");
}

function renderReport(report, synthesis, variants = localVariantsFromReport(report)) {
  renderMetrics(report);
  renderRuns(report);
  renderSynthesis(synthesis);
  renderVariants(variants);
  renderList("risks", report.top_risks);
  renderList("recommendations", report.recommendations);
  renderList("governance", report.governance_checks);
}

async function renderHistory() {
  const response = await fetch("/api/history");
  const items = await response.json();
  const target = document.getElementById("history");
  if (items.length === 0) {
    target.innerHTML = "<p>No saved analyses yet.</p>";
    return;
  }
  target.innerHTML = items.map((item) => `
    <button class="history-item" data-history-id="${item.id}">
      <strong>${item.scenario}</strong>
      <span>${item.source}</span>
      <span>${pct(item.collision_rate)} collisions, risk ${item.average_risk_score}</span>
    </button>
  `).join("");

  target.querySelectorAll(".history-item").forEach((button) => {
    button.addEventListener("click", async () => {
      const reportResponse = await fetch(`/api/history/${button.dataset.historyId}/report`);
      const report = await reportResponse.json();
      document.getElementById("source-label").textContent = `Viewing saved analysis: ${report.source}`;
      renderReport(report, localSynthesisFromReport(report), localVariantsFromReport(report));
    });
  });
}

async function loadSampleDashboard() {
  const [reportResponse, synthesisResponse, variantsResponse] = await Promise.all([
    fetch("/api/report"),
    fetch("/api/agentic-report"),
    fetch("/api/scenario-variants"),
  ]);
  const report = await reportResponse.json();
  const synthesis = await synthesisResponse.json();
  const variants = await variantsResponse.json();

  document.getElementById("source-label").textContent = "Using bundled sample trace.";
  renderReport(report, synthesis, variants);
  renderHistory();
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
  renderReport(report, synthesis, localVariantsFromReport(report));
  renderHistory();
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

function localVariantsFromReport(report) {
  const sortedRuns = [...report.run_summaries].sort((left, right) => right.risk_score - left.risk_score);
  const variants = [];

  if (report.collision_rate > 0) {
    variants.push({
      name: "Increase obstacle pull-in aggressiveness",
      priority: "high",
      rationale: "Collision evidence indicates the planner needs harder cut-in validation before release review.",
      parameter_changes: [
        "Reduce obstacle initial distance by 20 percent.",
        "Move obstacle lateral offset closer to the ego lane center.",
        "Run the scenario at the highest observed ego speed.",
      ],
      acceptance_criteria: [
        "Zero collisions across the new variant batch.",
        "Minimum time-to-collision stays above 1.5 seconds.",
        "No manual intervention is required.",
      ],
    });
  }

  if (report.run_summaries.some((run) => run.interventions > 0)) {
    variants.push({
      name: "Replay intervention runs with sensor noise",
      priority: "high",
      rationale: "Human or safety-driver intervention means the autonomy stack needs robustness checks around the same trigger.",
      parameter_changes: [
        "Replay each intervention run with bounded perception noise.",
        "Vary braking response delay between 0.1 and 0.4 seconds.",
        "Keep the same road geometry for traceability.",
      ],
      acceptance_criteria: [
        "Intervention rate is lower than the baseline trace.",
        "Risk score does not increase for any replayed run.",
        "Planner behavior remains explainable in the review report.",
      ],
    });
  }

  if (report.run_summaries.some((run) => run.max_lane_deviation_m >= 0.6)) {
    variants.push({
      name: "Stress lane keeping during evasive response",
      priority: "medium",
      rationale: "Large lane deviation suggests the safety envelope should be tested while the ego vehicle avoids the obstacle.",
      parameter_changes: [
        "Add a narrower lane boundary for the worst lane-deviation run.",
        "Sweep ego speed around the baseline speed by plus or minus 10 percent.",
        "Keep obstacle behavior constant to isolate lane-control behavior.",
      ],
      acceptance_criteria: [
        "Maximum lane deviation remains below 0.5 meters.",
        "No collision or intervention appears in the variant.",
        "Brake events remain consistent with the original safety strategy.",
      ],
    });
  }

  if (sortedRuns.length > 0) {
    const worst = sortedRuns[0];
    variants.push({
      name: `Build regression pack around ${worst.run_id}`,
      priority: worst.risk_score < 70 ? "medium" : "high",
      rationale: "The highest-risk run should become a repeatable regression case for future model or planner changes.",
      parameter_changes: [
        `Use ${worst.run_id} as the seed trace.`,
        "Generate boundary cases around obstacle distance, ego speed, and braking delay.",
        "Label the pack with scenario, source, and baseline release decision.",
      ],
      acceptance_criteria: [
        "Regression pack is reproducible from versioned input data.",
        "Each run has a stored report and release recommendation.",
        "Any increase in risk score blocks automatic approval.",
      ],
    });
  }

  return variants.slice(0, 4);
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

document.getElementById("save-sample").addEventListener("click", async () => {
  const response = await fetch("/api/history/sample", { method: "POST" });
  const item = await response.json();
  document.getElementById("source-label").textContent = `Saved sample analysis #${item.id}.`;
  renderHistory();
});

loadSampleDashboard().catch((error) => {
  document.querySelector("main").innerHTML = `<section class="panel"><h2>Unable to load report</h2><p>${error}</p></section>`;
});
