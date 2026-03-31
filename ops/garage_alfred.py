#!/usr/bin/env python3
"""First narrow Alfred-style processor on top of the validated Garage runtime."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from typing import Any, Callable, Protocol

from ops.garage_runtime import (
    GarageHandlerOutput,
    GarageProcessingResult,
    GarageProcessorError,
    GarageRecordWrite,
    GarageRuntimeProcessor,
)


Clock = Callable[[], str]
PLAN_ACTIVEISH_STATUSES = {"in_progress", "needs_child_job", "blocked"}
PLAN_RESOLVED_STATUSES = {"verified", "abandoned"}
MECHANICAL_PROOF_RULE_TYPES = {
    "artifact_exists",
    "artifact_matches_kind",
    "result_present",
    "summary_present",
    "evidence_bundle_present",
    "no_extra_requirement",
}


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

    def read_tracked_plan(
        self,
        task_id: str,
        plan_version: int,
    ) -> dict[str, Any] | None: ...


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
            "plan.record",
            "child_job.request",
            "job.start",
            "result.submit",
            "failure.report",
            "checkpoint.create",
            "continuation.record",
        )

    def _register_supported_handlers(self) -> None:
        self._runtime.register_handler("task.create", self._handle_task_create)
        self._runtime.register_handler("plan.record", self._handle_plan_record)
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

    def _handle_plan_record(self, call: dict[str, Any]) -> GarageHandlerOutput:
        payload = call.get("payload")
        if not isinstance(payload, dict):
            raise GarageAlfredProcessingError(
                "plan.record requires inline payload for tracked-plan reconstruction in this slice"
            )
        task_id = call["task_id"]
        plan_version = int(call["plan_version"])
        if payload.get("task_id") != task_id:
            raise GarageAlfredProcessingError(
                "plan.record payload.task_id must match envelope task_id"
            )
        if int(payload.get("plan_version") or 0) != plan_version:
            raise GarageAlfredProcessingError(
                "plan.record payload.plan_version must match envelope plan_version"
            )
        if "job_id" in call and "job_id" in payload and payload["job_id"] != call["job_id"]:
            raise GarageAlfredProcessingError(
                "plan.record payload.job_id must match envelope job_id when both are present"
            )

        recorded_at = self._recorded_at(call)
        event_id = self._ids.mint_event_id(task_id)
        tracked_plan = dict(payload)
        tracked_plan["items"] = [dict(item) for item in payload.get("items", [])]
        tracked_plan.setdefault("created_at", recorded_at)
        tracked_plan["updated_at"] = recorded_at
        if "job_id" in call and "job_id" not in tracked_plan:
            tracked_plan["job_id"] = call["job_id"]
        tracked_plan = self._normalize_recorded_plan(tracked_plan)
        tracked_plan["plan_status"] = self._derive_plan_status(tracked_plan)

        event = self._build_plan_recorded_event(
            call,
            event_id=event_id,
            recorded_at=recorded_at,
        )
        task_record = self._build_task_record(
            task_id,
            recorded_at,
            current_plan_version=plan_version,
        )
        return GarageHandlerOutput(
            result={
                "task_id": task_id,
                "plan_version": plan_version,
                "event_id": event_id,
                "event_type": "plan.recorded",
            },
            events=(event,),
            records=(
                GarageRecordWrite("task-record", task_record),
                GarageRecordWrite("tracked-plan", tracked_plan),
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
        tracked_plan_write = self._mutate_tracked_plan_for_child_job_request(
            task_id,
            recorded_at,
        )
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
                *(() if tracked_plan_write is None else (tracked_plan_write,)),
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
        tracked_plan_write = self._mutate_tracked_plan_for_job_start(
            task_id,
            recorded_at,
        )
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
                *(() if tracked_plan_write is None else (tracked_plan_write,)),
                self._event_record_write(event),
            ),
        )

    def _handle_result_submit(self, call: dict[str, Any]) -> GarageHandlerOutput:
        task_id = call["task_id"]
        job_id = call["job_id"]
        recorded_at = self._recorded_at(call)
        event_id = self._ids.mint_event_id(task_id)
        evidence_refs, artifact_writes = self._collect_registered_evidence(
            call,
            task_id=task_id,
            job_id=job_id,
            event_id=event_id,
            recorded_at=recorded_at,
        )
        tracked_plan_write = self._mutate_tracked_plan_for_result_submit(
            call,
            recorded_at,
            evidence_refs=evidence_refs,
        )
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
                *(() if tracked_plan_write is None else (tracked_plan_write,)),
                *artifact_writes,
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
        evidence_refs, artifact_writes = self._collect_registered_evidence(
            call,
            task_id=task_id,
            job_id=job_id,
            event_id=event_id,
            recorded_at=recorded_at,
        )
        tracked_plan_write = self._mutate_tracked_plan_for_failure_report(
            task_id,
            recorded_at,
            evidence_refs=evidence_refs,
        )
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
                *(() if tracked_plan_write is None else (tracked_plan_write,)),
                *artifact_writes,
                self._event_record_write(event),
            ),
        )

    def _handle_checkpoint_create(self, call: dict[str, Any]) -> GarageHandlerOutput:
        task_id = call["task_id"]
        checkpoint_id = call.get("checkpoint_id") or self._ids.mint_checkpoint_id(task_id)
        recorded_at = self._recorded_at(call)
        event_id = self._ids.mint_event_id(task_id)
        evidence_refs, artifact_writes = self._collect_registered_evidence(
            call,
            task_id=task_id,
            job_id=str(call["job_id"]) if "job_id" in call else None,
            event_id=event_id,
            recorded_at=recorded_at,
        )
        tracked_plan_write = self._mutate_tracked_plan_for_supporting_evidence(
            task_id,
            recorded_at,
            evidence_refs=evidence_refs,
        )
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
                *(() if tracked_plan_write is None else (tracked_plan_write,)),
                *artifact_writes,
                self._event_record_write(event),
            ),
        )

    def _handle_continuation_record(self, call: dict[str, Any]) -> GarageHandlerOutput:
        task_id = call["task_id"]
        recorded_at = self._recorded_at(call)
        event_id = self._ids.mint_event_id(task_id)
        evidence_refs, artifact_writes = self._collect_registered_evidence(
            call,
            task_id=task_id,
            job_id=str(call["job_id"]) if "job_id" in call else None,
            event_id=event_id,
            recorded_at=recorded_at,
        )
        tracked_plan_write = self._mutate_tracked_plan_for_supporting_evidence(
            task_id,
            recorded_at,
            evidence_refs=evidence_refs,
        )
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
                *(() if tracked_plan_write is None else (tracked_plan_write,)),
                *artifact_writes,
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

    def _build_plan_recorded_event(
        self,
        call: dict[str, Any],
        *,
        event_id: str,
        recorded_at: str,
    ) -> dict[str, Any]:
        event = {
            "schema_version": call["schema_version"],
            "event_type": "plan.recorded",
            "event_id": event_id,
            "task_id": call["task_id"],
            "plan_version": call["plan_version"],
            "related_call_type": "plan.record",
            "recorded_at": recorded_at,
        }
        if "job_id" in call:
            event["job_id"] = call["job_id"]
        if "payload_ref" in call:
            event["payload_ref"] = call["payload_ref"]
        return event

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

    def _mutate_tracked_plan_for_job_start(
        self,
        task_id: str,
        recorded_at: str,
    ) -> GarageRecordWrite | None:
        plan = self._existing_active_tracked_plan(task_id)
        if plan is None:
            return None
        current_item = self._current_plan_item(plan)
        if current_item is None:
            current_item = self._next_executable_item(plan)
            if current_item is None:
                raise GarageAlfredProcessingError(
                    f"job.start for task '{task_id}' cannot select a coherent active plan item"
                )
            plan["current_active_item"] = current_item["item_id"]

        status = str(current_item["status"])
        if status == "todo":
            if not self._dependencies_resolved(plan["items"], current_item):
                raise GarageAlfredProcessingError(
                    f"job.start for task '{task_id}' cannot advance blocked dependencies for "
                    f"plan item '{current_item['item_id']}'"
                )
            current_item["status"] = "in_progress"
        elif status == "in_progress":
            pass
        else:
            raise GarageAlfredProcessingError(
                f"job.start for task '{task_id}' cannot treat plan item "
                f"'{current_item['item_id']}' in status '{status}' as executable"
            )
        return self._tracked_plan_write(plan, recorded_at)

    def _mutate_tracked_plan_for_child_job_request(
        self,
        task_id: str,
        recorded_at: str,
    ) -> GarageRecordWrite | None:
        plan = self._existing_active_tracked_plan(task_id)
        if plan is None:
            return None
        current_item = self._current_plan_item(plan)
        if current_item is None:
            current_item = self._next_executable_item(plan)
            if current_item is None:
                raise GarageAlfredProcessingError(
                    f"child_job.request for task '{task_id}' cannot select a coherent active plan item"
                )
            plan["current_active_item"] = current_item["item_id"]

        status = str(current_item["status"])
        if status == "todo":
            if not self._dependencies_resolved(plan["items"], current_item):
                raise GarageAlfredProcessingError(
                    f"child_job.request for task '{task_id}' cannot hand off blocked dependencies for "
                    f"plan item '{current_item['item_id']}'"
                )
            current_item["status"] = "needs_child_job"
        elif status == "in_progress":
            current_item["status"] = "needs_child_job"
        elif status == "needs_child_job":
            pass
        else:
            raise GarageAlfredProcessingError(
                f"child_job.request for task '{task_id}' cannot treat plan item "
                f"'{current_item['item_id']}' in status '{status}' as handoff-ready"
            )
        return self._tracked_plan_write(plan, recorded_at)

    def _mutate_tracked_plan_for_result_submit(
        self,
        call: dict[str, Any],
        recorded_at: str,
        *,
        evidence_refs: tuple[dict[str, Any], ...],
    ) -> GarageRecordWrite | None:
        task_id = call["task_id"]
        plan = self._existing_active_tracked_plan(task_id)
        if plan is None:
            return None
        current_item = self._current_plan_item(plan)
        if current_item is None:
            raise GarageAlfredProcessingError(
                f"result.submit for task '{task_id}' has no coherent active plan item"
            )

        reported_status = str(call["reported_status"])
        status = str(current_item["status"])
        current_item["evidence_refs"] = self._merge_evidence_refs(
            current_item.get("evidence_refs"),
            evidence_refs,
        )
        if reported_status == "succeeded":
            if status not in {"in_progress", "needs_child_job"}:
                raise GarageAlfredProcessingError(
                    f"result.submit for task '{task_id}' cannot complete plan item "
                    f"'{current_item['item_id']}' from status '{status}'"
                )
            current_item["status"] = (
                "verified" if self._proof_gate_satisfied(current_item) else "done_unverified"
            )
            if current_item["status"] == "done_unverified":
                plan["current_active_item"] = current_item["item_id"]
            else:
                next_item = self._next_executable_item(plan, exclude_item_id=current_item["item_id"])
                if next_item is None:
                    plan.pop("current_active_item", None)
                else:
                    plan["current_active_item"] = next_item["item_id"]
        elif reported_status == "partial":
            if status == "needs_child_job":
                current_item["status"] = "in_progress"
            elif status != "in_progress":
                raise GarageAlfredProcessingError(
                    f"result.submit for task '{task_id}' cannot keep plan item "
                    f"'{current_item['item_id']}' active from status '{status}'"
                )
            plan["current_active_item"] = current_item["item_id"]
        else:
            plan["current_active_item"] = current_item["item_id"]
        return self._tracked_plan_write(plan, recorded_at)

    def _mutate_tracked_plan_for_failure_report(
        self,
        task_id: str,
        recorded_at: str,
        *,
        evidence_refs: tuple[dict[str, Any], ...],
    ) -> GarageRecordWrite | None:
        plan = self._existing_active_tracked_plan(task_id)
        if plan is None:
            return None
        current_item = self._current_plan_item(plan)
        if current_item is None:
            raise GarageAlfredProcessingError(
                f"failure.report for task '{task_id}' has no coherent active plan item"
            )
        status = str(current_item["status"])
        if status not in {"in_progress", "needs_child_job", "blocked"}:
            raise GarageAlfredProcessingError(
                f"failure.report for task '{task_id}' cannot block plan item "
                f"'{current_item['item_id']}' from status '{status}'"
            )
        current_item["status"] = "blocked"
        current_item["evidence_refs"] = self._merge_evidence_refs(
            current_item.get("evidence_refs"),
            evidence_refs,
        )
        plan["current_active_item"] = current_item["item_id"]
        return self._tracked_plan_write(plan, recorded_at)

    def _mutate_tracked_plan_for_supporting_evidence(
        self,
        task_id: str,
        recorded_at: str,
        *,
        evidence_refs: tuple[dict[str, Any], ...],
    ) -> GarageRecordWrite | None:
        if not evidence_refs:
            return None
        try:
            plan = self._existing_active_tracked_plan(task_id)
        except GarageAlfredProcessingError:
            return None
        if plan is None:
            return None
        target_item = self._verification_pending_plan_item(plan)
        if target_item is None:
            return None
        target_item["evidence_refs"] = self._merge_evidence_refs(
            target_item.get("evidence_refs"),
            evidence_refs,
        )
        if self._proof_gate_satisfied(target_item):
            target_item["status"] = "verified"
            next_item = self._next_executable_item(plan, exclude_item_id=target_item["item_id"])
            if next_item is None:
                plan.pop("current_active_item", None)
            else:
                plan["current_active_item"] = next_item["item_id"]
        else:
            plan["current_active_item"] = target_item["item_id"]
        return self._tracked_plan_write(plan, recorded_at)

    def _tracked_plan_write(
        self,
        plan: dict[str, Any],
        recorded_at: str,
    ) -> GarageRecordWrite:
        if plan.get("current_active_item") is None:
            plan.pop("current_active_item", None)
        plan["updated_at"] = recorded_at
        plan["plan_status"] = self._derive_plan_status(plan)
        return GarageRecordWrite("tracked-plan", plan)

    def _existing_active_tracked_plan(self, task_id: str) -> dict[str, Any] | None:
        task_record = self._existing_task_record(task_id)
        if task_record is None:
            return None
        plan_version = task_record.get("current_plan_version")
        if not isinstance(plan_version, int) or self._state_reader is None:
            return None
        plan = self._state_reader.read_tracked_plan(task_id, plan_version)
        if not isinstance(plan, dict):
            raise GarageAlfredProcessingError(
                f"task '{task_id}' points at missing tracked plan version '{plan_version}'"
            )
        return self._normalize_recorded_plan(
            {
                **dict(plan),
                "items": [dict(item) for item in plan.get("items", [])],
            }
        )

    def _normalize_recorded_plan(self, plan: dict[str, Any]) -> dict[str, Any]:
        items = plan.get("items")
        if not isinstance(items, list) or not items:
            raise GarageAlfredProcessingError("tracked plan requires a non-empty items list")
        items_by_id = {
            str(item["item_id"]): item
            for item in items
            if isinstance(item, dict) and "item_id" in item
        }
        current_active_item = plan.get("current_active_item")
        if current_active_item is not None:
            current_active_item = str(current_active_item)
            if current_active_item not in items_by_id:
                raise GarageAlfredProcessingError(
                    f"tracked plan current_active_item '{current_active_item}' is not present in items"
                )
            plan["current_active_item"] = current_active_item

        activeish_ids = [
            item_id
            for item_id, item in items_by_id.items()
            if item.get("status") in PLAN_ACTIVEISH_STATUSES
        ]
        if len(activeish_ids) > 1:
            raise GarageAlfredProcessingError(
                f"tracked plan has incoherent multiple active items: {activeish_ids}"
            )
        if len(activeish_ids) == 1:
            activeish_item_id = activeish_ids[0]
            if current_active_item is None:
                plan["current_active_item"] = activeish_item_id
            elif current_active_item != activeish_item_id:
                raise GarageAlfredProcessingError(
                    "tracked plan current_active_item conflicts with reconstructed active item"
                )
        for item in items:
            if (
                item.get("status") == "verified"
                and isinstance(item.get("verification_rule"), dict)
                and not self._proof_gate_satisfied(item)
            ):
                raise GarageAlfredProcessingError(
                    f"tracked plan item '{item['item_id']}' cannot be verified without a satisfied proof gate"
                )
        return plan

    @staticmethod
    def _merge_evidence_refs(
        existing_refs: Any,
        new_refs: tuple[dict[str, Any], ...],
    ) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = []
        seen: set[str] = set()
        for collection in (existing_refs or (), new_refs):
            if not isinstance(collection, (list, tuple)):
                continue
            for ref in collection:
                if not isinstance(ref, dict):
                    continue
                encoded = str(ref)
                try:
                    encoded = json.dumps(ref, sort_keys=True)
                except Exception:
                    pass
                if encoded in seen:
                    continue
                seen.add(encoded)
                merged.append(dict(ref))
        return merged

    @staticmethod
    def _proof_gate_satisfied(item: dict[str, Any]) -> bool:
        verification_rule = item.get("verification_rule")
        if not isinstance(verification_rule, dict):
            return False
        rule_type = verification_rule.get("type")
        if rule_type not in MECHANICAL_PROOF_RULE_TYPES:
            return False
        evidence_refs = [
            ref for ref in item.get("evidence_refs", [])
            if isinstance(ref, dict)
        ]
        artifact_refs = [ref for ref in evidence_refs if "artifact_id" in ref]
        params = verification_rule.get("params") if isinstance(verification_rule.get("params"), dict) else {}
        if rule_type == "no_extra_requirement":
            return True
        if rule_type == "artifact_exists":
            return bool(artifact_refs)
        if rule_type == "artifact_matches_kind":
            required_kind = params.get("kind")
            if required_kind is None:
                return bool(artifact_refs)
            return any(ref.get("kind") == required_kind for ref in artifact_refs)
        if rule_type == "result_present":
            return any(ref.get("kind") in {"result-json", "summary"} for ref in evidence_refs)
        if rule_type == "summary_present":
            return any(ref.get("kind") == "summary" for ref in evidence_refs)
        if rule_type == "evidence_bundle_present":
            minimum_count = params.get("min_count", 2)
            try:
                minimum_count = int(minimum_count)
            except Exception:
                minimum_count = 2
            return len(evidence_refs) >= max(1, minimum_count)
        return False

    def _collect_registered_evidence(
        self,
        call: dict[str, Any],
        *,
        task_id: str,
        job_id: str | None,
        event_id: str,
        recorded_at: str,
    ) -> tuple[tuple[dict[str, Any], ...], tuple[GarageRecordWrite, ...]]:
        evidence_refs: list[dict[str, Any]] = []
        artifact_writes: list[GarageRecordWrite] = []
        for artifact_ref in call.get("artifact_refs", ()):
            if not isinstance(artifact_ref, dict):
                continue
            normalized_ref = dict(artifact_ref)
            normalized_ref.setdefault("created_at", recorded_at)
            if job_id is not None:
                normalized_ref.setdefault("source_job_id", job_id)
            normalized_ref.setdefault("source_event_id", event_id)
            evidence_refs.append(normalized_ref)
            artifact_writes.append(
                GarageRecordWrite(
                    "artifact-index-record",
                    self._build_artifact_index_record(
                        normalized_ref,
                        task_id=task_id,
                        job_id=job_id,
                        event_id=event_id,
                        recorded_at=recorded_at,
                    ),
                )
            )
        for workspace_ref in call.get("workspace_refs", ()):
            if isinstance(workspace_ref, dict):
                evidence_refs.append(dict(workspace_ref))
        payload_ref = call.get("payload_ref")
        if isinstance(payload_ref, dict):
            evidence_refs.append(dict(payload_ref))
        deduped_evidence = self._merge_evidence_refs((), tuple(evidence_refs))
        deduped_writes: list[GarageRecordWrite] = []
        seen_artifact_ids: set[str] = set()
        for write in artifact_writes:
            artifact_id = str(write.data["artifact_id"])
            if artifact_id in seen_artifact_ids:
                continue
            seen_artifact_ids.add(artifact_id)
            deduped_writes.append(write)
        return tuple(deduped_evidence), tuple(deduped_writes)

    @staticmethod
    def _build_artifact_index_record(
        artifact_ref: dict[str, Any],
        *,
        task_id: str,
        job_id: str | None,
        event_id: str,
        recorded_at: str,
    ) -> dict[str, Any]:
        record = {
            "artifact_id": artifact_ref["artifact_id"],
            "kind": artifact_ref["kind"],
            "workspace_ref": artifact_ref["workspace_ref"],
            "reported_by": artifact_ref["reported_by"],
            "created_at": artifact_ref.get("created_at", recorded_at),
            "task_id": task_id,
            "event_id": event_id,
        }
        if job_id is not None:
            record["job_id"] = job_id
        for optional_field in ("description", "mime_type", "size_bytes", "hash"):
            if optional_field in artifact_ref:
                record[optional_field] = artifact_ref[optional_field]
        return record

    def _current_plan_item(self, plan: dict[str, Any]) -> dict[str, Any] | None:
        current_active_item = plan.get("current_active_item")
        if isinstance(current_active_item, str):
            return self._find_plan_item(plan, current_active_item)
        return None

    def _verification_pending_plan_item(self, plan: dict[str, Any]) -> dict[str, Any] | None:
        current_item = self._current_plan_item(plan)
        if (
            isinstance(current_item, dict)
            and current_item.get("status") == "done_unverified"
            and not self._proof_gate_satisfied(current_item)
        ):
            return current_item
        for item in reversed(plan.get("items", [])):
            if (
                item.get("status") == "done_unverified"
                and not self._proof_gate_satisfied(item)
            ):
                return item
        return None

    def _find_plan_item(
        self,
        plan: dict[str, Any],
        item_id: str,
    ) -> dict[str, Any] | None:
        for item in plan.get("items", []):
            if item.get("item_id") == item_id:
                return item
        return None

    def _next_executable_item(
        self,
        plan: dict[str, Any],
        *,
        exclude_item_id: str | None = None,
    ) -> dict[str, Any] | None:
        for item in plan.get("items", []):
            if exclude_item_id is not None and item.get("item_id") == exclude_item_id:
                continue
            if item.get("status") != "todo":
                continue
            if self._dependencies_resolved(plan.get("items", []), item):
                return item
        return None

    def _dependencies_resolved(
        self,
        items: list[dict[str, Any]],
        item: dict[str, Any],
    ) -> bool:
        items_by_id = {entry["item_id"]: entry for entry in items if "item_id" in entry}
        for dependency_id in item.get("depends_on", []):
            dependency = items_by_id.get(dependency_id)
            if dependency is None:
                return False
            if dependency.get("status") not in PLAN_RESOLVED_STATUSES:
                return False
        return True

    def _derive_plan_status(self, plan: dict[str, Any]) -> str:
        plan_status = str(plan.get("plan_status") or "active")
        if plan_status in {"abandoned", "superseded"}:
            return plan_status
        items = [
            item for item in plan.get("items", [])
            if isinstance(item, dict) and "status" in item
        ]
        if items and all(item.get("status") in PLAN_RESOLVED_STATUSES for item in items):
            return "completed"
        if any(item.get("status") == "blocked" for item in items):
            return "blocked"
        return "active"

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
