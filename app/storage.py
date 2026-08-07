import json
import sqlite3
from pathlib import Path

from app.agentic import build_agentic_report
from app.models import AnalysisReport, HistoryItem


DB_PATH = Path(__file__).resolve().parent.parent / "data" / "analysis_history.db"


def save_analysis(report: AnalysisReport, db_path: Path = DB_PATH) -> HistoryItem:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    synthesis = build_agentic_report(report)
    with sqlite3.connect(db_path) as connection:
        _ensure_schema(connection)
        cursor = connection.execute(
            """
            INSERT INTO analysis_history (
                source,
                scenario,
                run_count,
                collision_rate,
                average_risk_score,
                release_decision,
                report_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report.source,
                report.scenario,
                report.run_count,
                report.collision_rate,
                report.average_risk_score,
                synthesis.release_decision,
                report.model_dump_json(),
            ),
        )
        connection.commit()
        item_id = int(cursor.lastrowid)
        row = connection.execute(
            """
            SELECT id, created_at, source, scenario, run_count, collision_rate, average_risk_score, release_decision
            FROM analysis_history
            WHERE id = ?
            """,
            (item_id,),
        ).fetchone()
    return _history_item(row)


def list_history(limit: int = 10, db_path: Path = DB_PATH) -> list[HistoryItem]:
    if not db_path.exists():
        return []
    with sqlite3.connect(db_path) as connection:
        _ensure_schema(connection)
        rows = connection.execute(
            """
            SELECT id, created_at, source, scenario, run_count, collision_rate, average_risk_score, release_decision
            FROM analysis_history
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [_history_item(row) for row in rows]


def load_report(item_id: int, db_path: Path = DB_PATH) -> AnalysisReport | None:
    if not db_path.exists():
        return None
    with sqlite3.connect(db_path) as connection:
        _ensure_schema(connection)
        row = connection.execute(
            "SELECT report_json FROM analysis_history WHERE id = ?",
            (item_id,),
        ).fetchone()
    if row is None:
        return None
    return AnalysisReport.model_validate(json.loads(row[0]))


def _ensure_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            source TEXT NOT NULL,
            scenario TEXT NOT NULL,
            run_count INTEGER NOT NULL,
            collision_rate REAL NOT NULL,
            average_risk_score REAL NOT NULL,
            release_decision TEXT NOT NULL,
            report_json TEXT NOT NULL
        )
        """
    )


def _history_item(row) -> HistoryItem:
    return HistoryItem(
        id=row[0],
        created_at=row[1],
        source=row[2],
        scenario=row[3],
        run_count=row[4],
        collision_rate=row[5],
        average_risk_score=row[6],
        release_decision=row[7],
    )
