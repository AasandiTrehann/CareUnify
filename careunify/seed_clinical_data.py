import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import random
import time

# CONFIGURATION
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "careunify_db"

sources = ["System Alpha", "Mayo Hub", "Quest Labs", "Community Clinic", "Radiology Center"]
conditions = ["Hypertension", "Type 2 Diabetes", "Asthma", "High Cholesterol", "NA"]

async def seed_data():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # 1. Clear existing demo data
    await db.clinical_data.delete_many({})
    await db.master_patient_index.delete_many({})
    
    print("--- Seeding 600 Clinical Atoms ---")
    
    records = []
    for i in range(600):
        name_root = f"Patient_{i}"
        # Simulate some duplicates
        if i < 50:
            name_root = f"Patient_{i % 10}" # Create duplicates for the first 10 patients
            
        record = {
            "resourceType": "Patient",
            "patient_id": f"GP-{8000 + i}",
            "name": f"{name_root}",
            "dob": f"{random.randint(1950, 2010)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            "source": random.choice(sources),
            "vitals": {
                "bp": f"{random.randint(110, 140)}/{random.randint(70, 95)}",
                "hr": f"{random.randint(60, 100)}",
                "temp": f"{random.uniform(97.5, 99.2):.1f}"
            },
            "condition": random.choice(conditions),
            "ingestion_timestamp": time.time(),
            "status": "FRAGMENTED"
        }
        records.append(record)
    
    # Batch Insert
    if records:
        await db.clinical_data.insert_many(records)
        print("SUCCESS: Injected 600 records into clinical_data.")

    # 2. Seed some Certified Golden Records (Registry)
    print("--- Certifying 342 Golden Records ---")
    golden_records = []
    for i in range(342):
        golden = {
            "master_id": f"MPI-{9000 + i}",
            "name": f"Verified_Patient_{i}",
            "status": "CERTIFIED",
            "source_count": random.randint(2, 5),
            "last_updated": time.time()
        }
        golden_records.append(golden)
    
    await db.master_patient_index.insert_many(golden_records)
    print("SUCCESS: Created 342 Master Identities.")

    print("FINISHED: Seeding Complete. Dashboard registry is now live with 600 atoms.")

if __name__ == "__main__":
    asyncio.run(seed_data())
