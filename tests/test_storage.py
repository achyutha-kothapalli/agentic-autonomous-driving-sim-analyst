from app.analyzer import analyze_trace, load_trace_points
from app.storage import list_history, load_report, save_analysis


def test_save_and_list_history(tmp_path):
    db_path = tmp_path / "history.db"
    report = analyze_trace(load_trace_points())

    saved = save_analysis(report, db_path=db_path)
    history = list_history(db_path=db_path)

    assert saved.id == 1
    assert len(history) == 1
    assert history[0].source == report.source
    assert history[0].release_decision.startswith("Block release")


def test_load_saved_report(tmp_path):
    db_path = tmp_path / "history.db"
    report = analyze_trace(load_trace_points())

    saved = save_analysis(report, db_path=db_path)
    loaded = load_report(saved.id, db_path=db_path)

    assert loaded is not None
    assert loaded.run_count == report.run_count
    assert loaded.run_summaries[0].run_id == "run_004"


def test_missing_history_report_returns_none(tmp_path):
    db_path = tmp_path / "history.db"

    assert load_report(999, db_path=db_path) is None
