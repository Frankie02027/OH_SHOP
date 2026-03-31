"""Narrow validation tests for the Garage v0.1 schema registry."""

from __future__ import annotations

import unittest

from ops.garage_schemas import (
    SchemaValidationError,
    load_schema_registry,
    validate_call,
    validate_call_envelope,
    validate_event,
    validate_object,
)


class GarageSchemaValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_schema_registry()

    def test_registry_loads_expected_dispatch_entries(self) -> None:
        self.assertIn("task.create", self.registry.available_call_types())
        self.assertIn("job.returned", self.registry.available_event_types())
        self.assertIn("task-record", self.registry.available_schema_names())

    def test_valid_task_create(self) -> None:
        validate_call(
            {
                "schema_version": "v0.1",
                "call_type": "task.create",
                "from_role": "jarvis",
                "to_role": "alfred",
                "payload": {
                    "objective": "Create a tracked plan for T000001."
                },
            }
        )

    def test_valid_child_job_request(self) -> None:
        validate_call(
            {
                "schema_version": "v0.1",
                "call_type": "child_job.request",
                "task_id": "T000001",
                "job_id": "T000001.J001",
                "from_role": "jarvis",
                "to_role": "alfred",
                "payload": {
                    "objective": "Open example.com and inspect the title.",
                    "reason_for_handoff": "Needs Robin browser lane.",
                    "constraints": ["Use browser tools only"],
                    "expected_output": ["page title"],
                    "success_criteria": ["title returned"],
                },
            }
        )

    def test_valid_result_submit(self) -> None:
        validate_call(
            {
                "schema_version": "v0.1",
                "call_type": "result.submit",
                "task_id": "T000001",
                "job_id": "T000001.J002",
                "from_role": "robin",
                "to_role": "alfred",
                "reported_at": "2026-03-30T12:00:00Z",
                "reported_status": "succeeded",
                "payload": {
                    "summary": "Found the exact page title.",
                    "structured_result": {"title": "Example Domain"},
                },
            }
        )

    def test_invalid_call_missing_required_field(self) -> None:
        with self.assertRaises(SchemaValidationError) as ctx:
            validate_call(
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
        self.assertIn("reported_at", str(ctx.exception))

    def test_valid_task_created_event(self) -> None:
        validate_event(
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

    def test_valid_job_returned_event(self) -> None:
        validate_event(
            {
                "schema_version": "v0.1",
                "event_type": "job.returned",
                "event_id": "T000001.E0007",
                "task_id": "T000001",
                "job_id": "T000001.J002",
                "related_call_type": "result.submit",
                "reported_status": "partial",
                "recorded_at": "2026-03-30T12:10:00Z",
            }
        )

    def test_valid_artifact_ref(self) -> None:
        validate_object(
            "artifact-ref",
            {
                "artifact_id": "T000001.J002.A001",
                "kind": "screenshot",
                "workspace_ref": {
                    "role": "robin",
                    "path": "/workspace/robin/tasks/T000001/jobs/J002/output/page.png",
                },
                "reported_by": "robin",
            },
        )

    def test_valid_task_record(self) -> None:
        validate_object(
            "task-record",
            {
                "task_id": "T000001",
                "task_state": "running",
                "created_at": "2026-03-30T11:59:00Z",
                "current_job_id": "T000001.J002",
                "current_plan_version": 1,
            },
        )

    def test_invalid_persisted_record(self) -> None:
        with self.assertRaises(SchemaValidationError) as ctx:
            validate_object(
                "job-record",
                {
                    "task_id": "T000001",
                    "job_id": "T000001.J002",
                    "job_state": "running",
                },
            )
        self.assertIn("created_at", str(ctx.exception))

    def test_envelope_validation_only(self) -> None:
        validate_call_envelope(
            {
                "schema_version": "v0.1",
                "call_type": "job.start",
                "task_id": "T000001",
                "job_id": "T000001.J002",
                "from_role": "robin",
                "to_role": "alfred",
                "reported_at": "2026-03-30T12:00:00Z",
            }
        )


if __name__ == "__main__":
    unittest.main()
