import uuid
from sqlalchemy import Column, String, Date, Float, DateTime, ForeignKey, Text, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Patient(Base):
    __tablename__ = "patients"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    dob = Column(String(10), nullable=False)  # Format: YYYY-MM-DD
    ssn = Column(String(50), nullable=True)   # Encrypted or raw (in mock)
    gender = Column(String(20), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(String(255), nullable=True)
    fhir_payload = Column(Text, nullable=True)  # FHIR Patient JSON object
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    links = relationship("PatientLink", back_populates="golden_patient", cascade="all, delete-orphan")
    clinical_resources = relationship("ClinicalResource", back_populates="patient", cascade="all, delete-orphan")
    match_queue_entries = relationship("MatchQueue", back_populates="candidate_patient", cascade="all, delete-orphan")

class PatientLink(Base):
    __tablename__ = "patient_links"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    golden_patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    source_system = Column(String(100), nullable=False)  # EHR_A, LAB_B, OCR_NOTE, VOICE_DICTATION
    source_patient_id = Column(String(100), nullable=True) # ID in the source database
    raw_payload = Column(Text, nullable=True)             # Raw JSON/CSV payload
    created_at = Column(DateTime, default=datetime.utcnow)

    golden_patient = relationship("Patient", back_populates="links")

class ClinicalResource(Base):
    __tablename__ = "clinical_resources"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    resource_type = Column(String(50), nullable=False)     # Observation, Encounter, MedicationRequest, etc.
    fhir_payload = Column(Text, nullable=False)            # Valided FHIR JSON payload
    extracted_text = Column(Text, nullable=True)           # Clinical text description for Vector DB index
    source_system = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="clinical_resources")

class MatchQueue(Base):
    __tablename__ = "match_queue"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    candidate_patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    incoming_record_payload = Column(Text, nullable=False) # JSON details of incoming record
    match_score = Column(Float, nullable=False)            # 0.60 to 0.85
    matching_features = Column(Text, nullable=False)       # JSON of comparisons (name:0.8, dob:1.0, etc.)
    status = Column(String(20), default="PENDING")         # PENDING, APPROVED_MERGE, REJECTED_NEW_PATIENT
    created_at = Column(DateTime, default=datetime.utcnow)

    candidate_patient = relationship("Patient", back_populates="match_queue_entries")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(100), nullable=False)          # Clinician user/role
    action = Column(String(100), nullable=False)           # VIEW_PATIENT, MERGE_RECORDS, LLM_QUERY, etc.
    patient_id = Column(String(36), nullable=True)         # Associated patient if any
    details = Column(Text, nullable=True)                  # Describe query, edits made, etc.
    timestamp = Column(DateTime, default=datetime.utcnow)
