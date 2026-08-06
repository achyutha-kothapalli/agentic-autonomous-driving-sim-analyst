from fastapi import FastAPI

from app.analyzer import analyze_trace, load_trace_points
from app.models import AnalysisReport, TracePoint


app = FastAPI(
    title="Agentic Autonomous Driving Simulation Analyst",
    description="API for autonomous driving simulation trace analysis.",
    version="0.1.0",
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/trace", response_model=list[TracePoint])
def trace() -> list[TracePoint]:
    return load_trace_points()


@app.get("/api/report", response_model=AnalysisReport)
def report() -> AnalysisReport:
    return analyze_trace(load_trace_points())
