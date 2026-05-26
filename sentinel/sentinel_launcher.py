import sys
import subprocess
import time
import urllib.request
from pathlib import Path

import webview

BASE_DIR   = Path(__file__).parent   # sentinel/
PARENT_DIR = BASE_DIR.parent         # Agentive Workflows/
APP_PY     = BASE_DIR / "app.py"
PORT       = 8502
URL        = f"http://localhost:{PORT}"


def _wait(timeout=30):
    for _ in range(timeout * 2):
        try:
            urllib.request.urlopen(URL, timeout=1)
            return
        except Exception:
            time.sleep(0.5)


proc = subprocess.Popen(
    [
        sys.executable, "-m", "streamlit", "run", str(APP_PY),
        "--server.port", str(PORT),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
    ],
    cwd=str(PARENT_DIR),
)

_wait()

webview.create_window(
    "Sentinel — Security Dashboard",
    URL,
    width=1400,
    height=900,
    min_size=(900, 600),
)
webview.start()

proc.terminate()
proc.wait()
