from __future__ import annotations

import os
import subprocess
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()

    subprocess.run(["python", "scripts/generate_py_fixtures.py"], check=True, cwd=root)

    js_script = root / "tests" / "js" / "generate_fixtures.js"
    if js_script.exists():
        subprocess.run(["node", str(js_script)], check=True, cwd=root, env=env)
