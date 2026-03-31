"""Tests for the first Garage storage adapter and Alfred storage wiring."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ops.garage_alfred import GarageAlfredProcessingError, GarageAlfredProcessor
from ops.garage_boundaries import GarageBoundaryError, write_garage_persisted_record
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
    *,
    task_id: str = "T000001",
    job_id: str = "T000001.J001",
    reported_status: str = "blocked",
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


class GarageStorageAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmpdir.name)
        self.storage = GarageStorageAdapter(self.root)

    def tearDown(self) -> None:
        self.storage.close()
        self.tmpdir.cleanup()

    def _reopen_storage(self) -> GarageStorageAdapter:
        self.storage.close()
        self.storage = GarageStorageAdapter(self.root)
        return self.storage

    def test_task_create_continuity_survives_processor_recreation(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        first = processor.process_call(make_task_create_call())
        storage.close()

        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:01:00Z",
        )
        second = processor.process_call(make_task_create_call())
        storage.close()

        self.assertEqual("T000001", first.result["task_id"])
        self.assertEqual("T000002", second.result["task_id"])

    def test_child_job_request_creates_durable_lineage_and_dispatch_events(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(make_job_start_call())
        result = processor.process_call(make_child_job_request_call())

        child_job = storage.read_job_record(result.result["job_id"])
        child_jobs = storage.list_child_jobs("T000001.J001")
        task_summary = storage.latest_task_state_summary("T000001")
        job_history = storage.read_event_history(job_id=result.result["job_id"])
        storage.close()

        self.assertEqual("T000001.J002", result.result["job_id"])
        self.assertEqual("T000001.J001", child_job["parent_job_id"])
        self.assertEqual("waiting_on_child", task_summary["task_record"]["task_state"])
        self.assertEqual("T000001.J002", task_summary["task_record"]["current_job_id"])
        self.assertEqual(1, len(child_jobs))
        self.assertEqual(
            ["job.created", "job.dispatched"],
            [event["event_type"] for event in job_history],
        )

    def test_event_id_continuity_survives_processor_recreation(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        first = processor.process_call(make_job_start_call())
        storage.close()
        event_log_path = self.root / "event_history.jsonl"
        event_log_path.unlink()

        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:02:00Z",
        )
        second = processor.process_call(make_result_submit_call())

        history = storage.read_event_history("T000001")
        next_event_id = storage.peek_next_event_id("T000001")
        storage.close()

        self.assertEqual("T000001.E0001", first.result["event_id"])
        self.assertEqual("T000001.E0002", second.result["event_id"])
        self.assertEqual(
            ["T000001.E0001", "T000001.E0002"],
            [event["event_id"] for event in history],
        )
        self.assertEqual("T000001.E0003", next_event_id)

    def test_checkpoint_id_continuity_survives_processor_recreation(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        first = processor.process_call(make_checkpoint_create_call())
        storage.close()

        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:03:00Z",
        )
        second = processor.process_call(make_checkpoint_create_call())
        next_checkpoint_id = storage.peek_next_checkpoint_id("T000001")
        storage.close()

        self.assertEqual("T000001.C001", first.result["checkpoint_id"])
        self.assertEqual("T000001.C002", second.result["checkpoint_id"])
        self.assertEqual("T000001.C003", next_checkpoint_id)

    def test_task_record_write_persists_durably(self) -> None:
        write_garage_persisted_record(
            "task-record",
            {
                "task_id": "T000001",
                "task_state": "running",
                "created_at": "2026-03-30T12:00:00Z",
            },
            self.storage.write_record,
        )
        self._reopen_storage()
        self.assertEqual("running", self.storage.read_task_record("T000001")["task_state"])

    def test_job_record_write_persists_durably(self) -> None:
        write_garage_persisted_record(
            "job-record",
            {
                "task_id": "T000001",
                "job_id": "T000001.J001",
                "job_state": "running",
                "created_at": "2026-03-30T12:01:00Z",
            },
            self.storage.write_record,
        )
        self._reopen_storage()
        self.assertEqual("running", self.storage.read_job_record("T000001.J001")["job_state"])

    def test_event_record_append_is_durable_and_append_only(self) -> None:
        write_garage_persisted_record(
            "event-record",
            {
                "schema_version": "v0.1",
                "event_type": "job.started",
                "event_id": "T000001.E0001",
                "task_id": "T000001",
                "job_id": "T000001.J001",
                "related_call_type": "job.start",
                "recorded_at": "2026-03-30T12:01:00Z",
            },
            self.storage.write_record,
        )
        write_garage_persisted_record(
            "event-record",
            {
                "schema_version": "v0.1",
                "event_type": "job.returned",
                "event_id": "T000001.E0002",
                "task_id": "T000001",
                "job_id": "T000001.J001",
                "related_call_type": "result.submit",
                "reported_status": "succeeded",
                "recorded_at": "2026-03-30T12:02:00Z",
            },
            self.storage.write_record,
        )
        self._reopen_storage()
        history = self.storage.read_event_history("T000001")
        self.assertEqual(2, len(history))
        self.assertEqual("T000001.E0001", history[0]["event_id"])
        self.assertEqual("T000001.E0002", history[1]["event_id"])

    def test_same_job_retry_continuity_is_durable(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(make_job_start_call(attempt_no=1))
        processor.process_call(make_result_submit_call())
        storage.close()

        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:05:00Z",
        )
        result = processor.process_call(make_job_start_call())
        job_record = storage.read_job_record("T000001.J001")
        summary = storage.read_job_state_summary("T000001.J001")
        history = storage.read_event_history(job_id="T000001.J001")
        storage.close()

        self.assertEqual(2, result.result["attempt_no"])
        self.assertEqual(2, job_record["attempt_no"])
        self.assertEqual("running", job_record["job_state"])
        self.assertEqual(2, summary["attempt_no"])
        self.assertEqual(
            [1, 2],
            [event["attempt_no"] for event in history if event["event_type"] == "job.started"],
        )

    def test_incoherent_retry_attempt_is_rejected(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(make_job_start_call(attempt_no=1))
        processor.process_call(make_result_submit_call())

        with self.assertRaises(GarageAlfredProcessingError) as ctx:
            processor.process_call(make_job_start_call(attempt_no=5))

        history = storage.read_event_history(job_id="T000001.J001")
        summary = storage.read_job_state_summary("T000001.J001")
        storage.close()

        self.assertIn("expected attempt_no 2 but received 5", str(ctx.exception))
        self.assertEqual(
            ["job.started", "job.returned"],
            [event["event_type"] for event in history],
        )
        self.assertEqual(1, summary["attempt_no"])

    def test_materially_new_refined_job_gets_new_job_id_with_recoverable_lineage(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(make_job_start_call())
        first_child = processor.process_call(make_child_job_request_call())
        refined_child = processor.process_call(
            make_child_job_request_call(parent_job_id=first_child.result["job_id"])
        )

        linked_children = storage.list_child_jobs(first_child.result["job_id"])
        refined_job = storage.read_job_record(refined_child.result["job_id"])
        next_job_id = storage.peek_next_job_id("T000001")
        storage.close()

        self.assertEqual("T000001.J002", first_child.result["job_id"])
        self.assertEqual("T000001.J003", refined_child.result["job_id"])
        self.assertEqual(first_child.result["job_id"], refined_job["parent_job_id"])
        self.assertEqual(1, len(linked_children))
        self.assertEqual("T000001.J004", next_job_id)

    def test_checkpoint_record_write_persists_durably(self) -> None:
        write_garage_persisted_record(
            "checkpoint-record",
            {
                "checkpoint_id": "T000001.C001",
                "task_id": "T000001",
                "created_at": "2026-03-30T12:03:00Z",
            },
            self.storage.write_record,
        )
        self._reopen_storage()
        self.assertEqual(
            "T000001",
            self.storage.read_checkpoint_record("T000001.C001")["task_id"],
        )

    def test_continuation_record_write_persists_durably(self) -> None:
        write_garage_persisted_record(
            "continuation-record",
            {
                "task_id": "T000001",
                "job_id": "T000001.J001",
                "created_at": "2026-03-30T12:04:00Z",
                "content_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/continuation.md",
                },
            },
            self.storage.write_record,
        )
        self._reopen_storage()
        continuations = self.storage.list_continuation_records("T000001")
        self.assertEqual(1, len(continuations))
        self.assertEqual("T000001.J001", continuations[0]["job_id"])

    def test_end_to_end_alfred_integration_records_land_in_storage(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        result = processor.process_call(make_task_create_call())

        task_record = storage.read_task_record(result.result["task_id"])
        event_history = storage.read_event_history(result.result["task_id"])
        next_task_id = storage.peek_next_task_id()
        storage.close()

        self.assertEqual("created", task_record["task_state"])
        self.assertEqual(1, len(event_history))
        self.assertEqual("task.created", event_history[0]["event_type"])
        self.assertEqual("T000002", next_task_id)

    def test_invalid_child_job_bundle_is_blocked_before_durable_side_effects(self) -> None:
        class BrokenChildJobProcessor(GarageAlfredProcessor):
            def _build_job_created_event(
                self,
                call: dict[str, object],
                *,
                child_job_id: str,
                parent_job_id: str,
                event_id: str,
                recorded_at: str,
            ) -> dict[str, object]:
                event = super()._build_job_created_event(
                    call,
                    child_job_id=child_job_id,
                    parent_job_id=parent_job_id,
                    event_id=event_id,
                    recorded_at=recorded_at,
                )
                event.pop("recorded_at")
                return event

        storage = GarageStorageAdapter(self.root)
        processor = BrokenChildJobProcessor(
            bundle_applier=storage.apply_official_bundle,
            id_allocator=storage,
            state_reader=storage,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )

        with self.assertRaises(GarageBoundaryError):
            processor.process_call(make_child_job_request_call())

        self.assertEqual([], storage.read_event_history("T000001"))
        self.assertIsNone(storage.read_job_record("T000001.J001"))
        storage.close()

    def test_invalid_record_fails_before_storage_side_effect(self) -> None:
        with self.assertRaises(GarageBoundaryError):
            write_garage_persisted_record(
                "task-record",
                {
                    "task_id": "T000001",
                },
                self.storage.write_record,
            )

        self.assertIsNone(self.storage.read_task_record("T000001"))
        self.assertEqual([], self.storage.read_event_history())

    def test_one_processed_call_applies_as_one_coherent_bundle(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        result = processor.process_call(make_task_create_call())

        self.assertEqual(
            ["task-record", "event-record"],
            [write[0] for write in result.written_records],
        )
        self.assertIsNotNone(storage.read_task_record("T000001"))
        self.assertEqual(1, len(storage.read_event_history("T000001")))
        self.assertEqual("task.created", storage.read_event_history("T000001")[0]["event_type"])
        storage.close()

    def test_failure_during_bundle_apply_rolls_back_canonical_state(self) -> None:
        class FailingBundleStorage(GarageStorageAdapter):
            def _before_bundle_record_write(self, index, record_write, bundle) -> None:
                if index == 2:
                    raise RuntimeError("simulated bundle failure")

        storage = FailingBundleStorage(self.root)
        processor = GarageAlfredProcessor(
            bundle_applier=storage.apply_official_bundle,
            id_allocator=storage,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )

        with self.assertRaises(RuntimeError) as ctx:
            processor.process_call(make_task_create_call())

        self.assertIn("simulated bundle failure", str(ctx.exception))
        self.assertIsNone(storage.read_task_record("T000001"))
        self.assertEqual([], storage.read_event_history("T000001"))
        self.assertEqual("T000001", storage.peek_next_task_id())
        storage.close()

    def test_readback_helpers_return_expected_supported_state(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(make_job_start_call())
        processor.process_call(make_result_submit_call())
        processor.process_call(make_checkpoint_create_call(plan_version=2))
        processor.process_call(make_continuation_record_call(plan_version=2))

        task_summary = storage.latest_task_state_summary("T000001")
        job_summary = storage.read_job_state_summary("T000001.J001")
        plan_linkage = storage.active_plan_linkage_summary("T000001")
        resume_anchor = storage.resolve_task_resume_anchor("T000001")
        job_history = storage.read_event_history(job_id="T000001.J001")
        continuations = storage.list_continuation_records("T000001")

        self.assertEqual("resuming", task_summary["task_record"]["task_state"])
        self.assertTrue(task_summary["is_resuming"])
        self.assertTrue(task_summary["has_resume_anchor"])
        self.assertEqual("resume-anchor-only", task_summary["dominant_target_kind"])
        self.assertEqual("resuming", task_summary["effective_task_posture"])
        self.assertEqual(2, task_summary["current_plan_version"])
        self.assertEqual("continuation.recorded", task_summary["latest_event"]["event_type"])
        self.assertEqual("job.returned", task_summary["latest_meaningful_event"]["event_type"])
        self.assertEqual("T000001.J001", task_summary["current_job"]["job_record"]["job_id"])
        self.assertEqual(2, task_summary["latest_checkpoint"]["plan_version"])
        self.assertEqual(2, task_summary["latest_continuation"]["plan_version"])
        self.assertEqual(2, plan_linkage["current_plan_version"])
        self.assertEqual(2, plan_linkage["latest_checkpoint_plan_version"])
        self.assertEqual(2, plan_linkage["latest_continuation_plan_version"])
        self.assertEqual("continuation-record", resume_anchor["anchor_kind"])
        self.assertEqual(2, resume_anchor["plan_version"])
        self.assertEqual("returned", job_summary["job_record"]["job_state"])
        self.assertEqual("returned", job_summary["job_state"])
        self.assertEqual("continuation.recorded", job_summary["latest_event_type"])
        self.assertEqual("job.returned", job_summary["latest_state_event_type"])
        self.assertEqual("succeeded", job_summary["latest_reported_status"])
        self.assertFalse(job_summary["is_same_job_retry"])
        self.assertFalse(job_summary["is_materially_new_child_leg"])
        self.assertTrue(job_summary["is_current_task_leg"])
        self.assertFalse(job_summary["current_job_is_primary_focus"])
        self.assertTrue(job_summary["current_job_subordinate_to_task_focus"])
        self.assertEqual(1, storage.latest_attempt_for_job("T000001.J001"))
        self.assertEqual(1, len(continuations))
        self.assertEqual(4, len(job_history))
        self.assertEqual(
            ["job.started", "job.returned", "checkpoint.created", "continuation.recorded"],
            [event["event_type"] for event in job_history],
        )
        storage.close()

    def test_waiting_on_child_and_child_job_summary_are_reconstructable(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(make_job_start_call())
        child = processor.process_call(make_child_job_request_call())

        task_summary = storage.latest_task_state_summary("T000001")
        child_summary = storage.read_job_state_summary(child.result["job_id"])
        parent_summary = storage.read_job_state_summary("T000001.J001")
        storage.close()

        self.assertTrue(task_summary["is_waiting_on_child"])
        self.assertEqual("waiting_on_child", task_summary["task_record"]["task_state"])
        self.assertEqual("waiting-on-child", task_summary["dominant_target_kind"])
        self.assertEqual("waiting-on-child", task_summary["dominant_blocker_kind"])
        self.assertEqual("waiting-on-child", task_summary["effective_task_posture"])
        self.assertTrue(task_summary["execution_held"])
        self.assertEqual("waiting-on-child", task_summary["execution_hold_kind"])
        self.assertIn("job.start", task_summary["allowed_call_types"])
        self.assertIn("child_job.request", task_summary["allowed_call_types"])
        self.assertEqual("job.start", task_summary["best_next_call_type"])
        self.assertEqual(
            "progress-child-leg", task_summary["best_next_move"]["move_kind"]
        )
        self.assertEqual(child.result["job_id"], task_summary["task_record"]["current_job_id"])
        self.assertEqual("dispatched", child_summary["job_state"])
        self.assertEqual("job.dispatched", child_summary["latest_event_type"])
        self.assertEqual("job.dispatched", child_summary["latest_state_event_type"])
        self.assertEqual(1, child_summary["attempt_no"])
        self.assertFalse(child_summary["is_same_job_retry"])
        self.assertTrue(child_summary["is_materially_new_child_leg"])
        self.assertTrue(child_summary["is_current_task_leg"])
        self.assertTrue(child_summary["current_job_is_primary_focus"])
        self.assertFalse(child_summary["current_job_subordinate_to_task_focus"])
        self.assertFalse(parent_summary["is_current_task_leg"])

    def test_resume_anchor_falls_back_to_checkpoint_when_no_continuation_exists(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(make_job_start_call())
        processor.process_call(make_result_submit_call())
        checkpoint = processor.process_call(make_checkpoint_create_call(plan_version=3))

        resume_anchor = storage.resolve_task_resume_anchor("T000001")
        storage.close()

        self.assertEqual("checkpoint-record", resume_anchor["anchor_kind"])
        self.assertEqual(checkpoint.result["checkpoint_id"], resume_anchor["record"]["checkpoint_id"])
        self.assertEqual(3, resume_anchor["plan_version"])

    def test_active_plan_linkage_and_item_states_are_reconstructable(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(make_job_start_call())
        processor.process_call(make_plan_record_call(plan_version=1, current_active_item="I002"))
        processor.process_call(
            make_plan_record_call(
                plan_version=2,
                current_active_item="I002",
                items=[
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
                        "status": "blocked",
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
            )
        )

        active_plan = storage.read_active_plan_summary("T000001")
        linkage = storage.active_plan_linkage_summary("T000001")
        active_item = storage.resolve_active_plan_item("T000001")
        verified_item = storage.read_plan_item_summary("T000001", 2, "I001")
        blocked_item = storage.read_plan_item_summary("T000001", 2, "I002")
        pending_item = storage.read_plan_item_summary("T000001", 2, "I003")
        prior_active_item = storage.read_plan_item_summary("T000001", 1, "I002")
        storage.close()

        self.assertEqual(2, active_plan["plan_version"])
        self.assertEqual("I002", active_plan["current_active_item"])
        self.assertEqual("I002", active_item["item_id"])
        self.assertEqual("I002", linkage["current_active_item"])
        self.assertEqual("I002", linkage["current_active_item_summary"]["item_id"])
        self.assertEqual("I002", linkage["next_plan_resume_target"]["item"]["item_id"])
        self.assertTrue(verified_item["is_completed"])
        self.assertTrue(prior_active_item["is_active"])
        self.assertTrue(blocked_item["is_blocked"])
        self.assertFalse(blocked_item["is_completed"])
        self.assertTrue(pending_item["is_pending"])
        self.assertFalse(pending_item["dependencies_resolved"])

    def test_task_summary_and_resume_target_become_plan_aware(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(make_job_start_call())
        processor.process_call(make_plan_record_call(plan_version=1, current_active_item="I002"))
        child = processor.process_call(make_child_job_request_call())
        processor.process_call(
            make_checkpoint_create_call(
                job_id=child.result["job_id"],
                plan_version=1,
                current_active_item="I002",
            )
        )
        processor.process_call(
            make_continuation_record_call(
                job_id=child.result["job_id"],
                plan_version=1,
            )
        )

        task_summary = storage.latest_task_state_summary("T000001")
        resume_anchor = storage.resolve_task_resume_anchor("T000001")
        next_target = storage.resolve_next_plan_resume_target("T000001")
        active_plan = storage.read_active_plan_summary("T000001")
        storage.close()

        self.assertEqual(1, task_summary["current_plan_version"])
        self.assertEqual("I002", task_summary["current_active_plan_item"]["item_id"])
        self.assertEqual("I002", task_summary["active_plan_linkage"]["current_active_item"])
        self.assertEqual("I002", task_summary["latest_checkpoint_summary"]["current_active_item"])
        self.assertEqual("I002", task_summary["latest_continuation_summary"]["current_active_item"])
        self.assertEqual("waiting-on-child", task_summary["dominant_target_kind"])
        self.assertEqual("waiting-on-child", next_target["target_kind"])
        self.assertEqual("continuation-record", resume_anchor["anchor_kind"])
        self.assertEqual("I002", resume_anchor["current_active_item"])
        self.assertEqual("I002", next_target["item"]["item_id"])
        self.assertEqual("I002", next_target["resume_anchor"]["current_active_item"])
        self.assertEqual("I002", active_plan["current_active_item_summary"]["item_id"])

    def test_next_plan_resume_target_falls_back_to_ready_pending_item(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(make_job_start_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item=None,
                items=[
                    {
                        "item_id": "I001",
                        "title": "Understand state",
                        "description": "Collect enough context to proceed safely.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Resume local implementation",
                        "description": "Continue locally once context is verified.",
                        "status": "todo",
                        "depends_on": ["I001"],
                    },
                    {
                        "item_id": "I003",
                        "title": "Final verification",
                        "description": "Run final checks after implementation.",
                        "status": "todo",
                        "depends_on": ["I002"],
                    },
                ],
            )
        )

        active_item = storage.resolve_active_plan_item("T000001")
        next_target = storage.resolve_next_plan_resume_target("T000001")
        resume_anchor = storage.resolve_task_resume_anchor("T000001")
        storage.close()

        self.assertIsNone(active_item)
        self.assertEqual("next-executable", next_target["target_kind"])
        self.assertEqual("I002", next_target["item"]["item_id"])
        self.assertTrue(next_target["item"]["dependencies_resolved"])
        self.assertEqual("job-state-event", resume_anchor["anchor_kind"])

    def test_job_start_mutates_ready_plan_item_to_in_progress(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                job_id="T000001.J001",
                plan_version=1,
                current_active_item=None,
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Start local work",
                        "description": "Kick off the next executable item.",
                        "status": "todo",
                        "depends_on": ["I001"],
                    },
                ],
            )
        )

        processor.process_call(make_job_start_call())

        active_plan = storage.read_active_plan_summary("T000001")
        active_item = storage.resolve_active_plan_item("T000001")
        next_executable = storage.resolve_next_executable_plan_item("T000001")
        task_summary = storage.latest_task_state_summary("T000001")
        storage.close()

        self.assertEqual("I002", active_plan["current_active_item"])
        self.assertEqual("I002", active_item["item_id"])
        self.assertEqual("in_progress", active_item["status"])
        self.assertIsNone(next_executable)
        self.assertEqual("I002", task_summary["current_active_plan_item"]["item_id"])
        self.assertTrue(task_summary["is_running"])

    def test_child_job_request_marks_active_plan_item_needs_child_job(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Run Robin child leg",
                        "description": "Delegate the browser step to Robin.",
                        "status": "todo",
                        "depends_on": ["I001"],
                    },
                ],
            )
        )
        processor.process_call(make_job_start_call())
        processor.process_call(make_child_job_request_call())

        active_item = storage.resolve_active_plan_item("T000001")
        task_summary = storage.latest_task_state_summary("T000001")
        storage.close()

        self.assertEqual("needs_child_job", active_item["status"])
        self.assertTrue(active_item["is_active"])
        self.assertEqual("I002", task_summary["resume_anchor"]["current_active_item"])
        self.assertTrue(task_summary["is_waiting_on_child"])

    def test_result_submit_marks_active_item_done_unverified_and_keeps_verification_target_active(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Run Robin child leg",
                        "description": "Delegate the browser step to Robin.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "artifact_exists"},
                    },
                    {
                        "item_id": "I003",
                        "title": "Resume local follow-up",
                        "description": "Continue with independent local follow-up.",
                        "status": "todo",
                    },
                ],
            )
        )

        processor.process_call(make_result_submit_call(reported_status="succeeded"))

        completed_item = storage.read_plan_item_summary("T000001", 1, "I002")
        active_item = storage.resolve_active_plan_item("T000001")
        next_executable = storage.resolve_next_executable_plan_item("T000001")
        task_summary = storage.latest_task_state_summary("T000001")
        continuation_effect = storage.evaluate_supported_call_posture_effect(
            "T000001", "continuation.record"
        )
        storage.close()

        self.assertEqual("done_unverified", completed_item["status"])
        self.assertTrue(completed_item["is_completed"])
        self.assertEqual("I002", active_item["item_id"])
        self.assertEqual("done_unverified", active_item["status"])
        self.assertEqual("I003", next_executable["item_id"])
        self.assertTrue(task_summary["is_verification_pending"])
        self.assertTrue(task_summary["is_waiting_on_proof"])
        self.assertFalse(task_summary["is_waiting_on_review"])
        self.assertEqual("proof-gathering", task_summary["dominant_target_kind"])
        self.assertEqual("proof-gathering", task_summary["dominant_blocker_kind"])
        self.assertEqual("waiting-on-proof", task_summary["effective_task_posture"])
        self.assertTrue(task_summary["execution_held"])
        self.assertEqual(
            ("checkpoint.create", "continuation.record"),
            task_summary["allowed_call_types"],
        )
        self.assertIn("job.start", task_summary["blocked_call_types"])
        self.assertEqual("continuation.record", task_summary["best_next_call_type"])
        self.assertEqual("attach-artifact-ref", task_summary["best_next_move"]["move_kind"])
        self.assertEqual(
            "preserve_or_resolve",
            task_summary["best_next_move_effect_kind"],
        )
        self.assertEqual("preserve_or_resolve", continuation_effect["effect_kind"])
        self.assertFalse(task_summary["current_job_is_primary_focus"])
        self.assertTrue(task_summary["relevant_plan_item_is_primary_focus"])
        self.assertEqual("proof-gathering", task_summary["next_plan_resume_target"]["target_kind"])
        self.assertEqual("I002", task_summary["next_plan_resume_target"]["item"]["item_id"])

    def test_failure_report_marks_active_item_blocked_and_plan_blocked(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Run Robin child leg",
                        "description": "Delegate the browser step to Robin.",
                        "status": "todo",
                        "depends_on": ["I001"],
                    },
                ],
            )
        )
        processor.process_call(make_job_start_call())
        processor.process_call(make_failure_report_call(reported_status="blocked"))

        active_plan = storage.read_active_plan_summary("T000001")
        active_item = storage.resolve_active_plan_item("T000001")
        task_summary = storage.latest_task_state_summary("T000001")
        storage.close()

        self.assertEqual("blocked", active_plan["plan_status"])
        self.assertEqual("I002", active_plan["current_active_item"])
        self.assertEqual("blocked", active_item["status"])
        self.assertTrue(active_item["is_blocked"])
        self.assertEqual("blocked-evidence-review", task_summary["dominant_target_kind"])
        self.assertEqual("blocked-evidence-review", task_summary["dominant_blocker_kind"])
        self.assertEqual("blocked-evidence-review", task_summary["effective_task_posture"])
        self.assertTrue(task_summary["execution_held"])
        self.assertIn("failure.report", task_summary["allowed_call_types"])
        self.assertIn("continuation.record", task_summary["allowed_call_types"])
        self.assertEqual("continuation.record", task_summary["best_next_call_type"])
        self.assertEqual(
            "capture-blocked-evidence",
            task_summary["best_next_move"]["move_kind"],
        )
        self.assertEqual(
            "preserve",
            task_summary["best_next_move_effect_kind"],
        )
        self.assertEqual("I002", task_summary["current_active_plan_item"]["item_id"])
        self.assertEqual("I002", task_summary["next_plan_resume_target"]["item"]["item_id"])

    def test_partial_result_submit_keeps_current_item_active_in_progress(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(make_plan_record_call(plan_version=1, current_active_item="I002"))
        child = processor.process_call(make_child_job_request_call())
        processor.process_call(
            make_result_submit_call(
                job_id=child.result["job_id"],
                reported_status="partial",
            )
        )

        active_item = storage.resolve_active_plan_item("T000001")
        task_summary = storage.latest_task_state_summary("T000001")
        storage.close()

        self.assertEqual("in_progress", active_item["status"])
        self.assertEqual("I002", task_summary["current_active_plan_item"]["item_id"])
        self.assertTrue(task_summary["is_resuming"])
        self.assertEqual("active-item", task_summary["dominant_target_kind"])
        self.assertEqual("running", task_summary["effective_task_posture"])
        self.assertTrue(task_summary["execution_allowed"])
        self.assertIn("result.submit", task_summary["allowed_call_types"])
        self.assertIn("failure.report", task_summary["allowed_call_types"])
        self.assertIsNone(task_summary["best_next_call_type"])
        self.assertEqual(
            "continue-active-execution",
            task_summary["best_next_move"]["move_kind"],
        )
        self.assertEqual("preserve", task_summary["best_next_move_effect_kind"])

    def test_incoherent_plan_transition_is_rejected_before_durable_side_effects(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        with self.assertRaises(GarageAlfredProcessingError) as ctx:
            processor.process_call(
                make_plan_record_call(
                    plan_version=1,
                    current_active_item="I003",
                    items=[
                        {
                            "item_id": "I001",
                            "title": "Prepare runtime",
                            "description": "Set up the execution slice.",
                            "status": "verified",
                        },
                        {
                            "item_id": "I002",
                            "title": "Run Robin child leg",
                            "description": "Delegate the browser step to Robin.",
                            "status": "in_progress",
                            "depends_on": ["I001"],
                        },
                        {
                            "item_id": "I003",
                            "title": "Resume local follow-up",
                            "description": "Continue with local follow-up.",
                            "status": "todo",
                        },
                    ],
                )
            )

        self.assertIn("conflicts with reconstructed active item", str(ctx.exception))
        self.assertIsNone(storage.read_tracked_plan("T000001", 1))
        self.assertEqual(["task.created"], [event["event_type"] for event in storage.read_event_history("T000001")])
        storage.close()

    def test_result_submit_registers_artifact_and_promotes_item_to_verified_when_gate_is_satisfied(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Produce summary proof",
                        "description": "Return the summary artifact for the current step.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "artifact_exists"},
                    },
                ],
            )
        )

        processor.process_call(
            make_result_submit_call(
                artifact_refs=[make_summary_artifact_ref()],
                reported_status="succeeded",
            )
        )

        item_summary = storage.read_plan_item_summary("T000001", 1, "I002")
        artifact_index = storage.read_artifact_index_record("T000001.J001.A001")
        task_summary = storage.latest_task_state_summary("T000001")
        storage.close()

        self.assertEqual("verified", item_summary["status"])
        self.assertTrue(item_summary["proof_satisfied"])
        self.assertEqual(2, item_summary["evidence_count"])
        self.assertEqual(("T000001.J001.A001",), item_summary["official_artifact_ids"])
        self.assertEqual("T000001", artifact_index["task_id"])
        self.assertEqual("T000001.J001", artifact_index["job_id"])
        self.assertEqual("verified", task_summary["relevant_plan_item"]["status"])
        self.assertEqual("T000001.J001.A001", task_summary["relevant_evidence_refs"][0]["artifact_id"])

    def test_artifact_matches_kind_exposes_unmet_requirement_and_later_promotes(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Capture screenshot proof",
                        "description": "Need a screenshot artifact before the step is verified.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {
                            "type": "artifact_matches_kind",
                            "params": {"kind": "screenshot"},
                        },
                    },
                    {
                        "item_id": "I003",
                        "title": "Continue follow-up",
                        "description": "Only continue once screenshot proof is verified.",
                        "status": "todo",
                        "depends_on": ["I002"],
                    },
                ],
            )
        )

        processor.process_call(
            make_result_submit_call(
                artifact_refs=[make_summary_artifact_ref()],
                reported_status="succeeded",
            )
        )

        unmet_item = storage.read_plan_item_summary("T000001", 1, "I002")
        unmet_task_summary = storage.latest_task_state_summary("T000001")

        processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[
                    make_summary_artifact_ref(
                        artifact_id="T000001.J001.A002",
                        kind="screenshot",
                    )
                ],
            )
        )

        promoted_item = storage.read_plan_item_summary("T000001", 1, "I002")
        promoted_task_summary = storage.latest_task_state_summary("T000001")
        storage.close()

        self.assertEqual("done_unverified", unmet_item["status"])
        self.assertTrue(unmet_item["proof_gate_supported"])
        self.assertTrue(unmet_item["rule_mechanical"])
        self.assertEqual("mechanically-satisfiable-later", unmet_item["rule_finality_kind"])
        self.assertEqual("missing_required_artifact_kind", unmet_item["unmet_requirement_kind"])
        self.assertEqual(
            "screenshot",
            unmet_item["unmet_requirement_detail"]["required_kind"],
        )
        self.assertEqual(
            ("summary",),
            unmet_item["unmet_requirement_detail"]["observed_artifact_kinds"],
        )
        self.assertTrue(unmet_item["can_be_satisfied_by_supported_evidence_calls"])
        self.assertFalse(unmet_item["can_only_remain_review_needed"])
        self.assertEqual(
            "missing_required_artifact_kind",
            unmet_task_summary["relevant_unmet_requirement_kind"],
        )
        self.assertTrue(
            unmet_task_summary["relevant_can_be_satisfied_by_supported_evidence_calls"]
        )
        self.assertEqual("verified", promoted_item["status"])
        self.assertTrue(promoted_item["proof_satisfied"])
        self.assertEqual("next-executable", promoted_task_summary["dominant_target_kind"])
        self.assertEqual("job.start", promoted_task_summary["best_next_call_type"])

    def test_rule_aware_policy_guidance_distinguishes_exact_requirement_postures(self) -> None:
        scenarios = [
            {
                "name": "missing_artifact_ref",
                "rule": {"type": "artifact_exists"},
                "evidence_refs": [],
                "expected_move_kind": "attach-artifact-ref",
                "expected_finality": "mechanically-satisfiable-later",
                "expected_hold_reason": "missing_artifact_ref",
                "reason_snippet": "artifact ref",
            },
            {
                "name": "missing_required_artifact_kind",
                "rule": {"type": "artifact_matches_kind", "params": {"kind": "screenshot"}},
                "evidence_refs": [make_summary_artifact_ref()],
                "expected_move_kind": "attach-required-artifact-kind",
                "expected_finality": "mechanically-satisfiable-later",
                "expected_hold_reason": "missing_required_artifact_kind",
                "reason_snippet": "screenshot",
            },
            {
                "name": "missing_result_evidence",
                "rule": {"type": "result_present"},
                "evidence_refs": [make_summary_artifact_ref()],
                "expected_move_kind": "attach-result-evidence",
                "expected_finality": "mechanically-satisfiable-later",
                "expected_hold_reason": "missing_result_evidence",
                "reason_snippet": "result-json",
            },
            {
                "name": "missing_summary_evidence",
                "rule": {"type": "summary_present"},
                "evidence_refs": [
                    {
                        "kind": "result-json",
                        "path": "/workspace/robin/tasks/T000001/jobs/001/result.json",
                        "role": "robin",
                    }
                ],
                "expected_move_kind": "attach-summary-evidence",
                "expected_finality": "mechanically-satisfiable-later",
                "expected_hold_reason": "missing_summary_evidence",
                "reason_snippet": "summary evidence",
            },
            {
                "name": "insufficient_evidence_bundle",
                "rule": {"type": "evidence_bundle_present", "params": {"minimum_count": 3}},
                "evidence_refs": [
                    make_summary_artifact_ref(),
                    {
                        "kind": "result-json",
                        "path": "/workspace/robin/tasks/T000001/jobs/001/result.json",
                        "role": "robin",
                    },
                ],
                "expected_move_kind": "complete-evidence-bundle",
                "expected_finality": "mechanically-satisfiable-later",
                "expected_hold_reason": "insufficient_evidence_bundle",
                "reason_snippet": "evidence bundle",
            },
            {
                "name": "manual_review_required",
                "rule": {"type": "manual_review_required"},
                "evidence_refs": [make_summary_artifact_ref()],
                "expected_move_kind": "capture-manual-review-context",
                "expected_finality": "review-required",
                "expected_hold_reason": "manual_review_required",
                "reason_snippet": "manual review",
            },
            {
                "name": "unsupported_in_slice",
                "rule": {"type": "test_pass"},
                "evidence_refs": [make_summary_artifact_ref()],
                "expected_move_kind": "capture-unsupported-rule-context",
                "expected_finality": "unsupported-in-slice",
                "expected_hold_reason": "test_pass_not_mechanically_supported",
                "reason_snippet": "cannot satisfy",
            },
            {
                "name": "ill_defined",
                "rule": {"type": "artifact_matches_kind", "params": {}},
                "evidence_refs": [make_summary_artifact_ref()],
                "expected_move_kind": "capture-rule-definition-context",
                "expected_finality": "ill-defined",
                "expected_hold_reason": "missing_required_kind_param",
                "reason_snippet": "ill-defined",
            },
        ]

        for scenario in scenarios:
            with self.subTest(scenario=scenario["name"]):
                scenario_root = self.root / scenario["name"]
                storage, processor = build_storage_backed_alfred_processor(
                    scenario_root,
                    now_provider=lambda: "2026-03-30T12:00:00Z",
                )
                processor.process_call(make_task_create_call())
                processor.process_call(
                    make_plan_record_call(
                        plan_version=1,
                        current_active_item="I002",
                        items=[
                            {
                                "item_id": "I001",
                                "title": "Prepare runtime",
                                "description": "Set up the execution slice.",
                                "status": "verified",
                            },
                            {
                                "item_id": "I002",
                                "title": "Hold on verification target",
                                "description": "Current target is held on its verification rule.",
                                "status": "done_unverified",
                                "depends_on": ["I001"],
                                "verification_rule": scenario["rule"],
                                "evidence_refs": scenario["evidence_refs"],
                            },
                        ],
                    )
                )

                task_summary = storage.latest_task_state_summary("T000001")
                proof_item = storage.read_relevant_proof_item_summary("T000001")
                posture_effect = storage.evaluate_supported_call_posture_effect(
                    "T000001",
                    "continuation.record",
                )
                policy = storage.evaluate_supported_call_policy(
                    "T000001",
                    "job.start",
                    job_id="T000001.J001",
                )
                storage.close()

                self.assertEqual(scenario["expected_move_kind"], task_summary["best_next_move"]["move_kind"])
                self.assertEqual(scenario["expected_finality"], task_summary["dominant_rule_finality_kind"])
                self.assertEqual(
                    scenario["expected_hold_reason"],
                    task_summary["execution_hold_reason"],
                )
                self.assertEqual(
                    scenario["expected_hold_reason"],
                    task_summary["execution_hold_detail_kind"],
                )
                self.assertEqual(
                    scenario["expected_hold_reason"],
                    proof_item["unmet_requirement_kind"],
                )
                self.assertEqual(
                    scenario["expected_finality"],
                    proof_item["rule_finality_kind"],
                )
                self.assertEqual(
                    ("checkpoint.create", "continuation.record"),
                    task_summary["allowed_call_types"],
                )
                self.assertFalse(policy["allowed"])
                self.assertIn(scenario["reason_snippet"], task_summary["best_next_move"]["reason"])
                self.assertIn(scenario["reason_snippet"], posture_effect["reason"])

    def test_result_present_rule_does_not_treat_summary_only_followup_as_result_proof(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Attach result payload",
                        "description": "Needs a result-json style proof object, not only a summary.",
                        "status": "done_unverified",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "result_present"},
                        "evidence_refs": [make_summary_artifact_ref()],
                    },
                ],
            )
        )

        processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[
                    make_summary_artifact_ref(
                        artifact_id="T000001.J001.A002",
                        kind="summary",
                    )
                ],
            )
        )

        proof_item = storage.read_relevant_proof_item_summary("T000001")
        task_summary = storage.latest_task_state_summary("T000001")
        storage.close()

        self.assertEqual("done_unverified", proof_item["status"])
        self.assertTrue(proof_item["rule_mechanical"])
        self.assertTrue(proof_item["proof_gate_supported"])
        self.assertFalse(proof_item["proof_satisfied"])
        self.assertEqual("mechanically-satisfiable-later", proof_item["rule_finality_kind"])
        self.assertEqual("missing_result_evidence", proof_item["unmet_requirement_kind"])
        self.assertEqual(
            "result-json",
            proof_item["unmet_requirement_detail"]["required_evidence_kind"],
        )
        self.assertIn("summary", proof_item["unmet_requirement_detail"]["observed_evidence_kinds"])
        self.assertEqual("proof-gathering", task_summary["dominant_target_kind"])
        self.assertEqual(
            "missing_result_evidence",
            task_summary["relevant_unmet_requirement_kind"],
        )

    def test_task_and_job_summaries_surface_exact_rule_aware_hold_detail(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(make_job_start_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Need screenshot proof",
                        "description": "Current target needs a screenshot artifact.",
                        "status": "done_unverified",
                        "depends_on": ["I001"],
                        "verification_rule": {
                            "type": "artifact_matches_kind",
                            "params": {"kind": "screenshot"},
                        },
                        "evidence_refs": [make_summary_artifact_ref()],
                    },
                ],
            )
        )

        task_summary = storage.latest_task_state_summary("T000001")
        job_summary = storage.read_job_state_summary("T000001.J001")
        active_plan_summary = storage.read_active_plan_summary("T000001")
        storage.close()

        self.assertEqual("proof-gathering", task_summary["dominant_target_kind"])
        self.assertEqual("mechanically-satisfiable-later", task_summary["dominant_rule_finality_kind"])
        self.assertEqual("missing_required_artifact_kind", task_summary["dominant_unmet_requirement_kind"])
        self.assertEqual("missing_required_artifact_kind", task_summary["execution_hold_detail_kind"])
        self.assertEqual(
            "screenshot",
            task_summary["execution_hold_detail"]["required_kind"],
        )
        self.assertEqual("attach-required-artifact-kind", task_summary["best_next_move"]["move_kind"])
        self.assertEqual(
            "missing_required_artifact_kind",
            job_summary["task_dominant_unmet_requirement_kind"],
        )
        self.assertEqual("missing_required_artifact_kind", job_summary["task_execution_hold_detail_kind"])
        self.assertTrue(job_summary["current_job_subordinate_to_task_focus"])
        self.assertEqual(
            "missing_required_artifact_kind",
            active_plan_summary["relevant_unmet_requirement_kind"],
        )

    def test_evidence_bundle_rule_uses_minimum_count_param_consistently(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Collect a full evidence bundle",
                        "description": "Need a larger evidence bundle before verification.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {
                            "type": "evidence_bundle_present",
                            "params": {"minimum_count": 4},
                        },
                    },
                ],
            )
        )

        processor.process_call(
            make_result_submit_call(
                artifact_refs=[make_summary_artifact_ref()],
                reported_status="succeeded",
            )
        )
        before = storage.read_relevant_proof_item_summary("T000001")

        processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[
                    make_summary_artifact_ref(
                        artifact_id="T000001.J001.A002",
                        kind="screenshot",
                    )
                ],
            )
        )
        after = storage.read_relevant_proof_item_summary("T000001")
        storage.close()

        self.assertEqual("done_unverified", before["status"])
        self.assertEqual("insufficient_evidence_bundle", before["unmet_requirement_kind"])
        self.assertEqual(
            4,
            before["unmet_requirement_detail"]["required_minimum_count"],
        )
        self.assertEqual(
            2,
            before["unmet_requirement_detail"]["current_evidence_count"],
        )
        self.assertTrue(before["can_be_satisfied_by_supported_evidence_calls"])
        self.assertEqual("verified", after["status"])
        self.assertTrue(after["proof_satisfied"])

    def test_manual_review_rule_keeps_item_done_unverified_even_with_evidence(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Produce proof needing review",
                        "description": "Return evidence that still needs review.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "manual_review_required"},
                    },
                ],
            )
        )

        processor.process_call(
            make_result_submit_call(
                artifact_refs=[make_summary_artifact_ref()],
                reported_status="succeeded",
            )
        )

        item_summary = storage.read_plan_item_summary("T000001", 1, "I002")
        task_summary = storage.latest_task_state_summary("T000001")
        storage.close()

        self.assertEqual("done_unverified", item_summary["status"])
        self.assertFalse(item_summary["proof_satisfied"])
        self.assertFalse(item_summary["proof_gate_supported"])
        self.assertFalse(item_summary["rule_mechanical"])
        self.assertEqual("review-required", item_summary["rule_finality_kind"])
        self.assertEqual("manual_review_required", item_summary["unmet_requirement_kind"])
        self.assertTrue(item_summary["review_required"])
        self.assertFalse(item_summary["can_be_satisfied_by_supported_evidence_calls"])
        self.assertTrue(item_summary["can_only_remain_review_needed"])
        self.assertEqual("review-needed", item_summary["proof_policy_kind"])
        self.assertTrue(item_summary["is_waiting_on_review"])
        self.assertEqual(2, item_summary["evidence_count"])
        self.assertTrue(task_summary["is_waiting_on_review"])
        self.assertFalse(task_summary["is_waiting_on_proof"])
        self.assertEqual("review-needed", task_summary["dominant_target_kind"])
        self.assertEqual("review-needed", task_summary["dominant_blocker_kind"])
        self.assertEqual("review-required", task_summary["relevant_rule_finality_kind"])
        self.assertTrue(task_summary["relevant_review_required"])
        self.assertTrue(task_summary["relevant_can_only_remain_review_needed"])
        self.assertTrue(task_summary["execution_held"])
        self.assertFalse(task_summary["execution_allowed"])
        self.assertEqual("review-needed", task_summary["execution_hold_kind"])

    def test_done_unverified_item_is_surfaced_as_verification_pending(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Produce proof needing review",
                        "description": "Return evidence that still needs review.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "manual_review_required"},
                    },
                ],
            )
        )

        processor.process_call(
            make_result_submit_call(
                artifact_refs=[make_summary_artifact_ref()],
                reported_status="succeeded",
            )
        )

        proof_item = storage.read_relevant_proof_item_summary("T000001")
        task_summary = storage.latest_task_state_summary("T000001")
        job_summary = storage.read_job_state_summary("T000001.J001")
        resume_target = storage.resolve_next_plan_resume_target("T000001")
        storage.close()

        self.assertEqual("I002", proof_item["item_id"])
        self.assertTrue(proof_item["is_verification_pending"])
        self.assertEqual("review-needed", proof_item["proof_policy_kind"])
        self.assertTrue(proof_item["is_waiting_on_review"])
        self.assertEqual("manual_review_required", proof_item["proof_gate_reason"])
        self.assertTrue(task_summary["is_verification_pending"])
        self.assertTrue(task_summary["is_waiting_on_review"])
        self.assertFalse(task_summary["is_waiting_on_proof"])
        self.assertEqual("manual_review_required", task_summary["relevant_proof_gate_reason"])
        self.assertEqual("review-needed", task_summary["dominant_target_kind"])
        self.assertEqual("waiting-on-review", task_summary["effective_task_posture"])
        self.assertTrue(task_summary["execution_held"])
        self.assertEqual("review-needed", task_summary["execution_hold_kind"])
        self.assertEqual(
            ("checkpoint.create", "continuation.record"),
            task_summary["allowed_call_types"],
        )
        self.assertEqual("continuation.record", task_summary["best_next_call_type"])
        self.assertEqual("capture-manual-review-context", task_summary["best_next_move"]["move_kind"])
        self.assertEqual("preserve", task_summary["best_next_move_effect_kind"])
        self.assertFalse(task_summary["current_job_is_primary_focus"])
        self.assertTrue(task_summary["relevant_plan_item_is_primary_focus"])
        self.assertEqual("review-needed", job_summary["relevant_plan_item_proof_policy_kind"])
        self.assertTrue(job_summary["relevant_plan_item_waiting_on_review"])
        self.assertTrue(job_summary["current_job_subordinate_to_task_focus"])
        self.assertTrue(job_summary["task_execution_held"])
        self.assertEqual("review-needed", job_summary["task_execution_hold_kind"])
        self.assertEqual(
            "capture-manual-review-context",
            job_summary["task_best_next_move"]["move_kind"],
        )
        self.assertEqual("review-needed", resume_target["target_kind"])
        self.assertEqual("I002", resume_target["item"]["item_id"])

    def test_unsupported_verification_rule_is_distinct_from_missing_evidence(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Collect proof needing test evaluation",
                        "description": "Return evidence Alfred cannot judge mechanically.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "test_pass"},
                    },
                ],
            )
        )

        processor.process_call(
            make_result_submit_call(
                artifact_refs=[make_summary_artifact_ref()],
                reported_status="succeeded",
            )
        )

        proof_item = storage.read_relevant_proof_item_summary("T000001")
        task_summary = storage.latest_task_state_summary("T000001")
        resume_target = storage.resolve_next_plan_resume_target("T000001")
        storage.close()

        self.assertEqual("done_unverified", proof_item["status"])
        self.assertFalse(proof_item["proof_gate_supported"])
        self.assertEqual("test_pass_not_mechanically_supported", proof_item["proof_gate_reason"])
        self.assertEqual("unsupported-in-slice", proof_item["rule_finality_kind"])
        self.assertFalse(proof_item["review_required"])
        self.assertFalse(proof_item["can_be_satisfied_by_supported_evidence_calls"])
        self.assertTrue(proof_item["can_only_remain_review_needed"])
        self.assertEqual("review-needed", proof_item["proof_policy_kind"])
        self.assertTrue(proof_item["is_waiting_on_review"])
        self.assertFalse(proof_item["is_waiting_on_proof"])
        self.assertTrue(task_summary["is_waiting_on_review"])
        self.assertEqual("review-needed", task_summary["dominant_target_kind"])
        self.assertEqual("unsupported-in-slice", task_summary["relevant_rule_finality_kind"])
        self.assertFalse(task_summary["relevant_review_required"])
        self.assertTrue(task_summary["execution_held"])
        self.assertEqual("review-needed", task_summary["execution_hold_kind"])
        self.assertEqual("review-needed", resume_target["target_kind"])

    def test_next_executable_unavailable_explains_dependency_unverified(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Produce required proof",
                        "description": "Return the artifact the next step depends on.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "artifact_exists"},
                    },
                    {
                        "item_id": "I003",
                        "title": "Resume dependent follow-up",
                        "description": "Continue once the predecessor is verified.",
                        "status": "todo",
                        "depends_on": ["I002"],
                    },
                ],
            )
        )

        processor.process_call(make_result_submit_call(reported_status="succeeded"))

        next_executable = storage.resolve_next_executable_plan_item("T000001")
        unavailable_reason = storage.explain_next_executable_unavailable("T000001")
        task_summary = storage.latest_task_state_summary("T000001")
        job_summary = storage.read_job_state_summary("T000001.J001")
        storage.close()

        self.assertIsNone(next_executable)
        self.assertEqual("dependency_unverified", unavailable_reason["reason"])
        self.assertEqual("I003", unavailable_reason["waiting_item_id"])
        self.assertEqual("I002", unavailable_reason["blocking_dependency_item_id"])
        self.assertEqual("artifact_exists", unavailable_reason["verification_rule_type"])
        self.assertEqual("missing_artifact_ref", unavailable_reason["proof_gate_reason"])
        self.assertEqual("proof-gathering", unavailable_reason["blocking_policy_kind"])
        self.assertEqual("dependency_unverified", task_summary["next_executable_unavailable_reason"]["reason"])
        self.assertEqual("proof-gathering", job_summary["relevant_plan_item_proof_policy_kind"])
        self.assertTrue(job_summary["relevant_plan_item_waiting_on_proof"])
        self.assertTrue(task_summary["execution_held"])
        self.assertEqual("proof-gathering", task_summary["execution_hold_kind"])

    def test_continuation_record_can_promote_done_unverified_item_to_verified(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Produce required proof",
                        "description": "Return the artifact the next step depends on.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "artifact_exists"},
                    },
                    {
                        "item_id": "I003",
                        "title": "Resume dependent follow-up",
                        "description": "Continue once the predecessor is verified.",
                        "status": "todo",
                        "depends_on": ["I002"],
                    },
                ],
            )
        )

        processor.process_call(make_result_submit_call(reported_status="succeeded"))
        processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref()],
            )
        )

        proof_item = storage.read_plan_item_summary("T000001", 1, "I002")
        active_item = storage.resolve_active_plan_item("T000001")
        next_target = storage.resolve_next_plan_resume_target("T000001")
        allowed_calls = storage.allowed_supported_call_types("T000001")
        best_move = storage.best_next_supported_move("T000001")
        storage.close()

        self.assertEqual("verified", proof_item["status"])
        self.assertTrue(proof_item["proof_satisfied"])
        self.assertEqual("I003", active_item["item_id"])
        self.assertEqual("next-executable", next_target["target_kind"])
        self.assertEqual("I003", next_target["item"]["item_id"])
        self.assertEqual(
            (
                "job.start",
                "child_job.request",
                "result.submit",
                "failure.report",
                "checkpoint.create",
                "continuation.record",
            ),
            allowed_calls,
        )
        self.assertEqual("start-next-executable", best_move["move_kind"])

    def test_job_start_is_rejected_while_task_waits_on_proof(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Produce required proof",
                        "description": "Return the artifact the next step depends on.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "artifact_exists"},
                    },
                ],
            )
        )
        processor.process_call(make_result_submit_call(reported_status="succeeded"))

        policy = storage.evaluate_supported_call_policy(
            "T000001",
            "job.start",
            job_id="T000001.J001",
        )
        with self.assertRaises(GarageAlfredProcessingError) as ctx:
            processor.process_call(make_job_start_call())

        self.assertFalse(policy["allowed"])
        self.assertEqual("proof-gathering", policy["dominant_target_kind"])
        self.assertEqual("proof-gathering", policy["execution_hold_kind"])
        self.assertEqual("continuation.record", policy["best_next_move"]["call_type"])
        self.assertIn("held on 'proof-gathering'", str(ctx.exception))
        storage.close()

    def test_job_start_is_rejected_while_task_waits_on_review(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Produce proof needing review",
                        "description": "Return evidence that still needs review.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "manual_review_required"},
                    },
                ],
            )
        )
        processor.process_call(
            make_result_submit_call(
                artifact_refs=[make_summary_artifact_ref()],
                reported_status="succeeded",
            )
        )

        policy = storage.evaluate_supported_call_policy(
            "T000001",
            "job.start",
            job_id="T000001.J001",
        )
        with self.assertRaises(GarageAlfredProcessingError) as ctx:
            processor.process_call(make_job_start_call())

        self.assertFalse(policy["allowed"])
        self.assertEqual("review-needed", policy["dominant_target_kind"])
        self.assertEqual("review-needed", policy["execution_hold_kind"])
        self.assertEqual("continuation.record", policy["best_next_move"]["call_type"])
        self.assertIn("held on 'review-needed'", str(ctx.exception))
        storage.close()

    def test_child_job_request_is_rejected_while_task_waits_on_review(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Produce proof needing review",
                        "description": "Return evidence that still needs review.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "manual_review_required"},
                    },
                ],
            )
        )
        processor.process_call(
            make_result_submit_call(
                artifact_refs=[make_summary_artifact_ref()],
                reported_status="succeeded",
            )
        )

        with self.assertRaises(GarageAlfredProcessingError) as ctx:
            processor.process_call(make_child_job_request_call())

        self.assertIn("held on 'review-needed'", str(ctx.exception))
        storage.close()

    def test_continuation_record_remains_usable_while_task_waits_on_review(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Produce proof needing review",
                        "description": "Return evidence that still needs review.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "manual_review_required"},
                    },
                ],
            )
        )
        processor.process_call(
            make_result_submit_call(
                artifact_refs=[make_summary_artifact_ref()],
                reported_status="succeeded",
            )
        )

        result = processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref(artifact_id="T000001.J001.A002")],
            )
        )
        task_summary = storage.latest_task_state_summary("T000001")
        proof_item = storage.read_relevant_proof_item_summary("T000001")
        storage.close()

        self.assertEqual("continuation.recorded", result.result["event_type"])
        self.assertEqual("review-needed", task_summary["dominant_target_kind"])
        self.assertTrue(task_summary["execution_held"])
        self.assertEqual("continuation.record", task_summary["best_next_call_type"])
        self.assertEqual("preserve", task_summary["best_next_move_effect_kind"])
        self.assertEqual("review-needed", proof_item["proof_policy_kind"])
        self.assertFalse(proof_item["proof_satisfied"])

    def test_waiting_on_child_rejects_new_handoff_but_allows_current_child_progress(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(make_job_start_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Run child leg",
                        "description": "Delegate the blocking child work.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                    },
                ],
            )
        )

        child = processor.process_call(make_child_job_request_call())
        child_job_id = child.result["job_id"]
        task_summary = storage.latest_task_state_summary("T000001")
        rejected_policy = storage.evaluate_supported_call_policy(
            "T000001",
            "child_job.request",
            job_id="T000001.J001",
        )
        started = processor.process_call(make_job_start_call(job_id=child_job_id))

        with self.assertRaises(GarageAlfredProcessingError) as ctx:
            processor.process_call(make_child_job_request_call())

        self.assertEqual("waiting-on-child", task_summary["dominant_target_kind"])
        self.assertTrue(task_summary["execution_held"])
        self.assertEqual("waiting-on-child", task_summary["execution_hold_kind"])
        self.assertEqual("job.start", task_summary["best_next_call_type"])
        self.assertEqual("preserve", task_summary["best_next_move_effect_kind"])
        self.assertFalse(rejected_policy["allowed"])
        self.assertEqual("job.started", started.result["event_type"])
        self.assertIn("held on 'waiting-on-child'", str(ctx.exception))
        storage.close()

    def test_job_start_is_allowed_when_task_is_ready_for_next_executable(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Produce required proof",
                        "description": "Return the artifact the next step depends on.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "artifact_exists"},
                    },
                    {
                        "item_id": "I003",
                        "title": "Resume dependent follow-up",
                        "description": "Continue once the predecessor is verified.",
                        "status": "todo",
                        "depends_on": ["I002"],
                    },
                ],
            )
        )
        processor.process_call(make_result_submit_call(reported_status="succeeded"))
        processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref()],
            )
        )

        task_summary = storage.latest_task_state_summary("T000001")
        policy = storage.evaluate_supported_call_policy(
            "T000001",
            "job.start",
            job_id="T000001.J001",
        )
        result = processor.process_call(make_job_start_call())
        active_item = storage.resolve_active_plan_item("T000001")
        storage.close()

        self.assertEqual("next-executable", task_summary["dominant_target_kind"])
        self.assertTrue(task_summary["execution_allowed"])
        self.assertFalse(task_summary["execution_held"])
        self.assertEqual("job.start", task_summary["best_next_call_type"])
        self.assertEqual("resolve", task_summary["best_next_move_effect_kind"])
        self.assertTrue(policy["allowed"])
        self.assertEqual("job.started", result.result["event_type"])
        self.assertEqual(2, result.result["attempt_no"])
        self.assertEqual("I003", active_item["item_id"])
        self.assertEqual("in_progress", active_item["status"])

    def test_checkpoint_without_required_artifact_preserves_proof_gathering_posture(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Produce required proof",
                        "description": "Return the artifact the next step depends on.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "artifact_exists"},
                    },
                ],
            )
        )
        processor.process_call(make_result_submit_call(reported_status="succeeded"))

        before = storage.latest_task_state_summary("T000001")
        processor.process_call(make_checkpoint_create_call(plan_version=1))
        after = storage.latest_task_state_summary("T000001")
        storage.close()

        self.assertEqual("proof-gathering", before["dominant_target_kind"])
        self.assertEqual("proof-gathering", after["dominant_target_kind"])
        self.assertEqual("continuation.record", after["best_next_call_type"])
        self.assertEqual("preserve_or_resolve", after["best_next_move_effect_kind"])

    def test_blocked_evidence_review_remains_blocked_after_continuation_enrichment(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Collect blocked evidence",
                        "description": "Capture failure evidence for the blocked step.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                    },
                ],
            )
        )
        processor.process_call(
            make_failure_report_call(
                reported_status="blocked",
                artifact_refs=[make_summary_artifact_ref()],
            )
        )

        before = storage.latest_task_state_summary("T000001")
        processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref(artifact_id="T000001.J001.A002")],
            )
        )
        after = storage.latest_task_state_summary("T000001")
        storage.close()

        self.assertEqual("blocked-evidence-review", before["dominant_target_kind"])
        self.assertEqual("blocked-evidence-review", after["dominant_target_kind"])
        self.assertEqual("continuation.record", after["best_next_call_type"])
        self.assertEqual("preserve", after["best_next_move_effect_kind"])

    def test_checkpoint_call_preserves_proof_gathering_transition_when_gate_stays_unsatisfied(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Need artifact proof",
                        "description": "Still needs an official artifact ref.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "artifact_exists"},
                    },
                ],
            )
        )
        processor.process_call(make_result_submit_call(reported_status="succeeded"))
        before = storage.latest_task_state_summary("T000001")

        processor.process_call(make_checkpoint_create_call(plan_version=1))
        transition = storage.summarize_applied_call_posture_transition(
            "T000001",
            "checkpoint.create",
            before_task_summary=before,
        )
        after = storage.latest_task_state_summary("T000001")
        storage.close()

        self.assertEqual("preserved", transition["transition_kind"])
        self.assertEqual("proof-gathering", transition["before_dominant_target_kind"])
        self.assertEqual("proof-gathering", transition["after_dominant_target_kind"])
        self.assertEqual("missing_artifact_ref", transition["after_unmet_requirement_kind"])
        self.assertFalse(transition["best_next_move_changed"])
        self.assertEqual("proof-gathering", after["dominant_target_kind"])
        self.assertEqual("attach-artifact-ref", after["best_next_move"]["move_kind"])

    def test_continuation_call_refines_proof_gathering_when_wrong_kind_evidence_arrives(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Need screenshot proof",
                        "description": "Needs a screenshot artifact before verification.",
                        "status": "done_unverified",
                        "depends_on": ["I001"],
                        "verification_rule": {
                            "type": "artifact_matches_kind",
                            "params": {"kind": "screenshot"},
                        },
                    },
                ],
            )
        )
        before = storage.latest_task_state_summary("T000001")

        processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref()],
            )
        )
        transition = storage.summarize_applied_call_posture_transition(
            "T000001",
            "continuation.record",
            before_task_summary=before,
        )
        after = storage.latest_task_state_summary("T000001")
        storage.close()

        self.assertEqual("refined", transition["transition_kind"])
        self.assertEqual("proof-gathering", transition["before_dominant_target_kind"])
        self.assertEqual("proof-gathering", transition["after_dominant_target_kind"])
        self.assertEqual("missing_required_artifact_kind", transition["before_unmet_requirement_kind"])
        self.assertEqual("missing_required_artifact_kind", transition["after_unmet_requirement_kind"])
        self.assertNotEqual(
            transition["before_unmet_requirement_detail"],
            transition["after_unmet_requirement_detail"],
        )
        self.assertEqual("attach-required-artifact-kind", after["best_next_move"]["move_kind"])

    def test_continuation_call_resolves_proof_gathering_into_next_executable_when_gate_satisfies(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Produce required proof",
                        "description": "Return the artifact the next step depends on.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "artifact_exists"},
                    },
                    {
                        "item_id": "I003",
                        "title": "Resume dependent follow-up",
                        "description": "Continue once the predecessor is verified.",
                        "status": "todo",
                        "depends_on": ["I002"],
                    },
                ],
            )
        )
        processor.process_call(make_result_submit_call(reported_status="succeeded"))
        before = storage.latest_task_state_summary("T000001")

        processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref()],
            )
        )
        transition = storage.summarize_applied_call_posture_transition(
            "T000001",
            "continuation.record",
            before_task_summary=before,
        )
        after = storage.latest_task_state_summary("T000001")
        storage.close()

        self.assertEqual("resolved", transition["transition_kind"])
        self.assertEqual("proof-gathering", transition["before_dominant_target_kind"])
        self.assertEqual("next-executable", transition["after_dominant_target_kind"])
        self.assertTrue(transition["best_next_move_changed"])
        self.assertEqual("next-executable", after["dominant_target_kind"])
        self.assertEqual("start-next-executable", after["best_next_move"]["move_kind"])
        self.assertTrue(after["execution_allowed"])

    def test_continuation_call_preserves_review_needed_posture_for_manual_review_rule(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Produce proof needing review",
                        "description": "Return evidence that still needs review.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "manual_review_required"},
                    },
                ],
            )
        )
        processor.process_call(
            make_result_submit_call(
                artifact_refs=[make_summary_artifact_ref()],
                reported_status="succeeded",
            )
        )
        before = storage.latest_task_state_summary("T000001")

        processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref(artifact_id="T000001.J001.A002")],
            )
        )
        transition = storage.summarize_applied_call_posture_transition(
            "T000001",
            "continuation.record",
            before_task_summary=before,
        )
        after = storage.latest_task_state_summary("T000001")
        storage.close()

        self.assertEqual("preserved", transition["transition_kind"])
        self.assertEqual("review-needed", transition["before_dominant_target_kind"])
        self.assertEqual("review-needed", transition["after_dominant_target_kind"])
        self.assertEqual("manual_review_required", transition["after_unmet_requirement_kind"])
        self.assertEqual("review-needed", after["dominant_target_kind"])
        self.assertEqual("capture-manual-review-context", after["best_next_move"]["move_kind"])

    def test_continuation_call_preserves_blocked_evidence_review_posture(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Collect blocked evidence",
                        "description": "Capture failure evidence for the blocked step.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                    },
                ],
            )
        )
        processor.process_call(
            make_failure_report_call(
                reported_status="blocked",
                artifact_refs=[make_summary_artifact_ref()],
            )
        )
        before = storage.latest_task_state_summary("T000001")

        processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref(artifact_id="T000001.J001.A002")],
            )
        )
        transition = storage.summarize_applied_call_posture_transition(
            "T000001",
            "continuation.record",
            before_task_summary=before,
        )
        after = storage.latest_task_state_summary("T000001")
        storage.close()

        self.assertEqual("preserved", transition["transition_kind"])
        self.assertEqual("blocked-evidence-review", transition["before_dominant_target_kind"])
        self.assertEqual("blocked-evidence-review", transition["after_dominant_target_kind"])
        self.assertEqual("blocked-evidence-review", after["dominant_target_kind"])
        self.assertEqual("capture-blocked-evidence", after["best_next_move"]["move_kind"])

    def test_child_return_resolves_waiting_on_child_into_next_posture(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(make_job_start_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Run child leg",
                        "description": "Delegate the blocking child work.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "artifact_exists"},
                    },
                    {
                        "item_id": "I003",
                        "title": "Continue follow-up",
                        "description": "Continue once the child-backed proof is verified.",
                        "status": "todo",
                        "depends_on": ["I002"],
                    },
                ],
            )
        )
        child = processor.process_call(make_child_job_request_call())
        child_job_id = child.result["job_id"]
        before = storage.latest_task_state_summary("T000001")

        processor.process_call(
            make_result_submit_call(
                job_id=child_job_id,
                reported_status="succeeded",
            )
        )
        transition = storage.summarize_applied_call_posture_transition(
            "T000001",
            "result.submit",
            before_task_summary=before,
        )
        after = storage.latest_task_state_summary("T000001")
        storage.close()

        self.assertEqual("resolved", transition["transition_kind"])
        self.assertEqual("waiting-on-child", transition["before_dominant_target_kind"])
        self.assertEqual("proof-gathering", transition["after_dominant_target_kind"])
        self.assertFalse(after["current_job_is_primary_focus"])
        self.assertTrue(after["relevant_plan_item_is_primary_focus"])

    def test_job_start_can_restore_current_job_focus_after_next_executable_release(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Produce required proof",
                        "description": "Return the artifact the next step depends on.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "artifact_exists"},
                    },
                    {
                        "item_id": "I003",
                        "title": "Resume dependent follow-up",
                        "description": "Continue once the predecessor is verified.",
                        "status": "todo",
                        "depends_on": ["I002"],
                    },
                ],
            )
        )
        processor.process_call(make_result_submit_call(reported_status="succeeded"))
        processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref()],
            )
        )
        before = storage.latest_task_state_summary("T000001")

        processor.process_call(make_job_start_call())
        transition = storage.summarize_applied_call_posture_transition(
            "T000001",
            "job.start",
            before_task_summary=before,
        )
        after = storage.latest_task_state_summary("T000001")
        storage.close()

        self.assertEqual("resolved", transition["transition_kind"])
        self.assertEqual("next-executable", transition["before_dominant_target_kind"])
        self.assertEqual("active-item", transition["after_dominant_target_kind"])
        self.assertTrue(transition["current_job_focus_changed"])
        self.assertTrue(transition["current_job_primary_focus_after"])
        self.assertTrue(after["current_job_is_primary_focus"])
        self.assertEqual("continue-active-execution", after["best_next_move"]["move_kind"])

    def test_accepted_checkpoint_call_returns_refreshed_preserved_posture_guidance(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Need artifact proof",
                        "description": "Still needs an official artifact ref.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "artifact_exists"},
                    },
                ],
            )
        )
        processor.process_call(make_result_submit_call(reported_status="succeeded"))

        result = processor.process_call(make_checkpoint_create_call(plan_version=1))
        guidance = result.result["post_call_guidance"]
        follow_up = guidance["immediate_follow_up"]
        next_call_hint = guidance["next_call_hint"]
        next_call_draft = guidance["next_call_draft"]
        default_readiness = guidance["next_call_draft_readiness"]
        default_preflight = guidance["next_call_preflight"]
        supplied_readiness = processor.summarize_next_call_draft_readiness(
            "T000001",
            supplied_fields={
                "from_role": "jarvis",
                "to_role": "alfred",
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/continuation.md",
                    "role": "jarvis",
                },
                "artifact_refs": [make_summary_artifact_ref()],
                "schema_version": "v9.9",
                "bogus": "ignored",
            },
        )
        supplied_preflight = processor.prepare_next_call_from_draft(
            "T000001",
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/continuation.md",
                    "role": "jarvis",
                },
                "artifact_refs": [make_summary_artifact_ref()],
                "schema_version": "v9.9",
                "bogus": "ignored",
            },
        )
        storage.close()

        self.assertEqual("preserved", guidance["posture_transition"]["transition_kind"])
        self.assertEqual("proof-gathering", guidance["dominant_target_kind"])
        self.assertEqual("proof-gathering", guidance["dominant_blocker_kind"])
        self.assertFalse(guidance["execution_allowed"])
        self.assertEqual("proof-gathering", guidance["execution_hold_kind"])
        self.assertEqual("attach-artifact-ref", guidance["best_next_move"]["move_kind"])
        self.assertEqual("gather-proof-next", follow_up["follow_up_behavior_kind"])
        self.assertTrue(follow_up["productive_in_slice"])
        self.assertTrue(follow_up["actionable_evidence_gathering"])
        self.assertEqual("attach-artifact-ref", follow_up["best_next_move"]["move_kind"])
        self.assertEqual(
            ("checkpoint.create",),
            tuple(move["call_type"] for move in follow_up["secondary_allowed_moves"]),
        )
        self.assertIn(
            "job.start",
            tuple(move["call_type"] for move in follow_up["blocked_moves"]),
        )
        self.assertEqual("caller-input-still-required", next_call_hint["hint_kind"])
        self.assertEqual("continuation.record", next_call_hint["recommended_call_type"])
        self.assertEqual("T000001", next_call_hint["task_id"])
        self.assertEqual("T000001.J001", next_call_hint["job_id"])
        self.assertEqual("I002", next_call_hint["target_item_id"])
        self.assertFalse(next_call_hint["execution_ready"])
        self.assertTrue(next_call_hint["requires_additional_user_or_agent_input"])
        self.assertFalse(next_call_hint["context_only"])
        self.assertFalse(next_call_hint["unavailable_in_slice"])
        self.assertEqual("partially-ready", next_call_draft["draft_kind"])
        self.assertEqual("continuation.record", next_call_draft["call_type"])
        self.assertEqual("v0.1", next_call_draft["known_fields"]["schema_version"])
        self.assertEqual("continuation.record", next_call_draft["known_fields"]["call_type"])
        self.assertEqual("T000001", next_call_draft["known_fields"]["task_id"])
        self.assertEqual("T000001.J001", next_call_draft["known_fields"]["job_id"])
        self.assertEqual(1, next_call_draft["known_fields"]["plan_version"])
        self.assertEqual(
            ("from_role", "to_role", "payload_ref"),
            next_call_draft["missing_required_fields"],
        )
        self.assertEqual(("artifact_refs",), next_call_draft["optional_fields_available"])
        self.assertEqual(
            ("payload_ref", "payload.content_ref", "artifact_refs"),
            next_call_draft["cannot_be_prefilled_fields"],
        )
        self.assertFalse(next_call_draft["executable_now"])
        self.assertTrue(next_call_draft["partially_ready"])
        self.assertFalse(next_call_draft["context_only"])
        self.assertFalse(next_call_draft["unavailable_in_slice"])
        self.assertEqual("partially-ready", default_readiness["readiness_kind"])
        self.assertEqual(
            ("from_role", "to_role", "payload_ref"),
            default_readiness["missing_required_fields"],
        )
        self.assertFalse(default_readiness["executable_now"])
        self.assertTrue(default_readiness["partially_ready"])
        self.assertEqual("not_ready_missing_fields", default_preflight["preflight_kind"])
        self.assertIsNone(default_preflight["prepared_call"])
        self.assertEqual(("payload_ref",), default_preflight["missing_required_fields"])
        self.assertFalse(default_preflight["ready_to_submit"])
        self.assertFalse(default_preflight["context_only"])
        self.assertEqual("executable-now", supplied_readiness["readiness_kind"])
        self.assertEqual((), supplied_readiness["missing_required_fields"])
        self.assertEqual(
            ("from_role", "to_role", "payload_ref", "artifact_refs"),
            supplied_readiness["accepted_supplied_fields"],
        )
        self.assertEqual(("bogus",), supplied_readiness["ignored_supplied_fields"])
        self.assertEqual(("schema_version",), supplied_readiness["disallowed_supplied_fields"])
        self.assertTrue(supplied_readiness["executable_now"])
        self.assertEqual("ready_to_submit", supplied_preflight["preflight_kind"])
        self.assertEqual((), supplied_preflight["missing_required_fields"])
        self.assertEqual(
            ("payload_ref", "artifact_refs"),
            supplied_preflight["accepted_supplied_fields"],
        )
        self.assertEqual(("bogus",), supplied_preflight["ignored_supplied_fields"])
        self.assertEqual(("schema_version",), supplied_preflight["disallowed_supplied_fields"])
        self.assertTrue(supplied_preflight["ready_to_submit"])
        self.assertFalse(supplied_preflight["context_only"])
        self.assertEqual(
            {
                "schema_version": "v0.1",
                "call_type": "continuation.record",
                "task_id": "T000001",
                "job_id": "T000001.J001",
                "plan_version": 1,
                "from_role": "jarvis",
                "to_role": "alfred",
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/continuation.md",
                    "role": "jarvis",
                },
                "artifact_refs": [make_summary_artifact_ref()],
            },
            supplied_preflight["prepared_call"],
        )
        self.assertEqual("checkpoint.create", result.call_type)

    def test_accepted_continuation_call_returns_resolved_next_executable_guidance(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Produce required proof",
                        "description": "Return the artifact the next step depends on.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "artifact_exists"},
                    },
                    {
                        "item_id": "I003",
                        "title": "Resume dependent follow-up",
                        "description": "Continue once the predecessor is verified.",
                        "status": "todo",
                        "depends_on": ["I002"],
                    },
                ],
            )
        )
        processor.process_call(make_result_submit_call(reported_status="succeeded"))

        result = processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref()],
            )
        )
        guidance = result.result["post_call_guidance"]
        follow_up = guidance["immediate_follow_up"]
        next_call_hint = guidance["next_call_hint"]
        next_call_draft = guidance["next_call_draft"]
        readiness = guidance["next_call_draft_readiness"]
        preflight = guidance["next_call_preflight"]
        storage.close()

        self.assertEqual("resolved", guidance["posture_transition"]["transition_kind"])
        self.assertEqual("next-executable", guidance["dominant_target_kind"])
        self.assertIsNone(guidance["dominant_blocker_kind"])
        self.assertTrue(guidance["execution_allowed"])
        self.assertEqual("start-next-executable", guidance["best_next_move"]["move_kind"])
        self.assertEqual("job.start", guidance["best_next_move"]["call_type"])
        self.assertEqual("start-next-executable-next", follow_up["follow_up_behavior_kind"])
        self.assertTrue(follow_up["productive_in_slice"])
        self.assertTrue(follow_up["actionable_execution"])
        self.assertFalse(follow_up["requires_non_mechanical_review"])
        self.assertEqual("job.start", follow_up["best_next_move"]["call_type"])
        self.assertEqual("executable-now", next_call_hint["hint_kind"])
        self.assertEqual("job.start", next_call_hint["recommended_call_type"])
        self.assertEqual("T000001", next_call_hint["task_id"])
        self.assertEqual("T000001.J001", next_call_hint["job_id"])
        self.assertEqual("I003", next_call_hint["target_item_id"])
        self.assertTrue(next_call_hint["execution_ready"])
        self.assertFalse(next_call_hint["requires_additional_user_or_agent_input"])
        self.assertFalse(next_call_hint["context_only"])
        self.assertFalse(next_call_hint["unavailable_in_slice"])
        self.assertEqual("executable-now", next_call_draft["draft_kind"])
        self.assertEqual("job.start", next_call_draft["call_type"])
        self.assertEqual(
            {
                "schema_version": "v0.1",
                "call_type": "job.start",
                "task_id": "T000001",
                "job_id": "T000001.J001",
            },
            next_call_draft["known_fields"],
        )
        self.assertEqual(
            ("from_role", "to_role", "reported_at"),
            next_call_draft["missing_required_fields"],
        )
        self.assertTrue(next_call_draft["executable_now"])
        self.assertFalse(next_call_draft["partially_ready"])
        self.assertFalse(next_call_draft["context_only"])
        self.assertFalse(next_call_draft["unavailable_in_slice"])
        self.assertEqual("executable-now", readiness["readiness_kind"])
        self.assertEqual((), readiness["missing_required_fields"])
        self.assertTrue(readiness["executable_now"])
        self.assertFalse(readiness["partially_ready"])
        self.assertEqual("ready_to_submit", preflight["preflight_kind"])
        self.assertTrue(preflight["ready_to_submit"])
        self.assertFalse(preflight["context_only"])
        self.assertEqual(
            {
                "schema_version": "v0.1",
                "call_type": "job.start",
                "task_id": "T000001",
                "job_id": "T000001.J001",
                "from_role": "jarvis",
                "to_role": "alfred",
                "reported_at": "2026-03-30T12:00:00Z",
            },
            preflight["prepared_call"],
        )

    def test_accepted_continuation_call_returns_review_held_guidance(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Produce proof needing review",
                        "description": "Return evidence that still needs review.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "manual_review_required"},
                    },
                ],
            )
        )
        processor.process_call(
            make_result_submit_call(
                artifact_refs=[make_summary_artifact_ref()],
                reported_status="succeeded",
            )
        )

        result = processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref(artifact_id="T000001.J001.A002")],
            )
        )
        guidance = result.result["post_call_guidance"]
        follow_up = guidance["immediate_follow_up"]
        next_call_hint = guidance["next_call_hint"]
        next_call_draft = guidance["next_call_draft"]
        default_readiness = guidance["next_call_draft_readiness"]
        default_preflight = guidance["next_call_preflight"]
        supplied_readiness = processor.summarize_next_call_draft_readiness(
            "T000001",
            supplied_fields={
                "from_role": "jarvis",
                "to_role": "alfred",
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/review.md",
                    "role": "jarvis",
                },
            },
        )
        supplied_preflight = processor.prepare_next_call_from_draft(
            "T000001",
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/review.md",
                    "role": "jarvis",
                },
            },
        )
        storage.close()

        self.assertEqual("preserved", guidance["posture_transition"]["transition_kind"])
        self.assertEqual("review-needed", guidance["dominant_target_kind"])
        self.assertEqual("review-needed", guidance["dominant_blocker_kind"])
        self.assertFalse(guidance["execution_allowed"])
        self.assertEqual("review-needed", guidance["execution_hold_kind"])
        self.assertEqual(
            "capture-manual-review-context",
            guidance["best_next_move"]["move_kind"],
        )
        self.assertEqual(
            "review-required",
            guidance["refreshed_task_policy"]["dominant_rule_finality_kind"],
        )
        self.assertEqual("capture-review-context-next", follow_up["follow_up_behavior_kind"])
        self.assertFalse(follow_up["productive_in_slice"])
        self.assertTrue(follow_up["requires_non_mechanical_review"])
        self.assertTrue(follow_up["review_context_capture_only"])
        self.assertFalse(follow_up["actionable_execution"])
        self.assertEqual("context-only", next_call_hint["hint_kind"])
        self.assertEqual("continuation.record", next_call_hint["recommended_call_type"])
        self.assertEqual("I002", next_call_hint["target_item_id"])
        self.assertFalse(next_call_hint["execution_ready"])
        self.assertTrue(next_call_hint["requires_additional_user_or_agent_input"])
        self.assertTrue(next_call_hint["context_only"])
        self.assertFalse(next_call_hint["unavailable_in_slice"])
        self.assertEqual("context-only", next_call_draft["draft_kind"])
        self.assertEqual("continuation.record", next_call_draft["call_type"])
        self.assertEqual("T000001", next_call_draft["known_fields"]["task_id"])
        self.assertEqual("T000001.J001", next_call_draft["known_fields"]["job_id"])
        self.assertEqual(1, next_call_draft["known_fields"]["plan_version"])
        self.assertEqual(
            ("from_role", "to_role", "payload_ref"),
            next_call_draft["missing_required_fields"],
        )
        self.assertFalse(next_call_draft["executable_now"])
        self.assertFalse(next_call_draft["partially_ready"])
        self.assertTrue(next_call_draft["context_only"])
        self.assertFalse(next_call_draft["unavailable_in_slice"])
        self.assertEqual("context-only", default_readiness["readiness_kind"])
        self.assertEqual("context-only", supplied_readiness["readiness_kind"])
        self.assertTrue(supplied_readiness["context_only"])
        self.assertFalse(supplied_readiness["executable_now"])
        self.assertEqual(
            "context_only_not_submittable", default_preflight["preflight_kind"]
        )
        self.assertIsNone(default_preflight["prepared_call"])
        self.assertEqual(("payload_ref",), default_preflight["missing_required_fields"])
        self.assertFalse(default_preflight["ready_to_submit"])
        self.assertTrue(default_preflight["context_only"])
        self.assertEqual(
            "context_only_not_submittable", supplied_preflight["preflight_kind"]
        )
        self.assertFalse(supplied_preflight["ready_to_submit"])
        self.assertTrue(supplied_preflight["context_only"])
        self.assertEqual((), supplied_preflight["missing_required_fields"])
        self.assertEqual(
            {
                "schema_version": "v0.1",
                "call_type": "continuation.record",
                "task_id": "T000001",
                "job_id": "T000001.J001",
                "plan_version": 1,
                "from_role": "jarvis",
                "to_role": "alfred",
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/review.md",
                    "role": "jarvis",
                },
            },
            supplied_preflight["prepared_call"],
        )

    def test_accepted_continuation_call_returns_blocked_evidence_guidance(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Collect blocked evidence",
                        "description": "Capture failure evidence for the blocked step.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                    },
                ],
            )
        )
        processor.process_call(
            make_failure_report_call(
                reported_status="blocked",
                artifact_refs=[make_summary_artifact_ref()],
            )
        )

        result = processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref(artifact_id="T000001.J001.A002")],
            )
        )
        guidance = result.result["post_call_guidance"]
        follow_up = guidance["immediate_follow_up"]
        next_call_hint = guidance["next_call_hint"]
        next_call_draft = guidance["next_call_draft"]
        default_readiness = guidance["next_call_draft_readiness"]
        default_preflight = guidance["next_call_preflight"]
        supplied_readiness = processor.summarize_next_call_draft_readiness(
            "T000001",
            supplied_fields={
                "from_role": "jarvis",
                "to_role": "alfred",
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/blocked.md",
                    "role": "jarvis",
                },
            },
        )
        supplied_preflight = processor.prepare_next_call_from_draft(
            "T000001",
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/blocked.md",
                    "role": "jarvis",
                },
            },
        )
        storage.close()

        self.assertEqual("preserved", guidance["posture_transition"]["transition_kind"])
        self.assertEqual("blocked-evidence-review", guidance["dominant_target_kind"])
        self.assertEqual("blocked-evidence-review", guidance["dominant_blocker_kind"])
        self.assertFalse(guidance["execution_allowed"])
        self.assertEqual("blocked-evidence-review", guidance["execution_hold_kind"])
        self.assertEqual(
            "capture-blocked-evidence",
            guidance["best_next_move"]["move_kind"],
        )
        self.assertEqual("capture-blocked-evidence-next", follow_up["follow_up_behavior_kind"])
        self.assertFalse(follow_up["productive_in_slice"])
        self.assertTrue(follow_up["holds_on_blocked_evidence"])
        self.assertTrue(follow_up["blocked_evidence_context_capture_only"])
        self.assertEqual("context-only", next_call_hint["hint_kind"])
        self.assertEqual("continuation.record", next_call_hint["recommended_call_type"])
        self.assertEqual("I002", next_call_hint["target_item_id"])
        self.assertFalse(next_call_hint["execution_ready"])
        self.assertTrue(next_call_hint["context_only"])
        self.assertFalse(next_call_hint["unavailable_in_slice"])
        self.assertEqual("context-only", next_call_draft["draft_kind"])
        self.assertEqual("continuation.record", next_call_draft["call_type"])
        self.assertEqual(
            ("from_role", "to_role", "payload_ref"),
            next_call_draft["missing_required_fields"],
        )
        self.assertTrue(next_call_draft["context_only"])
        self.assertFalse(next_call_draft["unavailable_in_slice"])
        self.assertEqual("context-only", default_readiness["readiness_kind"])
        self.assertEqual("context-only", supplied_readiness["readiness_kind"])
        self.assertTrue(supplied_readiness["context_only"])
        self.assertFalse(supplied_readiness["executable_now"])
        self.assertEqual(
            "context_only_not_submittable", default_preflight["preflight_kind"]
        )
        self.assertIsNone(default_preflight["prepared_call"])
        self.assertEqual(("payload_ref",), default_preflight["missing_required_fields"])
        self.assertEqual(
            "context_only_not_submittable", supplied_preflight["preflight_kind"]
        )
        self.assertFalse(supplied_preflight["ready_to_submit"])
        self.assertTrue(supplied_preflight["context_only"])
        self.assertEqual(
            {
                "schema_version": "v0.1",
                "call_type": "continuation.record",
                "task_id": "T000001",
                "job_id": "T000001.J001",
                "plan_version": 1,
                "from_role": "jarvis",
                "to_role": "alfred",
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/blocked.md",
                    "role": "jarvis",
                },
            },
            supplied_preflight["prepared_call"],
        )

    def test_accepted_child_job_request_returns_waiting_on_child_follow_up_guidance(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(make_job_start_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Run child leg",
                        "description": "Delegate the blocking child work.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                    },
                ],
            )
        )

        result = processor.process_call(make_child_job_request_call())
        guidance = result.result["post_call_guidance"]
        follow_up = guidance["immediate_follow_up"]
        next_call_hint = guidance["next_call_hint"]
        next_call_draft = guidance["next_call_draft"]
        readiness = guidance["next_call_draft_readiness"]
        preflight = guidance["next_call_preflight"]
        storage.close()

        self.assertEqual("waiting-on-child", guidance["dominant_target_kind"])
        self.assertEqual("waiting-on-child", guidance["dominant_blocker_kind"])
        self.assertFalse(guidance["execution_allowed"])
        self.assertEqual("job.start", guidance["best_next_move"]["call_type"])
        self.assertEqual("progress-child-leg-next", follow_up["follow_up_behavior_kind"])
        self.assertTrue(follow_up["productive_in_slice"])
        self.assertTrue(follow_up["waits_on_child_progress"])
        self.assertTrue(follow_up["child_held_progression"])
        self.assertEqual("job.start", follow_up["best_next_move"]["call_type"])
        self.assertEqual("executable-now", next_call_hint["hint_kind"])
        self.assertEqual("job.start", next_call_hint["recommended_call_type"])
        self.assertEqual("T000001.J002", next_call_hint["job_id"])
        self.assertEqual("I002", next_call_hint["target_item_id"])
        self.assertTrue(next_call_hint["execution_ready"])
        self.assertFalse(next_call_hint["unavailable_in_slice"])
        self.assertEqual("executable-now", next_call_draft["draft_kind"])
        self.assertEqual("job.start", next_call_draft["call_type"])
        self.assertEqual("T000001.J002", next_call_draft["known_fields"]["job_id"])
        self.assertTrue(next_call_draft["executable_now"])
        self.assertFalse(next_call_draft["unavailable_in_slice"])
        self.assertEqual("executable-now", readiness["readiness_kind"])
        self.assertEqual((), readiness["missing_required_fields"])
        self.assertTrue(readiness["executable_now"])
        self.assertEqual("ready_to_submit", preflight["preflight_kind"])
        self.assertTrue(preflight["ready_to_submit"])
        self.assertEqual(
            {
                "schema_version": "v0.1",
                "call_type": "job.start",
                "task_id": "T000001",
                "job_id": "T000001.J002",
                "from_role": "jarvis",
                "to_role": "alfred",
                "reported_at": "2026-03-30T12:00:00Z",
            },
            preflight["prepared_call"],
        )

    def test_waiting_on_child_running_leg_does_not_fake_start_draft(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(make_job_start_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Run child leg",
                        "description": "Delegate the blocking child work.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                    },
                ],
            )
        )

        child = processor.process_call(make_child_job_request_call())
        child_job_id = child.result["job_id"]
        result = processor.process_call(make_job_start_call(job_id=child_job_id))
        guidance = result.result["post_call_guidance"]
        next_call_hint = guidance["next_call_hint"]
        next_call_draft = guidance["next_call_draft"]
        readiness = guidance["next_call_draft_readiness"]
        preflight = guidance["next_call_preflight"]
        storage.close()

        self.assertEqual("waiting-on-child", guidance["dominant_target_kind"])
        self.assertEqual("unavailable-in-slice", next_call_hint["hint_kind"])
        self.assertIsNone(next_call_hint["recommended_call_type"])
        self.assertTrue(next_call_hint["unavailable_in_slice"])
        self.assertEqual("unavailable-in-slice", next_call_draft["draft_kind"])
        self.assertIsNone(next_call_draft["call_type"])
        self.assertEqual({}, next_call_draft["known_fields"])
        self.assertFalse(next_call_draft["executable_now"])
        self.assertTrue(next_call_draft["unavailable_in_slice"])
        self.assertEqual("unavailable-in-slice", readiness["readiness_kind"])
        self.assertEqual((), readiness["accepted_supplied_fields"])
        self.assertEqual("unavailable_in_slice", preflight["preflight_kind"])
        self.assertIsNone(preflight["prepared_call"])
        self.assertTrue(preflight["unavailable_in_slice"])

    def test_accepted_job_start_returns_refreshed_current_job_focus_guidance(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Produce required proof",
                        "description": "Return the artifact the next step depends on.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "artifact_exists"},
                    },
                    {
                        "item_id": "I003",
                        "title": "Resume dependent follow-up",
                        "description": "Continue once the predecessor is verified.",
                        "status": "todo",
                        "depends_on": ["I002"],
                    },
                ],
            )
        )
        processor.process_call(make_result_submit_call(reported_status="succeeded"))
        processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref()],
            )
        )

        result = processor.process_call(make_job_start_call())
        guidance = result.result["post_call_guidance"]
        follow_up = guidance["immediate_follow_up"]
        next_call_hint = guidance["next_call_hint"]
        next_call_draft = guidance["next_call_draft"]
        readiness = guidance["next_call_draft_readiness"]
        preflight = guidance["next_call_preflight"]
        storage.close()

        self.assertEqual("resolved", guidance["posture_transition"]["transition_kind"])
        self.assertEqual("active-item", guidance["dominant_target_kind"])
        self.assertTrue(guidance["execution_allowed"])
        self.assertTrue(guidance["current_job_is_primary_focus"])
        self.assertFalse(guidance["relevant_plan_item_is_primary_focus"])
        self.assertEqual(
            "continue-active-execution",
            guidance["best_next_move"]["move_kind"],
        )
        self.assertEqual("resume-active-leg-next", follow_up["follow_up_behavior_kind"])
        self.assertTrue(follow_up["productive_in_slice"])
        self.assertTrue(follow_up["actionable_execution"])
        self.assertFalse(follow_up["no_productive_follow_up_in_slice"])
        self.assertEqual("unavailable-in-slice", next_call_hint["hint_kind"])
        self.assertIsNone(next_call_hint["recommended_call_type"])
        self.assertEqual("T000001.J001", next_call_hint["job_id"])
        self.assertEqual("I003", next_call_hint["target_item_id"])
        self.assertFalse(next_call_hint["execution_ready"])
        self.assertTrue(next_call_hint["unavailable_in_slice"])
        self.assertEqual("unavailable-in-slice", next_call_draft["draft_kind"])
        self.assertIsNone(next_call_draft["call_type"])
        self.assertEqual({}, next_call_draft["known_fields"])
        self.assertEqual((), next_call_draft["missing_required_fields"])
        self.assertTrue(next_call_draft["unavailable_in_slice"])
        self.assertEqual("unavailable-in-slice", readiness["readiness_kind"])
        self.assertTrue(readiness["unavailable_in_slice"])
        self.assertEqual("unavailable_in_slice", preflight["preflight_kind"])
        self.assertIsNone(preflight["prepared_call"])

    def test_draft_preflight_reports_disallowed_and_ignored_fields_without_pretending_ready(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Need artifact proof",
                        "description": "Still needs an official artifact ref.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "artifact_exists"},
                    },
                ],
            )
        )
        processor.process_call(make_result_submit_call(reported_status="succeeded"))
        processor.process_call(make_checkpoint_create_call(plan_version=1))

        preflight = processor.prepare_next_call_from_draft(
            "T000001",
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/continuation.md",
                    "role": "jarvis",
                },
                "schema_version": "v9.9",
                "content_ref": {"kind": "bad", "path": "/tmp/bad", "role": "jarvis"},
                "bogus": "ignored",
            },
        )
        storage.close()

        self.assertEqual("ready_to_submit", preflight["preflight_kind"])
        self.assertEqual(("payload_ref",), preflight["accepted_supplied_fields"])
        self.assertEqual(("bogus",), preflight["ignored_supplied_fields"])
        self.assertEqual(
            ("schema_version", "content_ref"),
            preflight["disallowed_supplied_fields"],
        )

    def test_submit_prepared_job_start_succeeds_when_fresh_state_still_allows_it(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Produce required proof",
                        "description": "Return the artifact the next step depends on.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "artifact_exists"},
                    },
                    {
                        "item_id": "I003",
                        "title": "Resume dependent follow-up",
                        "description": "Continue once the predecessor is verified.",
                        "status": "todo",
                        "depends_on": ["I002"],
                    },
                ],
            )
        )
        processor.process_call(make_result_submit_call(reported_status="succeeded"))
        continuation = processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref()],
            )
        )
        prepared_call = continuation.result["post_call_guidance"]["next_call_preflight"][
            "prepared_call"
        ]

        decision = processor.submit_prepared_next_call(prepared_call=prepared_call)
        receipt = decision["submit_receipt"]
        storage.close()

        self.assertEqual("submitted", decision["decision_kind"])
        self.assertTrue(decision["allowed_to_submit"])
        self.assertEqual("productive_in_slice", decision["submission_mode"])
        self.assertTrue(decision["productive_in_slice"])
        self.assertFalse(decision["stale_or_blocked"])
        self.assertIsNotNone(decision["submit_result"])
        self.assertEqual("job.start", decision["submit_result"].call_type)
        self.assertEqual("active-item", decision["submit_result"].result["post_call_guidance"]["dominant_target_kind"])
        self.assertEqual("submitted", receipt["decision_kind"])
        self.assertEqual("productive_in_slice", receipt["submission_mode"])
        self.assertEqual("productive_execution_advanced", receipt["submit_effect_kind"])
        self.assertEqual("active-item", receipt["dominant_target_kind_now"])
        self.assertEqual("continue-active-execution", receipt["best_next_move_now"]["move_kind"])
        self.assertTrue(receipt["execution_allowed_now"])
        self.assertTrue(receipt["current_job_is_primary_focus_now"])

    def test_submit_prepared_job_start_rejects_stale_call_after_posture_changes(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Produce required proof",
                        "description": "Return the artifact the next step depends on.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "artifact_exists"},
                    },
                    {
                        "item_id": "I003",
                        "title": "Resume dependent follow-up",
                        "description": "Continue once the predecessor is verified.",
                        "status": "todo",
                        "depends_on": ["I002"],
                    },
                ],
            )
        )
        processor.process_call(make_result_submit_call(reported_status="succeeded"))
        continuation = processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref()],
            )
        )
        prepared_call = continuation.result["post_call_guidance"]["next_call_preflight"][
            "prepared_call"
        ]
        processor.process_call(make_job_start_call())

        decision = processor.submit_prepared_next_call(prepared_call=prepared_call)
        receipt = decision["submit_receipt"]
        storage.close()

        self.assertEqual("stale_prepared_call", decision["decision_kind"])
        self.assertFalse(decision["allowed_to_submit"])
        self.assertIsNone(decision["submission_mode"])
        self.assertTrue(decision["stale_or_blocked"])
        self.assertIsNone(decision["submit_result"])
        self.assertEqual("unavailable_in_slice", decision["fresh_preflight"]["preflight_kind"])
        self.assertTrue(decision["unavailable_in_slice"])
        self.assertEqual("submission_refused_stale", receipt["submit_effect_kind"])
        self.assertEqual("active-item", receipt["dominant_target_kind_now"])
        self.assertEqual("continue-active-execution", receipt["best_next_move_now"]["move_kind"])
        self.assertTrue(receipt["execution_allowed_now"])

    def test_submit_prepared_proof_continuation_requires_real_content_before_submission(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Need artifact proof",
                        "description": "Still needs an official artifact ref.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "artifact_exists"},
                    },
                ],
            )
        )
        processor.process_call(make_result_submit_call(reported_status="succeeded"))
        processor.process_call(make_checkpoint_create_call(plan_version=1))

        denied = processor.submit_prepared_next_call(task_id="T000001")
        submitted = processor.submit_prepared_next_call(
            task_id="T000001",
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/continuation.md",
                    "role": "jarvis",
                }
            },
        )
        storage.close()

        self.assertEqual("not_ready_missing_fields", denied["decision_kind"])
        self.assertFalse(denied["allowed_to_submit"])
        self.assertEqual("productive_in_slice", denied["submission_mode"])
        self.assertTrue(denied["productive_in_slice"])
        self.assertEqual(("payload_ref",), denied["missing_required_fields"])
        self.assertIsNone(denied["submit_result"])
        self.assertEqual(
            "submission_refused_missing_fields",
            denied["submit_receipt"]["submit_effect_kind"],
        )
        self.assertEqual("proof-gathering", denied["submit_receipt"]["dominant_target_kind_now"])
        self.assertEqual("submitted", submitted["decision_kind"])
        self.assertTrue(submitted["allowed_to_submit"])
        self.assertEqual("productive_in_slice", submitted["submission_mode"])
        self.assertTrue(submitted["productive_in_slice"])
        self.assertEqual("continuation.record", submitted["submit_result"].call_type)
        self.assertEqual(
            "proof-gathering",
            submitted["submit_result"].result["post_call_guidance"]["dominant_target_kind"],
        )

    def test_submit_prepared_review_context_call_stays_context_only(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Produce proof needing review",
                        "description": "Return evidence that still needs review.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "manual_review_required"},
                    },
                ],
            )
        )
        processor.process_call(
            make_result_submit_call(
                artifact_refs=[make_summary_artifact_ref()],
                reported_status="succeeded",
            )
        )
        processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref(artifact_id="T000001.J001.A002")],
            )
        )

        decision = processor.submit_prepared_next_call(
            task_id="T000001",
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/review.md",
                    "role": "jarvis",
                }
            },
        )
        receipt = decision["submit_receipt"]
        storage.close()

        self.assertEqual("submitted", decision["decision_kind"])
        self.assertTrue(decision["allowed_to_submit"])
        self.assertEqual("context_capture", decision["submission_mode"])
        self.assertFalse(decision["productive_in_slice"])
        self.assertTrue(decision["context_only"])
        self.assertIsNotNone(decision["submit_result"])
        self.assertEqual("continuation.record", decision["submit_result"].call_type)
        self.assertEqual(
            "review-needed",
            decision["submit_result"].result["post_call_guidance"]["dominant_target_kind"],
        )
        self.assertEqual(
            "capture-review-context-next",
            decision["submit_result"].result["post_call_guidance"]["immediate_follow_up"][
                "follow_up_behavior_kind"
            ],
        )
        self.assertEqual("submitted", receipt["decision_kind"])
        self.assertEqual("context_capture", receipt["submission_mode"])
        self.assertEqual(
            "posture_preserved_after_context_capture",
            receipt["submit_effect_kind"],
        )
        self.assertFalse(receipt["productive_in_slice"])
        self.assertTrue(receipt["context_capture_only"])
        self.assertEqual("review-needed", receipt["dominant_target_kind_now"])
        self.assertEqual(
            "capture-manual-review-context",
            receipt["best_next_move_now"]["move_kind"],
        )
        self.assertFalse(receipt["execution_allowed_now"])

    def test_submit_prepared_blocked_evidence_call_stays_context_only(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Collect blocked evidence",
                        "description": "Capture failure evidence for the blocked step.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                    },
                ],
            )
        )
        processor.process_call(
            make_failure_report_call(
                reported_status="blocked",
                artifact_refs=[make_summary_artifact_ref()],
            )
        )
        processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref(artifact_id="T000001.J001.A002")],
            )
        )

        decision = processor.submit_prepared_next_call(
            task_id="T000001",
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/blocked.md",
                    "role": "jarvis",
                }
            },
        )
        receipt = decision["submit_receipt"]
        storage.close()

        self.assertEqual("submitted", decision["decision_kind"])
        self.assertTrue(decision["allowed_to_submit"])
        self.assertEqual("context_capture", decision["submission_mode"])
        self.assertFalse(decision["productive_in_slice"])
        self.assertTrue(decision["context_only"])
        self.assertIsNotNone(decision["submit_result"])
        self.assertEqual("continuation.record", decision["submit_result"].call_type)
        self.assertEqual(
            "blocked-evidence-review",
            decision["submit_result"].result["post_call_guidance"]["dominant_target_kind"],
        )
        self.assertEqual(
            "capture-blocked-evidence-next",
            decision["submit_result"].result["post_call_guidance"]["immediate_follow_up"][
                "follow_up_behavior_kind"
            ],
        )
        self.assertEqual(
            "posture_preserved_after_context_capture",
            receipt["submit_effect_kind"],
        )
        self.assertFalse(receipt["productive_in_slice"])
        self.assertTrue(receipt["context_capture_only"])
        self.assertEqual("blocked-evidence-review", receipt["dominant_target_kind_now"])
        self.assertEqual(
            "capture-blocked-evidence",
            receipt["best_next_move_now"]["move_kind"],
        )

    def test_submit_prepared_review_context_capture_rejects_when_posture_becomes_stale(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Produce proof needing review",
                        "description": "Return evidence that still needs review.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "manual_review_required"},
                    },
                    {
                        "item_id": "I003",
                        "title": "Resume dependent follow-up",
                        "description": "Continue once the predecessor is settled.",
                        "status": "todo",
                        "depends_on": ["I002"],
                    },
                ],
            )
        )
        processor.process_call(
            make_result_submit_call(
                artifact_refs=[make_summary_artifact_ref()],
                reported_status="succeeded",
            )
        )
        processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref(artifact_id="T000001.J001.A002")],
            )
        )
        prepared_call = processor.prepare_next_call_from_draft(
            "T000001",
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/review.md",
                    "role": "jarvis",
                }
            },
        )["prepared_call"]
        processor.process_call(
            make_plan_record_call(
                plan_version=2,
                current_active_item="I003",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Produce proof needing review",
                        "description": "Return evidence that still needs review.",
                        "status": "verified",
                        "depends_on": ["I001"],
                    },
                    {
                        "item_id": "I003",
                        "title": "Resume dependent follow-up",
                        "description": "Continue once the predecessor is settled.",
                        "status": "todo",
                        "depends_on": ["I002"],
                    },
                ],
            )
        )

        decision = processor.submit_prepared_next_call(prepared_call=prepared_call)
        receipt = decision["submit_receipt"]
        storage.close()

        self.assertEqual("stale_prepared_call", decision["decision_kind"])
        self.assertFalse(decision["allowed_to_submit"])
        self.assertTrue(decision["stale_or_blocked"])
        self.assertTrue(decision["productive_in_slice"])
        self.assertFalse(decision["context_only"])
        self.assertIsNone(decision["submit_result"])
        self.assertEqual("submission_refused_stale", receipt["submit_effect_kind"])
        self.assertEqual("next-executable", receipt["dominant_target_kind_now"])
        self.assertEqual("job.start", receipt["best_next_move_now"]["call_type"])

    def test_submit_prepared_child_job_start_rejects_when_child_leg_is_stale(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(make_job_start_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Run child leg",
                        "description": "Delegate the blocking child work.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                    },
                ],
            )
        )
        child = processor.process_call(make_child_job_request_call())
        prepared_call = child.result["post_call_guidance"]["next_call_preflight"]["prepared_call"]
        child_job_id = child.result["job_id"]
        processor.process_call(make_job_start_call(job_id=child_job_id))

        decision = processor.submit_prepared_next_call(prepared_call=prepared_call)
        receipt = decision["submit_receipt"]
        storage.close()

        self.assertEqual("stale_prepared_call", decision["decision_kind"])
        self.assertFalse(decision["allowed_to_submit"])
        self.assertIsNone(decision["submission_mode"])
        self.assertTrue(decision["stale_or_blocked"])
        self.assertIsNone(decision["submit_result"])
        self.assertEqual("unavailable_in_slice", decision["fresh_preflight"]["preflight_kind"])
        self.assertEqual("submission_refused_stale", receipt["submit_effect_kind"])
        self.assertEqual("waiting-on-child", receipt["dominant_target_kind_now"])

    def test_submit_prepared_call_does_not_fabricate_active_leg_path(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Produce required proof",
                        "description": "Return the artifact the next step depends on.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "artifact_exists"},
                    },
                    {
                        "item_id": "I003",
                        "title": "Resume dependent follow-up",
                        "description": "Continue once the predecessor is verified.",
                        "status": "todo",
                        "depends_on": ["I002"],
                    },
                ],
            )
        )
        processor.process_call(make_result_submit_call(reported_status="succeeded"))
        processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref()],
            )
        )
        processor.process_call(make_job_start_call())

        decision = processor.submit_prepared_next_call(task_id="T000001")
        receipt = decision["submit_receipt"]
        storage.close()

        self.assertEqual("unavailable_in_slice", decision["decision_kind"])
        self.assertFalse(decision["allowed_to_submit"])
        self.assertIsNone(decision["submission_mode"])
        self.assertTrue(decision["unavailable_in_slice"])
        self.assertIsNone(decision["submit_result"])
        self.assertEqual("submission_refused_unavailable", receipt["submit_effect_kind"])
        self.assertEqual("active-item", receipt["dominant_target_kind_now"])
        self.assertEqual("continue-active-execution", receipt["best_next_move_now"]["move_kind"])

    def test_attempt_best_next_call_submits_ready_job_start(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Produce required proof",
                        "description": "Return the artifact the next step depends on.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "artifact_exists"},
                    },
                    {
                        "item_id": "I003",
                        "title": "Resume dependent follow-up",
                        "description": "Continue once the predecessor is verified.",
                        "status": "todo",
                        "depends_on": ["I002"],
                    },
                ],
            )
        )
        processor.process_call(make_result_submit_call(reported_status="succeeded"))
        processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref()],
            )
        )

        attempt = processor.attempt_best_next_call("T000001")
        receipt = attempt["submit_receipt"]
        storage.close()

        self.assertEqual("attempted_productive_execution", attempt["attempt_kind"])
        self.assertEqual("job.start", attempt["attempted_call_type"])
        self.assertEqual("productive_in_slice", attempt["attempted_submission_mode"])
        self.assertEqual("job.start", attempt["best_next_move"]["call_type"])
        self.assertTrue(attempt["attempt_allowed"])
        self.assertFalse(attempt["requires_additional_user_or_agent_input"])
        self.assertTrue(attempt["formed_concrete_call"])
        self.assertFalse(attempt["context_capture_only"])
        self.assertFalse(attempt["unavailable_in_slice"])
        self.assertIsNotNone(receipt)
        self.assertEqual("productive_execution_advanced", receipt["submit_effect_kind"])
        self.assertEqual("active-item", receipt["dominant_target_kind_now"])

    def test_attempt_best_next_call_refuses_proof_gathering_until_content_exists(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Need artifact proof",
                        "description": "Still needs an official artifact ref.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "artifact_exists"},
                    },
                ],
            )
        )
        processor.process_call(make_result_submit_call(reported_status="succeeded"))
        processor.process_call(make_checkpoint_create_call(plan_version=1))

        attempt = processor.attempt_best_next_call("T000001")
        receipt = attempt["submit_receipt"]
        storage.close()

        self.assertEqual("attempt_refused_missing_fields", attempt["attempt_kind"])
        self.assertEqual("continuation.record", attempt["attempted_call_type"])
        self.assertEqual("attach-artifact-ref", attempt["best_next_move"]["move_kind"])
        self.assertFalse(attempt["attempt_allowed"])
        self.assertEqual(("payload_ref",), attempt["missing_required_fields"])
        self.assertTrue(attempt["requires_additional_user_or_agent_input"])
        self.assertFalse(attempt["formed_concrete_call"])
        self.assertFalse(attempt["context_capture_only"])
        self.assertFalse(attempt["unavailable_in_slice"])
        self.assertIsNotNone(receipt)
        self.assertEqual("submission_refused_missing_fields", receipt["submit_effect_kind"])
        self.assertEqual("proof-gathering", receipt["dominant_target_kind_now"])

    def test_attempt_best_next_call_submits_review_context_capture_when_content_present(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Produce proof needing review",
                        "description": "Return evidence that still needs review.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "manual_review_required"},
                    },
                ],
            )
        )
        processor.process_call(
            make_result_submit_call(
                artifact_refs=[make_summary_artifact_ref()],
                reported_status="succeeded",
            )
        )
        processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref(artifact_id="T000001.J001.A002")],
            )
        )

        attempt = processor.attempt_best_next_call(
            "T000001",
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/review.md",
                    "role": "jarvis",
                }
            },
        )
        receipt = attempt["submit_receipt"]
        storage.close()

        self.assertEqual("attempted_context_capture", attempt["attempt_kind"])
        self.assertEqual("continuation.record", attempt["attempted_call_type"])
        self.assertEqual("context_capture", attempt["attempted_submission_mode"])
        self.assertEqual("capture-review-context-next", attempt["follow_up_behavior_kind"])
        self.assertTrue(attempt["attempt_allowed"])
        self.assertTrue(attempt["formed_concrete_call"])
        self.assertTrue(attempt["context_capture_only"])
        self.assertFalse(attempt["productive_in_slice"])
        self.assertFalse(attempt["unavailable_in_slice"])
        self.assertIsNotNone(receipt)
        self.assertEqual("context_capture", receipt["submission_mode"])
        self.assertEqual(
            "posture_preserved_after_context_capture",
            receipt["submit_effect_kind"],
        )
        self.assertEqual("review-needed", receipt["dominant_target_kind_now"])

    def test_attempt_best_next_call_submits_blocked_evidence_context_capture_when_content_present(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Collect blocked evidence",
                        "description": "Capture failure evidence for the blocked step.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                    },
                ],
            )
        )
        processor.process_call(
            make_failure_report_call(
                reported_status="blocked",
                artifact_refs=[make_summary_artifact_ref()],
            )
        )
        processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref(artifact_id="T000001.J001.A002")],
            )
        )

        attempt = processor.attempt_best_next_call(
            "T000001",
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/blocked.md",
                    "role": "jarvis",
                }
            },
        )
        receipt = attempt["submit_receipt"]
        storage.close()

        self.assertEqual("attempted_context_capture", attempt["attempt_kind"])
        self.assertEqual("continuation.record", attempt["attempted_call_type"])
        self.assertEqual("context_capture", attempt["attempted_submission_mode"])
        self.assertEqual("capture-blocked-evidence-next", attempt["follow_up_behavior_kind"])
        self.assertTrue(attempt["attempt_allowed"])
        self.assertTrue(attempt["formed_concrete_call"])
        self.assertTrue(attempt["context_capture_only"])
        self.assertFalse(attempt["productive_in_slice"])
        self.assertFalse(attempt["unavailable_in_slice"])
        self.assertIsNotNone(receipt)
        self.assertEqual(
            "posture_preserved_after_context_capture",
            receipt["submit_effect_kind"],
        )
        self.assertEqual("blocked-evidence-review", receipt["dominant_target_kind_now"])

    def test_attempt_best_next_call_submits_child_job_start_only_when_startable(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(make_job_start_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Run child leg",
                        "description": "Delegate the blocking child work.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                    },
                ],
            )
        )
        processor.process_call(make_child_job_request_call())

        attempt = processor.attempt_best_next_call("T000001")
        receipt = attempt["submit_receipt"]
        storage.close()

        self.assertEqual("attempted_productive_execution", attempt["attempt_kind"])
        self.assertEqual("job.start", attempt["attempted_call_type"])
        self.assertTrue(attempt["attempt_allowed"])
        self.assertTrue(attempt["formed_concrete_call"])
        self.assertIsNotNone(receipt)
        self.assertEqual("submitted", receipt["decision_kind"])
        self.assertEqual("job.start", receipt["submit_result"].call_type)

    def test_attempt_best_next_call_does_not_fabricate_active_leg_path(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Produce required proof",
                        "description": "Return the artifact the next step depends on.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "artifact_exists"},
                    },
                    {
                        "item_id": "I003",
                        "title": "Resume dependent follow-up",
                        "description": "Continue once the predecessor is verified.",
                        "status": "todo",
                        "depends_on": ["I002"],
                    },
                ],
            )
        )
        processor.process_call(make_result_submit_call(reported_status="succeeded"))
        processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref()],
            )
        )
        processor.process_call(make_job_start_call())

        attempt = processor.attempt_best_next_call("T000001")
        receipt = attempt["submit_receipt"]
        storage.close()

        self.assertEqual("attempt_refused_unavailable", attempt["attempt_kind"])
        self.assertIsNone(attempt["attempted_call_type"])
        self.assertFalse(attempt["attempt_allowed"])
        self.assertFalse(attempt["formed_concrete_call"])
        self.assertTrue(attempt["unavailable_in_slice"])
        self.assertIsNotNone(receipt)
        self.assertEqual("submission_refused_unavailable", receipt["submit_effect_kind"])
        self.assertEqual("active-item", receipt["dominant_target_kind_now"])

    def test_failure_report_attaches_evidence_and_keeps_item_blocked(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Collect failure evidence",
                        "description": "Return failure artifacts for the blocked step.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                    },
                ],
            )
        )

        processor.process_call(
            make_failure_report_call(
                reported_status="blocked",
                artifact_refs=[make_summary_artifact_ref(kind="screenshot")],
            )
        )

        item_summary = storage.read_plan_item_summary("T000001", 1, "I002")
        artifact_index = storage.read_artifact_index_record("T000001.J001.A001")
        task_summary = storage.latest_task_state_summary("T000001")
        resume_target = storage.resolve_next_plan_resume_target("T000001")
        storage.close()

        self.assertEqual("blocked", item_summary["status"])
        self.assertTrue(item_summary["is_blocked"])
        self.assertEqual(2, item_summary["evidence_count"])
        self.assertEqual("screenshot", artifact_index["kind"])
        self.assertEqual("blocked", task_summary["relevant_plan_item"]["status"])
        self.assertEqual("blocked-evidence-review", resume_target["target_kind"])
        self.assertEqual("I002", resume_target["item"]["item_id"])

    def test_resume_summaries_surface_relevant_evidence_refs(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(make_plan_record_call(plan_version=1, current_active_item="I002"))
        processor.process_call(
            make_checkpoint_create_call(
                plan_version=1,
                current_active_item="I002",
                artifact_refs=[make_summary_artifact_ref()],
            )
        )
        processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref(artifact_id="T000001.J001.A002")],
            )
        )

        checkpoint_summary = storage.latest_task_state_summary("T000001")["latest_checkpoint_summary"]
        continuation_summary = storage.latest_task_state_summary("T000001")["latest_continuation_summary"]
        resume_evidence = storage.resolve_resume_evidence_refs("T000001")
        artifact_records = storage.list_artifact_index_records(task_id="T000001")
        storage.close()

        self.assertEqual("T000001.J001.A001", checkpoint_summary["evidence_refs"][0]["artifact_id"])
        self.assertEqual("T000001.J001.A002", continuation_summary["evidence_refs"][0]["artifact_id"])
        self.assertEqual("T000001.J001.A002", resume_evidence[0]["artifact_id"])
        self.assertEqual(2, len(artifact_records))

    def test_verified_item_without_satisfied_gate_is_rejected_before_write(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())

        with self.assertRaises(GarageAlfredProcessingError) as ctx:
            processor.process_call(
                make_plan_record_call(
                    plan_version=1,
                    current_active_item=None,
                    items=[
                        {
                            "item_id": "I001",
                            "title": "Claim verified too early",
                            "description": "Mark verified without satisfying the declared gate.",
                            "status": "verified",
                            "verification_rule": {"type": "artifact_exists"},
                        }
                    ],
                )
            )

        self.assertIn("cannot be verified without a satisfied proof gate", str(ctx.exception))
        self.assertIsNone(storage.read_tracked_plan("T000001", 1))
        storage.close()


if __name__ == "__main__":
    unittest.main()
