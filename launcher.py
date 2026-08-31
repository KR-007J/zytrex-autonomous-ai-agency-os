#!/usr/bin/env python3
"""Turnkey Standalone AI Agency Desktop Application Launcher."""

from __future__ import annotations
import sys
import os
import time
import webbrowser
import threading
import subprocess
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.database.db import init_db


def open_browser_delayed(url: str, delay: float = 1.5):
    """Wait for server startup and open default browser window."""
    time.sleep(delay)
    print(f"🚀 Opening Autonomous AI Agency Mission Control at: {url}")
    try:
        webbrowser.open(url)
    except Exception:
        pass


def main():
    print("=" * 70)
    print(" ⚡ AUTONOMOUS AI AGENCY OPERATING SYSTEM — ENTERPRISE TURNKEY EDITION")
    print("=" * 70)
    print(" Initializing local databases, security shields, and Excel engine...")

    config = load_config()
    init_db(config.app.database_url)

    host = config.app.host or "127.0.0.1"
    port = config.app.port or 8000
    url = f"http://{host}:{port}"

    # Open client UI in background thread
    threading.Thread(target=open_browser_delayed, args=(url,), daemon=True).start()

    import uvicorn
    uvicorn.run("src.api.main:app", host=host, port=port, log_level="info", reload=False)


if __name__ == "__main__":
    main()
