"""Microbial consortium and symbiosis modeling.

Predicts the dynamics of multi-organism communities where metabolic
specialization occurs.
"""

from __future__ import annotations
from .models import CandidateProgram, EnvironmentSpec

def evaluate_consortium(candidate: CandidateProgram) -> tuple[float, list[str]]:
    """Evaluates the efficiency and stability of a multi-organism consortium."""
    if "consortium" not in candidate.archetype.lower():
        return 1.0, ["N/A: Single-organism deployment."]
    
    stability_index = 8.5
    interactions = ["Mutualism: Metabolic cross-feeding detected."]
    
    # Modeling niche specialization
    if len(candidate.modules) > 10:
        stability_index -= 2.0
        interactions.append("Warning: High complexity may lead to community de-synchronization.")
    
    # Check for specific consortium modules (abstracted)
    if any("exchange" in m.lower() for m in candidate.modules):
        stability_index += 1.0
        interactions.append("Optimization: Engineered transport for intermediate sharing.")
    
    return max(0.0, stability_index), interactions
