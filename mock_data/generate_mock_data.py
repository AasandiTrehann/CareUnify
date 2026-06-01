import os
import json
import csv
import struct

def make_dirs():
    os.makedirs("c:/Users/Aasandi/OneDrive/Desktop/CareUnify/mock_data", exist_ok=True)

def generate_ehr_1():
    # EHR Record 1: Primary John Doe
    data = {
        "resourceType": "Patient",
        "identifier": [
            {
                "system": "http://hl7.org/fhir/sid/us-ssn",
                "value": "999-12-3456"
            }
        ],
        "name": [
            {
                "use": "official",
                "family": "Doe",
                "given": ["John", "Alexander"]
            }
        ],
        "telecom": [
            {
                "system": "phone",
                "value": "555-0192",
                "use": "home"
            },
            {
                "system": "email",
                "value": "john.doe@email.com"
            }
        ],
        "gender": "male",
        "birthDate": "1980-05-15",
        "address": [
            {
                "line": ["123 Main St"],
                "city": "Springfield",
                "state": "IL",
                "postalCode": "62701"
            }
        ]
    }
    with open("c:/Users/Aasandi/OneDrive/Desktop/CareUnify/mock_data/ehr_record_1.json", "w") as f:
        json.dump(data, f, indent=2)

def generate_ehr_2():
    # EHR Record 2: Misspelled "Jon Doe" from clinic B, slightly different phone, missing SSN, same DOB
    data = {
        "resourceType": "Patient",
        "name": [
            {
                "use": "official",
                "family": "Doe",
                "given": ["Jon"]
            }
        ],
        "telecom": [
            {
                "system": "phone",
                "value": "555-0199",
                "use": "mobile"
            },
            {
                "system": "email",
                "value": "jdoe80@email.com"
            }
        ],
        "gender": "male",
        "birthDate": "1980-05-16",
        "address": [
            {
                "line": ["123 Main Street"],
                "city": "Springfield",
                "state": "IL",
                "postalCode": "62701"
            }
        ]
    }
    with open("c:/Users/Aasandi/OneDrive/Desktop/CareUnify/mock_data/ehr_record_2.json", "w") as f:
        json.dump(data, f, indent=2)

def generate_lab_csv():
    # Lab CSV dataset: "Jonathan Doe" with clinical observations
    rows = [
        ["FirstName", "LastName", "DOB", "SSN", "Gender", "Phone", "Email", "LabTest", "Result", "Unit", "Date"],
        ["Jonathan", "Doe", "1980-05-15", "999-12-3456", "male", "555-0192", "john.doe@email.com", "A1C", "6.2", "%", "2026-01-15"],
        ["Jonathan", "Doe", "1980-05-15", "999-12-3456", "male", "555-0192", "john.doe@email.com", "Cholesterol", "210", "mg/dL", "2026-01-15"],
        ["Jonathan", "Doe", "1980-05-15", "999-12-3456", "male", "555-0192", "john.doe@email.com", "HDL", "45", "mg/dL", "2026-01-15"],
        ["Jonathan", "Doe", "1980-05-15", "999-12-3456", "male", "555-0192", "john.doe@email.com", "LDL", "135", "mg/dL", "2026-01-15"]
    ]
    with open("c:/Users/Aasandi/OneDrive/Desktop/CareUnify/mock_data/lab_results.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

def generate_pdf_note():
    # Create a plain-text representation of a PDF note. We'll write standard text but save with PDF extension.
    # To keep it robust against standard PDF parsers, we write a simple valid PDF structure containing the note text.
    # The note describes an encounter and clinical history.
    pdf_content = (
        "%PDF-1.4\n"
        "1 0 obj <</Type/Catalog/Pages 2 0 R>> endobj\n"
        "2 0 obj <</Type/Pages/Kids[3 0 R]/Count 1>> endobj\n"
        "3 0 obj <</Type/Page/Parent 2 0 R/MediaBox[0 0 595 842]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>> endobj\n"
        "4 0 obj <</Length 285>> stream\n"
        "BT\n"
        "/F1 12 Tf\n"
        "70 800 Td\n"
        "(CareUnify Clinical Health Center - Scanned Document) Tj\n"
        "0 -20 Td (Patient Name: Jonathan Alexander Doe) Tj\n"
        "0 -20 Td (DOB: 05/15/1980   SSN: 999-12-3456) Tj\n"
        "0 -20 Td (Date of Encounter: 2026-03-22) Tj\n"
        "0 -40 Td (Clinical Notes:) Tj\n"
        "0 -20 Td (Patient reports mild chest pain and shortness of breath when exercising.) Tj\n"
        "0 -20 Td (Diagnosed with essential hypertension. Prescribed Lisinopril 20mg daily.) Tj\n"
        "0 -20 Td (Advised low sodium diet. Return in 3 months for blood pressure check.) Tj\n"
        "ET\n"
        "endstream\n"
        "endobj\n"
        "5 0 obj <</Type/Font/Subtype/Type1/BaseFont/Helvetica>> endobj\n"
        "xref\n"
        "0 6\n"
        "0000000000 65535 f\n"
        "0000000009 00000 n\n"
        "0000000056 00000 n\n"
        "0000000111 00000 n\n"
        "0000000222 00000 n\n"
        "0000000556 00000 n\n"
        "trailer <</Size 6/Root 1 0 R>>\n"
        "startxref\n"
        "625\n"
        "%%EOF\n"
    )
    # We will write this as bytes
    with open("c:/Users/Aasandi/OneDrive/Desktop/CareUnify/mock_data/scanned_note.pdf", "wb") as f:
        f.write(pdf_content.encode("ascii"))

def generate_voice_note():
    # Write a simple dummy WAV file (silence, 8000 Hz, 8-bit mono, 1 second).
    # Header format for standard WAV:
    # ChunkID ('RIFF') -> size -> Format ('WAVE')
    # Subchunk1ID ('fmt ') -> Subchunk1Size (16) -> AudioFormat (1 for PCM) -> NumChannels (1)
    # SampleRate (8000) -> ByteRate (8000) -> BlockAlign (1) -> BitsPerSample (8)
    # Subchunk2ID ('data') -> Subchunk2Size (8000) -> 8000 bytes of data (128 for silence in 8-bit PCM)
    
    num_samples = 8000
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + num_samples,
        b"WAVE",
        b"fmt ",
        16,
        1, # PCM
        1, # Mono
        8000, # Sample rate
        8000, # Byte rate
        1, # Block align
        8, # Bits per sample
        b"data",
        num_samples
    )
    data = bytes([128] * num_samples) # 128 is silence mid-point in unsigned 8-bit PCM
    
    with open("c:/Users/Aasandi/OneDrive/Desktop/CareUnify/mock_data/voice_dictation.wav", "wb") as f:
        f.write(header + data)
        
    # We also write a companion transcript text file so our OCR/Speech service can do a robust fallback
    transcript_content = (
        "Dictation Transcript:\n"
        "Dictating for patient Jon Doe, DOB 1980-05-15. "
        "Encounter Date: 2026-05-10. "
        "The patient complains of mild headache. "
        "Blood pressure measured at 135/88. "
        "Plan is to continue current lifestyle changes. "
        "No medication adjustments needed today."
    )
    with open("c:/Users/Aasandi/OneDrive/Desktop/CareUnify/mock_data/voice_dictation_transcript.txt", "w") as f:
        f.write(transcript_content)

def main():
    make_dirs()
    generate_ehr_1()
    generate_ehr_2()
    generate_lab_csv()
    generate_pdf_note()
    generate_voice_note()
    print("Mock data generated successfully in c:/Users/Aasandi/OneDrive/Desktop/CareUnify/mock_data/")

if __name__ == "__main__":
    main()
