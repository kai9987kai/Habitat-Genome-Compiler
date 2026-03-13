"""Digital Twin Time-Series Simulator for Habitat Genome Compiler."""

import math
from habitat_genome_compiler.models import CandidateProgram, MissionSpec, GrowthSimulation
from habitat_genome_compiler.adapters import HabitatProfile

def simulate_growth(mission: MissionSpec, candidate: CandidateProgram, habitat: HabitatProfile) -> GrowthSimulation:
    """
    Simulates a 72-hour growth and production run using an ODE proxy system.
    Predicts biomass (OD600) and product titer (g/L) over time, factoring in
    metabolic burden, habitat severity, and consortium dynamics.
    """
    # Base parameters
    base_mu_max = 0.8  # max specific growth rate (1/h)
    base_carrying_capacity = 10.0  # max OD600
    
    # Extract metabolic constraints from FBA if applied
    burden_multiplier = 1.0
    yield_efficiency = 0.7
    if hasattr(candidate, "flux") and candidate.flux:
        burden_multiplier += candidate.flux.metabolic_burden
        yield_efficiency = candidate.flux.theoretical_yield

    # Scale parameters
    mu_max = base_mu_max * (1.0 - (habitat.severity * 0.05)) / burden_multiplier
    k = base_carrying_capacity * (1.0 - (habitat.severity * 0.02))
    mu_max = max(0.01, mu_max)
    k = max(0.5, k)
    
    # Consortium drag
    if "consortium" in candidate.archetype.lower():
        mu_max *= 0.8  # Growth is slower as sub-populations equilibrate
        k *= 1.2       # Higher overall capacity usually
    
    # ODE Simulation Variables (72 hours, 1 hour steps)
    time_points = []
    biomass = []
    product = []
    
    current_od = 0.1  # Initial inoculum
    current_product = 0.0
    dt = 1.0
    
    for t in range(73):
        time_points.append(float(t))
        biomass.append(round(current_od, 3))
        product.append(round(current_product, 3))
        
        # Logistic growth step: dX/dt = mu * X * (1 - X/K)
        growth_rate = mu_max * current_od * (1 - current_od / k)
        dx = growth_rate * dt
        current_od += dx
        current_od = max(0.1, current_od)
        
        # Luedeking-Piret product formation step: dP/dt = alpha * dX/dt + beta * X
        # Alpha (growth-associated), Beta (non-growth associated)
        alpha = yield_efficiency * 0.5
        beta = yield_efficiency * 0.05
        
        dp = (alpha * growth_rate + beta * current_od) * dt
        current_product += dp

    return GrowthSimulation(
        time_points_h=time_points,
        biomass_od600=biomass,
        product_titer_gl=product,
        peak_growth_rate=round(mu_max, 3),
        carrying_capacity=round(k, 3)
    )
