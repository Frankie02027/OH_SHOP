#!/usr/bin/env python3
"""Read-oriented Ledger service for the first real Garage runtime plane."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ops.garage_ledger_adapter import GarageLedgerAdapter
from ops.garage_paths import GarageWorkspacePaths
from ops.garage_workspace_bootstrap import bootstrap_workspace


class RecordWriteRequest(BaseModel):
    schema_name: str = Field(..., min_length=1)
    data: dict[str, Any]


class LedgerState:
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

    def close(self) -> None:
        self.storage.close()


state: LedgerState | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global state
    state = LedgerState()
    try:
        yield
    finally:
        assert state is not None
        state.close()
        state = None


app = FastAPI(title="AI Garage Ledger Service", version="0.1", lifespan=lifespan)


def _storage() -> GarageLedgerAdapter:
    if state is None:
        raise RuntimeError("ledger state is not initialized")
    return state.storage


@app.get("/healthz")
def healthz() -> dict[str, object]:
    assert state is not None
    return {
        "ok": True,
        "workspace_root": str(state.paths.root),
        "db_root": str(state.paths.ledger_db),
        "events_root": str(state.paths.ledger_events),
        "indexes_root": str(state.paths.ledger_indexes),
    }


@app.post("/records/write")
def write_record(request: RecordWriteRequest) -> dict[str, object]:
    try:
        schema_name, record = _storage().write_record(request.schema_name, request.data)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"schema_name": schema_name, "record": record}


@app.get("/tasks/{task_id}")
def read_task(task_id: str) -> dict[str, object]:
    record = _storage().read_task_record(task_id)
    if record is None:
        raise HTTPException(status_code=404, detail="task not found")
    return record


@app.get("/tasks/{task_id}/summary")
def read_task_summary(task_id: str) -> dict[str, object]:
    summary = _storage().latest_task_state_summary(task_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="task summary not found")
    return summary


@app.get("/jobs/{job_id}")
def read_job(job_id: str) -> dict[str, object]:
    record = _storage().read_job_record(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="job not found")
    return record


@app.get("/jobs/{job_id}/summary")
def read_job_summary(job_id: str) -> dict[str, object]:
    summary = _storage().read_job_state_summary(job_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="job summary not found")
    return summary


@app.get("/plans/{task_id}/{plan_version}")
def read_plan(task_id: str, plan_version: int) -> dict[str, object]:
    plan = _storage().read_tracked_plan(task_id, plan_version)
    if plan is None:
        raise HTTPException(status_code=404, detail="plan not found")
    return plan


@app.get("/artifacts/{artifact_id}")
def read_artifact(artifact_id: str) -> dict[str, object]:
    record = _storage().read_artifact_index_record(artifact_id)
    if record is None:
        raise HTTPException(status_code=404, detail="artifact not found")
    return record


@app.get("/events")
def read_events(task_id: str | None = None, job_id: str | None = None) -> list[dict[str, object]]:
    return _storage().read_event_history(task_id=task_id, job_id=job_id)
