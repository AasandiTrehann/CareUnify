const API_BASE_URL = "http://localhost:8000/api/v1";

let activePatientId = null;
let currentPatientDemographics = null;

// User Session and Role State
let currentUserRole = null;
let currentUserProfile = { name: "", role: "" };

// Chart.js instances tracker to prevent canvas overlay redraw issues
let chartInstances = {
    bp: null,
    chol: null,
    a1c: null
};

// Page Router
function showSection(sectionId) {
    if (!currentUserRole) return;

    // Toggle active section
    document.querySelectorAll(".view-section").forEach(sec => {
        sec.classList.remove("active");
    });
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.add("active");
    }

    // Toggle active navbar tab
    document.querySelectorAll(".nav-item").forEach(item => {
        item.classList.remove("active");
    });
    
    if (sectionId === "dashboard-section") {
        document.getElementById("nav-dashboard").classList.add("active");
        loadPatients();
    } else if (sectionId === "queue-section") {
        document.getElementById("nav-queue").classList.add("active");
        loadMatchQueue();
    } else if (sectionId === "audit-section") {
        document.getElementById("nav-audit").classList.add("active");
        loadAuditLogs();
    }
}

// Session Login Handler
async function handleLogin(role) {
    currentUserRole = role;
    
    const overlay = document.getElementById("login-overlay");
    const sidebar = document.getElementById("app-sidebar");
    const mainContent = document.getElementById("app-main-content");
    
    // Set Profile Properties
    const avatar = document.getElementById("user-avatar-text");
    const roleText = document.getElementById("profile-role-text");
    const nameText = document.getElementById("profile-name-text");
    
    if (role === "doctor") {
        currentUserProfile = { name: "Dr. Alex Smith", role: "Doctor (Clinician)" };
        avatar.innerText = "D";
        avatar.style.background = "linear-gradient(135deg, var(--color-primary), #7e22ce)";
    } else if (role === "lab") {
        currentUserProfile = { name: "Tech Jones", role: "Lab Assistant" };
        avatar.innerText = "L";
        avatar.style.background = "linear-gradient(135deg, var(--color-secondary), #0f766e)";
    } else if (role === "patient") {
        currentUserProfile = { name: "John Doe", role: "Patient" };
        avatar.innerText = "P";
        avatar.style.background = "linear-gradient(135deg, var(--color-warning), #d97706)";
    }
    
    roleText.innerText = currentUserProfile.role;
    nameText.innerText = currentUserProfile.name;
    
    // Animate views transition
    overlay.style.display = "none";
    sidebar.style.display = (role === "patient") ? "none" : "flex";
    mainContent.style.display = "flex";
    
    // Apply role-based page elements restriction
    applyRolePermissions();
    
    if (role === "patient") {
        // Patients directly enter their own workspace.
        // We find the patient John Doe in the database
        mainContent.style.marginLeft = "0";
        mainContent.style.width = "100%";
        mainContent.style.padding = "24px";
        
        try {
            const res = await fetch(`${API_BASE_URL}/patients`);
            const patients = await res.json();
            
            // Find "John" or load the first one
            const john = patients.find(p => p.first_name.toLowerCase().includes("john")) || patients[0];
            if (john) {
                openPatientWorkspace(john.id);
            } else {
                alert("No patient record found in the database. Please log in as a Doctor and ingest mock records first.");
                logout();
            }
        } catch (err) {
            console.error("Patient login error:", err);
            alert("Error retrieving patient records. Make sure the API is running.");
            logout();
        }
    } else {
        // Doctor / Lab Assistant load directory dashboard
        mainContent.style.marginLeft = "";
        mainContent.style.width = "";
        mainContent.style.padding = "";
        showSection("dashboard-section");
        updateQueueBadge();
    }
}

// Session Logout Handler
function logout() {
    currentUserRole = null;
    activePatientId = null;
    currentPatientDemographics = null;
    
    // Clear active Chart.js graphs
    destroyCharts();
    
    // Reset workspace tab selection
    switchWorkspaceTab("timeline");
    
    // Hide UI panels and display login overlay
    document.getElementById("app-sidebar").style.display = "none";
    document.getElementById("app-main-content").style.display = "none";
    document.getElementById("login-overlay").style.display = "flex";
    
    // Reset search
    document.getElementById("patient-search").value = "";
}

// Enforces role-based display configurations
function applyRolePermissions() {
    const navQueue = document.getElementById("nav-queue");
    const navAudit = document.getElementById("nav-audit");
    const btnIngest = document.getElementById("btn-sidebar-ingest");
    const btnBack = document.getElementById("btn-back-to-dir");
    const chatContainer = document.querySelector(".chat-container");
    const btnPurge = document.getElementById("btn-gdpr-purge");
    
    if (currentUserRole === "doctor") {
        navQueue.style.display = "block";
        navAudit.style.display = "block";
        btnIngest.style.display = "flex";
        btnBack.style.display = "flex";
        chatContainer.style.display = "flex";
        btnPurge.style.display = "block";
        
        // Restore standard grid widths
        document.querySelector(".workspace-layout").style.gridTemplateColumns = "1.2fr 1fr";
    } else if (currentUserRole === "lab") {
        // Lab Assistant has restricted layout access
        navQueue.style.display = "none";
        navAudit.style.display = "none";
        btnIngest.style.display = "flex";
        btnBack.style.display = "flex";
        chatContainer.style.display = "none"; // Hide AI clinical queries
        btnPurge.style.display = "none";      // Hide GDPR delete
        
        // Expand Left Column timeline to take full width
        document.querySelector(".workspace-layout").style.gridTemplateColumns = "1fr";
    } else if (currentUserRole === "patient") {
        // Patient has highly restricted workspace layout
        navQueue.style.display = "none";
        navAudit.style.display = "none";
        btnIngest.style.display = "none";
        btnBack.style.display = "none";       // Hide back button
        chatContainer.style.display = "flex";  // Patients can query their own data
        btnPurge.style.display = "none";       // Patients cannot delete themselves
        
        // Restore columns width
        document.querySelector(".workspace-layout").style.gridTemplateColumns = "1.2fr 1fr";
    }
}

// Initializer
window.addEventListener("DOMContentLoaded", () => {
    // We check queue count periodically for badges
    updateQueueBadge();
    setInterval(updateQueueBadge, 15000);
});

// Load Patient Directory
async function loadPatients(query = "") {
    if (!currentUserRole) return;
    
    const listContainer = document.getElementById("patients-list");
    listContainer.innerHTML = `<div class="spinner" style="grid-column: 1/-1; margin: 40px auto;"></div>`;

    try {
        const url = query ? `${API_BASE_URL}/patients?query=${encodeURIComponent(query)}` : `${API_BASE_URL}/patients`;
        const res = await fetch(url);
        const patients = await res.json();

        listContainer.innerHTML = "";
        
        if (patients.length === 0) {
            listContainer.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); margin-top: 40px;">
                    <span class="material-icons" style="font-size: 48px; margin-bottom: 12px;">person_search</span>
                    <p>No unified patient records found.</p>
                </div>
            `;
            return;
        }

        patients.forEach(p => {
            const card = document.createElement("div");
            card.className = "glass-card patient-card";
            card.onclick = () => openPatientWorkspace(p.id);

            const isMale = (p.gender || "").toLowerCase() === "male";
            const avatarIcon = isMale ? "male" : "female";
            const avatarColor = isMale ? "rgba(13, 148, 136, 0.15)" : "rgba(168, 85, 247, 0.15)";
            const iconColor = isMale ? "var(--color-secondary)" : "var(--color-primary)";

            card.innerHTML = `
                <div class="patient-avatar" style="background: ${avatarColor}; color: ${iconColor};">
                    <span class="material-icons">${avatarIcon}</span>
                </div>
                <h3 class="patient-name">${p.first_name} ${p.last_name}</h3>
                <div class="patient-meta-row">
                    <span class="material-icons" style="font-size: 14px;">calendar_today</span>
                    <span>DOB: ${p.dob}</span>
                </div>
                <div class="patient-meta-row">
                    <span class="material-icons" style="font-size: 14px;">phone</span>
                    <span>${p.phone || "No phone"}</span>
                </div>
                <div class="patient-meta-row">
                    <span class="material-icons" style="font-size: 14px;">badge</span>
                    <span>SSN: ${p.ssn || "Unavailable"}</span>
                </div>
            `;
            listContainer.appendChild(card);
        });
    } catch (err) {
        console.error("Error loading patients:", err);
        listContainer.innerHTML = `<div style="grid-column: 1/-1; color: var(--color-error); text-align: center;">Error loading patient records. Ensure API backend is running.</div>`;
    }
}

// Search debounce
let searchTimeout;
function searchPatients() {
    clearTimeout(searchTimeout);
    const query = document.getElementById("patient-search").value;
    searchTimeout = setTimeout(() => {
        loadPatients(query);
    }, 300);
}

// Open Workspace for a patient
async function openPatientWorkspace(patientId) {
    activePatientId = patientId;
    
    // Switch view
    document.querySelectorAll(".view-section").forEach(sec => sec.classList.remove("active"));
    document.getElementById("patient-detail-section").classList.add("active");
    
    // Reset workspace tab selection
    switchWorkspaceTab("timeline");
    
    // Loading indicators
    document.getElementById("det-name").innerText = "Loading patient...";
    document.getElementById("det-dob").innerText = "-";
    document.getElementById("det-gender").innerText = "-";
    document.getElementById("det-ssn").innerText = "-";
    document.getElementById("det-contact").innerText = "-";
    document.getElementById("timeline-list").innerHTML = `<div class="spinner" style="margin: 40px auto;"></div>`;
    document.getElementById("provenance-list").innerHTML = `<div class="spinner" style="margin: 20px auto;"></div>`;
    
    // Reset Chat Box
    document.getElementById("chat-box").innerHTML = `
        <div class="chat-bubble assistant">
            Hello! I have loaded the unified patient clinical record. Ask me any natural language clinical question, such as:
            <br><em>"What medications has this patient been on?"</em> or 
            <br><em>"Summarize their cardiovascular checkups."</em>
        </div>
    `;

    try {
        // 1. Fetch details
        const resDetail = await fetch(`${API_BASE_URL}/patients/${patientId}`);
        if (!resDetail.ok) throw new Error("Failed to load demographics");
        const p = await resDetail.json();
        
        currentPatientDemographics = p;
        
        // Render banner
        document.getElementById("det-name").innerText = `${p.first_name} ${p.last_name}`;
        document.getElementById("det-dob").innerText = p.dob;
        document.getElementById("det-gender").innerText = p.gender ? p.gender.charAt(0).toUpperCase() + p.gender.slice(1) : "Unknown";
        document.getElementById("det-ssn").innerText = p.ssn || "N/A";
        document.getElementById("det-contact").innerText = `${p.phone || "No phone"} | ${p.email || "No email"}`;
        
        const isMale = (p.gender || "").toLowerCase() === "male";
        document.getElementById("det-avatar").innerText = p.first_name.charAt(0) + p.last_name.charAt(0);
        document.getElementById("det-avatar").style.background = isMale 
            ? "linear-gradient(135deg, var(--color-secondary), #0f766e)" 
            : "linear-gradient(135deg, var(--color-primary), #7e22ce)";

        // 2. Fetch timeline
        const resTimeline = await fetch(`${API_BASE_URL}/patients/${patientId}/timeline`);
        const timeline = await resTimeline.json();
        renderTimeline(timeline);

        // 3. Render provenance links
        renderProvenance(p.lineage_links);

    } catch (err) {
        console.error("Error opening workspace:", err);
        alert("Failed to load clinical workspace. See console.");
    }
}

// Render FHIR timeline
function renderTimeline(events) {
    const list = document.getElementById("timeline-list");
    list.innerHTML = "";
    
    if (events.length === 0) {
        list.innerHTML = `<div style="text-align: center; color: var(--text-muted); margin-top: 40px;">No clinical events matching this patient. Ingest lab CSVs or OCR documents first.</div>`;
        return;
    }
    
    events.forEach(ev => {
        const item = document.createElement("div");
        const typeCls = ev.resource_type.toLowerCase();
        item.className = `timeline-item ${typeCls}`;
        
        let icon = "assignment";
        let badgeColor = "rgba(255,255,255,0.08)";
        let textColor = "white";
        
        if (typeCls === "observation") {
            icon = "biotech";
            badgeColor = "rgba(13, 148, 136, 0.15)";
            textColor = "var(--color-secondary)";
        } else if (typeCls === "medicationrequest") {
            icon = "medication";
            badgeColor = "rgba(168, 85, 247, 0.15)";
            textColor = "var(--color-primary)";
        } else if (typeCls === "encounter") {
            icon = "medical_services";
            badgeColor = "rgba(16, 185, 129, 0.15)";
            textColor = "var(--color-success)";
        } else if (typeCls === "diagnosticreport") {
            icon = "analytics";
            badgeColor = "rgba(245, 158, 11, 0.15)";
            textColor = "var(--color-warning)";
        }
        
        item.innerHTML = `
            <div class="timeline-marker"></div>
            <div class="timeline-date">${ev.date}</div>
            <div class="timeline-body">
                <div class="timeline-title">
                    <span class="material-icons" style="font-size: 16px; color: ${textColor};">${icon}</span>
                    <span>${ev.resource_type}</span>
                    <span class="timeline-badge" style="background: ${badgeColor}; color: ${textColor};">${ev.source_system}</span>
                </div>
                <p class="timeline-desc">${ev.summary_text}</p>
            </div>
        `;
        list.appendChild(item);
    });
}

// Render data provenance links
function renderProvenance(links) {
    const list = document.getElementById("provenance-list");
    list.innerHTML = "";
    
    if (links.length === 0) {
        list.innerHTML = `<p style="color: var(--text-muted); font-size: 13px;">No original ingestion source mappings recorded.</p>`;
        return;
    }
    
    links.forEach(l => {
        const box = document.createElement("div");
        box.className = "lineage-box";
        
        let icon = "api";
        if (l.source_system === "OCR_SCAN") icon = "picture_as_pdf";
        if (l.source_system === "VOICE_DICTATION") icon = "record_voice_over";
        if (l.source_system === "LAB_CSV_UPLOAD") icon = "table_view";
        
        box.innerHTML = `
            <div class="lineage-title">
                <span class="material-icons" style="font-size: 16px; color: var(--color-warning);">${icon}</span>
                <span>Source: ${l.source_system}</span>
            </div>
            <div style="color: var(--text-muted); font-size: 11px; margin-top: 4px;">Mapped: ${l.created_at}</div>
            <div style="color: var(--text-muted); font-size: 11px;">Source ID: ${l.source_patient_id || "N/A"}</div>
        `;
        list.appendChild(box);
    });
}

// Workspace Tab Switching (Timeline vs. Charts)
function switchWorkspaceTab(tab) {
    const tabTimeline = document.getElementById("tab-timeline");
    const tabAnalytics = document.getElementById("tab-analytics");
    const timelineList = document.getElementById("timeline-list");
    const analyticsContainer = document.getElementById("analytics-container");
    
    if (tab === "timeline") {
        tabTimeline.classList.add("active");
        tabAnalytics.classList.remove("active");
        timelineList.style.display = "block";
        analyticsContainer.style.display = "none";
    } else {
        tabTimeline.classList.remove("active");
        tabAnalytics.classList.add("active");
        timelineList.style.display = "none";
        analyticsContainer.style.display = "flex";
        
        if (activePatientId) {
            renderClinicalCharts(activePatientId);
        }
    }
}

// Destroys active charts to prevent canvas overlaps
function destroyCharts() {
    Object.keys(chartInstances).forEach(key => {
        if (chartInstances[key]) {
            chartInstances[key].destroy();
            chartInstances[key] = null;
        }
    });
}

// Renders visual statistics using Chart.js on chronological lab observations
async function renderClinicalCharts(patientId) {
    destroyCharts();

    try {
        const resTimeline = await fetch(`${API_BASE_URL}/patients/${patientId}/timeline`);
        const events = await resTimeline.json();
        
        // Filter out observations
        const observations = events
            .filter(ev => ev.resource_type.toLowerCase() === "observation")
            .map(ev => ({
                date: ev.date,
                payload: ev.payload
            }));
            
        // Group by clinical metrics
        let bpData = [];
        let cholData = { total: [], hdl: [], ldl: [] };
        let a1cData = [];
        
        observations.forEach(obs => {
            const codeObj = obs.payload.code || {};
            const text = (codeObj.text || "").toLowerCase();
            
            // 1. Blood Pressure Check
            if (text.includes("blood pressure") || text.includes("bp") || obs.payload.component) {
                if (obs.payload.component && obs.payload.component.length >= 2) {
                    // Extract systolic/diastolic components
                    const systolicVal = obs.payload.component[0].valueQuantity?.value;
                    const diastolicVal = obs.payload.component[1].valueQuantity?.value;
                    if (systolicVal && diastolicVal) {
                        bpData.push({ date: obs.date, systolic: systolicVal, diastolic: diastolicVal });
                    }
                } else if (obs.payload.valueString) {
                    // Parse strings like "130/85"
                    const parts = obs.payload.valueString.split("/");
                    if (parts.length === 2) {
                        bpData.push({ date: obs.date, systolic: parseFloat(parts[0]), diastolic: parseFloat(parts[1]) });
                    }
                }
            }
            
            // 2. Cholesterol Panel
            if (text.includes("cholesterol") || text.includes("hdl") || text.includes("ldl")) {
                const val = obs.payload.valueQuantity?.value;
                if (val) {
                    if (text === "hdl") {
                        cholData.hdl.push({ date: obs.date, value: val });
                    } else if (text === "ldl") {
                        cholData.ldl.push({ date: obs.date, value: val });
                    } else {
                        cholData.total.push({ date: obs.date, value: val });
                    }
                }
            }
            
            // 3. HbA1c
            if (text.includes("a1c") || text.includes("glycated")) {
                const val = obs.payload.valueQuantity?.value;
                if (val) {
                    a1cData.push({ date: obs.date, value: val });
                }
            }
        });
        
        // Sorting datasets chronologically
        const sortByDate = (a, b) => new Date(a.date) - new Date(b.date);
        bpData.sort(sortByDate);
        cholData.total.sort(sortByDate);
        cholData.hdl.sort(sortByDate);
        cholData.ldl.sort(sortByDate);
        a1cData.sort(sortByDate);
        
        // Common chart styling configurations
        const chartFontColor = "#94a3b8";
        const gridColor = "rgba(255, 255, 255, 0.05)";
        
        const chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: chartFontColor, font: { family: 'Inter', size: 10 } }
                }
            },
            scales: {
                x: {
                    grid: { color: gridColor },
                    ticks: { color: chartFontColor, font: { family: 'Inter', size: 9 } }
                },
                y: {
                    grid: { color: gridColor },
                    ticks: { color: chartFontColor, font: { family: 'Inter', size: 9 } }
                }
            }
        };

        // Render BP Chart
        if (bpData.length > 0) {
            const ctx = document.getElementById("bp-chart").getContext("2d");
            chartInstances.bp = new Chart(ctx, {
                type: "line",
                data: {
                    labels: bpData.map(d => d.date),
                    datasets: [
                        {
                            label: "Systolic",
                            data: bpData.map(d => d.systolic),
                            borderColor: "#ef4444",
                            backgroundColor: "rgba(239, 68, 68, 0.1)",
                            tension: 0.3,
                            fill: true
                        },
                        {
                            label: "Diastolic",
                            data: bpData.map(d => d.diastolic),
                            borderColor: "#3b82f6",
                            backgroundColor: "rgba(59, 130, 246, 0.1)",
                            tension: 0.3,
                            fill: true
                        }
                    ]
                },
                options: chartOptions
            });
        }

        // Render Cholesterol Chart
        // Combine or map LDL, HDL, and Total Cholesterol
        const cholDates = [...new Set([
            ...cholData.total.map(d => d.date),
            ...cholData.hdl.map(d => d.date),
            ...cholData.ldl.map(d => d.date)
        ])].sort((a,b) => new Date(a) - new Date(b));
        
        if (cholDates.length > 0) {
            // Helper function to locate observation value on specific date
            const findValOnDate = (dataset, date) => {
                const match = dataset.find(d => d.date === date);
                return match ? match.value : null;
            };

            const ctx = document.getElementById("chol-chart").getContext("2d");
            chartInstances.chol = new Chart(ctx, {
                type: "bar",
                data: {
                    labels: cholDates,
                    datasets: [
                        {
                            label: "Total Cholesterol",
                            data: cholDates.map(d => findValOnDate(cholData.total, d)),
                            backgroundColor: "rgba(168, 85, 247, 0.65)",
                            borderColor: "var(--color-primary)",
                            borderWidth: 1
                        },
                        {
                            label: "LDL (Bad)",
                            data: cholDates.map(d => findValOnDate(cholData.ldl, d)),
                            backgroundColor: "rgba(239, 68, 68, 0.65)",
                            borderColor: "#ef4444",
                            borderWidth: 1
                        },
                        {
                            label: "HDL (Good)",
                            data: cholDates.map(d => findValOnDate(cholData.hdl, d)),
                            backgroundColor: "rgba(16, 185, 129, 0.65)",
                            borderColor: "var(--color-success)",
                            borderWidth: 1
                        }
                    ]
                },
                options: chartOptions
            });
        }

        // Render HbA1c Chart
        if (a1cData.length > 0) {
            const ctx = document.getElementById("a1c-chart").getContext("2d");
            chartInstances.a1c = new Chart(ctx, {
                type: "line",
                data: {
                    labels: a1cData.map(d => d.date),
                    datasets: [
                        {
                            label: "HbA1c (%)",
                            data: a1cData.map(d => d.value),
                            borderColor: "var(--color-secondary)",
                            backgroundColor: "rgba(13, 148, 136, 0.1)",
                            tension: 0.3,
                            fill: true
                        }
                    ]
                },
                options: chartOptions
            });
        }

    } catch (err) {
        console.error("Error drawing charts:", err);
    }
}

// RAG Conversation Logic
async function sendChatQuery() {
    const input = document.getElementById("chat-input");
    const query = input.value.trim();
    if (!query) return;

    input.value = "";
    
    const chatBox = document.getElementById("chat-box");
    
    // Add user bubble
    const userBubble = document.createElement("div");
    userBubble.className = "chat-bubble user";
    userBubble.innerText = query;
    chatBox.appendChild(userBubble);
    chatBox.scrollTop = chatBox.scrollHeight;
    
    // Add thinking bubble
    const thinkingBubble = document.createElement("div");
    thinkingBubble.className = "chat-bubble assistant";
    thinkingBubble.innerHTML = `<div class="spinner" style="width: 14px; height: 14px; display: inline-block; vertical-align: middle; margin-right: 8px;"></div>Thinking...`;
    chatBox.appendChild(thinkingBubble);
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
        const res = await fetch(`${API_BASE_URL}/query`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                patient_id: activePatientId,
                query: query
            })
        });
        
        if (!res.ok) throw new Error("RAG API failed");
        
        const data = await res.json();
        
        // Remove thinking bubble
        chatBox.removeChild(thinkingBubble);
        
        // Add response bubble
        const assistantBubble = document.createElement("div");
        assistantBubble.className = "chat-bubble assistant";
        
        let rawAnswer = data.answer;
        // Escape standard HTML, but format newlines as <br>
        let formattedAnswer = rawAnswer.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, "<br>");
        
        assistantBubble.innerHTML = `<div>${formattedAnswer}</div>`;
        
        // Render citations
        if (data.sources && data.sources.length > 0) {
            const sourcesDiv = document.createElement("div");
            sourcesDiv.className = "chat-sources";
            sourcesDiv.innerHTML = `<strong>References:</strong> `;
            
            data.sources.forEach((src, idx) => {
                sourcesDiv.innerHTML += `
                    <span class="chat-source-badge" title="${src.text}">
                        [${idx + 1}] ${src.resource_type} (${src.source_system})
                    </span>
                `;
            });
            assistantBubble.appendChild(sourcesDiv);
        }
        
        chatBox.appendChild(assistantBubble);
        
        // Render offline fallback banner if LLM fell back
        if (data.is_fallback) {
            const fallbackBubble = document.createElement("div");
            fallbackBubble.className = "chat-bubble system";
            fallbackBubble.innerText = "System notice: Ollama local instance is offline. Synthesizing keyword-based vector search context.";
            chatBox.appendChild(fallbackBubble);
        }
        
        chatBox.scrollTop = chatBox.scrollHeight;

    } catch (err) {
        console.error("Error in query:", err);
        chatBox.removeChild(thinkingBubble);
        const errBubble = document.createElement("div");
        errBubble.className = "chat-bubble assistant";
        errBubble.style.color = "var(--color-error)";
        errBubble.innerText = "Error: Clinical Intelligence service encountered an error while synthesizing context. Verify Ollama is running.";
        chatBox.appendChild(errBubble);
        chatBox.scrollTop = chatBox.scrollHeight;
    }
}

function handleChatKey(event) {
    if (event.key === "Enter") {
        sendChatQuery();
    }
}

// GDPR purge
async function confirmGdprErasure() {
    if (!activePatientId || !currentPatientDemographics) return;
    
    const confirmName = prompt(
        `GDPR Right-to-Erasure Action:\n` +
        `This will permanently purge the Golden Record, data links, clinical resources, and RAG embeddings for this patient.\n` +
        `To confirm deletion, type the patient's full name ("${currentPatientDemographics.first_name} ${currentPatientDemographics.last_name}"):`
    );
    
    if (confirmName === `${currentPatientDemographics.first_name} ${currentPatientDemographics.last_name}`) {
        try {
            const res = await fetch(`${API_BASE_URL}/patients/${activePatientId}`, {
                method: "DELETE"
            });
            if (res.ok) {
                alert("Patient records purged successfully.");
                if (currentUserRole === "patient") {
                    logout();
                } else {
                    showSection("dashboard-section");
                }
            } else {
                throw new Error("Purge failed");
            }
        } catch (err) {
            alert("GDPR delete failed: " + err.message);
        }
    } else if (confirmName !== null) {
        alert("Verification name did not match. Deletion aborted.");
    }
}

// Entity Resolution: Load Match Queue
async function loadMatchQueue() {
    const container = document.getElementById("queue-container");
    container.innerHTML = `<div class="spinner" style="margin: 40px auto;"></div>`;

    try {
        const res = await fetch(`${API_BASE_URL}/match-queue`);
        const queue = await res.json();
        
        container.innerHTML = "";
        
        // Update badge count
        const badge = document.getElementById("queue-count-badge");
        badge.innerText = queue.length;
        badge.style.display = queue.length > 0 ? "inline-block" : "none";
        
        if (queue.length === 0) {
            container.innerHTML = `
                <div class="glass-card" style="text-align: center; color: var(--text-muted); padding: 40px;">
                    <span class="material-icons" style="font-size: 48px; color: var(--color-success); margin-bottom: 12px;">done_all</span>
                    <p>All clean! There are no potential duplicates in the review queue.</p>
                </div>
            `;
            return;
        }

        queue.forEach(item => {
            const card = document.createElement("div");
            card.className = "glass-card match-item";
            
            const features = item.matching_features;
            
            // Generate field checks (compare values side-by-side)
            const fieldsToCompare = [
                { label: "First Name", key: "first_name", incoming: item.incoming_payload.first_name, candidate: item.candidate_phone ? item.candidate_name.split(" ")[0] : item.candidate_name, score: features.first_name_sim },
                { label: "Last Name", key: "last_name", incoming: item.incoming_payload.last_name, candidate: item.candidate_name.split(" ").slice(-1)[0], score: features.last_name_sim },
                { label: "DOB", key: "dob", incoming: item.incoming_payload.dob, candidate: item.candidate_dob, score: features.dob_sim },
                { label: "SSN", key: "ssn", incoming: item.incoming_payload.ssn || "N/A", candidate: item.candidate_ssn || "N/A", score: features.ssn_sim },
                { label: "Phone", key: "phone", incoming: item.incoming_payload.phone || "N/A", candidate: item.candidate_phone || "N/A", score: features.phone_sim },
                { label: "Email", key: "email", incoming: item.incoming_payload.email || "N/A", candidate: item.candidate_email || "N/A", score: features.email_sim },
                { label: "Address", key: "address", incoming: item.incoming_payload.address || "N/A", candidate: item.candidate_address || "N/A", score: features.address_sim }
            ];

            let comparisonHTML = "";
            fieldsToCompare.forEach(f => {
                // Highlight difference
                let isDiff = f.score < 0.85;
                if (f.incoming === "N/A" || f.candidate === "N/A") isDiff = false;
                const statusClass = isDiff ? "diff" : "match";
                const checkIcon = isDiff ? "warning" : "check_circle";
                const iconColor = isDiff ? "var(--color-warning)" : "var(--color-success)";

                comparisonHTML += `
                    <div class="comparison-field ${statusClass}">
                        <span style="font-weight: 500;">${f.label}</span>
                        <div style="text-align: right;">
                            <span style="color: var(--text-muted);">${f.candidate}</span>
                            <span style="margin: 0 8px; color: var(--text-dark);">➔</span>
                            <span style="font-weight: 600;">${f.incoming}</span>
                            <span class="material-icons" style="font-size: 14px; vertical-align: middle; margin-left: 4px; color: ${iconColor};">${checkIcon}</span>
                        </div>
                    </div>
                `;
            });

            const percentScore = Math.round(item.match_score * 100);
            
            card.innerHTML = `
                <div class="match-header-row">
                    <div>
                        <h4 style="font-size: 16px; font-weight: 600;">Duplicate Record Candidate: ${item.incoming_payload.first_name} ${item.incoming_payload.last_name}</h4>
                        <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">Flagged profile matches Golden Record: <strong>${item.candidate_name}</strong></div>
                    </div>
                    <div class="match-percentage">${percentScore}% Match Prob</div>
                </div>

                <div class="match-comparison-grid">
                    <div class="comparison-column">
                        <div class="comparison-column-title">Demographics Comparison</div>
                        ${comparisonHTML}
                    </div>
                    
                    <div class="comparison-column" style="display: flex; flex-direction: column; justify-content: space-between;">
                        <div>
                            <div class="comparison-column-title">Integration Logic Diagnostics</div>
                            <p style="font-size: 13px; color: var(--text-muted); line-height: 1.5; margin-bottom: 12px;">
                                Phonetic algorithm (Soundex/NYSIIS) matched birth keys: <strong>${item.incoming_payload.last_name.toUpperCase()}</strong> initial DOB grouping.
                            </p>
                            <p style="font-size: 13px; color: var(--text-muted); line-height: 1.5;">
                                Weighted scoring parameters identified Name similarities (JW First: ${Math.round(features.first_name_sim*100)}%, JW Last: ${Math.round(features.last_name_sim*100)}%) and DOB matching score (${Math.round(features.dob_sim*100)}%).
                            </p>
                        </div>
                        
                        <div class="match-actions" style="margin-top: 24px;">
                            <button class="btn btn-reject" onclick="resolveMatch('${item.id}', 'reject')">Reject & Create New</button>
                            <button class="btn btn-approve" onclick="resolveMatch('${item.id}', 'approve')">Approve Merge Link</button>
                        </div>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });
    } catch (err) {
        console.error("Error loading queue:", err);
        container.innerHTML = `<div style="color: var(--color-error); text-align: center;">Error loading review queue.</div>`;
    }
}

// Update match queue badge count
async function updateQueueBadge() {
    try {
        const res = await fetch(`${API_BASE_URL}/match-queue`);
        const queue = await res.json();
        const badge = document.getElementById("queue-count-badge");
        badge.innerText = queue.length;
        badge.style.display = queue.length > 0 ? "inline-block" : "none";
    } catch (err) {
        // fail silently on background poll
    }
}

// Resolve duplicate record merge alert
async function resolveMatch(queueId, action) {
    const formData = new FormData();
    formData.append("action", action);

    try {
        const res = await fetch(`${API_BASE_URL}/match-queue/${queueId}/resolve`, {
            method: "POST",
            body: formData
        });
        if (res.ok) {
            alert(`Match resolved. Action: ${action.toUpperCase()}`);
            loadMatchQueue();
        } else {
            throw new Error("Failed to resolve");
        }
    } catch (err) {
        alert("Error resolving match: " + err.message);
    }
}

// Load HIPAA compliance audit trail logs
async function loadAuditLogs() {
    const rowsContainer = document.getElementById("audit-log-rows");
    rowsContainer.innerHTML = `<tr><td colspan="5" style="text-align: center;"><div class="spinner" style="margin: 20px auto;"></div></td></tr>`;

    try {
        const res = await fetch(`${API_BASE_URL}/audit`);
        const logs = await res.json();
        
        rowsContainer.innerHTML = "";
        
        if (logs.length === 0) {
            rowsContainer.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No audit trails recorded.</td></tr>`;
            return;
        }

        logs.forEach(l => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td style="color: var(--color-secondary); font-family: monospace;">${l.timestamp}</td>
                <td><strong>${l.user_id}</strong></td>
                <td><span style="padding: 2px 6px; border-radius: 4px; background: rgba(255,255,255,0.05); font-weight: 600; font-size: 11px;">${l.action}</span></td>
                <td style="font-size: 11px; color: var(--text-dark);">${l.patient_id || "System"}</td>
                <td style="color: var(--text-muted);">${l.details}</td>
            `;
            rowsContainer.appendChild(tr);
        });
    } catch (err) {
        console.error("Error loading audit logs:", err);
        rowsContainer.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--color-error);">Error retrieving audit log.</td></tr>`;
    }
}

// Ingest Modal control
function openIngestModal() {
    document.getElementById("ingest-modal").classList.add("active");
    toggleIngestFields();
}

// Close Ingestion view overlay
function closeIngestModal() {
    document.getElementById("ingest-modal").classList.remove("active");
}

// Adapts modal inputs based on ingestion channel selection
function toggleIngestFields() {
    const type = document.getElementById("ingest-type").value;
    const jsonWrapper = document.getElementById("json-input-wrapper");
    const fileWrapper = document.getElementById("file-input-wrapper");
    
    if (type === "patient") {
        jsonWrapper.style.display = "block";
        fileWrapper.style.display = "none";
    } else {
        jsonWrapper.style.display = "none";
        fileWrapper.style.display = "block";
        
        // Adjust file input accept attributes for guidance
        const fileInput = document.getElementById("file-upload");
        if (type === "csv") fileInput.accept = ".csv";
        if (type === "ocr") fileInput.accept = ".pdf,image/*";
        if (type === "voice") fileInput.accept = ".wav,.mp3";
    }
}

// Ingest form submission
async function submitIngestion(event) {
    event.preventDefault();
    
    const submitBtn = document.getElementById("btn-ingest-submit");
    submitBtn.innerText = "Ingesting & Analyzing...";
    submitBtn.disabled = true;
    
    const type = document.getElementById("ingest-type").value;
    const sourceSystem = document.getElementById("source-system").value;

    try {
        let response;
        if (type === "patient") {
            const rawJson = document.getElementById("json-payload").value;
            let payload;
            try {
                payload = JSON.parse(rawJson);
            } catch (je) {
                alert("Invalid JSON format. Check brackets and quotes.");
                submitBtn.innerText = "Upload & Process";
                submitBtn.disabled = false;
                return;
            }
            
            payload.sourceSystem = sourceSystem;

            response = await fetch(`${API_BASE_URL}/ingest/patient`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
        } else {
            const fileInput = document.getElementById("file-upload");
            if (fileInput.files.length === 0) {
                alert("Please select a file to ingest.");
                submitBtn.innerText = "Upload & Process";
                submitBtn.disabled = false;
                return;
            }
            
            const file = fileInput.files[0];
            const formData = new FormData();
            formData.append("file", file);
            formData.append("sourceSystem", sourceSystem);
            
            response = await fetch(`${API_BASE_URL}/ingest/${type}`, {
                method: "POST",
                body: formData
            });
        }

        if (!response.ok) {
            const errDetail = await response.json();
            throw new Error(errDetail.detail || "Server ingestion failed");
        }
        
        const result = await response.json();
        
        closeIngestModal();
        
        // Notify matching result status
        let statusMsg = "";
        if (result.status === "MERGED" || result.match_status === "MERGED") {
            statusMsg = `Successfully matched and merged patient record! Associated ID: ${result.patient_id}`;
            alert(statusMsg);
            if (result.patient_id) openPatientWorkspace(result.patient_id);
        } else if (result.status === "REVIEW_REQUIRED" || result.match_status === "REVIEW_REQUIRED") {
            statusMsg = "Record matched potential duplicates. Routed to 'Match Queue' for clinician manual review.";
            alert(statusMsg);
            if (currentUserRole === "doctor") {
                showSection("queue-section");
            } else {
                loadPatients();
            }
        } else if (result.status === "CREATED_NEW" || result.match_status === "CREATED_NEW") {
            statusMsg = `Created a new standalone Golden Record for patient. Associated ID: ${result.patient_id}`;
            alert(statusMsg);
            if (result.patient_id) openPatientWorkspace(result.patient_id);
        } else if (type === "csv") {
            statusMsg = `CSV ingestion pipeline complete.\nTotal Processed: ${result.processed_records}\nMerged: ${result.merged}\nCreated New: ${result.created_new}\nQueued Review: ${result.queued_review}`;
            alert(statusMsg);
            loadPatients();
        } else {
            alert("Document ingested successfully.");
            loadPatients();
        }
        
        updateQueueBadge();
        
    } catch (err) {
        console.error("Ingest error:", err);
        alert("Ingest error: " + err.message);
    } finally {
        submitBtn.innerText = "Upload & Process";
        submitBtn.disabled = false;
    }
}
