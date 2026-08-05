from app.analyzer import analyze_trace, load_trace_points


def test_sample_trace_produces_ranked_report():
    report = analyze_trace(load_trace_points())

    assert report.run_count == 5
    assert report.collision_rate == 0.2
    assert report.intervention_rate == 0.4
    assert report.run_summaries[0].run_id == "run_004"
    assert report.run_summaries[0].risk_level == "critical"


def test_governance_reacts_to_safety_events():
    report = analyze_trace(load_trace_points())

    assert any("auditable exception" in check for check in report.governance_checks)
    assert any("Block release" in item for item in report.recommendations)


def test_lowest_risk_run_stays_inside_safety_envelope():
    report = analyze_trace(load_trace_points())
    lowest_risk = report.run_summaries[-1]

    assert lowest_risk.run_id == "run_005"
    assert lowest_risk.risk_level == "low"
