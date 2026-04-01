"""Small runtime-shaped tests for the Garage processor."""

from __future__ import annotations

import unittest
from typing import Any

from ops.garage_boundaries import GarageBoundaryError
from ops.garage_runtime import (
    GarageProcessorError,
    GarageRecordWrite,
    GarageRuntimeProcessor,
)


def make_valid_child_job_request() -> dict[str, Any]:
    return {
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


class GarageRuntimeProcessorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.recorded_events: list[dict[str, Any]] = []
        self.written_records: list[tuple[str, dict[str, Any]]] = []
        self.processor = GarageRuntimeProcessor(
            event_recorder=self._record_event,
            record_writer=self._write_record,
        )

    def _record_event(self, event: dict[str, Any]) -> dict[str, Any]:
        self.recorded_events.append(event)
        return event

    def _write_record(
        self,
        schema_name: str,
        data: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        self.written_records.append((schema_name, data))
        return (schema_name, data)

    def test_valid_inbound_call_reaches_registered_handler(self) -> None:
        seen_calls: list[dict[str, Any]] = []

        def handler(data: dict[str, Any]) -> dict[str, Any]:
            seen_calls.append(data)
            return {"result": {"accepted": True}}

        self.processor.register_handler("child_job.request", handler)
        result = self.processor.process_call(make_valid_child_job_request())

        self.assertEqual(1, len(seen_calls))
        self.assertEqual({"accepted": True}, result.result)

    def test_invalid_inbound_call_fails_before_handler_dispatch(self) -> None:
        called = False

        def handler(data: dict[str, Any]) -> dict[str, Any]:
            nonlocal called
            called = True
            return {"result": data}

        self.processor.register_handler("result.submit", handler)

        with self.assertRaises(GarageBoundaryError) as ctx:
            self.processor.process_call(
                {
                    "schema_version": "v0.1",
                    "call_type": "result.submit",
                    "task_id": "T000001",
                    "job_id": "T000001.J002",
                    "from_role": "robin",
                    "to_role": "alfred",
                    "reported_status": "succeeded",
                    "payload": {
                        "summary": "Missing reported_at should fail.",
                        "structured_result": {"title": "Example Domain"},
                    },
                }
            )

        self.assertFalse(called)
        self.assertIn("reported_at", str(ctx.exception))

    def test_valid_handler_event_is_recorded_after_validation(self) -> None:
        def handler(_: dict[str, Any]) -> dict[str, Any]:
            return {
                "result": {"ok": True},
                "events": [
                    {
                        "schema_version": "v0.1",
                        "event_type": "job.returned",
                        "event_id": "T000001.E0007",
                        "task_id": "T000001",
                        "job_id": "T000001.J001",
                        "related_call_type": "result.submit",
                        "reported_status": "succeeded",
                        "recorded_at": "2026-03-30T12:10:00Z",
                    }
                ],
            }

        self.processor.register_handler("child_job.request", handler)
        result = self.processor.process_call(make_valid_child_job_request())

        self.assertEqual(1, len(self.recorded_events))
        self.assertEqual("job.returned", result.recorded_events[0]["event_type"])

    def test_invalid_handler_event_is_rejected_before_recorder_side_effect(self) -> None:
        def handler(_: dict[str, Any]) -> dict[str, Any]:
            return {
                "events": [
                    {
                        "schema_version": "v0.1",
                        "event_type": "job.returned",
                        "event_id": "T000001.E0007",
                        "task_id": "T000001",
                        "job_id": "T000001.J001",
                        "reported_status": "succeeded",
                        "recorded_at": "2026-03-30T12:10:00Z",
                    }
                ]
            }

        self.processor.register_handler("child_job.request", handler)

        with self.assertRaises(GarageBoundaryError) as ctx:
            self.processor.process_call(make_valid_child_job_request())

        self.assertEqual([], self.recorded_events)
        self.assertIn("related_call_type", str(ctx.exception))

    def test_valid_handler_record_is_written_after_validation(self) -> None:
        def handler(_: dict[str, Any]) -> dict[str, Any]:
            return {
                "records": [
                    GarageRecordWrite(
                        schema_name="task-record",
                        data={
                            "task_id": "T000001",
                            "task_state": "running",
                            "created_at": "2026-03-30T11:59:00Z",
                            "current_job_id": "T000001.J001",
                        },
                    )
                ]
            }

        self.processor.register_handler("child_job.request", handler)
        result = self.processor.process_call(make_valid_child_job_request())

        self.assertEqual(1, len(self.written_records))
        self.assertEqual("task-record", result.written_records[0][0])

    def test_invalid_handler_record_is_rejected_before_writer_side_effect(self) -> None:
        def handler(_: dict[str, Any]) -> dict[str, Any]:
            return {
                "records": [
                    (
                        "event-record",
                        {
                            "schema_version": "v0.1",
                            "event_type": "task.created",
                            "event_id": "T000001.E0001",
                            "recorded_at": "2026-03-30T12:00:01Z",
                        },
                    )
                ]
            }

        self.processor.register_handler("child_job.request", handler)

        with self.assertRaises(GarageBoundaryError) as ctx:
            self.processor.process_call(make_valid_child_job_request())

        self.assertEqual([], self.written_records)
        self.assertIn("task_id", str(ctx.exception))

    def test_dispatch_by_call_type_uses_registered_handler(self) -> None:
        seen: list[str] = []

        def child_handler(_: dict[str, Any]) -> dict[str, Any]:
            seen.append("child")
            return {"result": "child"}

        def task_handler(_: dict[str, Any]) -> dict[str, Any]:
            seen.append("task")
            return {"result": "task"}

        self.processor.register_handler("child_job.request", child_handler)
        self.processor.register_handler("task.create", task_handler)

        result = self.processor.process_call(make_valid_child_job_request())

        self.assertEqual(["child"], seen)
        self.assertEqual("child", result.result)

    def test_known_call_type_without_registered_handler_fails_clearly(self) -> None:
        with self.assertRaises(GarageProcessorError) as ctx:
            self.processor.process_call(
                {
                    "schema_version": "v0.1",
                    "call_type": "task.create",
                    "from_role": "jarvis",
                    "to_role": "alfred",
                    "payload": {
                        "objective": "Start a brand-new task."
                    },
                }
            )

        self.assertIn(
            "No handler registered for call_type 'task.create'",
            str(ctx.exception),
        )


if __name__ == "__main__":
    unittest.main()
