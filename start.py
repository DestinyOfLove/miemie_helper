"""MieMie Helper -- launcher (cross-platform)."""

import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).parent
URL = "http://localhost:4001"


def open_browser() -> None:
    time.sleep(2)
    webbrowser.open(URL)


def main() -> None:
    # Auto-install if needed
    if not (ROOT / ".venv").exists():
        print("First run -- installing dependencies ...")
        subprocess.run(["uv", "sync"], cwd=ROOT, check=True)

    if not (ROOT / "static" / "index.html").exists():
        print("Frontend not built -- building ...")
        npm = "npm.cmd" if sys.platform == "win32" else "npm"
        subprocess.run([npm, "install"], cwd=ROOT / "frontend", check=True)
        subprocess.run([npm, "run", "build"], cwd=ROOT / "frontend", check=True)

    print(f"\n  MieMie Helper starting ...")
    print(f"  Open {URL}")
    print(f"  Press Ctrl+C to stop\n")

    threading.Thread(target=open_browser, daemon=True).start()
    subprocess.run(["uv", "run", "python", "main.py"], cwd=ROOT)


if __name__ == "__main__":
    main()
