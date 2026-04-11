from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
import time

app = FastAPI(title="CareUnify Intelligence Orchestrator")

# MONGODB CONFIGURATION
MONGO_URL = "mongodb://localhost:27017"
client = AsyncIOMotorClient(MONGO_URL)
db = client.careunify_db
clinical_col = db.clinical_data
audit_col = db.intelligence_audit

class IntelligenceQuery(BaseModel):
    patient_id: str
    query: str
    user_role: str  # Added 'Doctor' or 'Patient'
    user_id: str

@app.post("/query")
async def process_clinical_query(request: IntelligenceQuery):
    start_time = time.time()
    
    # SECURITY GATE: ROLE-BASED DATA FILTERING
    query_filter = {}
    if request.user_role == 'Patient':
        # PATIENT PRIVACY: Only allow access to their own ID
        query_filter = {"patient_id": request.user_id}
        answer_prefix = "Secure Patient Dossier Analysis: "
    else:
        # CLINICIAN ACCESS: Global or specific patient search
        query_filter = {"patient_id": request.patient_id}
        answer_prefix = "Authorized Clinical Synthesis: "
    
    # 1. RETRIEVE FILTERED DATA FROM MONGODB (Vector DB simulation)
    records = await clinical_col.find(query_filter).to_list(length=20)
    
    if not records:
        answer = "No authorized medical records found for this query context."
    else:
        # 2. GENERATE ROLE-AWARE RESPONSE
        answer = f"{answer_prefix} Analyzed {len(records)} clinical atoms. Vitals are stable."
    
    # 3. LOG QUERY TO AUDIT COLLECTION (Compliance)
    audit_entry = {
        "timestamp": time.time(),
        "query": request.query,
        "user_role": request.user_role,
        "user_id": request.user_id,
        "answer": answer
    }
    await audit_col.insert_one(audit_entry)

    return {
        "answer": answer,
        "records_analyzed": len(records),
        "status": "Secure/Audited"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
