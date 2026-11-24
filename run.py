import sys
import subprocess
import os
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def run_backend(port=8000):
    print(f"[*] Starting FastAPI backend on http://0.0.0.0:{port}...")
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)

def run_frontend(port=8501):
    print(f"[*] Starting Streamlit frontend on http://localhost:{port}...")
    frontend_path = str(BASE_DIR / "frontend" / "app.py")
    subprocess.run([
        sys.executable,
        "-m",
        "streamlit",
        "run",
        frontend_path,
        "--server.port",
        str(port),
        "--server.address",
        "0.0.0.0",
        "--server.headless",
        "true"
    ])

def run_both():
    import threading
    print("[*] Launching both FastAPI backend and Streamlit frontend concurrently...")
    
    t_backend = threading.Thread(target=run_backend, args=(8000,), daemon=True)
    t_backend.start()
    
    # Run frontend in main thread
    run_frontend(8501)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-Tool AI Agent Service Launcher")
    parser.add_argument("service", choices=["backend", "frontend", "both"], default="both", nargs="?", help="Which service to launch")
    parser.add_argument("--port", type=int, default=None, help="Port override")
    
    args = parser.parse_args()
    
    if args.service == "backend":
        run_backend(port=args.port or 8000)
    elif args.service == "frontend":
        run_frontend(port=args.port or 8501)
    else:
        run_both()
