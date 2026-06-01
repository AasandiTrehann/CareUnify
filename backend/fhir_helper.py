import uuid
from datetime import datetime

def generate_fhir_id() -> str:
    return str(uuid.uuid4())

def validate_fhir_resource(resource: dict) -> tuple[bool, list[str]]:
    """Validates basic FHIR R4 resource requirements."""
    errors = []
    if not isinstance(resource, dict):
        return False, ["Resource must be a JSON dictionary"]
        
    resource_type = resource.get("resourceType")
    if not resource_type:
        errors.append("Missing 'resourceType' field")
        return False, errors
        
    if resource_type == "Patient":
        if not resource.get("name") or not isinstance(resource.get("name"), list):
            errors.append("Patient resource must contain a list of 'name' objects")
        if not resource.get("gender"):
            errors.append("Patient resource must contain 'gender'")
        if not resource.get("birthDate"):
            errors.append("Patient resource must contain 'birthDate'")
            
    elif resource_type == "Observation":
        if not resource.get("status"):
            errors.append("Observation must contain a 'status'")
        if not resource.get("code") or not isinstance(resource.get("code"), dict):
            errors.append("Observation must contain a 'code' object")
        if not resource.get("subject") or not isinstance(resource.get("subject"), dict):
            errors.append("Observation must contain a 'subject' reference mapping")
            
    elif resource_type == "Encounter":
        if not resource.get("status"):
            errors.append("Encounter must contain a 'status'")
        if not resource.get("class"):
            errors.append("Encounter must contain a 'class' element")
        if not resource.get("subject") or not isinstance(resource.get("subject"), dict):
            errors.append("Encounter must contain a 'subject' reference mapping")
            
    elif resource_type == "MedicationRequest":
        if not resource.get("status"):
            errors.append("MedicationRequest must contain a 'status'")
        if not resource.get("intent"):
            errors.append("MedicationRequest must contain an 'intent'")
        if not resource.get("medicationCodeableConcept") and not resource.get("medicationReference"):
            errors.append("MedicationRequest must specify a medication")
        if not resource.get("subject") or not isinstance(resource.get("subject"), dict):
            errors.append("MedicationRequest must contain a 'subject' reference mapping")
            
    elif resource_type == "DiagnosticReport":
        if not resource.get("status"):
            errors.append("DiagnosticReport must contain a 'status'")
        if not resource.get("code") or not isinstance(resource.get("code"), dict):
            errors.append("DiagnosticReport must contain a 'code' object")
        if not resource.get("subject") or not isinstance(resource.get("subject"), dict):
            errors.append("DiagnosticReport must contain a 'subject' reference mapping")
            
    else:
        errors.append(f"Unsupported resourceType: '{resource_type}'")
        
    return len(errors) == 0, errors


def to_fhir_patient(data: dict) -> dict:
    """Standardizes input patient data into FHIR R4 Patient resource."""
    patient_id = data.get("id") or generate_fhir_id()
    
    # Structure names
    given_names = data.get("given_names") or []
    if isinstance(given_names, str):
        given_names = [given_names]
        
    names = [{
        "use": "official",
        "family": data.get("last_name", ""),
        "given": given_names
    }]
    
    # Structure telecom
    telecoms = []
    if data.get("phone"):
        telecoms.append({
            "system": "phone",
            "value": data.get("phone"),
            "use": "home"
        })
    if data.get("email"):
        telecoms.append({
            "system": "email",
            "value": data.get("email")
        })
        
    # Structure address
    addresses = []
    if data.get("address"):
        addresses.append({
            "line": [data.get("address")],
            "city": data.get("city", ""),
            "state": data.get("state", ""),
            "postalCode": data.get("postal_code", "")
        })
        
    # Structure identifier (SSN if present)
    identifiers = []
    if data.get("ssn"):
        identifiers.append({
            "system": "http://hl7.org/fhir/sid/us-ssn",
            "value": data.get("ssn")
        })
        
    return {
        "resourceType": "Patient",
        "id": patient_id,
        "active": True,
        "identifier": identifiers,
        "name": names,
        "telecom": telecoms,
        "gender": data.get("gender", "unknown").lower(),
        "birthDate": data.get("dob", ""),
        "address": addresses
    }


def to_fhir_observation(patient_id: str, data: dict) -> dict:
    """Standardizes clinical metrics into FHIR R4 Observation resource."""
    obs_id = data.get("id") or generate_fhir_id()
    
    # Map common lab tests to LOINC codes if possible
    test_name = data.get("test_name", "Unknown Lab")
    loinc_codes = {
        "A1C": "4548-4",
        "Cholesterol": "2093-3",
        "HDL": "2085-9",
        "LDL": "18262-6",
        "Blood Pressure": "85354-9",
        "Systolic BP": "8480-6",
        "Diastolic BP": "8462-4"
    }
    
    loinc_code = loinc_codes.get(test_name, "unknown-code")
    
    observation = {
        "resourceType": "Observation",
        "id": obs_id,
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "laboratory" if test_name != "Blood Pressure" else "vital-signs",
                        "display": "Laboratory" if test_name != "Blood Pressure" else "Vital Signs"
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": loinc_code,
                    "display": test_name
                }
            ],
            "text": test_name
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "effectiveDateTime": data.get("date", datetime.utcnow().strftime("%Y-%m-%d")),
        "issued": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    # Handle composite vital sign (BP) vs single value
    if test_name == "Blood Pressure" and "/" in str(data.get("result", "")):
        parts = str(data.get("result")).split("/")
        observation["component"] = [
            {
                "code": {
                    "coding": [{"system": "http://loinc.org", "code": "8480-6", "display": "Systolic BP"}]
                },
                "valueQuantity": {
                    "value": float(parts[0]),
                    "unit": "mmHg",
                    "system": "http://unitsofmeasure.org",
                    "code": "mm[Hg]"
                }
            },
            {
                "code": {
                    "coding": [{"system": "http://loinc.org", "code": "8462-4", "display": "Diastolic BP"}]
                },
                "valueQuantity": {
                    "value": float(parts[1]),
                    "unit": "mmHg",
                    "system": "http://unitsofmeasure.org",
                    "code": "mm[Hg]"
                }
            }
        ]
    else:
        try:
            val = float(data.get("result", 0))
            observation["valueQuantity"] = {
                "value": val,
                "unit": data.get("unit", ""),
                "system": "http://unitsofmeasure.org",
                "code": data.get("unit", "")
            }
        except ValueError:
            observation["valueString"] = str(data.get("result", ""))
            
    return observation


def to_fhir_encounter(patient_id: str, data: dict) -> dict:
    """Standardizes encounter records into FHIR R4 Encounter resource."""
    enc_id = data.get("id") or generate_fhir_id()
    
    return {
        "resourceType": "Encounter",
        "id": enc_id,
        "status": "finished",
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": data.get("class_code", "AMB"), # Ambulatory default
            "display": data.get("class_display", "ambulatory")
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "period": {
            "start": data.get("date", datetime.utcnow().strftime("%Y-%m-%d"))
        },
        "reasonCode": [
            {
                "text": data.get("reason", "Routine Checkup")
            }
        ]
    }


def to_fhir_medication_request(patient_id: str, data: dict) -> dict:
    """Standardizes medication prescriptions into FHIR R4 MedicationRequest."""
    req_id = data.get("id") or generate_fhir_id()
    
    return {
        "resourceType": "MedicationRequest",
        "id": req_id,
        "status": "active",
        "intent": "order",
        "medicationCodeableConcept": {
            "coding": [
                {
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": data.get("rxnorm_code", "unknown"),
                    "display": data.get("medication_name", "Prescription")
                }
            ],
            "text": data.get("medication_name", "Prescription")
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "authoredOn": data.get("date", datetime.utcnow().strftime("%Y-%m-%d")),
        "dosageInstruction": [
            {
                "text": data.get("dosage", "As directed")
            }
        ]
    }


def to_fhir_diagnostic_report(patient_id: str, data: dict) -> dict:
    """Standardizes diagnostic reports into FHIR R4 DiagnosticReport."""
    rep_id = data.get("id") or generate_fhir_id()
    
    return {
        "resourceType": "DiagnosticReport",
        "id": rep_id,
        "status": "final",
        "code": {
            "text": data.get("title", "Clinical Scan Document")
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "effectiveDateTime": data.get("date", datetime.utcnow().strftime("%Y-%m-%d")),
        "conclusion": data.get("conclusion", ""),
        "presentedForm": [
            {
                "contentType": "text/plain",
                "title": data.get("title", "Transcription Output"),
                "data": data.get("raw_text", "")
            }
        ]
    }


def create_clinical_summary_text(resource: dict) -> str:
    """Synthesizes clinical resource data into a single readable sentence for indexing in RAG."""
    r_type = resource.get("resourceType")
    
    if r_type == "Observation":
        code = resource.get("code", {}).get("text", "clinical metric")
        date = resource.get("effectiveDateTime", "recent date")
        
        if "valueQuantity" in resource:
            val = resource["valueQuantity"].get("value")
            unit = resource["valueQuantity"].get("unit", "")
            return f"Lab test {code} showed a result of {val} {unit} on {date}."
        elif "component" in resource:
            parts = []
            for comp in resource["component"]:
                comp_name = comp.get("code", {}).get("coding", [{}])[0].get("display", "metric")
                val = comp.get("valueQuantity", {}).get("value")
                unit = comp.get("valueQuantity", {}).get("unit", "")
                parts.append(f"{comp_name} of {val} {unit}")
            return f"Observation {code} recorded: {', '.join(parts)} on {date}."
        elif "valueString" in resource:
            return f"Observation {code} resulted in: {resource['valueString']} on {date}."
            
    elif r_type == "Encounter":
        reason = resource.get("reasonCode", [{}])[0].get("text", "routine health review")
        date = resource.get("period", {}).get("start", "recent date")
        cls = resource.get("class", {}).get("display", "clinic visit")
        return f"Patient completed a {cls} medical encounter for '{reason}' on {date}."
        
    elif r_type == "MedicationRequest":
        med = resource.get("medicationCodeableConcept", {}).get("text", "medication")
        dosage = resource.get("dosageInstruction", [{}])[0].get("text", "as directed")
        date = resource.get("authoredOn", "recent date")
        return f"Medication prescription created: Patient prescribed {med}, dosage: {dosage}, on {date}."
        
    elif r_type == "DiagnosticReport":
        title = resource.get("code", {}).get("text", "clinical report")
        conclusion = resource.get("conclusion", "")
        date = resource.get("effectiveDateTime", "recent date")
        summary = f"Diagnostic report '{title}' on {date}."
        if conclusion:
            summary += f" Medical conclusion: {conclusion}."
        return summary
        
    elif r_type == "Patient":
        names = resource.get("name", [{}])[0]
        fname = " ".join(names.get("given", []))
        lname = names.get("family", "")
        dob = resource.get("birthDate", "unknown")
        gender = resource.get("gender", "unknown")
        return f"Demographic summary: Patient named {fname} {lname}, DOB: {dob}, Gender: {gender}."
        
    return f"Clinical record of type {r_type} ingested."
