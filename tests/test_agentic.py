from app.agentic import build_agentic_report, stream_agentic_report
from app.analyzer import analyze_trace, load_trace_points


def test_agentic_report_blocks_release_for_collision_runs():
    analysis = analyze_trace(load_trace_points())
    synthesis = build_agentic_report(analysis)

    assert synthesis.provider == "local deterministic synthesis"
    assert synthesis.release_decision == "Block release until collision runs are reviewed"
    assert len(synthesis.agent_steps) == 4
    assert any("human" in item.lower() for item in synthesis.human_ai_handoff)


def test_stream_agentic_report_contains_decision():
    analysis = analyze_trace(load_trace_points())
    synthesis = build_agentic_report(analysis)
    streamed = "".join(stream_agentic_report(synthesis))

    assert "release_decision" in streamed
    assert "Block release" in streamed


def test_openai_mode_without_key_falls_back_to_local(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    synthesis = build_agentic_report(analyze_trace(load_trace_points()))

    assert synthesis.provider == "local deterministic synthesis"


def test_unknown_provider_falls_back_to_local(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "not-a-provider")

    synthesis = build_agentic_report(analyze_trace(load_trace_points()))

    assert synthesis.provider == "local deterministic synthesis"
