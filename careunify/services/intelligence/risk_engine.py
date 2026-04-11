from typing import List, Dict, Any

class ClinicalRiskEngine:
    """
    Automated safety scanning for unified patient records.
    """
    
    @staticmethod
    def identify_risks(golden_record: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Scans merged clinical data for conflicts and risks.
        """
        risks = []
        patient_data = golden_record.get("merged_resource", {})
        
        # 1. Duplicate Medication Detection (Post-Merge)
        meds = [m for m in patient_data.get("medicationRequest", [])]
        med_names = [m.get("medicationCodeableConcept", {}).get("text", "").lower() for m in meds]
        
        seen_meds = set()
        for name in med_names:
            if name in seen_meds:
                risks.append({
                    "level": "CRITICAL",
                    "type": "DUPLICATE_MEDICATION",
                    "message": f"Potential duplicate medication detected: {name.title()}",
                    "affected_field": "MedicationRequest"
                })
            seen_meds.add(name)

        # 2. Conflicting Conditions
        conditions = [c.get("code", {}).get("text", "").lower() for c in patient_data.get("condition", [])]
        if "chronic kidney disease" in conditions and "ibuprofen" in med_names:
              risks.append({
                    "level": "WARNING",
                    "type": "CONTRAINDICATION",
                    "message": "NSAID (Ibuprofen) detected in patient with CKD.",
                    "affected_field": "ClinicalHistory"
                })

        return risks
