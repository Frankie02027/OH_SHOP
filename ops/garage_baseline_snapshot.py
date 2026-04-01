#!/usr/bin/env python3
"""Capture a pre-runtime-plane baseline snapshot into the canonical ledger tree."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
from datetime import datetime, timezone

from ops.garage_paths import GarageWorkspacePaths
from ops.garage_workspace_bootstrap import bootstrap_workspace


SNAPSHOT_SOURCES: tuple[str, ...] = (
    "compose/docker-compose.yml",
    "compose/openhands_override",
    "compose/agent_server_override",
    "data/openhands",
    "ops/garagectl.py",
    "workspace/README.md",
)


def _copy_if_exists(repo_root: Path, relative_path: str, destination: Path) -> dict[str, object]:
    source = repo_root / relative_path
    target = destination / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    if not source.exists():
        return {"path": relative_path, "exists": False}
    if source.is_dir():
        shutil.copytree(source, target, dirs_exist_ok=True)
        file_count = sum(1 for _ in target.rglob("*") if _.is_file())
        return {"path": relative_path, "exists": True, "kind": "directory", "file_count": file_count}
    shutil.copy2(source, target)
    return {"path": relative_path, "exists": True, "kind": "file", "size_bytes": source.stat().st_size}

def _capture_command(command: list[str]) -> dict[str, object]:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except Exception as exc:
        return {"command": command, "ok": False, "detail": str(exc)}
    return {
        "command": command,
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def create_baseline_snapshot(workspace_root: Path | None = None) -> dict[str, object]:
    bootstrap_workspace(workspace_root)
    paths = (
        GarageWorkspacePaths(root=workspace_root.resolve())
        if workspace_root is not None
        else GarageWorkspacePaths.from_env()
    )
    repo_root = Path(__file__).resolve().parents[1]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snapshot_root = paths.ledger_snapshots / f"runtime_baseline_{stamp}"
    snapshot_root.mkdir(parents=True, exist_ok=False)

    copied = [
        _copy_if_exists(repo_root, relative_path, snapshot_root)
        for relative_path in SNAPSHOT_SOURCES
    ]
    docker_ps = _capture_command(["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}\t{{.Image}}"])
    docker_images = _capture_command(["docker", "images", "--format", "table {{.Repository}}\t{{.Tag}}\t{{.ID}}"])
    compose_config = _capture_command(["docker", "compose", "-f", str(repo_root / "compose" / "docker-compose.yml"), "config"])

    manifest = {
        "captured_at": stamp,
        "repo_root": str(repo_root),
        "snapshot_root": str(snapshot_root),
        "sources": copied,
        "docker_ps": docker_ps,
        "docker_images": docker_images,
        "compose_config": compose_config,
    }
    manifest_path = snapshot_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    summary_path = snapshot_root / "SUMMARY.md"
    lines = [
        "# Runtime Baseline Snapshot",
        "",
        f"- Captured at: {stamp}",
        f"- Repo root: {repo_root}",
        "",
        "## Copied sources",
    ]
    for entry in copied:
        if entry.get("exists"):
            lines.append(f"- `{entry['path']}`")
        else:
            lines.append(f"- `{entry['path']}` (missing)")
    lines.extend(
        [
            "",
            "## Docker availability",
            f"- `docker ps`: {'ok' if docker_ps.get('ok') else 'failed'}",
            f"- `docker images`: {'ok' if docker_images.get('ok') else 'failed'}",
            f"- `docker compose config`: {'ok' if compose_config.get('ok') else 'failed'}",
            "",
        ]
    )
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "snapshot_root": str(snapshot_root),
        "manifest_path": str(manifest_path),
        "summary_path": str(summary_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace-root", type=Path, default=None)
    args = parser.parse_args()
    result = create_baseline_snapshot(args.workspace_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
