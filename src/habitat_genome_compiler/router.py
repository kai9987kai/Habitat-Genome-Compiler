"""Mission-aware expert routing inspired by a mixture-of-experts control plane."""

from __future__ import annotations

from .models import MissionSpec


def select_experts(mission: MissionSpec) -> list[str]:
    experts = [
        "mission-architect",
        "biosafety-governor",
        "automation-planner",
        "genome-architect",
        "regulatory-programmer",
        "phenotype-critic",
    ]

    if mission.environment.radiation_level >= 4:
        experts.append("radiation-hardening-specialist")

    if mission.environment.salinity_ppt >= 35:
        experts.append("osmotic-stability-specialist")

    if len(mission.environment.stressors) >= 3:
        experts.append("consortium-designer")

    summary = " ".join(
        [mission.summary, mission.domain, *mission.environment.stressors, *mission.environment.nutrients]
    ).lower()

    if any(token in summary for token in ("pfas", "waste", "remediation", "degradation")):
        experts.append("industrial-remediation-specialist")

    if any(token in summary for token in ("mars", "lunar", "space", "radiation", "low gravity", "regolith")):
        experts.append("habitat-systems-specialist")

    if any(token in summary for token in ("biofilm", "material", "coating", "infrastructure")):
        experts.append("living-materials-designer")

    if any(token in summary for token in ("telemetry", "digital twin", "control-loop", "observability", "sensor")):
        experts.append("digital-twin-controls-specialist")

    if any(token in summary for token in ("recycle", "regolith", "waste carbon", "resource loop")):
        experts.append("resource-loop-specialist")

    experts.append("workflow-compiler")

    seen: set[str] = set()
    ordered: list[str] = []
    for expert in experts:
        if expert not in seen:
            ordered.append(expert)
            seen.add(expert)
    return ordered
