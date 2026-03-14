"""MieMie Helper -- first-time setup script (cross-platform)."""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent


def run(cmd: list[str], **kw) -> bool:
    print(f"  > {' '.join(cmd)}")
    r = subprocess.run(cmd, **kw)
    return r.returncode == 0


def check(name: str, cmd: list[str]) -> str | None:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
        ver = r.stdout.strip() or r.stderr.strip()
        print(f"  {name}: {ver}")
        return ver
    except FileNotFoundError:
        return None


def main() -> None:
    print("=" * 48)
    print("  MieMie Helper install")
    print("=" * 48)

    # 1. Python
    print("\n[1/4] Python")
    if not check("python", [sys.executable, "--version"]):
        sys.exit("Python not found")

    # 2. uv
    print("\n[2/4] uv")
    if not shutil.which("uv"):
        print("  uv not found, installing ...")
        if sys.platform == "win32":
            ok = run(["powershell", "-ExecutionPolicy", "ByPass", "-c",
                       "irm https://astral.sh/uv/install.ps1 | iex"])
        else:
            ok = run(["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"])
        if not ok:
            sys.exit("uv install failed -- see https://docs.astral.sh/uv/")
        print("  uv installed. Please restart your terminal, then re-run this script.")
        return
    check("uv", ["uv", "--version"])

    # 3. Node.js
    print("\n[3/4] Node.js")
    if not shutil.which("node"):
        sys.exit("Node.js not found -- download from https://nodejs.org/")
    check("node", ["node", "--version"])

    # 4. Install
    print("\n[4/4] Install dependencies & build frontend")

    print("\n  -- uv sync --")
    if not run(["uv", "sync"], cwd=ROOT):
        sys.exit("uv sync failed")

    frontend = ROOT / "frontend"
    npm = "npm.cmd" if sys.platform == "win32" else "npm"

    print("\n  -- npm install --")
    if not run([npm, "install"], cwd=frontend):
        sys.exit("npm install failed")

    print("\n  -- npm run build (Next.js static export) --")
    if not run([npm, "run", "build"], cwd=frontend):
        sys.exit("npm run build failed")

    print("\n" + "=" * 48)
    print("  Done! Run to start:")
    print(f"    python start.py")
    print("=" * 48)


if __name__ == "__main__":
    main()
