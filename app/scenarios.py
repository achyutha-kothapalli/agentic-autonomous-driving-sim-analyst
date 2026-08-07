from app.models import AnalysisReport, ScenarioVariant


def suggest_scenario_variants(report: AnalysisReport) -> list[ScenarioVariant]:
    worst_runs = sorted(report.run_summaries, key=lambda run: run.risk_score, reverse=True)
    variants: list[ScenarioVariant] = []

    if report.collision_rate > 0:
        variants.append(
            ScenarioVariant(
                name="Increase obstacle pull-in aggressiveness",
                priority="high",
                rationale="Collision evidence indicates the planner needs harder cut-in validation before release review.",
                parameter_changes=[
                    "Reduce obstacle initial distance by 20 percent.",
                    "Move obstacle lateral offset closer to the ego lane center.",
                    "Run the scenario at the highest observed ego speed.",
                ],
                acceptance_criteria=[
                    "Zero collisions across the new variant batch.",
                    "Minimum time-to-collision stays above 1.5 seconds.",
                    "No manual intervention is required.",
                ],
            )
        )

    if any(run.interventions > 0 for run in report.run_summaries):
        variants.append(
            ScenarioVariant(
                name="Replay intervention runs with sensor noise",
                priority="high",
                rationale="Human or safety-driver intervention means the autonomy stack needs robustness checks around the same trigger.",
                parameter_changes=[
                    "Replay each intervention run with bounded perception noise.",
                    "Vary braking response delay between 0.1 and 0.4 seconds.",
                    "Keep the same road geometry for traceability.",
                ],
                acceptance_criteria=[
                    "Intervention rate is lower than the baseline trace.",
                    "Risk score does not increase for any replayed run.",
                    "Planner behavior remains explainable in the review report.",
                ],
            )
        )

    high_lane_runs = [run for run in report.run_summaries if run.max_lane_deviation_m >= 0.6]
    if high_lane_runs:
        variants.append(
            ScenarioVariant(
                name="Stress lane keeping during evasive response",
                priority="medium",
                rationale="Large lane deviation suggests the safety envelope should be tested while the ego vehicle avoids the obstacle.",
                parameter_changes=[
                    "Add a narrower lane boundary for the worst lane-deviation run.",
                    "Sweep ego speed around the baseline speed by plus or minus 10 percent.",
                    "Keep obstacle behavior constant to isolate lane-control behavior.",
                ],
                acceptance_criteria=[
                    "Maximum lane deviation remains below 0.5 meters.",
                    "No collision or intervention appears in the variant.",
                    "Brake events remain consistent with the original safety strategy.",
                ],
            )
        )

    if worst_runs:
        worst = worst_runs[0]
        variants.append(
            ScenarioVariant(
                name=f"Build regression pack around {worst.run_id}",
                priority="medium" if worst.risk_score < 70 else "high",
                rationale="The highest-risk run should become a repeatable regression case for future model or planner changes.",
                parameter_changes=[
                    f"Use {worst.run_id} as the seed trace.",
                    "Generate boundary cases around obstacle distance, ego speed, and braking delay.",
                    "Label the pack with scenario, source, and baseline release decision.",
                ],
                acceptance_criteria=[
                    "Regression pack is reproducible from versioned input data.",
                    "Each run has a stored report and release recommendation.",
                    "Any increase in risk score blocks automatic approval.",
                ],
            )
        )

    return variants[:4]
