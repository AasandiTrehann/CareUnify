import sys
import os
# Add the project root to sys.path for local imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from careunify.services.resolution.scorer import ResolutionScorer

def test_resolution_logic():
    print("=== CareUnify Phase Two: Resolution Engine Test ===\n")

    # 1. Exact Match Test (Deterministic)
    rec_a = {
        "id": "p1",
        "name": [{"family": "Smith", "given": ["Alice"]}],
        "birthDate": "1985-05-12",
        "gender": "female",
        "identifier": [{"system": "SSN", "value": "123-45-678"}]
    }
    rec_b = {
        "id": "p2",
        "name": [{"family": "Smith", "given": ["Alice"]}],
        "birthDate": "1985-05-12",
        "gender": "female",
        "identifier": [{"system": "SSN", "value": "123-45-678"}]
    }
    
    score1 = ResolutionScorer.score_pair(rec_a, rec_b)
    print(f"[TEST 1] Exact Match (SSN): Probability={score1.probability}, Method={score1.method}")

    # 2. Fuzzy Match Test (Typos & Phonetics)
    rec_c = {
        "id": "p3",
        "name": [{"family": "Smyth", "given": ["Alise"]}],
        "birthDate": "1985-05-12",
        "gender": "female"
    }
    score2 = ResolutionScorer.score_pair(rec_a, rec_c)
    print(f"[TEST 2] Fuzzy/Phonetic Match: Probability={score2.probability}, Method={score2.method}")
    print(f"       Features: {score2.features}")

    # 3. Disparate Record Test
    rec_d = {
        "id": "p4",
        "name": [{"family": "Brown", "given": ["Charlie"]}],
        "birthDate": "1990-10-10",
        "gender": "male"
    }
    score3 = ResolutionScorer.score_pair(rec_a, rec_d)
    print(f"[TEST 3] Disparate Records: Probability={score3.probability}, Method={score3.method}")

    print("\n=================================================")

if __name__ == "__main__":
    test_resolution_logic()
