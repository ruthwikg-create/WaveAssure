"""Start the local research workbench; open a browser ONLY after health passes.

STDOUT/STDERR are kept in the foreground so Windows users see real startup
tracebacks instead of mistaking an early refused connection for a broken UI.
Never expose this unauthenticated prototype outside 127.0.0.1.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import sys
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
import webbrowser

ROOT = Path(__file__).resolve().parent.parent
HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}"
HEALTH = URL + "/api/health"


def probe_health() -> dict | None:
    """Accept only WaveAssure's local research API health response."""
    try:
        with urlopen(HEALTH, timeout=0.6) as response:
            if response.status != 200:
                return None
            data = json.load(response)
    except (OSError, HTTPError, URLError, ValueError, TimeoutError):
        return None
    if (isinstance(data, dict) and data.get("status") == "ok"
            and data.get("intended_use") == "research_only"
            and isinstance(data.get("version"), str)):
        return data
    return None


def port_in_use() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.6)
        return sock.connect_ex((HOST, PORT)) == 0


def open_browser_when_ready() -> None:
    # Keep browser launch off the server thread. Never launch before health OK.
    for _ in range(60):
        health = probe_health()
        if health and health.get("workspace_mode") == "engineering":
            print(f"[WaveAssure] READY - v{health['version']} at {URL}", flush=True)
            print("[WaveAssure] Keep this console open. Ctrl+C stops the server.", flush=True)
            try:
                opened = webbrowser.open(URL, new=2)
                if not opened:
                    print(f"[WaveAssure] Browser did not open automatically. Visit {URL}", flush=True)
            except Exception as exc:
                print(f"[WaveAssure] Browser launch failed ({exc}). Visit {URL}", flush=True)
            return
        time.sleep(0.5)
    print("[WaveAssure] WARNING: Startup health not confirmed. Review any errors above.", flush=True)


def main() -> int:
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))
    if port_in_use():
        health = probe_health()
        if health and health.get("workspace_mode") == "engineering":
            print(f"[WaveAssure] Existing local research server detected: {URL}", flush=True)
            webbrowser.open(URL, new=2)
            return 0
        print("[WaveAssure] ERROR: Port 8000 is occupied by another service or unavailable mode.", flush=True)
        print("[WaveAssure] Run: Get-NetTCPConnection -LocalPort 8000 -State Listen", flush=True)
        return 1
    print("[WaveAssure] Loading application. Browser will open after the health check.", flush=True)
    threading.Thread(target=open_browser_when_ready, name="WaveAssureHealthGate", daemon=True).start()
    try:
        import uvicorn
        uvicorn.run("waveassure.api:app", host=HOST, port=PORT, log_level="info")
    except (ImportError, OSError) as exc:
        print(f"[WaveAssure] ERROR: Server startup failed: {exc}", file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
