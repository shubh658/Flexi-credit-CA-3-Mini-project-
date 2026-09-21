import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional

from app import database, triage_agent, dispatch_engine, simulator

app = FastAPI(
    title="AegisResponse AI - Public Safety Incident Agent API",
    description="Emergency Command Center & Citizen AI Triage API Engine",
    version="2.0.0"
)

# Pydantic schemas for request validation
class IncidentReportRequest(BaseModel):
    description: str
    location_name: Optional[str] = ""
    reported_by: Optional[str] = "Citizen Portal"

class CitizenChatRequest(BaseModel):
    incident_id: str
    message: str

class DispatchAssignRequest(BaseModel):
    incident_id: str
    unit_ids: List[str]

class StatusUpdateRequest(BaseModel):
    status: str # New, Dispatched, On Scene, Resolved

class TriggerScenarioRequest(BaseModel):
    scenario_key: str

class TavilySearchRequest(BaseModel):
    query: str

@app.on_event("startup")
def startup_event():
    database.init_db()

# Serve static UI files
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
def get_dashboard():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>AegisResponse AI Backend Running</h1>")

# --- Incidents Endpoints ---

@app.get("/api/incidents")
def list_incidents():
    incidents = database.fetch_all_incidents()
    return {"incidents": incidents, "count": len(incidents)}

@app.post("/api/incidents/report")
def report_incident(payload: IncidentReportRequest):
    if not payload.description.strip():
        raise HTTPException(status_code=400, detail="Description cannot be empty")
    incident = triage_agent.analyze_report(
        description=payload.description,
        location_name=payload.location_name,
        reported_by=payload.reported_by
    )
    return {"success": True, "incident": incident}

@app.get("/api/incidents/{incident_id}")
def get_incident_detail(incident_id: str):
    incident = database.fetch_incident_by_id(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    chat_history = database.fetch_chat_history(incident_id)
    recommendations = dispatch_engine.get_recommended_units(incident_id)
    return {
        "incident": incident,
        "chat_history": chat_history,
        "recommendations": recommendations
    }

@app.post("/api/incidents/chat")
def citizen_chat(payload: CitizenChatRequest):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    result = triage_agent.process_citizen_chat(payload.incident_id, payload.message)
    return result

@app.post("/api/incidents/{incident_id}/status")
def update_status(incident_id: str, payload: StatusUpdateRequest):
    valid_statuses = ["New", "Dispatched", "On Scene", "Resolved"]
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of {valid_statuses}")
    res = dispatch_engine.update_incident_status(incident_id, payload.status)
    return res

# --- Dispatch & Units Endpoints ---

@app.get("/api/units")
def list_units():
    units = database.fetch_all_units()
    return {"units": units}

@app.get("/api/dispatch/recommendations/{incident_id}")
def get_dispatch_recommendations(incident_id: str):
    recommendations = dispatch_engine.get_recommended_units(incident_id)
    return {"incident_id": incident_id, "recommendations": recommendations}

@app.post("/api/dispatch/assign")
def assign_units(payload: DispatchAssignRequest):
    if not payload.unit_ids:
        raise HTTPException(status_code=400, detail="No unit IDs provided")
    res = dispatch_engine.dispatch_units(payload.incident_id, payload.unit_ids)
    return res

# --- Simulator, Tavily & Analytics ---

@app.get("/api/simulator/scenarios")
def get_scenarios():
    return {"scenarios": simulator.get_available_scenarios()}

@app.post("/api/simulator/trigger")
def trigger_simulated_scenario(payload: TriggerScenarioRequest):
    incident = simulator.trigger_scenario(payload.scenario_key)
    return {"success": True, "incident": incident}

@app.post("/api/search/tavily")
def tavily_live_search(payload: TavilySearchRequest):
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    result = triage_agent.search_tavily_emergency_knowledge(payload.query)
    return {"query": payload.query, "result": result, "status": "active" if result else "no_results"}

@app.get("/api/analytics")
def get_analytics():
    incidents = database.fetch_all_incidents()
    units = database.fetch_all_units()
    audit_logs = database.fetch_audit_logs(limit=20)

    total_incidents = len(incidents)
    critical_count = sum(1 for i in incidents if i['severity'] == 'P1-Critical')
    dispatched_count = sum(1 for i in incidents if i['status'] == 'Dispatched')
    resolved_count = sum(1 for i in incidents if i['status'] == 'Resolved')

    total_units = len(units)
    available_units = sum(1 for u in units if u['status'] == 'Available')

    return {
        "metrics": {
            "total_incidents": total_incidents,
            "critical_p1_incidents": critical_count,
            "active_dispatched": dispatched_count,
            "resolved_incidents": resolved_count,
            "total_units": total_units,
            "available_units": available_units,
            "unit_readiness_pct": round((available_units / total_units * 100), 1) if total_units > 0 else 0,
            "tavily_search_status": "Active (Key Configured)"
        },
        "audit_logs": audit_logs
    }
