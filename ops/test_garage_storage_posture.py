"""Factual raw-record storage tests for the storage-backed Garage processor."""

from __future__ import annotations

from ops.garage_alfred import GarageAlfredProcessingError
from ops.garage_storage import build_storage_backed_alfred_processor
from ops.test_garage_fixtures import (
    GarageTempRootTestCase,
    make_checkpoint_create_call,
    make_child_job_request_call,
    make_continuation_record_call,
    make_job_start_call,
    make_plan_record_call,
    make_result_submit_call,
    make_summary_artifact_ref,
    make_task_create_call,
)


class GarageStoragePostureTests(GarageTempRootTestCase):
    def test_tracked_plan_versions_are_persisted_as_recorded(self) -> None:
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
                        "title": "Run child work",
                        "description": "Delegate the next step.",
                        "status": "todo",
                        "depends_on": ["I001"],
                    },
                ],
            )
        )
        processor.process_call(
            make_plan_record_call(
                plan_version=2,
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
                        "title": "Run child work",
                        "description": "Delegate the next step.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                    },
                ],
            )
        )

        first_plan = storage.read_tracked_plan("T000001", 1)
        second_plan = storage.read_tracked_plan("T000001", 2)
        storage.close()

        assert first_plan is not None
        assert second_plan is not None
        self.assertEqual(1, first_plan["plan_version"])
        self.assertEqual("I002", first_plan["current_active_item"])
        self.assertEqual("todo", first_plan["items"][1]["status"])
        self.assertEqual(2, second_plan["plan_version"])
        self.assertEqual("I002", second_plan["current_active_item"])
        self.assertEqual("needs_child_job", second_plan["items"][1]["status"])

    def test_checkpoint_and_continuation_records_are_persisted_raw(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(make_job_start_call())
        processor.process_call(make_result_submit_call(reported_status="succeeded"))
        checkpoint = processor.process_call(
            make_checkpoint_create_call(
                plan_version=3,
                current_active_item="I002",
            )
        )
        processor.process_call(
            make_continuation_record_call(
                plan_version=3,
                artifact_refs=[make_summary_artifact_ref()],
            )
        )

        checkpoint_record = storage.read_checkpoint_record(checkpoint.result["checkpoint_id"])
        continuation_records = storage.list_continuation_records("T000001")
        latest_continuation = storage.latest_continuation_for_task("T000001")
        storage.close()

        assert checkpoint_record is not None
        assert latest_continuation is not None
        self.assertEqual(checkpoint.result["checkpoint_id"], checkpoint_record["checkpoint_id"])
        self.assertEqual(3, checkpoint_record["plan_version"])
        self.assertEqual("I002", checkpoint_record["current_active_item"])
        self.assertEqual(1, len(continuation_records))
        self.assertEqual(3, latest_continuation["plan_version"])
        self.assertEqual(latest_continuation, continuation_records[0])
        self.assertEqual(
            "T000001.J001.A001",
            latest_continuation["artifact_refs"][0]["artifact_id"],
        )

    def test_child_job_request_persists_raw_job_lineage(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        processor.process_call(make_job_start_call())
        child = processor.process_call(make_child_job_request_call())

        child_job = storage.read_job_record(child.result["job_id"])
        child_jobs = storage.list_child_jobs("T000001.J001")
        child_events = storage.read_event_history(job_id=child.result["job_id"])
        storage.close()

        assert child_job is not None
        self.assertEqual(child.result["job_id"], child_job["job_id"])
        self.assertEqual("T000001.J001", child_job["parent_job_id"])
        self.assertEqual(1, len(child_jobs))
        self.assertEqual(child.result["job_id"], child_jobs[0]["job_id"])
        self.assertEqual(
            ["job.created", "job.dispatched"],
            [event["event_type"] for event in child_events],
        )

    def test_result_submit_persists_artifact_index_and_plan_record_state(self) -> None:
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
        processor.process_call(make_job_start_call())
        processor.process_call(
            make_result_submit_call(
                artifact_refs=[make_summary_artifact_ref()],
                reported_status="succeeded",
            )
        )

        artifact_index = storage.read_artifact_index_record("T000001.J001.A001")
        tracked_plan = storage.read_tracked_plan("T000001", 1)
        event_history = storage.read_event_history(task_id="T000001")
        storage.close()

        assert artifact_index is not None
        assert tracked_plan is not None
        self.assertEqual("T000001", artifact_index["task_id"])
        self.assertEqual("T000001.J001", artifact_index["job_id"])
        self.assertEqual("T000001.J001.A001", artifact_index["artifact_id"])
        self.assertEqual("verified", tracked_plan["items"][1]["status"])
        self.assertEqual(
            ["task.created", "plan.recorded", "job.started", "job.returned"],
            [event["event_type"] for event in event_history],
        )

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
        self.assertEqual(
            ["task.created"],
            [event["event_type"] for event in storage.read_event_history("T000001")],
        )
        storage.close()
