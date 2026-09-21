# AegisResponse AI — Public Safety Incident Agent (India GIS & Tavily Intel)

**AegisResponse AI** is a complete, intelligent Public Safety & Emergency Dispatch System designed for **India**. It features an automated AI Triage Agent, real-time GIS Command Center, Tavily live emergency web search, Indian emergency fleet dispatching, and interactive citizen triage guidance.

---

## 🚀 Quick Start Instructions

### 1. Requirements
- **Python 3.12+**
- Packages: `fastapi`, `uvicorn`, `pydantic`, `jinja2`

### 2. Launch the Application
Run the launcher script:

```bash
python run.py
```

Open your web browser:
👉 **[http://localhost:8000](http://localhost:8000)**

---

## 🇮🇳 Features & Architecture

### 1. Indian GIS Command Center (`app/static/index.html`, `app/static/app.js`)
- **Map Center**: New Delhi / NCR Sector (`28.6139, 77.2090`).
- **Interactive Map**: OpenStreetMap dark tiles with color-coded incident markers and live responder units.
- **Queue & Co-Pilot Inspector**: Priority scoring (1-100), severity badges (P1-Critical to P4-Low), extracted hazards, and SOP protocols.

### 2. Indian Emergency Response Fleet (`app/database.py`)
- `POL-112`: PCR Van 112 (Delhi Police)
- `POL-114`: Traffic Interceptor 114
- `FIRE-101`: DFS Fire Tender 101 (Connaught Place HQ)
- `FIRE-102`: Hydraulic Platform Ladder 102 (Okhla Industrial Fire Station)
- `AMB-108`: CATS ALS Ambulance 108 (LNJP Hospital)
- `AMB-109`: Emergency Trauma Ambulance 109 (AIIMS Trauma Center)
- `NDRF-501`: NDRF Battalion 8th Response Unit (Noida Regional Post)
- `HAZ-301`: Hazmat Chemical Response Van (Wazirpur Industrial Post)

### 3. Tavily Live Emergency Web Search (`app/triage_agent.py`)
- Integrated Tavily API Key (`tvly-dev-...`) for real-time web search of chemical datasheets, MSDS guidelines, evacuation radii, and first-aid instructions.
- Dedicated Command Center search widget and backend REST API endpoint (`POST /api/search/tavily`).

### 4. Automated AI Triage Agent (`app/triage_agent.py`)
- **NLP Categorization**: Fire, Medical, Crime, Hazard, Traffic, Disaster.
- **Priority Algorithm**: Calculates 1-100 score based on life threat, victim count, and active hazards.
- **Citizen Safety Co-Pilot**: Step-by-step guidance for callers (CPR, fire evacuation, chemical distance).
- **Caller Escalation**: Caller reports of condition worsening automatically escalate priority to CRITICAL.

### 5. Proximity Dispatch Engine (`app/dispatch_engine.py`)
- Haversine formula calculation for distance in kilometers between incident coordinates and available units.
- Automatic ETA estimation and unit capability ranking.

### 6. Emergency Simulator (`app/simulator.py`)
- One-click trigger buttons for pre-loaded Indian scenarios:
  - *Okhla Garment Factory Fire* (P1-Critical)
  - *NH-48 Ammonia Chemical Tanker Spill* (P1-Critical)
  - *Minto Bridge Underpass Submerged Bus Rescue* (P2-High)
  - *Rajiv Chowk Metro Transformer Blast*
  - *Connaught Place Bank Silent Alarm*

---

## 🛠️ Testing

Run the automated unit test suite:

```bash
python test_agent.py
```

Expected output:
```text
Ran 5 tests in 0.145s
OK
```

---

## 📁 Project Directory Structure

```text
Flexi Credit MiniProj/
├── app/
│   ├── __init__.py
│   ├── aegis_safety.db     # SQLite Database (Persistent Incidents & Units)
│   ├── database.py         # DB Schemas, ORM & Seed Data
│   ├── dispatch_engine.py  # Haversine Proximity Math & Dispatch Logic
│   ├── main.py             # FastAPI REST Server & Static File Host
│   ├── simulator.py        # Scenario Simulator Engine
│   ├── triage_agent.py     # AI Triage Parsing, Scoring & Tavily Intel
│   └── static/
│       ├── app.js          # Client UI Logic, Leaflet GIS Map & Polling
│       ├── index.html      # High-Tech Dark Mode Command Center UI
│       └── styles.css      # Dark Mode Layout & Pulse Animation Styling
├── README.md               # Documentation & System Architecture
├── requirements.txt        # Dependencies
├── run.py                  # Server Launcher Script
└── test_agent.py           # Automated Test Suite
```

---

## 📜 License & Copyright
Developed for Public Safety Emergency Command Centers and Citizen Safety Automation.
