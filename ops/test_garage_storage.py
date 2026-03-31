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
