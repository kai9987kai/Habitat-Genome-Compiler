"""Typed mission, workflow, and report models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import json
from typing import Any, Optional, cast


@dataclass(slots=True)
class EnvironmentSpec:
    name: str
    temperature_range_c: tuple[float, float]
    radiation_level: float
    salinity_ppt: float
    ph_range: tuple[float, float]
    gravity_g: float
    atmosphere: list[str] = field(default_factory=list)
    nutrients: list[str] = field(default_factory=list)
    stressors: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EnvironmentSpec":
        return cls(
            name=str(payload["name"]),
            temperature_range_c=tuple(payload["temperature_range_c"]),
            radiation_level=float(payload["radiation_level"]),
            salinity_ppt=float(payload["salinity_ppt"]),
            ph_range=tuple(payload["ph_range"]),
            gravity_g=float(payload["gravity_g"]),
            atmosphere=[str(item) for item in payload.get("atmosphere", [])],
            nutrients=[str(item) for item in payload.get("nutrients", [])],
            stressors=[str(item) for item in payload.get("stressors", [])],
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

EnvironmentProfile = EnvironmentSpec
MissionEnvironment = EnvironmentSpec
@dataclass(slots=True)
class ObjectiveSpec:
    id: str
    title: str
    metric: str
    target: str
    priority: int
    constraints: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ObjectiveSpec":
        return cls(
            id=str(payload["id"]),
            title=str(payload["title"]),
            metric=str(payload["metric"]),
            target=str(payload["target"]),
            priority=int(payload["priority"]),
            constraints=[str(item) for item in payload.get("constraints", [])],
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class MissionSpec:
    name: str
    summary: str
    domain: str
    deployment_context: str
    environment: EnvironmentSpec
    objectives: list[ObjectiveSpec]
    biosafety_constraints: list[str] = field(default_factory=list)
    disallowed_capabilities: list[str] = field(default_factory=list)
    allowed_modalities: list[str] = field(default_factory=lambda: ["simulation"])

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MissionSpec":
        return cls(
            name=str(payload["name"]),
            summary=str(payload["summary"]),
            domain=str(payload["domain"]),
            deployment_context=str(payload["deployment_context"]),
            environment=EnvironmentSpec.from_dict(payload["environment"]),
            objectives=[ObjectiveSpec.from_dict(item) for item in payload["objectives"]],
            biosafety_constraints=[
                str(item) for item in payload.get("biosafety_constraints", [])
            ],
            disallowed_capabilities=[
                str(item) for item in payload.get("disallowed_capabilities", [])
            ],
            allowed_modalities=[str(item) for item in payload.get("allowed_modalities", ["simulation"])],
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class WorkflowStage:
    id: str
    owner: str
    description: str
    inputs: list[str]
    outputs: list[str]
    dependencies: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RobustnessReport:
    """Per-candidate Monte Carlo robustness summary."""

    candidate_id: str
    mean_total: float
    std_total: float
    failure_rate: float
    sensitivity: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class GrowthSimulation:
    time_points_h: list[float]
    biomass_od600: list[float]
    product_titer_gl: list[float]
    peak_growth_rate: float
    carrying_capacity: float
@dataclass(slots=True)
class TEAReport:
    estimated_capex_usd_k: float
    estimated_opex_usd_k_yr: float
    energy_return_on_investment: float
    carbon_footprint_kg_co2_kg_prod: float
    viability_score: float
    cost_drivers: list[str] = field(default_factory=list)

@dataclass(slots=True)
class MetabolicFlux:
    theoretical_yield: float
    limiting_nutrient: str | None
    metabolic_burden: float
    toxic_intermediate_risk: float
    pathway_bottlenecks: list[str] = field(default_factory=list)

@dataclass(slots=True)
class BiocontainmentPlan:
    active_strategies: list[str] = field(default_factory=list)
    auxotrophy_targets: list[str] = field(default_factory=list)
    kill_switch_triggers: list[str] = field(default_factory=list)
    genetic_firewalls: list[str] = field(default_factory=list)

@dataclass(slots=True)
class CandidateProgram:
    id: str
    title: str
    summary: str
    archetype: str
    modules: list[str]
    rationale: list[str]
    risks: list[str]
    scores: dict[str, float]
    evidence_channels: list[str]
    blocked_reason: str | None = None
    robustness: RobustnessReport | None = None
    tea: TEAReport | None = None
    flux: MetabolicFlux | None = None
    dna_sequence: str | None = None
    growth_simulation: GrowthSimulation | None = None
    stability_score: float | None = None
    stability_findings: list[str] = field(default_factory=list)
    evolutionary_risk_score: float | None = None
    genetic_lock_in_strategies: list[str] = field(default_factory=list)
    consortium_stability_index: float | None = None
    consortium_interactions: list[str] = field(default_factory=list)
    xenobiology_score: float | None = None
    xenobiology_features: list[str] = field(default_factory=list)
    epigenetic_tunability_score: float | None = None
    epigenetic_marks: list[str] = field(default_factory=list)
    plm_fitness_score: float | None = None
    plm_fitness_findings: list[str] = field(default_factory=list)
    circuit_reliability_score: float | None = None
    circuit_findings: list[str] = field(default_factory=list)
    circuit_gates: list[dict[str, str]] = field(default_factory=list)
    codon_score: float | None = None
    codon_findings: list[str] = field(default_factory=list)
    crispr_diagnostics_score: float | None = None
    crispr_diagnostics_assays: list[dict[str, str]] = field(default_factory=list)

@dataclass(slots=True)
class CompileResult:
    mission: MissionSpec
    allowed: bool
    risk_level: str
    risk_score: float
    risk_tier: str
    recommended_containment: str
    findings: list[str]
    experts: list[str]
    workflow: list[WorkflowStage]
    candidates: list[CandidateProgram]
    next_steps: list[str]
    disclaimers: list[str]
    compile_metadata: dict[str, Any] = field(default_factory=dict)
    dag_analysis: dict[str, Any] = field(default_factory=dict)
    containment_plan: BiocontainmentPlan | None = None
    regulatory_readiness: float | None = None
    regulatory_checklist: list[str] = field(default_factory=list)
    regulatory_frameworks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        def _strip_inf(obj):
            if isinstance(obj, float):
                if obj == float("inf"): return 1e12
                if obj == float("-inf"): return -1e12
                # Round for JSON cleanliness
                return round(obj, 6)
            if isinstance(obj, dict):
                return {k: _strip_inf(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_strip_inf(i) for i in obj]
            return obj
        # Cast self to Any to satisfy linters that don't recognize slots-based dataclasses
        return _strip_inf(asdict(cast(Any, self)))

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


def load_json_file(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
