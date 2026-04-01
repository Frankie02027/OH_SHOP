#!/usr/bin/env python3
"""Artifact-promotion helpers for the first real runtime plane."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import shutil
import uuid

from ops.garage_paths import GarageWorkspacePaths


@dataclass(frozen=True)
class PromotedArtifact:
    artifact_ref: dict[str, object]
    record: dict[str, object]
    promoted_path: Path


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _hash_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def promote_worker_artifact(
    *,
    paths: GarageWorkspacePaths,
    source_path: Path,
    task_id: str,
    job_id: str | None,
    kind: str,
    reported_by: str,
    description: str | None = None,
) -> PromotedArtifact:
    resolved_source = source_path.expanduser().resolve()
    allowed = False
    for root in paths.allowed_artifact_source_roots():
        try:
            resolved_source.relative_to(root.resolve())
            allowed = True
            break
        except ValueError:
            continue
    if not allowed:
        raise ValueError(f"artifact source is outside allowed worker/shared roots: {resolved_source}")

    created_at = _utc_stamp()
    artifact_id = f"A{uuid.uuid4().hex[:12]}"
    task_bucket = paths.ledger_artifacts / "by_task" / task_id
    job_bucket = task_bucket / (job_id or "no-job")
    type_bucket = paths.ledger_artifacts / "by_type" / kind
    date_bucket = paths.ledger_artifacts / "by_date" / created_at.split("T", 1)[0]
    target_dir = job_bucket / kind
    target_dir.mkdir(parents=True, exist_ok=True)
    type_bucket.mkdir(parents=True, exist_ok=True)
    date_bucket.mkdir(parents=True, exist_ok=True)

    target_path = target_dir / f"{artifact_id}__{resolved_source.name}"
    if resolved_source.is_dir():
        shutil.copytree(resolved_source, target_path, dirs_exist_ok=True)
    else:
        shutil.copy2(resolved_source, target_path)

    role = paths.classify_source_role(resolved_source)
    workspace_ref = {
        "role": role,
        "path": str(resolved_source),
    }
    artifact_ref: dict[str, object] = {
        "artifact_id": artifact_id,
        "kind": kind,
        "workspace_ref": workspace_ref,
        "reported_by": reported_by,
        "created_at": created_at,
        "description": description or f"Promoted from {resolved_source}",
        "size_bytes": target_path.stat().st_size if target_path.is_file() else 0,
    }
    file_hash = _hash_file(target_path)
    if file_hash:
        artifact_ref["hash"] = file_hash

    record: dict[str, object] = {
        "artifact_id": artifact_id,
        "kind": kind,
        "workspace_ref": workspace_ref,
        "reported_by": reported_by,
        "created_at": created_at,
        "task_id": task_id,
        "description": artifact_ref["description"],
        "size_bytes": artifact_ref["size_bytes"],
        "promoted_path": str(target_path),
    }
    if job_id is not None:
        record["job_id"] = job_id
    if file_hash:
        record["hash"] = file_hash

    manifest = {
        "artifact_ref": artifact_ref,
        "record": record,
        "promoted_path": str(target_path),
    }
    for mirror_root in (job_bucket, type_bucket, date_bucket):
        (mirror_root / f"{artifact_id}.json").write_text(
            __import__("json").dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    return PromotedArtifact(
        artifact_ref=artifact_ref,
        record=record,
        promoted_path=target_path,
    )
