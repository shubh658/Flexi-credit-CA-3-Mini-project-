import random
from typing import Dict, Any, List
from app import triage_agent, database

SIMULATED_SCENARIOS = {
    "fire_trapped": {
        "title": "Okhla Garment Factory Fire",
        "description": "Heavy smoke blowing from 3rd floor windows at Plot 42, Okhla Industrial Area Phase-3. 3 textile factory workers reported trapped in room 302 with heat intensifying.",
        "location_name": "Okhla Industrial Area Phase-3, New Delhi",
        "reported_by": "Factory Security Supervisor"
    },
    "hazmat_leak": {
        "title": "NH-48 Ammonia Chemical Tanker Spill",
        "description": "Ruptured valve on 5000-liter ammonia chemical tanker near Mahipalpur Flyover on NH-48 Expressway. Corrosive vapors spreading toward traffic lane.",
        "location_name": "NH-48 Delhi-Gurgaon Expressway",
        "reported_by": "NHAI Highway Patrol #112"
    },
    "subway_panic": {
        "title": "Rajiv Chowk Metro Transformer Blast",
        "description": "Electrical short-circuit blowout at Rajiv Chowk Metro Station Gate 2. Thick spark haze causing passenger evacuation. 3 minor injuries reported.",
        "location_name": "Rajiv Chowk Metro Station, Connaught Place",
        "reported_by": "CISF Metro Security Desk"
    },
    "highway_crash": {
        "title": "Noida Expressway Multi-Car Pileup",
        "description": "Heavy fog collision involving 4 passenger vehicles on Noida-Greater Noida Expressway near Sector 144. Fuel leak detected on roadway.",
        "location_name": "Noida Expressway Sector 144",
        "reported_by": "UP Emergency Helpline 112"
    },
    "bank_robbery": {
        "title": "Connaught Place Bank Silent Alarm",
        "description": "Silent security alarm triggered at State Bank of India branch, Inner Circle Block B. Two armed individuals reported inside vault section.",
        "location_name": "SBI Block B, Connaught Place",
        "reported_by": "Bank Silent Alarm Sensor"
    }
}

def get_available_scenarios() -> List[Dict[str, Any]]:
    return [
        {"key": k, "name": v["title"], "location": v["location_name"], "description": v["description"]}
        for k, v in SIMULATED_SCENARIOS.items()
    ]

def trigger_scenario(key: str) -> Dict[str, Any]:
    if key not in SIMULATED_SCENARIOS:
        key = random.choice(list(SIMULATED_SCENARIOS.keys()))

    data = SIMULATED_SCENARIOS[key]
    incident = triage_agent.analyze_report(
        description=data["description"],
        location_name=data["location_name"],
        reported_by=data["reported_by"]
    )
    database.log_audit("SIMULATION_TRIGGERED", incident["id"], f"Triggered scenario: {data['title']}")
    return incident
