"""Multi-objective ranking for candidate programs.

Implements NSGA-II-inspired Pareto-frontier ranking with crowding-distance
diversity preservation, based on the SYNBADm / MOODA multi-objective
optimisation frameworks used in genetic design automation.
"""

from __future__ import annotations

from .adapters import HabitatProfile
from .models import CandidateProgram, MissionSpec

# ---------------------------------------------------------------------------
# Axis scoring (unchanged logic, cleaner structure)
# ---------------------------------------------------------------------------

_OBJECTIVE_AXES = ("mission_fit", "habitat_fit", "feasibility", "biosafety_margin")


def _score_axes(
    mission: MissionSpec, habitat: HabitatProfile, candidate: CandidateProgram
) -> dict[str, float]:
    """Compute the four raw scoring axes for a single candidate."""
    objective_text = " ".join(o.title.lower() for o in mission.objectives)
    needs_materials = any(t in objective_text for t in ("coating", "surface", "material"))
    needs_remediation = any(t in objective_text for t in ("pfas", "remediation", "degradation"))
    needs_carbon = any(t in objective_text for t in ("carbon", "capture", "fixation"))

    mission_fit = 5.0
    habitat_fit = 5.0
    feasibility = 6.0
    biosafety_margin = 8.0

    if candidate.archetype == "consortium":
        mission_fit += 2.0
        habitat_fit += 1.5 if habitat.severity >= 5 else 0.5
        feasibility -= 1.0
    elif candidate.archetype == "single-chassis":
        feasibility += 1.5
        habitat_fit += 0.5
    elif candidate.archetype == "living-material":
        biosafety_margin += 0.8
        habitat_fit += 1.0 if needs_materials else 0.0
    elif candidate.archetype == "hybrid-consortium":
        mission_fit += 1.5
        habitat_fit += 1.2 if habitat.severity >= 5 else 0.3
        feasibility -= 0.5
        biosafety_margin += 0.4
    elif candidate.archetype == "phage-assisted":
        mission_fit += 1.0
        habitat_fit += 1.0
        feasibility -= 1.5
        biosafety_margin -= 0.3

    if needs_remediation and "pollutant capture and conversion layer" in candidate.modules:
        mission_fit += 1.8
    if needs_carbon and any("carbon" in m for m in candidate.modules):
        mission_fit += 1.4
    if needs_materials and candidate.archetype == "living-material":
        mission_fit += 2.0

    if habitat.severity >= 6 and "extreme-environment hardening" in candidate.modules:
        habitat_fit += 1.8
    if "containment logic" in candidate.modules:
        biosafety_margin += 0.7
    if "shutdown sentinel" in candidate.modules:
        biosafety_margin += 0.7

    return {
        "mission_fit": round(mission_fit, 2),
        "habitat_fit": round(habitat_fit, 2),
        "feasibility": round(feasibility, 2),
        "biosafety_margin": round(biosafety_margin, 2),
    }


# ---------------------------------------------------------------------------
# Pareto-frontier ranking (NSGA-II convention)
# ---------------------------------------------------------------------------


def _dominates(a: dict[str, float], b: dict[str, float]) -> bool:
    """Return True if *a* Pareto-dominates *b* (all axes >= and at least one >)."""
    dominated = False
    for axis in _OBJECTIVE_AXES:
        if a[axis] < b[axis]:
            return False
        if a[axis] > b[axis]:
            dominated = True
    return dominated


def pareto_rank(candidates: list[CandidateProgram]) -> list[CandidateProgram]:
    """Assign ``pareto_front`` and ``crowding_distance`` to each candidate.

    Front 0 = non-dominated best.  Within a front, higher crowding distance
    means the candidate occupies a less crowded region of the objective space
    (NSGA-II diversity preservation).
    """
    remaining = list(range(len(candidates)))
    front_idx = 0

    while remaining:
        front: list[int] = []
        for i in remaining:
            is_dominated = False
            for j in remaining:
                if i != j and _dominates(candidates[j].scores, candidates[i].scores):
                    is_dominated = True
                    break
            if not is_dominated:
                front.append(i)
        for i in front:
            candidates[i].scores["pareto_front"] = float(front_idx)
            remaining.remove(i)
        _assign_crowding(candidates, front)
        front_idx += 1

    return sorted(
        candidates,
        key=lambda c: (c.scores["pareto_front"], -c.scores["crowding_distance"]),
    )


def _assign_crowding(candidates: list[CandidateProgram], front: list[int]) -> None:
    """Compute crowding distance for one Pareto front."""
    for i in front:
        candidates[i].scores["crowding_distance"] = 0.0

    if len(front) <= 2:
        for i in front:
            candidates[i].scores["crowding_distance"] = float("inf")
        return

    for axis in _OBJECTIVE_AXES:
        ordered = sorted(front, key=lambda i: candidates[i].scores[axis])
        lo = candidates[ordered[0]].scores[axis]
        hi = candidates[ordered[-1]].scores[axis]
        span = hi - lo if hi != lo else 1.0
        candidates[ordered[0]].scores["crowding_distance"] = float("inf")
        candidates[ordered[-1]].scores["crowding_distance"] = float("inf")
        for k in range(1, len(ordered) - 1):
            diff = candidates[ordered[k + 1]].scores[axis] - candidates[ordered[k - 1]].scores[axis]
            candidates[ordered[k]].scores["crowding_distance"] += diff / span


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def score_candidates(
    mission: MissionSpec, habitat: HabitatProfile, candidates: list[CandidateProgram]
) -> list[CandidateProgram]:
    """Score, Pareto-rank, and sort candidates."""
    for candidate in candidates:
        candidate.scores = _score_axes(mission, habitat, candidate)
        s = candidate.scores
        s["total"] = round(
            s["mission_fit"] * 0.35
            + s["habitat_fit"] * 0.25
            + s["feasibility"] * 0.2
            + s["biosafety_margin"] * 0.2,
            2,
        )
    return pareto_rank(candidates)
