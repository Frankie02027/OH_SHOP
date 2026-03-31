"""Integration-oriented tests for Garage validation boundaries."""

from __future__ import annotations

import unittest

from ops.garage_boundaries import (
    GarageBoundaryError,
    get_garage_schema_registry,
    handle_inbound_garage_call,
    record_garage_event,
    validate_garage_event_record,
    validate_garage_persisted_record,
    write_garage_persisted_record,
)


class GarageBoundaryIntegrationTests(unittest.TestCase):
    def test_registry_singleton_is_available_to_boundary_layer(self) -> None:
        first = get_garage_schema_registry()
        second = get_garage_schema_registry()
        self.assertIs(first, second)

    def test_valid_inbound_call_reaches_handler(self) -> None:
        seen: list[dict[str, object]] = []

        def handler(data: dict[str, object]) -> str:
            seen.append(data)
            return "handled"

        result = handle_inbound_garage_call(
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
            },
            handler,
        )

        self.assertEqual("handled", result)
        self.assertEqual(1, len(seen))

    def test_invalid_inbound_call_is_rejected_before_handler(self) -> None:
        called = False

        def handler(_: dict[str, object]) -> str:
            nonlocal called
            called = True
            return "should-not-run"

        with self.assertRaises(GarageBoundaryError) as ctx:
            handle_inbound_garage_call(
                {
                    "schema_version": "v0.1",
                    "call_type": "result.submit",
                    "task_id": "T000001",
                    "job_id": "T000001.J002",
                    "from_role": "robin",
                    "to_role": "alfred",
                    "reported_status": "succeeded",
                    "payload": {
                        "summary": "Missing reported_at.",
                        "structured_result": {"title": "Example Domain"},
                    },
                },
                handler,
            )

        self.assertFalse(called)
        self.assertIn("result.submit", str(ctx.exception))
        self.assertIn("reported_at", str(ctx.exception))

    def test_valid_event_reaches_recorder(self) -> None:
        seen: list[dict[str, object]] = []

        def recorder(data: dict[str, object]) -> str:
            seen.append(data)
            return "recorded"

        result = record_garage_event(
            {
                "schema_version": "v0.1",
                "event_type": "job.returned",
                "event_id": "T000001.E0007",
                "task_id": "T000001",
                "job_id": "T000001.J002",
                "related_call_type": "result.submit",
                "reported_status": "succeeded",
                "recorded_at": "2026-03-30T12:10:00Z",
            },
            recorder,
        )

        self.assertEqual("recorded", result)
        self.assertEqual(1, len(seen))

    def test_invalid_event_is_rejected_before_record(self) -> None:
        called = False

        def recorder(_: dict[str, object]) -> str:
            nonlocal called
            called = True
            return "should-not-run"

        with self.assertRaises(GarageBoundaryError) as ctx:
            record_garage_event(
                {
                    "schema_version": "v0.1",
                    "event_type": "job.returned",
                    "event_id": "T000001.E0007",
                    "task_id": "T000001",
                    "job_id": "T000001.J002",
                    "reported_status": "succeeded",
                    "recorded_at": "2026-03-30T12:10:00Z",
                },
                recorder,
            )

        self.assertFalse(called)
        self.assertIn("job.returned", str(ctx.exception))
        self.assertIn("related_call_type", str(ctx.exception))

    def test_valid_persisted_record_reaches_writer(self) -> None:
        writes: list[tuple[str, dict[str, object]]] = []

        def writer(schema_name: str, data: dict[str, object]) -> str:
            writes.append((schema_name, data))
            return "written"

        result = write_garage_persisted_record(
            "task-record",
            {
                "task_id": "T000001",
                "task_state": "running",
                "created_at": "2026-03-30T11:59:00Z",
                "current_job_id": "T000001.J002",
            },
            writer,
        )

        self.assertEqual("written", result)
        self.assertEqual(1, len(writes))
        self.assertEqual("task-record", writes[0][0])

    def test_invalid_persisted_record_is_rejected_before_write(self) -> None:
        called = False

        def writer(schema_name: str, data: dict[str, object]) -> str:
            nonlocal called
            called = True
            return "should-not-run"

        with self.assertRaises(GarageBoundaryError) as ctx:
            write_garage_persisted_record(
                "event-record",
                {
                    "schema_version": "v0.1",
                    "event_type": "task.created",
                    "event_id": "T000001.E0001",
                    "recorded_at": "2026-03-30T12:00:01Z",
                },
                writer,
            )

        self.assertFalse(called)
        self.assertIn("event-record", str(ctx.exception))
        self.assertIn("task_id", str(ctx.exception))

    def test_direct_event_boundary_helper_still_works(self) -> None:
        validated = validate_garage_event_record(
            {
                "schema_version": "v0.1",
                "event_type": "task.created",
                "event_id": "T000001.E0001",
                "task_id": "T000001",
                "related_call_type": "task.create",
                "recorded_at": "2026-03-30T12:00:01Z",
                "from_role": "jarvis",
                "to_role": "alfred",
            }
        )
        self.assertEqual("task.created", validated["event_type"])

    def test_direct_persisted_record_helper_still_works(self) -> None:
        validated = validate_garage_persisted_record(
            "artifact-index-record",
            {
                "artifact_id": "T000001.J002.A001",
                "kind": "screenshot",
                "workspace_ref": {
                    "role": "robin",
                    "path": "/workspace/robin/tasks/T000001/jobs/J002/output/page.png",
                },
                "reported_by": "robin",
                "created_at": "2026-03-30T12:12:00Z",
            },
        )
        self.assertEqual("screenshot", validated["kind"])


if __name__ == "__main__":
    unittest.main()
