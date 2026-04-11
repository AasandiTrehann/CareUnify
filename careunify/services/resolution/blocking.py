import jellyfish
from typing import List, Dict, Any, Set

class BlockingEngine:
    """
    Candidate generation (blocking) to group potentially matching records.
    """
    
    @staticmethod
    def get_blocking_keys(patient: Dict[str, Any]) -> List[str]:
        """
        Generates multiple blocking keys for a patient to ensure high recall.
        """
        name_entry = patient.get("name", [{}])[0]
        family = name_entry.get("family", "").lower()
        first = name_entry.get("given", [""])[0].lower() if name_entry.get("given") else ""
        dob = patient.get("birthDate", "") # YYYY-MM-DD
        
        keys = []
        
        # 1. Phonetic Block (Last Name NYSIIS)
        if family:
            keys.append(f"phonetic_{jellyfish.nysiis(family)}")
            
        # 2. DOB + First Initial Block
        if dob and first:
            year = dob[:4]
            keys.append(f"dob_{year}_{first[:1]}")
            
        # 3. Zip Code Block (if address available)
        address = patient.get("address", [{}])[0]
        postal = address.get("postalCode")
        if postal:
            keys.append(f"zip_{postal}")
            
        return keys

    @staticmethod
    def group_by_blocks(records: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Groups record IDs by blocking keys.
        Returns {key: [record_id1, record_id2, ...]}
        """
        blocks = {}
        for rec in records:
            rec_id = rec.get("id") or str(id(rec))
            keys = BlockingEngine.get_blocking_keys(rec)
            for k in keys:
                if k not in blocks:
                    blocks[k] = []
                blocks[k].append(rec_id)
        return blocks
