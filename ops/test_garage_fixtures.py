"""Shared test builders and temporary-root fixtures for Garage tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ops.garage_storage import GarageStorageAdapter, build_storage_backed_alfred_processor


def make_task_create_call() -> dict[str, object]:
    return {
        "schema_version": "v0.1",
        "call_type": "task.create",
        "from_role": "jarvis",
        "to_role": "alfred",
        "payload": {"objective": "Create a durable task."},
    }


def make_job_start_call(
    *,
    task_id: str = "T000001",
    job_id: str = "T000001.J001",
    attempt_no: int | None = None,
) -> dict[str, object]:
    call: dict[str, object] = {
        "schema_version": "v0.1",
        "call_type": "job.start",
        "task_id": task_id,
        "job_id": job_id,
        "from_role": "jarvis",
        "to_role": "alfred",
        "reported_at": "2026-03-30T12:01:00Z",
    }
    if attempt_no is not None:
        call["attempt_no"] = attempt_no
    return call


def make_plan_record_call(
    *,
    task_id: str = "T000001",
    job_id: str | None = "T000001.J001",
    plan_version: int = 1,
    current_active_item: str | None = "I002",
    items: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "task_id": task_id,
        "plan_version": plan_version,
        "created_by": "jarvis",
        "plan_status": "active",
        "items": items
        or [
            {
                "item_id": "I001",
                "title": "Understand state",
                "description": "Collect enough context to proceed safely.",
                "status": "verified",
            },
            {
                "item_id": "I002",
                "title": "Run Robin child leg",
                "description": "Delegate the browser step to Robin.",
                "status": "needs_child_job",
                "depends_on": ["I001"],
            },
            {
                "item_id": "I003",
                "title": "Resume and verify",
                "description": "Resume locally after the child returns.",
                "status": "todo",
                "depends_on": ["I002"],
            },
        ],
    }
    if current_active_item is not None:
        payload["current_active_item"] = current_active_item
    call: dict[str, object] = {
        "schema_version": "v0.1",
        "call_type": "plan.record",
        "task_id": task_id,
        "from_role": "jarvis",
        "to_role": "alfred",
        "plan_version": plan_version,
        "payload": payload,
    }
    if job_id is not None:
        call["job_id"] = job_id
    return call


def make_child_job_request_call(
    *,
    task_id: str = "T000001",
    job_id: str = "T000001.J001",
    parent_job_id: str | None = None,
) -> dict[str, object]:
    call: dict[str, object] = {
        "schema_version": "v0.1",
        "call_type": "child_job.request",
        "task_id": task_id,
        "job_id": job_id,
        "from_role": "jarvis",
        "to_role": "alfred",
        "reported_at": "2026-03-30T12:01:30Z",
        "payload": {
            "objective": "Use Robin for browser work.",
            "reason_for_handoff": "Needs browser lane.",
            "constraints": ["stay in browser lane"],
            "expected_output": ["page title"],
            "success_criteria": ["title captured"],
        },
    }
    if parent_job_id is not None:
        call["parent_job_id"] = parent_job_id
    return call


def make_result_submit_call(
    *,
    task_id: str = "T000001",
    job_id: str = "T000001.J001",
    reported_status: str = "succeeded",
    artifact_refs: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    call = {
        "schema_version": "v0.1",
        "call_type": "result.submit",
        "task_id": task_id,
        "job_id": job_id,
        "from_role": "robin",
        "to_role": "alfred",
        "reported_at": "2026-03-30T12:02:00Z",
        "reported_status": reported_status,
        "payload_ref": {
            "kind": "result-json",
            "path": f"/workspace/robin/tasks/{task_id}/jobs/{job_id.split('.J', 1)[1]}/result.json",
            "role": "robin",
        },
    }
    if artifact_refs is not None:
        call["artifact_refs"] = artifact_refs
    return call


def make_failure_report_call(
    reported_status: str = "blocked",
    *,
    task_id: str = "T000001",
    job_id: str = "T000001.J001",
    artifact_refs: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    call = {
        "schema_version": "v0.1",
        "call_type": "failure.report",
        "task_id": task_id,
        "job_id": job_id,
        "from_role": "robin",
        "to_role": "alfred",
        "reported_at": "2026-03-30T12:03:00Z",
        "reported_status": reported_status,
        "payload_ref": {
            "kind": "failure-json",
            "path": f"/workspace/robin/tasks/{task_id}/jobs/{job_id.split('.J', 1)[1]}/failure.json",
            "role": "robin",
        },
    }
    if artifact_refs is not None:
        call["artifact_refs"] = artifact_refs
    return call


def make_checkpoint_create_call(
    *,
    task_id: str = "T000001",
    job_id: str = "T000001.J001",
    plan_version: int | None = None,
    current_active_item: str | None = None,
    artifact_refs: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    call: dict[str, object] = {
        "schema_version": "v0.1",
        "call_type": "checkpoint.create",
        "task_id": task_id,
        "job_id": job_id,
        "from_role": "jarvis",
        "to_role": "alfred",
        "payload": {"reason": "checkpoint before restart"},
    }
    if plan_version is not None:
        call["plan_version"] = plan_version
    if current_active_item is not None:
        call["payload"]["current_active_item"] = current_active_item
    if artifact_refs is not None:
        call["artifact_refs"] = artifact_refs
    return call


def make_continuation_record_call(
    *,
    task_id: str = "T000001",
    job_id: str = "T000001.J001",
    plan_version: int | None = None,
    artifact_refs: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    call: dict[str, object] = {
        "schema_version": "v0.1",
        "call_type": "continuation.record",
        "task_id": task_id,
        "job_id": job_id,
        "from_role": "jarvis",
        "to_role": "alfred",
        "payload_ref": {
            "kind": "continuation-note",
            "path": f"/workspace/jarvis/tasks/{task_id}/continuation.md",
            "role": "jarvis",
        },
    }
    if plan_version is not None:
        call["plan_version"] = plan_version
    if artifact_refs is not None:
        call["artifact_refs"] = artifact_refs
    return call


def make_summary_artifact_ref(
    *,
    task_id: str = "T000001",
    job_id: str = "T000001.J001",
    artifact_id: str = "T000001.J001.A001",
    kind: str = "summary",
) -> dict[str, object]:
    return {
        "artifact_id": artifact_id,
        "kind": kind,
        "workspace_ref": {
            "role": "robin",
            "path": f"/workspace/robin/tasks/{task_id}/jobs/{job_id.split('.J', 1)[1]}/{artifact_id.split('.A', 1)[1]}.json",
        },
        "reported_by": "robin",
        "description": "Proof-bearing output for the supported slice.",
    }


class GarageTempRootTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmpdir.name)

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def _new_processor(self, *, now: str = "2026-03-30T12:00:00Z"):
        return build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: now,
        )


class GarageStorageRootTestCase(GarageTempRootTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.storage = GarageStorageAdapter(self.root)

    def tearDown(self) -> None:
        self.storage.close()
        super().tearDown()

    def _reopen_storage(self) -> GarageStorageAdapter:
        self.storage.close()
        self.storage = GarageStorageAdapter(self.root)
        return self.storage
