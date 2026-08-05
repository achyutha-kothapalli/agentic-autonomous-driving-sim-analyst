import csv
from collections import Counter, defaultdict
from pathlib import Path

from app.models import AnalysisReport, RunSummary, TracePoint


DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "scenic_badly_parked_pull_in.csv"


def load_trace_points(path: Path = DATA_PATH) -> list[TracePoint]:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return [
            TracePoint(
                run_id=row["run_id"],
                scenario=row["scenario"],
                time_s=float(row["time_s"]),
                ego_speed_mps=float(row["ego_speed_mps"]),
                ego_lane_offset_m=float(row["ego_lane_offset_m"]),
                obstacle_distance_m=float(row["obstacle_distance_m"]),
                obstacle_lateral_offset_m=float(row["obstacle_lateral_offset_m"]),
                obstacle_speed_mps=float(row["obstacle_speed_mps"]),
                braking=_to_bool(row["braking"]),
                collision=_to_bool(row["collision"]),
                intervention=_to_bool(row["intervention"]),
            )
            for row in reader
        ]


def analyze_trace(points: list[TracePoint]) -> AnalysisReport:
    if not points:
        raise ValueError("No simulation trace points supplied.")

    grouped: dict[str, list[TracePoint]] = defaultdict(list)
    for point in points:
        grouped[point.run_id].append(point)

    summaries = [_summarize_run(run_id, run_points) for run_id, run_points in grouped.items()]
    summaries.sort(key=lambda summary: summary.risk_score, reverse=True)

    scenario = points[0].scenario
    run_count = len(summaries)
    collision_rate = sum(1 for summary in summaries if summary.collision) / run_count
    intervention_rate = sum(1 for summary in summaries if summary.interventions > 0) / run_count
    average_risk = sum(summary.risk_score for summary in summaries) / run_count
    top_risks = _rank_findings(summaries)

    return AnalysisReport(
        scenario=scenario,
        source="Scenic inspired parked vehicle pull-in scenario",
        run_count=run_count,
        collision_rate=round(collision_rate, 3),
        intervention_rate=round(intervention_rate, 3),
        average_risk_score=round(average_risk, 1),
        top_risks=top_risks,
        recommendations=_recommend(top_risks, collision_rate, intervention_rate),
        governance_checks=_governance_checks(collision_rate, intervention_rate),
        run_summaries=summaries,
    )


def _summarize_run(run_id: str, points: list[TracePoint]) -> RunSummary:
    ordered = sorted(points, key=lambda point: point.time_s)
    min_distance = min(point.obstacle_distance_m for point in ordered)
    max_lane_deviation = max(abs(point.ego_lane_offset_m) for point in ordered)
    brake_events = _count_rising_edges([point.braking for point in ordered])
    interventions = sum(1 for point in ordered if point.intervention)
    collision = any(point.collision for point in ordered)
    min_ttc = _min_time_to_collision(ordered)

    findings = _findings(collision, min_ttc, min_distance, max_lane_deviation, interventions, brake_events)
    score = _risk_score(collision, min_ttc, min_distance, max_lane_deviation, interventions, brake_events)

    return RunSummary(
        run_id=run_id,
        scenario=ordered[0].scenario,
        min_time_to_collision_s=None if min_ttc is None else round(min_ttc, 2),
        min_obstacle_distance_m=round(min_distance, 2),
        max_lane_deviation_m=round(max_lane_deviation, 2),
        brake_events=brake_events,
        interventions=interventions,
        collision=collision,
        risk_score=score,
        risk_level=_risk_level(score),
        primary_findings=findings,
    )


def _findings(
    collision: bool,
    min_ttc: float | None,
    min_distance: float,
    max_lane_deviation: float,
    interventions: int,
    brake_events: int,
) -> list[str]:
    findings: list[str] = []
    if collision:
        findings.append("Collision occurred")
    if min_ttc is not None and min_ttc < 1.5:
        findings.append("Critical time-to-collision below 1.5s")
    if min_distance < 3.0:
        findings.append("Obstacle clearance below 3m")
    if max_lane_deviation > 0.7:
        findings.append("Lane deviation exceeded 0.7m")
    if interventions:
        findings.append("Human or safety intervention required")
    if brake_events > 1:
        findings.append("Multiple braking responses detected")
    if not findings:
        findings.append("Scenario completed inside safety envelope")
    return findings


def _min_time_to_collision(points: list[TracePoint]) -> float | None:
    values = []
    for point in points:
        closing_speed = point.ego_speed_mps - point.obstacle_speed_mps
        if closing_speed > 0 and point.obstacle_distance_m > 0:
            values.append(point.obstacle_distance_m / closing_speed)
    return min(values) if values else None


def _risk_score(
    collision: bool,
    min_ttc: float | None,
    min_distance: float,
    max_lane_deviation: float,
    interventions: int,
    brake_events: int,
) -> int:
    score = 0
    if collision:
        score += 45
    if min_ttc is not None:
        if min_ttc < 1:
            score += 30
        elif min_ttc < 1.5:
            score += 22
        elif min_ttc < 2.5:
            score += 12
    if min_distance < 2:
        score += 18
    elif min_distance < 3:
        score += 12
    elif min_distance < 5:
        score += 6
    if max_lane_deviation > 1:
        score += 12
    elif max_lane_deviation > 0.7:
        score += 8
    if interventions:
        score += min(20, 6 * interventions)
    if brake_events > 1:
        score += 5
    return min(score, 100)


def _risk_level(score: int) -> str:
    if score >= 70:
        return "critical"
    if score >= 45:
        return "high"
    if score >= 25:
        return "medium"
    return "low"


def _rank_findings(summaries: list[RunSummary]) -> list[str]:
    counter: Counter[str] = Counter()
    for summary in summaries:
        counter.update(summary.primary_findings)
    return [finding for finding, _count in counter.most_common(5)]


def _recommend(top_risks: list[str], collision_rate: float, intervention_rate: float) -> list[str]:
    recommendations = [
        "Replay high-risk runs with denser sampling around obstacle motion and ego braking decisions.",
        "Add scenario variants for obstacle pull-in timing, lateral offset, ego speed, and visibility constraints.",
    ]
    if collision_rate > 0:
        recommendations.append("Block release until collision runs have root-cause labels and mitigation evidence.")
    if intervention_rate >= 0.25:
        recommendations.append("Add a human review workflow for runs requiring safety intervention.")
    if any("time-to-collision" in risk for risk in top_risks):
        recommendations.append("Prioritize earlier intent prediction for parked-vehicle pull-in behavior.")
    return recommendations


def _governance_checks(collision_rate: float, intervention_rate: float) -> list[str]:
    checks = [
        "Record scenario seed, simulator version, map version, model version, and data lineage for every run.",
        "Separate safety-critical recommendations from automated decisions; require human approval for release gating.",
        "Track false negatives: runs rated low-risk by the analyzer but flagged by downstream validation.",
    ]
    if collision_rate > 0 or intervention_rate > 0:
        checks.append("Create an auditable exception report before promoting the driving stack.")
    return checks


def _count_rising_edges(values: list[bool]) -> int:
    count = 0
    previous = False
    for value in values:
        if value and not previous:
            count += 1
        previous = value
    return count


def _to_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y"}
