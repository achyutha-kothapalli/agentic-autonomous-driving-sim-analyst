import json
import os

from app.models import AgentStep, AgenticReport, AnalysisReport


def build_agentic_report(report: AnalysisReport) -> AgenticReport:
    local_report = _build_local_report(report)
    provider = os.getenv("AI_PROVIDER", "local").strip().lower()

    if provider == "openai" and os.getenv("OPENAI_API_KEY"):
        return _try_openai_synthesis(report, local_report)
    if provider == "bedrock":
        return _try_bedrock_synthesis(report, local_report)
    return local_report


def stream_agentic_report(report: AgenticReport):
    yield f"provider: {report.provider}\n"
    yield f"release_decision: {report.release_decision}\n\n"
    yield "executive_summary:\n"
    yield report.executive_summary + "\n\n"

    yield "agent_steps:\n"
    for step in report.agent_steps:
        yield f"- {step.name}: {step.role}\n"
        for item in step.output:
            yield f"  - {item}\n"

    yield "\nnext_actions:\n"
    for action in report.next_actions:
        yield f"- {action}\n"


def _build_local_report(report: AnalysisReport) -> AgenticReport:
    worst_run = report.run_summaries[0]
    release_decision = _release_decision(report)

    agent_steps = [
        _trace_analyst_step(report),
        _safety_risk_step(report),
        _governance_step(report),
        _release_step(report, release_decision),
    ]

    return AgenticReport(
        provider="local deterministic synthesis",
        release_decision=release_decision,
        executive_summary=(
            f"{report.scenario} has {report.run_count} simulation runs. "
            f"The highest risk run is {worst_run.run_id} with a {worst_run.risk_level} risk level "
            f"and a risk score of {worst_run.risk_score}. "
            f"Collision rate is {report.collision_rate:.0%}, intervention rate is {report.intervention_rate:.0%}, "
            f"and the current release recommendation is {release_decision}."
        ),
        agent_steps=agent_steps,
        process_architecture=[
            "Simulation traces are loaded from Scenic style scenario data.",
            "The analyzer validates each time step and groups records by simulation run.",
            "Safety metrics are calculated for clearance, time-to-collision, lane deviation, braking, interventions, and collisions.",
            "The agentic synthesis layer turns the metric report into release, governance, and review actions.",
            "A human validation owner reviews the highest risk runs before any release decision is accepted.",
        ],
        human_ai_handoff=[
            "The system ranks and explains high risk runs; the human safety engineer owns the final release decision.",
            "The system proposes governance checks; the governance reviewer confirms evidence and traceability.",
            "The system identifies scenario gaps; validation engineers decide which new simulations to run.",
        ],
        next_actions=_next_actions(report, release_decision),
    )


def _try_openai_synthesis(report: AnalysisReport, fallback: AgenticReport) -> AgenticReport:
    try:
        from openai import OpenAI

        model = os.getenv("OPENAI_MODEL", "gpt-5-nano")
        client = OpenAI()
        response = client.chat.completions.create(
            model=model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": _synthesis_system_prompt()},
                {"role": "user", "content": _synthesis_prompt(report, fallback)},
            ],
        )
        text = response.choices[0].message.content or fallback.executive_summary
        return fallback.model_copy(
            update={
                "provider": f"openai:{model}",
                "executive_summary": text.strip(),
            }
        )
    except Exception:
        return fallback


def _try_bedrock_synthesis(report: AnalysisReport, fallback: AgenticReport) -> AgenticReport:
    try:
        import boto3

        region = os.getenv("DEFAULT_AWS_REGION", "us-east-1")
        model = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")
        client = boto3.client("bedrock-runtime", region_name=region)
        response = client.converse(
            modelId=model,
            system=[{"text": _synthesis_system_prompt()}],
            messages=[{"role": "user", "content": [{"text": _synthesis_prompt(report, fallback)}]}],
            inferenceConfig={"temperature": 0.2},
        )
        text = response["output"]["message"]["content"][0]["text"]
        return fallback.model_copy(
            update={
                "provider": f"bedrock:{model}",
                "executive_summary": text.strip(),
            }
        )
    except Exception:
        return fallback


def _synthesis_system_prompt() -> str:
    return (
        "You are an autonomous driving validation lead. Write a concise release review summary "
        "from the simulation analysis. Do not claim that real simulator execution happened unless "
        "the input explicitly says so."
    )


def _synthesis_prompt(report: AnalysisReport, fallback: AgenticReport) -> str:
    payload = {
        "analysis": report.model_dump(mode="json"),
        "local_synthesis": fallback.model_dump(mode="json"),
    }
    return (
        "Summarize the validation risk for engineering and governance stakeholders. "
        "Mention the release decision, highest risk run, main safety concerns, and human review needs.\n\n"
        + json.dumps(payload, indent=2)
    )


def _trace_analyst_step(report: AnalysisReport) -> AgentStep:
    return AgentStep(
        name="Trace Analyst",
        role="Summarize what the simulation data contains.",
        output=[
            f"Loaded {report.run_count} runs from {report.source}.",
            f"Average risk score is {report.average_risk_score}.",
            f"The highest ranked run is {report.run_summaries[0].run_id}.",
        ],
    )


def _safety_risk_step(report: AnalysisReport) -> AgentStep:
    return AgentStep(
        name="Safety Risk",
        role="Identify the safety signals that should drive engineering review.",
        output=[
            f"Collision rate is {report.collision_rate:.0%}.",
            f"Intervention rate is {report.intervention_rate:.0%}.",
            *report.top_risks[:3],
        ],
    )


def _governance_step(report: AnalysisReport) -> AgentStep:
    return AgentStep(
        name="Governance",
        role="Convert safety findings into release control checks.",
        output=report.governance_checks,
    )


def _release_step(report: AnalysisReport, release_decision: str) -> AgentStep:
    return AgentStep(
        name="Release Review",
        role="Prepare the human decision owner for the next release discussion.",
        output=[
            f"Recommended decision: {release_decision}.",
            *report.recommendations,
        ],
    )


def _release_decision(report: AnalysisReport) -> str:
    if report.collision_rate > 0:
        return "Block release until collision runs are reviewed"
    if report.intervention_rate >= 0.25:
        return "Conditional review before release"
    if report.average_risk_score >= 40:
        return "Engineering review recommended"
    return "No release blocker found in sample trace"


def _next_actions(report: AnalysisReport, release_decision: str) -> list[str]:
    actions = [
        "Review the top ranked simulation runs with the validation owner.",
        "Add scenario variants for obstacle pull-in timing, ego speed, and lateral offset.",
        "Record simulator version, scenario seed, map version, model version, and analysis date.",
    ]
    if "Block release" in release_decision:
        actions.insert(0, "Create a root-cause note for every collision run before release discussion.")
    if report.intervention_rate >= 0.25:
        actions.append("Confirm whether intervention events came from the driving stack, simulator monitor, or human override.")
    return actions
