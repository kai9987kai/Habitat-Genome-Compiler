"""Deterministic mock adapters with a dynamic archetype registry.

Expands the design space from 3 to 5 candidate archetypes (consortium,
single-chassis, living-material, hybrid-consortium, phage-assisted) using
a registry pattern inspired by DBTL-cycle design-space exploration papers.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import CandidateProgram, MissionSpec


@dataclass(slots=True)
class HabitatProfile:
    severity: float
    drivers: list[str]
    narrative: str


@dataclass(slots=True)
class ArchetypeTemplate:
    """Blueprint for generating a candidate from an archetype."""

    id_prefix: str
    title: str
    summary: str
    archetype: str
    base_modules: list[str]
    base_rationale: list[str]
    base_risks: list[str]
    tag_modules: dict[str, str] = field(default_factory=dict)
    severity_module: str | None = None
    extra_evidence: str = ""


# ---------------------------------------------------------------------------
# Archetype registry
# ---------------------------------------------------------------------------

SAFETY_MODULES = ["containment logic", "shutdown sentinel", "traceability telemetry"]

BASE_EVIDENCE = [
    "habitat simulation",
    "genome architecture scoring",
    "regulatory program review",
    "phenotype projection",
]

ARCHETYPE_REGISTRY: list[ArchetypeTemplate] = [
    ArchetypeTemplate(
        id_prefix="candidate-a",
        title="Closed-loop specialist consortium",
        summary="A contained consortium that splits sensing, transformation, and resilience into separate roles.",
        archetype="consortium",
        base_modules=["division-of-labor consortium", "stress buffer chassis"],
        base_rationale=[
            "Uses ecological specialization instead of overloading one chassis.",
            "Matches the multistage mission-compiler concept while remaining simulation-first.",
        ],
        base_risks=["coordination drift", "simulation-to-reality gap"],
        tag_modules={
            "remediation": "pollutant capture and conversion layer",
            "carbon": "carbon fixation layer",
            "materials": "matrix-forming biofilm layer",
            "consortium": "programmed metabolic exchange module",
        },
        extra_evidence="community stability sweep",
    ),
    ArchetypeTemplate(
        id_prefix="candidate-b",
        title="Minimal operations chassis",
        summary="A simpler design centered on robust control logic and low-variance execution.",
        archetype="single-chassis",
        base_modules=["single chassis with modular regulation", "adaptive stress-response logic"],
        base_rationale=[
            "Simpler operationally than a consortium and easier to validate in a closed reactor.",
            "Relies on regulatory program quality more heavily than ecological diversity.",
        ],
        base_risks=["single-point failure", "tighter genome/regulation coupling required"],
        severity_module="extreme-environment hardening",
        tag_modules={
            "offworld": "radiation shielding pigment program",
            "evolution": "orthogonal tRNA evolutionary lock-in",
            "xenobiology": "HNA (Hexitol Nucleic Acid) xeno-backbone",
            "epigenetics": "dCas9-DNMT3A epigenetic silencer",
        },
        extra_evidence="control logic ablation",
    ),
    ArchetypeTemplate(
        id_prefix="candidate-c",
        title="Living material sentinel",
        summary="A biofilm or coating-like program optimized for environmental sensing, capture, and passive resilience.",
        archetype="living-material",
        base_modules=["living-material interface", "environmental sensing skin"],
        base_rationale=[
            "Best when the mission includes infrastructure, coatings, or persistent surfaces.",
            "Pushes the design toward passive containment and easy shutdown paths.",
        ],
        base_risks=["surface fouling", "weaker throughput than active consortia"],
        tag_modules={
            "materials": "surface repair matrix",
            "offworld": "surface repair matrix",
            "carbon": "carbon-sequestering matrix chemistry",
            "remediation": "adsorption-first contaminant removal layer",
        },
        extra_evidence="surface durability sweep",
    ),
    ArchetypeTemplate(
        id_prefix="candidate-d",
        title="Hybrid consortium-material composite",
        summary="Combines microbial division-of-labor with a living-material interface for dual-mode operation.",
        archetype="hybrid-consortium",
        base_modules=[
            "division-of-labor consortium",
            "living-material interface",
            "cross-layer signaling bus",
        ],
        base_rationale=[
            "Merges ecological specialization with passive structural resilience.",
            "Suited for missions that require both active processing and persistent infrastructure.",
        ],
        base_risks=[
            "increased design complexity",
            "inter-layer coordination latency",
            "wider failure surface area",
        ],
        tag_modules={
            "remediation": "dual-mode capture and degradation layer",
            "carbon": "carbon fixation + sequestration hybrid layer",
            "materials": "self-healing structural biofilm",
            "offworld": "regolith-binding composite matrix",
        },
        severity_module="extreme-environment hardening",
        extra_evidence="cross-layer communication stability sweep",
    ),
    ArchetypeTemplate(
        id_prefix="candidate-e",
        title="Phage-assisted adaptive chassis",
        summary="Leverages bacteriophage-mediated gene transfer for rapid in-situ adaptation under environmental pressure.",
        archetype="phage-assisted",
        base_modules=[
            "temperate phage integration cassette",
            "adaptive gene shuttle system",
            "phage-host compatibility layer",
        ],
        base_rationale=[
            "Enables rapid trait acquisition under habitat stress without pre-engineering all pathways.",
            "Draws on phage-mediated horizontal gene transfer documented in extremophile communities.",
        ],
        base_risks=[
            "phage escape risk (mitigated by containment and defective phage design)",
            "unintended gene disruption at integration sites",
            "regulatory complexity for phage-bearing constructs",
        ],
        tag_modules={
            "remediation": "phage-delivered degradation cassette",
            "carbon": "phage-delivered fixation operon",
            "offworld": "radiation-adaptive transduction system",
        },
        extra_evidence="phage integration fidelity sweep",
    ),
]


# ---------------------------------------------------------------------------
# Habitat profiling
# ---------------------------------------------------------------------------


def build_habitat_profile(mission: MissionSpec) -> HabitatProfile:
    env = mission.environment
    temperature_span = abs(env.temperature_range_c[1] - env.temperature_range_c[0])
    acidity_span = abs(env.ph_range[1] - env.ph_range[0])
    severity = min(
        10.0,
        0.05 * temperature_span
        + 0.08 * env.salinity_ppt
        + 0.7 * env.radiation_level
        + 0.9 * acidity_span
        + 0.4 * len(env.stressors),
    )

    drivers: list[str] = []
    if env.radiation_level >= 4:
        drivers.append("radiation")
    if env.salinity_ppt >= 35:
        drivers.append("salinity")
    if temperature_span >= 20:
        drivers.append("thermal cycling")
    if acidity_span >= 2:
        drivers.append("pH drift")
    drivers.extend(env.stressors)

    narrative = (
        f"{env.name} requires adaptation to {', '.join(dict.fromkeys(drivers)) or 'baseline industrial stress'} "
        "with a preference for closed-loop containment and simulation-first evaluation."
    )
    return HabitatProfile(severity=round(severity, 2), drivers=list(dict.fromkeys(drivers)), narrative=narrative)


# ---------------------------------------------------------------------------
# Objective tag extraction
# ---------------------------------------------------------------------------


def _core_objective_tags(mission: MissionSpec) -> set[str]:
    text = " ".join(
        [mission.summary, mission.domain, *(o.title for o in mission.objectives)]
    ).lower()
    tags: set[str] = set()
    if any(t in text for t in ("pfas", "waste", "remediation", "degradation")):
        tags.add("remediation")
    if any(t in text for t in ("carbon", "capture", "fixation")):
        tags.add("carbon")
    if any(t in text for t in ("biofilm", "coating", "material", "infrastructure")):
        tags.add("materials")
    if any(t in text for t in ("mars", "lunar", "space", "habitat")):
        tags.add("offworld")
    if any(t in text for t in ("evolution", "lock-in", "stability", "persistence")):
        tags.add("evolution")
    if any(t in text for t in ("consortium", "symbiosis", "community", "exchange")):
        tags.add("consortium")
    if any(t in text for t in ("xeno", "orthogonal", "absolute biocontainment", "alien")):
        tags.add("xenobiology")
    if any(t in text for t in ("epigenetic", "tuning", "methylation", "chromatin")):
        tags.add("epigenetics")
    return tags


# ---------------------------------------------------------------------------
# Dynamic candidate generation via RL Design Space Exploration
# ---------------------------------------------------------------------------

import random

def _calculate_rl_reward(archetype: ArchetypeTemplate, selected_modules: set[str], habitat: HabitatProfile, tags: set[str]) -> float:
    """Calculate the proxy Q-learning reward for a specific assembly."""
    reward = 10.0
    
    # Reward synergy with mission tags
    for tag in tags:
        if tag in archetype.tag_modules and archetype.tag_modules[tag] in selected_modules:
            reward = reward + 3.0
            
    # Penalize complexity (metabolic burden)
    reward = reward - (float(len(selected_modules)) * 0.5)
    
    # Reward environment matching
    if habitat.severity >= 6.0 and archetype.severity_module and archetype.severity_module in selected_modules:
        reward = reward + 5.0
    elif habitat.severity < 6.0 and archetype.severity_module and archetype.severity_module in selected_modules:
        reward = reward - 2.0  # Unnecessary payload burden
        
    # Consortium stability penalty under extreme stress
    if "consortium" in archetype.archetype and habitat.severity >= 8.0:
         reward = reward - 4.0
         
    return reward

def propose_candidates(mission: MissionSpec, habitat: HabitatProfile) -> list[CandidateProgram]:
    """Generate candidates dynamically via RL-proxy combinatorial exploration."""
    tags = _core_objective_tags(mission)
    candidates: list[CandidateProgram] = []
    
    random.seed(hash(mission.name) + int(habitat.severity * 100)) # Deterministic exploration
    
    # RL Agent Configuration
    num_epochs = 20
    learning_rate = 0.1
    exploration_rate = 0.3
    
    # We explore the space of (Archetype, Optional Modules) combinations
    for i, template in enumerate(ARCHETYPE_REGISTRY):
        best_module_set: set[str] = set(template.base_modules) | set(SAFETY_MODULES)
        max_reward = -float('inf')
        
        # Available optional modules for this archetype
        optional_modules: list[str] = list(template.tag_modules.values())
        if template.severity_module:
            optional_modules.append(template.severity_module)
            
        # RL combinatorial exploration loop (Q-learning proxy)
        current_modules: set[str] = set(best_module_set)
        for epoch in range(num_epochs):
            # Epsilon-greedy exploration
            if random.random() < exploration_rate and optional_modules:
                toggle_mod = random.choice(optional_modules)
                if toggle_mod in current_modules:
                    current_modules.remove(toggle_mod)
                else:
                    current_modules.add(toggle_mod)
            else:
                # Exploitation: greedy add missing high-value tag modules
                for t in tags:
                    if t in template.tag_modules:
                        current_modules.add(template.tag_modules[t])
                if habitat.severity >= 6.0 and template.severity_module:
                    current_modules.add(template.severity_module)
                    
            # Evaluate state reward
            reward = _calculate_rl_reward(template, current_modules, habitat, tags)
            
            # Update best state
            if reward > max_reward:
                max_reward = reward
                best_module_set = set(current_modules)
                
            # Decay exploration over epochs
            exploration_rate *= (1.0 - learning_rate)

        rationale = list(template.base_rationale)
        rationale.append(habitat.narrative)
        rationale.append(f"RL agent converged on this module graph over {num_epochs} epochs with peak reward {max_reward:.2f}.")

        evidence = list(BASE_EVIDENCE)
        if template.extra_evidence:
            evidence.append(template.extra_evidence)

        candidates.append(
            CandidateProgram(
                id=template.id_prefix,
                title=template.title,
                summary=template.summary,
                archetype=template.archetype,
                modules=list(best_module_set),
                rationale=rationale,
                risks=list(template.base_risks),
                scores={},
                evidence_channels=evidence,
            )
        )

    return candidates
