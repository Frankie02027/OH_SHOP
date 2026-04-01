"""Storage durability and persistence tests for the Garage adapter."""

from __future__ import annotations

from typing import Any

from ops.garage_alfred import GarageAlfredProcessingError, GarageAlfredProcessor
from ops.garage_boundaries import GarageBoundaryError, write_garage_persisted_record
from ops.garage_storage import GarageStorageAdapter, build_storage_backed_alfred_processor
from ops.test_garage_fixtures import (
    GarageStorageRootTestCase,
    make_checkpoint_create_call,
    make_child_job_request_call,
    make_continuation_record_call,
    make_job_start_call,
    make_result_submit_call,
    make_task_create_call,
)


class GarageStoragePersistenceTests(GarageStorageRootTestCase):
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
                call: dict[str, Any],
                *,
                child_job_id: str,
                parent_job_id: str,
                event_id: str,
                recorded_at: str,
            ) -> dict[str, Any]:
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
