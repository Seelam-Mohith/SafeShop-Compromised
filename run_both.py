#!/usr/bin/env python3
\"\"\"
Run both websites together (localhost only).
- Legitimate site: http://127.0.0.1:5000
- Suspicious site: http://127.0.0.1:5001
Both write to logs/web_logs.csv
\"\"\"
import os
import sys
import subprocess
import time

ROOT = os.path.abspath(os.path.dirname(__file__))
LEGIT = os.path.join(ROOT, "sites", "legitimate")
SUSP = os.path.join(ROOT, "sites", "suspicious")

def main():
    env_legit = os.environ.copy()
    env_legit["PYTHONPATH"] = ROOT + os.pathsep + LEGIT + (os.pathsep + env_legit.get("PYTHONPATH", ""))
    env_susp = os.environ.copy()
    env_susp["PYTHONPATH"] = ROOT + os.pathsep + SUSP + (os.pathsep + env_susp.get("PYTHONPATH", ""))
    
    print("Starting SafeShop (legitimate) on http://127.0.0.1:5000")
    p1 = subprocess.Popen([sys.executable, "app.py"], cwd=LEGIT, env=env_legit)
    time.sleep(1)
    print("Starting SafeShop (suspicious) on http://127.0.0.1:5001")
    p2 = subprocess.Popen([sys.executable, "app.py"], cwd=SUSP, env=env_susp)
    print("Both started. Press Ctrl+C to stop.")
    try:
        p1.wait()
        p2.wait()
    except KeyboardInterrupt:
        p1.terminate()
        p2.terminate()
        print("\\nStopped.")

if __name__ == "__main__":
    main()
