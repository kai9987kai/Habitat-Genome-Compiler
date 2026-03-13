"""Tests for the Digital Twin Time-Series Simulator."""

import pytest

from habitat_genome_compiler.models import CandidateProgram, MissionEnvironment, MissionSpec
from habitat_genome_compiler.adapters import HabitatProfile
from habitat_genome_compiler.simulation import simulate_growth

@pytest.fixture
def base_mission() -> MissionSpec:
    from habitat_genome_compiler.models import EnvironmentProfile
    return MissionSpec(
        name="Test Twin",
        summary="Testing...",
        domain="industrial",
        objectives=[],
        deployment_context="closed bioreactor",
        environment=EnvironmentProfile(
            name="Sim Tester",
            radiation_level=1.0,
            salinity_ppt=0.0,
            gravity_g=1.0,
            temperature_range_c=(30.0, 35.0),
            ph_range=(6.5, 7.5),
            nutrients=["glucose"],
            stressors=[]
        )
    )

@pytest.fixture
def base_candidate() -> CandidateProgram:
    return CandidateProgram(
        id="c1",
        title="Twin Tester",
        summary="A test candidate",
        archetype="single-chassis microbial factory",
        modules=["sensing layer", "payload synthesis"],
        rationale=[],
        risks=[],
        scores={},
        evidence_channels=[]
    )

def test_growth_simulation_structure(base_mission, base_candidate):
    habitat = HabitatProfile(severity=1.0, narrative="Benign", drivers=[])
    sim = simulate_growth(base_mission, base_candidate, habitat)
    
    assert len(sim.time_points_h) == 73  # 0 to 72 inclusive
    assert len(sim.biomass_od600) == 73
    assert len(sim.product_titer_gl) == 73
    
    # Growth should increase and plateau at carrying capacity
    assert sim.biomass_od600[-1] > sim.biomass_od600[0]
    assert sim.biomass_od600[-1] <= sim.carrying_capacity
    
    # Product titer should increase
    assert sim.product_titer_gl[-1] > sim.product_titer_gl[0]

def test_severe_habitat_growth_penalty(base_mission, base_candidate):
    habitat_benign = HabitatProfile(severity=1.0, narrative="Benign", drivers=[])
    habitat_severe = HabitatProfile(severity=9.0, narrative="Severe", drivers=[])
    
    sim_benign = simulate_growth(base_mission, base_candidate, habitat_benign)
    sim_severe = simulate_growth(base_mission, base_candidate, habitat_severe)
    
    assert sim_severe.peak_growth_rate < sim_benign.peak_growth_rate
    assert sim_severe.carrying_capacity < sim_benign.carrying_capacity
    assert sim_severe.biomass_od600[-1] < sim_benign.biomass_od600[-1]
