# CareUnify Interview & Manual Build Guide

Welcome to the **CareUnify Comprehensive Interview and Technical Build Guide**. This document is structured to serve as an in-depth reference sheet. It explains the core problems, system architecture, feature highlights, and a step-by-step blueprint on how to manually construct this entire platform from scratch.

---

## Part 1: Project Overview & Interview Pitch

### The Core Problem Statement
Modern healthcare suffers from extreme data fragmentation. When patients visit different clinics, hospitals, laboratories, or specialist centers, their records are created independently. On average, a single patient has **4.7 separate records** scattered across disconnected systems.
* **Clinical Risks**: Critical medication errors, missing drug-to-drug interactions, diagnostic delays, and duplicate laboratory test orders.
* **Financial Burden**: Multi-billion dollar administrative overhead spent manually reconciling profiles and repeating diagnostics.
* **Compliance Issues**: Storing multiple duplicate files containing Protected Health Information (PHI) makes HIPAA audits, GDPR "Right-to-Erasure," and traceability extremely difficult.

### The CareUnify Solution Pitch
CareUnify is an AI-powered Clinical Data Integration platform that ingests multi-modal data streams and resolves patient duplicates to compile a single, unified profile called the **"Golden Record"**. 

The system standardizes all medical records into standard **FHIR R4 models**, deploys a multi-stage **Entity Resolution matching pipeline** (phonetic blocking + fuzzy string weights + Human-in-the-loop validation), indexes clinical events in a secure **RAG vector store**, and exposes an **AI-powered clinical workspace** with dynamic trend charts and a conversational assistant to query patient histories.

---

## Part 2: Platform Architecture Diagram

```
                 [ INGESTION CHANNELS ]
  EHR (JSON)  |  Labs (CSV)  |  Scanned PDF (OCR)  |  Audio (Whisper)
                           │
                           ▼
              [ FHIR R4 STANDARDIZATION ]
       maps payload to Patient, Observation, etc.
                           │
                           ▼
            [ MULTI-STAGE RECORD MATCHING ]
 ┌─────────────────────────────────────────────────────┐
 │ 1. BLOCKING: Generate phonetic keys (Soundex/NYSIIS)│
 │ 2. FEATURING: Extract Name, DOB, SSN, Contact sim   │
 │ 3. DECISION: Classifier Probability Score (P)       │
 └─────────────────────────┬───────────────────────────┘
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
          P >= 0.85   0.60<=P<0.85    P < 0.60
          [Merge]      [HITL Queue]   [New Patient]
             │             │             │
             └─────────────┼─────────────┘
                           ▼
             [ DATA SURVIVORSHIP MERGE ]
            Updates Golden Record in DB
                           │
          ┌────────────────┴────────────────┐
          ▼                                 ▼
   [ SQLite / Postgres ]           [ DE-IDENTIFICATION ]
 Demographics, Provenance Links,     Scrubs PHI Name/SSN
 FHIR payloads, HIPAA audit logs            │
                                            ▼
                                   [ VECTOR DB INDEX ]
                                    FAISS Embeddings
                                            │
                                            ▼
                                   [ CLINICAL RAG CHAT ]
                                    Ollama / Llama 3
```

---

## Part 3: Core Features Explained (Under the Hood)

### 1. Multi-Modal Ingestion & Processing
* **EHR API (JSON)**: Directly parses JSON payloads mapping to demographics.
* **Lab Panels (CSV)**: Reads tabular files, extracts demographic headers for patient matching, and transforms row values into FHIR R4 `Observation` records.
* **Document Scan (Tesseract OCR)**: Extracts text from scanned PDFs or images. A regular expression semantic engine parses names, DOBs, and SSNs from unstructured text, converting documents into FHIR `DiagnosticReport` objects.
* **Physician Voice (Whisper transcription)**: Transcribes dictations into clinical logs. Parsers search for demographics to match, saving text in the timeline.

### 2. Multi-Stage Entity Resolution Engine
Instead of comparing every new record with all database records ($O(N^2)$ time complexity), the engine runs a multi-tier matching strategy:
1. **Phonetic Blocking**: Computes **Soundex** and **NYSIIS** codes for the patient's last name, combined with first initial and DOB birth year (e.g. `D200_J_1980`). It queries only database records sharing this blocking key.
2. **Feature Engineering**: Calculates Jaro-Winkler string similarity for First Name and Last Name (allowing swaps), Levenshtein distances for DOB, phone numbers, emails, addresses, and exact matches for SSN.
3. **Probabilistic Scoring**: Operates a weighted feature algorithm to output a match score $P \in [0.0, 1.0]$.
4. **Survivorship Rules**: When merging, the system chooses the most complete demographic values (e.g., formal first name "Jonathan" instead of "Jon", or the longer mobile number).

### 3. Human-in-the-Loop (HITL) Merge Queue
If matching probability is between `0.60` and `0.85`, the system suspends auto-merge. It places the entry in a review queue. Doctors see side-by-side demographic comparisons with highlighted field differences. They manually click **Approve** (executes data survivorship merge) or **Reject** (forces creation of a new patient).

### 4. Conversational Clinical RAG (Retrieval-Augmented Generation)
* **HIPAA De-identification**: Before clinical text is indexed or queried, a scrubbing filter replaces patient names, SSNs, phone numbers, and emails with placeholders (like `[REDACTED_SSN]`) to protect patient privacy.
* **Context Retrieval**: Generates text embeddings using `SentenceTransformers` and executes a local FAISS-based vector cosine similarity search to retrieve the patient's medical history.
* **Synthesis**: Feeds de-identified context and query to Llama 3 via a local **Ollama** API to compile Cited Clinical summaries.
* **Resilient Fallback**: If the local Ollama instance is offline, the service falls back to a custom Python keyword-context compiler, ensuring the UI remains active and informative.

### 5. Role-Based Access Control (RBAC) Views
* **Doctor**: Accesses the full directory, full timeline, RAG clinical AI search, statistics analytics charts, manual review match queues, and immutable HIPAA audits.
* **Lab Assistant**: Can view the directory list and upload lab CSVs/notes, but cannot query RAG or access merge queues.
* **Patient**: Directs immediately to their own portal. They can view their timeline and query their own files via the RAG chat, but have no access to the directory, audits, or ingestion overlays.

### 6. Interactive Health Statistics Charts
Doctors can switch to the **Clinical Stats** tab in the patient's workspace. Integrated with **Chart.js**, this dynamically parses chronological values from FHIR `Observation` payload streams to render live trend line/bar charts for Blood Pressure (systolic vs. diastolic), Cholesterol Panels (Total, LDL, HDL), and HbA1c.

---

## Part 4: Step-by-Step Manual Build Guide

If you wanted to manually construct this entire platform from absolute scratch, follow this engineering roadmap:

### Phase 1: Database Modeling & Schema
1. **Set up the Database**: Choose a relational database (SQLite for local development, PostgreSQL for production).
2. **Define Schema Tables**:
   * `patients`: Stores demographics and the consolidated `fhir_payload` (JSON string).
   - `patient_links`: Keeps track of record lineage (provenance mapping of source patient IDs to the Golden Patient ID).
   * `clinical_resources`: Stores FHIR resources (Observations, MedicationRequests) mapped to `patient_id`.
   - `match_queue`: Stores duplicates awaiting clinician review (match scores, payloads, status).
   * `audit_logs`: An immutable log table storing actions, usernames, and timestamps.
3. **Initialize Database Sessions**: Write database helpers using SQLAlchemy to manage transactions.

### Phase 2: Ingestion & Parsing Services
1. **Phonetic Helper**: Implement `Soundex` and `NYSIIS` algorithms in Python. Use them to write a function that returns a deduplicating "blocking key" for each record.
2. **FHIR R4 Map Helper**: Write a mapping utility that converts dictionaries into structured FHIR R4 schema JSON objects (e.g. creating `Patient` structures or `Observation` categories with LOINC codes).
3. **OCR Document Reader**: Write a PDF file reader wrapper. Integrate `pytesseract` or a standard binary scanner. Write regular expressions to search text for Names, DOBs, and SSNs.
4. **Audio Transcriber**: Set up a helper utilizing `whisper` to read audio files and return transcript text, falling back to reading companion text files if necessary.

### Phase 3: The Entity Resolution Pipeline
1. **Fuzzy String Metrics**: Write helpers computing Jaro-Winkler similarity (for names and strings) and Levenshtein distance (for DOBs and numbers).
2. **Calculate Match Scores**: Combine metrics using weighting formulas. SSN matches should provide massive boosts, while SSN mismatches should trigger severe penalties.
3. **Survivorship Logic**: Create a function that merges two dictionaries. Iterate over keys and retain the longest, most complete values.
4. **Merge Function**: Write database operations to:
   * Update demographics on the target Golden Record.
   - Insert new `PatientLink` records mapping the source.
   * Re-link clinical resources from the old ID to the new merged ID.

### Phase 4: Setting up the FastAPI Web Server
1. **Initialize API**: Create a FastAPI app instance and add CORS middleware.
2. **Implement API Routers**:
   * `POST /api/v1/ingest/patient`: Demographics entry endpoint. Runs the matching engine.
   - `POST /api/v1/ingest/csv`: Parses CSV uploads, loops rows, matches profiles, and saves observations.
   * `POST /api/v1/ingest/ocr` / `ingest/voice`: Handles multi-part file uploads, triggers parsers, matches patient, and saves diagnostic reports.
   - `GET /api/v1/patients`: Directory fetcher (with query filters).
   * `GET /api/v1/match-queue` & `POST /api/v1/match-queue/{id}/resolve`: Queue endpoints.
   - `GET /api/v1/audit`: Returns audit trails.

### Phase 5: Building RAG & Vector Stores
1. **De-identification**: Write a text parser that takes patient demographics and replaces all matching name substrings in the text with `[PATIENT_FIRST_NAME]`, etc.
2. **Vector Index**: Maintain a vector list. Generate text vectors using a transformer library (like sentence-transformers `all-MiniLM-L6-v2`).
3. **Similarity Search**: Calculate cosine similarity between the query embedding and the stored embeddings. Retrieve the top 3 highest scoring contexts.
4. **LLM Connection**: Send a system prompt containing the context, query, and citation instructions to Ollama via HTTP request. Write a regex-based fallback summary text generator if Ollama is unreachable.

### Phase 6: Designing the SPA User Interface
1. **Construct the HTML**: Create a dual-page layout (`index.html` as landing, `portal.html` as the SPA). Design the login panel overlay, the side navigation layout, the grids for directory records, and detail workspace panes.
2. **Write vanilla CSS**: Utilize a dark-mode palette. Apply `backdrop-filter: blur()` for glassmorphism panels. Write animations for modal fade-ins and sliding panels.
3. **Write JS Client**:
   * Add active sections router (`showSection(id)`).
   - Implement `handleLogin(role)` managing sessions and `applyRolePermissions()` hiding sidebar options.
   * Connect input events to FastAPI REST routes using `fetch`.
   - Add tab-switching in the patient file (`switchWorkspaceTab`).
   * Group observations, sort chronologically, and render graphs using **Chart.js** (`new Chart(ctx, {type: 'line', ...})`).

---

## Part 5: Potential Interview Questions & Answers

### Q1: How does your patient matching engine handle typos or naming variations?
**Answer**: We use a multi-tiered matching engine. First, we use **phonetic blocking (Soundex & NYSIIS)** on the patient's last name. This filters out spelling variations (e.g. "Smith" and "Smyth" group under the same code). Next, we run fuzzy string metrics—specifically **Jaro-Winkler** for names (which matches character transpositions and common prefix matching) and **Levenshtein** for dates and numbers. Finally, a weighted ruleset calculates the probability score to determine whether it merges automatically or routes to the clinician matching queue.

### Q2: What security measures ensure this platform is HIPAA compliant?
**Answer**: HIPAA requires the protection of Protected Health Information (PHI). We address this by:
1. **PHI De-identification**: Clinical logs are scrubbed of sensitive identifiers (names, SSNs, phone numbers) *before* being indexed in the vector store or transmitted to the LLM.
2. **Immutable Audit Logs**: Every clinical view, RAG query, database merge, or deletion is logged in an audit table with clinician credentials, action, and timestamps.
3. **Role-Based Access**: Restricting views so Patients only see their own files, Lab assistants can only ingest data, and Doctors can manage matches and audit records.

### Q3: How do you prevent the record comparisons from scaling out of control as the patient list grows?
**Answer**: If we compared every new patient record against all existing database records, the time complexity would be $O(N^2)$, which is extremely inefficient. We solve this by using **Blocking Keys**. By grouping patient records into local buckets using last name Soundex + first initial + birth year, we restrict fuzzy similarity scoring to a tiny subset of matching candidates, keeping the lookup running in near $O(1)$ constant time.

### Q4: How is data merged when a duplicate is confirmed? (Survivorship Rules)
**Answer**: We apply **demographic survivorship rules**. When record A merges with B, the engine preserves the most complete information: we keep the longest name string (e.g., "Jonathan" instead of "Jon"), the most complete phone number, and non-null values. Additionally, we append a link in `patient_links` to record the data lineage (provenance), showing that the record came from multiple separate systems originally.
