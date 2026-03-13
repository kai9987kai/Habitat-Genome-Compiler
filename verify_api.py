import requests
import json

def test_extreme_severity():
    url = "http://127.0.0.1:8000/api/compile"
    payload = {
        "name": "Extreme Stress Test",
        "summary": "Testing high severity opex overflow",
        "domain": "industrial",
        "deployment_context": "closed bioreactor",
        "environment": {
            "name": "Super Volcanic",
            "temperature_range_c": [100.0, 150.0],
            "radiation_level": 50.0,
            "salinity_ppt": 300.0,
            "ph_range": [1.0, 2.0],
            "gravity_g": 2.5,
            "nutrients": ["heat", "sulfur"],
            "stressors": ["extreme heat", "acid", "radiation"]
        },
        "objectives": [
            {"id": "o1", "title": "survive and produce", "metric": "yield", "target": "biomass", "priority": 1}
        ]
    }
    
    try:
        print("Sending extreme payload...")
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("Successfully parsed JSON response!")
            for c in result.get("candidates", []):
                print(f"Candidate: {c['title']}")
                print(f"  Stability Score: {c.get('stability_score')}")
                print(f"  Eco-Risk Score: {c.get('evolutionary_risk_score')}")
                print(f"  Symbiosis Index: {c.get('consortium_stability_index')}")
                print(f"  Xeno-Safety: {c.get('xenobiology_score')}")
                print(f"  Epi-Tuning: {c.get('epigenetic_tunability_score')}")
                print(f"  PLM Fitness: {c.get('plm_fitness_score')}")
                print(f"  Circuit Reliability: {c.get('circuit_reliability_score')}")
                print(f"  OPEX: {c.get('tea', {}).get('estimated_opex_usd_k_yr')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_extreme_severity()
