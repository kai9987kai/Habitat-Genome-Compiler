"""Evolutionary stability and genetic lock-in modeling.

Predicts the long-term stability of engineered traits and proposes
strategies to prevent 'evolutionary escape'.
"""

from __future__ import annotations
from .models import CandidateProgram, EnvironmentSpec

def calculate_evolutionary_risk(candidate: CandidateProgram, env: EnvironmentSpec) -> tuple[float, list[str]]:
    """Predicts a 0-10 evolutionary risk score (higher = more likely to lose trait)."""
    base_risk = 3.0
    strategies = []
    
    # 1. Mutational Pressure from Environment
    if env.radiation_level > 10.0:
        base_risk += 4.0
        strategies.append("Recommendation: Implement quintuple-redundant DNA repair pathways.")
    
    # 2. Metabolic Burden Conflict
    # If the flux burden is high, evolution will favor 'cheaters' who drop the pathway
    if candidate.flux and candidate.flux.metabolic_burden > 0.4:
        base_risk += 3.0
        strategies.append("Risk: High metabolic burden favors non-producing mutants.")
        strategies.append("Lock-in: Link essential amino acid synthesis to the production pathway.")

    # 3. Trait Complexity
    if len(candidate.modules) > 5:
        base_risk += 2.0
        strategies.append("Risk: Large genetic constructs increase recombination target size.")

    # 4. Propose Genetic Lock-in
    if base_risk > 5.0:
        strategies.append("Lock-in Proposal: Use codon-shuffling to minimize sequence homology.")
        strategies.append("Lock-in Proposal: Overlap essential gene open reading frames (ORFs).")

    return min(10.0, base_risk), strategies
