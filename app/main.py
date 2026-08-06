from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.analyzer import analyze_trace, load_trace_points
from app.models import AnalysisReport, TracePoint


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
    return analyze_trace(load_trace_points())
