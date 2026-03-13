"""Main mission compilation entrypoints."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .adapters import build_habitat_profile, propose_candidates
from .biosafety import assess_mission
from .codon_optimizer import optimize_codons
from .consortium import evaluate_consortium
from .crispr_diagnostics import design_crispr_diagnostic
from .epigenetics import generate_epigenetic_profile
from .evolutionary_risk import calculate_evolutionary_risk
from .fitness_landscape import predict_fitness_landscape
from .genetic_circuits import compile_genetic_circuit
from .metabolism import simulate_flux
from .models import CompileResult, MissionSpec, load_json_file
from .planner import build_workflow, critical_path, parallel_groups
from .regulatory import generate_regulatory_report
from .robustness import robustness_sweep
from .router import select_experts
from .scoring import score_candidates
from .sequence_gen import generate_sequences
from .simulation import simulate_growth
from .stability import calculate_stability_score
from .sustainability import evaluate_sustainability
from .xenobiology import evaluate_xenobiology

__version__ = "0.3.0"

DISCLAIMERS = [
    "This prototype is simulation-first and planning-only.",
    "It does not emit DNA, protein, CRISPR, or laboratory protocol artifacts.",
    "Any transition from simulation to wet-lab work requires biosafety, institutional, and legal review.",
    "Robustness scores are based on Monte Carlo perturbation of environment parameters and are indicative, not definitive.",
    "Economics (TEA) and theoretical yields (FBA) are abstract prospective estimates.",
]


def _coerce_mission(payload: MissionSpec | dict[str, Any]) -> MissionSpec:
    if isinstance(payload, MissionSpec):
        return payload
    return MissionSpec.from_dict(payload)


def _compile_metadata(mission: MissionSpec) -> dict[str, Any]:
    """Generate provenance metadata for the compile result."""
    raw = json.dumps(mission.to_dict() if hasattr(mission, "to_dict") else {}, sort_keys=True)
    return {
        "compiler_version": __version__,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_hash": hashlib.sha256(raw.encode()).hexdigest()[:16],
    }


def compile_mission(payload: MissionSpec | dict[str, Any]) -> CompileResult:
    mission = _coerce_mission(payload)
    biosafety = assess_mission(mission)
    experts = select_experts(mission)
    workflow = build_workflow(mission, experts)

    cpath = critical_path(workflow)
    pgroups = parallel_groups(workflow)
    dag = {
        "critical_path": cpath,
        "critical_path_length": len(cpath),
        "parallel_groups": pgroups,
        "max_parallelism": max(len(group) for group in pgroups) if pgroups else 0,
    }

    metadata = _compile_metadata(mission)

    if not biosafety.allowed:
        return CompileResult(
            mission=mission,
            allowed=False,
            risk_level=biosafety.risk_level,
            risk_score=biosafety.risk_score,
            risk_tier=biosafety.risk_tier,
            recommended_containment=biosafety.recommended_containment,
            findings=biosafety.findings,
            experts=experts,
            workflow=workflow,
            candidates=[],
            next_steps=[
                "Re-scope the mission to closed, simulation-first industrial or environmental domains.",
                "Remove blocked capabilities from the request.",
            ],
            disclaimers=DISCLAIMERS,
            compile_metadata=metadata,
            dag_analysis=dag,
            containment_plan=biosafety.containment_plan,
        )

    habitat = build_habitat_profile(mission)
    candidates = score_candidates(mission, habitat, propose_candidates(mission, habitat))
    robustness_reports = robustness_sweep(mission, candidates)
    tea_reports = evaluate_sustainability(mission, candidates, habitat.severity)

    for index, candidate in enumerate(candidates):
        candidate.robustness = robustness_reports[index]
        candidate.tea = tea_reports[index]
        candidate.flux = simulate_flux(mission, candidate, habitat)
        candidate.dna_sequence = generate_sequences(candidate)
        candidate.growth_simulation = simulate_growth(mission, candidate, habitat)

        stability_score, stability_findings = calculate_stability_score(candidate, mission.environment)
        candidate.stability_score = stability_score
        candidate.stability_findings = stability_findings

        evo_risk, evo_strategies = calculate_evolutionary_risk(candidate, mission.environment)
        candidate.evolutionary_risk_score = evo_risk
        candidate.genetic_lock_in_strategies = evo_strategies

        consortium_stability, consortium_interactions = evaluate_consortium(candidate)
        candidate.consortium_stability_index = consortium_stability
        candidate.consortium_interactions = consortium_interactions

        xeno_score, xeno_features = evaluate_xenobiology(
            candidate,
            mission.environment,
            biosafety.risk_tier,
        )
        candidate.xenobiology_score = xeno_score
        candidate.xenobiology_features = xeno_features

        epi_score, epi_marks = generate_epigenetic_profile(candidate)
        candidate.epigenetic_tunability_score = epi_score
        candidate.epigenetic_marks = epi_marks

        plm_score, plm_findings = predict_fitness_landscape(candidate)
        candidate.plm_fitness_score = plm_score
        candidate.plm_fitness_findings = plm_findings

        circuit_score, circuit_findings, circuit_gates = compile_genetic_circuit(mission, candidate)
        candidate.circuit_reliability_score = circuit_score
        candidate.circuit_findings = circuit_findings
        candidate.circuit_gates = circuit_gates

        codon_score, codon_findings = optimize_codons(candidate, mission)
        candidate.codon_score = codon_score
        candidate.codon_findings = codon_findings

        diag_score, diag_assays = design_crispr_diagnostic(candidate, mission)
        candidate.crispr_diagnostics_score = diag_score
        candidate.crispr_diagnostics_assays = diag_assays

    next_steps = [
        "Review the top-ranked candidate (Pareto front 0) and its failure modes.",
        "Examine robustness reports for sensitivity to environmental perturbations.",
        "Assess TEA viability score to verify economic scaling feasibility.",
        "Review metabolic bottlenecks and toxicity risks in the flux simulation.",
        "Export the Biocontainment Plan to institutional biosafety committees.",
        "Attach a higher-fidelity habitat simulator or external model adapter behind the workflow stages.",
        "Define institution-specific review gates before any non-simulation activity.",
    ]
    if habitat.severity >= 6:
        next_steps.insert(2, "Prioritize robustness sweeps for thermal, osmotic, and radiation extremes.")

    findings = list(biosafety.findings)
    findings.append(f"Habitat severity score: {habitat.severity}/10.")
    findings.append(habitat.narrative)
    findings.append(f"Quantitative risk score: {biosafety.risk_score}/10 -> tier: {biosafety.risk_tier}.")
    findings.append(f"Recommended containment: {biosafety.recommended_containment}.")

    result = CompileResult(
        mission=mission,
        allowed=True,
        risk_level=biosafety.risk_level,
        risk_score=biosafety.risk_score,
        risk_tier=biosafety.risk_tier,
        recommended_containment=biosafety.recommended_containment,
        findings=findings,
        experts=experts,
        workflow=workflow,
        candidates=candidates,
        next_steps=next_steps,
        disclaimers=DISCLAIMERS,
        compile_metadata=metadata,
        dag_analysis=dag,
        containment_plan=biosafety.containment_plan,
    )

    reg_readiness, reg_checklist, reg_frameworks = generate_regulatory_report(result)
    result.regulatory_readiness = reg_readiness
    result.regulatory_checklist = reg_checklist
    result.regulatory_frameworks = reg_frameworks

    return result


def load_mission_file(path: str | Path) -> MissionSpec:
    return MissionSpec.from_dict(load_json_file(path))


def render_markdown(result: CompileResult) -> str:
    lines = [
        f"# {result.mission.name}",
        "",
        f"- Allowed: `{str(result.allowed).lower()}`",
        f"- Risk level: `{result.risk_level}`",
        f"- Risk score: `{result.risk_score}/10`",
        f"- Risk tier: `{result.risk_tier}`",
        f"- Recommended containment: `{result.recommended_containment}`",
        f"- Domain: `{result.mission.domain}`",
        f"- Deployment context: `{result.mission.deployment_context}`",
    ]

    if result.compile_metadata:
        lines.extend(["", "## Compile Metadata"])
        for key, value in result.compile_metadata.items():
            lines.append(f"- {key}: `{value}`")

    lines.extend(["", "## Findings"])
    lines.extend(f"- {finding}" for finding in result.findings)

    if result.containment_plan and (
        result.containment_plan.active_strategies or result.containment_plan.kill_switch_triggers
    ):
        lines.extend(["", "## Active Biocontainment Plan"])
        plan = result.containment_plan
        lines.append(f"- **Strategies**: {', '.join(plan.active_strategies)}")
        if plan.auxotrophy_targets:
            lines.append(f"- **Auxotrophy Targets**: {', '.join(plan.auxotrophy_targets)}")
        if plan.kill_switch_triggers:
            lines.append(f"- **Kill-Switch Triggers**: {', '.join(plan.kill_switch_triggers)}")
        if plan.genetic_firewalls:
            lines.append(f"- **Genetic Firewalls**: {', '.join(plan.genetic_firewalls)}")

    lines.extend(["", "## Experts"])
    lines.extend(f"- {expert}" for expert in result.experts)

    lines.extend(["", "## Workflow"])
    for stage in result.workflow:
        deps = f" (depends: {', '.join(stage.dependencies)})" if stage.dependencies else ""
        lines.append(f"- `{stage.id}` ({stage.owner}): {stage.description}{deps}")

    if result.dag_analysis:
        lines.extend(["", "## DAG Analysis"])
        if "critical_path" in result.dag_analysis:
            joined = "` -> `".join(result.dag_analysis["critical_path"])
            lines.append(
                f"- **Critical path** ({result.dag_analysis['critical_path_length']} stages): `{joined}`"
            )
        if "max_parallelism" in result.dag_analysis:
            lines.append(f"- **Max parallelism**: {result.dag_analysis['max_parallelism']} stages")
        if "parallel_groups" in result.dag_analysis:
            for index, group in enumerate(result.dag_analysis["parallel_groups"]):
                lines.append(f"  - Level {index}: {', '.join(f'`{stage}`' for stage in group)}")

    lines.extend(["", "## Candidates"])
    if not result.candidates:
        lines.append("- No candidates generated because the mission was blocked.")
    else:
        for candidate in result.candidates:
            front = int(candidate.scores.get("pareto_front", 0))
            crowding = candidate.scores.get("crowding_distance", 0)
            crowd_str = "inf" if crowding == float("inf") else f"{crowding:.2f}"
            lines.append(f"### {candidate.title} (Pareto front {front})")
            lines.append(
                f"- **Total**: `{candidate.scores.get('total', 0)}` | "
                f"mission `{candidate.scores.get('mission_fit', 0)}` | habitat `{candidate.scores.get('habitat_fit', 0)}` | "
                f"feasibility `{candidate.scores.get('feasibility', 0)}` | biosafety `{candidate.scores.get('biosafety_margin', 0)}`"
            )
            lines.append(f"- **Crowding distance**: `{crowd_str}`")
            lines.append(f"- **Archetype**: `{candidate.archetype}`")

            if candidate.tea:
                tea = candidate.tea
                lines.append(
                    f"- **TEA / LCA**: Viability `{tea.viability_score}/10` | "
                    f"CAPEX `M${tea.estimated_capex_usd_k / 1000:.2f}` | "
                    f"OPEX `M$/yr {tea.estimated_opex_usd_k_yr / 1000:.2f}` | "
                    f"EROI `{tea.energy_return_on_investment}` | "
                    f"CO2e `{tea.carbon_footprint_kg_co2_kg_prod} kg/kg`"
                )
                if tea.cost_drivers:
                    lines.append(f"  - Drivers: {', '.join(tea.cost_drivers)}")

            if candidate.flux:
                flux = candidate.flux
                limiting = f" | Limiting: `{flux.limiting_nutrient}`" if flux.limiting_nutrient else ""
                lines.append(
                    f"- **Metabolic Flux**: Theoretical Yield `{flux.theoretical_yield:.1%}` | "
                    f"Burden `{flux.metabolic_burden}` | Tox Risk `{flux.toxic_intermediate_risk}`{limiting}"
                )
                if flux.pathway_bottlenecks:
                    lines.append(f"  - Bottlenecks: {', '.join(flux.pathway_bottlenecks)}")

            lines.append(f"- Summary: {candidate.summary}")
            lines.append(f"- Modules: {', '.join(candidate.modules)}")
            lines.append(f"- Risks: {', '.join(candidate.risks)}")

            if candidate.robustness:
                robustness = candidate.robustness
                lines.append(
                    f"- **Robustness**: mean `{robustness.mean_total}` +/- `{robustness.std_total}` | "
                    f"failure rate `{robustness.failure_rate:.1%}`"
                )
                if robustness.sensitivity:
                    sensitivity = [f"{key}: `{value:+.4f}`" for key, value in robustness.sensitivity.items()]
                    lines.append(f"  - Sensitivity: {', '.join(sensitivity)}")

            if candidate.dna_sequence:
                sequence = candidate.dna_sequence
                gc_content = (sequence.count('G') + sequence.count('C')) / len(sequence) if sequence else 0.0
                lines.append(f"- **GenAI Sequence**: `{len(sequence)} bp` | GC content `{gc_content:.1%}`")

            if candidate.growth_simulation:
                simulation = candidate.growth_simulation
                lines.append(
                    f"- **Digital Twin ODE**: Peak mu `{simulation.peak_growth_rate} h^-1` | "
                    f"Capacity OD600 `{simulation.carrying_capacity}` | "
                    f"Peak Titer `{max(simulation.product_titer_gl, default=0)} g/L`"
                )

            if candidate.stability_score is not None:
                lines.append(f"- **Stability Analysis**: `{candidate.stability_score}/10` Proteostasis Score")
                for finding in candidate.stability_findings:
                    lines.append(f"  - {finding}")

            if candidate.evolutionary_risk_score is not None:
                lines.append(f"- **Evolutionary Risk**: `{candidate.evolutionary_risk_score}/10` Eco-Risk Score")
                if candidate.genetic_lock_in_strategies:
                    lines.append("  - **Safeguards**:")
                    for strategy in candidate.genetic_lock_in_strategies:
                        lines.append(f"    - {strategy}")

            if candidate.consortium_stability_index is not None and "consortium" in candidate.archetype.lower():
                lines.append(f"- **Consortium Symbiosis**: `{candidate.consortium_stability_index}/10` Index")
                for interaction in candidate.consortium_interactions:
                    lines.append(f"  - {interaction}")

            if candidate.xenobiology_score is not None and candidate.xenobiology_score > 5.0:
                lines.append(f"- **Xenobiology (Absolute Biocontainment)**: `{candidate.xenobiology_score}/10`")
                for feature in candidate.xenobiology_features:
                    lines.append(f"  - {feature}")

            if candidate.epigenetic_tunability_score is not None and candidate.epigenetic_tunability_score > 5.0:
                lines.append(
                    f"- **Epigenetic Tuning Profile**: `{candidate.epigenetic_tunability_score}/10` Flexibility"
                )
                for mark in candidate.epigenetic_marks:
                    lines.append(f"  - {mark}")

            if candidate.plm_fitness_score is not None:
                lines.append(f"- **PLM Fitness Landscape**: `{candidate.plm_fitness_score}/10`")
                for finding in candidate.plm_fitness_findings:
                    lines.append(f"  - {finding}")

            if candidate.circuit_reliability_score is not None:
                lines.append(f"- **Genetic Circuit**: `{candidate.circuit_reliability_score}/10` Reliability")
                for finding in candidate.circuit_findings:
                    lines.append(f"  - {finding}")

            if candidate.codon_score is not None:
                lines.append(f"- **Codon Optimization**: `{candidate.codon_score}/10`")
                for finding in candidate.codon_findings:
                    lines.append(f"  - {finding}")

            if candidate.crispr_diagnostics_assays:
                lines.append(f"- **CRISPR Diagnostics**: `{candidate.crispr_diagnostics_score}/10` Relevance")
                for assay in candidate.crispr_diagnostics_assays:
                    lines.append(f"  - [{assay.get('assay', '')}] {assay.get('target', '')} ({assay.get('sensitivity', '')} sensitivity)")

    lines.extend(["", "## Next Steps"])
    lines.extend(f"- {step}" for step in result.next_steps)

    lines.extend(["", "## Disclaimers"])
    lines.extend(f"- {item}" for item in result.disclaimers)

    if result.regulatory_readiness is not None:
        lines.extend(["", "## Regulatory Compliance (GLP)"])
        lines.append(f"- **Readiness Score**: `{result.regulatory_readiness}/10`")
        if result.regulatory_frameworks:
            lines.append(f"- **Applicable Frameworks**: {', '.join(result.regulatory_frameworks)}")
        for item in result.regulatory_checklist:
            lines.append(f"- {item}")

    return "\n".join(lines)
