import asyncio
import os
import json
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

# Mock configuration overrides before importing app dependencies
os.environ["OLLAMA_MODEL"] = "llama3"

from backend.database import AsyncSessionLocal, sync_engine, Base
from backend.models import Patient, PatientLink, ClinicalResource, MatchQueue, AuditLog
from backend.app import process_incoming_patient_matching
import backend.matching_engine as matching_engine
import backend.fhir_helper as fhir_helper
import backend.rag_service as rag_service

async def run_tests():
    print("=== Starting Integration Test Suite for CareUnify ===")
    
    # 1. Initialize Tables
    Base.metadata.drop_all(bind=sync_engine)
    Base.metadata.create_all(bind=sync_engine)
    print("Database tables re-created successfully.")
    
    async with AsyncSessionLocal() as db:
        # Load Mock Data
        with open("c:/Users/Aasandi/OneDrive/Desktop/CareUnify/mock_data/ehr_record_1.json", "r") as f:
            ehr1 = json.load(f)
        with open("c:/Users/Aasandi/OneDrive/Desktop/CareUnify/mock_data/ehr_record_2.json", "r") as f:
            ehr2 = json.load(f)
            
        print("Mock files loaded.")
        
        # 2. Ingest Primary Patient: John Doe
        p1_flat = {
            "first_name": ehr1["name"][0]["given"][0],
            "last_name": ehr1["name"][0]["family"],
            "dob": ehr1["birthDate"],
            "ssn": ehr1["identifier"][0]["value"],
            "gender": ehr1["gender"],
            "phone": ehr1["telecom"][0]["value"],
            "email": ehr1["telecom"][1]["value"],
            "address": ehr1["address"][0]["line"][0]
        }
        
        res1 = await process_incoming_patient_matching(db, p1_flat, "EHR_SYSTEM_A", "P-101")
        assert res1["status"] == "CREATED_NEW", f"Expected CREATED_NEW, got {res1['status']}"
        p1_id = res1["patient_id"]
        print(f"John Doe ingested successfully. Created Golden Patient ID: {p1_id}")
        
        # 3. Ingest Duplicate Candidate: Jon Doe
        p2_flat = {
            "first_name": ehr2["name"][0]["given"][0],
            "last_name": ehr2["name"][0]["family"],
            "dob": ehr2["birthDate"],
            "ssn": "", # Missing SSN
            "gender": ehr2["gender"],
            "phone": ehr2["telecom"][0]["value"],
            "email": ehr2["telecom"][1]["value"],
            "address": ehr2["address"][0]["line"][0]
        }
        
        res2 = await process_incoming_patient_matching(db, p2_flat, "CLINIC_SYSTEM_B", "P-202")
        assert res2["status"] == "REVIEW_REQUIRED", f"Expected REVIEW_REQUIRED, got {res2['status']}"
        queue_id = res2["queue_id"]
        print(f"Jon Doe duplicate candidate flagged successfully. Sent to Match Queue ID: {queue_id}")
        
        # 4. Resolve Match from Queue (Approve Merge)
        stmt = select(MatchQueue).where(MatchQueue.id == queue_id).options(selectinload(MatchQueue.candidate_patient))
        result = await db.execute(stmt)
        queue_item = result.scalar_one_or_none()
        
        assert queue_item is not None, "Match queue item should exist."
        
        incoming_data = json.loads(queue_item.incoming_record_payload)
        candidate = queue_item.candidate_patient
        
        # Merge candidate
        merged_patient = await matching_engine.execute_merge(
            db=db,
            golden_patient=candidate,
            incoming_data=incoming_data,
            source_system="MANUAL_MERGE_HITL"
        )
        
        # Check that survivorship rules were executed (phone took the longer, etc.)
        assert merged_patient.first_name == "John", f"Expected first_name 'John', got '{merged_patient.first_name}'"
        assert merged_patient.phone == "555-0199", f"Expected phone '555-0199' (survived longer mobile), got '{merged_patient.phone}'"
        
        # Index unified demographics in Vector DB
        demographics = {
            "first_name": merged_patient.first_name,
            "last_name": merged_patient.last_name,
            "dob": merged_patient.dob,
            "ssn": merged_patient.ssn,
            "phone": merged_patient.phone,
            "email": merged_patient.email
        }
        patient_text = fhir_helper.create_clinical_summary_text(json.loads(merged_patient.fhir_payload))
        rag_service.index_clinical_resource(
            resource_id=merged_patient.id + "_demographics",
            patient_id=merged_patient.id,
            text=patient_text,
            metadata={"source_system": "TEST_SUITE", "resource_type": "Patient", "date": merged_patient.dob},
            patient_demographics=demographics
        )
        print("Duplicate record manual merge approved. Demographic survivorship validated.")
        
        # 5. Ingest and Attach Observation Resource
        obs_payload = {
            "test_name": "Cholesterol",
            "result": "210",
            "unit": "mg/dL",
            "date": "2026-01-15"
        }
        obs_fhir = fhir_helper.to_fhir_observation(merged_patient.id, obs_payload)
        summary_txt = fhir_helper.create_clinical_summary_text(obs_fhir)
        
        clinical_res = ClinicalResource(
            patient_id=merged_patient.id,
            resource_type="Observation",
            fhir_payload=json.dumps(obs_fhir),
            extracted_text=summary_txt,
            source_system="LAB_TEST"
        )
        db.add(clinical_res)
        await db.flush()
        
        # Index in Vector store
        rag_service.index_clinical_resource(
            resource_id=clinical_res.id,
            patient_id=merged_patient.id,
            text=summary_txt,
            metadata={"source_system": "LAB_TEST", "resource_type": "Observation", "date": obs_payload["date"]},
            patient_demographics=demographics
        )
        print("FHIR Observation generated and indexed in RAG Vector DB.")
        
        # 6. Test RAG Context Retrieval & Query
        # Retrieve context
        contexts = rag_service.retrieve_relevant_contexts(merged_patient.id, "Find cholesterol readings")
        assert len(contexts) > 0, "Should retrieve at least one context."
        assert "210" in contexts[0]["text"], "Should contain lab reading value."
        print(f"RAG Context Retrieval passed: {contexts[0]['text']}")
        
        # Test Query Fallback (Ollama is likely offline in test script)
        ans = rag_service.run_clinical_query(merged_patient.id, "What is their cholesterol level?", demographics)
        assert "210" in ans["summary"], "Synthesized answer should mention the reading."
        print(f"RAG synthesized query answer: {ans['summary']}")
        
        # 7. Test HIPAA Audit trail insertion
        stmt_audit = select(AuditLog).where(AuditLog.patient_id == merged_patient.id)
        res_audit = await db.execute(stmt_audit)
        audits = res_audit.scalars().all()
        assert len(audits) > 0, "Audit trail entries should be generated."
        print(f"Validated HIPAA Auditing. Generated {len(audits)} audit entries.")
        
        # Commit all test transformations
        await db.commit()

    print("\n=== Integration Test Suite Completed: ALL TESTS PASSED! ===")

if __name__ == "__main__":
    asyncio.run(run_tests())
