import sys
import os
import shutil
import subprocess

def check_command(cmd):
    return shutil.which(cmd) is not None

def check_python_imports():
    required = ["fastapi", "fhir.resources", "hl7", "motor", "pytesseract", "speech_recognition", "pandas"]
    missing = []
    for lib in required:
        try:
            __import__(lib.replace("-", "_"))
        except ImportError:
            missing.append(lib)
    return missing

def main():
    print("=== CareUnify Phase One Setup Check ===")
    
    # 1. External Binaries
    print(f"\n[1] Checking System Binaries:")
    tesseract_ok = check_command("tesseract")
    print(f" - Tesseract OCR: {'OK' if tesseract_ok else 'MISSING'}")
    if not tesseract_ok:
        print("   -> Tip: Install Tesseract for OCR support: https://github.com/UB-Mannheim/tesseract/wiki")
        
    ffmpeg_ok = check_command("ffmpeg")
    print(f" - FFmpeg: {'OK' if ffmpeg_ok else 'MISSING'}")
    if not ffmpeg_ok:
        print("   -> Tip: Install FFmpeg for Audio support: https://ffmpeg.org/download.html")

    # 2. Python Environment
    print(f"\n[2] Checking Python Packages:")
    missing = check_python_imports()
    if not missing:
        print(" - All required Python packages are installed.")
    else:
        print(f" - MISSING: {', '.join(missing)}")
        print("   -> Tip: Run 'pip install -r requirements.txt'")

    # 3. Project Structure
    print(f"\n[3] Checking Project Structure:")
    files = ["careunify/services/ingestion/main.py", "careunify/shared/models.py", ".env"]
    for f in files:
        print(f" - {f}: {'OK' if os.path.exists(f) else 'MISSING'}")

    print("\n=======================================")
    if not tesseract_ok or not ffmpeg_ok or missing:
        print("WARNING: Some components are missing. The system might have limited functionality.")
    else:
        print("SUCCESS: System is ready for Phase One.")

if __name__ == "__main__":
    main()
