from app.main import agentic_report, app, health, report, trace


def test_api_routes_are_registered():
    routes = {route.path for route in app.routes}

    assert "/api/health" in routes
    assert "/api/trace" in routes
    assert "/api/report" in routes
    assert "/api/report/upload" in routes
    assert "/api/agentic-report" in routes
    assert "/api/agentic-report/stream" in routes


def test_health_endpoint_returns_ok():
    assert health() == {"status": "ok"}


def test_report_endpoint_returns_analysis():
    analysis = report()

    assert analysis.run_count == 5
    assert analysis.run_summaries[0].run_id == "run_004"


def test_trace_endpoint_returns_raw_points():
    points = trace()

    assert len(points) == 25
    assert points[0].scenario == "badly_parked_pull_in"


def test_agentic_endpoint_returns_synthesis():
    synthesis = agentic_report()

    assert synthesis.release_decision.startswith("Block release")
    assert synthesis.agent_steps[0].name == "Trace Analyst"
