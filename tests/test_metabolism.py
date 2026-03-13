"""Tests for the Flux Balance Analysis (FBA) proxy."""

import pytest

from habitat_genome_compiler.adapters import HabitatProfile
from habitat_genome_compiler.metabolism import simulate_flux
from habitat_genome_compiler.models import CandidateProgram, EnvironmentProfile, MissionSpec


@pytest.fixture
def base_mission() -> MissionSpec:
    return MissionSpec(
        name="Test",
        summary="Test",
        domain="industrial",
        objectives=[],
        deployment_context="closed bioreactor",
        environment=EnvironmentProfile(name="Test", radiation_level=1.0, salinity_ppt=0.0, gravity_g=1.0, 
            temperature_range_c=(30.0, 35.0),
            ph_range=(6.5, 7.5),
            nutrients=["glucose", "nitrogen", "trace metals"],
            stressors=[]
        )
    )


@pytest.fixture
def base_habitat() -> HabitatProfile:
    return HabitatProfile(severity=2.0, drivers=[], narrative="Benign scenario")


@pytest.fixture
def base_candidate() -> CandidateProgram:
    return CandidateProgram(
        id="c1",
        title="Test Candidate",
        summary="A test candidate",
        archetype="single-chassis microbial factory",
        modules=["sensing layer", "synthetic regulator", "payload synthesis"],
        rationale=[],
        risks=[],
        scores={},
        evidence_channels=[]
    )


def test_standard_metabolic_flux(base_mission, base_candidate, base_habitat):
    flux = simulate_flux(base_mission, base_candidate, base_habitat)
    assert flux.theoretical_yield > 0.4
    assert flux.theoretical_yield < 1.0
    assert flux.limiting_nutrient == "glucose"  # First nutrient
    assert flux.metabolic_burden == len(base_candidate.modules) * 0.08
    assert flux.toxic_intermediate_risk == 0.1


def test_consortium_flux_penalty(base_mission, base_candidate, base_habitat):
    base_candidate.archetype = "synthetic consortium"
    flux = simulate_flux(base_mission, base_candidate, base_habitat)
    assert flux.theoretical_yield < 0.65  # Base for consortium is 0.65, minus burden


def test_high_stress_burden_multiplier(base_mission, base_candidate, base_habitat):
    base_habitat.severity = 8.0
    flux = simulate_flux(base_mission, base_candidate, base_habitat)
    expected_burden = len(base_candidate.modules) * 0.08 * 1.5
    assert flux.metabolic_burden == pytest.approx(expected_burden)
    assert any("energy diverted" in str(b).lower() for b in flux.pathway_bottlenecks)


def test_phage_toxicity(base_mission, base_candidate, base_habitat):
    base_candidate.modules.append("phage-delivered degradation cassette")
    flux = simulate_flux(base_mission, base_candidate, base_habitat)
    assert flux.toxic_intermediate_risk == pytest.approx(0.5)  # 0.1 base + 0.4


def test_remediation_nitrogen_limitation(base_mission, base_candidate, base_habitat):
    base_candidate.archetype = "remediation strain"
    flux = simulate_flux(base_mission, base_candidate, base_habitat)
    assert flux.limiting_nutrient == "carbon"
