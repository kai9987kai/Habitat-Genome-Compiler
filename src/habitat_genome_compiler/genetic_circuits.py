"""Genetic circuit design automation (Cello-style).

Inspired by the 2016 Cello framework and 2026 iTidetron AI engine, this module
compiles high-level logical intent from mission objectives into a predicted
genetic circuit topology and estimates its reliability.
"""

from __future__ import annotations

from .models import CandidateProgram, MissionSpec


_GATE_LIBRARY = {
    "sensor": {"label": "Environmental Sensor", "reliability": 0.95},
    "not": {"label": "NOT Inverter", "reliability": 0.92},
    "and": {"label": "AND Gate (split-intein)", "reliability": 0.88},
    "or": {"label": "OR Gate (tandem promoter)", "reliability": 0.91},
    "output": {"label": "Reporter / Actuator", "reliability": 0.97},
}


def _infer_circuit(mission: MissionSpec, candidate: CandidateProgram) -> list[dict[str, str]]:
    """Infer a minimal genetic circuit from mission objectives and candidate modules."""
    gates: list[dict[str, str]] = []
    haystack = " ".join(
        [mission.summary, mission.domain]
        + [o.title for o in mission.objectives]
        + candidate.modules
    ).lower()

    # Every circuit starts with an environmental sensor
    gates.append({"type": "sensor", "note": "Detect deployment-environment signal"})

    if any(kw in haystack for kw in ("capture", "degrade", "remediation", "fixation")):
        gates.append({"type": "and", "note": "Require sensor AND metabolic readiness"})
    if any(kw in haystack for kw in ("shutdown", "kill", "failsafe", "containment")):
        gates.append({"type": "not", "note": "Invert viability signal for kill-switch"})
    if any(kw in haystack for kw in ("consortium", "division", "community")):
        gates.append({"type": "or", "note": "Accept signal from any consortium member"})

    gates.append({"type": "output", "note": "Actuate target metabolic pathway"})
    return gates


def compile_genetic_circuit(
    mission: MissionSpec,
    candidate: CandidateProgram,
) -> tuple[float, list[str], list[dict[str, str]]]:
    """Compile a genetic circuit and return reliability score, findings, and gate list."""
    gates = _infer_circuit(mission, candidate)

    # Circuit reliability = product of individual gate reliabilities
    reliability = 1.0
    for gate in gates:
        reliability *= _GATE_LIBRARY.get(gate["type"], {"reliability": 0.90})["reliability"]

    score = round(reliability * 10.0, 1)
    findings: list[str] = []

    findings.append(f"Circuit depth: {len(gates)} logic gates.")
    for gate in gates:
        lib = _GATE_LIBRARY.get(gate["type"], {"label": gate["type"], "reliability": 0.90})
        findings.append(f"  Gate [{lib['label']}]: {gate['note']} (reliability {lib['reliability']:.0%})")

    if score >= 8.0:
        findings.append("High predicted circuit reliability; suitable for autonomous deployment.")
    elif score >= 6.0:
        findings.append("Moderate circuit reliability; add redundant logic or error-correcting insulation parts.")
    else:
        findings.append("Low reliability; simplify circuit or use cell-free prototyping before in-vivo assembly.")

    return score, findings, gates
