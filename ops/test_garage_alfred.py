"""Tests for the first Alfred-style Garage processor slice."""

from __future__ import annotations

import unittest

from ops.garage_boundaries import GarageBoundaryError
from ops.garage_alfred import (
    GarageAlfredProcessingError,
    GarageAlfredProcessor,
    GarageProcessorError,
)


def make_task_create_call() -> dict[str, object]:
    return {
        "schema_version": "v0.1",
        "call_type": "task.create",
        "from_role": "jarvis",
        "to_role": "alfred",
        "payload": {
            "objective": "Create a new tracked task."
        },
    }


def make_job_start_call() -> dict[str, object]:
    return {
        "schema_version": "v0.1",
        "call_type": "job.start",
        "task_id": "T000001",
        "job_id": "T000001.J001",
        "from_role": "jarvis",
        "to_role": "alfred",
        "reported_at": "2026-03-30T12:01:00Z",
    }


def make_result_submit_call() -> dict[str, object]:
    return {
        "schema_version": "v0.1",
        "call_type": "result.submit",
        "task_id": "T000001",
        "job_id": "T000001.J001",
        "from_role": "robin",
        "to_role": "alfred",
        "reported_at": "2026-03-30T12:02:00Z",
        "reported_status": "partial",
        "payload_ref": {
            "kind": "result-json",
            "path": "/workspace/robin/tasks/T000001/jobs/J001/result.json",
            "role": "robin",
        },
    }


def make_failure_report_call(status: str) -> dict[str, object]:
    return {
        "schema_version": "v0.1",
        "call_type": "failure.report",
        "task_id": "T000001",
        "job_id": "T000001.J001",
        "from_role": "robin",
        "to_role": "alfred",
        "reported_at": "2026-03-30T12:03:00Z",
        "reported_status": status,
        "payload_ref": {
            "kind": "failure-json",
            "path": "/workspace/robin/tasks/T000001/jobs/J001/failure.json",
            "role": "robin",
        },
    }


def make_checkpoint_create_call() -> dict[str, object]:
    return {
        "schema_version": "v0.1",
        "call_type": "checkpoint.create",
        "task_id": "T000001",
        "job_id": "T000001.J001",
        "from_role": "jarvis",
        "to_role": "alfred",
        "plan_version": 2,
        "payload": {
            "reason": "Pause before storage wiring.",
            "resume_point": {"step": "wire-storage"},
        },
    }


def make_continuation_record_call() -> dict[str, object]:
    return {
        "schema_version": "v0.1",
        "call_type": "continuation.record",
        "task_id": "T000001",
        "job_id": "T000001.J001",
        "from_role": "jarvis",
        "to_role": "alfred",
        "plan_version": 2,
        "payload_ref": {
            "kind": "continuation-note",
            "path": "/workspace/jarvis/tasks/T000001/continuation.md",
            "role": "jarvis",
        },
        "artifact_refs": [
            {
                "artifact_id": "T000001.J001.A001",
                "kind": "summary",
                "workspace_ref": {
                    "role": "jarvis",
                    "path": "/workspace/jarvis/tasks/T000001/continuation.md",
                },
                "reported_by": "jarvis",
            }
        ],
    }


class GarageAlfredProcessorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.recorded_events: list[dict[str, object]] = []
        self.written_records: list[tuple[str, dict[str, object]]] = []
        self.processor = GarageAlfredProcessor(
            event_recorder=self._record_event,
            record_writer=self._write_record,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )

    def _record_event(self, event: dict[str, object]) -> dict[str, object]:
        self.recorded_events.append(event)
        return event

    def _write_record(
        self,
        schema_name: str,
        data: dict[str, object],
    ) -> tuple[str, dict[str, object]]:
        self.written_records.append((schema_name, data))
        return (schema_name, data)

    def test_task_create_produces_task_created_and_task_record_intent(self) -> None:
        result = self.processor.process_call(make_task_create_call())

        self.assertEqual("task.created", result.recorded_events[0]["event_type"])
        self.assertEqual("T000001", result.result["task_id"])
        self.assertEqual(["task-record", "event-record"], [w[0] for w in result.written_records])

    def test_job_start_produces_job_started_and_job_record_path(self) -> None:
        result = self.processor.process_call(make_job_start_call())

        self.assertEqual("job.started", result.recorded_events[0]["event_type"])
        self.assertEqual(["job-record", "event-record"], [w[0] for w in result.written_records])
        self.assertEqual("running", result.written_records[0][1]["job_state"])

    def test_result_submit_produces_job_returned_with_same_job_linkage(self) -> None:
        call = make_result_submit_call()
        result = self.processor.process_call(call)

        self.assertEqual("job.returned", result.recorded_events[0]["event_type"])
        self.assertEqual(call["job_id"], result.recorded_events[0]["job_id"])
        self.assertEqual(call["job_id"], result.written_records[0][1]["job_id"])

    def test_failure_report_blocked_produces_job_blocked(self) -> None:
        result = self.processor.process_call(make_failure_report_call("blocked"))
        self.assertEqual("job.blocked", result.recorded_events[0]["event_type"])
        self.assertEqual("blocked", result.written_records[0][1]["job_state"])

    def test_failure_report_failed_produces_job_failed(self) -> None:
        result = self.processor.process_call(make_failure_report_call("failed"))
        self.assertEqual("job.failed", result.recorded_events[0]["event_type"])
        self.assertEqual("failed", result.written_records[0][1]["job_state"])

    def test_checkpoint_create_produces_checkpoint_created_and_checkpoint_record(self) -> None:
        result = self.processor.process_call(make_checkpoint_create_call())

        self.assertEqual("checkpoint.created", result.recorded_events[0]["event_type"])
        self.assertEqual(
            ["checkpoint-record", "event-record"],
            [w[0] for w in result.written_records],
        )
        self.assertEqual("T000001.C001", result.result["checkpoint_id"])

    def test_continuation_record_produces_continuation_recorded_and_record(self) -> None:
        result = self.processor.process_call(make_continuation_record_call())

        self.assertEqual(
            "continuation.recorded",
            result.recorded_events[0]["event_type"],
        )
        self.assertEqual(
            ["continuation-record", "event-record"],
            [w[0] for w in result.written_records],
        )
        self.assertEqual(
            "continuation-note",
            result.written_records[0][1]["content_ref"]["kind"],
        )

    def test_unsupported_call_type_fails_clearly(self) -> None:
        with self.assertRaises(GarageProcessorError) as ctx:
            self.processor.process_call(
                {
                    "schema_version": "v0.1",
                    "call_type": "child_job.request",
                    "task_id": "T000001",
                    "job_id": "T000001.J001",
                    "from_role": "jarvis",
                    "to_role": "alfred",
                    "payload": {
                        "objective": "Use Robin for browser work.",
                        "reason_for_handoff": "Needs browser lane.",
                        "constraints": ["stay in browser lane"],
                        "expected_output": ["page title"],
                        "success_criteria": ["title captured"],
                    },
                }
            )

        self.assertIn("No handler registered for call_type 'child_job.request'", str(ctx.exception))

    def test_invalid_mapped_event_is_blocked_before_side_effect(self) -> None:
        class BrokenTaskCreateProcessor(GarageAlfredProcessor):
            def _build_task_created_event(
                self,
                call: dict[str, object],
                task_id: str,
                event_id: str,
                recorded_at: str,
            ) -> dict[str, object]:
                event = super()._build_task_created_event(
                    call, task_id, event_id, recorded_at
                )
                event.pop("related_call_type")
                return event

        processor = BrokenTaskCreateProcessor(
            event_recorder=self._record_event,
            record_writer=self._write_record,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )

        with self.assertRaises(GarageBoundaryError) as ctx:
            processor.process_call(make_task_create_call())

        self.assertEqual([], self.recorded_events)
        self.assertEqual([], self.written_records)
        self.assertIn("related_call_type", str(ctx.exception))

    def test_continuation_record_without_content_ref_source_fails_clearly(self) -> None:
        bad_call = make_continuation_record_call()
        bad_call.pop("payload_ref")
        bad_call["payload"] = {
            "summary": "Continuation note exists, but not as payload_ref or content_ref."
        }

        with self.assertRaises(GarageAlfredProcessingError) as ctx:
            self.processor.process_call(bad_call)

        self.assertIn("payload_ref or payload.content_ref", str(ctx.exception))
        self.assertEqual([], self.recorded_events)
        self.assertEqual([], self.written_records)


if __name__ == "__main__":
    unittest.main()
