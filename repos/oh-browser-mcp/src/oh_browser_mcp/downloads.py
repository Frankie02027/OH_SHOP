from __future__ import annotations

import hashlib
from pathlib import Path


def ensure_download_dir(download_dir: str | Path) -> Path:
    path = Path(download_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def compute_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_record(path: str | Path) -> dict[str, str | int]:
    file_path = Path(path)
    return {
        "path": str(file_path),
        "sha256": compute_sha256(file_path),
        "bytes": file_path.stat().st_size,
    }
