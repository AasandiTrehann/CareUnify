from typing import Dict, Any, List, Optional
from fhir.resources.patient import Patient
from fhir.resources.observation import Observation
from fhir.resources.condition import Condition
from fhir.resources.medicationrequest import MedicationRequest
from fhir.resources.encounter import Encounter
from pydantic import ValidationError
import datetime

class FHIRMapper:
    """
    Standardizes raw ingestion data into FHIR R4 resources.
    """
    
    RESOURCE_MAP = {
        "Patient": Patient,
        "Observation": Observation,
        "Condition": Condition,
        "MedicationRequest": MedicationRequest,
        "Encounter": Encounter
    }

    @classmethod
    def map_to_fhir(cls, resource_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempts to map and validate a dictionary to a FHIR resource.
        """
        if resource_type not in cls.RESOURCE_MAP:
            raise ValueError(f"Unsupported FHIR resource type: {resource_type}")
        
        resource_class = cls.RESOURCE_MAP[resource_type]
        
        # Ensure 'resourceType' is set for the FHIR resource
        if "resourceType" not in data:
            data["resourceType"] = resource_type
            
        try:
            # Pydantic validation via fhir.resources
            resource = resource_class(**data)
            return resource.dict()
        except ValidationError as e:
            raise ValueError(f"FHIR Validation Error for {resource_type}: {e.json()}")

    @staticmethod
    def transform_csv_row(resource_type: str, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Custom transformation logic for CSV rows based on resource type.
        This provides a hook for specific source-to-FHIR templates.
        """
        # Example transformation for CSV -> Patient
        if resource_type == "Patient":
            return {
                "name": [{"family": row.get("last_name"), "given": [row.get("first_name")]}],
                "gender": row.get("gender", "unknown").lower(),
                "birthDate": row.get("dob")
            }
        # Generic return if no specific mapping
        return row
