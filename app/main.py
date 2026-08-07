from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from app.agentic import build_agentic_report, stream_agentic_report
from app.analyzer import analyze_trace, load_trace_points, load_trace_points_from_csv_text
from app.models import AgenticReport, AnalysisReport, TracePoint


STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="Agentic Autonomous Driving Simulation Analyst",
    description="API for autonomous driving simulation trace analysis.",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/trace", response_model=list[TracePoint])
def trace() -> list[TracePoint]:
    return load_trace_points()


@app.get("/api/report", response_model=AnalysisReport)
def report() -> AnalysisReport:
    return analyze_trace(load_trace_points(), source="Scenic inspired parked vehicle pull-in scenario")


@app.post("/api/report/upload", response_model=AnalysisReport)
async def uploaded_report(file: UploadFile = File(...)) -> AnalysisReport:
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Upload a CSV file.")
    try:
        content = await file.read()
        text = content.decode("utf-8-sig")
        points = load_trace_points_from_csv_text(text, source_name=f"Uploaded file: {file.filename}")
        return analyze_trace(points, source=f"Uploaded file: {file.filename}")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded.") from exc
    except (ValueError, ValidationError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/agentic-report", response_model=AgenticReport)
def agentic_report() -> AgenticReport:
    return build_agentic_report(report())


@app.get("/api/agentic-report/stream")
def agentic_report_stream() -> StreamingResponse:
    synthesis = build_agentic_report(report())
    return StreamingResponse(stream_agentic_report(synthesis), media_type="text/plain")
