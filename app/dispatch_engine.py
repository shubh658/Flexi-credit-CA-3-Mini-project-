import math
from typing import List, Dict, Any, Optional
from app import database

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # Radius of Earth in kilometers
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def calculate_eta_minutes(distance_km: float, speed_kmh: float = 45.0) -> int:
    time_hours = distance_km / speed_kmh
    minutes = int(round(time_hours * 60))
    return max(2, minutes) # minimum 2 min ETA

def get_recommended_units(incident_id: str) -> List[Dict[str, Any]]:
    incident = database.fetch_incident_by_id(incident_id)
    if not incident:
        return []

    inc_lat = incident['lat']
    inc_lng = incident['lng']
    inc_cat = incident['category']

    all_units = database.fetch_all_units()
    available_units = [u for u in all_units if u['status'] == 'Available']

    # Preferred unit types mapping
    type_preference = {
        "Fire": ["Fire", "EMS", "Hazmat"],
        "Medical": ["EMS", "Fire"],
        "Crime": ["Police", "Traffic"],
        "Hazard": ["Hazmat", "Fire", "EMS"],
        "Traffic": ["Traffic", "Police", "EMS"],
        "Disaster": ["Fire", "Police", "EMS", "Hazmat"]
    }
    preferred_types = type_preference.get(inc_cat, ["Police", "Fire", "EMS"])

    scored_units = []
    for u in available_units:
        dist = haversine_distance(inc_lat, inc_lng, u['lat'], u['lng'])
        eta = calculate_eta_minutes(dist)

        # Suitability score
        type_weight = 1.0
        if u['type'] in preferred_types:
            rank = preferred_types.index(u['type'])
            type_weight = 1.0 - (rank * 0.2)
        else:
            type_weight = 0.4

        score = (1.0 / (dist + 0.1)) * type_weight

        scored_units.append({
            "unit_id": u['id'],
            "name": u['name'],
            "type": u['type'],
            "base_station": u['base_station'],
            "distance_km": dist,
            "eta_minutes": eta,
            "status": u['status'],
            "recommendation_score": round(score, 3),
            "is_preferred": u['type'] in preferred_types
        })

    # Sort by recommendation score descending
    scored_units.sort(key=lambda x: x['recommendation_score'], reverse=True)
    return scored_units

def dispatch_units(incident_id: str, unit_ids: List[str]) -> Dict[str, Any]:
    incident = database.fetch_incident_by_id(incident_id)
    if not incident:
        return {"error": "Incident not found"}

    current_dispatched = set(incident.get('dispatched_units', []))
    new_dispatched = list(current_dispatched.union(unit_ids))

    incident['dispatched_units'] = new_dispatched
    incident['status'] = "Dispatched"
    database.save_incident(incident)

    for uid in unit_ids:
        database.update_unit_status(uid, "Dispatched", incident_id)

    database.log_audit("UNITS_DISPATCHED", incident_id, f"Dispatched units {unit_ids} to incident {incident_id}")

    return {
        "success": True,
        "incident_id": incident_id,
        "dispatched_units": new_dispatched,
        "status": "Dispatched"
    }

def update_incident_status(incident_id: str, new_status: str) -> Dict[str, Any]:
    incident = database.fetch_incident_by_id(incident_id)
    if not incident:
        return {"error": "Incident not found"}

    old_status = incident['status']
    incident['status'] = new_status
    database.save_incident(incident)

    if new_status == "Resolved":
        # Free up assigned units
        dispatched_units = incident.get('dispatched_units', [])
        all_units = database.fetch_all_units()
        for u in all_units:
            if u['assigned_incident_id'] == incident_id:
                database.update_unit_status(u['id'], "Available", None)

    database.log_audit("STATUS_CHANGED", incident_id, f"Status updated from {old_status} to {new_status}")

    return {
        "success": True,
        "incident_id": incident_id,
        "old_status": old_status,
        "new_status": new_status
    }
