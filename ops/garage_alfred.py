#!/usr/bin/env python3
"""First narrow Alfred-style processor on top of the validated Garage runtime."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from ops.garage_runtime import (
    GarageHandlerOutput,
    GarageProcessingResult,
    GarageProcessorError,
    GarageRecordWrite,
    GarageRuntimeProcessor,
)


Clock = Callable[[], str]


class GarageAlfredProcessingError(RuntimeError):
    """Raised when Alfred cannot produce a coherent official bundle."""


@dataclass
class AlfredIdAllocator:
    """Small in-memory ID allocator for the first Alfred processing slice."""

    next_task_number: int = 1

    def __post_init__(self) -> None:
        self._next_event_number_by_task: dict[str, int] = defaultdict(int)
        self._next_checkpoint_number_by_task: dict[str, int] = defaultdict(int)

    def mint_task_id(self) -> str:
        task_id = f"T{self.next_task_number:06d}"
        self.next_task_number += 1
        return task_id

    def mint_event_id(self, task_id: str) -> str:
        self._next_event_number_by_task[task_id] += 1
        return f"{task_id}.E{self._next_event_number_by_task[task_id]:04d}"

    def mint_checkpoint_id(self, task_id: str) -> str:
        self._next_checkpoint_number_by_task[task_id] += 1
        return f"{task_id}.C{self._next_checkpoint_number_by_task[task_id]:03d}"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


class GarageAlfredProcessor:
    """Small deterministic Alfred-style processor for official Garage calls."""

    def __init__(
        self,
        *,
        event_recorder: Callable[[dict[str, Any]], Any] | None = None,
        record_writer: Callable[[str, dict[str, Any]], Any] | None = None,
        now_provider: Clock | None = None,
        id_allocator: AlfredIdAllocator | None = None,
    ) -> None:
        self._runtime = GarageRuntimeProcessor(
            event_recorder=event_recorder,
            record_writer=record_writer,
        )
        self._now = now_provider or _utc_now_iso
        self._ids = id_allocator or AlfredIdAllocator()
        self._register_supported_handlers()

    def process_call(self, data: dict[str, Any]) -> GarageProcessingResult:
        """Process one official Garage call through the Alfred slice."""

        return self._runtime.process_call(data)

    def supported_call_types(self) -> tuple[str, ...]:
        return (
            "task.create",
            "job.start",
            "result.submit",
            "failure.report",
            "checkpoint.create",
            "continuation.record",
        )

    def _register_supported_handlers(self) -> None:
        self._runtime.register_handler("task.create", self._handle_task_create)
        self._runtime.register_handler("job.start", self._handle_job_start)
        self._runtime.register_handler("result.submit", self._handle_result_submit)
        self._runtime.register_handler("failure.report", self._handle_failure_report)
        self._runtime.register_handler(
            "checkpoint.create", self._handle_checkpoint_create
        )
        self._runtime.register_handler(
            "continuation.record", self._handle_continuation_record
        )

    def _handle_task_create(self, call: dict[str, Any]) -> GarageHandlerOutput:
        task_id = self._ids.mint_task_id()
        recorded_at = self._recorded_at(call)
        event_id = self._ids.mint_event_id(task_id)
        event = self._build_task_created_event(call, task_id, event_id, recorded_at)
        task_record = {
            "task_id": task_id,
            "task_state": "created",
            "created_at": recorded_at,
            "updated_at": recorded_at,
        }
        return GarageHandlerOutput(
            result={
                "task_id": task_id,
                "event_id": event_id,
                "event_type": "task.created",
            },
            events=(event,),
            records=(
                GarageRecordWrite("task-record", task_record),
                self._event_record_write(event),
            ),
        )

    def _handle_job_start(self, call: dict[str, Any]) -> GarageHandlerOutput:
        task_id = call["task_id"]
        job_id = call["job_id"]
        recorded_at = self._recorded_at(call)
        event_id = self._ids.mint_event_id(task_id)
        event = self._build_job_started_event(call, event_id, recorded_at)
        job_record = {
            "task_id": task_id,
            "job_id": job_id,
            "job_state": "running",
            "from_role": call["from_role"],
            "to_role": call["to_role"],
            "latest_event_id": event_id,
            "created_at": recorded_at,
            "updated_at": recorded_at,
        }
        self._copy_optional_job_fields(call, job_record)
        return GarageHandlerOutput(
            result={
                "task_id": task_id,
                "job_id": job_id,
                "event_id": event_id,
                "event_type": "job.started",
            },
            events=(event,),
            records=(
                GarageRecordWrite("job-record", job_record),
                self._event_record_write(event),
            ),
        )

    def _handle_result_submit(self, call: dict[str, Any]) -> GarageHandlerOutput:
        task_id = call["task_id"]
        job_id = call["job_id"]
        recorded_at = self._recorded_at(call)
        event_id = self._ids.mint_event_id(task_id)
        event = self._build_job_returned_event(call, event_id, recorded_at)
        job_record = {
            "task_id": task_id,
            "job_id": job_id,
            "job_state": "returned",
            "from_role": call["from_role"],
            "to_role": call["to_role"],
            "last_reported_status": call["reported_status"],
            "latest_event_id": event_id,
            "created_at": recorded_at,
            "updated_at": recorded_at,
        }
        self._copy_optional_job_fields(call, job_record)
        return GarageHandlerOutput(
            result={
                "task_id": task_id,
                "job_id": job_id,
                "event_id": event_id,
                "event_type": "job.returned",
                "reported_status": call["reported_status"],
            },
            events=(event,),
            records=(
                GarageRecordWrite("job-record", job_record),
                self._event_record_write(event),
            ),
        )

    def _handle_failure_report(self, call: dict[str, Any]) -> GarageHandlerOutput:
        task_id = call["task_id"]
        job_id = call["job_id"]
        reported_status = call["reported_status"]
        if reported_status == "blocked":
            event_type = "job.blocked"
            job_state = "blocked"
        elif reported_status == "failed":
            event_type = "job.failed"
            job_state = "failed"
        else:
            raise GarageAlfredProcessingError(
                f"failure.report cannot map reported_status '{reported_status}'"
            )

        recorded_at = self._recorded_at(call)
        event_id = self._ids.mint_event_id(task_id)
        event = self._build_failure_event(
            call,
            event_id=event_id,
            event_type=event_type,
            recorded_at=recorded_at,
        )
        job_record = {
            "task_id": task_id,
            "job_id": job_id,
            "job_state": job_state,
            "from_role": call["from_role"],
            "to_role": call["to_role"],
            "last_reported_status": reported_status,
            "latest_event_id": event_id,
            "created_at": recorded_at,
            "updated_at": recorded_at,
        }
        self._copy_optional_job_fields(call, job_record)
        return GarageHandlerOutput(
            result={
                "task_id": task_id,
                "job_id": job_id,
                "event_id": event_id,
                "event_type": event_type,
                "reported_status": reported_status,
            },
            events=(event,),
            records=(
                GarageRecordWrite("job-record", job_record),
                self._event_record_write(event),
            ),
        )

    def _handle_checkpoint_create(self, call: dict[str, Any]) -> GarageHandlerOutput:
        task_id = call["task_id"]
        checkpoint_id = call.get("checkpoint_id") or self._ids.mint_checkpoint_id(task_id)
        recorded_at = self._recorded_at(call)
        event_id = self._ids.mint_event_id(task_id)
        event = self._build_checkpoint_created_event(
            call,
            checkpoint_id=checkpoint_id,
            event_id=event_id,
            recorded_at=recorded_at,
        )
        checkpoint_record = {
            "checkpoint_id": checkpoint_id,
            "task_id": task_id,
            "created_at": recorded_at,
        }
        if "job_id" in call:
            checkpoint_record["job_id"] = call["job_id"]
        if "plan_version" in call:
            checkpoint_record["plan_version"] = call["plan_version"]
        if isinstance(call.get("payload"), dict):
            payload = call["payload"]
            if isinstance(payload.get("current_active_item"), str):
                checkpoint_record["current_active_item"] = payload["current_active_item"]
            if isinstance(payload.get("reason"), str):
                checkpoint_record["reason"] = payload["reason"]
            if "resume_point" in payload:
                checkpoint_record["resume_point"] = payload["resume_point"]
        key_ref_bundle = self._build_key_ref_bundle(call)
        if key_ref_bundle:
            checkpoint_record["key_ref_bundle"] = key_ref_bundle
        return GarageHandlerOutput(
            result={
                "task_id": task_id,
                "checkpoint_id": checkpoint_id,
                "event_id": event_id,
                "event_type": "checkpoint.created",
            },
            events=(event,),
            records=(
                GarageRecordWrite("checkpoint-record", checkpoint_record),
                self._event_record_write(event),
            ),
        )

    def _handle_continuation_record(self, call: dict[str, Any]) -> GarageHandlerOutput:
        task_id = call["task_id"]
        recorded_at = self._recorded_at(call)
        event_id = self._ids.mint_event_id(task_id)
        event = self._build_continuation_recorded_event(call, event_id, recorded_at)
        continuation_record = {
            "task_id": task_id,
            "created_at": recorded_at,
            "content_ref": self._build_continuation_content_ref(call),
        }
        if "job_id" in call:
            continuation_record["job_id"] = call["job_id"]
        if "checkpoint_id" in call:
            continuation_record["checkpoint_id"] = call["checkpoint_id"]
        if "plan_version" in call:
            continuation_record["plan_version"] = call["plan_version"]
        if "artifact_refs" in call:
            continuation_record["artifact_refs"] = call["artifact_refs"]
        if "workspace_refs" in call:
            continuation_record["workspace_refs"] = call["workspace_refs"]
        return GarageHandlerOutput(
            result={
                "task_id": task_id,
                "event_id": event_id,
                "event_type": "continuation.recorded",
            },
            events=(event,),
            records=(
                GarageRecordWrite("continuation-record", continuation_record),
                self._event_record_write(event),
            ),
        )

    def _build_task_created_event(
        self,
        call: dict[str, Any],
        task_id: str,
        event_id: str,
        recorded_at: str,
    ) -> dict[str, Any]:
        event = {
            "schema_version": call["schema_version"],
            "event_type": "task.created",
            "event_id": event_id,
            "task_id": task_id,
            "related_call_type": "task.create",
            "recorded_at": recorded_at,
            "from_role": call["from_role"],
            "to_role": call["to_role"],
        }
        self._copy_optional_ref_fields(call, event)
        return event

    def _build_job_started_event(
        self,
        call: dict[str, Any],
        event_id: str,
        recorded_at: str,
    ) -> dict[str, Any]:
        event = {
            "schema_version": call["schema_version"],
            "event_type": "job.started",
            "event_id": event_id,
            "task_id": call["task_id"],
            "job_id": call["job_id"],
            "related_call_type": "job.start",
            "recorded_at": recorded_at,
        }
        if "attempt_no" in call:
            event["attempt_no"] = call["attempt_no"]
        return event

    def _build_job_returned_event(
        self,
        call: dict[str, Any],
        event_id: str,
        recorded_at: str,
    ) -> dict[str, Any]:
        event = {
            "schema_version": call["schema_version"],
            "event_type": "job.returned",
            "event_id": event_id,
            "task_id": call["task_id"],
            "job_id": call["job_id"],
            "related_call_type": "result.submit",
            "reported_status": call["reported_status"],
            "recorded_at": recorded_at,
        }
        self._copy_optional_ref_fields(call, event)
        return event

    def _build_failure_event(
        self,
        call: dict[str, Any],
        *,
        event_id: str,
        event_type: str,
        recorded_at: str,
    ) -> dict[str, Any]:
        event = {
            "schema_version": call["schema_version"],
            "event_type": event_type,
            "event_id": event_id,
            "task_id": call["task_id"],
            "job_id": call["job_id"],
            "related_call_type": "failure.report",
            "reported_status": call["reported_status"],
            "recorded_at": recorded_at,
        }
        self._copy_optional_ref_fields(call, event)
        return event

    def _build_checkpoint_created_event(
        self,
        call: dict[str, Any],
        *,
        checkpoint_id: str,
        event_id: str,
        recorded_at: str,
    ) -> dict[str, Any]:
        event = {
            "schema_version": call["schema_version"],
            "event_type": "checkpoint.created",
            "event_id": event_id,
            "task_id": call["task_id"],
            "checkpoint_id": checkpoint_id,
            "related_call_type": "checkpoint.create",
            "recorded_at": recorded_at,
        }
        if "job_id" in call:
            event["job_id"] = call["job_id"]
        self._copy_optional_ref_fields(call, event)
        return event

    def _build_continuation_recorded_event(
        self,
        call: dict[str, Any],
        event_id: str,
        recorded_at: str,
    ) -> dict[str, Any]:
        event = {
            "schema_version": call["schema_version"],
            "event_type": "continuation.recorded",
            "event_id": event_id,
            "task_id": call["task_id"],
            "related_call_type": "continuation.record",
            "recorded_at": recorded_at,
        }
        if "job_id" in call:
            event["job_id"] = call["job_id"]
        self._copy_optional_ref_fields(call, event)
        return event

    def _copy_optional_ref_fields(
        self,
        source: dict[str, Any],
        target: dict[str, Any],
    ) -> None:
        for field_name in ("artifact_refs", "workspace_refs", "payload_ref"):
            if field_name in source:
                target[field_name] = source[field_name]

    def _copy_optional_job_fields(
        self,
        call: dict[str, Any],
        job_record: dict[str, Any],
    ) -> None:
        for field_name in (
            "parent_job_id",
            "attempt_no",
            "artifact_refs",
            "workspace_refs",
            "payload_ref",
        ):
            if field_name in call:
                job_record[field_name] = call[field_name]

    def _recorded_at(self, call: dict[str, Any]) -> str:
        return str(call.get("reported_at") or self._now())

    def _build_key_ref_bundle(self, call: dict[str, Any]) -> dict[str, Any]:
        key_ref_bundle: dict[str, Any] = {}
        for field_name in ("artifact_refs", "workspace_refs", "payload_ref"):
            if field_name in call:
                key_ref_bundle[field_name] = call[field_name]
        payload = call.get("payload")
        if isinstance(payload, dict) and isinstance(payload.get("content_ref"), dict):
            key_ref_bundle["content_ref"] = payload["content_ref"]
        return key_ref_bundle

    def _build_continuation_content_ref(self, call: dict[str, Any]) -> dict[str, Any]:
        payload_ref = call.get("payload_ref")
        if isinstance(payload_ref, dict):
            return {
                "kind": "continuation-note",
                "payload_ref": payload_ref,
                "description": "Derived from continuation.record payload_ref",
            }

        payload = call.get("payload")
        if isinstance(payload, dict) and isinstance(payload.get("content_ref"), dict):
            return payload["content_ref"]

        raise GarageAlfredProcessingError(
            "continuation.record requires payload_ref or payload.content_ref to "
            "produce a continuation-record content_ref"
        )

    def _event_record_write(self, event: dict[str, Any]) -> GarageRecordWrite:
        return GarageRecordWrite("event-record", dict(event))


__all__ = [
    "AlfredIdAllocator",
    "GarageAlfredProcessingError",
    "GarageAlfredProcessor",
    "GarageProcessingResult",
    "GarageProcessorError",
]
