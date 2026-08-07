# Agentic Autonomous Driving Simulation Analyst

A production style AI application for analyzing autonomous driving simulation traces and turning safety signals into agentic release recommendations.

The project focuses on a [Scenic](https://scenic-lang.org/) inspired validation scenario: a badly parked vehicle begins moving into the ego lane while the ego vehicle approaches. The first version uses a small example trace so the app can run locally without a heavyweight simulator.

## What It Does Today

The app loads a small Scenic inspired trace, calculates safety metrics, ranks the riskiest simulation runs, and shows the results in a browser dashboard.

It also has a local agentic synthesis layer. That layer turns the raw analysis into a release decision, agent steps, human-AI handoff notes, governance checks, and next actions. The app works without model credentials, and can optionally use OpenAI or AWS Bedrock for the executive summary.

You can use the bundled sample trace or upload a CSV with the same schema for quick local analysis.

## Project Goals

- Analyze autonomous driving simulation traces.
- Compute safety metrics such as time-to-collision, obstacle clearance, lane deviation, braking behavior, collision rate, and intervention rate.
- Rank risky simulation runs for engineering review.
- Generate governance aware validation recommendations.
- Provide a clear path from deterministic analysis to optional OpenAI or AWS Bedrock synthesis.

## Current Features

- FastAPI backend
- Browser dashboard with separate HTML, CSS, and JavaScript
- Scenic inspired sample trace
- CSV upload for new trace files
- Deterministic safety scoring
- Local agentic synthesis
- Optional OpenAI and AWS Bedrock provider modes
- Streaming synthesis endpoint
- Pytest test suite
- GitHub Actions test workflow

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Install optional AI provider SDKs:

```powershell
python -m pip install -e ".[ai,dev]"
```

Run the tests:

```powershell
python -m pytest
```

Start the app:

```powershell
python -m uvicorn app.main:app --reload
```

Open the dashboard:

```text
http://127.0.0.1:8000
```

## API Endpoints

```text
GET /
GET /api/health
GET /api/trace
GET /api/report
POST /api/report/upload
GET /api/agentic-report
GET /api/agentic-report/stream
```

Check the API:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
Invoke-RestMethod http://127.0.0.1:8000/api/report
Invoke-RestMethod http://127.0.0.1:8000/api/agentic-report
Invoke-RestMethod http://127.0.0.1:8000/api/agentic-report/stream
```

Upload a CSV trace:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/report/upload -Method Post -Form @{ file = Get-Item .\data\scenic_badly_parked_pull_in.csv }
```

## AI Provider Modes

Local mode is the default:

```powershell
$env:AI_PROVIDER = "local"
```

OpenAI mode:

```powershell
$env:AI_PROVIDER = "openai"
$env:OPENAI_API_KEY = "your_key_here"
$env:OPENAI_MODEL = "gpt-5-nano"
```

AWS Bedrock mode:

```powershell
$env:AI_PROVIDER = "bedrock"
$env:DEFAULT_AWS_REGION = "us-east-1"
$env:BEDROCK_MODEL_ID = "amazon.nova-lite-v1:0"
```

There is a `.env.example` file with the supported settings. Keep real secrets in environment variables or a local `.env` file. Do not commit `.env`.

If a provider package, key, or cloud permission is missing, the app falls back to the local synthesis so the dashboard still works.

## Project Phases

1. Project skeleton and local development setup.
2. Simulation trace data model and deterministic safety analysis.
3. FastAPI backend for production style APIs.
4. Browser dashboard with separated HTML, CSS, and JavaScript.
5. Agentic synthesis pipeline with local fallback.
6. Optional OpenAI and AWS Bedrock provider integrations.
7. Tests, CI, documentation, and portfolio polish.

## Roadmap

- Add real Scenic generated data.
- Add CARLA or MetaDrive simulation export examples.
- Add scenario mutation suggestions.
- Add persistence for analysis history.
- Deploy the API and dashboard.

## Portfolio Positioning

This project demonstrates applied AI engineering for mobility validation: domain specific data analysis, production API design, agentic process decomposition, human-AI handoff, and governance aware decision support.
