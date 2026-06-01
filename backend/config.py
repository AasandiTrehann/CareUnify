import os

# Base paths
BASE_DIR = "c:/Users/Aasandi/OneDrive/Desktop/CareUnify"
DB_PATH = os.path.join(BASE_DIR, "careunify.db")
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"
SYNC_DATABASE_URL = f"sqlite:///{DB_PATH}"

# Directory structures for file storage
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
UPLOAD_DIR = os.path.join(STORAGE_DIR, "uploads")
OCR_DIR = os.path.join(STORAGE_DIR, "ocr_output")
AUDIO_DIR = os.path.join(STORAGE_DIR, "audio_records")

for d in [STORAGE_DIR, UPLOAD_DIR, OCR_DIR, AUDIO_DIR]:
    os.makedirs(d, exist_ok=True)

# Entity Resolution Thresholds
MATCH_AUTO_MERGE = 0.85
MATCH_REVIEW_REQUIRED = 0.60

# LLM & RAG Configuration
OLLAMA_API_URL = os.environ.get("OLLAMA_API_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")

# Security configurations
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "careunify_super_secret_dev_key_32_bytes_long_=")
