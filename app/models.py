from pydantic import BaseModel, Field


class TracePoint(BaseModel):
    run_id: str
    scenario: str
    time_s: float = Field(ge=0)
    ego_speed_mps: float = Field(ge=0)
    ego_lane_offset_m: float
    obstacle_distance_m: float = Field(ge=0)
    obstacle_lateral_offset_m: float
    obstacle_speed_mps: float = Field(ge=0)
    braking: bool
    collision: bool
    intervention: bool


class RunSummary(BaseModel):
    run_id: str
    scenario: str
    min_time_to_collision_s: float | None
    min_obstacle_distance_m: float
    max_lane_deviation_m: float
    brake_events: int
    interventions: int
    collision: bool
    risk_score: int
    risk_level: str
    primary_findings: list[str]


class AnalysisReport(BaseModel):
    scenario: str
    source: str
    run_count: int
    collision_rate: float
    intervention_rate: float
    average_risk_score: float
    top_risks: list[str]
    recommendations: list[str]
    governance_checks: list[str]
    run_summaries: list[RunSummary]


class AgentStep(BaseModel):
    name: str
    role: str
    output: list[str]


class AgenticReport(BaseModel):
    provider: str
    release_decision: str
    executive_summary: str
    agent_steps: list[AgentStep]
    process_architecture: list[str]
    human_ai_handoff: list[str]
    next_actions: list[str]


class HistoryItem(BaseModel):
    id: int
    created_at: str
    source: str
    scenario: str
    run_count: int
    collision_rate: float
    average_risk_score: float
    release_decision: str


class ScenarioVariant(BaseModel):
    name: str
    priority: str
    rationale: str
    parameter_changes: list[str]
    acceptance_criteria: list[str]
