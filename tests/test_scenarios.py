from app.analyzer import analyze_trace, load_trace_points
from app.scenarios import suggest_scenario_variants


def test_scenario_variants_prioritize_collision_and_regression_cases():
    report = analyze_trace(load_trace_points(), source="test trace")

    variants = suggest_scenario_variants(report)

    names = [variant.name for variant in variants]
    assert "Increase obstacle pull-in aggressiveness" in names
    assert any(name.startswith("Build regression pack around") for name in names)
    assert variants[0].priority == "high"


def test_scenario_variants_have_actionable_acceptance_criteria():
    report = analyze_trace(load_trace_points(), source="test trace")

    variants = suggest_scenario_variants(report)

    assert all(variant.parameter_changes for variant in variants)
    assert all(variant.acceptance_criteria for variant in variants)
    assert all(variant.rationale for variant in variants)
