"""Safe mission-spec generation for the GUI builder."""

from __future__ import annotations

from typing import Any

from .models import MissionSpec

SAFE_ALLOWED_MODALITIES = ["simulation", "digital twin", "non-actionable planning"]
SAFE_DISALLOWED_CAPABILITIES = [
    "pathogen design",
    "immune evasion",
    "toxins",
    "host range expansion",
]

RESEARCH_LIBRARY: dict[str, dict[str, str]] = {
    "digital_twin_controls": {
        "title": "Digital Twins for Bioprocess Control Strategy Development and Realisation",
        "url": "https://pubmed.ncbi.nlm.nih.gov/33215237/",
        "applied_rule": "Added observability and control-loop objectives for builder-generated missions.",
    },
    "consortium_homeostasis": {
        "title": "Long-term homeostasis of synthetic microbial consortia through auxotrophic division of labor",
        "url": "https://www.nature.com/articles/s41467-025-57022-3",
        "applied_rule": "Added community-balance objectives when the mission needs multi-stressor or consortium behavior.",
    },
    "biocontainment_layering": {
        "title": "Cas9-assisted biological containment for safe deployment of engineered microbes in environments",
        "url": "https://www.nature.com/articles/s41587-024-02277-7",
        "applied_rule": "Strengthened containment defaults for any mission that moves beyond pure simulation framing.",
    },
    "offworld_resource_loops": {
        "title": "Cyanobacteria as candidates to support Mars colonization: growth, biofertilization and biomining capacity using Mars regolith as a resource",
        "url": "https://pubmed.ncbi.nlm.nih.gov/35710677/",
        "applied_rule": "Added nutrient-recycle objectives for offworld and regolith-linked habitats.",
    },
}

BLOCKED_TERMS = (
    "pathogen",
    "virulence",
    "immune evasion",
    "toxin",
    "weapon",
    "transmissible",
    "host range expansion",
)


def _normalize_text(value: Any, default: str = "") -> str:
    text = str(value or default).strip()
    return text or default


def _normalize_list(value: Any) -> list[str]:
    if isinstance(value, list):
        parts = [str(item).strip() for item in value]
    else:
        text = str(value or "")
        normalized = text.replace("\r", "\n").replace(";", ",")
        parts = []
        for line in normalized.splitlines():
            parts.extend(piece.strip() for piece in line.split(","))
    seen: set[str] = set()
    items: list[str] = []
    for item in parts:
        if item and item.lower() not in seen:
            items.append(item)
            seen.add(item.lower())
    return items


def _normalize_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _objective(
    idx: int,
    title: str,
    metric: str,
    target: str,
    priority: int,
    constraints: list[str],
) -> dict[str, Any]:
    return {
        "id": f"obj-{idx}",
        "title": title,
        "metric": metric,
        "target": target,
        "priority": priority,
        "constraints": constraints,
    }


def _append_objective(
    objectives: list[dict[str, Any]],
    title: str,
    metric: str,
    target: str,
    priority: int,
    constraints: list[str],
) -> None:
    lowered = title.lower()
    if any(existing["title"].lower() == lowered for existing in objectives):
        return
    objectives.append(_objective(len(objectives) + 1, title, metric, target, priority, constraints))


def _base_constraints(safety_profile: str) -> list[str]:
    if safety_profile == "closed-loop-pilot":
        return [
            "simulation only until institutional review",
            "closed loop containment",
            "must include shutdown logic",
            "must include telemetry",
        ]
    if safety_profile == "contained-field-pilot":
        return [
            "simulation only until institutional review",
            "must include layered biocontainment",
            "must include auxotrophy",
            "must include telemetry",
        ]
    return [
        "simulation only",
        "must include containment",
        "must include shutdown logic",
    ]


def generate_mission_spec(payload: dict[str, Any]) -> dict[str, Any]:
    """Generate a validated mission spec plus builder research notes."""
    name = _normalize_text(payload.get("name"), "Custom Mission")
    domain = _normalize_text(payload.get("domain"), "industrial-remediation")
    deployment_context = _normalize_text(payload.get("deployment_context"), "closed bioreactor pilot")
    environment_name = _normalize_text(payload.get("environment_name"), "custom environment")
    problem_focus = _normalize_text(payload.get("problem_focus"), "mission planning")
    architecture_preference = _normalize_text(payload.get("architecture_preference"), "auto")
    safety_profile = _normalize_text(payload.get("safety_profile"), "simulation-only")

    atmosphere = _normalize_list(payload.get("atmosphere"))
    nutrients = _normalize_list(payload.get("nutrients"))
    stressors = _normalize_list(payload.get("stressors"))
    custom_constraints = _normalize_list(payload.get("custom_constraints"))

    primary_title = _normalize_text(payload.get("primary_objective_title"), "Improve mission performance")
    primary_metric = _normalize_text(payload.get("primary_objective_metric"), "relative process performance")
    primary_target = _normalize_text(payload.get("primary_objective_target"), ">=25% improvement in simulation")
    secondary_title = _normalize_text(payload.get("secondary_objective_title"))
    secondary_metric = _normalize_text(payload.get("secondary_objective_metric"), "system stability")
    secondary_target = _normalize_text(payload.get("secondary_objective_target"), ">=90% stable runtime in digital twin")

    guard_text = " ".join(
        [
            name,
            domain,
            deployment_context,
            environment_name,
            problem_focus,
            primary_title,
            secondary_title,
            *stressors,
            *custom_constraints,
        ]
    ).lower()
    if any(term in guard_text for term in BLOCKED_TERMS):
        raise ValueError(
            "Mission builder supports only safe, simulation-first industrial, environmental, and habitat missions."
        )

    combined_text = " ".join([domain, deployment_context, environment_name, problem_focus, *stressors]).lower()
    is_offworld = any(token in combined_text for token in ("mars", "lunar", "offworld", "space", "regolith", "habitat"))
    closed_loop = any(token in combined_text for token in ("closed", "reactor", "bioreactor", "habitat", "pilot"))
    prefers_consortium = architecture_preference == "consortium" or len(stressors) >= 3

    objectives: list[dict[str, Any]] = []
    _append_objective(
        objectives,
        primary_title,
        primary_metric,
        primary_target,
        10,
        ["must remain within simulation-first workflows"],
    )
    if secondary_title:
        _append_objective(objectives, secondary_title, secondary_metric, secondary_target, 8, custom_constraints[:1])

    research_notes: list[dict[str, str]] = []
    biosafety_constraints = _base_constraints(safety_profile)

    if closed_loop or "telemetry" in problem_focus.lower() or "control" in problem_focus.lower():
        _append_objective(
            objectives,
            "Maintain observability and control",
            "sensor coverage and control-loop uptime",
            ">=95% telemetry coverage in digital twin",
            9,
            ["online monitoring must remain active across stress excursions"],
        )
        biosafety_constraints.append("must include online telemetry in the digital twin")
        research_notes.append({"id": "digital_twin_controls", **RESEARCH_LIBRARY["digital_twin_controls"]})

    if prefers_consortium:
        _append_objective(
            objectives,
            "Maintain community balance",
            "population composition drift",
            "<=10% drift over 120h digital twin",
            8,
            ["prefer division-of-labor or self-regulated community control"],
        )
        biosafety_constraints.append("must model community balance control")
        research_notes.append({"id": "consortium_homeostasis", **RESEARCH_LIBRARY["consortium_homeostasis"]})

    if safety_profile != "simulation-only" or "field" in deployment_context.lower():
        _append_objective(
            objectives,
            "Validate layered containment",
            "simulated escape probability",
            "<=0.1% escape probability under perturbation sweep",
            9,
            ["layered containment must be represented before any non-simulation stage"],
        )
        biosafety_constraints.append("must include genetic firewall or equivalent containment logic")
        research_notes.append({"id": "biocontainment_layering", **RESEARCH_LIBRARY["biocontainment_layering"]})

    if is_offworld:
        _append_objective(
            objectives,
            "Close the resource recycle loop",
            "recycled nutrient substitution",
            ">=60% nutrient replacement in simulation",
            8,
            ["use local mineral or waste-derived inputs where possible"],
        )
        biosafety_constraints.append("must quantify nutrient recycle efficiency")
        research_notes.append({"id": "offworld_resource_loops", **RESEARCH_LIBRARY["offworld_resource_loops"]})

    biosafety_constraints.extend(custom_constraints)
    seen_constraints: set[str] = set()
    deduped_constraints: list[str] = []
    for item in biosafety_constraints:
        key = item.lower()
        if item and key not in seen_constraints:
            deduped_constraints.append(item)
            seen_constraints.add(key)

    summary_capabilities = ["containment", "telemetry"]
    if prefers_consortium:
        summary_capabilities.append("community balance control")
    if is_offworld:
        summary_capabilities.append("resource recycling")

    architecture_phrase = {
        "consortium": "with a division-of-labor consortium bias",
        "single-chassis": "with a tightly monitored single-chassis bias",
        "living-material": "with a living-material surface bias",
        "hybrid-consortium": "with a hybrid consortium-material bias",
    }.get(architecture_preference, "with an adaptive architecture bias")

    mission_dict = {
        "name": name,
        "summary": (
            f"Design a safe simulation-first {problem_focus.lower()} program for {deployment_context} "
            f"in {environment_name} {architecture_phrase} and {', '.join(summary_capabilities)}."
        ),
        "domain": domain,
        "deployment_context": deployment_context,
        "biosafety_constraints": deduped_constraints,
        "disallowed_capabilities": SAFE_DISALLOWED_CAPABILITIES,
        "allowed_modalities": SAFE_ALLOWED_MODALITIES,
        "environment": {
            "name": environment_name,
            "temperature_range_c": [
                _normalize_float(payload.get("temperature_min_c"), 10.0),
                _normalize_float(payload.get("temperature_max_c"), 32.0),
            ],
            "radiation_level": _normalize_float(payload.get("radiation_level"), 1.0),
            "salinity_ppt": _normalize_float(payload.get("salinity_ppt"), 10.0),
            "ph_range": [
                _normalize_float(payload.get("ph_min"), 6.5),
                _normalize_float(payload.get("ph_max"), 8.0),
            ],
            "gravity_g": _normalize_float(payload.get("gravity_g"), 1.0),
            "atmosphere": atmosphere or ["air"],
            "nutrients": nutrients or ["trace minerals"],
            "stressors": stressors or ["process variability"],
        },
        "objectives": objectives,
    }

    mission = MissionSpec.from_dict(mission_dict)
    return {
        "mission": mission.to_dict(),
        "research_notes": research_notes,
        "builder_summary": "Generated a simulation-first mission spec with research-backed safety and control objectives.",
    }


__all__ = ["RESEARCH_LIBRARY", "generate_mission_spec"]
