from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class MatchScore(BaseModel):
    probability: float
    features: Dict[str, float]
    method: str  # e.g., 'ML-XGBoost', 'Deterministic-Rule'

class MatchRecordLink(BaseModel):
    target_person_id: str  # The unique ID of the Golden Record
    source_resource_ids: List[str]  # IDs of FHIR resources linked
    confidence_score: float
    status: str = "pending"  # auto-merged, pending-review, rejected
    created_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_by: Optional[str] = None
    review_timestamp: Optional[datetime] = None
    review_reason: Optional[str] = None

class GoldenPatientRecord(BaseModel):
    id: Optional[str] = None
    merged_resource: Dict[str, Any]  # The merged FHIR Patient resource
    linked_source_records: Optional[List[Dict[str, Any]]] = []
    lineage: Optional[Dict[str, str]] = {}
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ReviewQueueItem(BaseModel):
    id: str
    candidate_records: List[Dict[str, Any]]  # The standardized resources to compare
    match_details: MatchScore
    status: str = "queued"
    created_at: datetime = Field(default_factory=datetime.utcnow)
