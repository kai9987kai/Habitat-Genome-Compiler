"""Xenobiology assessment for orthogonal biocontainment options."""

from __future__ import annotations

from .models import CandidateProgram, EnvironmentSpec


def _environment_escape_pressure(env: EnvironmentSpec) -> float:
    return min(
        10.0,
        round(
            0.4 * env.radiation_level
            + 0.06 * env.salinity_ppt
            + 0.9 * len(env.stressors)
            + 4.0 * abs(1.0 - env.gravity_g),
            2,
        ),
    )


def evaluate_xenobiology(
    candidate: CandidateProgram,
    env: EnvironmentSpec,
    biosafety_tier: str,
) -> tuple[float, list[str]]:
    """Recommend orthogonal biology when containment pressure is high."""
    tier_lower = biosafety_tier.lower()
    escape_pressure = _environment_escape_pressure(env)
    xeno_candidate = any(
        token in module.lower()
        for module in candidate.modules
        for token in ("xeno", "orthogonal", "recoded", "cell-free")
    )

    if xeno_candidate or tier_lower in {"elevated", "blocked"} or escape_pressure >= 6.0:
        score = 8.5 if xeno_candidate else 6.5
        features = [
            "Orthogonal translation system recommended to reduce cross-talk with natural ribosomes.",
            "Swapped-code or recoded payload channels recommended to interrupt horizontal gene transfer.",
        ]
        if escape_pressure >= 7.5:
            features.append("High escape pressure suggests cell-free or chemically dependent execution windows.")
        return score, features

    return 2.0, ["Standard DNA/RNA execution; no xenobiology layer was triggered."]
