"""Environmental stability and proteostasis modeling.

Predicts how well a candidate's proteome and genetic architecture will
remain stable under the specified environmental stressors.
"""

from __future__ import annotations
from .models import CandidateProgram, EnvironmentSpec

def calculate_stability_score(candidate: CandidateProgram, env: EnvironmentSpec) -> tuple[float, list[str]]:
    """Calculates a proteostasis stability score from 0-10."""
    score = 8.0  # Base stability for a 'standard' chassis
    findings = []
    
    # 1. Temperature Adaptation
    # Proxy: Thermophily correlates with high charged/hydrophobic ratio
    low_t, high_t = env.temperature_range_c
    if high_t > 80:  # Hyperthermophilic
        if "thermophile" in candidate.archetype.lower():
            score += 1.0
            findings.append("Match: Hyperthermophilic chassis selected for volcanic environment.")
        else:
            score -= 5.0
            findings.append("Critical: Proteome instability expected at >80°C without specialized chaperones.")
    elif high_t > 45:  # Thermophilic
        if "thermophile" in candidate.archetype.lower():
            score += 0.5
        else:
            score -= 2.0
            findings.append("Warning: Thermal stress may inhibit enzymatic throughput.")

    # 2. Salinity (Halophilicity)
    if env.salinity_ppt > 100:  # Hypersaline
        if "halophile" in candidate.archetype.lower():
            score += 1.0
            findings.append("Match: Halophilic acidic proteome maintains hydration in hypersaline context.")
        else:
            score -= 4.0
            findings.append("Critical: Osmotic collapse likely in hypersaline environment.")

    # 3. Radiation Resilience
    if env.radiation_level > 5.0:  # High radiation (kGy/hr proxy)
        if any("repair" in mod.lower() for mod in candidate.modules):
            score += 0.5
            findings.append("Resilience: Enhanced DNA repair machinery detected.")
        else:
            score -= 3.0
            findings.append("Warning: Accelerated mutation rates expected due to radiation damage.")

    # 4. Acid/Base Stress
    ph_low, ph_high = env.ph_range
    if ph_low < 3.0:
        if "acidophile" in candidate.archetype.lower():
            score += 1.0
        else:
            score -= 3.0
            findings.append("Warning: Low pH may denature surface proteins.")

    return max(0.0, min(10.0, score)), findings
