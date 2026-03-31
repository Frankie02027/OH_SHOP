#!/usr/bin/env python3
"""Small local storage adapter for Garage canonical state and event history."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from ops.garage_alfred import (
    Clock,
    GarageAlfredProcessor,
    GarageOfficialBundle,
    MECHANICAL_PROOF_RULE_TYPES,
)
from ops.garage_runtime import GarageRecordWrite


class GarageStorageError(RuntimeError):
    """Raised when the local Garage storage adapter cannot complete a write/read."""


class GarageStorageAdapter:
    """SQLite + JSONL storage for the first durable Garage record path."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "garage_state.db"
        self.event_log_path = self.root / "event_history.jsonl"
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._pending_counters: dict[str, int] = {}
        self._initialize_storage()

    def close(self) -> None:
        self._conn.close()

    def mint_task_id(self) -> str:
        number = self._reserve_pending_counter("task", self._max_task_number)
        return f"T{number:06d}"

    def mint_job_id(self, task_id: str) -> str:
        number = self._reserve_pending_counter(
            f"job:{task_id}",
            lambda: self._max_job_number(task_id),
        )
        return f"{task_id}.J{number:03d}"

    def mint_event_id(self, task_id: str) -> str:
        number = self._reserve_pending_counter(
            f"event:{task_id}",
            lambda: self._max_event_number(task_id),
        )
        return f"{task_id}.E{number:04d}"

    def mint_checkpoint_id(self, task_id: str) -> str:
        number = self._reserve_pending_counter(
            f"checkpoint:{task_id}",
            lambda: self._max_checkpoint_number(task_id),
        )
        return f"{task_id}.C{number:03d}"

    def write_record(self, schema_name: str, data: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        bundle = GarageOfficialBundle(
            call_type="direct-record-write",
            result=(schema_name, data),
            events=(),
            records=(GarageRecordWrite(schema_name, data),),
        )
        _, written_records = self.apply_official_bundle(bundle)
        return written_records[0]

    def apply_official_bundle(
        self,
        bundle: GarageOfficialBundle,
    ) -> tuple[tuple[dict[str, Any], ...], tuple[tuple[str, dict[str, Any]], ...]]:
        try:
            with self._conn:
                for index, record_write in enumerate(bundle.records, start=1):
                    self._before_bundle_record_write(index, record_write, bundle)
                    self._apply_record_write(record_write)
                self._persist_counters_from_bundle(bundle)
        except Exception:
            self._pending_counters.clear()
            raise

        self._pending_counters.clear()
        self._rewrite_event_log_from_sqlite()
        return (
            tuple(dict(event) for event in bundle.events),
            tuple((record.schema_name, dict(record.data)) for record in bundle.records),
        )

    def read_task_record(self, task_id: str) -> dict[str, Any] | None:
        return self._read_json_record("task_records", "task_id", task_id)

    def read_job_record(self, job_id: str) -> dict[str, Any] | None:
        return self._read_json_record("job_records", "job_id", job_id)

    def read_checkpoint_record(self, checkpoint_id: str) -> dict[str, Any] | None:
        return self._read_json_record("checkpoint_records", "checkpoint_id", checkpoint_id)

    def read_tracked_plan(self, task_id: str, plan_version: int) -> dict[str, Any] | None:
        row = self._conn.execute(
            """
            SELECT data_json
            FROM tracked_plans
            WHERE task_id = ? AND plan_version = ?
            """,
            (task_id, plan_version),
        ).fetchone()
        if row is None:
            return None
        return json.loads(row["data_json"])

    def list_continuation_records(self, task_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT data_json FROM continuation_records"
        params: tuple[Any, ...] = ()
        if task_id is not None:
            query += " WHERE task_id = ?"
            params = (task_id,)
        query += " ORDER BY row_id ASC"
        rows = self._conn.execute(query, params).fetchall()
        return [json.loads(row["data_json"]) for row in rows]

    def read_artifact_index_record(self, artifact_id: str) -> dict[str, Any] | None:
        return self._read_json_record(
            "artifact_index_records",
            "artifact_id",
            artifact_id,
        )

    def list_artifact_index_records(
        self,
        *,
        task_id: str | None = None,
        job_id: str | None = None,
        event_id: str | None = None,
    ) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT data_json FROM artifact_index_records ORDER BY artifact_id ASC"
        ).fetchall()
        records = [json.loads(row["data_json"]) for row in rows]
        filtered: list[dict[str, Any]] = []
        for record in records:
            if task_id is not None and record.get("task_id") != task_id:
                continue
            if job_id is not None and record.get("job_id") != job_id:
                continue
            if event_id is not None and record.get("event_id") != event_id:
                continue
            filtered.append(record)
        return filtered

    def read_event_history(
        self,
        task_id: str | None = None,
        job_id: str | None = None,
    ) -> list[dict[str, Any]]:
        query = "SELECT data_json FROM event_records"
        conditions: list[str] = []
        params: list[Any] = []
        if task_id is not None:
            conditions.append("task_id = ?")
            params.append(task_id)
        if job_id is not None:
            conditions.append("job_id = ?")
            params.append(job_id)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY row_id ASC"
        rows = self._conn.execute(query, tuple(params)).fetchall()
        return [json.loads(row["data_json"]) for row in rows]

    def peek_next_task_id(self) -> str:
        return f"T{self._current_counter_value('task', self._max_task_number):06d}"

    def peek_next_event_id(self, task_id: str) -> str:
        value = self._current_counter_value(f"event:{task_id}", lambda: self._max_event_number(task_id))
        return f"{task_id}.E{value:04d}"

    def peek_next_job_id(self, task_id: str) -> str:
        value = self._current_counter_value(
            f"job:{task_id}",
            lambda: self._max_job_number(task_id),
        )
        return f"{task_id}.J{value:03d}"

    def peek_next_checkpoint_id(self, task_id: str) -> str:
        value = self._current_counter_value(
            f"checkpoint:{task_id}",
            lambda: self._max_checkpoint_number(task_id),
        )
        return f"{task_id}.C{value:03d}"

    def latest_task_state_summary(self, task_id: str) -> dict[str, Any] | None:
        task_record = self.read_task_record(task_id)
        if task_record is None:
            return None
        history = self.read_event_history(task_id=task_id)
        latest_event = history[-1] if history else None
        current_job_id = task_record.get("current_job_id")
        latest_checkpoint_id = task_record.get("latest_checkpoint_id")
        latest_continuation = self.latest_continuation_for_task(task_id)
        current_job_summary = (
            self.read_job_state_summary(current_job_id)
            if isinstance(current_job_id, str)
            else None
        )
        plan_linkage = self.active_plan_linkage_summary(task_id)
        active_plan_summary = self.read_active_plan_summary(task_id)
        current_active_plan_item = self.resolve_active_plan_item(task_id)
        relevant_plan_item = self.resolve_relevant_plan_item(task_id)
        resume_anchor = self.resolve_task_resume_anchor(task_id)
        return {
            "task_record": task_record,
            "latest_event": latest_event,
            "event_count": len(history),
            "latest_meaningful_event": self._latest_meaningful_task_event(
                current_job_summary=current_job_summary,
                latest_event=latest_event,
            ),
            "current_job": current_job_summary,
            "latest_checkpoint": self.read_checkpoint_record(latest_checkpoint_id)
            if isinstance(latest_checkpoint_id, str)
            else None,
            "latest_continuation": latest_continuation,
            "current_plan_version": task_record.get("current_plan_version"),
            "active_plan_linkage": plan_linkage,
            "active_plan_summary": active_plan_summary,
            "current_active_plan_item": current_active_plan_item,
            "relevant_plan_item": relevant_plan_item,
            "current_item_evidence_refs": (
                current_active_plan_item.get("evidence_refs")
                if isinstance(current_active_plan_item, dict)
                else ()
            ),
            "relevant_evidence_refs": (
                relevant_plan_item.get("evidence_refs")
                if isinstance(relevant_plan_item, dict)
                else ()
            ),
            "current_item_proof_satisfied": (
                current_active_plan_item.get("proof_satisfied")
                if isinstance(current_active_plan_item, dict)
                else False
            ),
            "relevant_verification_rule_type": (
                relevant_plan_item.get("verification_rule_type")
                if isinstance(relevant_plan_item, dict)
                else None
            ),
            "relevant_proof_gate_reason": (
                relevant_plan_item.get("proof_gate_reason")
                if isinstance(relevant_plan_item, dict)
                else None
            ),
            "is_verification_pending": (
                isinstance(relevant_plan_item, dict)
                and bool(relevant_plan_item.get("is_verification_pending"))
            ),
            "is_waiting_on_proof": (
                isinstance(relevant_plan_item, dict)
                and bool(relevant_plan_item.get("is_verification_pending"))
            ),
            "is_waiting_on_child": task_record.get("task_state") == "waiting_on_child",
            "is_resuming": task_record.get("task_state") == "resuming",
            "is_running": task_record.get("task_state") == "running",
            "resume_anchor": resume_anchor,
            "has_resume_anchor": resume_anchor is not None,
            "latest_checkpoint_summary": self._checkpoint_anchor_summary(
                self.read_checkpoint_record(latest_checkpoint_id)
                if isinstance(latest_checkpoint_id, str)
                else None
            ),
            "latest_continuation_summary": self._continuation_anchor_summary(
                latest_continuation,
                active_plan_summary,
            ),
            "resume_evidence_refs": self.resolve_resume_evidence_refs(task_id),
            "next_plan_resume_target": self.resolve_next_plan_resume_target(task_id),
            "next_executable_unavailable_reason": (
                active_plan_summary.get("next_executable_unavailable_reason")
                if isinstance(active_plan_summary, dict)
                else None
            ),
        }

    def read_job_state_summary(self, job_id: str) -> dict[str, Any] | None:
        job_record = self.read_job_record(job_id)
        if job_record is None:
            return None
        history = self.read_event_history(job_id=job_id)
        latest_event = history[-1] if history else None
        attempt_no = self.latest_attempt_for_job(job_id)
        latest_state_event = self._latest_job_state_event(history)
        task_record = self.read_task_record(str(job_record["task_id"]))
        relevant_plan_item = (
            self.resolve_relevant_plan_item(str(job_record["task_id"]))
            if task_record is not None and task_record.get("current_job_id") == job_id
            else None
        )
        return {
            "job_record": job_record,
            "latest_event": latest_event,
            "latest_state_event": latest_state_event,
            "attempt_no": attempt_no,
            "event_count": len(history),
            "job_state": job_record.get("job_state"),
            "latest_event_type": latest_event.get("event_type") if latest_event else None,
            "latest_state_event_type": latest_state_event.get("event_type")
            if latest_state_event
            else None,
            "latest_reported_status": job_record.get("last_reported_status"),
            "latest_evidence_refs": self._extract_event_evidence_refs(
                latest_event if isinstance(latest_event, dict) else None
            ),
            "parent_job_id": job_record.get("parent_job_id"),
            "is_same_job_retry": bool(attempt_no and attempt_no > 1),
            "is_materially_new_child_leg": job_record.get("parent_job_id") is not None,
            "is_current_task_leg": (
                task_record is not None and task_record.get("current_job_id") == job_id
            ),
            "relevant_plan_item_id": (
                relevant_plan_item.get("item_id") if isinstance(relevant_plan_item, dict) else None
            ),
            "relevant_plan_item_verification_pending": (
                relevant_plan_item.get("is_verification_pending")
                if isinstance(relevant_plan_item, dict)
                else False
            ),
            "relevant_plan_item_proof_satisfied": (
                relevant_plan_item.get("proof_satisfied")
                if isinstance(relevant_plan_item, dict)
                else False
            ),
        }

    def list_child_jobs(self, parent_job_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT data_json FROM job_records ORDER BY job_id ASC"
        ).fetchall()
        records = [json.loads(row["data_json"]) for row in rows]
        return [
            record
            for record in records
            if record.get("parent_job_id") == parent_job_id
        ]

    def latest_attempt_for_job(self, job_id: str) -> int | None:
        job_record = self.read_job_record(job_id)
        if job_record is None:
            return None
        history = self.read_event_history(job_id=job_id)
        started_attempts = [
            int(event["attempt_no"])
            for event in history
            if event.get("event_type") == "job.started" and "attempt_no" in event
        ]
        record_attempt = int(job_record.get("attempt_no") or 1)
        return max([record_attempt, *started_attempts])

    def latest_continuation_for_task(self, task_id: str) -> dict[str, Any] | None:
        continuations = self.list_continuation_records(task_id)
        if not continuations:
            return None
        return continuations[-1]

    def read_active_plan_summary(self, task_id: str) -> dict[str, Any] | None:
        task_record = self.read_task_record(task_id)
        if task_record is None:
            return None
        plan_version = task_record.get("current_plan_version")
        if not isinstance(plan_version, int):
            return None
        plan = self.read_tracked_plan(task_id, plan_version)
        if plan is None:
            return None
        items = [self._plan_item_summary(plan, item) for item in plan.get("items", [])]
        current_active_item_summary = self._resolve_active_plan_item_summary(plan, items)
        relevant_plan_item_summary = self._resolve_relevant_plan_item_summary(
            items,
            current_active_item_summary,
        )
        next_executable_item = next(
            (item for item in items if item["is_executable"]),
            None,
        )
        next_executable_unavailable_reason = self._next_executable_unavailable_reason(
            items,
            relevant_plan_item_summary,
            next_executable_item,
        )
        return {
            "task_id": task_id,
            "plan_version": plan_version,
            "plan_status": plan.get("plan_status"),
            "current_active_item": plan.get("current_active_item"),
            "plan": plan,
            "items": items,
            "current_active_item_summary": current_active_item_summary,
            "next_executable_item_summary": next_executable_item,
            "next_executable_unavailable_reason": next_executable_unavailable_reason,
            "relevant_plan_item_summary": relevant_plan_item_summary,
            "verification_pending_item_summary": (
                relevant_plan_item_summary
                if isinstance(relevant_plan_item_summary, dict)
                and relevant_plan_item_summary.get("is_verification_pending")
                else None
            ),
        }

    def read_plan_item_summary(
        self,
        task_id: str,
        plan_version: int,
        item_id: str,
    ) -> dict[str, Any] | None:
        plan = self.read_tracked_plan(task_id, plan_version)
        if plan is None:
            return None
        for item in plan.get("items", []):
            if item.get("item_id") == item_id:
                return self._plan_item_summary(plan, item)
        return None

    def resolve_active_plan_item(self, task_id: str) -> dict[str, Any] | None:
        task_record = self.read_task_record(task_id)
        if task_record is None:
            return None
        plan_version = task_record.get("current_plan_version")
        if not isinstance(plan_version, int):
            return None
        plan = self.read_tracked_plan(task_id, plan_version)
        if plan is None:
            return None
        items = [self._plan_item_summary(plan, item) for item in plan.get("items", [])]
        return self._resolve_active_plan_item_summary(plan, items)

    def active_plan_linkage_summary(self, task_id: str) -> dict[str, Any] | None:
        task_record = self.read_task_record(task_id)
        if task_record is None:
            return None
        latest_checkpoint = None
        latest_checkpoint_id = task_record.get("latest_checkpoint_id")
        if isinstance(latest_checkpoint_id, str):
            latest_checkpoint = self.read_checkpoint_record(latest_checkpoint_id)
        latest_continuation = self.latest_continuation_for_task(task_id)
        active_plan_summary = self.read_active_plan_summary(task_id)
        return {
            "task_id": task_id,
            "current_plan_version": task_record.get("current_plan_version"),
            "active_plan_summary": active_plan_summary,
            "current_active_item": (
                active_plan_summary.get("current_active_item")
                if isinstance(active_plan_summary, dict)
                else None
            ),
            "current_active_item_summary": (
                active_plan_summary.get("current_active_item_summary")
                if isinstance(active_plan_summary, dict)
                else None
            ),
            "relevant_plan_item_summary": (
                active_plan_summary.get("relevant_plan_item_summary")
                if isinstance(active_plan_summary, dict)
                else None
            ),
            "verification_pending_item_summary": (
                active_plan_summary.get("verification_pending_item_summary")
                if isinstance(active_plan_summary, dict)
                else None
            ),
            "latest_checkpoint_id": latest_checkpoint_id,
            "latest_checkpoint_plan_version": (
                latest_checkpoint.get("plan_version") if latest_checkpoint else None
            ),
            "latest_continuation_plan_version": (
                latest_continuation.get("plan_version") if latest_continuation else None
            ),
            "latest_checkpoint": latest_checkpoint,
            "latest_continuation": latest_continuation,
            "next_plan_resume_target": self.resolve_next_plan_resume_target(task_id),
            "next_executable_unavailable_reason": (
                active_plan_summary.get("next_executable_unavailable_reason")
                if isinstance(active_plan_summary, dict)
                else None
            ),
        }

    def resolve_task_resume_anchor(self, task_id: str) -> dict[str, Any] | None:
        task_record = self.read_task_record(task_id)
        if task_record is None:
            return None
        relevant_plan_item = self.resolve_relevant_plan_item(task_id)
        latest_continuation = self.latest_continuation_for_task(task_id)
        if isinstance(latest_continuation, dict):
            active_plan_item = self.resolve_active_plan_item(task_id)
            return {
                "anchor_kind": "continuation-record",
                "task_id": task_id,
                "job_id": latest_continuation.get("job_id"),
                "plan_version": latest_continuation.get("plan_version"),
                "current_active_item": (
                    active_plan_item.get("item_id") if isinstance(active_plan_item, dict) else None
                ),
                "relevant_plan_item": (
                    relevant_plan_item.get("item_id") if isinstance(relevant_plan_item, dict) else None
                ),
                "verification_pending": (
                    relevant_plan_item.get("is_verification_pending")
                    if isinstance(relevant_plan_item, dict)
                    else False
                ),
                "proof_satisfied": (
                    relevant_plan_item.get("proof_satisfied")
                    if isinstance(relevant_plan_item, dict)
                    else False
                ),
                "verification_rule_type": (
                    relevant_plan_item.get("verification_rule_type")
                    if isinstance(relevant_plan_item, dict)
                    else None
                ),
                "evidence_refs": self.resolve_resume_evidence_refs(task_id),
                "record": latest_continuation,
            }
        latest_checkpoint = None
        latest_checkpoint_id = task_record.get("latest_checkpoint_id")
        if isinstance(latest_checkpoint_id, str):
            latest_checkpoint = self.read_checkpoint_record(latest_checkpoint_id)
        if isinstance(latest_checkpoint, dict):
            return {
                "anchor_kind": "checkpoint-record",
                "task_id": task_id,
                "job_id": latest_checkpoint.get("job_id"),
                "plan_version": latest_checkpoint.get("plan_version"),
                "current_active_item": latest_checkpoint.get("current_active_item"),
                "relevant_plan_item": (
                    relevant_plan_item.get("item_id") if isinstance(relevant_plan_item, dict) else None
                ),
                "verification_pending": (
                    relevant_plan_item.get("is_verification_pending")
                    if isinstance(relevant_plan_item, dict)
                    else False
                ),
                "proof_satisfied": (
                    relevant_plan_item.get("proof_satisfied")
                    if isinstance(relevant_plan_item, dict)
                    else False
                ),
                "verification_rule_type": (
                    relevant_plan_item.get("verification_rule_type")
                    if isinstance(relevant_plan_item, dict)
                    else None
                ),
                "evidence_refs": self.resolve_resume_evidence_refs(task_id),
                "record": latest_checkpoint,
            }
        current_job_id = task_record.get("current_job_id")
        current_job = (
            self.read_job_state_summary(current_job_id)
            if isinstance(current_job_id, str)
            else None
        )
        if isinstance(current_job, dict) and isinstance(current_job.get("latest_state_event"), dict):
            active_plan_item = self.resolve_active_plan_item(task_id)
            return {
                "anchor_kind": "job-state-event",
                "task_id": task_id,
                "job_id": current_job["job_record"]["job_id"],
                "plan_version": task_record.get("current_plan_version"),
                "current_active_item": (
                    active_plan_item.get("item_id") if isinstance(active_plan_item, dict) else None
                ),
                "relevant_plan_item": (
                    relevant_plan_item.get("item_id") if isinstance(relevant_plan_item, dict) else None
                ),
                "verification_pending": (
                    relevant_plan_item.get("is_verification_pending")
                    if isinstance(relevant_plan_item, dict)
                    else False
                ),
                "proof_satisfied": (
                    relevant_plan_item.get("proof_satisfied")
                    if isinstance(relevant_plan_item, dict)
                    else False
                ),
                "verification_rule_type": (
                    relevant_plan_item.get("verification_rule_type")
                    if isinstance(relevant_plan_item, dict)
                    else None
                ),
                "evidence_refs": self.resolve_resume_evidence_refs(task_id),
                "record": current_job["latest_state_event"],
            }
        return None

    def resolve_next_plan_resume_target(self, task_id: str) -> dict[str, Any] | None:
        active_plan_summary = self.read_active_plan_summary(task_id)
        if active_plan_summary is None:
            return None
        current_item = active_plan_summary.get("current_active_item_summary")
        relevant_item = active_plan_summary.get("relevant_plan_item_summary")
        resume_anchor = self.resolve_task_resume_anchor(task_id)
        next_executable_unavailable_reason = active_plan_summary.get(
            "next_executable_unavailable_reason"
        )
        if (
            isinstance(relevant_item, dict)
            and relevant_item.get("is_verification_pending")
        ):
            return {
                "task_id": task_id,
                "plan_version": active_plan_summary["plan_version"],
                "target_kind": "verification-pending",
                "item": relevant_item,
                "resume_anchor": resume_anchor,
                "next_executable_unavailable_reason": next_executable_unavailable_reason,
            }
        if isinstance(relevant_item, dict) and relevant_item.get("is_blocked"):
            return {
                "task_id": task_id,
                "plan_version": active_plan_summary["plan_version"],
                "target_kind": "blocked-evidence-review",
                "item": relevant_item,
                "resume_anchor": resume_anchor,
                "next_executable_unavailable_reason": next_executable_unavailable_reason,
            }
        if isinstance(current_item, dict):
            return {
                "task_id": task_id,
                "plan_version": active_plan_summary["plan_version"],
                "target_kind": "active-item",
                "item": current_item,
                "resume_anchor": resume_anchor,
                "next_executable_unavailable_reason": next_executable_unavailable_reason,
            }
        next_item = self.resolve_next_executable_plan_item(task_id)
        if isinstance(next_item, dict):
            return {
                "task_id": task_id,
                "plan_version": active_plan_summary["plan_version"],
                "target_kind": "next-executable",
                "item": next_item,
                "resume_anchor": resume_anchor,
                "next_executable_unavailable_reason": next_executable_unavailable_reason,
            }
        if isinstance(resume_anchor, dict):
            return {
                "task_id": task_id,
                "plan_version": active_plan_summary["plan_version"],
                "target_kind": "resume-anchor-only",
                "resume_anchor": resume_anchor,
                "next_executable_unavailable_reason": next_executable_unavailable_reason,
            }
        return None

    def resolve_next_executable_plan_item(self, task_id: str) -> dict[str, Any] | None:
        active_plan_summary = self.read_active_plan_summary(task_id)
        if active_plan_summary is None:
            return None
        for item in active_plan_summary.get("items", []):
            if item["is_executable"]:
                return item
        return None

    def explain_next_executable_unavailable(self, task_id: str) -> dict[str, Any] | None:
        active_plan_summary = self.read_active_plan_summary(task_id)
        if active_plan_summary is None:
            return None
        return active_plan_summary.get("next_executable_unavailable_reason")

    def resolve_relevant_plan_item(self, task_id: str) -> dict[str, Any] | None:
        task_record = self.read_task_record(task_id)
        if task_record is None:
            return None
        plan_version = task_record.get("current_plan_version")
        if not isinstance(plan_version, int):
            return None
        plan = self.read_tracked_plan(task_id, plan_version)
        if plan is None:
            return None
        item_summaries = [self._plan_item_summary(plan, item) for item in plan.get("items", [])]
        current_item = self._resolve_active_plan_item_summary(plan, item_summaries)
        return self._resolve_relevant_plan_item_summary(item_summaries, current_item)

    def read_relevant_proof_item_summary(self, task_id: str) -> dict[str, Any] | None:
        relevant_item = self.resolve_relevant_plan_item(task_id)
        if not isinstance(relevant_item, dict):
            return None
        return {
            "item_id": relevant_item.get("item_id"),
            "status": relevant_item.get("status"),
            "verification_rule_type": relevant_item.get("verification_rule_type"),
            "proof_satisfied": relevant_item.get("proof_satisfied"),
            "proof_gate_reason": relevant_item.get("proof_gate_reason"),
            "is_verification_pending": relevant_item.get("is_verification_pending"),
            "evidence_refs": relevant_item.get("evidence_refs", ()),
            "evidence_count": relevant_item.get("evidence_count", 0),
        }

    def resolve_resume_evidence_refs(self, task_id: str) -> tuple[dict[str, Any], ...]:
        latest_continuation = self.latest_continuation_for_task(task_id)
        if isinstance(latest_continuation, dict):
            refs = self._extract_continuation_evidence_refs(latest_continuation)
            if refs:
                return refs
        task_record = self.read_task_record(task_id)
        if isinstance(task_record, dict):
            latest_checkpoint_id = task_record.get("latest_checkpoint_id")
            if isinstance(latest_checkpoint_id, str):
                checkpoint = self.read_checkpoint_record(latest_checkpoint_id)
                refs = self._extract_checkpoint_evidence_refs(checkpoint)
                if refs:
                    return refs
        relevant_item = self.resolve_relevant_plan_item(task_id)
        if isinstance(relevant_item, dict):
            return tuple(dict(ref) for ref in relevant_item.get("evidence_refs", ()))
        return ()

    @staticmethod
    def _resolve_active_plan_item_summary(
        plan: dict[str, Any],
        item_summaries: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        current_active_item = plan.get("current_active_item")
        if isinstance(current_active_item, str):
            for item in item_summaries:
                if item.get("item_id") == current_active_item:
                    return item
        active_candidates = [
            item for item in item_summaries if item["status"] in {"in_progress", "needs_child_job", "blocked"}
        ]
        if len(active_candidates) == 1:
            return active_candidates[0]
        return None

    @staticmethod
    def _resolve_relevant_plan_item_summary(
        item_summaries: list[dict[str, Any]],
        current_item: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if isinstance(current_item, dict):
            return current_item
        for item in reversed(item_summaries):
            if item.get("is_verification_pending"):
                return item
        for item in reversed(item_summaries):
            if item["evidence_count"] > 0 or item["status"] in {"verified", "blocked"}:
                return item
        return None

    @staticmethod
    def _next_executable_unavailable_reason(
        item_summaries: list[dict[str, Any]],
        relevant_item: dict[str, Any] | None,
        next_executable_item: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if isinstance(next_executable_item, dict):
            return None
        items_by_id = {item["item_id"]: item for item in item_summaries}
        for item in item_summaries:
            if item["status"] != "todo":
                continue
            dependency_ids = item.get("depends_on", ())
            if not dependency_ids:
                continue
            for dependency_id in dependency_ids:
                dependency = items_by_id.get(str(dependency_id))
                if dependency is None:
                    return {
                        "reason": "missing_dependency",
                        "waiting_item_id": item["item_id"],
                        "blocking_dependency_item_id": dependency_id,
                    }
                if dependency["status"] == "done_unverified":
                    return {
                        "reason": "dependency_unverified",
                        "waiting_item_id": item["item_id"],
                        "blocking_dependency_item_id": dependency["item_id"],
                        "verification_rule_type": dependency.get("verification_rule_type"),
                        "proof_gate_reason": dependency.get("proof_gate_reason"),
                    }
                if dependency["status"] == "blocked":
                    return {
                        "reason": "dependency_blocked",
                        "waiting_item_id": item["item_id"],
                        "blocking_dependency_item_id": dependency["item_id"],
                    }
                if dependency["status"] not in {"verified", "abandoned"}:
                    return {
                        "reason": "dependency_incomplete",
                        "waiting_item_id": item["item_id"],
                        "blocking_dependency_item_id": dependency["item_id"],
                        "blocking_dependency_status": dependency["status"],
                    }
        if isinstance(relevant_item, dict) and relevant_item.get("is_verification_pending"):
            return {
                "reason": "verification_pending",
                "blocking_item_id": relevant_item["item_id"],
                "verification_rule_type": relevant_item.get("verification_rule_type"),
                "proof_gate_reason": relevant_item.get("proof_gate_reason"),
            }
        if isinstance(relevant_item, dict) and relevant_item.get("is_blocked"):
            return {
                "reason": "blocked_item",
                "blocking_item_id": relevant_item["item_id"],
                "evidence_count": relevant_item.get("evidence_count"),
            }
        return None

    @staticmethod
    def _proof_gate_evaluation(item: dict[str, Any]) -> dict[str, Any]:
        verification_rule = item.get("verification_rule")
        if not isinstance(verification_rule, dict):
            return {
                "rule_type": None,
                "supported": False,
                "satisfied": False,
                "reason": "no_verification_rule",
            }

        rule_type = verification_rule.get("type")
        if not isinstance(rule_type, str):
            return {
                "rule_type": None,
                "supported": False,
                "satisfied": False,
                "reason": "no_verification_rule_type",
            }

        evidence_refs = [ref for ref in item.get("evidence_refs", []) if isinstance(ref, dict)]
        artifact_refs = [ref for ref in evidence_refs if "artifact_id" in ref]
        params = verification_rule.get("params") if isinstance(verification_rule.get("params"), dict) else {}

        if rule_type not in MECHANICAL_PROOF_RULE_TYPES:
            reason = "unsupported_verification_rule"
            if rule_type == "manual_review_required":
                reason = "manual_review_required"
            elif rule_type == "downstream_item_confirms":
                reason = "downstream_item_confirms"
            elif rule_type == "test_pass":
                reason = "test_pass_not_mechanically_supported"
            return {
                "rule_type": rule_type,
                "supported": False,
                "satisfied": False,
                "reason": reason,
            }

        if rule_type == "no_extra_requirement":
            return {
                "rule_type": rule_type,
                "supported": True,
                "satisfied": True,
                "reason": None,
            }
        if rule_type == "artifact_exists":
            satisfied = bool(artifact_refs)
            return {
                "rule_type": rule_type,
                "supported": True,
                "satisfied": satisfied,
                "reason": None if satisfied else "missing_artifact_ref",
            }
        if rule_type == "artifact_matches_kind":
            required_kind = params.get("kind")
            satisfied = any(ref.get("kind") == required_kind for ref in artifact_refs)
            return {
                "rule_type": rule_type,
                "supported": True,
                "satisfied": satisfied,
                "reason": None if satisfied else "missing_required_artifact_kind",
            }
        if rule_type == "result_present":
            satisfied = any(ref.get("kind") in {"result-json", "summary"} for ref in evidence_refs)
            return {
                "rule_type": rule_type,
                "supported": True,
                "satisfied": satisfied,
                "reason": None if satisfied else "missing_result_evidence",
            }
        if rule_type == "summary_present":
            satisfied = any(ref.get("kind") == "summary" for ref in evidence_refs)
            return {
                "rule_type": rule_type,
                "supported": True,
                "satisfied": satisfied,
                "reason": None if satisfied else "missing_summary_evidence",
            }
        minimum_count = params.get("minimum_count", 1)
        try:
            minimum_count = int(minimum_count)
        except (TypeError, ValueError):
            minimum_count = 1
        satisfied = len(evidence_refs) >= max(1, minimum_count)
        return {
            "rule_type": rule_type,
            "supported": True,
            "satisfied": satisfied,
            "reason": None if satisfied else "insufficient_evidence_bundle",
        }

    @staticmethod
    def _latest_job_state_event(
        history: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        state_event_types = {
            "job.created",
            "job.dispatched",
            "job.started",
            "job.returned",
            "job.blocked",
            "job.failed",
        }
        for event in reversed(history):
            if event.get("event_type") in state_event_types:
                return event
        return None

    @staticmethod
    def _latest_meaningful_task_event(
        *,
        current_job_summary: dict[str, Any] | None,
        latest_event: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if isinstance(current_job_summary, dict):
            latest_state_event = current_job_summary.get("latest_state_event")
            if isinstance(latest_state_event, dict):
                return latest_state_event
        return latest_event

    @staticmethod
    def _plan_item_summary(
        plan: dict[str, Any],
        item: dict[str, Any],
    ) -> dict[str, Any]:
        status = str(item["status"])
        proof_gate = GarageStorageAdapter._proof_gate_evaluation(item)
        dependencies_resolved = GarageStorageAdapter._dependencies_resolved(
            plan.get("items", []),
            item,
        )
        return {
            "item": item,
            "item_id": item["item_id"],
            "title": item["title"],
            "status": status,
            "depends_on": tuple(item.get("depends_on", ())),
            "verification_rule_type": (
                item.get("verification_rule", {}).get("type")
                if isinstance(item.get("verification_rule"), dict)
                else None
            ),
            "evidence_refs": tuple(
                dict(ref) for ref in item.get("evidence_refs", []) if isinstance(ref, dict)
            ),
            "evidence_count": len(
                [ref for ref in item.get("evidence_refs", []) if isinstance(ref, dict)]
            ),
            "official_artifact_ids": tuple(
                str(ref["artifact_id"])
                for ref in item.get("evidence_refs", [])
                if isinstance(ref, dict) and "artifact_id" in ref
            ),
            "is_pending": status == "todo",
            "is_active": status in {"in_progress", "needs_child_job"},
            "is_completed": status in {"done_unverified", "verified"},
            "is_blocked": status == "blocked",
            "dependencies_resolved": dependencies_resolved,
            "is_executable": status == "todo" and dependencies_resolved,
            "is_current_target": plan.get("current_active_item") == item.get("item_id"),
            "proof_satisfied": proof_gate["satisfied"],
            "proof_gate_supported": proof_gate["supported"],
            "proof_gate_reason": proof_gate["reason"],
            "is_verification_pending": status == "done_unverified" and not proof_gate["satisfied"],
        }

    @staticmethod
    def _dependencies_resolved(
        items: list[dict[str, Any]],
        item: dict[str, Any],
    ) -> bool:
        items_by_id = {entry["item_id"]: entry for entry in items if "item_id" in entry}
        for dependency_id in item.get("depends_on", []):
            dependency = items_by_id.get(dependency_id)
            if dependency is None:
                return False
            if dependency.get("status") not in {"verified", "abandoned"}:
                return False
        return True

    @staticmethod
    def _checkpoint_anchor_summary(
        checkpoint_record: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if checkpoint_record is None:
            return None
        return {
            "checkpoint_id": checkpoint_record["checkpoint_id"],
            "job_id": checkpoint_record.get("job_id"),
            "plan_version": checkpoint_record.get("plan_version"),
            "current_active_item": checkpoint_record.get("current_active_item"),
            "resume_point": checkpoint_record.get("resume_point"),
            "reason": checkpoint_record.get("reason"),
            "evidence_refs": GarageStorageAdapter._extract_checkpoint_evidence_refs(
                checkpoint_record
            ),
            "record": checkpoint_record,
        }

    @staticmethod
    def _continuation_anchor_summary(
        continuation_record: dict[str, Any] | None,
        active_plan_summary: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if continuation_record is None:
            return None
        current_active_item = None
        if isinstance(active_plan_summary, dict):
            current_active_item = active_plan_summary.get("current_active_item")
        return {
            "job_id": continuation_record.get("job_id"),
            "plan_version": continuation_record.get("plan_version"),
            "current_active_item": current_active_item,
            "content_ref": continuation_record.get("content_ref"),
            "evidence_refs": GarageStorageAdapter._extract_continuation_evidence_refs(
                continuation_record
            ),
            "record": continuation_record,
        }

    @staticmethod
    def _extract_event_evidence_refs(
        event: dict[str, Any] | None,
    ) -> tuple[dict[str, Any], ...]:
        if event is None:
            return ()
        refs: list[dict[str, Any]] = []
        for field_name in ("artifact_refs", "workspace_refs"):
            for ref in event.get(field_name, ()):
                if isinstance(ref, dict):
                    refs.append(dict(ref))
        payload_ref = event.get("payload_ref")
        if isinstance(payload_ref, dict):
            refs.append(dict(payload_ref))
        return tuple(refs)

    @staticmethod
    def _extract_checkpoint_evidence_refs(
        checkpoint_record: dict[str, Any] | None,
    ) -> tuple[dict[str, Any], ...]:
        if checkpoint_record is None:
            return ()
        refs: list[dict[str, Any]] = []
        key_ref_bundle = checkpoint_record.get("key_ref_bundle")
        if isinstance(key_ref_bundle, dict):
            for field_name in ("artifact_refs", "workspace_refs"):
                for ref in key_ref_bundle.get(field_name, ()):
                    if isinstance(ref, dict):
                        refs.append(dict(ref))
            payload_ref = key_ref_bundle.get("payload_ref")
            if isinstance(payload_ref, dict):
                refs.append(dict(payload_ref))
        return tuple(refs)

    @staticmethod
    def _extract_continuation_evidence_refs(
        continuation_record: dict[str, Any] | None,
    ) -> tuple[dict[str, Any], ...]:
        if continuation_record is None:
            return ()
        refs: list[dict[str, Any]] = []
        for field_name in ("artifact_refs", "workspace_refs"):
            for ref in continuation_record.get(field_name, ()):
                if isinstance(ref, dict):
                    refs.append(dict(ref))
        return tuple(refs)

    def _initialize_storage(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS id_counters (
                scope TEXT PRIMARY KEY,
                next_value INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS task_records (
                task_id TEXT PRIMARY KEY,
                data_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS job_records (
                job_id TEXT PRIMARY KEY,
                data_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS checkpoint_records (
                checkpoint_id TEXT PRIMARY KEY,
                data_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tracked_plans (
                task_id TEXT NOT NULL,
                plan_version INTEGER NOT NULL,
                data_json TEXT NOT NULL,
                PRIMARY KEY(task_id, plan_version)
            );

            CREATE TABLE IF NOT EXISTS continuation_records (
                row_id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                job_id TEXT,
                created_at TEXT NOT NULL,
                data_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS event_records (
                row_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                task_id TEXT NOT NULL,
                job_id TEXT,
                recorded_at TEXT NOT NULL,
                data_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS artifact_index_records (
                artifact_id TEXT PRIMARY KEY,
                data_json TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def _reserve_pending_counter(self, scope: str, seed_func: callable) -> int:
        if scope in self._pending_counters:
            current_value = self._pending_counters[scope]
        else:
            current_value = self._current_counter_value(scope, seed_func)
        self._pending_counters[scope] = current_value + 1
        return current_value

    def _current_counter_value(self, scope: str, seed_func: callable) -> int:
        current_row = self._conn.execute(
            "SELECT next_value FROM id_counters WHERE scope = ?",
            (scope,),
        ).fetchone()
        if current_row is None:
            return max(1, int(seed_func()) + 1)
        return int(current_row["next_value"])

    def _max_task_number(self) -> int:
        row = self._conn.execute("SELECT task_id FROM task_records ORDER BY task_id DESC LIMIT 1").fetchone()
        if row is None:
            return 0
        return int(str(row["task_id"])[1:])

    def _max_job_number(self, task_id: str) -> int:
        rows = self._conn.execute(
            "SELECT data_json FROM job_records ORDER BY job_id DESC"
        ).fetchall()
        job_ids = [
            json.loads(row["data_json"])["job_id"]
            for row in rows
            if json.loads(row["data_json"]).get("task_id") == task_id
        ]
        if not job_ids:
            return 0
        return int(str(job_ids[0]).split(".J", 1)[1])

    def _max_checkpoint_number(self, task_id: str) -> int:
        row = self._conn.execute(
            """
            SELECT checkpoint_id
            FROM checkpoint_records
            WHERE checkpoint_id LIKE ?
            ORDER BY checkpoint_id DESC
            LIMIT 1
            """,
            (f"{task_id}.C%",),
        ).fetchone()
        if row is None:
            return 0
        return int(str(row["checkpoint_id"]).split(".C", 1)[1])

    def _max_event_number(self, task_id: str) -> int:
        row = self._conn.execute(
            """
            SELECT event_id
            FROM event_records
            WHERE task_id = ?
            ORDER BY row_id DESC
            LIMIT 1
            """,
            (task_id,),
        ).fetchone()
        if row is None:
            return 0
        return int(str(row["event_id"]).split(".E", 1)[1])

    def _upsert_json_record(
        self,
        table_name: str,
        key_field: str,
        key_value: str,
        data: dict[str, Any],
    ) -> None:
        self._conn.execute(
            f"""
            INSERT INTO {table_name}({key_field}, data_json)
            VALUES(?, ?)
            ON CONFLICT({key_field}) DO UPDATE SET data_json = excluded.data_json
            """,
            (key_value, json.dumps(data, sort_keys=True)),
        )
    def _insert_continuation_record(self, data: dict[str, Any]) -> None:
        self._conn.execute(
            """
            INSERT INTO continuation_records(task_id, job_id, created_at, data_json)
            VALUES(?, ?, ?, ?)
            """,
            (
                data["task_id"],
                data.get("job_id"),
                data["created_at"],
                json.dumps(data, sort_keys=True),
            ),
        )

    def _read_json_record(
        self,
        table_name: str,
        key_field: str,
        key_value: str,
    ) -> dict[str, Any] | None:
        row = self._conn.execute(
            f"SELECT data_json FROM {table_name} WHERE {key_field} = ?",
            (key_value,),
        ).fetchone()
        if row is None:
            return None
        return json.loads(row["data_json"])

    def _apply_record_write(self, record_write: GarageRecordWrite) -> None:
        schema_name = record_write.schema_name
        data = record_write.data
        if schema_name == "task-record":
            self._upsert_json_record("task_records", "task_id", data["task_id"], data)
        elif schema_name == "job-record":
            self._upsert_json_record("job_records", "job_id", data["job_id"], data)
        elif schema_name == "tracked-plan":
            self._upsert_tracked_plan(data)
        elif schema_name == "checkpoint-record":
            self._upsert_json_record(
                "checkpoint_records",
                "checkpoint_id",
                data["checkpoint_id"],
                data,
            )
        elif schema_name == "continuation-record":
            self._insert_continuation_record(data)
        elif schema_name == "artifact-index-record":
            self._upsert_json_record(
                "artifact_index_records",
                "artifact_id",
                data["artifact_id"],
                data,
            )
        elif schema_name == "event-record":
            self._insert_event_record(data)
        else:
            raise GarageStorageError(f"Unsupported schema_name for storage: {schema_name}")

    def _insert_event_record(self, data: dict[str, Any]) -> None:
        self._conn.execute(
            """
            INSERT INTO event_records(event_id, task_id, job_id, recorded_at, data_json)
            VALUES(?, ?, ?, ?, ?)
            """,
            (
                data["event_id"],
                data["task_id"],
                data.get("job_id"),
                data["recorded_at"],
                json.dumps(data, sort_keys=True),
            ),
        )

    def _upsert_tracked_plan(self, data: dict[str, Any]) -> None:
        self._conn.execute(
            """
            INSERT INTO tracked_plans(task_id, plan_version, data_json)
            VALUES(?, ?, ?)
            ON CONFLICT(task_id, plan_version) DO UPDATE SET data_json = excluded.data_json
            """,
            (
                data["task_id"],
                data["plan_version"],
                json.dumps(data, sort_keys=True),
            ),
        )

    def _persist_counters_from_bundle(self, bundle: GarageOfficialBundle) -> None:
        next_values: dict[str, int] = {}
        for record in bundle.records:
            if record.schema_name == "task-record":
                task_id = record.data["task_id"]
                next_values["task"] = max(
                    next_values.get("task", 1),
                    int(str(task_id)[1:]) + 1,
                )
            elif record.schema_name == "job-record":
                job_id = record.data["job_id"]
                task_id = record.data["task_id"]
                next_values[f"job:{task_id}"] = max(
                    next_values.get(f"job:{task_id}", 1),
                    int(str(job_id).split(".J", 1)[1]) + 1,
                )
            elif record.schema_name == "checkpoint-record":
                checkpoint_id = record.data["checkpoint_id"]
                task_id = record.data["task_id"]
                next_values[f"checkpoint:{task_id}"] = max(
                    next_values.get(f"checkpoint:{task_id}", 1),
                    int(str(checkpoint_id).split(".C", 1)[1]) + 1,
                )
            elif record.schema_name == "event-record":
                event_id = record.data["event_id"]
                task_id = record.data["task_id"]
                next_values[f"event:{task_id}"] = max(
                    next_values.get(f"event:{task_id}", 1),
                    int(str(event_id).split(".E", 1)[1]) + 1,
                )

        for scope, next_value in next_values.items():
            current_next = self._current_counter_value(scope, lambda: 0)
            persisted_next = max(current_next, next_value)
            self._conn.execute(
                """
                INSERT INTO id_counters(scope, next_value)
                VALUES(?, ?)
                ON CONFLICT(scope) DO UPDATE SET next_value = excluded.next_value
                """,
                (scope, persisted_next),
            )

    def _rewrite_event_log_from_sqlite(self) -> None:
        rows = self._conn.execute(
            "SELECT data_json FROM event_records ORDER BY row_id ASC"
        ).fetchall()
        with self.event_log_path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(row["data_json"])
                handle.write("\n")

    def _before_bundle_record_write(
        self,
        index: int,
        record_write: GarageRecordWrite,
        bundle: GarageOfficialBundle,
    ) -> None:
        """Protected hook for narrow failure-in-transaction tests."""
        return None


def build_storage_backed_alfred_processor(
    storage_root: Path | str,
    *,
    now_provider: Clock | None = None,
) -> tuple[GarageStorageAdapter, GarageAlfredProcessor]:
    """Create a storage-backed Alfred processor and its adapter."""

    storage = GarageStorageAdapter(storage_root)
    processor = GarageAlfredProcessor(
        bundle_applier=storage.apply_official_bundle,
        id_allocator=storage,
        state_reader=storage,
        now_provider=now_provider,
    )
    return storage, processor


__all__ = [
    "GarageStorageAdapter",
    "GarageStorageError",
    "build_storage_backed_alfred_processor",
]
