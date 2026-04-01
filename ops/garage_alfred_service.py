#!/usr/bin/env python3
"""Internal Alfred HTTP surface for official call processing and artifact promotion."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ops.garage_alfred import GarageAlfredProcessor, GarageOfficialBundle, GarageRecordWrite
from ops.garage_artifacts import promote_worker_artifact
from ops.garage_ledger_adapter import GarageLedgerAdapter
from ops.garage_paths import GarageWorkspacePaths
from ops.garage_workspace_bootstrap import bootstrap_workspace


class CallRequest(BaseModel):
    call: dict[str, Any]


class ArtifactPromotionRequest(BaseModel):
    source_path: str = Field(..., min_length=1)
    task_id: str = Field(..., min_length=1)
    job_id: str | None = None
    kind: str = Field(..., min_length=1)
    reported_by: str = Field(..., min_length=1)
    description: str | None = None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class AlfredState:
    def __init__(self) -> None:
        self.paths = GarageWorkspacePaths.from_env()
        bootstrap_workspace(self.paths.root)
        self.storage = GarageLedgerAdapter(
            self.paths.ledger_db,
            events_root=self.paths.ledger_events,
            indexes_root=self.paths.ledger_indexes,
            tasks_root=self.paths.ledger / "tasks",
            plans_root=self.paths.ledger / "plans",
        )
        self.processor = GarageAlfredProcessor(
            bundle_applier=self.storage.apply_official_bundle,
            state_reader=self.storage,
            id_allocator=self.storage,
            now_provider=_utc_now_iso,
        )

    def close(self) -> None:
        self.storage.close()


state: AlfredState | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global state
    state = AlfredState()
    try:
        yield
    finally:
        assert state is not None
        state.close()
        state = None


app = FastAPI(title="AI Garage Alfred Service", version="0.1", lifespan=lifespan)


def _state() -> AlfredState:
    if state is None:
        raise RuntimeError("alfred state is not initialized")
    return state


@app.get("/healthz")
def healthz() -> dict[str, object]:
    current = _state()
    return {
        "ok": True,
        "workspace_root": str(current.paths.root),
        "ledger_root": str(current.paths.ledger),
        "db_root": str(current.paths.ledger_db),
    }


@app.post("/calls/process")
def process_call(request: CallRequest) -> dict[str, object]:
    current = _state()
    try:
        result = current.processor.process_call(dict(request.call))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "call_type": result.call_type,
        "result": result.result,
        "recorded_events": list(result.recorded_events),
        "written_records": list(result.written_records),
    }


@app.post("/artifacts/promote")
def promote_artifact(request: ArtifactPromotionRequest) -> dict[str, object]:
    current = _state()
    try:
        promoted = promote_worker_artifact(
            paths=current.paths,
            source_path=Path(request.source_path),
            task_id=request.task_id,
            job_id=request.job_id,
            kind=request.kind,
            reported_by=request.reported_by,
            description=request.description,
        )
        event_id = current.storage.mint_event_id(request.task_id)
        recorded_at = _utc_now_iso()
        event: dict[str, object] = {
            "event_id": event_id,
            "event_type": "artifact.registered",
            "task_id": request.task_id,
            "recorded_at": recorded_at,
            "artifact_refs": [promoted.artifact_ref],
        }
        if request.job_id is not None:
            event["job_id"] = request.job_id
        record = dict(promoted.record)
        record["event_id"] = event_id
        bundle = GarageOfficialBundle(
            call_type="artifact.registered",
            result=promoted.artifact_ref,
            events=(event,),
            records=(GarageRecordWrite("artifact-index-record", record),),
        )
        current.storage.apply_official_bundle(bundle)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "artifact_ref": promoted.artifact_ref,
        "record": record,
        "event_id": event_id,
        "recorded_at": recorded_at,
        "promoted_path": str(promoted.promoted_path),
    }


@app.get("/tasks/{task_id}/summary")
def read_task_summary(task_id: str) -> dict[str, object]:
    summary = _state().storage.latest_task_state_summary(task_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="task summary not found")
    return summary
