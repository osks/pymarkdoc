from __future__ import annotations

import subprocess
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    output = root / "docs" / "api"
    output.mkdir(parents=True, exist_ok=True)
    subprocess.run(["pdoc", "-o", str(output), "markdocpy"], check=True)
