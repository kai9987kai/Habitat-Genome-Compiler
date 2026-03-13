"""Tiered biosafety assessment with defense-in-depth scoring.

Combines hard-block screening, quantitative escape-risk scoring, explicit
safeguard detection, BSL-equivalent containment inference, and an active
biocontainment plan informed by recent biocontainment literature and current
NIH guidance for gene-drive work.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import BiocontainmentPlan, MissionSpec


HIGH_RISK_KEYWORDS: dict[str, tuple[str, float]] = {
    "pathogen": ("Pathogen-related intent is outside the scope of this compiler.", 3.0),
    "virulence": ("Virulence-related design goals are blocked.", 3.0),
    "immune evasion": ("Immune-evasion related requests are blocked.", 3.0),
    "transmissible": ("Transmissibility-related requests are blocked.", 3.0),
    "contagious": ("Contagion-related requests are blocked.", 3.0),
    "host range": ("Host-range expansion is blocked.", 2.5),
    "host-range": ("Host-range expansion is blocked.", 2.5),
    "toxin": ("Toxin-related requests are blocked.", 2.5),
    "weapon": ("Weaponization-related language is blocked.", 4.0),
    "human embryo": ("Human embryo modification is blocked.", 3.5),
    "human deployment": ("Human deployment is blocked for this prototype.", 2.0),
    "gain of function": ("Gain-of-function related requests are blocked.", 3.5),
}

CAUTION_KEYWORDS: dict[str, tuple[str, float]] = {
    "open release": ("Open-release language raises containment concerns.", 1.5),
    "environmental release": ("Environmental release raises containment concerns.", 1.5),
    "antibiotic resistance": ("Antibiotic resistance markers should be simulation-only.", 1.0),
    "horizontal transfer": ("Horizontal gene transfer increases ecological risk.", 1.2),
    "self-replicating": ("Self-replicating constructs require elevated containment.", 1.5),
    "gene drive": ("Gene drive technology requires elevated containment and review.", 2.0),
}

_DEPLOYMENT_CONTEXT_SCORES: dict[str, float] = {
    "closed": 0.0,
    "contained": 0.5,
    "semi-open": 3.0,
    "open": 5.0,
    "field": 7.0,
}

_RISK_TIERS = [
    (0.0, 1.5, "negligible"),
    (1.5, 3.5, "low"),
    (3.5, 5.5, "moderate"),
    (5.5, 8.0, "elevated"),
    (8.0, float("inf"), "blocked"),
]

_CONTAINMENT_MAP = [
    (0.0, 2.0, "simulation-only"),
    (2.0, 4.0, "BSL-1"),
    (4.0, 6.0, "BSL-2"),
    (6.0, float("inf"), "BSL-3"),
]

_CONTAINMENT_RANK = {
    "simulation-only": 0,
    "BSL-1": 1,
    "BSL-2": 2,
    "BSL-3": 3,
}


@dataclass(frozen=True, slots=True)
class SafeguardSignal:
    label: str
    credit: float
    patterns: tuple[str, ...]


_SAFEGUARD_SIGNALS = (
    SafeguardSignal(
        label="Simulation-only execution",
        credit=0.8,
        patterns=("simulation only", "simulation-first", "digital twin", "non-actionable", "cell-free"),
    ),
    SafeguardSignal(
        label="Closed-loop physical containment",
        credit=0.8,
        patterns=(
            "closed loop",
            "closed-loop",
            "closed bioreactor",
            "closed habitat",
            "closed reactor",
            "closed system",
            "contained",
            "containment",
        ),
    ),
    SafeguardSignal(
        label="Explicit shutdown logic",
        credit=0.5,
        patterns=("shutdown logic", "passive shutdown", "passive failure handling", "kill switch", "failsafe"),
    ),
    SafeguardSignal(
        label="Synthetic auxotrophy",
        credit=1.1,
        patterns=("synthetic auxotrophy", "auxotrophy", "non-standard amino acid", "unnatural amino acid", "nsaa"),
    ),
    SafeguardSignal(
        label="Horizontal-transfer firewall",
        credit=1.0,
        patterns=(
            "genetic firewall",
            "orthogonal translation",
            "swapped genetic code",
            "swapped-code",
            "crispr containment",
            "transfer interruption",
        ),
    ),
)


@dataclass(slots=True)
class BiosafetyAssessment:
    allowed: bool
    risk_level: str
    risk_score: float
    risk_tier: str
    recommended_containment: str
    findings: list[str]
    keyword_hits: list[str] = field(default_factory=list)
    containment_plan: BiocontainmentPlan = field(default_factory=BiocontainmentPlan)


def _build_haystack(mission: MissionSpec) -> str:
    """Build text to scan for biosafety keywords.

    ``disallowed_capabilities`` is intentionally excluded because those are
    capabilities the mission forbids. Including them would cause false-positive
    keyword hits.
    """
    return " ".join(
        [
            mission.name,
            mission.summary,
            mission.domain,
            mission.deployment_context,
            *mission.biosafety_constraints,
            *mission.allowed_modalities,
            *mission.environment.stressors,
            *mission.environment.nutrients,
            *(objective.title for objective in mission.objectives),
            *(objective.target for objective in mission.objectives),
            *(constraint for objective in mission.objectives for constraint in objective.constraints),
        ]
    ).lower()


def _detect_safeguards(mission: MissionSpec) -> tuple[list[str], float]:
    haystack = _build_haystack(mission)
    detected: list[str] = []
    total_credit = 0.0

    for signal in _SAFEGUARD_SIGNALS:
        if any(pattern in haystack for pattern in signal.patterns):
            detected.append(signal.label)
            total_credit += signal.credit

    return detected, min(3.0, round(total_credit, 2))


def _unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def _is_open_context(context_lower: str) -> bool:
    return any(token in context_lower for token in ("semi-open", "open", "field"))


def _max_containment(current: str, minimum: str) -> str:
    if _CONTAINMENT_RANK[current] >= _CONTAINMENT_RANK[minimum]:
        return current
    return minimum


def quantitative_risk_score(mission: MissionSpec) -> tuple[float, list[str], list[str], bool]:
    """Compute a 0-10 risk score with hazard, context, and safeguard signals."""
    haystack = _build_haystack(mission)
    score = 0.0
    findings: list[str] = []
    keyword_hits: list[str] = []
    hard_blocked = False

    for keyword, (reason, weight) in HIGH_RISK_KEYWORDS.items():
        if keyword in haystack:
            findings.append(reason)
            keyword_hits.append(keyword)
            score += weight
            hard_blocked = True

    for keyword, (reason, weight) in CAUTION_KEYWORDS.items():
        if keyword in haystack:
            findings.append(f"Warning: {reason}")
            keyword_hits.append(keyword)
            score += weight

    context_lower = mission.deployment_context.lower()
    context_score = 2.0
    for key, value in _DEPLOYMENT_CONTEXT_SCORES.items():
        if key in context_lower:
            context_score = value
            break
    score += context_score * 0.4

    if "simulation" not in {modality.lower() for modality in mission.allowed_modalities}:
        findings.append("Mission does not include simulation as an allowed modality.")
        score += 1.0

    if "containment" not in haystack and "closed" not in context_lower:
        findings.append("Containment language is weak; mission should stay in closed or simulated environments.")
        score += 0.8

    env = mission.environment
    env_severity = min(
        3.0,
        0.1 * env.radiation_level + 0.02 * env.salinity_ppt + 0.1 * len(env.stressors),
    )
    score += env_severity * 0.2

    safeguards, safeguard_credit = _detect_safeguards(mission)
    if safeguards:
        findings.append(
            f"Detected safeguard layers: {', '.join(safeguards)} (risk credit -{safeguard_credit:.1f})."
        )
        score -= safeguard_credit

    non_operational_layers = [
        layer
        for layer in safeguards
        if layer not in {"Simulation-only execution", "Closed-loop physical containment"}
    ]
    if _is_open_context(context_lower) and len(non_operational_layers) < 2:
        findings.append("Open or field deployment needs at least two orthogonal engineered safeguard layers.")
        score += 1.4

    if any(term in haystack for term in ("horizontal transfer", "gene drive", "open release", "environmental release")):
        if "Horizontal-transfer firewall" not in safeguards:
            findings.append("Add an explicit HGT firewall for transfer-prone or environmental deployment contexts.")
            score += 0.9

    if "gene drive" in haystack:
        findings.append("Gene-drive work requires at least BL2 containment under the NIH Guidelines revised on April 4, 2024.")

    return min(10.0, max(0.0, round(score, 2))), findings, keyword_hits, hard_blocked


def _classify_tier(score: float) -> str:
    for lower, upper, tier in _RISK_TIERS:
        if lower <= score < upper:
            return tier
    return "blocked"


def _recommend_containment(score: float, mission: MissionSpec) -> str:
    level = "BSL-3"
    for lower, upper, containment in _CONTAINMENT_MAP:
        if lower <= score < upper:
            level = containment
            break

    haystack = _build_haystack(mission)
    context_lower = mission.deployment_context.lower()

    if _is_open_context(context_lower):
        level = _max_containment(level, "BSL-2")
    if "gene drive" in haystack:
        level = _max_containment(level, "BSL-2")

    return level


def assess_mission(mission: MissionSpec) -> BiosafetyAssessment:
    """Full biosafety assessment with safeguard-aware containment planning."""
    score, findings, keyword_hits, hard_blocked = quantitative_risk_score(mission)
    safeguards, _ = _detect_safeguards(mission)
    tier = "blocked" if hard_blocked else _classify_tier(score)
    containment = _recommend_containment(score, mission)

    if hard_blocked:
        risk_level = "blocked"
    elif score < 2.0:
        risk_level = "low"
    else:
        risk_level = "guarded"

    plan = BiocontainmentPlan()
    context_lower = mission.deployment_context.lower()
    haystack = _build_haystack(mission)

    if "simulation" in {modality.lower() for modality in mission.allowed_modalities}:
        plan.active_strategies.append("Simulation-only execution")
    if any(token in context_lower for token in ("closed", "contained", "habitat", "bioreactor")):
        plan.active_strategies.append("Closed-loop physical containment")
    if any(pattern in haystack for pattern in ("shutdown logic", "passive shutdown", "passive failure handling")):
        plan.active_strategies.append("Passive shutdown logic")

    if "Synthetic auxotrophy" in safeguards or score >= 1.5:
        plan.active_strategies.append("Synthetic auxotrophy")
        plan.auxotrophy_targets.append("nsAA dependency for an essential replication or translation factor")

    needs_transfer_firewall = any(term in haystack for term in ("horizontal transfer", "gene drive"))
    if "Horizontal-transfer firewall" in safeguards or needs_transfer_firewall or _is_open_context(context_lower) or score >= 3.5:
        plan.active_strategies.append("Multi-input CRISPR kill-switch")
        plan.genetic_firewalls.append("Programmed cleavage of escaped DNA or origins of replication")
        if _is_open_context(context_lower):
            plan.kill_switch_triggers.append("Absence of synthetic inducer ligand outside the approved site")
            plan.kill_switch_triggers.append("Temperature boundary violation outside validated process limits")
        else:
            plan.kill_switch_triggers.append("Detection of an external degradation or shutdown signal")

    if _is_open_context(context_lower) or score >= 5.5:
        plan.active_strategies.append("Semantic containment (genetic firewall)")
        plan.genetic_firewalls.append("Orthogonal translation or swapped-code payload isolation")
        plan.auxotrophy_targets.append("Phosphite obligate dependency to restrict nutrient escape")

    if "cell-free" in haystack:
        plan.active_strategies.append("Cell-free execution window")

    plan.active_strategies = _unique(plan.active_strategies)
    plan.auxotrophy_targets = _unique(plan.auxotrophy_targets)
    plan.kill_switch_triggers = _unique(plan.kill_switch_triggers)
    plan.genetic_firewalls = _unique(plan.genetic_firewalls)

    return BiosafetyAssessment(
        allowed=not hard_blocked,
        risk_level=risk_level,
        risk_score=score,
        risk_tier=tier,
        recommended_containment=containment,
        findings=findings,
        keyword_hits=keyword_hits,
        containment_plan=plan,
    )
