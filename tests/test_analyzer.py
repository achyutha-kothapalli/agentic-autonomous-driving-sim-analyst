from app.analyzer import analyze_trace, load_trace_points, load_trace_points_from_csv_text


def test_sample_trace_produces_ranked_report():
    report = analyze_trace(load_trace_points())

    assert report.run_count == 5
    assert report.collision_rate == 0.2
    assert report.intervention_rate == 0.4
    assert report.run_summaries[0].run_id == "run_004"
    assert report.run_summaries[0].risk_level == "critical"


def test_uploaded_trace_text_can_be_analyzed():
    csv_text = """run_id,scenario,time_s,ego_speed_mps,ego_lane_offset_m,obstacle_distance_m,obstacle_lateral_offset_m,obstacle_speed_mps,braking,collision,intervention
run_x,upload_case,0,8.0,0.0,20.0,1.0,0.0,false,false,false
run_x,upload_case,1,7.0,0.1,12.0,0.8,0.0,true,false,false
"""
    report = analyze_trace(load_trace_points_from_csv_text(csv_text), source="Uploaded unit test trace")

    assert report.source == "Uploaded unit test trace"
    assert report.run_count == 1
    assert report.scenario == "upload_case"


def test_uploaded_trace_requires_expected_columns():
    csv_text = "run_id,scenario,time_s\nrun_x,upload_case,0\n"

    try:
        load_trace_points_from_csv_text(csv_text)
    except ValueError as exc:
        assert "Missing required CSV columns" in str(exc)
    else:
        raise AssertionError("Expected missing column validation to fail")


def test_governance_reacts_to_safety_events():
    report = analyze_trace(load_trace_points())

    assert any("auditable exception" in check for check in report.governance_checks)
    assert any("Block release" in item for item in report.recommendations)


def test_lowest_risk_run_stays_inside_safety_envelope():
    report = analyze_trace(load_trace_points())
    lowest_risk = report.run_summaries[-1]

    assert lowest_risk.run_id == "run_005"
    assert lowest_risk.risk_level == "low"
