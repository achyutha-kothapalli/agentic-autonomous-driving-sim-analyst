# Agentic Autonomous Driving Simulation Analyst

A production style AI application for analyzing autonomous driving simulation traces and turning safety signals into agentic release recommendations.

The project focuses on a [Scenic](https://scenic-lang.org/) inspired validation scenario: a badly parked vehicle begins moving into the ego lane while the ego vehicle approaches. The first version uses a small example trace so the app can run locally without a heavyweight simulator.

## Project Goals

- Analyze autonomous driving simulation traces.
- Compute safety metrics such as time-to-collision, obstacle clearance, lane deviation, braking behavior, collision rate, and intervention rate.
- Rank risky simulation runs for engineering review.
- Generate governance aware validation recommendations.
- Provide a clear path from deterministic analysis to optional OpenAI or AWS Bedrock synthesis.

## Planned Phases

1. Project skeleton and local development setup.
2. Simulation trace data model and deterministic safety analysis.
3. FastAPI backend for production style APIs.
4. Browser dashboard with separated HTML, CSS, and JavaScript.
5. Agentic synthesis pipeline with local fallback.
6. Optional OpenAI and AWS Bedrock provider integrations.
7. Tests, CI, documentation, and portfolio polish.

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

The runnable application code is added phase by phase.

## Portfolio Positioning

This project demonstrates applied AI engineering for mobility validation: domain specific data analysis, production API design, agentic process decomposition, human-AI handoff, and governance aware decision support.
