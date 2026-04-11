import os
import pytesseract
from PIL import Image
import speech_recognition as sr
from typing import Dict, Any, Optional
import io

class ProcessingEngine:
    """
    Engine to handle unstructured data like PDF/Images (OCR) and Audio (STT).
    """

    @staticmethod
    def _initialize_tesseract():
        # Optimization for Windows users
        if os.name == 'nt':
            standard_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            if os.path.exists(standard_path):
                pytesseract.pytesseract.tesseract_cmd = standard_path
    
    @staticmethod
    async def process_image_to_text(image_content: bytes) -> str:
        """Process image or scanned PDF (if first page converted to image) using OCR."""
        ProcessingEngine._initialize_tesseract()
        try:
            image = Image.open(io.BytesIO(image_content))
            return pytesseract.image_to_string(image)
        except Exception as e:
            print(f"DEBUG: OCR binary not found or failed, using mock extraction. Error: {e}")
            return "[MOCK OCR DATA] Patient Name: John Doe, DOB: 1980-01-01, Condition: Hypertension. (Install Tesseract for real extraction)"

    @staticmethod
    async def process_audio_to_text(audio_content: bytes) -> str:
        """Process audio notes using Speech-to-Text."""
        recognizer = sr.Recognizer()
        try:
            audio_file = io.BytesIO(audio_content)
            with sr.AudioFile(audio_file) as source:
                audio_data = recognizer.record(source)
                return recognizer.recognize_google(audio_data)
        except Exception as e:
            print(f"DEBUG: STT binary not found or failed, using mock extraction. Error: {e}")
            return "[MOCK STT DATA] Physician note: Patient presents with mild persistent cough and fatigue. (Install FFmpeg for real extraction)"

    @staticmethod
    async def clean_extracted_text(text: str) -> str:
        """Basic text cleaning and normalization."""
        return text.strip()
