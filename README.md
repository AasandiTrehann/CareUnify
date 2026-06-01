# CareUnify - AI-Powered Clinical Data Integration Platform

CareUnify is an AI-powered Clinical Data Integration platform designed to resolve the clinical risk and administrative burden of fragmented patient records. The platform ingests multi-modal data streams, resolves patient duplicates using an advanced Entity Resolution pipeline, standardizes data into the industry-standard FHIR R4 schema, maintains a single source of truth called the **"Golden Record"**, and exposes a HIPAA-compliant workspace with interactive stats charts and a Conversational RAG assistant to query patient histories.

---

## 🚀 Key Features

* **Multi-Modal Data Ingestion**: Supports ingestion of structured EHR JSON payloads, tabular laboratory CSV panels, scanned medical PDFs (using OCR text parsing), and physician dictation audio recordings (using Whisper speech transcription).
* **AI Entity Resolution Matching Engine**:
  * Phonetic blocking partitions (using **Soundex** and **NYSIIS** algorithms) to optimize search scaling from $O(N^2)$ to near $O(1)$.
  * Fuzzy demographic matching (Jaro-Winkler string similarity for FirstName/LastName swaps, Levenshtein distances for DOBs/addresses).
  * Probabilistic scoring weighted classifier determining automatic merge thresholds vs. review queues.
* **Human-in-the-Loop (HITL) Queue**: A review terminal for border-case matches ($0.60 \le P < 0.85$), showing side-by-side field comparisons for clinician approval.
* **HL7 & FHIR Standard Compliance**:
  * An active **TCP MLLP (Minimal Lower Layer Protocol) listener** on port 2575 to receive live HL7 streams.
  * Formulates validated **FHIR R4 JSON models** (Patient, Observation, Encounter, MedicationRequest, and DiagnosticReport).
* **Role-Based Access Control (RBAC)**: Separated client portal overlays adjusting workspace displays for **Doctors**, **Lab Assistants**, and **Patients**.
* **Clinical Statistics Visualizer**: Dynamically extracts observation telemetry from the FHIR timeline and plots chronological trend curves using **Chart.js** (Blood Pressure, Cholesterol Panels, and HbA1c).
* **Conversational Clinical RAG**: 
  * Automatically **de-identifies/redacts PHI** identifiers (SSN, name, phone, email) to protect patient privacy before vector indexing.
  * Generates local FAISS vector index embeddings to fetch context.
  * Synthesizes clinical reports using **Llama 3 (via Ollama)**, falling back to a custom keyword scraper if offline.
* **HIPAA Compliance Auditing**: Maintains persistent, immutable logs tracking accesses, queries, and merges.

---

## 📂 Project Structure

```
CareUnify/
├── backend/
│   ├── app.py                # FastAPI endpoint controllers, routers, and CORS middleware
│   ├── config.py             # System paths, variables, and matching thresholds
│   ├── database.py           # Async engine session factories and dependencies
│   ├── fhir_helper.py        # FHIR R4 schema transformers, validation, and clinical descriptions
│   ├── hl7_listener.py       # TCP MLLP socket listener parsing live HL7 v2 messages
│   ├── matching_engine.py    # Record matching fuzzy similarities and survivorship rules
│   ├── models.py             # SQLAlchemy models (Patients, Links, ClinicalResources, HITL queue)
│   ├── ocr_speech_service.py # OCR parsing (Tesseract fallback) and Whisper transcripts loading
│   ├── phonetic_helper.py    # Pure Python Soundex & NYSIIS phonetic blocking calculators
│   ├── rag_service.py        # HIPAA de-identification scrubber, vector DB search, and Ollama client
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── app.js                # Frontend client state manager, session controller, and charts
│   ├── index.html            # Premium marketing product landing page
│   ├── portal.html           # Clinician & Patient workspace SPA dashboard structure
│   └── styles.css            # Premium dark-mode styling (glassmorphism cards, timelines, chat, login, landing)
├── mock_data/
│   ├── ehr_record_1.json     # Primary John Doe EHR patient profile
│   ├── ehr_record_2.json     # Duplicate Jon Doe EHR profile (typo in DOB and phone)
│   ├── generate_mock_data.py # Script generating testing data (JSONs, lab CSV, PDF scan, WAV audio)
│   └── ...
├── backend_test.py           # Automated integration verification test suite
├── send_hl7_test.py          # Testing utility to transmit raw HL7 messages over MLLP socket
└── README.md                 # Project documentation
```

---

## 🛠️ Quick Start Guide

### Step 1: Install Dependencies
Make sure you have python and pip installed. In your terminal, run:
```powershell
pip install -r backend/requirements.txt
```

### Step 2: Start the FastAPI Backend
Start the uvicorn development server:
```powershell
uvicorn backend.app:app --reload --port 8000
```
This boots the API on `http://localhost:8000`. You can inspect the interactive OpenAPI documentation at `http://localhost:8000/docs`.

### Step 3: Run the HL7 MLLP TCP Listener (Optional)
Open a separate terminal window and start the socket listener:
```powershell
python backend/hl7_listener.py
```
This starts listening on port `2575` for incoming HL7 streams.

### Step 4: Dispatch a Test HL7 Stream Message (Optional)
In a third terminal window, send a test HL7 message using our sender utility:
```powershell
python send_hl7_test.py
```

### Step 5: Open the Workspace Portal
1. Double-click `frontend/index.html` in your web browser. This loads the product marketing landing page.
2. Click **Launch Portal** or **Enter Workspace Portal** in the hero section to be redirected to `frontend/portal.html`.
3. Log in using Doctor, Lab, or Patient roles to verify the dashboards and charts.

---

## 🧪 Integration Testing
Run the automated test suite to verify table initialization, phonetic blocking calculations, fuzzy similarity features scoring, merge pipelines, context retrieval, and RAG fallbacks:
```powershell
python backend_test.py
```
All tests should output `ALL TESTS PASSED!`.
