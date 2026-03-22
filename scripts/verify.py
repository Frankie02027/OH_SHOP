#!/usr/bin/env python3
"""Run Agent House verification checks."""

from __future__ import annotations

import subprocess
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    script = root / "scripts" / "agent_house.py"
    return subprocess.call(["python3", str(script), "verify"])


if __name__ == "__main__":
    raise SystemExit(main())
