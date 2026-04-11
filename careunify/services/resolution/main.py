from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
import time

app = FastAPI(title="CareUnify Resolution Service")

# MONGODB CONFIGURATION
MONGO_URL = "mongodb://localhost:27017"
client = AsyncIOMotorClient(MONGO_URL)
db = client.careunify_db
mpi_collection = db.master_patient_index
audit_collection = db.audit_logs

@app.get("/analytics/global")
async def get_global_analytics():
    """
    Feeds the new Doctor Dashboard Charts with Golden Record Stats.
    """
    total_records = await db.clinical_data.count_documents({})
    golden_records = await mpi_collection.count_documents({"status": "CERTIFIED"})
    precision_rate = 0.984 # Simulated from model validation
    
    return {
        "total_atoms": total_records,
        "certified_golden": golden_records,
        "fragmented_sources": total_records - golden_records,
        "precision": precision_rate
    }

@app.post("/request-duplicate-review")
async def flag_duplicate_document(file_id_1: str, file_id_2: str, reason: str):
    """
    Flag two potentially duplicate files for Doctor Review.
    """
    conflict = {
        "type": "DOCUMENT_DUPLICATE",
        "ids": [file_id_1, file_id_2],
        "reason": reason,
        "timestamp": time.time(),
        "status": "PENDING_DOCTOR"
    }
    await db.conflicts.insert_one(conflict)
    return {"status": "flagged", "msg": "Conflict sent to Doctor Dashboard"}

@app.post("/approve-merge")
async def approve_merge(approval: MergeApproval):
    """
    Stage 2: Commit a Golden Record and Audit Log to MongoDB.
    """
    try:
        # 1. Create Audit Log
        audit_entry = {
            "timestamp": time.time(),
            "event": "IDENTITY_MERGE",
            "reviewer": approval.reviewer_id,
            "reason": approval.reason,
            "original_id": approval.conflict_id
        }
        await audit_collection.insert_one(audit_entry)
        
        # 2. Create/Update Golden Record
        golden_record = {
            "master_id": f"GP-{approval.conflict_id}",
            "last_updated": time.time(),
            "status": "CERTIFIED",
            "provenance": audit_entry
        }
        await mpi_collection.insert_one(golden_record)
        
        return {"status": "success", "msg": "Golden Record persisted and audited in MongoDB"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
