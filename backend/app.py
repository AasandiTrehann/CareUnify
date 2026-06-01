import os
import json
import uuid
import csv
import io
import shutil
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.config import UPLOAD_DIR, MATCH_AUTO_MERGE, MATCH_REVIEW_REQUIRED
from backend.database import get_db, sync_engine, Base
from backend.models import Patient, PatientLink, ClinicalResource, MatchQueue, AuditLog
import backend.fhir_helper as fhir_helper
import backend.matching_engine as matching_engine
import backend.ocr_speech_service as ocr_speech_service
import backend.rag_service as rag_service

app = FastAPI(title="CareUnify Clinical Integration Platform API", version="1.0.0")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup DB initializations
@app.on_event("startup")
async def on_startup():
    # Sync create tables (SQLite handles this fast)
    Base.metadata.create_all(bind=sync_engine)
    
    # Pre-index existing clinical resources into RAG Vector DB
    # We do this asynchronously using a temporary session
    from backend.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        # Load all clinical resources
        stmt = select(ClinicalResource).options(selectinload(ClinicalResource.patient))
        result = await db.execute(stmt)
        resources = result.scalars().all()
        
        for res in resources:
            try:
                payload = json.loads(res.fhir_payload)
                demographics = {
                    "first_name": res.patient.first_name,
                    "last_name": res.patient.last_name,
                    "dob": res.patient.dob,
                    "ssn": res.patient.ssn,
                    "phone": res.patient.phone,
                    "email": res.patient.email
                }
                
                # Retrieve text to index
                text_to_index = res.extracted_text or fhir_helper.create_clinical_summary_text(payload)
                
                # Index in RAG vector store
                metadata = {
                    "source_system": res.source_system,
                    "resource_type": res.resource_type,
                    "date": payload.get("effectiveDateTime") or payload.get("period", {}).get("start") or payload.get("authoredOn") or datetime.utcnow().strftime("%Y-%m-%d")
                }
                
                rag_service.index_clinical_resource(
                    resource_id=res.id,
                    patient_id=res.patient_id,
                    text=text_to_index,
                    metadata=metadata,
                    patient_demographics=demographics
                )
            except Exception as e:
                print(f"Error pre-indexing resource {res.id}: {e}")
                
        print(f"Pre-indexed {len(resources)} clinical resources into Vector DB.")


# HELPERS
async def process_incoming_patient_matching(db: AsyncSession, incoming_patient_dict: dict, source_system: str, source_patient_id: str = None) -> dict:
    """Core pipeline handler for parsing, matching, and committing patient records."""
    # Find matching candidates using phonetic blocking keys
    candidates = await matching_engine.search_duplicates_blocking(db, incoming_patient_dict)
    
    # 1. AUTO-MERGE: Check if we have a matching score >= threshold
    if candidates and candidates[0][1] >= MATCH_AUTO_MERGE:
        best_cand, score, features = candidates[0]
        
        # Merge incoming data using survivorship rules
        merged_patient = await matching_engine.execute_merge(
            db=db,
            golden_patient=best_cand,
            incoming_data=incoming_patient_dict,
            source_system=source_system,
            source_patient_id=source_patient_id
        )
        
        # Update FHIR resource text index
        patient_text = fhir_helper.create_clinical_summary_text(json.loads(merged_patient.fhir_payload))
        rag_service.index_clinical_resource(
            resource_id=merged_patient.id + "_demographics",
            patient_id=merged_patient.id,
            text=patient_text,
            metadata={"source_system": source_system, "resource_type": "Patient", "date": merged_patient.dob},
            patient_demographics=incoming_patient_dict
        )
        
        return {
            "status": "MERGED",
            "patient_id": merged_patient.id,
            "match_score": score,
            "matching_features": features,
            "first_name": merged_patient.first_name,
            "last_name": merged_patient.last_name
        }
        
    # 2. HUMAN-IN-THE-LOOP: Review needed for border-case scores
    elif candidates and candidates[0][1] >= MATCH_REVIEW_REQUIRED:
        best_cand, score, features = candidates[0]
        
        # Add entry to match queue
        queue_item = MatchQueue(
            candidate_patient_id=best_cand.id,
            incoming_record_payload=json.dumps(incoming_patient_dict),
            match_score=score,
            matching_features=json.dumps(features),
            status="PENDING"
        )
        db.add(queue_item)
        await db.flush()
        
        # Save a temporary record link as 'unverified' in audit logs
        audit = AuditLog(
            user_id="SYSTEM_INTEGRATION",
            action="QUEUE_MATCH_REVIEW",
            patient_id=best_cand.id,
            details=f"Incoming patient record from '{source_system}' flagged for duplication review. Match score: {score}."
        )
        db.add(audit)
        
        return {
            "status": "REVIEW_REQUIRED",
            "queue_id": queue_item.id,
            "candidate_id": best_cand.id,
            "match_score": score,
            "matching_features": features,
            "first_name": incoming_patient_dict.get("first_name"),
            "last_name": incoming_patient_dict.get("last_name")
        }
        
    # 3. NEW PATIENT: High uniqueness, create new Golden Record
    else:
        new_patient = Patient(
            first_name=incoming_patient_dict.get("first_name"),
            last_name=incoming_patient_dict.get("last_name"),
            dob=incoming_patient_dict.get("dob"),
            ssn=incoming_patient_dict.get("ssn"),
            gender=incoming_patient_dict.get("gender"),
            phone=incoming_patient_dict.get("phone"),
            email=incoming_patient_dict.get("email"),
            address=incoming_patient_dict.get("address")
        )
        # Create FHIR representation
        fhir_obj = fhir_helper.to_fhir_patient(incoming_patient_dict)
        new_patient.id = fhir_obj["id"]
        new_patient.fhir_payload = json.dumps(fhir_obj)
        db.add(new_patient)
        
        # Save lineage link
        link = PatientLink(
            golden_patient_id=new_patient.id,
            source_system=source_system,
            source_patient_id=source_patient_id,
            raw_payload=json.dumps(incoming_patient_dict)
        )
        db.add(link)
        
        # Index demographic data for RAG
        patient_text = fhir_helper.create_clinical_summary_text(fhir_obj)
        rag_service.index_clinical_resource(
            resource_id=new_patient.id + "_demographics",
            patient_id=new_patient.id,
            text=patient_text,
            metadata={"source_system": source_system, "resource_type": "Patient", "date": new_patient.dob},
            patient_demographics=incoming_patient_dict
        )
        
        # Log audit
        audit = AuditLog(
            user_id="SYSTEM_INTEGRATION",
            action="CREATE_PATIENT",
            patient_id=new_patient.id,
            details=f"Created new Golden Patient record from '{source_system}' ingestion."
        )
        db.add(audit)
        
        await db.flush()
        return {
            "status": "CREATED_NEW",
            "patient_id": new_patient.id,
            "match_score": 0.0,
            "first_name": new_patient.first_name,
            "last_name": new_patient.last_name
        }


# API ENDPOINTS

# 1. Ingestion: Patient Demographics Ingest (JSON / EHR standard)
@app.post("/api/v1/ingest/patient")
async def ingest_patient(payload: dict, db: AsyncSession = Depends(get_db)):
    source_system = payload.get("sourceSystem", "EHR_REST_API")
    source_patient_id = payload.get("sourcePatientId", str(uuid.uuid4()))
    
    # Flatten input FHIR/payload format
    extracted = {
        "first_name": payload.get("first_name") or payload.get("firstName") or "",
        "last_name": payload.get("last_name") or payload.get("lastName") or "",
        "dob": payload.get("dob") or payload.get("birthDate") or "",
        "ssn": payload.get("ssn") or "",
        "gender": payload.get("gender") or "unknown",
        "phone": payload.get("phone") or "",
        "email": payload.get("email") or "",
        "address": payload.get("address") or ""
    }
    
    # Process FHIR nested name lists if present
    if "name" in payload and isinstance(payload["name"], list) and len(payload["name"]) > 0:
        names = payload["name"][0]
        extracted["last_name"] = names.get("family", "")
        givens = names.get("given", [])
        if givens:
            extracted["first_name"] = givens[0]
            
    if "birthDate" in payload:
        extracted["dob"] = payload["birthDate"]
        
    if not extracted["first_name"] or not extracted["last_name"] or not extracted["dob"]:
        raise HTTPException(status_code=400, detail="Missing required demographic fields (first_name, last_name, dob)")
        
    res = await process_incoming_patient_matching(db, extracted, source_system, source_patient_id)
    return res


# 2. Ingestion: CSV Import Handler
@app.post("/api/v1/ingest/csv")
async def ingest_csv(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    contents = await file.read()
    decoded = contents.decode("utf-8")
    csv_reader = csv.DictReader(io.StringIO(decoded))
    
    records_processed = 0
    merged_count = 0
    new_count = 0
    queued_count = 0
    
    for row in csv_reader:
        # Check standard columns
        extracted = {
            "first_name": row.get("FirstName", "").strip(),
            "last_name": row.get("LastName", "").strip(),
            "dob": row.get("DOB", "").strip(),
            "ssn": row.get("SSN", "").strip(),
            "gender": row.get("Gender", "unknown").strip(),
            "phone": row.get("Phone", "").strip(),
            "email": row.get("Email", "").strip(),
            "address": row.get("Address", "").strip() or "Springfield, IL"
        }
        
        if not extracted["first_name"] or not extracted["last_name"] or not extracted["dob"]:
            continue # Skip invalid row
            
        # Match patient
        match_result = await process_incoming_patient_matching(db, extracted, "LAB_CSV_UPLOAD", row.get("PatientID"))
        
        # If merged or created new, attach lab observations
        patient_id = match_result.get("patient_id")
        
        if match_result["status"] == "MERGED":
            merged_count += 1
        elif match_result["status"] == "CREATED_NEW":
            new_count += 1
        elif match_result["status"] == "REVIEW_REQUIRED":
            queued_count += 1
            
        records_processed += 1
        
        # If patient was successfully resolved (merged or newly created), save the observation
        if patient_id and row.get("LabTest") and row.get("Result"):
            # Map to FHIR Observation
            obs_data = {
                "test_name": row.get("LabTest"),
                "result": row.get("Result"),
                "unit": row.get("Unit", ""),
                "date": row.get("Date") or datetime.utcnow().strftime("%Y-%m-%d")
            }
            obs_fhir = fhir_helper.to_fhir_observation(patient_id, obs_data)
            
            # Save clinical resource
            summary_txt = fhir_helper.create_clinical_summary_text(obs_fhir)
            clinical_res = ClinicalResource(
                patient_id=patient_id,
                resource_type="Observation",
                fhir_payload=json.dumps(obs_fhir),
                extracted_text=summary_txt,
                source_system="LAB_CSV_UPLOAD"
            )
            db.add(clinical_res)
            await db.flush()
            
            # Index in RAG Vector Store
            metadata = {
                "source_system": "LAB_CSV_UPLOAD",
                "resource_type": "Observation",
                "date": obs_data["date"]
            }
            rag_service.index_clinical_resource(
                resource_id=clinical_res.id,
                patient_id=patient_id,
                text=summary_txt,
                metadata=metadata,
                patient_demographics=extracted
            )
            
    return {
        "processed_records": records_processed,
        "merged": merged_count,
        "created_new": new_count,
        "queued_review": queued_count
    }


# 3. Ingestion: OCR Scan Upload PDF/Image
@app.post("/api/v1/ingest/ocr")
async def ingest_ocr(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    # Save raw file
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    saved_path = os.path.join(UPLOAD_DIR, file_id + ext)
    
    with open(saved_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
        
    # Process OCR
    extracted_text = ocr_speech_service.run_ocr_on_file(saved_path)
    
    # Parse demographics
    demographics = ocr_speech_service.parse_clinical_text(extracted_text)
    
    if not demographics["first_name"] or not demographics["last_name"]:
        # Set dummy/unresolved properties if parsing failed
        demographics["first_name"] = "Unknown"
        demographics["last_name"] = "Patient"
        demographics["dob"] = datetime.utcnow().strftime("%Y-%m-%d")
        
    # Match patient
    match_res = await process_incoming_patient_matching(db, demographics, "OCR_SCAN", file.filename)
    patient_id = match_res.get("patient_id")
    
    if patient_id:
        # Convert to FHIR DiagnosticReport
        report_data = {
            "title": f"OCR Scan: {file.filename}",
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "conclusion": "Scanned document text successfully extracted and indexed.",
            "raw_text": extracted_text
        }
        report_fhir = fhir_helper.to_fhir_diagnostic_report(patient_id, report_data)
        
        # Save clinical resource
        summary_txt = fhir_helper.create_clinical_summary_text(report_fhir)
        clinical_res = ClinicalResource(
            patient_id=patient_id,
            resource_type="DiagnosticReport",
            fhir_payload=json.dumps(report_fhir),
            extracted_text=summary_txt + f"\nDocument details: {extracted_text}",
            source_system="OCR_SCAN"
        )
        db.add(clinical_res)
        await db.flush()
        
        # Index in Vector DB
        rag_service.index_clinical_resource(
            resource_id=clinical_res.id,
            patient_id=patient_id,
            text=clinical_res.extracted_text,
            metadata={
                "source_system": "OCR_SCAN",
                "resource_type": "DiagnosticReport",
                "date": report_data["date"]
            },
            patient_demographics=demographics
        )
        
    return {
        "match_status": match_res["status"],
        "patient_id": patient_id,
        "parsed_demographics": demographics,
        "extracted_snippet": extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text
    }


# 4. Ingestion: Voice Dictation Audio Upload
@app.post("/api/v1/ingest/voice")
async def ingest_voice(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    # Save audio
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    saved_path = os.path.join(UPLOAD_DIR, file_id + ext)
    
    with open(saved_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
        
    # Process speech transcription
    transcript_text = ocr_speech_service.run_speech_to_text(saved_path)
    
    # Parse patient metadata from transcription
    demographics = ocr_speech_service.parse_clinical_text(transcript_text)
    
    if not demographics["first_name"] or not demographics["last_name"]:
        demographics["first_name"] = "Unknown"
        demographics["last_name"] = "Patient"
        demographics["dob"] = datetime.utcnow().strftime("%Y-%m-%d")
        
    # Match patient
    match_res = await process_incoming_patient_matching(db, demographics, "VOICE_DICTATION", file.filename)
    patient_id = match_res.get("patient_id")
    
    if patient_id:
        # Convert transcript into FHIR DiagnosticReport (or simple Observation)
        report_data = {
            "title": f"Voice Dictation: {file.filename}",
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "conclusion": "Physician dictation transcription successfully recorded.",
            "raw_text": transcript_text
        }
        report_fhir = fhir_helper.to_fhir_diagnostic_report(patient_id, report_data)
        
        # Save clinical resource
        summary_txt = fhir_helper.create_clinical_summary_text(report_fhir)
        clinical_res = ClinicalResource(
            patient_id=patient_id,
            resource_type="DiagnosticReport",
            fhir_payload=json.dumps(report_fhir),
            extracted_text=summary_txt + f"\nTranscription: {transcript_text}",
            source_system="VOICE_DICTATION"
        )
        db.add(clinical_res)
        await db.flush()
        
        # Index in Vector DB
        rag_service.index_clinical_resource(
            resource_id=clinical_res.id,
            patient_id=patient_id,
            text=clinical_res.extracted_text,
            metadata={
                "source_system": "VOICE_DICTATION",
                "resource_type": "DiagnosticReport",
                "date": report_data["date"]
            },
            patient_demographics=demographics
        )
        
    return {
        "match_status": match_res["status"],
        "patient_id": patient_id,
        "parsed_demographics": demographics,
        "transcript": transcript_text
    }


# 5. Patient: Retrieve paginated list
@app.get("/api/v1/patients")
async def get_patients(query: str = None, db: AsyncSession = Depends(get_db)):
    stmt = select(Patient)
    if query:
        stmt = stmt.where(
            Patient.first_name.like(f"%{query}%") |
            Patient.last_name.like(f"%{query}%") |
            Patient.dob.like(f"%{query}%") |
            Patient.ssn.like(f"%{query}%")
        )
    result = await db.execute(stmt)
    patients = result.scalars().all()
    
    return [
        {
            "id": p.id,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "dob": p.dob,
            "gender": p.gender,
            "phone": p.phone,
            "email": p.email,
            "address": p.address
        }
        for p in patients
    ]


# 6. Patient: Detail & Provenance links
@app.get("/api/v1/patients/{id}")
async def get_patient_detail(id: str, db: AsyncSession = Depends(get_db)):
    # Load patient and their source patient links
    stmt = select(Patient).where(Patient.id == id).options(selectinload(Patient.links))
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient Golden Record not found")
        
    # Log view in audit logs
    audit = AuditLog(
        user_id="CLINICIAN_USER",
        action="VIEW_PATIENT",
        patient_id=patient.id,
        details=f"Viewed unified Patient Golden Record and data lineage."
    )
    db.add(audit)
    
    links = [
        {
            "id": link.id,
            "source_system": link.source_system,
            "source_patient_id": link.source_patient_id,
            "raw_payload": json.loads(link.raw_payload) if link.raw_payload else {},
            "created_at": link.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for link in patient.links
    ]
    
    return {
        "id": patient.id,
        "first_name": patient.first_name,
        "last_name": patient.last_name,
        "dob": patient.dob,
        "gender": patient.gender,
        "phone": patient.phone,
        "email": patient.email,
        "address": patient.address,
        "fhir_payload": json.loads(patient.fhir_payload) if patient.fhir_payload else {},
        "lineage_links": links
    }


# 7. Patient: FHIR Clinical Timeline
@app.get("/api/v1/patients/{id}/timeline")
async def get_patient_timeline(id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(ClinicalResource).where(ClinicalResource.patient_id == id)
    result = await db.execute(stmt)
    resources = result.scalars().all()
    
    timeline = []
    for res in resources:
        payload = json.loads(res.fhir_payload)
        
        # Get date from payload based on resource type
        date = payload.get("effectiveDateTime") or payload.get("period", {}).get("start") or payload.get("authoredOn") or res.created_at.strftime("%Y-%m-%d")
        
        timeline.append({
            "id": res.id,
            "resource_type": res.resource_type,
            "date": date,
            "source_system": res.source_system,
            "summary_text": res.extracted_text or fhir_helper.create_clinical_summary_text(payload),
            "payload": payload
        })
        
    # Sort chronologically, descending
    timeline = sorted(timeline, key=lambda x: x["date"], reverse=True)
    return timeline


# 8. Patient: GDPR Right-to-Erasure (Deletion)
@app.delete("/api/v1/patients/{id}")
async def delete_patient(id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Patient).where(Patient.id == id)
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
        
    patient_name = f"{patient.first_name} {patient.last_name}"
    
    # Audit log entry before deleting patient references
    audit = AuditLog(
        user_id="CLINICIAN_USER",
        action="DELETE_PATIENT_GDPR",
        patient_id=None,
        details=f"GDPR deletion requested for patient '{patient_name}' (ID: {id}). Deleting all records, clinical logs, and vector database indexes."
    )
    db.add(audit)
    
    # Delete from RAG Vector DB
    rag_service.delete_patient_embeddings(id)
    
    # Delete database record (Cascade deletes related links, resources, and match entries)
    await db.delete(patient)
    await db.commit()
    
    return {"message": f"Patient '{patient_name}' record and all associated clinical histories purged in compliance with GDPR."}


# 9. Match Queue: List pending items
@app.get("/api/v1/match-queue")
async def get_match_queue(db: AsyncSession = Depends(get_db)):
    stmt = select(MatchQueue).where(MatchQueue.status == "PENDING").options(selectinload(MatchQueue.candidate_patient))
    result = await db.execute(stmt)
    entries = result.scalars().all()
    
    return [
        {
            "id": item.id,
            "candidate_id": item.candidate_patient_id,
            "candidate_name": f"{item.candidate_patient.first_name} {item.candidate_patient.last_name}",
            "candidate_dob": item.candidate_patient.dob,
            "candidate_phone": item.candidate_patient.phone,
            "candidate_email": item.candidate_patient.email,
            "candidate_address": item.candidate_patient.address,
            "incoming_payload": json.loads(item.incoming_record_payload),
            "match_score": item.match_score,
            "matching_features": json.loads(item.matching_features)
        }
        for item in entries
    ]


# 10. Match Queue: Action Resolution
@app.post("/api/v1/match-queue/{id}/resolve")
async def resolve_match(id: str, action: str = Form(...), db: AsyncSession = Depends(get_db)):
    stmt = select(MatchQueue).where(MatchQueue.id == id).options(selectinload(MatchQueue.candidate_patient))
    result = await db.execute(stmt)
    queue_item = result.scalar_one_or_none()
    
    if not queue_item:
        raise HTTPException(status_code=404, detail="Match Queue item not found")
        
    candidate = queue_item.candidate_patient
    incoming_data = json.loads(queue_item.incoming_record_payload)
    
    if action == "approve":
        # Execute merge using survivorship rules
        merged_patient = await matching_engine.execute_merge(
            db=db,
            golden_patient=candidate,
            incoming_data=incoming_data,
            source_system="MANUAL_MERGE_HITL",
            source_patient_id=None
        )
        
        # Update queue status
        queue_item.status = "APPROVED_MERGE"
        
        # Update demographics RAG index
        patient_text = fhir_helper.create_clinical_summary_text(json.loads(merged_patient.fhir_payload))
        rag_service.index_clinical_resource(
            resource_id=merged_patient.id + "_demographics",
            patient_id=merged_patient.id,
            text=patient_text,
            metadata={"source_system": "MANUAL_MERGE_HITL", "resource_type": "Patient", "date": merged_patient.dob},
            patient_demographics=incoming_data
        )
        
        # Audit log resolution
        audit = AuditLog(
            user_id="CLINICIAN_USER",
            action="RESOLVE_MERGE_APPROVE",
            patient_id=candidate.id,
            details=f"Clinician manually approved merging duplicate records for {candidate.first_name} {candidate.last_name}."
        )
        db.add(audit)
        
        await db.commit()
        return {"status": "SUCCESS", "message": "Records merged successfully.", "patient_id": candidate.id}
        
    elif action == "reject":
        # Reject merge, create a new separate patient profile
        new_patient = Patient(
            first_name=incoming_data.get("first_name"),
            last_name=incoming_data.get("last_name"),
            dob=incoming_data.get("dob"),
            ssn=incoming_data.get("ssn"),
            gender=incoming_data.get("gender"),
            phone=incoming_data.get("phone"),
            email=incoming_data.get("email"),
            address=incoming_data.get("address")
        )
        # Create FHIR Patient object
        fhir_obj = fhir_helper.to_fhir_patient(incoming_data)
        new_patient.id = fhir_obj["id"]
        new_patient.fhir_payload = json.dumps(fhir_obj)
        db.add(new_patient)
        
        # Set queue status
        queue_item.status = "REJECTED_NEW_PATIENT"
        
        # Add source link
        link = PatientLink(
            golden_patient_id=new_patient.id,
            source_system="MANUAL_MERGE_HITL",
            raw_payload=queue_item.incoming_record_payload
        )
        db.add(link)
        
        # Index demographic data for RAG
        patient_text = fhir_helper.create_clinical_summary_text(fhir_obj)
        rag_service.index_clinical_resource(
            resource_id=new_patient.id + "_demographics",
            patient_id=new_patient.id,
            text=patient_text,
            metadata={"source_system": "MANUAL_MERGE_HITL", "resource_type": "Patient", "date": new_patient.dob},
            patient_demographics=incoming_data
        )
        
        # Audit log rejection
        audit = AuditLog(
            user_id="CLINICIAN_USER",
            action="RESOLVE_MERGE_REJECT",
            patient_id=new_patient.id,
            details=f"Clinician rejected record match. Created new standalone Patient record (ID: {new_patient.id}) for {new_patient.first_name} {new_patient.last_name}."
        )
        db.add(audit)
        
        await db.commit()
        return {"status": "SUCCESS", "message": "Match rejected. Created new Patient Record.", "patient_id": new_patient.id}
        
    else:
        raise HTTPException(status_code=400, detail="Invalid resolution action. Use 'approve' or 'reject'.")


# 11. RAG Query
@app.post("/api/v1/query")
async def clinical_query(payload: dict, db: AsyncSession = Depends(get_db)):
    patient_id = payload.get("patient_id")
    query = payload.get("query")
    
    if not patient_id or not query:
        raise HTTPException(status_code=400, detail="Missing fields 'patient_id' and 'query'")
        
    # Get patient details to de-identify data
    stmt = select(Patient).where(Patient.id == patient_id)
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient Golden Record not found")
        
    demographics = {
        "first_name": patient.first_name,
        "last_name": patient.last_name,
        "dob": patient.dob,
        "ssn": patient.ssn,
        "phone": patient.phone,
        "email": patient.email
    }
    
    # Run the RAG pipeline
    rag_result = rag_service.run_clinical_query(patient_id, query, demographics)
    
    # Log in immutable HIPAA audit logs
    audit = AuditLog(
        user_id="CLINICIAN_USER",
        action="LLM_RAG_QUERY",
        patient_id=patient_id,
        details=f"Clinician executed Natural Language query: '{query}'. Context retrieved and synthesized."
    )
    db.add(audit)
    await db.flush()
    
    return {
        "patient_id": patient_id,
        "query": query,
        "answer": rag_result["summary"],
        "sources": rag_result["sources"],
        "is_fallback": rag_result["is_fallback"]
    }


# 12. Audit Log API
@app.get("/api/v1/audit")
async def get_audit_logs(db: AsyncSession = Depends(get_db)):
    stmt = select(AuditLog).order_by(AuditLog.timestamp.desc())
    result = await db.execute(stmt)
    logs = result.scalars().all()
    
    return [
        {
            "id": item.id,
            "user_id": item.user_id,
            "action": item.action,
            "patient_id": item.patient_id,
            "details": item.details,
            "timestamp": item.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
        for item in logs
    ]
