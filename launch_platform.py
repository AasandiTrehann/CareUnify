import subprocess
import time
import os

def main():
    print("=== CareUnify Platform Orchestrator (V3 - Multi-Window) ===\n")
    print("🚀 Launching backends in separate windows for maximum stability...")
    
    # 0. Auth Service (Port 5000 - Node.js)
    if not os.path.exists("careunify/services/auth/node_modules"):
        print("⚠️ Installing Auth dependencies first...")
        subprocess.run("npm install", shell=True, cwd="careunify/services/auth")

    # Command to open a new terminal window on Windows: "start cmd /k <command>"
    # /k keeps the window open after the service finishes so you can see errors
    
    services = {
        "Auth [5000]": "start cmd /k node server.js",
        "Ingestion [8000]": "start cmd /k python -m uvicorn careunify.services.ingestion.main:app --port 8000",
        "Resolution [8001]": "start cmd /k python -m uvicorn careunify.services.resolution.main:app --port 8001",
        "Intelligence [8002]": "start cmd /k python -m uvicorn careunify.services.intelligence.main:app --port 8002",
        "Dashboard [UI]": "start cmd /k npm run dev"
    }

    # Launch Auth specifically
    print("- Launching Auth...")
    subprocess.Popen(services["Auth [5000]"], shell=True, cwd="careunify/services/auth")
    
    # Launch Python microservices
    print("- Launching Microservices...")
    subprocess.Popen(services["Ingestion [8000]"], shell=True)
    subprocess.Popen(services["Resolution [8001]"], shell=True)
    subprocess.Popen(services["Intelligence [8002]"], shell=True)
    
    # Launch Frontend
    print("- Launching UI Dashboard...")
    subprocess.Popen(services["Dashboard [UI]"], shell=True, cwd="careunify_ui")
    
    print("\n✅ ALL SERVICES DISPATCHED.")
    print("Check the new windows appearing on your taskbar!")
    print("--------------------------------------------------")
    print("Dashboard will be available at: http://localhost:5173")

if __name__ == "__main__":
    main()
