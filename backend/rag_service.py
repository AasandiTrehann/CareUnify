import os
import json
import re
import urllib.request
import urllib.error
from datetime import datetime
from backend.config import OLLAMA_API_URL, OLLAMA_MODEL

# Try importing SentenceTransformer. If it fails, we fall back to a keyword-based retriever.
SENTENCE_TRANSFORMERS_AVAILABLE = False
try:
    from sentence_transformers import SentenceTransformer
    # Load model lazily
    embedding_model = None
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    print("sentence-transformers not installed. Falling back to keyword search for RAG.")
    embedding_model = None

# A simple in-memory vector store database
# Format: [ { "id": str, "patient_id": str, "text": str, "embedding": list[float], "metadata": dict } ]
VECTOR_DATABASE = []

def get_embedding(text: str) -> list[float]:
    """Generates float vector embedding using SentenceTransformer (or mock embedding fallback)."""
    global embedding_model
    if SENTENCE_TRANSFORMERS_AVAILABLE:
        try:
            if embedding_model is None:
                embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            vector = embedding_model.encode(text)
            return vector.tolist()
        except Exception as e:
            print(f"Error generating SentenceTransformer embedding: {e}")
            
    # Mock embedding fallback: generate a basic pseudo-vector based on character frequencies
    # 384 dimensions to match all-MiniLM-L6-v2
    vec = [0.0] * 384
    cleaned = re.sub(r'[^a-z]', '', text.lower())
    for char in cleaned:
        idx = ord(char) % 384
        vec[idx] += 1.0
        
    # Normalize vector
    norm = sum(x**2 for x in vec) ** 0.5
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Computes cosine similarity between two float vectors."""
    if len(v1) != len(v2) or not v1:
        return 0.0
    dot_product = sum(x * y for x, y in zip(v1, v2))
    norm1 = sum(x**2 for x in v1) ** 0.5
    norm2 = sum(x**2 for x in v2) ** 0.5
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)


def deidentify_text(text: str, patient_demographics: dict) -> str:
    """HIPAA compliance filter: redacts/anonymizes patient names, phone, email, and SSN.
    
    Replaces sensitive clinical data with de-identified tokens.
    """
    scrubbed = text
    
    # 1. SSN
    ssn = patient_demographics.get("ssn")
    if ssn:
        scrubbed = scrubbed.replace(ssn, "[REDACTED_SSN]")
        raw_ssn = re.sub(r'\D', '', ssn)
        if len(raw_ssn) == 9:
            scrubbed = scrubbed.replace(raw_ssn, "[REDACTED_SSN]")
            
    # 2. Phone
    phone = patient_demographics.get("phone")
    if phone:
        scrubbed = scrubbed.replace(phone, "[REDACTED_PHONE]")
        raw_phone = re.sub(r'\D', '', phone)
        if len(raw_phone) >= 7:
            scrubbed = scrubbed.replace(raw_phone, "[REDACTED_PHONE]")
            
    # 3. Email
    email = patient_demographics.get("email")
    if email:
        scrubbed = scrubbed.replace(email, "[REDACTED_EMAIL]")
        
    # 4. Names
    fname = patient_demographics.get("first_name")
    lname = patient_demographics.get("last_name")
    
    if fname and len(fname) > 1:
        # Match word boundaries case insensitively
        scrubbed = re.sub(rf"\b{fname}\b", "[PATIENT_FIRST_NAME]", scrubbed, flags=re.IGNORECASE)
    if lname and len(lname) > 1:
        scrubbed = re.sub(rf"\b{lname}\b", "[PATIENT_LAST_NAME]", scrubbed, flags=re.IGNORECASE)
        
    return scrubbed


def index_clinical_resource(resource_id: str, patient_id: str, text: str, metadata: dict, patient_demographics: dict):
    """De-identifies and indexes clinical text into the vector database."""
    # Apply HIPAA compliance scrubbing
    de_id_text = deidentify_text(text, patient_demographics)
    
    embedding = get_embedding(de_id_text)
    
    # Check if already exists, overwrite if yes
    for idx, entry in enumerate(VECTOR_DATABASE):
        if entry["id"] == resource_id:
            VECTOR_DATABASE[idx] = {
                "id": resource_id,
                "patient_id": patient_id,
                "text": de_id_text,
                "embedding": embedding,
                "metadata": metadata
            }
            return
            
    VECTOR_DATABASE.append({
        "id": resource_id,
        "patient_id": patient_id,
        "text": de_id_text,
        "embedding": embedding,
        "metadata": metadata
    })


def delete_patient_embeddings(patient_id: str):
    """GDPR Right-to-Erasure compliance: purges all stored vector search embeddings for patient."""
    global VECTOR_DATABASE
    VECTOR_DATABASE = [entry for entry in VECTOR_DATABASE if entry["patient_id"] != patient_id]


def retrieve_relevant_contexts(patient_id: str, query: str, top_k: int = 4) -> list[dict]:
    """Retrieves relevant contexts for a specific patient using semantic or keyword search."""
    # Filter embeddings matching this patient
    patient_records = [entry for entry in VECTOR_DATABASE if entry["patient_id"] == patient_id]
    if not patient_records:
        return []
        
    query_emb = get_embedding(query)
    
    scored_records = []
    for entry in patient_records:
        sim = cosine_similarity(query_emb, entry["embedding"])
        
        # Keyword boost: if query keywords are in the text, boost similarity
        keywords = re.findall(r'\b\w{4,}\b', query.lower())
        kw_matches = sum(1 for kw in keywords if kw in entry["text"].lower())
        if keywords and kw_matches > 0:
            sim += (kw_matches / len(keywords)) * 0.1
            
        scored_records.append((entry, sim))
        
    scored_records = sorted(scored_records, key=lambda x: x[1], reverse=True)
    return [item[0] for item in scored_records[:top_k]]


def query_ollama(prompt: str) -> str:
    """Queries local Ollama Llama 3 instance using standard urllib."""
    url = f"{OLLAMA_API_URL}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }
    
    headers = {"Content-Type": "application/json"}
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=12) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)
            return res_json.get("response", "")
    except urllib.error.URLError as e:
        print(f"Ollama connection error: {e}")
    except Exception as e:
        print(f"Ollama execution error: {e}")
        
    return ""


def run_clinical_query(patient_id: str, query: str, patient_demographics: dict) -> dict:
    """Performs RAG to retrieve patient context and generates synthesized responses."""
    # 1. Retrieve contexts
    contexts = retrieve_relevant_contexts(patient_id, query)
    
    # 2. Assemble context strings
    context_str = ""
    sources = []
    
    for i, ctx in enumerate(contexts):
        m = ctx["metadata"]
        src_sys = m.get("source_system", "EHR")
        res_type = m.get("resource_type", "Record")
        date = m.get("date", "unknown date")
        
        context_str += f"[{i+1}] [{date}] Source: {src_sys} | Type: {res_type} - Content: {ctx['text']}\n"
        sources.append({
            "resource_id": ctx["id"],
            "text": ctx["text"],
            "source_system": src_sys,
            "resource_type": res_type,
            "date": date
        })
        
    # De-identify the query itself to protect PHI
    clean_query = deidentify_text(query, patient_demographics)
    
    # 3. Create Ollama System Prompt
    system_prompt = (
        "You are an AI Clinical Intel Assistant for CareUnify. "
        "Analyze the de-identified patient clinical records provided in the Context section and answer the Clinician's Query.\n"
        "Rules:\n"
        "1. Answer based ONLY on the provided Context. If the context does not contain the answer, say that you cannot find it.\n"
        "2. Cite the context sources using numbers (e.g., [1], [2]) at the end of statements where they apply.\n"
        "3. Do not include or make up any patient names or identifying SSNs/emails. Use placeholders like [Patient] if necessary.\n"
        "4. Be concise and professional in clinical summaries.\n\n"
        f"Context:\n{context_str or 'No medical history found.'}\n\n"
        f"Clinician's Query: {clean_query}\n\n"
        "Summary Response:"
    )
    
    # 4. Invoke LLM or Fallback
    model_response = query_ollama(system_prompt)
    is_fallback = False
    
    if not model_response:
        is_fallback = True
        # Keyword-based summarizer fallback when Ollama is offline
        model_response = synthesize_fallback_response(clean_query, contexts)
        
    return {
        "summary": model_response,
        "sources": sources,
        "is_fallback": is_fallback
    }


def synthesize_fallback_response(query: str, contexts: list[dict]) -> str:
    """Generates simple clinical summaries in pure Python when Ollama is offline."""
    query_lower = query.lower()
    
    lines = [
        "[Notice: Ollama Llama 3 was offline. Synthesizing offline clinical analysis based on search query matching...]",
        ""
    ]
    
    if not contexts:
        lines.append("No patient medical records were found in the database matching this profile.")
        return "\n".join(lines)
        
    lines.append("Based on patient records retrieved from the database, here is a summary of matches:")
    
    matched_any = False
    for i, ctx in enumerate(contexts):
        text = ctx["text"]
        m = ctx["metadata"]
        src = m.get("source_system", "EHR")
        date = m.get("date", "unknown")
        
        # Search for key terms (medication, cholesterol, BP, lab)
        keywords = ["medication", "prescrib", "mg", "blood", "pressure", "cholesterol", "hdl", "ldl", "a1c", "chest", "pain", "headache"]
        matched_kws = [kw for kw in keywords if kw in text.lower() or kw in query_lower]
        
        if matched_kws or any(w in text.lower() for w in query_lower.split()):
            lines.append(f"- On {date} ({src}): {text} [{i+1}]")
            matched_any = True
            
    if not matched_any:
        lines.append("No active prescriptions or metrics directly matched the query words, but the following history exists:")
        for i, ctx in enumerate(contexts):
            lines.append(f"- On {ctx['metadata'].get('date')} ({ctx['metadata'].get('source_system')}): {ctx['text']} [{i+1}]")
            
    return "\n".join(lines)
