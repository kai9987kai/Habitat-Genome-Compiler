"""Tests for the Techno-Economic Analysis (TEA) and LCA module."""

import pytest
import math

from habitat_genome_compiler.sustainability import evaluate_sustainability
from habitat_genome_compiler.models import CandidateProgram, EnvironmentProfile, MissionSpec, ObjectiveSpec


@pytest.fixture
def base_mission() -> MissionSpec:
    return MissionSpec(
        name="Test TEA",
        summary="Test",
        domain="industrial",
        objectives=[],
        deployment_context="closed bioreactor",
        environment=EnvironmentProfile(name="Test", radiation_level=1.0, salinity_ppt=0.0, gravity_g=1.0, 
            temperature_range_c=(30.0, 35.0),
            ph_range=(6.5, 7.5),
            nutrients=["glucose"],
            stressors=[]
        )
    )

@pytest.fixture
def carbon_mission() -> MissionSpec:
    return MissionSpec(
        name="Test Carbon TEA",
        summary="Test",
        domain="environmental",
        objectives=[ObjectiveSpec(id="o1", title="carbon fixation", target="co2", metric="none", priority=1)],
        deployment_context="open field",
        environment=EnvironmentProfile(name="Test", radiation_level=1.0, salinity_ppt=0.0, gravity_g=1.0, 
            temperature_range_c=(20.0, 30.0),
            ph_range=(6.0, 8.0),
            nutrients=["sunlight", "co2"],
            stressors=[]
        )
    )

@pytest.fixture
def base_candidates() -> list[CandidateProgram]:
    return [
        CandidateProgram(
            id="c1",
            title="Single Chassis",
            summary="Standard",
            archetype="single-chassis",
            modules=["a", "b", "c"],
            rationale=[],
            risks=[],
            scores={},
            evidence_channels=[]
        ),
        CandidateProgram(
            id="c2",
            title="Consortium",
            summary="Complex",
            archetype="consortium",
            modules=["a", "b", "c", "d"],
            rationale=[],
            risks=[],
            scores={},
            evidence_channels=[]
        )
    ]


def test_base_capex_and_opex_scaling(base_mission, base_candidates):
    # 'closed bioreactor' context has base capex of 10000.0 setup in sustainability.py
    # severity 2.0
    reports = evaluate_sustainability(base_mission, base_candidates, habitat_severity=2.0)
    
    assert len(reports) == 2
    r1, r2 = reports
    
    # Consortium (c2) should be more expensive than single-chassis (c1)
    assert r2.estimated_capex_usd_k > r1.estimated_capex_usd_k
    assert r2.estimated_opex_usd_k_yr > r1.estimated_opex_usd_k_yr
    
    # EROI degrades with complexity
    assert r1.energy_return_on_investment > r2.energy_return_on_investment
    
    # Positive footprint
    assert r1.carbon_footprint_kg_co2_kg_prod > 0


def test_carbon_fixation_footprint(carbon_mission, base_candidates):
    reports = evaluate_sustainability(carbon_mission, base_candidates, habitat_severity=3.0)
    r1 = reports[0]
    
    # Carbon footprint should be deeply reduced or negative
    assert r1.carbon_footprint_kg_co2_kg_prod < 5.0  # Or negative
    assert r1.energy_return_on_investment > 1.0  # Base EROI for carbon fixation is 1.5


def test_extreme_habitat_severity_viability(base_mission, base_candidates):
    reports = evaluate_sustainability(base_mission, base_candidates, habitat_severity=10.0)
    r1, r2 = reports
    
    assert r1.viability_score < 10.0
    assert r2.viability_score < 10.0
    # Opex should be huge due to math.exp(10.0 * 0.15)
    assert r1.estimated_opex_usd_k_yr > 10000.0
    assert any("Prohibitive operational overhead" in d for d in r1.cost_drivers)
