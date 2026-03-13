"""Flux Balance Analysis (FBA) Proxy.

Abstractly simulates genome-scale metabolic flux to optimize theoretical targeted
yields against habitat constraints based on constraint-based modeling paradigms.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .adapters import HabitatProfile
from .models import CandidateProgram, MissionSpec


@dataclass(slots=True)
class MetabolicFlux:
    theoretical_yield: float  # 0 to 1 scale representing efficiency
    limiting_nutrient: str | None
    metabolic_burden: float  # Scale of growth penalty introduced by payload
    toxic_intermediate_risk: float  # Risk of poisoning the cell
    pathway_bottlenecks: list[str] = field(default_factory=list)


def _detect_limiting_nutrient(mission: MissionSpec, candidate: CandidateProgram) -> str | None:
    nutrients = [n.lower() for n in mission.environment.nutrients]
    if "remediation" in candidate.archetype or "capture" in " ".join(candidate.modules).lower():
        if "nitrogen" in nutrients:
            return "carbon"  # High N implies C limitation in typical waste streams
        return "trace metals"  # Usually rate-limiting for complex enzymes
    if not nutrients:
        return "baseline minimal media"
    return nutrients[0]


def simulate_flux(
    mission: MissionSpec, candidate: CandidateProgram, habitat: HabitatProfile
) -> MetabolicFlux:
    """Run an abstract constraint-based flux simulation on the candidate's pathways."""
    
    # 1. Base theoretical yield based on archetype efficiency
    base_yield = 0.8  # Strong theoretical baseline
    if "consortium" in candidate.archetype:
        base_yield = 0.65  # Inefficient carbon transfer between strains
    elif "phage" in candidate.archetype:
        base_yield = 0.5   # Heavy burden of viral replication machinery
        
    # 2. Metabolic Burden (cost of synthetic modules)
    burden = len(candidate.modules) * 0.08
    if habitat.severity > 5.0:
        burden *= 1.5  # Stress resistance competes with production flux
        
    # 3. Calculate final constrained yield
    yield_efficiency = max(0.01, base_yield - burden)
    
    # 4. Analyze bottlenecks and toxicity
    bottlenecks = []
    toxic_risk = 0.1
    
    limiting = _detect_limiting_nutrient(mission, candidate)
    if limiting:
        bottlenecks.append(f"Flux constrained by availability of {limiting}")
        yield_efficiency *= 0.9

    if "phage-delivered degradation cassette" in candidate.modules:
        toxic_risk += 0.4
        bottlenecks.append("High translation demand on host ribosomes")

    if habitat.severity > 7.0:
        bottlenecks.append("Energy diverted from payload to maintain osmotic/thermal homeostasis")
        yield_efficiency *= 0.7

    if "carbon fixation layer" in candidate.modules:
        bottlenecks.append("RuBisCO turnover rate limit in Calvin cycle")

    return MetabolicFlux(
        theoretical_yield=round(yield_efficiency, 3),
        limiting_nutrient=limiting,
        metabolic_burden=round(burden, 3),
        toxic_intermediate_risk=round(toxic_risk, 3),
        pathway_bottlenecks=bottlenecks
    )
