import os
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, Any, List
from careunify.shared.models import NormalizedResource
from dotenv import load_dotenv

load_dotenv()

class CanonicalDataStore:
    """
    Persistence layer for FHIR resources and provenance metadata.
    """
    
    def __init__(self):
        self.mock_mode = False
        try:
            mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
            self.client = AsyncIOMotorClient(mongo_uri, serverSelectionTimeoutMS=2000)
            self.db = self.client.careunify
            self.collection = self.db.fhir_resources
            # Check connection
            import asyncio
            # In a real app we'd do a ping here, but we'll handle it during first operation
        except Exception:
            print("DEBUG: MongoDB connection failed. Switching to IN-MEMORY MOCK STORAGE.")
            self.mock_mode = True
            self.memory_store = []

    async def save_resource(self, resource: NormalizedResource):
        """Saves a normalized resource with provenance, falling back to mock if DB fails."""
        if self.mock_mode:
            self.memory_store.append(resource.dict())
            return f"mock_id_{len(self.memory_store)}"
            
        try:
            document = resource.dict()
            if "id" in document["fhir_resource"]:
                document["_id"] = document["fhir_resource"]["id"]
                
            result = await self.collection.update_one(
                {"_id": document.get("_id")},
                {"$set": document},
                upsert=True
            )
            return result.upserted_id or document.get("_id")
        except Exception as e:
            print(f"DEBUG: MongoDB operation failed ({e}). Falling back to MOCK STORAGE for this record.")
            self.mock_mode = True
            if not hasattr(self, 'memory_store'):
                self.memory_store = []
            self.memory_store.append(resource.dict())
            return "mock_id_fallback"

    async def get_resources(self, resource_type: str = None) -> List[Dict[str, Any]]:
        """Retrieves resources, optionally filtered by type."""
        query = {}
        if resource_type:
            query["fhir_resource.resourceType"] = resource_type
            
        cursor = self.collection.find(query)
        return await cursor.to_list(length=100)
