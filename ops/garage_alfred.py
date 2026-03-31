#!/usr/bin/env python3
"""First narrow Alfred-style processor on top of the validated Garage runtime."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Protocol

from ops.garage_runtime import (
    GarageHandlerOutput,
    GarageProcessingResult,
    GarageProcessorError,
    GarageRecordWrite,
    GarageRuntimeProcessor,
)


Clock = Callable[[], str]


class AlfredIdProvider(Protocol):
    """The small ID minting surface Alfred needs in this slice."""

    def mint_task_id(self) -> str: ...

    def mint_job_id(self, task_id: str) -> str: ...

    def mint_event_id(self, task_id: str) -> str: ...

    def mint_checkpoint_id(self, task_id: str) -> str: ...


class AlfredStateReader(Protocol):
    """Minimal readback surface Alfred uses for current-state continuity."""

    def read_task_record(self, task_id: str) -> dict[str, Any] | None: ...

    def read_job_record(self, job_id: str) -> dict[str, Any] | None: ...


@dataclass(frozen=True)
class GarageOfficialBundle:
    """One official Alfred-produced bundle for a single processed call."""

    call_type: str
    result: Any
    events: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    records: tuple[GarageRecordWrite, ...] = field(default_factory=tuple)


class GarageAlfredProcessingError(RuntimeError):
    """Raised when Alfred cannot produce a coherent official bundle."""


@dataclass
class AlfredIdAllocator:
    """Small in-memory ID allocator for the first Alfred processing slice."""

    next_task_number: int = 1

    def __post_init__(self) -> None:
        self._next_job_number_by_task: dict[str, int] = defaultdict(int)
        self._next_event_number_by_task: dict[str, int] = defaultdict(int)
        self._next_checkpoint_number_by_task: dict[str, int] = defaultdict(int)

    def mint_task_id(self) -> str:
        task_id = f"T{self.next_task_number:06d}"
        self.next_task_number += 1
        return task_id

    def mint_job_id(self, task_id: str) -> str:
        self._next_job_number_by_task[task_id] += 1
        return f"{task_id}.J{self._next_job_number_by_task[task_id]:03d}"

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
        bundle_applier: Callable[[GarageOfficialBundle], tuple[tuple[Any, ...], tuple[Any, ...]]] | None = None,
        now_provider: Clock | None = None,
        id_allocator: AlfredIdProvider | None = None,
        state_reader: AlfredStateReader | None = None,
    ) -> None:
        self._bundle_applier = bundle_applier
        if bundle_applier is not None:
            event_recorder = self._collect_event_for_bundle
            record_writer = self._collect_record_for_bundle
        self._runtime = GarageRuntimeProcessor(
            event_recorder=event_recorder,
            record_writer=record_writer,
        )
        self._now = now_provider or _utc_now_iso
        self._ids = id_allocator or AlfredIdAllocator()
        self._state_reader = state_reader
        self._register_supported_handlers()

    def process_call(self, data: dict[str, Any]) -> GarageProcessingResult:
        """Process one official Garage call through the Alfred slice."""

        runtime_result = self._runtime.process_call(data)
        if self._bundle_applier is None:
            return runtime_result

        bundle = GarageOfficialBundle(
            call_type=runtime_result.call_type,
            result=runtime_result.result,
            events=tuple(dict(event) for event in runtime_result.recorded_events),
            records=tuple(
                self._coerce_record_write(record)
                for record in runtime_result.written_records
            ),
        )
        recorded_events, written_records = self._bundle_applier(bundle)
        return GarageProcessingResult(
            call_type=bundle.call_type,
            result=bundle.result,
            recorded_events=recorded_events,
            written_records=written_records,
        )

    def supported_call_types(self) -> tuple[str, ...]:
        return (
            "task.create",
            "child_job.request",
            "job.start",
            "result.submit",
            "failure.report",
            "checkpoint.create",
            "continuation.record",
        )

    def _register_supported_handlers(self) -> None:
        self._runtime.register_handler("task.create", self._handle_task_create)
        self._runtime.register_handler(
            "child_job.request", self._handle_child_job_request
        )
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
        task_record = self._build_task_record(
            task_id,
            recorded_at,
            task_state="created",
        )
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

    def _handle_child_job_request(self, call: dict[str, Any]) -> GarageHandlerOutput:
        task_id = call["task_id"]
        lineage_parent_job_id = str(call.get("parent_job_id") or call["job_id"])
        child_job_id = self._mint_distinct_child_job_id(
            task_id,
            forbidden_job_ids={str(call["job_id"]), lineage_parent_job_id},
        )
        recorded_at = self._recorded_at(call)
        created_event_id = self._ids.mint_event_id(task_id)
        created_event = self._build_job_created_event(
            call,
            child_job_id=child_job_id,
            parent_job_id=lineage_parent_job_id,
            event_id=created_event_id,
            recorded_at=recorded_at,
        )
        dispatched_event_id = self._ids.mint_event_id(task_id)
        dispatched_event = self._build_job_dispatched_event(
            call,
            child_job_id=child_job_id,
            event_id=dispatched_event_id,
            recorded_at=recorded_at,
        )
        task_record = self._build_task_record(
            task_id,
            recorded_at,
            task_state="waiting_on_child",
            current_job_id=child_job_id,
        )
        job_record = self._build_job_record(
            call,
            task_id=task_id,
            job_id=child_job_id,
            job_state="dispatched",
            latest_event_id=dispatched_event_id,
            recorded_at=recorded_at,
            from_role=call["from_role"],
            to_role="robin",
            attempt_no=1,
            parent_job_id=lineage_parent_job_id,
        )
        return GarageHandlerOutput(
            result={
                "task_id": task_id,
                "job_id": child_job_id,
                "parent_job_id": lineage_parent_job_id,
                "event_ids": (created_event_id, dispatched_event_id),
                "event_types": ("job.created", "job.dispatched"),
            },
            events=(created_event, dispatched_event),
            records=(
                GarageRecordWrite("task-record", task_record),
                GarageRecordWrite("job-record", job_record),
                self._event_record_write(created_event),
                self._event_record_write(dispatched_event),
            ),
        )

    def _handle_job_start(self, call: dict[str, Any]) -> GarageHandlerOutput:
        task_id = call["task_id"]
        job_id = call["job_id"]
        existing_job_record = self._existing_job_record(job_id)
        resolved_attempt_no = self._resolve_job_start_attempt_no(
            call,
            existing_job_record,
        )
        recorded_at = self._recorded_at(call)
        event_id = self._ids.mint_event_id(task_id)
        event = self._build_job_started_event(
            call,
            event_id,
            recorded_at,
            attempt_no=resolved_attempt_no,
        )
        task_record = self._build_task_record(
            task_id,
            recorded_at,
            task_state="running",
            current_job_id=job_id,
        )
        job_record = self._build_job_record(
            call,
            task_id=task_id,
            job_id=job_id,
            job_state="running",
            latest_event_id=event_id,
            recorded_at=recorded_at,
            attempt_no=resolved_attempt_no,
        )
        return GarageHandlerOutput(
            result={
                "task_id": task_id,
                "job_id": job_id,
                "event_id": event_id,
                "event_type": "job.started",
                "attempt_no": resolved_attempt_no,
            },
            events=(event,),
            records=(
                GarageRecordWrite("task-record", task_record),
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
        task_record = self._build_task_record(
            task_id,
            recorded_at,
            task_state="resuming",
            current_job_id=job_id,
        )
        job_record = self._build_job_record(
            call,
            task_id=task_id,
            job_id=job_id,
            job_state="returned",
            latest_event_id=event_id,
            recorded_at=recorded_at,
            last_reported_status=call["reported_status"],
        )
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
                GarageRecordWrite("task-record", task_record),
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
        task_record = self._build_task_record(
            task_id,
            recorded_at,
            task_state="resuming",
            current_job_id=job_id,
        )
        job_record = self._build_job_record(
            call,
            task_id=task_id,
            job_id=job_id,
            job_state=job_state,
            latest_event_id=event_id,
            recorded_at=recorded_at,
            last_reported_status=reported_status,
        )
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
                GarageRecordWrite("task-record", task_record),
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
        task_record = self._build_task_record(
            task_id,
            recorded_at,
            latest_checkpoint_id=checkpoint_id,
            current_plan_version=call.get("plan_version"),
        )
        return GarageHandlerOutput(
            result={
                "task_id": task_id,
                "checkpoint_id": checkpoint_id,
                "event_id": event_id,
                "event_type": "checkpoint.created",
            },
            events=(event,),
            records=(
                GarageRecordWrite("task-record", task_record),
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
        task_record = self._build_task_record(
            task_id,
            recorded_at,
            latest_continuation_ref=continuation_record["content_ref"],
            current_plan_version=call.get("plan_version"),
        )
        return GarageHandlerOutput(
            result={
                "task_id": task_id,
                "event_id": event_id,
                "event_type": "continuation.recorded",
            },
            events=(event,),
            records=(
                GarageRecordWrite("task-record", task_record),
                GarageRecordWrite("continuation-record", continuation_record),
                self._event_record_write(event),
            ),
        )

    def _build_job_created_event(
        self,
        call: dict[str, Any],
        *,
        child_job_id: str,
        parent_job_id: str,
        event_id: str,
        recorded_at: str,
    ) -> dict[str, Any]:
        return {
            "schema_version": call["schema_version"],
            "event_type": "job.created",
            "event_id": event_id,
            "task_id": call["task_id"],
            "job_id": child_job_id,
            "parent_job_id": parent_job_id,
            "from_role": call["from_role"],
            "to_role": "robin",
            "recorded_at": recorded_at,
        }

    def _build_job_dispatched_event(
        self,
        call: dict[str, Any],
        *,
        child_job_id: str,
        event_id: str,
        recorded_at: str,
    ) -> dict[str, Any]:
        return {
            "schema_version": call["schema_version"],
            "event_type": "job.dispatched",
            "event_id": event_id,
            "task_id": call["task_id"],
            "job_id": child_job_id,
            "from_role": "alfred",
            "to_role": "robin",
            "recorded_at": recorded_at,
        }

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
        *,
        attempt_no: int | None = None,
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
        if attempt_no is not None:
            event["attempt_no"] = attempt_no
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

    def _build_task_record(
        self,
        task_id: str,
        recorded_at: str,
        *,
        task_state: str | None = None,
        current_job_id: str | None | object = None,
        latest_checkpoint_id: str | None | object = None,
        latest_continuation_ref: dict[str, Any] | None | object = None,
        current_plan_version: int | None = None,
    ) -> dict[str, Any]:
        existing = self._existing_task_record(task_id)
        record = dict(existing or {"task_id": task_id})
        record.setdefault("created_at", recorded_at)
        if task_state is not None:
            record["task_state"] = task_state
        else:
            record.setdefault("task_state", "created")
        if current_job_id is not None:
            record["current_job_id"] = current_job_id
        if latest_checkpoint_id is not None:
            record["latest_checkpoint_id"] = latest_checkpoint_id
        if latest_continuation_ref is not None:
            record["latest_continuation_ref"] = latest_continuation_ref
        if current_plan_version is not None:
            record["current_plan_version"] = current_plan_version
        record["updated_at"] = recorded_at
        return record

    def _build_job_record(
        self,
        call: dict[str, Any],
        *,
        task_id: str,
        job_id: str,
        job_state: str,
        latest_event_id: str,
        recorded_at: str,
        from_role: str | None = None,
        to_role: str | None = None,
        attempt_no: int | None = None,
        parent_job_id: str | None = None,
        last_reported_status: str | None = None,
    ) -> dict[str, Any]:
        existing = self._existing_job_record(job_id)
        record = dict(existing or {"task_id": task_id, "job_id": job_id})
        record["task_id"] = task_id
        record["job_id"] = job_id
        record.setdefault("created_at", recorded_at)
        record["job_state"] = job_state
        record["latest_event_id"] = latest_event_id
        record["updated_at"] = recorded_at
        record["from_role"] = from_role or str(record.get("from_role") or call["from_role"])
        record["to_role"] = to_role or str(record.get("to_role") or call["to_role"])
        if parent_job_id is not None:
            record["parent_job_id"] = parent_job_id
        elif "parent_job_id" in call:
            record["parent_job_id"] = call["parent_job_id"]
        if attempt_no is not None:
            record["attempt_no"] = attempt_no
        elif "attempt_no" in call:
            record["attempt_no"] = call["attempt_no"]
        elif "attempt_no" not in record and job_state in {"dispatched", "running"}:
            record["attempt_no"] = 1
        if last_reported_status is not None:
            record["last_reported_status"] = last_reported_status
        self._copy_optional_job_fields(call, record)
        return record

    def _resolve_job_start_attempt_no(
        self,
        call: dict[str, Any],
        existing_job_record: dict[str, Any] | None,
    ) -> int:
        explicit_attempt = call.get("attempt_no")
        explicit_value = int(explicit_attempt) if explicit_attempt is not None else None
        if existing_job_record is None:
            return explicit_value or 1

        current_attempt = int(existing_job_record.get("attempt_no") or 1)
        current_state = str(existing_job_record.get("job_state") or "")

        if current_state in {"queued", "dispatched"}:
            expected_attempt = current_attempt
        elif current_state in {"returned", "blocked", "failed", "cancelled", "completed"}:
            expected_attempt = current_attempt + 1
        elif current_state == "running":
            raise GarageAlfredProcessingError(
                f"job.start for already-running job '{call['job_id']}' is incoherent"
            )
        else:
            expected_attempt = current_attempt

        if explicit_value is None:
            return expected_attempt
        if explicit_value != expected_attempt:
            raise GarageAlfredProcessingError(
                f"job.start for '{call['job_id']}' expected attempt_no "
                f"{expected_attempt} but received {explicit_value}"
            )
        return explicit_value

    def _mint_distinct_child_job_id(
        self,
        task_id: str,
        *,
        forbidden_job_ids: set[str],
    ) -> str:
        candidate = self._ids.mint_job_id(task_id)
        while candidate in forbidden_job_ids:
            candidate = self._ids.mint_job_id(task_id)
        return candidate

    def _existing_task_record(self, task_id: str) -> dict[str, Any] | None:
        if self._state_reader is None:
            return None
        record = self._state_reader.read_task_record(task_id)
        return dict(record) if isinstance(record, dict) else None

    def _existing_job_record(self, job_id: str) -> dict[str, Any] | None:
        if self._state_reader is None:
            return None
        record = self._state_reader.read_job_record(job_id)
        return dict(record) if isinstance(record, dict) else None

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

    @staticmethod
    def _collect_event_for_bundle(event: dict[str, Any]) -> dict[str, Any]:
        return dict(event)

    @staticmethod
    def _collect_record_for_bundle(
        schema_name: str,
        data: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        return (schema_name, dict(data))

    @staticmethod
    def _coerce_record_write(record: Any) -> GarageRecordWrite:
        if isinstance(record, GarageRecordWrite):
            return record
        if (
            isinstance(record, tuple)
            and len(record) == 2
            and isinstance(record[0], str)
            and isinstance(record[1], dict)
        ):
            return GarageRecordWrite(record[0], record[1])
        raise GarageAlfredProcessingError("Bundle write intent is malformed")


__all__ = [
    "AlfredIdAllocator",
    "GarageOfficialBundle",
    "GarageAlfredProcessingError",
    "GarageAlfredProcessor",
    "GarageProcessingResult",
    "GarageProcessorError",
]
