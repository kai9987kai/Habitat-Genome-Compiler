"""Regulatory compliance & GLP documentation generator (Phase 8).

Automatically generates a regulatory readiness checklist and GLP
documentation skeleton based on the mission's deployment context,
biosafety tier, and target jurisdiction.
"""

from __future__ import annotations

from .models import CompileResult


_JURISDICTION_FRAMEWORKS: dict[str, list[str]] = {
    "us": [
        "FDA 21 CFR Part 58 (GLP)",
        "EPA TSCA Biotechnology Notification",
        "USDA APHIS Permit (if plant-associated)",
        "NIH Guidelines for Research Involving rDNA",
    ],
    "eu": [
        "EU Directive 2001/18/EC (Deliberate Release)",
        "EU Regulation 1829/2003 (GMO Food/Feed)",
        "OECD GLP Principles (ENV/MC/CHEM(98)17)",
    ],
    "kr": [
        "Synthetic Biology Promotion Act (April 2026)",
        "K-BioSafety Framework",
    ],
    "default": [
        "Cartagena Protocol on Biosafety",
        "OECD GLP Principles",
        "Local Institutional Biosafety Committee (IBC) Review",
    ],
}


def _infer_jurisdiction(result: CompileResult) -> str:
    """Infer target jurisdiction from mission metadata."""
    haystack = (result.mission.summary + " " + result.mission.deployment_context).lower()
    if any(tok in haystack for tok in ("us", "usa", "fda", "epa", "nih")):
        return "us"
    if any(tok in haystack for tok in ("eu", "europe", "ema")):
        return "eu"
    if any(tok in haystack for tok in ("korea", "kr", "korean")):
        return "kr"
    return "default"


def generate_regulatory_report(result: CompileResult) -> tuple[float, list[str], list[str]]:
    """Generate a regulatory readiness score, checklist, and applicable frameworks.

    Returns (readiness_score, checklist_items, applicable_frameworks).
    """
    jurisdiction = _infer_jurisdiction(result)
    frameworks = _JURISDICTION_FRAMEWORKS[jurisdiction]

    checklist: list[str] = []
    readiness = 5.0  # base score

    # Biosafety documentation
    if result.allowed:
        checklist.append("[PASS] Mission cleared biosafety screening.")
        readiness += 1.0
    else:
        checklist.append("[FAIL] Mission BLOCKED by biosafety screening. Cannot proceed to GLP.")
        readiness -= 3.0

    # Containment plan
    if result.containment_plan and result.containment_plan.active_strategies:
        strategy_count = len(result.containment_plan.active_strategies)
        checklist.append(f"[PASS] Biocontainment plan present ({strategy_count} active strategies).")
        readiness += min(2.0, strategy_count * 0.5)
    else:
        checklist.append("[WARN] No active biocontainment plan generated.")

    # Deployment context risk
    context_lower = result.mission.deployment_context.lower()
    if any(tok in context_lower for tok in ("open", "field")):
        checklist.append("[WARN] Open/field deployment requires additional environmental impact assessment.")
        readiness -= 1.0
    elif "contained" in context_lower or "closed" in context_lower:
        checklist.append("[PASS] Contained deployment context reduces regulatory burden.")
        readiness += 0.5

    # Candidate quality
    if result.candidates:
        checklist.append(f"[INFO] {len(result.candidates)} candidate designs available for review.")
    else:
        checklist.append("[WARN] No candidate designs generated.")
        readiness -= 1.0

    # Risk tier escalation
    if result.risk_tier in ("elevated", "blocked"):
        checklist.append(f"[WARN] Risk tier '{result.risk_tier}' requires elevated regulatory scrutiny.")
        readiness -= 1.5
    elif result.risk_tier in ("negligible", "low"):
        checklist.append(f"[PASS] Risk tier '{result.risk_tier}' is within standard regulatory bounds.")
        readiness += 0.5

    # GLP documentation skeleton
    checklist.append("[TODO] Prepare Standard Operating Procedures (SOPs) for all wet-lab transitions.")
    checklist.append("[TODO] Assign a Study Director and Quality Assurance Unit per GLP requirements.")
    checklist.append("[TODO] Archive this compilation dossier as the pre-study plan.")

    readiness = round(min(10.0, max(0.0, readiness)), 1)
    return readiness, checklist, frameworks
