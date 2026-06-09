from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

sys.stdout = (LOG_DIR / "streamlit.out.log").open("a", encoding="utf-8", buffering=1)
sys.stderr = (LOG_DIR / "streamlit.err.log").open("a", encoding="utf-8", buffering=1)

os.chdir(ROOT)

from streamlit.web import cli as streamlit_cli  # noqa: E402


sys.argv = [
    "streamlit",
    "run",
    "app.py",
    "--server.port",
    os.environ.get("GEARMIND_PORT", "8501"),
    "--server.address",
    "127.0.0.1",
    "--server.headless",
    "true",
    "--browser.gatherUsageStats",
    "false",
]

streamlit_cli.main()
