from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class ProvenanceMetadata(BaseModel):
    source_system: str = Field(..., description="Identifier of the source system")
    ingestion_timestamp: datetime = Field(default_factory=datetime.utcnow)
    original_record_id: Optional[str] = Field(None, description="Reference to the original record in the source system")
    content_type: str = Field(..., description="MIME type or shorthand for the original content")
    transformation_version: str = Field("1.0.0", description="Version of the mapping logic used")

class IngestedData(BaseModel):
    raw_data: Any
    metadata: ProvenanceMetadata
    resource_type: str  # e.g., 'Patient', 'Observation'
    
class NormalizedResource(BaseModel):
    fhir_resource: Dict[str, Any]
    provenance: ProvenanceMetadata
    validation_status: str = "valid"
    validation_errors: Optional[list] = None
