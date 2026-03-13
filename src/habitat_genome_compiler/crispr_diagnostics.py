"""CRISPR diagnostics designer (Phase 8).

Inspired by SHERLOCK and DETECTR platforms. This module evaluates whether a
candidate's deployment context would benefit from a CRISPR-based environmental
biosensor for field monitoring, contamination detection, or containment
verification.
"""

from __future__ import annotations

from .models import CandidateProgram, MissionSpec


_DIAGNOSTIC_TARGETS = {
    "contamination": {"assay": "Cas12a-DETECTR", "target": "Environmental contaminant DNA", "sensitivity": "aM"},
    "pathogen": {"assay": "Cas13a-SHERLOCK", "target": "Pathogen RNA signature", "sensitivity": "aM"},
    "escape": {"assay": "Cas12a-DETECTR", "target": "Engineered construct outside containment boundary", "sensitivity": "fM"},
    "consortium": {"assay": "Cas13a-SHERLOCKv2", "target": "Multi-species community balance RNA", "sensitivity": "fM"},
    "expression": {"assay": "Cas12a-lateral-flow", "target": "Reporter transcript abundance", "sensitivity": "pM"},
}


def design_crispr_diagnostic(
    candidate: CandidateProgram,
    mission: MissionSpec,
) -> tuple[float, list[dict[str, str]]]:
    """Design CRISPR diagnostic assays relevant to the mission context."""
    haystack = " ".join(
        [mission.summary, mission.domain, mission.deployment_context]
        + [o.title for o in mission.objectives]
        + candidate.modules
    ).lower()

    assays: list[dict[str, str]] = []

    for keyword, config in _DIAGNOSTIC_TARGETS.items():
        if keyword in haystack:
            assays.append({
                "keyword": keyword,
                "assay": config["assay"],
                "target": config["target"],
                "sensitivity": config["sensitivity"],
            })

    # Always recommend escape detection for open/field deployments
    context_lower = mission.deployment_context.lower()
    if any(tok in context_lower for tok in ("open", "field", "semi-open")):
        escape_assay = {
            "keyword": "escape-monitoring",
            "assay": "Cas12a-DETECTR",
            "target": "Engineered construct detection outside approved perimeter",
            "sensitivity": "fM",
        }
        if not any(a["keyword"] == "escape" for a in assays):
            assays.append(escape_assay)

    relevance_score = round(min(10.0, len(assays) * 3.5), 1)
    return relevance_score, assays
