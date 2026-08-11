import os
import sys
import subprocess
import time

def main():
    print("\n========================================")
    print("   LegalBuddy — Microservices Dev Mode")
    print("========================================\n")
    print("Starting all services...")
    print("  Auth Service     -> http://localhost:8001")
    print("  Document Service -> http://localhost:8002")
    print("  RAG Service      -> http://localhost:8003")
    print("  API Gateway      -> http://localhost:5000\n")
    print("Frontend still runs on http://localhost:5173 (npm run dev)\n")

    import platform
    is_windows = platform.system() == "Windows"
    
    if is_windows:
        venv_python = os.path.join("venv", "Scripts", "python.exe")
    else:
        venv_python = os.path.join("venv", "bin", "python")

    if not os.path.exists(venv_python):
        print(f"Warning: Virtual environment not found at {venv_python}. Install dependencies first.")
        sys.exit(1)

    cwd = os.getcwd()
    env = os.environ.copy()
    env["PYTHONPATH"] = cwd
    
    processes = []

    def start_service(module, port):
        if is_windows:
            cmd = f'start cmd /k "{venv_python} -m uvicorn {module} --host 0.0.0.0 --port {port} --reload"'
            subprocess.Popen(cmd, shell=True, env=env)
        else:
            cmd = [venv_python, "-m", "uvicorn", module, "--host", "0.0.0.0", "--port", str(port), "--reload"]
            p = subprocess.Popen(cmd, env=env)
            processes.append(p)

    start_service("services.auth_service.main:app", 8001)
    start_service("services.document_service.main:app", 8002)
    start_service("services.rag_service.main:app", 8003)
    
    time.sleep(3)
    
    start_service("services.api_gateway.main:app", 5000)

    if is_windows:
        print("\nAll services launched in separate windows!")
        print("Close each window to stop individual services.")
    else:
        print("\nAll services launched in the background! Press Ctrl+C to stop all services.")
        try:
            for p in processes:
                p.wait()
        except KeyboardInterrupt:
            print("\nStopping all services...")
            for p in processes:
                p.terminate()

if __name__ == "__main__":
    main()
