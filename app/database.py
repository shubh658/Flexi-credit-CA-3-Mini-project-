import sqlite3
import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aegis_safety.db")

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Incidents table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incidents (
        id TEXT PRIMARY KEY,
        timestamp TEXT,
        title TEXT,
        category TEXT,
        severity TEXT,
        priority_score INTEGER,
        status TEXT,
        location_name TEXT,
        lat REAL,
        lng REAL,
        description TEXT,
        reported_by TEXT,
        victims_count INTEGER DEFAULT 0,
        hazards TEXT DEFAULT '',
        dispatched_units TEXT DEFAULT '[]',
        ai_summary TEXT DEFAULT '',
        recommended_protocol TEXT DEFAULT ''
    );
    """)

    # Emergency Units table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS units (
        id TEXT PRIMARY KEY,
        name TEXT,
        type TEXT,
        status TEXT,
        lat REAL,
        lng REAL,
        assigned_incident_id TEXT,
        base_station TEXT
    );
    """)

    # Chat Messages table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_id TEXT,
        sender TEXT,
        message TEXT,
        timestamp TEXT
    );
    """)

    # Audit Logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        event_type TEXT,
        incident_id TEXT,
        detail TEXT
    );
    """)

    conn.commit()

    # Reset tables if old data exists to ensure Indian dataset initialization
    cursor.execute("SELECT COUNT(*) FROM units WHERE id LIKE 'POL-112%';")
    if cursor.fetchone()[0] == 0:
        cursor.execute("DELETE FROM units;")
        cursor.execute("DELETE FROM incidents;")
        conn.commit()

        # Seed initial Indian emergency response units
        seed_units = [
            ("POL-112", "PCR Van 112 (Delhi Police)", "Police", "Available", 28.6139, 77.2090, None, "Connaught Place Police Station"),
            ("POL-114", "Traffic Interceptor 114", "Police", "Available", 28.5355, 77.1557, None, "Vasant Kunj Precinct"),
            ("FIRE-101", "DFS Fire Tender 101", "Fire", "Available", 28.6289, 77.2215, None, "Connaught Place Fire Station"),
            ("FIRE-102", "Hydraulic Platform Ladder 102", "Fire", "Available", 28.5562, 77.2410, None, "Okhla Industrial Fire Station"),
            ("AMB-108", "CATS ALS Ambulance 108", "EMS", "Available", 28.6250, 77.2100, None, "LNJP Hospital Medical Complex"),
            ("AMB-109", "Emergency Trauma Ambulance 109", "EMS", "Available", 28.5672, 77.2100, None, "AIIMS Trauma Center"),
            ("NDRF-501", "NDRF Battalion 8th Response Unit", "Disaster", "Available", 28.5900, 77.3200, None, "Noida Regional Response Post"),
            ("HAZ-301", "Hazmat Chemical Response Van", "Hazmat", "Available", 28.6800, 77.1400, None, "Wazirpur Industrial Fire Post")
        ]
        cursor.executemany("""
            INSERT INTO units (id, name, type, status, lat, lng, assigned_incident_id, base_station)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, seed_units)
        conn.commit()

        # Seed initial Indian incidents
        now_str = datetime.now(timezone.utc).isoformat()
        seed_incidents = [
            (
                "INC-IND-9001",
                now_str,
                "Okhla Industrial Complex Structure Fire",
                "Fire",
                "P1-Critical",
                92,
                "New",
                "Plot 42, Okhla Industrial Area Phase-3, New Delhi",
                28.5430,
                77.2720,
                "Heavy black smoke and fire breaking out in garment manufacturing factory. 4 workers trapped on 2nd floor.",
                "Citizen via 112 India Helpline",
                4,
                "Dense Smoke, Flammable Textiles",
                json.dumps([]),
                "P1 Critical Structure Fire in Delhi Industrial Zone. High victim risk.",
                "Protocol F-10: Deploy DFS Fire Tender + Hydraulic Ladder. Evacuate adjacent plots. Alert AIIMS Trauma unit."
            ),
            (
                "INC-IND-9002",
                now_str,
                "Ammonia Tanker Spill on NH-48",
                "Hazard",
                "P1-Critical",
                95,
                "Dispatched",
                "NH-48 Delhi-Gurgaon Expressway near Mahipalpur Flyover",
                28.5480,
                77.1210,
                "Industrial anhydrous ammonia tanker overturned. Toxic gas fumes spreading across expressway. Traffic halted.",
                "NHAI Highway Control Room",
                2,
                "Toxic Ammonia Vapors, Fuel Spill",
                json.dumps(["HAZ-301", "POL-114"]),
                "P1 Critical Hazmat spill on major national highway. Acute respiratory hazard.",
                "Protocol H-08: Deploy Hazmat Response Unit in Level-A gear. Divert traffic toward MG Road. 500m downwind evacuation."
            ),
            (
                "INC-IND-9003",
                now_str,
                "Submerged Bus at Minto Bridge Underpass",
                "Traffic",
                "P2-High",
                76,
                "New",
                "Minto Bridge Underpass, Connaught Place Outer Ring",
                28.6330,
                77.2220,
                "Heavy monsoon deluge flooded underpass. DTC public transit bus stalled in 5 feet of water with 12 passengers on roof.",
                "Delhi Traffic Police Command",
                12,
                "Submerged Expressway, Electrical Cables",
                json.dumps([]),
                "P2 High flood rescue incident. Water rise monitored.",
                "Protocol T-01: Deploy NDRF inflatable boats + Traffic PCR divert. Cut underpass power lines."
            )
        ]
        cursor.executemany("""
            INSERT INTO incidents (id, timestamp, title, category, severity, priority_score, status, location_name, lat, lng, description, reported_by, victims_count, hazards, dispatched_units, ai_summary, recommended_protocol)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, seed_incidents)
        conn.commit()

        # Update initial unit status for dispatched units
        cursor.execute("UPDATE units SET status='Dispatched', assigned_incident_id='INC-IND-9002' WHERE id IN ('HAZ-301', 'POL-114');")
        conn.commit()

    conn.close()

def fetch_all_incidents() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidents ORDER BY priority_score DESC, timestamp DESC;")
    rows = cursor.fetchall()
    incidents = []
    for r in rows:
        item = dict(r)
        item['dispatched_units'] = json.loads(item['dispatched_units']) if item['dispatched_units'] else []
        incidents.append(item)
    conn.close()
    return incidents

def fetch_incident_by_id(incident_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidents WHERE id = ?;", (incident_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        item = dict(row)
        item['dispatched_units'] = json.loads(item['dispatched_units']) if item['dispatched_units'] else []
        return item
    return None

def save_incident(incident: Dict[str, Any]):
    conn = get_connection()
    cursor = conn.cursor()
    dispatched_str = json.dumps(incident.get('dispatched_units', []))
    cursor.execute("""
        INSERT INTO incidents (id, timestamp, title, category, severity, priority_score, status, location_name, lat, lng, description, reported_by, victims_count, hazards, dispatched_units, ai_summary, recommended_protocol)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            title=excluded.title,
            category=excluded.category,
            severity=excluded.severity,
            priority_score=excluded.priority_score,
            status=excluded.status,
            location_name=excluded.location_name,
            lat=excluded.lat,
            lng=excluded.lng,
            description=excluded.description,
            victims_count=excluded.victims_count,
            hazards=excluded.hazards,
            dispatched_units=excluded.dispatched_units,
            ai_summary=excluded.ai_summary,
            recommended_protocol=excluded.recommended_protocol;
    """, (
        incident['id'],
        incident['timestamp'],
        incident['title'],
        incident['category'],
        incident['severity'],
        incident['priority_score'],
        incident['status'],
        incident['location_name'],
        incident['lat'],
        incident['lng'],
        incident['description'],
        incident.get('reported_by', 'Citizen'),
        incident.get('victims_count', 0),
        incident.get('hazards', ''),
        dispatched_str,
        incident.get('ai_summary', ''),
        incident.get('recommended_protocol', '')
    ))
    conn.commit()
    conn.close()

def fetch_all_units() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM units ORDER BY id ASC;")
    rows = cursor.fetchall()
    units = [dict(r) for r in rows]
    conn.close()
    return units

def update_unit_status(unit_id: str, status: str, assigned_incident_id: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE units SET status = ?, assigned_incident_id = ? WHERE id = ?;", (status, assigned_incident_id, unit_id))
    conn.commit()
    conn.close()

def save_chat_message(incident_id: str, sender: str, message: str) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    ts = datetime.now(timezone.utc).isoformat()
    cursor.execute("""
        INSERT INTO chat_messages (incident_id, sender, message, timestamp)
        VALUES (?, ?, ?, ?);
    """, (incident_id, sender, message, ts))
    conn.commit()
    msg_id = cursor.lastrowid
    conn.close()
    return {"id": msg_id, "incident_id": incident_id, "sender": sender, "message": message, "timestamp": ts}

def fetch_chat_history(incident_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chat_messages WHERE incident_id = ? ORDER BY id ASC;", (incident_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def log_audit(event_type: str, incident_id: str, detail: str):
    conn = get_connection()
    cursor = conn.cursor()
    ts = datetime.now(timezone.utc).isoformat()
    cursor.execute("""
        INSERT INTO audit_logs (timestamp, event_type, incident_id, detail)
        VALUES (?, ?, ?, ?);
    """, (ts, event_type, incident_id, detail))
    conn.commit()
    conn.close()

def fetch_audit_logs(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?;", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
