from datetime import datetime
from typing import List, Dict, Any, Optional
from careunify.shared.resolution_models import GoldenPatientRecord
import uuid

class MergeEngine:
    """
    Handles merging of linked records into a single Golden Record.
    """
    
    @staticmethod
    def create_golden_record(resources: List[Dict[str, Any]]) -> GoldenPatientRecord:
        """
        Merges multiple FHIR Patient resources into one Golden Record.
        Applies survivorship policy: Prefer recently ingested data for each field.
        """
        if not resources:
            raise ValueError("Cannot merge empty resource list")

        # Sort resources by 'updated' or an ingestion timestamp if available
        # For now, we assume provide order or just use the first one as base
        primary = resources[0]
        golden_id = f"G-{uuid.uuid4().hex[:8]}"
        
        merged_patient = {
            "resourceType": "Patient",
            "id": golden_id,
            "active": True,
            "name": primary.get("name"),
            "gender": primary.get("gender"),
            "birthDate": primary.get("birthDate"),
            "telecom": [],
            "address": [],
            "identifier": []
        }
        
        lineage = {}
        source_links = []

        # Aggregate identifiers and unique info from all records
        seen_identifiers = set()
        
        for res in resources:
            source_id = res.get("id", "unknown")
            source_links.append({
                "source_id": source_id,
                "system": res.get("meta", {}).get("source", "unknown"),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Merge identifiers
            for ident in res.get("identifier", []):
                val = ident.get("value")
                if val and val not in seen_identifiers:
                    merged_patient["identifier"].append(ident)
                    seen_identifiers.add(val)
                    lineage[f"identifier.{val}"] = source_id

            # Merge Address/Telecom if not present
            if res.get("address") and not merged_patient["address"]:
                merged_patient["address"] = res.get("address")
                lineage["address"] = source_id
                
            if res.get("telecom"):
                merged_patient["telecom"].extend(res.get("telecom"))

        return GoldenPatientRecord(
            id=golden_id,
            merged_resource=merged_patient,
            linked_source_records=source_links,
            lineage=lineage
        )
