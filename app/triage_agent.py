import re
import random
import json
import urllib.request
from datetime import datetime, timezone
from typing import Dict, Any, List
from app import database

TAVILY_API_KEY = "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"

BASE_LAT = 28.6139
BASE_LNG = 77.2090

FIRE_KEYWORDS = ["fire", "smoke", "flames", "burn", "explosion", "blaze", "trapped in building", "spark"]
MEDICAL_KEYWORDS = ["unconscious", "bleeding", "heart attack", "stroke", "breathing", "cpr", "fracture", "head injury", "overdose", "seizure", "collapsed"]
CRIME_KEYWORDS = ["gunshot", "shooter", "robbery", "assault", "stabbing", "break-in", "weapon", "burglary", "hostage", "active shooter"]
HAZARD_KEYWORDS = ["gas leak", "chemical", "toxic", "spill", "radiation", "fumes", "hazmat", "corrosive", "poison", "ammonia"]
TRAFFIC_KEYWORDS = ["crash", "collision", "pileup", "rollover", "hit and run", "vehicle", "traffic", "highway"]
DISASTER_KEYWORDS = ["flood", "earthquake", "structural collapse", "storm", "hurricane", "tornado", "landslide"]

def search_tavily_emergency_knowledge(query: str) -> str:
    """Uses Tavily Search API to fetch real-time public safety & hazmat first-aid protocols."""
    if not TAVILY_API_KEY:
        return ""
    try:
        url = "https://api.tavily.com/search"
        payload = json.dumps({
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "basic",
            "max_results": 2
        }).encode('utf-8')
        
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=4) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            results = res_data.get("results", [])
            if results:
                snippets = [r.get("content", "") for r in results if r.get("content")]
                combined = " ".join(snippets)
                # Clean up whitespace
                combined = re.sub(r'\s+', ' ', combined).strip()
                return combined[:350]
    except Exception as e:
        print(f"Tavily search exception: {e}")
    return ""

def match_word(word: str, text: str) -> bool:
    return bool(re.search(r'\b' + re.escape(word) + r'\b', text, re.IGNORECASE))

def classify_incident(text: str) -> str:
    text_lower = text.lower()
    scores = {
        "Fire": sum(1 for k in FIRE_KEYWORDS if match_word(k, text_lower)),
        "Medical": sum(1 for k in MEDICAL_KEYWORDS if match_word(k, text_lower)),
        "Crime": sum(1 for k in CRIME_KEYWORDS if match_word(k, text_lower)),
        "Hazard": sum(1 for k in HAZARD_KEYWORDS if match_word(k, text_lower)),
        "Traffic": sum(1 for k in TRAFFIC_KEYWORDS if match_word(k, text_lower)),
        "Disaster": sum(1 for k in DISASTER_KEYWORDS if match_word(k, text_lower))
    }
    best_cat = max(scores, key=scores.get)
    if scores[best_cat] == 0:
        if any(match_word(w, text_lower) for w in ["hurt", "pain", "doctor", "ambulance"]):
            return "Medical"
        return "Crime" if any(match_word(w, text_lower) for w in ["police", "suspicious", "thief"]) else "Fire"
    return best_cat

def calculate_priority(text: str, category: str) -> tuple[str, int]:
    text_lower = text.lower()
    score = 50

    critical_terms = ["trapped", "unconscious", "explosion", "active shooter", "gunshot", "not breathing", "chemical spill", "multiple casualties", "heavy flames", "collapse"]
    high_terms = ["bleeding", "smoke", "weapon", "broken bone", "highway", "collision", "gas smell", "struggling to breathe"]

    for term in critical_terms:
        if match_word(term, text_lower):
            score += 15

    for term in high_terms:
        if match_word(term, text_lower):
            score += 8

    victim_matches = re.findall(r'(\d+)\s*(people|persons|victims|injured|trapped)', text_lower)
    if victim_matches:
        count = sum(int(m[0]) for m in victim_matches)
        score += min(count * 5, 20)

    score = max(10, min(99, score))

    if score >= 85:
        severity = "P1-Critical"
    elif score >= 65:
        severity = "P2-High"
    elif score >= 45:
        severity = "P3-Medium"
    else:
        severity = "P4-Low"

    return severity, score

def extract_victims_and_hazards(text: str) -> tuple[int, str]:
    text_lower = text.lower()
    victims = 0
    victim_matches = re.findall(r'(\d+)\s*(people|person|victims|injured|trapped|casualties)', text_lower)
    if victim_matches:
        victims = sum(int(m[0]) for m in victim_matches)
    elif any(w in text_lower for w in ["person trapped", "someone hurt", "one victim"]):
        victims = 1

    hazards_list = []
    if match_word("smoke", text_lower): hazards_list.append("Dense Smoke")
    if match_word("fire", text_lower) or match_word("flames", text_lower): hazards_list.append("Active Fire")
    if match_word("chemical", text_lower) or match_word("gas", text_lower) or match_word("fumes", text_lower) or match_word("ammonia", text_lower): hazards_list.append("Chemical Vapor / Toxic Gas")
    if match_word("weapon", text_lower) or match_word("gun", text_lower) or match_word("knife", text_lower): hazards_list.append("Armed Suspect")
    if match_word("fuel", text_lower) or match_word("oil", text_lower): hazards_list.append("Flammable Fuel Spill")
    if "power line" in text_lower or match_word("electricity", text_lower): hazards_list.append("Downed Power Lines")

    return victims, ", ".join(hazards_list) if hazards_list else "None identified"

def generate_location_coords(location_name: str) -> tuple[float, float]:
    seed_val = sum(ord(c) for c in location_name)
    random.seed(seed_val)
    lat_offset = random.uniform(-0.03, 0.03)
    lng_offset = random.uniform(-0.03, 0.03)
    random.seed()
    return round(BASE_LAT + lat_offset, 5), round(BASE_LNG + lng_offset, 5)

def generate_protocol(category: str, severity: str) -> str:
    protocols = {
        "Fire": "Protocol F-10: Immediate dual Engine dispatch, establish 150m perimeter, turn off main gas line, initiate aerial search & rescue.",
        "Medical": "Protocol M-04: Dispatch ALS Paramedics, direct caller to initiate chest compressions if non-responsive, clear access corridor for ambulance.",
        "Crime": "Protocol C-02: Dispatch perimeter units in high-alert mode, secure scene boundaries, isolate witnesses, lock down immediate zone.",
        "Hazard": "Protocol H-08: Deploy Hazmat Unit Level-A gear, evacuate 300m downwind radius, shut off ventilation systems.",
        "Traffic": "Protocol T-01: Dispatch Traffic units & Tow recovery, deploy highway flares, redirect oncoming traffic to secondary arterial roads.",
        "Disaster": "Protocol D-05: Activate Search & Rescue, establish Incident Command Post, coordinate multi-agency emergency response."
    }
    return protocols.get(category, "Protocol G-01: Standard emergency response unit deployment and scene safety assessment.")

def analyze_report(description: str, location_name: str = "", reported_by: str = "Citizen Intake") -> Dict[str, Any]:
    category = classify_incident(description)
    severity, priority_score = calculate_priority(description, category)
    victims_count, hazards = extract_victims_and_hazards(description)

    if not location_name:
        loc_match = re.search(r'(?:at|on|near)\s+([A-Za-z0-9\s,#]+)', description)
        if loc_match:
            location_name = loc_match.group(1).strip()
        else:
            location_name = "Central Metro Sector"

    lat, lng = generate_location_coords(location_name)

    incident_id = f"INC-2026-{random.randint(1000, 9999)}"
    now_str = datetime.now(timezone.utc).isoformat()

    title_map = {
        "Fire": f"Emergency Fire Alert ({severity})",
        "Medical": f"Critical Medical Call ({severity})",
        "Crime": f"Public Security Incident ({severity})",
        "Hazard": f"Hazardous Chemical/Gas Incident ({severity})",
        "Traffic": f"Motor Vehicle Accident ({severity})",
        "Disaster": f"Natural/Structural Disaster Alert ({severity})"
    }
    title = title_map.get(category, f"Public Safety Incident ({severity})")

    # Fetch live Tavily safety info if Hazmat or Medical emergency
    tavily_info = ""
    if category in ["Hazard", "Medical"]:
        search_query = f"{description[:60]} emergency first aid protocol"
        tavily_info = search_tavily_emergency_knowledge(search_query)

    ai_summary = f"{severity} {category} report at {location_name}. {victims_count} victims reported; Hazards: {hazards}. Priority score: {priority_score}/100."
    if tavily_info:
        ai_summary += f" [Tavily Live Intel: {tavily_info[:160]}...]"

    recommended_protocol = generate_protocol(category, severity)

    incident = {
        "id": incident_id,
        "timestamp": now_str,
        "title": title,
        "category": category,
        "severity": severity,
        "priority_score": priority_score,
        "status": "New",
        "location_name": location_name,
        "lat": lat,
        "lng": lng,
        "description": description,
        "reported_by": reported_by,
        "victims_count": victims_count,
        "hazards": hazards,
        "dispatched_units": [],
        "ai_summary": ai_summary,
        "recommended_protocol": recommended_protocol
    }

    database.save_incident(incident)
    database.log_audit("INCIDENT_CREATED", incident_id, f"Created {category} incident with priority {priority_score}")

    initial_ai_msg = get_initial_safety_advice(category, severity, location_name, tavily_info)
    database.save_chat_message(incident_id, "AI Agent", initial_ai_msg)

    return incident

def get_initial_safety_advice(category: str, severity: str, location_name: str, tavily_info: str = "") -> str:
    base = f"🚨 AegisResponse AI Agent online. I have registered your emergency report for {location_name} and alerted emergency dispatch.\n\n"

    safety_advice = {
        "Fire": "🔥 **FIRE SAFETY INSTRUCTIONS:**\n1. Stay low beneath smoke.\n2. Do NOT use elevators.\n3. If trapped, seal door cracks with wet towels and wave a cloth at windows.\n4. Keep calm—Fire & Rescue units are being dispatched!",
        "Medical": "🚑 **MEDICAL EMERGENCY INSTRUCTIONS:**\n1. Ensure the scene is safe for you.\n2. If victim is unresponsive and not breathing, begin firm chest compressions in center of chest.\n3. Keep victim warm and still.\n4. Paramedics are en route!",
        "Crime": "🛡️ **SECURITY SAFETY INSTRUCTIONS:**\n1. Move to a safe, locked shelter if suspect is present.\n2. Keep your voice quiet and turn off phone ringer.\n3. Do not confront suspects.\n4. Police units are mobilizing to your area!",
        "Hazard": "⚠️ **HAZMAT SAFETY INSTRUCTIONS:**\n1. Move upwind and uphill from the chemical source.\n2. Cover nose and mouth with a damp cloth.\n3. Avoid touching spilled substances.\n4. Specialized Hazmat unit is notified!",
        "Traffic": "🚗 **ACCIDENT SAFETY INSTRUCTIONS:**\n1. Turn on vehicle hazard lights.\n2. If safe, move off active traffic lanes.\n3. Do not move severely injured victims unless immediate fire threat exists.\n4. Traffic responders dispatched!",
        "Disaster": "🌪️ **DISASTER SAFETY INSTRUCTIONS:**\n1. Take cover under heavy furniture or interior wall.\n2. Avoid windows and downed wires.\n3. Stay tuned to dispatcher updates."
    }

    res_text = base + safety_advice.get(category, "Stay in a safe position and keep your phone line clear.")
    if tavily_info:
        res_text += f"\n\n🌐 **TAVILY LIVE HAZMAT INTEL:**\n{tavily_info}"
    return res_text

def process_citizen_chat(incident_id: str, user_message: str) -> Dict[str, Any]:
    incident = database.fetch_incident_by_id(incident_id)
    database.save_chat_message(incident_id, "Citizen", user_message)

    msg_lower = user_message.lower()

    if not incident:
        ai_reply = "I am processing your emergency request. Please confirm your current location."
    else:
        cat = incident['category']
        worse_terms = ["worse", "bleeding more", "thicker", "spreading", "gunshot", "armed", "cannot breathe", "can't breathe"]
        eta_terms = ["eta", "where are they", "how long", "status", "coming"]
        safe_terms = ["safe", "out", "evacuated", "better"]

        if any(term in msg_lower for term in worse_terms):
            incident['priority_score'] = min(99, incident['priority_score'] + 10)
            incident['severity'] = "P1-Critical"
            database.save_incident(incident)
            database.log_audit("INCIDENT_ESCALATED", incident_id, f"Priority escalated to {incident['priority_score']} due to caller update.")
            ai_reply = f"⚠️ Escalating emergency priority to CRITICAL ({incident['priority_score']}/100). Dispatchers have been updated on condition worsening. Please follow immediate safety protocol!"

        elif any(match_word(term, msg_lower) for term in eta_terms):
            units = incident.get('dispatched_units', [])
            if units:
                ai_reply = f"Units {', '.join(units)} have been dispatched and are currently en route to your location. Estimated arrival time: 3-5 minutes."
            else:
                ai_reply = "The dispatch officer is selecting the nearest response units right now. Help will be en route shortly."

        elif any(match_word(term, msg_lower) for term in safe_terms):
            ai_reply = "Thank you for the update. Please remain at a safe rendezvous point until emergency personnel reach you."

        else:
            # Check if user asks specific safety question and fetch via Tavily if needed
            if any(k in msg_lower for k in ["how to", "what should i do", "first aid", "treatment", "chemical"]):
                tav_res = search_tavily_emergency_knowledge(f"Emergency safety guidance for {user_message}")
                if tav_res:
                    ai_reply = f"🌐 **Tavily Emergency Guide:** {tav_res}\n\nEmergency units are en route to your location."
                else:
                    ai_reply = f"Understood. I have logged your message: '{user_message}'. Please stay in a safe location."
            else:
                ai_reply = f"Understood. I have logged your message: '{user_message}'. Is anyone else in immediate danger near your position?"

    saved_msg = database.save_chat_message(incident_id, "AI Agent", ai_reply)
    return {
        "reply": ai_reply,
        "incident": database.fetch_incident_by_id(incident_id),
        "message": saved_msg
    }
