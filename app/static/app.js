// Global state
let incidents = [];
let units = [];
let selectedIncidentId = null;
let activeChatIncidentId = null;
let map = null;
let mapMarkers = {};
let unitMarkers = {};

// Initialize on window load
window.addEventListener('DOMContentLoaded', () => {
    initMap();
    startClock();
    loadIncidents();
    loadAnalyticsAndFleet();

    // Poll every 4 seconds for real-time updates
    setInterval(() => {
        loadIncidents(true);
    }, 4000);
});

// Real-time Clock
function startClock() {
    const clockEl = document.getElementById('live-clock');
    setInterval(() => {
        const now = new Date();
        clockEl.innerText = now.toUTCString().split(' ')[4] + ' UTC';
    }, 1000);
}

// Leaflet GIS Map Initialization
function initMap() {
    // Default center: India / New Delhi Sector (28.6139, 77.2090)
    map = L.map('map', {
        zoomControl: true,
        attributionControl: false
    }).setView([28.6139, 77.2090], 12);

    // OpenStreetMap dark carto tiles with reliable fallback
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap'
    }).addTo(map);
}

// Tab Navigation
function switchTab(tabName) {
    const cmdView = document.getElementById('view-command');
    const citizenView = document.getElementById('view-citizen');
    const fleetView = document.getElementById('view-fleet');

    const cmdBtn = document.getElementById('tab-cmd-btn');
    const citizenBtn = document.getElementById('tab-citizen-btn');
    const fleetBtn = document.getElementById('tab-fleet-btn');

    // Reset styles
    [cmdBtn, citizenBtn, fleetBtn].forEach(btn => {
        btn.className = "px-4 py-1.5 rounded-md text-slate-400 hover:text-slate-200 flex items-center gap-2 transition";
    });

    [cmdView, citizenView, fleetView].forEach(v => v.classList.add('hidden'));

    if (tabName === 'command') {
        cmdView.classList.remove('hidden');
        cmdBtn.className = "px-4 py-1.5 rounded-md bg-blue-600 text-white shadow-sm flex items-center gap-2 transition";
        setTimeout(() => map.invalidateSize(), 200);
    } else if (tabName === 'citizen') {
        citizenView.classList.remove('hidden');
        citizenBtn.className = "px-4 py-1.5 rounded-md bg-blue-600 text-white shadow-sm flex items-center gap-2 transition";
    } else if (tabName === 'fleet') {
        fleetView.classList.remove('hidden');
        fleetBtn.className = "px-4 py-1.5 rounded-md bg-blue-600 text-white shadow-sm flex items-center gap-2 transition";
        loadAnalyticsAndFleet();
    }
}

// Fetch Incidents from Backend API
async function loadIncidents(isSilent = false) {
    try {
        const res = await fetch('/api/incidents');
        const data = await res.json();
        incidents = data.incidents || [];
        
        document.getElementById('incident-count-badge').innerText = `${incidents.length} Active`;
        
        renderIncidentList();
        renderMapMarkers();
        loadUnitsOnMap();

        if (selectedIncidentId) {
            renderCopilotPanel(selectedIncidentId);
        } else if (incidents.length > 0 && !isSilent) {
            selectIncident(incidents[0].id);
        }
    } catch (err) {
        console.error("Error loading incidents:", err);
    }
}

// Render Incident List Sidebar
function renderIncidentList() {
    const container = document.getElementById('incident-list-container');
    const searchVal = document.getElementById('filter-search').value.toLowerCase();
    const categoryVal = document.getElementById('filter-category').value;

    const filtered = incidents.filter(item => {
        const matchSearch = item.title.toLowerCase().includes(searchVal) || 
                            item.location_name.toLowerCase().includes(searchVal) ||
                            item.id.toLowerCase().includes(searchVal);
        const matchCategory = categoryVal === 'ALL' || item.category === categoryVal;
        return matchSearch && matchCategory;
    });

    if (filtered.length === 0) {
        container.innerHTML = `<div class="text-center py-8 text-slate-500 text-xs">No incidents match search filter</div>`;
        return;
    }

    container.innerHTML = filtered.map(item => {
        const isSelected = item.id === selectedIncidentId;
        const isCritical = item.severity === 'P1-Critical';
        
        // Category Icon Mapping
        const catIcons = {
            'Fire': 'fa-fire text-rose-500',
            'Medical': 'fa-notes-medical text-emerald-400',
            'Crime': 'fa-shield-cat text-purple-400',
            'Hazard': 'fa-biohazard text-amber-400',
            'Traffic': 'fa-car-burst text-orange-400',
            'Disaster': 'fa-tornado text-blue-400'
        };
        const iconClass = catIcons[item.category] || 'fa-triangle-exclamation text-slate-400';

        // Severity Badge Colors
        const severityColors = {
            'P1-Critical': 'bg-rose-950 border-rose-700 text-rose-300 animate-critical',
            'P2-High': 'bg-amber-950 border-amber-700 text-amber-300',
            'P3-Medium': 'bg-blue-950 border-blue-700 text-blue-300',
            'P4-Low': 'bg-slate-800 border-slate-700 text-slate-300'
        };
        const sevClass = severityColors[item.severity] || 'bg-slate-800 text-slate-300';

        // Status Badge
        const statusColors = {
            'New': 'text-amber-400 bg-amber-950/60 border-amber-800/80',
            'Dispatched': 'text-blue-400 bg-blue-950/60 border-blue-800/80',
            'On Scene': 'text-indigo-400 bg-indigo-950/60 border-indigo-800/80',
            'Resolved': 'text-emerald-400 bg-emerald-950/60 border-emerald-800/80'
        };
        const statusClass = statusColors[item.status] || 'text-slate-400';

        return `
            <div onclick="selectIncident('${item.id}')" class="p-3 rounded-lg border transition cursor-pointer ${
                isSelected ? 'bg-slate-800/90 border-blue-500 shadow-md ring-1 ring-blue-500/50' : 'bg-slate-900 border-slate-800/80 hover:border-slate-700'
            }">
                <div class="flex items-center justify-between gap-2 mb-1.5">
                    <div class="flex items-center gap-2">
                        <i class="fa-solid ${iconClass} text-sm"></i>
                        <span class="font-bold text-xs text-slate-100">${item.title}</span>
                    </div>
                    <span class="text-[10px] px-2 py-0.5 rounded border font-mono font-bold ${sevClass}">${item.severity}</span>
                </div>

                <div class="text-[11px] text-slate-400 mb-2 flex items-center justify-between">
                    <span class="truncate"><i class="fa-solid fa-location-dot text-slate-500 mr-1"></i>${item.location_name}</span>
                    <span class="text-[10px] px-1.5 py-0.5 rounded border font-mono ${statusClass}">${item.status}</span>
                </div>

                <!-- Priority Bar -->
                <div class="w-full bg-slate-950 rounded-full h-1.5 overflow-hidden flex items-center">
                    <div class="h-full bg-gradient-to-r from-amber-500 to-rose-600 rounded-full" style="width: ${item.priority_score}%"></div>
                </div>
                <div class="flex justify-between items-center text-[9px] text-slate-500 mt-1 font-mono">
                    <span>${item.id}</span>
                    <span>Priority Score: <strong class="text-slate-300">${item.priority_score}</strong>/100</span>
                </div>
            </div>
        `;
    }).join('');
}

// Render Map Markers for Incidents
function renderMapMarkers() {
    incidents.forEach(item => {
        const markerKey = item.id;
        const color = item.severity === 'P1-Critical' ? '#f43f5e' : (item.severity === 'P2-High' ? '#f59e0b' : '#3b82f6');
        
        if (mapMarkers[markerKey]) {
            mapMarkers[markerKey].setLatLng([item.lat, item.lng]);
        } else {
            const customHtml = `
                <div class="custom-map-icon" style="background-color: ${color}; width: 26px; height: 26px; border: 2px solid #fff;">
                    <i class="fa-solid fa-triangle-exclamation"></i>
                </div>
            `;
            const icon = L.divIcon({
                html: customHtml,
                className: '',
                iconSize: [26, 26],
                iconAnchor: [13, 13]
            });

            const marker = L.marker([item.lat, item.lng], { icon: icon }).addTo(map);
            marker.bindPopup(`
                <div style="min-width:180px;">
                    <strong style="color:${color};">${item.severity}</strong> - ${item.title}<br/>
                    <small style="color:#94a3b8;">${item.location_name}</small><br/>
                    <button onclick="selectIncident('${item.id}')" style="margin-top:8px; width:100%; padding:4px; background:#2563eb; color:#fff; border:none; border-radius:4px; font-size:11px; cursor:pointer;">
                        Inspect Incident
                    </button>
                </div>
            `);
            mapMarkers[markerKey] = marker;
        }
    });
}

// Load Emergency Units on Map
async function loadUnitsOnMap() {
    try {
        const res = await fetch('/api/units');
        const data = await res.json();
        units = data.units || [];

        units.forEach(u => {
            const key = u.id;
            const colors = {
                'Police': '#3b82f6',
                'Fire': '#f59e0b',
                'EMS': '#10b981',
                'Hazmat': '#8b5cf6',
                'Traffic': '#ec4899'
            };
            const color = colors[u.type] || '#64748b';

            if (unitMarkers[key]) {
                unitMarkers[key].setLatLng([u.lat, u.lng]);
            } else {
                const customHtml = `
                    <div class="custom-map-icon" style="background-color: ${color}; width: 22px; height: 22px; border: 1.5px solid #fff;">
                        <i class="fa-solid fa-truck"></i>
                    </div>
                `;
                const icon = L.divIcon({
                    html: customHtml,
                    className: '',
                    iconSize: [22, 22],
                    iconAnchor: [11, 11]
                });

                const marker = L.marker([u.lat, u.lng], { icon: icon }).addTo(map);
                marker.bindPopup(`
                    <div>
                        <strong style="color:${color}">${u.name}</strong> (${u.type})<br/>
                        Status: <b>${u.status}</b><br/>
                        Base: ${u.base_station}
                    </div>
                `);
                unitMarkers[key] = marker;
            }
        });
    } catch (e) {
        console.error("Error loading units on map:", e);
    }
}

// Select Incident & Highlight
function selectIncident(incidentId) {
    selectedIncidentId = incidentId;
    renderIncidentList();
    renderCopilotPanel(incidentId);

    const item = incidents.find(i => i.id === incidentId);
    if (item && map) {
        map.flyTo([item.lat, item.lng], 14, { duration: 1 });
        if (mapMarkers[incidentId]) {
            mapMarkers[incidentId].openPopup();
        }
    }
}

// Render AI Co-Pilot Panel for Selected Incident
async function renderCopilotPanel(incidentId) {
    const panel = document.getElementById('copilot-panel');
    panel.innerHTML = `<div class="text-center py-10 text-slate-500"><i class="fa-solid fa-spinner fa-spin text-2xl"></i> Loading AI Triage Analysis...</div>`;

    try {
        const res = await fetch(`/api/incidents/${incidentId}`);
        const data = await res.json();
        const item = data.incident;
        const recommendations = data.recommendations || [];

        const dispatchedUnits = item.dispatched_units || [];

        panel.innerHTML = `
            <!-- Incident Header -->
            <div class="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-3">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-mono text-blue-400 font-bold">${item.id}</span>
                    <div class="flex items-center gap-2">
                        <span class="text-xs px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800 font-mono font-bold">${item.severity}</span>
                        <select onchange="updateIncidentStatus('${item.id}', this.value)" class="bg-slate-900 border border-slate-700 text-xs rounded px-2 py-1 text-slate-200 font-semibold focus:outline-none">
                            <option value="New" ${item.status==='New'?'selected':''}>Status: New</option>
                            <option value="Dispatched" ${item.status==='Dispatched'?'selected':''}>Status: Dispatched</option>
                            <option value="On Scene" ${item.status==='On Scene'?'selected':''}>Status: On Scene</option>
                            <option value="Resolved" ${item.status==='Resolved'?'selected':''}>Status: Resolved</option>
                        </select>
                    </div>
                </div>

                <h2 class="text-base font-bold text-slate-100">${item.title}</h2>
                <p class="text-xs text-slate-400"><i class="fa-solid fa-location-dot text-rose-400 mr-1"></i>${item.location_name}</p>

                <!-- Priority Meter -->
                <div class="space-y-1">
                    <div class="flex justify-between text-[11px] text-slate-400">
                        <span>Risk Priority Score:</span>
                        <span class="font-bold text-slate-200">${item.priority_score} / 100</span>
                    </div>
                    <div class="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
                        <div class="h-full bg-gradient-to-r from-amber-500 via-rose-500 to-red-600" style="width: ${item.priority_score}%"></div>
                    </div>
                </div>
            </div>

            <!-- AI Entity Extraction & Protocol -->
            <div class="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-3">
                <div class="flex items-center gap-2 text-xs font-bold text-blue-400 tracking-wider uppercase">
                    <i class="fa-solid fa-brain"></i> AI Extracted Entities & Protocol
                </div>

                <div class="grid grid-cols-2 gap-2 text-xs">
                    <div class="bg-slate-900 p-2.5 rounded-lg border border-slate-800/80">
                        <span class="text-[10px] text-slate-500 block uppercase">Reported Victims</span>
                        <strong class="text-slate-200">${item.victims_count} Persons</strong>
                    </div>
                    <div class="bg-slate-900 p-2.5 rounded-lg border border-slate-800/80">
                        <span class="text-[10px] text-slate-500 block uppercase">Identified Hazards</span>
                        <strong class="text-amber-400 truncate block">${item.hazards || 'None'}</strong>
                    </div>
                </div>

                <div class="bg-slate-900 p-3 rounded-lg border border-slate-800 text-xs space-y-1">
                    <span class="text-[10px] text-slate-500 font-bold uppercase block">AI Executive Summary</span>
                    <p class="text-slate-300 leading-relaxed">${item.ai_summary}</p>
                </div>

                <div class="bg-blue-950/40 border border-blue-800/60 p-3 rounded-lg text-xs space-y-1">
                    <span class="text-[10px] text-blue-300 font-bold uppercase block flex items-center gap-1">
                        <i class="fa-solid fa-clipboard-check"></i> Recommended Protocol
                    </span>
                    <p class="text-blue-200 font-mono text-[11px]">${item.recommended_protocol}</p>
                </div>
            </div>

            <!-- Smart Dispatch Recommendation Panel -->
            <div class="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-3">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2 text-xs font-bold text-emerald-400 tracking-wider uppercase">
                        <i class="fa-solid fa-truck-fast"></i> AI Dispatch Recommendations
                    </div>
                    <span class="text-[10px] text-slate-400 font-mono">${recommendations.length} Units Available</span>
                </div>

                ${dispatchedUnits.length > 0 ? `
                    <div class="p-2.5 bg-emerald-950/60 border border-emerald-800/80 rounded-lg text-xs text-emerald-300 flex items-center gap-2">
                        <i class="fa-solid fa-circle-check text-emerald-400"></i>
                        <span>Active Dispatched Units: <strong>${dispatchedUnits.join(', ')}</strong></span>
                    </div>
                ` : ''}

                <div class="space-y-2 max-h-[220px] overflow-y-auto pr-1">
                    ${recommendations.length === 0 ? `<div class="text-xs text-slate-500 py-4 text-center">No available units ready for dispatch</div>` : ''}
                    ${recommendations.slice(0, 4).map(rec => `
                        <div class="bg-slate-900 border border-slate-800 p-2.5 rounded-lg flex items-center justify-between text-xs hover:border-slate-700 transition">
                            <div>
                                <div class="font-bold text-slate-200 flex items-center gap-1.5">
                                    <span>${rec.name}</span>
                                    <span class="text-[9px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">${rec.type}</span>
                                </div>
                                <div class="text-[10px] text-slate-400 font-mono mt-0.5">
                                    Distance: <b>${rec.distance_km} km</b> | ETA: <b class="text-emerald-400">${rec.eta_minutes} min</b>
                                </div>
                            </div>

                            <button onclick="dispatchUnit('${item.id}', '${rec.unit_id}')" class="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded text-xs shadow transition flex items-center gap-1">
                                <i class="fa-solid fa-paper-plane text-[10px]"></i> Dispatch
                            </button>
                        </div>
                    `).join('')}
                </div>
            </div>

            <!-- Citizen Interactive Session Link -->
            <button onclick="openCitizenChatForIncident('${item.id}')" class="w-full py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded-lg border border-slate-700 text-xs flex items-center justify-center gap-2 transition">
                <i class="fa-solid fa-comments text-blue-400"></i> Open Citizen Interactive AI Triage Chat
            </button>
        `;
    } catch (e) {
        console.error("Error loading copilot panel:", e);
    }
}

// 1-Click Dispatch Action
async function dispatchUnit(incidentId, unitId) {
    try {
        const res = await fetch('/api/dispatch/assign', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                incident_id: incidentId,
                unit_ids: [unitId]
            })
        });
        const data = await res.json();
        if (data.success) {
            loadIncidents(true);
            renderCopilotPanel(incidentId);
        }
    } catch (e) {
        console.error("Error dispatching unit:", e);
    }
}

// Update Incident Status
async function updateIncidentStatus(incidentId, newStatus) {
    try {
        const res = await fetch(`/api/incidents/${incidentId}/status`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ status: newStatus })
        });
        const data = await res.json();
        if (data.success) {
            loadIncidents(true);
        }
    } catch (e) {
        console.error("Error updating status:", e);
    }
}

// Trigger Emergency Simulation Scenario
async function triggerSim(scenarioKey) {
    try {
        const res = await fetch('/api/simulator/trigger', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ scenario_key: scenarioKey })
        });
        const data = await res.json();
        if (data.success) {
            await loadIncidents(false);
            selectIncident(data.incident.id);
        }
    } catch (e) {
        console.error("Error triggering simulation:", e);
    }
}

// Submit Citizen Emergency Report
async function submitCitizenReport(event) {
    event.preventDefault();
    const location = document.getElementById('report-location').value;
    const caller = document.getElementById('report-caller').value;
    const description = document.getElementById('report-description').value;

    try {
        const res = await fetch('/api/incidents/report', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                location_name: location,
                reported_by: caller,
                description: description
            })
        });
        const data = await res.json();
        if (data.success) {
            const inc = data.incident;
            await loadIncidents(false);
            openCitizenChatForIncident(inc.id);
            document.getElementById('citizen-report-form').reset();
        }
    } catch (e) {
        console.error("Error submitting report:", e);
    }
}

// Open Citizen Chat Session
async function openCitizenChatForIncident(incidentId) {
    activeChatIncidentId = incidentId;
    switchTab('citizen');
    document.getElementById('chat-input').disabled = false;
    document.getElementById('chat-send-btn').disabled = false;
    
    document.getElementById('active-chat-incident-label').innerText = `Active Session: ${incidentId}`;
    document.getElementById('chat-status-badge').innerText = `Connected`;
    document.getElementById('chat-status-badge').className = `text-xs px-2.5 py-1 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800 font-mono`;

    await loadChatHistory(incidentId);
}

// Load Chat History
async function loadChatHistory(incidentId) {
    const box = document.getElementById('chat-messages-box');
    try {
        const res = await fetch(`/api/incidents/${incidentId}`);
        const data = await res.json();
        const history = data.chat_history || [];

        box.innerHTML = history.map(msg => {
            const isAI = msg.sender === 'AI Agent';
            return `
                <div class="flex flex-col ${isAI ? 'items-start' : 'items-end'}">
                    <div class="flex items-center gap-1.5 text-[10px] text-slate-500 mb-1">
                        <span class="font-bold ${isAI ? 'text-blue-400' : 'text-slate-300'}">${msg.sender}</span>
                        <span>•</span>
                        <span>${new Date(msg.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <div class="max-w-[85%] p-3 rounded-xl text-xs leading-relaxed ${
                        isAI ? 'bg-slate-800 text-slate-100 border border-slate-700/80 rounded-tl-none shadow' : 'bg-blue-600 text-white rounded-tr-none shadow'
                    }">
                        ${msg.message.replace(/\n/g, '<br/>')}
                    </div>
                </div>
            `;
        }).join('');
        box.scrollTop = box.scrollHeight;
    } catch (e) {
        console.error("Error loading chat history:", e);
    }
}

// Send Citizen Chat Message
async function sendCitizenChatMessage(event) {
    event.preventDefault();
    if (!activeChatIncidentId) return;

    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg) return;

    input.value = '';

    try {
        await fetch('/api/incidents/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                incident_id: activeChatIncidentId,
                message: msg
            })
        });

        await loadChatHistory(activeChatIncidentId);
        loadIncidents(true);
    } catch (e) {
        console.error("Error sending chat message:", e);
    }
}

// Fleet Status & Analytics Page
async function loadAnalyticsAndFleet() {
    try {
        const res = await fetch('/api/analytics');
        const data = await res.json();
        const m = data.metrics || {};
        const logs = data.audit_logs || [];

        // Metrics Banner
        document.getElementById('analytics-cards').innerHTML = `
            <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                <div class="text-xs text-slate-400 uppercase font-semibold mb-1">Total Incidents</div>
                <div class="text-2xl font-bold text-slate-100 font-mono">${m.total_incidents || 0}</div>
                <div class="text-[10px] text-slate-500 mt-1">${m.critical_p1_incidents || 0} P1-Critical</div>
            </div>
            <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                <div class="text-xs text-slate-400 uppercase font-semibold mb-1">Active Dispatches</div>
                <div class="text-2xl font-bold text-blue-400 font-mono">${m.active_dispatched || 0}</div>
                <div class="text-[10px] text-slate-500 mt-1">${m.resolved_incidents || 0} Resolved</div>
            </div>
            <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                <div class="text-xs text-slate-400 uppercase font-semibold mb-1">Fleet Readiness</div>
                <div class="text-2xl font-bold text-emerald-400 font-mono">${m.unit_readiness_pct || 0}%</div>
                <div class="text-[10px] text-slate-500 mt-1">${m.available_units || 0} / ${m.total_units || 0} Units Available</div>
            </div>
            <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                <div class="text-xs text-slate-400 uppercase font-semibold mb-1">AI Triage Latency</div>
                <div class="text-2xl font-bold text-indigo-400 font-mono">&lt; 120ms</div>
                <div class="text-[10px] text-slate-500 mt-1">Real-time Rule & Entity Extraction</div>
            </div>
        `;

        // Fleet Table
        const fleetRes = await fetch('/api/units');
        const fleetData = await fleetRes.json();
        const unitsList = fleetData.units || [];

        document.getElementById('fleet-units-tbody').innerHTML = unitsList.map(u => {
            const statusBadge = u.status === 'Available' ? 
                '<span class="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800 font-mono">Available</span>' :
                '<span class="px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800 font-mono">Dispatched</span>';
            return `
                <tr>
                    <td class="p-2.5 font-mono font-bold text-slate-200">${u.id}</td>
                    <td class="p-2.5">${u.name}</td>
                    <td class="p-2.5 text-slate-400">${u.type}</td>
                    <td class="p-2.5">${statusBadge}</td>
                    <td class="p-2.5 text-slate-400">${u.base_station}</td>
                </tr>
            `;
        }).join('');

        // Audit Logs
        document.getElementById('audit-log-container').innerHTML = logs.map(l => `
            <div class="p-2 rounded bg-slate-950 border border-slate-800/80 text-[11px] space-y-0.5">
                <div class="flex justify-between text-slate-500">
                    <span class="text-blue-400 font-bold">${l.event_type}</span>
                    <span>${new Date(l.timestamp).toLocaleTimeString()}</span>
                </div>
                <div class="text-slate-300">${l.detail}</div>
            </div>
        `).join('');
    } catch (e) {
        console.error("Error loading analytics:", e);
    }
}

// Tavily Live Emergency Web Search
async function executeTavilySearch(event) {
    event.preventDefault();
    const query = document.getElementById('tavily-query').value.trim();
    if (!query) return;

    const banner = document.getElementById('tavily-result-banner');
    const resultText = document.getElementById('tavily-result-text');

    banner.classList.remove('hidden');
    resultText.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-1"></i> Querying Tavily live search engine for: <b>"${query}"</b>...`;

    try {
        const res = await fetch('/api/search/tavily', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ query: query })
        });
        const data = await res.json();
        if (data.result) {
            resultText.innerHTML = `<strong>🌐 Tavily Live Intel:</strong> ${data.result}`;
        } else {
            resultText.innerHTML = `<strong>🌐 Tavily Search:</strong> No specific hazmat results found for "${query}".`;
        }
    } catch (e) {
        console.error("Tavily search error:", e);
        resultText.innerHTML = `<strong>⚠️ Tavily Search Error:</strong> Unable to fetch live web search results.`;
    }
}

function closeTavilyBanner() {
    document.getElementById('tavily-result-banner').classList.add('hidden');
}

