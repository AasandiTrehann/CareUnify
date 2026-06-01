import json
import re
from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import Patient, PatientLink, ClinicalResource, MatchQueue, AuditLog
from backend.phonetic_helper import soundex, nysiis
from backend.config import MATCH_AUTO_MERGE, MATCH_REVIEW_REQUIRED

def jaro_distance(s1: str, s2: str) -> float:
    """Computes the Jaro distance between two strings."""
    if not s1 or not s2:
        return 0.0
        
    s1, s2 = s1.strip().lower(), s2.strip().lower()
    if s1 == s2:
        return 1.0
        
    len1, len2 = len(s1), len(s2)
    max_dist = max(len1, len2) // 2 - 1
    if max_dist < 0:
        max_dist = 0
        
    match1 = [False] * len1
    match2 = [False] * len2
    
    matches = 0
    transpositions = 0
    
    for i in range(len1):
        start = max(0, i - max_dist)
        end = min(len2, i + max_dist + 1)
        for j in range(start, end):
            if not match2[j] and s1[i] == s2[j]:
                match1[i] = True
                match2[j] = True
                matches += 1
                break
                
    if matches == 0:
        return 0.0
        
    k = 0
    for i in range(len1):
        if match1[i]:
            while not match2[k]:
                k += 1
            if s1[i] != s2[k]:
                transpositions += 1
            k += 1
            
    transpositions //= 2
    return (matches / len1 + matches / len2 + (matches - transpositions) / matches) / 3.0


def jaro_winkler_distance(s1: str, s2: str) -> float:
    """Computes the Jaro-Winkler distance between two strings."""
    jaro = jaro_distance(s1, s2)
    if jaro < 0.7:
        return jaro
        
    # Common prefix length up to 4 chars
    prefix = 0
    for c1, c2 in zip(s1.lower(), s2.lower()):
        if c1 == c2:
            prefix += 1
        else:
            break
        if prefix == 4:
            break
            
    return jaro + prefix * 0.1 * (1.0 - jaro)


def levenshtein_distance(s1: str, s2: str) -> int:
    """Computes the Levenshtein distance between two strings."""
    s1, s2 = s1.lower(), s2.lower()
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
        
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
        
    return previous_row[-1]


def get_blocking_keys(first_name: str, last_name: str, dob: str) -> list[str]:
    """Generates phonetic blocking keys to partition the database search space.
    
    Returns keys like Soundex_LastName + FirstInitial + BirthYear.
    """
    fname = re.sub(r'[^A-Z]', '', (first_name or '').upper())
    lname = re.sub(r'[^A-Z]', '', (last_name or '').upper())
    
    first_initial = fname[0] if fname else "X"
    birth_year = dob[:4] if dob and len(dob) >= 4 else "0000"
    
    snd_ln = soundex(lname)
    ny_ln = nysiis(lname)
    
    # We generate two keys using Soundex and NYSIIS for robustness
    key1 = f"{snd_ln}_{first_initial}_{birth_year}"
    key2 = f"{ny_ln}_{first_initial}_{birth_year}"
    
    return [key1, key2]


def calculate_match_probability(p1: dict, p2: dict) -> tuple[float, dict]:
    """Calculates match probability using a weighted rule-based ML classifier mimic.
    
    Compares demographic features and produces a score between 0.0 and 1.0.
    """
    features = {}
    
    # Name similarity
    fn1, ln1 = p1.get("first_name", ""), p1.get("last_name", "")
    fn2, ln2 = p2.get("first_name", ""), p2.get("last_name", "")
    
    jw_first = jaro_winkler_distance(fn1, fn2)
    jw_last = jaro_winkler_distance(ln1, ln2)
    
    # Handle swapped names (first/last swap)
    jw_swap1 = jaro_winkler_distance(fn1, ln2)
    jw_swap2 = jaro_winkler_distance(ln1, fn2)
    
    if (jw_swap1 + jw_swap2) > (jw_first + jw_last):
        features["name_swapped"] = True
        jw_first, jw_last = jw_swap1, jw_swap2
    else:
        features["name_swapped"] = False
        
    features["first_name_sim"] = jw_first
    features["last_name_sim"] = jw_last
    
    # DOB similarity
    dob1 = p1.get("dob", "")
    dob2 = p2.get("dob", "")
    if dob1 == dob2 and dob1:
        features["dob_sim"] = 1.0
    elif dob1 and dob2:
        # Check for minor typos (e.g. 1 Levenshtein distance, or swapped month/day)
        dist = levenshtein_distance(dob1, dob2)
        if dist == 1:
            features["dob_sim"] = 0.8
        elif dob1[5:7] == dob2[8:10] and dob1[8:10] == dob2[5:7]: # Swapped MM and DD
            features["dob_sim"] = 0.85
        else:
            features["dob_sim"] = 0.0
    else:
        features["dob_sim"] = 0.5 # Neutral weight if missing
        
    # SSN similarity
    ssn1 = re.sub(r'\D', '', p1.get("ssn" or "") or "")
    ssn2 = re.sub(r'\D', '', p2.get("ssn" or "") or "")
    if ssn1 and ssn2:
        if ssn1 == ssn2:
            features["ssn_sim"] = 1.0
        else:
            # Check for close typos
            dist = levenshtein_distance(ssn1, ssn2)
            if dist <= 2:
                features["ssn_sim"] = 0.7
            else:
                features["ssn_sim"] = -1.0 # Heavy mismatch penalty
    else:
        features["ssn_sim"] = 0.0 # Missing
        
    # Phone similarity
    ph1 = re.sub(r'\D', '', p1.get("phone" or "") or "")
    ph2 = re.sub(r'\D', '', p2.get("phone" or "") or "")
    if ph1 and ph2:
        features["phone_sim"] = 1.0 if ph1 == ph2 or ph1[-7:] == ph2[-7:] else 0.0
    else:
        features["phone_sim"] = 0.5
        
    # Email similarity
    em1 = (p1.get("email") or "").strip().lower()
    em2 = (p2.get("email") or "").strip().lower()
    if em1 and em2:
        features["email_sim"] = jaro_winkler_distance(em1, em2)
    else:
        features["email_sim"] = 0.5
        
    # Address similarity
    addr1 = (p1.get("address") or "").strip()
    addr2 = (p2.get("address") or "").strip()
    if addr1 and addr2:
        features["address_sim"] = jaro_winkler_distance(addr1, addr2)
    else:
        features["address_sim"] = 0.5

    # Classifier weighted prediction logic
    # SSN mismatch is an absolute blocker unless names match perfectly
    if features["ssn_sim"] == -1.0:
        if features["first_name_sim"] > 0.95 and features["last_name_sim"] > 0.95:
            # Maybe same person, wrong SSN entry
            probability = 0.50
        else:
            probability = 0.10
    else:
        # Weights mimicking trained XGBoost importances
        # SSN match is extremely strong
        if features["ssn_sim"] == 1.0:
            name_avg = (features["first_name_sim"] + features["last_name_sim"]) / 2
            if name_avg > 0.75 and features["dob_sim"] >= 0.8:
                probability = 0.99
            elif name_avg > 0.6:
                probability = 0.85
            else:
                probability = 0.65
        else:
            # Weighted formula
            w_first = 0.25
            w_last = 0.25
            w_dob = 0.30
            w_contact = 0.20 # combined email, phone, address
            
            contact_scores = [c for c in [features["phone_sim"], features["email_sim"], features["address_sim"]] if c != 0.5]
            contact_avg = sum(contact_scores) / len(contact_scores) if contact_scores else 0.5
            
            base_score = (
                features["first_name_sim"] * w_first +
                features["last_name_sim"] * w_last +
                features["dob_sim"] * w_dob +
                contact_avg * w_contact
            )
            
            # Penalize name mismatch
            if features["first_name_sim"] < 0.6 or features["last_name_sim"] < 0.6:
                base_score *= 0.5
                
            # Penalize DOB mismatch
            if features["dob_sim"] == 0.0:
                base_score *= 0.7
                
            probability = min(1.0, max(0.0, base_score))
            
    return round(probability, 3), features


def apply_survivorship_rules(existing: dict, incoming: dict) -> dict:
    """Merges incoming record fields with the existing Golden record based on survivorship.
    
    Longer/more complete strings survive. Missing fields get populated.
    """
    merged = existing.copy()
    
    # Names (prefer longer name string)
    if len(incoming.get("first_name", "")) > len(existing.get("first_name", "")):
        merged["first_name"] = incoming["first_name"]
    if len(incoming.get("last_name", "")) > len(existing.get("last_name", "")):
        merged["last_name"] = incoming["last_name"]
        
    # DOB (prefer exact non-null)
    if incoming.get("dob") and not existing.get("dob"):
        merged["dob"] = incoming["dob"]
        
    # SSN
    if incoming.get("ssn") and not existing.get("ssn"):
        merged["ssn"] = incoming["ssn"]
        
    # Gender
    if incoming.get("gender") and (not existing.get("gender") or existing.get("gender") == "unknown"):
        merged["gender"] = incoming["gender"]
        
    # Phone, Email, Address (prefer longer/newer)
    if incoming.get("phone") and len(incoming.get("phone", "")) >= len(existing.get("phone", "") or ""):
        merged["phone"] = incoming["phone"]
    if incoming.get("email") and len(incoming.get("email", "")) >= len(existing.get("email", "") or ""):
        merged["email"] = incoming["email"]
    if incoming.get("address") and len(incoming.get("address", "")) >= len(existing.get("address", "") or ""):
        merged["address"] = incoming["address"]
        
    return merged


async def search_duplicates_blocking(db: AsyncSession, new_patient_dict: dict) -> list[tuple[Patient, float, dict]]:
    """Uses phonetic blocking keys to query database candidates and scores them."""
    dob = new_patient_dict.get("dob", "")
    fname = new_patient_dict.get("first_name", "")
    lname = new_patient_dict.get("last_name", "")
    
    keys = get_blocking_keys(fname, lname, dob)
    
    # Query database. For SQLite, we retrieve patients, calculate block keys in Python, and score them.
    # To be performant, we only load candidate records that share first initial and DOB birth year or last name soundex.
    birth_year = dob[:4] if dob else ""
    first_init = fname[0].upper() if fname else ""
    
    # Filter candidates by birth year and first letter of first name
    stmt = select(Patient).where(Patient.dob.like(f"{birth_year}%"))
    result = await db.execute(stmt)
    all_candidates = result.scalars().all()
    
    matches = []
    seen_ids = set()
    
    for cand in all_candidates:
        if cand.id in seen_ids:
            continue
            
        cand_dict = {
            "first_name": cand.first_name,
            "last_name": cand.last_name,
            "dob": cand.dob,
            "ssn": cand.ssn,
            "phone": cand.phone,
            "email": cand.email,
            "address": cand.address
        }
        
        # Check if the blocking key matches
        cand_keys = get_blocking_keys(cand.first_name, cand.last_name, cand.dob)
        if any(k in cand_keys for k in keys):
            prob, features = calculate_match_probability(new_patient_dict, cand_dict)
            if prob >= MATCH_REVIEW_REQUIRED:
                matches.append((cand, prob, features))
                seen_ids.add(cand.id)
                
    return sorted(matches, key=lambda x: x[1], reverse=True)


async def execute_merge(db: AsyncSession, golden_patient: Patient, incoming_data: dict, source_system: str, source_patient_id: str = None) -> Patient:
    """Executes a merge of incoming patient data into the existing Golden Record."""
    existing_data = {
        "first_name": golden_patient.first_name,
        "last_name": golden_patient.last_name,
        "dob": golden_patient.dob,
        "ssn": golden_patient.ssn,
        "gender": golden_patient.gender,
        "phone": golden_patient.phone,
        "email": golden_patient.email,
        "address": golden_patient.address
    }
    
    merged = apply_survivorship_rules(existing_data, incoming_data)
    
    # Update Golden Record demographics
    golden_patient.first_name = merged["first_name"]
    golden_patient.last_name = merged["last_name"]
    golden_patient.dob = merged["dob"]
    golden_patient.ssn = merged["ssn"]
    golden_patient.gender = merged["gender"]
    golden_patient.phone = merged["phone"]
    golden_patient.email = merged["email"]
    golden_patient.address = merged["address"]
    
    # Construct updated FHIR patient object
    from backend.fhir_helper import to_fhir_patient
    updated_fhir = to_fhir_patient(merged)
    updated_fhir["id"] = golden_patient.id
    golden_patient.fhir_payload = json.dumps(updated_fhir)
    
    # Save the lineage link
    new_link = PatientLink(
        golden_patient_id=golden_patient.id,
        source_system=source_system,
        source_patient_id=source_patient_id,
        raw_payload=json.dumps(incoming_data)
    )
    db.add(new_link)
    
    # Audit log
    audit = AuditLog(
        user_id="SYSTEM_INTEGRATION",
        action="MERGE_RECORDS",
        patient_id=golden_patient.id,
        details=f"Merged incoming record from '{source_system}' (Source ID: {source_patient_id}) into Golden Record. Updated properties."
    )
    db.add(audit)
    
    await db.flush()
    return golden_patient
