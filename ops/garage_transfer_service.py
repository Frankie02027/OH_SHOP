#!/usr/bin/env python3
"""PO-box transfer broker for the first real runtime plane."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import uuid

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from ops.garage_paths import GarageWorkspacePaths
from ops.garage_workspace_bootstrap import bootstrap_workspace


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class ExportStageRequest(BaseModel):
    source_path: str = Field(..., min_length=1)
    export_name: str | None = None
    task_id: str | None = None
    job_id: str | None = None
    note: str | None = None


class TransferState:
    def __init__(self) -> None:
        self.paths = GarageWorkspacePaths.from_env()
        bootstrap_workspace(self.paths.root)

    def manifest_path(self, manifest_id: str) -> Path:
        return self.paths.pobox / "manifests" / f"{manifest_id}.json"


state: TransferState | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global state
    state = TransferState()
    try:
        yield
    finally:
        state = None


app = FastAPI(title="AI Garage Transfer Service", version="0.1", lifespan=lifespan)


def _state() -> TransferState:
    if state is None:
        raise RuntimeError("transfer state is not initialized")
    return state


def _write_manifest(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@app.get("/healthz")
def healthz() -> dict[str, object]:
    current = _state()
    return {
        "ok": True,
        "workspace_root": str(current.paths.root),
        "pobox_root": str(current.paths.pobox),
    }


@app.post("/imports/upload")
async def upload_import(
    file: UploadFile = File(...),
    task_id: str | None = Form(default=None),
    job_id: str | None = Form(default=None),
    note: str | None = Form(default=None),
) -> dict[str, object]:
    current = _state()
    manifest_id = f"IN-{uuid.uuid4().hex[:12]}"
    safe_name = Path(file.filename or "unnamed-import").name
    target = current.paths.pobox / "inbound" / f"{manifest_id}__{safe_name}"
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = await file.read()
    target.write_bytes(raw)

    ledger_copy = current.paths.ledger_imports / target.name
    ledger_copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target, ledger_copy)

    manifest = {
        "manifest_id": manifest_id,
        "direction": "inbound",
        "captured_at": _utc_stamp(),
        "filename": safe_name,
        "pobox_path": str(target),
        "ledger_copy_path": str(ledger_copy),
        "task_id": task_id,
        "job_id": job_id,
        "note": note,
        "size_bytes": len(raw),
    }
    _write_manifest(current.manifest_path(manifest_id), manifest)
    return manifest


@app.post("/exports/stage")
def stage_export(request: ExportStageRequest) -> dict[str, object]:
    current = _state()
    source = Path(request.source_path).expanduser().resolve()
    allowed_roots = (current.paths.projects.resolve(), current.paths.jobs.resolve(), current.paths.ledger.resolve())
    if not any(str(source).startswith(str(root)) for root in allowed_roots):
        raise HTTPException(status_code=400, detail=f"export source is outside allowed roots: {source}")
    if not source.exists():
        raise HTTPException(status_code=404, detail="export source does not exist")

    manifest_id = f"OUT-{uuid.uuid4().hex[:12]}"
    export_name = Path(request.export_name or source.name).name
    target = current.paths.pobox / "outbound" / f"{manifest_id}__{export_name}"
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, target, dirs_exist_ok=True)
    else:
        shutil.copy2(source, target)

    ledger_copy = current.paths.ledger_exports / target.name
    ledger_copy.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, ledger_copy, dirs_exist_ok=True)
    else:
        shutil.copy2(source, ledger_copy)

    manifest = {
        "manifest_id": manifest_id,
        "direction": "outbound",
        "captured_at": _utc_stamp(),
        "source_path": str(source),
        "pobox_path": str(target),
        "ledger_copy_path": str(ledger_copy),
        "task_id": request.task_id,
        "job_id": request.job_id,
        "note": request.note,
    }
    _write_manifest(current.manifest_path(manifest_id), manifest)
    return manifest


@app.get("/manifests/{manifest_id}")
def read_manifest(manifest_id: str) -> dict[str, object]:
    current = _state()
    manifest_path = current.manifest_path(manifest_id)
    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail="manifest not found")
    return json.loads(manifest_path.read_text(encoding="utf-8"))
