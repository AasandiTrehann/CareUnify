"""
CareUnify Generation Engine (Independent Service)
Responsibility: Grounded Summarization & Provenance Binding.
Constraint: Clinically Conservative (Precision over Creativity).
"""

class ClinicalGenerator:
    def __init__(self, temperature: float = 0.0):
        self.temperature = temperature # 0.0 ensures deterministic, non-creative results

    def generate_grounded_response(self, query: str, context: list):
        """
        Takes raw FHIR atoms and synthesizes a cited clinician-ready response.
        """
        if not context:
            return "No relevant clinical records were retrieved to answer this query safely."

        # Logic for mapping retrieved atoms to structured summaries
        summary_parts = []
        citations = []
        
        for atom in context:
            parts = f"{atom['val']} (Source: {atom['source']}, Date: {atom['date']})"
            summary_parts.append(parts)
            citations.append(atom['id'])

        # Final Synthesis
        response = f"Clinical Summary: Found {len(context)} relevant records. " + " | ".join(summary_parts)
        
        return {
            "answer": response,
            "citations": citations,
            "policy": "Grounded-Precision"
        }

generator = ClinicalGenerator()
