from typing import Dict, Any
from careunify.services.resolution.similarity import SimilarityEngine
from careunify.shared.resolution_models import MatchScore

class ResolutionScorer:
    """
    ML-based (or weighted heuristic) match probability scorer.
    """
    
    # Weights for the scoring model
    WEIGHTS = {
        "last_name_sim": 0.40,
        "first_name_sim": 0.20,
        "dob_match": 0.25,
        "phonetic_last_match": 0.10,
        "gender_match": 0.05
    }

    @classmethod
    def score_pair(cls, rec1: Dict[str, Any], rec2: Dict[str, Any]) -> MatchScore:
        """
        Computes match probability for a pair of records.
        """
        features = SimilarityEngine.compute_feature_vector(rec1, rec2)
        
        # Weighted linear combination (replaces ML classifier for bootstrap)
        probability = sum(features[f] * cls.WEIGHTS[f] for f in cls.WEIGHTS)
        
        # Rule-based Overrides (High Precision)
        # If National ID exists and matches exactly, override probability to 1.0
        ids1 = set(i.get("value") for i in rec1.get("identifier", []) if i.get("value"))
        ids2 = set(i.get("value") for i in rec2.get("identifier", []) if i.get("value"))
        if ids1.intersection(ids2):
             return MatchScore(probability=1.0, features=features, method="Deterministic-Rule")

        return MatchScore(probability=round(probability, 4), features=features, method="Weighted-Hybrid")
