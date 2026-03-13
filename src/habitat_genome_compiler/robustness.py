"""Monte Carlo robustness envelope for candidate programs.

Applies perturbation-based sensitivity analysis to evaluate how each
candidate's score degrades under environmental uncertainty.  Based on
2024 Monte Carlo sensitivity frameworks for synthetic gene networks.
"""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field

from .adapters import HabitatProfile, build_habitat_profile
from .models import CandidateProgram, MissionSpec
from .scoring import _score_axes


@dataclass(slots=True)
class RobustnessReport:
    """Per-candidate summary of Monte Carlo robustness analysis."""

    candidate_id: str
    mean_total: float
    std_total: float
    failure_rate: float
    sensitivity: dict[str, float] = field(default_factory=dict)


def perturb_environment(env_dict: dict, noise_pct: float, rng: random.Random) -> dict:
    """Return a shallow-mutated copy of environment kwargs with Gaussian noise."""
    result = dict(env_dict)

    def _jitter(value: float) -> float:
        return value + rng.gauss(0, abs(value * noise_pct) + 0.01)

    temp = list(result["temperature_range_c"])
    temp[0] = _jitter(temp[0])
    temp[1] = _jitter(temp[1])
    if temp[0] > temp[1]:
        temp[0], temp[1] = temp[1], temp[0]
    result["temperature_range_c"] = tuple(temp)

    result["radiation_level"] = max(0.0, _jitter(result["radiation_level"]))
    result["salinity_ppt"] = max(0.0, _jitter(result["salinity_ppt"]))

    ph = list(result["ph_range"])
    ph[0] = max(0.0, min(14.0, _jitter(ph[0])))
    ph[1] = max(0.0, min(14.0, _jitter(ph[1])))
    if ph[0] > ph[1]:
        ph[0], ph[1] = ph[1], ph[0]
    result["ph_range"] = tuple(ph)

    result["gravity_g"] = max(0.0, _jitter(result["gravity_g"]))
    return result


def _env_to_dict(env) -> dict:
    """Convert an EnvironmentSpec to a plain dict for perturbation."""
    return {
        "name": env.name,
        "temperature_range_c": list(env.temperature_range_c),
        "radiation_level": env.radiation_level,
        "salinity_ppt": env.salinity_ppt,
        "ph_range": list(env.ph_range),
        "gravity_g": env.gravity_g,
        "atmosphere": list(env.atmosphere),
        "nutrients": list(env.nutrients),
        "stressors": list(env.stressors),
    }


def _total_score(scores: dict[str, float]) -> float:
    return (
        scores["mission_fit"] * 0.35
        + scores["habitat_fit"] * 0.25
        + scores["feasibility"] * 0.2
        + scores["biosafety_margin"] * 0.2
    )


def _sensitivity_analysis(
    mission: MissionSpec,
    candidate: CandidateProgram,
    env_base: dict,
    delta: float = 0.05,
) -> dict[str, float]:
    """Finite-difference sensitivity: ∂total/∂param for each numeric param."""
    from .models import EnvironmentSpec

    base_mission = copy.deepcopy(mission)
    base_mission.environment = EnvironmentSpec.from_dict(env_base)
    base_habitat = build_habitat_profile(base_mission)
    base_total = _total_score(_score_axes(base_mission, base_habitat, candidate))

    params = {
        "radiation_level": env_base["radiation_level"],
        "salinity_ppt": env_base["salinity_ppt"],
        "gravity_g": env_base["gravity_g"],
    }

    sensitivity: dict[str, float] = {}
    for param, val in params.items():
        perturbed = dict(env_base)
        perturbed[param] = val + max(abs(val) * delta, 0.01)
        p_mission = copy.deepcopy(mission)
        p_mission.environment = EnvironmentSpec.from_dict(perturbed)
        p_habitat = build_habitat_profile(p_mission)
        p_total = _total_score(_score_axes(p_mission, p_habitat, candidate))
        step = perturbed[param] - val
        sensitivity[param] = round((p_total - base_total) / step, 4) if step else 0.0

    return sensitivity


def robustness_sweep(
    mission: MissionSpec,
    candidates: list[CandidateProgram],
    n_samples: int = 200,
    noise_pct: float = 0.15,
    failure_threshold: float = 4.0,
    seed: int = 42,
) -> list[RobustnessReport]:
    """Run Monte Carlo perturbation analysis for each candidate."""
    from .models import EnvironmentSpec

    rng = random.Random(seed)
    env_base = _env_to_dict(mission.environment)
    reports: list[RobustnessReport] = []

    for candidate in candidates:
        totals: list[float] = []
        failures = 0

        for _ in range(n_samples):
            p_env = perturb_environment(env_base, noise_pct, rng)
            p_mission = copy.deepcopy(mission)
            p_mission.environment = EnvironmentSpec.from_dict(p_env)
            p_habitat = build_habitat_profile(p_mission)
            scores = _score_axes(p_mission, p_habitat, candidate)
            total = _total_score(scores)
            totals.append(total)
            if total < failure_threshold:
                failures += 1

        mean_t = sum(totals) / len(totals)
        std_t = (sum((t - mean_t) ** 2 for t in totals) / len(totals)) ** 0.5

        sensitivity = _sensitivity_analysis(mission, candidate, env_base)

        reports.append(
            RobustnessReport(
                candidate_id=candidate.id,
                mean_total=round(mean_t, 4),
                std_total=round(std_t, 4),
                failure_rate=round(failures / n_samples, 4),
                sensitivity=sensitivity,
            )
        )

    return reports
