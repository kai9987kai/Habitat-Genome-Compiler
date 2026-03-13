"""Prospective Techno-Economic Analysis (TEA) and Life Cycle Assessment (LCA).

Estimates scaled manufacturing costs and environmental impact margins based
on 2024 state-of-the-art predictive modeling for synthetic biology.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .models import CandidateProgram, MissionSpec


@dataclass(slots=True)
class TEAReport:
    estimated_capex_usd_k: float
    estimated_opex_usd_k_yr: float
    energy_return_on_investment: float  # Value > 1.0 means energy positive
    carbon_footprint_kg_co2_kg_prod: float
    viability_score: float  # 0 to 10 scale
    cost_drivers: list[str] = field(default_factory=list)


def _base_capex(context: str) -> float:
    context = context.lower()
    if "open" in context or "field" in context:
        return 500.0  # Open/field deployments have lower upfront infrastructure
    if "semi-open" in context:
        return 1500.0
    if "contained" in context:
        return 5000.0
    return 10000.0  # Fully closed/reactor systems are very expensive


def _calc_complexity_multiplier(candidate: CandidateProgram) -> float:
    mult = 1.0
    mod_count = len(candidate.modules)
    if "consortium" in candidate.archetype:
        mult *= 1.5  # Co-culturing is harder
    if "hybrid" in candidate.archetype:
        mult *= 1.8  # Complex material/bio-interfaces
    if "phage" in candidate.archetype:
        mult *= 1.4  # Viral delivery/stability overhead
    mult += (mod_count * 0.05)
    return mult


def evaluate_sustainability(
    mission: MissionSpec, candidates: list[CandidateProgram], habitat_severity: float
) -> list[TEAReport]:
    """Calculate prospective TEA and LCA profiles for each candidate."""
    reports: list[TEAReport] = []

    base_capex = _base_capex(mission.deployment_context)
    has_carbon_fixation = any("carbon" in o.title.lower() for o in mission.objectives)
    base_eroi = 1.5 if has_carbon_fixation else 0.8
    env_stress_penalty = 1.0 + (habitat_severity * 0.1)

    for candidate in candidates:
        comp_mult = _calc_complexity_multiplier(candidate)

        # CAPEX: Scales with baseline context and candidate complexity
        capex = base_capex * comp_mult * env_stress_penalty

        # OPEX: Scales heavily with environment severity (e.g. heating/cooling)
        # Assuming baseline 20% of capex for OPEX
        base_opex = capex * 0.2
        # Severe habitats require exponential operational cost to maintain homeostasis
        opex_multiplier = min(1000.0, math.exp(habitat_severity * 0.15))
        opex = base_opex * opex_multiplier

        # EROI: Degrades heavily with complexity (more pathways to power) and habitat stress
        eroi = base_eroi / (comp_mult * math.sqrt(env_stress_penalty))

        # Carbon Footprint: kg CO2 equivalent per kg product
        # Lower is better. Negative is carbon sequestering.
        carbon = 5.0 * comp_mult * opex_multiplier
        if has_carbon_fixation:
             carbon -= 15.0  # Deep subtraction for bio-sequestration
        carbon = round(carbon, 2)

        viability = 10.0
        cost_drivers = []
        if capex > 20000.0:
            viability -= 3.0
            cost_drivers.append("Extreme initial capitalization (Capex)")
        if opex > 10000.0:
            viability -= 3.0
            cost_drivers.append("Prohibitive operational overhead (Opex due to severity)")
        if eroi < 0.5:
            viability -= 2.0
            cost_drivers.append("Severe negative energy return (Thermodynamic limit)")
        if "consortium" in candidate.archetype and habitat_severity > 7.0:
            viability -= 1.0
            cost_drivers.append("Co-culture stability at high environmental stress")

        if not cost_drivers:
            cost_drivers.append("Favorable economics at scale")

        reports.append(
            TEAReport(
                estimated_capex_usd_k=float(round(capex, 1)),
                estimated_opex_usd_k_yr=float(round(opex, 1)),
                energy_return_on_investment=float(round(eroi, 3)),
                carbon_footprint_kg_co2_kg_prod=carbon,
                viability_score=max(0.0, float(round(viability, 1))),
                cost_drivers=cost_drivers,
            )
        )

    return reports
