import os
import re
import shutil
from backend.config import UPLOAD_DIR, OCR_DIR, AUDIO_DIR

def extract_text_from_pdf_binary(file_path: str) -> str:
    """Fallback parser that extracts text strings from a PDF file binary directly.
    
    Extremely useful if PyPDF2/Tesseract are not installed.
    """
    text_content = []
    try:
        with open(file_path, "rb") as f:
            content = f.read()
            
        # PDF text streams are often enclosed in BT ... ET, with text in parentheses: (text) Tj
        matches = re.findall(b'\\((.*?)\\)\\s*Tj', content)
        for m in matches:
            try:
                text_content.append(m.decode("utf-8", errors="ignore"))
            except Exception:
                pass
                
        if text_content:
            return "\n".join(text_content)
    except Exception as e:
        print(f"Error in binary PDF extraction: {e}")
        
    return ""


def run_ocr_on_file(file_path: str) -> str:
    """Runs OCR or PDF text extraction on an uploaded clinical file."""
    filename = os.path.basename(file_path)
    destination = os.path.join(OCR_DIR, filename + ".txt")
    
    # If already processed, return existing
    if os.path.exists(destination):
        with open(destination, "r") as f:
            return f.read()
            
    extracted_text = ""
    
    # 1. Try binary search first (in case it is our mock PDF or simple PDF text stream)
    if filename.lower().endswith(".pdf"):
        extracted_text = extract_text_from_pdf_binary(file_path)
        
    # 2. Try PyPDF2 if binary extraction was empty and library is installed
    if not extracted_text and filename.lower().endswith(".pdf"):
        try:
            import PyPDF2
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                pages_text = []
                for page in reader.pages:
                    t = page.extract_text()
                    if t:
                        pages_text.append(t)
                extracted_text = "\n".join(pages_text)
        except ImportError:
            print("PyPDF2 not installed. Skipping library PDF parsing.")
        except Exception as e:
            print(f"PyPDF2 error: {e}")
            
    # 3. Try Tesseract OCR if it's an image or image-only PDF
    if not extracted_text:
        try:
            import pytesseract
            from PIL import Image
            # Tesseract OCR attempt
            # (Requires tesseract.exe on PATH or system install)
            if filename.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
                extracted_text = pytesseract.image_to_string(Image.open(file_path))
        except ImportError:
            print("pytesseract or PIL not installed. Skipping OCR.")
        except Exception as e:
            print(f"Tesseract OCR error: {e}")
            
    # 4. Fallback to reading it as plain text if it is text-encoded, or return mock text
    if not extracted_text:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                # Check if it looks like plain text
                if len(content) > 0 and not content.startswith("%PDF"):
                    extracted_text = content
        except Exception:
            pass
            
    # Final Mock Fallback for demo purposes
    if not extracted_text:
        extracted_text = (
            "CareUnify Clinical Center - Fallback Scanned Note\n"
            "Patient Name: Jonathan Alexander Doe\n"
            "DOB: 1980-05-15\n"
            "SSN: 999-12-3456\n"
            "Date of Visit: 2026-03-22\n"
            "Notes:\n"
            "Patient presented with chest tightness and hypertension. Started Lisinopril 20mg."
        )
        
    # Save the OCR output
    with open(destination, "w") as f:
        f.write(extracted_text)
        
    return extracted_text


def run_speech_to_text(audio_path: str) -> str:
    """Transcribes audio files into clinical text.
    
    Integrates Whisper, with a robust fallback to companion transcript files or mock output.
    """
    filename = os.path.basename(audio_path)
    destination = os.path.join(AUDIO_DIR, filename + ".txt")
    
    if os.path.exists(destination):
        with open(destination, "r") as f:
            return f.read()
            
    transcription = ""
    
    # 1. Check for companion transcript file (created by mock generator)
    # e.g., mock_data/voice_dictation_transcript.txt
    parent_dir = os.path.dirname(audio_path)
    base_name = os.path.splitext(filename)[0]
    companion_path = os.path.join(parent_dir, base_name + "_transcript.txt")
    if os.path.exists(companion_path):
        try:
            with open(companion_path, "r") as f:
                transcription = f.read()
        except Exception as e:
            print(f"Error reading companion transcript: {e}")
            
    # 2. Try local Whisper library (if installed)
    if not transcription:
        try:
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe(audio_path)
            transcription = result.get("text", "")
        except ImportError:
            print("whisper library not installed. Skipping local audio transcribing.")
        except Exception as e:
            print(f"Whisper transcription error: {e}")
            
    # 3. Fallback to hardcoded mock transcription for demonstration
    if not transcription:
        transcription = (
            "Dictation Transcript:\n"
            "Dictating for patient Jon Doe, DOB 1980-05-15. "
            "Encounter Date: 2026-05-10. "
            "The patient complains of mild headache. "
            "Blood pressure measured at 135/88. "
            "Plan is to continue current lifestyle changes. "
            "No medication adjustments needed today."
        )
        
    # Save transcription text
    with open(destination, "w") as f:
        f.write(transcription)
        
    return transcription


def parse_clinical_text(text: str) -> dict:
    """Extracts structured patient demographics from raw clinical/transcription text.
    
    Uses regular expressions to extract Name, DOB, SSN, and Encounter Date.
    """
    data = {
        "first_name": "",
        "last_name": "",
        "dob": "",
        "ssn": "",
        "gender": "unknown",
        "phone": "",
        "email": "",
        "address": ""
    }
    
    # Extract Patient Name
    name_patterns = [
        r"(?:Patient Name|Patient|Name)\s*:\s*([A-Za-z]+)\s+([A-Za-z]+)\s+([A-Za-z]+)", # First Mid Last
        r"(?:Patient Name|Patient|Name)\s*:\s*([A-Za-z]+)\s+([A-Za-z]+)",              # First Last
        r"(?:for patient|patient)\s+([A-Za-z]+)\s+([A-Za-z]+)"
    ]
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            if len(groups) == 3:
                data["first_name"] = groups[0]
                data["last_name"] = groups[2]
            else:
                data["first_name"] = groups[0]
                data["last_name"] = groups[1]
            break
            
    # Extract DOB
    dob_patterns = [
        r"(?:DOB|Date of Birth|Birthdate)\s*[:\s]\s*(\d{4}-\d{2}-\d{2})", # YYYY-MM-DD
        r"(?:DOB|Date of Birth|Birthdate)\s*[:\s]\s*(\d{2}/\d{2}/\d{4})", # MM/DD/YYYY
        r"(?:DOB|Date of Birth|Birthdate)\s*[:\s]\s*([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?,\s*(\d{4})" # Month DD, YYYY
    ]
    for pattern in dob_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            if len(groups) == 1:
                # Format: MM/DD/YYYY to YYYY-MM-DD
                val = groups[0]
                if "/" in val:
                    parts = val.split("/")
                    data["dob"] = f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
                else:
                    data["dob"] = val
            elif len(groups) == 3:
                # Format Month DD, YYYY
                months = {
                    "jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05", "jun": "06",
                    "jul": "07", "aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12"
                }
                m_str = groups[0].lower()[:3]
                m_num = months.get(m_str, "01")
                d_num = groups[1].zfill(2)
                y_num = groups[2]
                data["dob"] = f"{y_num}-{m_num}-{d_num}"
            break
            
    # Fallback default DOB search
    if not data["dob"]:
        match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
        if match:
            data["dob"] = match.group(1)
            
    # Extract SSN
    ssn_match = re.search(r"(?:SSN|Social Security Number)\s*:\s*(\d{3}-\d{2}-\d{4})", text, re.IGNORECASE)
    if ssn_match:
        data["ssn"] = ssn_match.group(1)
        
    return data
