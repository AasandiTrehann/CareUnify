import jellyfish
import Levenshtein
from typing import Dict, Any, Optional

class SimilarityEngine:
    """
    Computes linguistic and phonetic similarity metrics between patient records.
    """
    
    @staticmethod
    def name_similarity(name1: str, name2: str) -> float:
        """Jaro-Winkler similarity for names (handles typos/transpositions well)."""
        if not name1 or not name2:
            return 0.0
        return jellyfish.jaro_winkler_similarity(name1.lower(), name2.lower())

    @staticmethod
    def phonetic_match(name1: str, name2: str) -> bool:
        """Check if names sound identical using NYSIIS (better for medical context than Soundex)."""
        if not name1 or not name2:
            return False
        return jellyfish.nysiis(name1) == jellyfish.nysiis(name2)

    @staticmethod
    def dob_similarity(dob1: str, dob2: str) -> float:
        """Similarity for Date of Birth. Exact match = 1.0, otherwise 0.0 or fuzzy lookup."""
        if not dob1 or not dob2:
            return 0.0
        if dob1 == dob2:
            return 1.0
        # Check for year/month transpositions could be added here
        return 0.0

    @staticmethod
    def compute_feature_vector(rec1: Dict[str, Any], rec2: Dict[str, Any]) -> Dict[str, float]:
        """
        Creates a feature vector for ML scoring.
        Assumes rec1/rec2 are standardized Patient resources.
        """
        # Extract name parts
        n1 = rec1.get("name", [{}])[0]
        n2 = rec2.get("name", [{}])[0]
        
        last1, last2 = n1.get("family", ""), n2.get("family", "")
        first1 = n1.get("given", [""])[0] if n1.get("given") else ""
        first2 = n2.get("given", [""])[0] if n2.get("given") else ""
        
        features = {
            "last_name_sim": SimilarityEngine.name_similarity(last1, last2),
            "first_name_sim": SimilarityEngine.name_similarity(first1, first2),
            "phonetic_last_match": 1.0 if SimilarityEngine.phonetic_match(last1, last2) else 0.0,
            "dob_match": SimilarityEngine.dob_similarity(rec1.get("birthDate"), rec2.get("birthDate")),
            "gender_match": 1.0 if rec1.get("gender") == rec2.get("gender") else 0.0
        }
        
        return features
