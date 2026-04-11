import requests
import os

BASE_URL = "http://localhost:8000"

def test_csv_upload():
    print("\n[1] Testing CSV Upload...")
    file_path = "samples/patients.csv"
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        return

    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, "text/csv")}
        params = {"resource_type": "Patient"}
        response = requests.post(f"{BASE_URL}/ingest/file", files=files, params=params)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

def test_hl7_upload():
    print("\n[2] Testing HL7 Upload...")
    file_path = "samples/message.hl7"
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        return

    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, "application/hl7-v2")}
        response = requests.post(f"{BASE_URL}/ingest/file", files=files)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

def test_rest_patient():
    print("\n[3] Testing REST Patient Ingestion...")
    patient_data = {
        "name": [{"family": "Doe", "given": ["John"]}],
        "gender": "male",
        "birthDate": "1980-01-01"
    }
    response = requests.post(f"{BASE_URL}/ingest/rest/Patient", json=patient_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    try:
        test_csv_upload()
        test_hl7_upload()
        test_rest_patient()
        print("\n✅ All tests completed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("Make sure the server is running at http://localhost:8000")
