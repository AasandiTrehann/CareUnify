from typing import List, Dict, Any
from careunify.shared.resolution_models import GoldenPatientRecord

class ClinicalRAGEngine:
    """
    Retrieval-Augmented Generation for Unified Patient Records.
    """
    
    @staticmethod
    def construct_context(golden_record: GoldenPatientRecord) -> str:
        """
        Transforms FHIR data into a searchable text context, stripping PHI.
        """
        res = golden_record.merged_resource
        
        context_parts = []
        context_parts.append(f"Patient Gender: {res.get('gender')}")
        context_parts.append(f"Age: [Redacted]")
        
        # Timeline context
        context_parts.append("\n=== Conditions ===")
        for cond in res.get("condition", []):
            context_parts.append(f"- {cond.get('code', {}).get('text')} (Status: {cond.get('clinicalStatus', {}).get('text', 'active')})")
            
        context_parts.append("\n=== Medications ===")
        for med in res.get("medicationRequest", []):
            context_parts.append(f"- {med.get('medicationCodeableConcept', {}).get('text')}")

        return "\n".join(context_parts)

    @staticmethod
    def query(golden_record: GoldenPatientRecord, prompt: str) -> Dict[str, Any]:
        """
        Simulated RAG Query logic.
        In production, this would use ChromaDB + LangChain + Clinical LLM.
        """
        context = ClinicalRAGEngine.construct_context(golden_record)
        
        # Simple heuristic generation for Phase Three Bootstrap
        answer = ""
        citations = []
        
        prompt_lower = prompt.lower()
        if "medication" in prompt_lower or "medicine" in prompt_lower:
             meds = [m.get('medicationCodeableConcept', {}).get('text') for m in golden_record.merged_resource.get('medicationRequest', [])]
             answer = f"The patient is currently prescribed: {', '.join(meds)}. Note: provenance indicates these were merged from multiple systems."
             citations = list(golden_record.lineage.keys())
        elif "condition" in prompt_lower or "status" in prompt_lower:
             conds = [c.get('code', {}).get('text') for c in golden_record.merged_resource.get('condition', [])]
             answer = f"The patient's clinical history includes: {', '.join(conds)}."
             citations = ["lineage.condition"]
        else:
             answer = "I'm sorry, I couldn't find a direct answer in the retrieved clinical context. Please refine your query."

        return {
            "answer": answer,
            "citations": citations,
            "context_retrieved": context,
            "timestamp": "2026-04-11T05:00:00Z"
        }
