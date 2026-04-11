FROM python:3.10-slim

# Install system dependencies for OCR and STT
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set PYTHONPATH to include the current directory for absolute imports
ENV PYTHONPATH=/app

CMD ["uvicorn", "careunify.services.ingestion.main:app", "--host", "0.0.0.0", "--port", "8000"]
