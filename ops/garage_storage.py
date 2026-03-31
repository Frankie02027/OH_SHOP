#!/usr/bin/env python3
"""Small local storage adapter for Garage canonical state and event history."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from ops.garage_boundaries import GarageBoundaryError, validate_inbound_garage_call
from ops.garage_alfred import (
    Clock,
    GarageAlfredProcessor,
    GarageOfficialBundle,
    MECHANICAL_PROOF_RULE_TYPES,
)
from ops.garage_runtime import GarageRecordWrite

SUPPORTED_POLICY_CALL_TYPES = (
    "job.start",
    "child_job.request",
    "result.submit",
    "failure.report",
    "checkpoint.create",
    "continuation.record",
)


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
        task_policy = self.effective_task_policy_summary(task_id)
        immediate_follow_up = self.summarize_immediate_follow_up_behavior(task_id)
        next_call_hint = self.summarize_next_call_hint(task_id)
        next_call_draft = self.summarize_next_call_draft(task_id)
        next_call_draft_readiness = self.summarize_next_call_draft_readiness(task_id)
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
            "relevant_proof_policy_kind": (
                relevant_plan_item.get("proof_policy_kind")
                if isinstance(relevant_plan_item, dict)
                else None
            ),
            "relevant_proof_gate_supported": (
                relevant_plan_item.get("proof_gate_supported")
                if isinstance(relevant_plan_item, dict)
                else False
            ),
            "relevant_rule_mechanical": (
                relevant_plan_item.get("rule_mechanical")
                if isinstance(relevant_plan_item, dict)
                else False
            ),
            "relevant_rule_finality_kind": (
                relevant_plan_item.get("rule_finality_kind")
                if isinstance(relevant_plan_item, dict)
                else None
            ),
            "relevant_proof_satisfied": (
                relevant_plan_item.get("proof_satisfied")
                if isinstance(relevant_plan_item, dict)
                else False
            ),
            "relevant_unmet_requirement_kind": (
                relevant_plan_item.get("unmet_requirement_kind")
                if isinstance(relevant_plan_item, dict)
                else None
            ),
            "relevant_unmet_requirement_detail": (
                relevant_plan_item.get("unmet_requirement_detail")
                if isinstance(relevant_plan_item, dict)
                else None
            ),
            "relevant_review_required": (
                relevant_plan_item.get("review_required")
                if isinstance(relevant_plan_item, dict)
                else False
            ),
            "relevant_can_be_satisfied_by_supported_evidence_calls": (
                relevant_plan_item.get("can_be_satisfied_by_supported_evidence_calls")
                if isinstance(relevant_plan_item, dict)
                else False
            ),
            "relevant_can_only_remain_review_needed": (
                relevant_plan_item.get("can_only_remain_review_needed")
                if isinstance(relevant_plan_item, dict)
                else False
            ),
            "is_verification_pending": (
                isinstance(relevant_plan_item, dict)
                and bool(relevant_plan_item.get("is_verification_pending"))
            ),
            "is_waiting_on_proof": (
                isinstance(relevant_plan_item, dict)
                and bool(relevant_plan_item.get("is_waiting_on_proof"))
            ),
            "is_waiting_on_review": (
                isinstance(relevant_plan_item, dict)
                and bool(relevant_plan_item.get("is_waiting_on_review"))
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
            "effective_task_policy": task_policy,
            "immediate_follow_up_behavior": immediate_follow_up,
            "next_call_hint": next_call_hint,
            "next_call_draft": next_call_draft,
            "next_call_draft_readiness": next_call_draft_readiness,
            "dominant_target": (
                task_policy.get("dominant_target") if isinstance(task_policy, dict) else None
            ),
            "dominant_target_kind": (
                task_policy.get("dominant_target_kind") if isinstance(task_policy, dict) else None
            ),
            "dominant_blocker": (
                task_policy.get("dominant_blocker") if isinstance(task_policy, dict) else None
            ),
            "dominant_blocker_kind": (
                task_policy.get("dominant_blocker_kind") if isinstance(task_policy, dict) else None
            ),
            "dominant_rule_finality_kind": (
                task_policy.get("dominant_rule_finality_kind")
                if isinstance(task_policy, dict)
                else None
            ),
            "dominant_unmet_requirement_kind": (
                task_policy.get("dominant_unmet_requirement_kind")
                if isinstance(task_policy, dict)
                else None
            ),
            "dominant_unmet_requirement_detail": (
                task_policy.get("dominant_unmet_requirement_detail")
                if isinstance(task_policy, dict)
                else None
            ),
            "effective_task_posture": (
                task_policy.get("effective_task_posture") if isinstance(task_policy, dict) else None
            ),
            "execution_allowed": (
                task_policy.get("execution_allowed")
                if isinstance(task_policy, dict)
                else False
            ),
            "execution_held": (
                task_policy.get("execution_held")
                if isinstance(task_policy, dict)
                else False
            ),
            "execution_hold_kind": (
                task_policy.get("execution_hold_kind")
                if isinstance(task_policy, dict)
                else None
            ),
            "execution_hold_detail_kind": (
                task_policy.get("execution_hold_detail_kind")
                if isinstance(task_policy, dict)
                else None
            ),
            "execution_hold_detail": (
                task_policy.get("execution_hold_detail")
                if isinstance(task_policy, dict)
                else None
            ),
            "execution_hold_reason": (
                task_policy.get("execution_hold_reason")
                if isinstance(task_policy, dict)
                else None
            ),
            "allowed_call_types": (
                task_policy.get("allowed_call_types")
                if isinstance(task_policy, dict)
                else ()
            ),
            "secondary_allowed_call_types": (
                task_policy.get("secondary_allowed_call_types")
                if isinstance(task_policy, dict)
                else ()
            ),
            "blocked_call_types": (
                task_policy.get("blocked_call_types")
                if isinstance(task_policy, dict)
                else ()
            ),
            "blocked_call_reason": (
                task_policy.get("blocked_call_reason")
                if isinstance(task_policy, dict)
                else None
            ),
            "best_next_move": (
                task_policy.get("best_next_move")
                if isinstance(task_policy, dict)
                else None
            ),
            "best_next_call_type": (
                task_policy.get("best_next_call_type")
                if isinstance(task_policy, dict)
                else None
            ),
            "best_next_move_effect_kind": (
                task_policy.get("best_next_move_effect_kind")
                if isinstance(task_policy, dict)
                else None
            ),
            "follow_up_behavior_kind": (
                immediate_follow_up.get("follow_up_behavior_kind")
                if isinstance(immediate_follow_up, dict)
                else None
            ),
            "follow_up_behavior_reason": (
                immediate_follow_up.get("follow_up_behavior_reason")
                if isinstance(immediate_follow_up, dict)
                else None
            ),
            "productive_in_slice": (
                immediate_follow_up.get("productive_in_slice")
                if isinstance(immediate_follow_up, dict)
                else False
            ),
            "next_call_hint_kind": (
                next_call_hint.get("hint_kind") if isinstance(next_call_hint, dict) else None
            ),
            "next_call_recommended_call_type": (
                next_call_hint.get("recommended_call_type")
                if isinstance(next_call_hint, dict)
                else None
            ),
            "next_call_draft_kind": (
                next_call_draft.get("draft_kind") if isinstance(next_call_draft, dict) else None
            ),
            "next_call_readiness_kind": (
                next_call_draft_readiness.get("readiness_kind")
                if isinstance(next_call_draft_readiness, dict)
                else None
            ),
            "allowed_call_policy": (
                task_policy.get("allowed_call_policy")
                if isinstance(task_policy, dict)
                else ()
            ),
            "blocked_call_policy": (
                task_policy.get("blocked_call_policy")
                if isinstance(task_policy, dict)
                else ()
            ),
            "effective_waiting_on_proof": (
                task_policy.get("effective_waiting_on_proof") if isinstance(task_policy, dict) else False
            ),
            "effective_waiting_on_review": (
                task_policy.get("effective_waiting_on_review") if isinstance(task_policy, dict) else False
            ),
            "effective_blocked_evidence_review": (
                task_policy.get("effective_blocked_evidence_review") if isinstance(task_policy, dict) else False
            ),
            "effective_waiting_on_child": (
                task_policy.get("effective_waiting_on_child") if isinstance(task_policy, dict) else False
            ),
            "effective_running": (
                task_policy.get("effective_running") if isinstance(task_policy, dict) else False
            ),
            "effective_ready_for_next": (
                task_policy.get("effective_ready_for_next") if isinstance(task_policy, dict) else False
            ),
            "current_job_is_primary_focus": (
                task_policy.get("current_job_is_primary_focus") if isinstance(task_policy, dict) else False
            ),
            "relevant_plan_item_is_primary_focus": (
                task_policy.get("relevant_plan_item_is_primary_focus")
                if isinstance(task_policy, dict)
                else False
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
        active_plan_summary = (
            self.read_active_plan_summary(str(job_record["task_id"]))
            if task_record is not None
            else None
        )
        current_active_plan_item = (
            active_plan_summary.get("current_active_item_summary")
            if isinstance(active_plan_summary, dict)
            else None
        )
        current_task_job_state = (
            job_record.get("job_state")
            if task_record is not None and task_record.get("current_job_id") == job_id
            else None
        )
        task_policy = (
            self._build_task_policy_summary(
                task_record=task_record,
                active_plan_summary=active_plan_summary,
                current_active_plan_item=current_active_plan_item,
                relevant_plan_item=relevant_plan_item,
                current_job_state=current_task_job_state,
            )
            if task_record is not None
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
            "relevant_plan_item_rule_mechanical": (
                relevant_plan_item.get("rule_mechanical")
                if isinstance(relevant_plan_item, dict)
                else False
            ),
            "relevant_plan_item_rule_finality_kind": (
                relevant_plan_item.get("rule_finality_kind")
                if isinstance(relevant_plan_item, dict)
                else None
            ),
            "relevant_plan_item_proof_policy_kind": (
                relevant_plan_item.get("proof_policy_kind")
                if isinstance(relevant_plan_item, dict)
                else None
            ),
            "relevant_plan_item_unmet_requirement_kind": (
                relevant_plan_item.get("unmet_requirement_kind")
                if isinstance(relevant_plan_item, dict)
                else None
            ),
            "relevant_plan_item_unmet_requirement_detail": (
                relevant_plan_item.get("unmet_requirement_detail")
                if isinstance(relevant_plan_item, dict)
                else None
            ),
            "relevant_plan_item_review_required": (
                relevant_plan_item.get("review_required")
                if isinstance(relevant_plan_item, dict)
                else False
            ),
            "relevant_plan_item_can_be_satisfied_by_supported_evidence_calls": (
                relevant_plan_item.get("can_be_satisfied_by_supported_evidence_calls")
                if isinstance(relevant_plan_item, dict)
                else False
            ),
            "relevant_plan_item_waiting_on_proof": (
                relevant_plan_item.get("is_waiting_on_proof")
                if isinstance(relevant_plan_item, dict)
                else False
            ),
            "relevant_plan_item_waiting_on_review": (
                relevant_plan_item.get("is_waiting_on_review")
                if isinstance(relevant_plan_item, dict)
                else False
            ),
            "task_dominant_target_kind": (
                task_policy.get("dominant_target_kind") if isinstance(task_policy, dict) else None
            ),
            "task_effective_posture": (
                task_policy.get("effective_task_posture") if isinstance(task_policy, dict) else None
            ),
            "task_execution_allowed": (
                task_policy.get("execution_allowed")
                if isinstance(task_policy, dict)
                else False
            ),
            "task_execution_held": (
                task_policy.get("execution_held")
                if isinstance(task_policy, dict)
                else False
            ),
            "task_execution_hold_kind": (
                task_policy.get("execution_hold_kind")
                if isinstance(task_policy, dict)
                else None
            ),
            "task_execution_hold_detail_kind": (
                task_policy.get("execution_hold_detail_kind")
                if isinstance(task_policy, dict)
                else None
            ),
            "task_execution_hold_detail": (
                task_policy.get("execution_hold_detail")
                if isinstance(task_policy, dict)
                else None
            ),
            "task_execution_hold_reason": (
                task_policy.get("execution_hold_reason")
                if isinstance(task_policy, dict)
                else None
            ),
            "task_dominant_rule_finality_kind": (
                task_policy.get("dominant_rule_finality_kind")
                if isinstance(task_policy, dict)
                else None
            ),
            "task_dominant_unmet_requirement_kind": (
                task_policy.get("dominant_unmet_requirement_kind")
                if isinstance(task_policy, dict)
                else None
            ),
            "task_allowed_call_types": (
                task_policy.get("allowed_call_types")
                if isinstance(task_policy, dict)
                else ()
            ),
            "task_blocked_call_types": (
                task_policy.get("blocked_call_types")
                if isinstance(task_policy, dict)
                else ()
            ),
            "task_best_next_move": (
                task_policy.get("best_next_move")
                if isinstance(task_policy, dict)
                else None
            ),
            "task_best_next_move_effect_kind": (
                task_policy.get("best_next_move_effect_kind")
                if isinstance(task_policy, dict)
                else None
            ),
            "task_allowed_call_policy": (
                task_policy.get("allowed_call_policy")
                if isinstance(task_policy, dict)
                else ()
            ),
            "current_job_is_primary_focus": (
                bool(task_record is not None and task_record.get("current_job_id") == job_id)
                and bool(
                    isinstance(task_policy, dict)
                    and task_policy.get("current_job_is_primary_focus")
                )
            ),
            "current_job_subordinate_to_task_focus": (
                bool(task_record is not None and task_record.get("current_job_id") == job_id)
                and bool(
                    isinstance(task_policy, dict)
                    and not task_policy.get("current_job_is_primary_focus")
                )
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
            "relevant_proof_policy_kind": (
                relevant_plan_item_summary.get("proof_policy_kind")
                if isinstance(relevant_plan_item_summary, dict)
                else None
            ),
            "relevant_rule_finality_kind": (
                relevant_plan_item_summary.get("rule_finality_kind")
                if isinstance(relevant_plan_item_summary, dict)
                else None
            ),
            "relevant_unmet_requirement_kind": (
                relevant_plan_item_summary.get("unmet_requirement_kind")
                if isinstance(relevant_plan_item_summary, dict)
                else None
            ),
            "relevant_unmet_requirement_detail": (
                relevant_plan_item_summary.get("unmet_requirement_detail")
                if isinstance(relevant_plan_item_summary, dict)
                else None
            ),
        }

    def effective_task_policy_summary(self, task_id: str) -> dict[str, Any] | None:
        task_record = self.read_task_record(task_id)
        if task_record is None:
            return None
        active_plan_summary = self.read_active_plan_summary(task_id)
        current_active_plan_item = self.resolve_active_plan_item(task_id)
        relevant_plan_item = self.resolve_relevant_plan_item(task_id)
        current_job_state = None
        current_job_id = task_record.get("current_job_id")
        if isinstance(current_job_id, str):
            current_job_record = self.read_job_record(current_job_id)
            if isinstance(current_job_record, dict):
                current_job_state = current_job_record.get("job_state")
        return self._build_task_policy_summary(
            task_record=task_record,
            active_plan_summary=active_plan_summary,
            current_active_plan_item=current_active_plan_item,
            relevant_plan_item=relevant_plan_item,
            current_job_state=current_job_state,
        )

    def resolve_dominant_task_target(self, task_id: str) -> dict[str, Any] | None:
        policy = self.effective_task_policy_summary(task_id)
        if not isinstance(policy, dict):
            return None
        return policy.get("dominant_target")

    def resolve_dominant_task_blocker(self, task_id: str) -> dict[str, Any] | None:
        policy = self.effective_task_policy_summary(task_id)
        if not isinstance(policy, dict):
            return None
        return policy.get("dominant_blocker")

    def allowed_supported_call_types(self, task_id: str) -> tuple[str, ...] | None:
        policy = self.effective_task_policy_summary(task_id)
        if not isinstance(policy, dict):
            return None
        return policy.get("allowed_call_types")

    def blocked_supported_call_types(self, task_id: str) -> tuple[str, ...] | None:
        policy = self.effective_task_policy_summary(task_id)
        if not isinstance(policy, dict):
            return None
        return policy.get("blocked_call_types")

    def best_next_supported_move(self, task_id: str) -> dict[str, Any] | None:
        policy = self.effective_task_policy_summary(task_id)
        if not isinstance(policy, dict):
            return None
        return policy.get("best_next_move")

    def summarize_next_call_hint(self, task_id: str) -> dict[str, Any] | None:
        task_record = self.read_task_record(task_id)
        if task_record is None:
            return None
        task_policy = self.effective_task_policy_summary(task_id)
        if not isinstance(task_policy, dict):
            return None
        immediate_follow_up = self.summarize_immediate_follow_up_behavior(task_id)
        return self._classify_next_call_hint(
            task_id=task_id,
            task_record=task_record,
            task_policy=task_policy,
            immediate_follow_up=immediate_follow_up,
        )

    def summarize_next_call_draft(self, task_id: str) -> dict[str, Any] | None:
        task_record = self.read_task_record(task_id)
        if task_record is None:
            return None
        task_policy = self.effective_task_policy_summary(task_id)
        if not isinstance(task_policy, dict):
            return None
        next_call_hint = self.summarize_next_call_hint(task_id)
        if not isinstance(next_call_hint, dict):
            return None
        return self._classify_next_call_draft(
            task_id=task_id,
            task_record=task_record,
            task_policy=task_policy,
            next_call_hint=next_call_hint,
        )

    def summarize_next_call_draft_readiness(
        self,
        task_id: str,
        supplied_fields: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        next_call_draft = self.summarize_next_call_draft(task_id)
        if not isinstance(next_call_draft, dict):
            return None
        return self._classify_next_call_draft_readiness(
            next_call_draft=next_call_draft,
            supplied_fields=supplied_fields,
        )

    def summarize_next_call_preflight(
        self,
        task_id: str,
        supplied_fields: dict[str, Any] | None = None,
        *,
        default_reported_at: str | None = None,
    ) -> dict[str, Any] | None:
        task_policy = self.effective_task_policy_summary(task_id)
        if not isinstance(task_policy, dict):
            return None
        next_call_draft = self.summarize_next_call_draft(task_id)
        if not isinstance(next_call_draft, dict):
            return None
        draft_readiness = self._classify_next_call_draft_readiness(
            next_call_draft=next_call_draft,
            supplied_fields=supplied_fields,
        )
        return self._classify_next_call_preflight(
            task_id=task_id,
            task_policy=task_policy,
            next_call_draft=next_call_draft,
            draft_readiness=draft_readiness,
            default_reported_at=default_reported_at,
        )

    def summarize_immediate_follow_up_behavior(
        self,
        task_id: str,
    ) -> dict[str, Any] | None:
        task_policy = self.effective_task_policy_summary(task_id)
        if not isinstance(task_policy, dict):
            return None
        return self._classify_immediate_follow_up_behavior(task_policy)

    def summarize_applied_call_posture_transition(
        self,
        task_id: str,
        call_type: str,
        *,
        before_task_summary: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        after_task_summary = self.latest_task_state_summary(task_id)
        if not isinstance(before_task_summary, dict) or not isinstance(after_task_summary, dict):
            return None
        return self._classify_applied_call_posture_transition(
            call_type=call_type,
            before_task_summary=before_task_summary,
            after_task_summary=after_task_summary,
        )

    def evaluate_supported_call_posture_effect(
        self,
        task_id: str,
        call_type: str,
    ) -> dict[str, Any] | None:
        policy = self.effective_task_policy_summary(task_id)
        if not isinstance(policy, dict):
            return None
        allowed_policy = policy.get("allowed_call_policy", ())
        for entry in allowed_policy:
            if isinstance(entry, dict) and entry.get("call_type") == call_type:
                return dict(entry)
        blocked_policy = policy.get("blocked_call_policy", ())
        for entry in blocked_policy:
            if isinstance(entry, dict) and entry.get("call_type") == call_type:
                return dict(entry)
        return None

    @staticmethod
    def _classify_applied_call_posture_transition(
        *,
        call_type: str,
        before_task_summary: dict[str, Any],
        after_task_summary: dict[str, Any],
    ) -> dict[str, Any]:
        def _summary_target_item_id(summary: dict[str, Any]) -> str | None:
            dominant_target = summary.get("dominant_target")
            if not isinstance(dominant_target, dict):
                return None
            item = dominant_target.get("item")
            if isinstance(item, dict):
                return item.get("item_id")
            return None

        def _move_signature(move: Any) -> tuple[Any, Any, Any]:
            if not isinstance(move, dict):
                return (None, None, None)
            return (move.get("move_kind"), move.get("call_type"), move.get("effect_kind"))

        def _anchor_signature(summary: dict[str, Any]) -> tuple[Any, Any, Any]:
            anchor = summary.get("resume_anchor")
            if not isinstance(anchor, dict):
                return (None, None, None)
            record = anchor.get("record")
            record_marker = None
            if isinstance(record, dict):
                record_marker = (
                    record.get("checkpoint_id")
                    or record.get("content_ref")
                    or record.get("event_id")
                )
            return (anchor.get("anchor_kind"), anchor.get("job_id"), record_marker)

        before_target_kind = before_task_summary.get("dominant_target_kind")
        after_target_kind = after_task_summary.get("dominant_target_kind")
        before_target_item_id = _summary_target_item_id(before_task_summary)
        after_target_item_id = _summary_target_item_id(after_task_summary)
        before_unmet = before_task_summary.get("dominant_unmet_requirement_kind")
        after_unmet = after_task_summary.get("dominant_unmet_requirement_kind")
        before_unmet_detail = before_task_summary.get("dominant_unmet_requirement_detail")
        after_unmet_detail = after_task_summary.get("dominant_unmet_requirement_detail")
        before_finality = before_task_summary.get("dominant_rule_finality_kind")
        after_finality = after_task_summary.get("dominant_rule_finality_kind")
        before_move = _move_signature(before_task_summary.get("best_next_move"))
        after_move = _move_signature(after_task_summary.get("best_next_move"))
        before_hold = before_task_summary.get("execution_hold_kind")
        after_hold = after_task_summary.get("execution_hold_kind")
        before_focus = (
            before_task_summary.get("current_job_is_primary_focus"),
            before_task_summary.get("relevant_plan_item_is_primary_focus"),
        )
        after_focus = (
            after_task_summary.get("current_job_is_primary_focus"),
            after_task_summary.get("relevant_plan_item_is_primary_focus"),
        )
        before_evidence = tuple(before_task_summary.get("relevant_evidence_refs") or ())
        after_evidence = tuple(after_task_summary.get("relevant_evidence_refs") or ())
        before_anchor = _anchor_signature(before_task_summary)
        after_anchor = _anchor_signature(after_task_summary)

        dominant_changed = (
            before_target_kind != after_target_kind
            or before_target_item_id != after_target_item_id
        )
        exact_rule_changed = (
            before_unmet != after_unmet
            or before_unmet_detail != after_unmet_detail
            or before_finality != after_finality
        )
        guidance_changed = before_move != after_move or before_hold != after_hold
        focus_changed = before_focus != after_focus
        context_changed = before_evidence != after_evidence or before_anchor != after_anchor

        if dominant_changed:
            transition_kind = "resolved"
            transition_reason = (
                f"dominant posture moved from '{before_target_kind}' to '{after_target_kind}'"
            )
        elif exact_rule_changed or guidance_changed or focus_changed:
            transition_kind = "refined"
            if exact_rule_changed:
                transition_reason = (
                    f"dominant requirement/finality changed from "
                    f"'{before_unmet or before_finality}' to '{after_unmet or after_finality}'"
                )
            elif guidance_changed:
                transition_reason = "best-next-move or hold guidance changed while posture stayed dominant"
            else:
                transition_reason = "job vs proof/review focus changed while dominant posture stayed the same"
        elif context_changed:
            transition_kind = "preserved"
            transition_reason = "dominant posture stayed the same while evidence/resume context was updated"
        else:
            transition_kind = "no_effect"
            transition_reason = "dominant posture and supporting context stayed unchanged"

        return {
            "call_type": call_type,
            "transition_kind": transition_kind,
            "transition_reason": transition_reason,
            "before_dominant_target_kind": before_target_kind,
            "after_dominant_target_kind": after_target_kind,
            "before_dominant_target_item_id": before_target_item_id,
            "after_dominant_target_item_id": after_target_item_id,
            "before_dominant_blocker_kind": before_task_summary.get("dominant_blocker_kind"),
            "after_dominant_blocker_kind": after_task_summary.get("dominant_blocker_kind"),
            "before_rule_finality_kind": before_finality,
            "after_rule_finality_kind": after_finality,
            "before_unmet_requirement_kind": before_unmet,
            "after_unmet_requirement_kind": after_unmet,
            "before_unmet_requirement_detail": before_unmet_detail,
            "after_unmet_requirement_detail": after_unmet_detail,
            "before_execution_allowed": before_task_summary.get("execution_allowed"),
            "after_execution_allowed": after_task_summary.get("execution_allowed"),
            "before_execution_hold_kind": before_hold,
            "after_execution_hold_kind": after_hold,
            "before_best_next_move": before_task_summary.get("best_next_move"),
            "after_best_next_move": after_task_summary.get("best_next_move"),
            "best_next_move_changed": before_move != after_move,
            "current_job_primary_focus_before": before_focus[0],
            "current_job_primary_focus_after": after_focus[0],
            "current_job_focus_changed": before_focus != after_focus,
            "context_changed": context_changed,
        }

    @staticmethod
    def _classify_immediate_follow_up_behavior(
        task_policy: dict[str, Any],
    ) -> dict[str, Any]:
        dominant_target_kind = task_policy.get("dominant_target_kind")
        best_next_move = task_policy.get("best_next_move")
        best_next_call_type = (
            best_next_move.get("call_type") if isinstance(best_next_move, dict) else None
        )
        allowed_call_policy = tuple(task_policy.get("allowed_call_policy", ()))
        blocked_call_policy = tuple(task_policy.get("blocked_call_policy", ()))
        secondary_allowed_moves = tuple(
            dict(entry)
            for entry in allowed_call_policy
            if isinstance(entry, dict) and entry.get("call_type") != best_next_call_type
        )
        blocked_moves = tuple(
            dict(entry) for entry in blocked_call_policy if isinstance(entry, dict)
        )

        follow_up_behavior_kind = "no-productive-follow-up-in-slice"
        follow_up_behavior_reason = (
            best_next_move.get("reason")
            if isinstance(best_next_move, dict)
            else "no productive next work is available in this supported slice"
        )
        productive_in_slice = False
        requires_non_mechanical_review = False
        holds_on_blocked_evidence = False
        waits_on_child_progress = False
        actionable_evidence_gathering = False
        actionable_execution = False
        child_held_progression = False
        review_context_capture_only = False
        blocked_evidence_context_capture_only = False

        if dominant_target_kind == "proof-gathering":
            follow_up_behavior_kind = "gather-proof-next"
            productive_in_slice = True
            actionable_evidence_gathering = True
        elif dominant_target_kind == "review-needed":
            follow_up_behavior_kind = "capture-review-context-next"
            requires_non_mechanical_review = True
            review_context_capture_only = True
        elif dominant_target_kind == "blocked-evidence-review":
            follow_up_behavior_kind = "capture-blocked-evidence-next"
            holds_on_blocked_evidence = True
            blocked_evidence_context_capture_only = True
        elif dominant_target_kind == "waiting-on-child":
            follow_up_behavior_kind = "progress-child-leg-next"
            waits_on_child_progress = True
            child_held_progression = True
            productive_in_slice = isinstance(best_next_call_type, str)
        elif dominant_target_kind == "active-item":
            follow_up_behavior_kind = "resume-active-leg-next"
            productive_in_slice = True
            actionable_execution = True
        elif dominant_target_kind == "next-executable":
            follow_up_behavior_kind = "start-next-executable-next"
            productive_in_slice = True
            actionable_execution = True

        no_productive_follow_up_in_slice = not productive_in_slice
        if not isinstance(follow_up_behavior_reason, str) or not follow_up_behavior_reason:
            follow_up_behavior_reason = (
                "no productive next work is available in this supported slice"
                if no_productive_follow_up_in_slice
                else "refreshed task policy defines the next supported move"
            )

        return {
            "follow_up_behavior_kind": follow_up_behavior_kind,
            "follow_up_behavior_reason": follow_up_behavior_reason,
            "best_next_move": dict(best_next_move) if isinstance(best_next_move, dict) else None,
            "secondary_allowed_moves": secondary_allowed_moves,
            "blocked_moves": blocked_moves,
            "productive_in_slice": productive_in_slice,
            "requires_non_mechanical_review": requires_non_mechanical_review,
            "holds_on_blocked_evidence": holds_on_blocked_evidence,
            "waits_on_child_progress": waits_on_child_progress,
            "actionable_evidence_gathering": actionable_evidence_gathering,
            "actionable_execution": actionable_execution,
            "child_held_progression": child_held_progression,
            "review_context_capture_only": review_context_capture_only,
            "blocked_evidence_context_capture_only": blocked_evidence_context_capture_only,
            "no_productive_follow_up_in_slice": no_productive_follow_up_in_slice,
        }

    @staticmethod
    def _classify_next_call_hint(
        *,
        task_id: str,
        task_record: dict[str, Any],
        task_policy: dict[str, Any],
        immediate_follow_up: dict[str, Any] | None,
    ) -> dict[str, Any]:
        dominant_target_kind = task_policy.get("dominant_target_kind")
        dominant_target = task_policy.get("dominant_target")
        best_next_move = task_policy.get("best_next_move")
        current_job_id = task_record.get("current_job_id")
        current_job_state = task_record.get("task_state")
        follow_up_kind = (
            immediate_follow_up.get("follow_up_behavior_kind")
            if isinstance(immediate_follow_up, dict)
            else None
        )
        follow_up_reason = (
            immediate_follow_up.get("follow_up_behavior_reason")
            if isinstance(immediate_follow_up, dict)
            else None
        )
        recommended_call_type = (
            best_next_move.get("call_type") if isinstance(best_next_move, dict) else None
        )
        target_item_id = None
        if isinstance(dominant_target, dict):
            item = dominant_target.get("item")
            if isinstance(item, dict):
                target_item_id = item.get("item_id")

        hint_kind = "unavailable-in-slice"
        hint_reason = (
            follow_up_reason
            if isinstance(follow_up_reason, str) and follow_up_reason
            else "no concrete next supported call is available in this slice"
        )
        execution_ready = False
        requires_additional_user_or_agent_input = False
        context_only = False
        unavailable_in_slice = True

        if follow_up_kind == "start-next-executable-next" and recommended_call_type == "job.start":
            hint_kind = "executable-now"
            execution_ready = True
            unavailable_in_slice = False
            hint_reason = best_next_move.get("reason") or hint_reason
        elif follow_up_kind == "progress-child-leg-next":
            if recommended_call_type == "job.start" and isinstance(current_job_id, str):
                hint_kind = "executable-now"
                execution_ready = True
                unavailable_in_slice = False
                hint_reason = best_next_move.get("reason") or hint_reason
            else:
                hint_kind = "unavailable-in-slice"
                hint_reason = best_next_move.get("reason") or hint_reason
        elif follow_up_kind == "gather-proof-next" and isinstance(recommended_call_type, str):
            hint_kind = "caller-input-still-required"
            requires_additional_user_or_agent_input = True
            unavailable_in_slice = False
            hint_reason = best_next_move.get("reason") or hint_reason
        elif follow_up_kind in {
            "capture-review-context-next",
            "capture-blocked-evidence-next",
        } and isinstance(recommended_call_type, str):
            hint_kind = "context-only"
            requires_additional_user_or_agent_input = True
            context_only = True
            unavailable_in_slice = False
            hint_reason = best_next_move.get("reason") or hint_reason
        elif follow_up_kind == "resume-active-leg-next":
            hint_kind = "unavailable-in-slice"
            hint_reason = best_next_move.get("reason") or hint_reason

        return {
            "hint_kind": hint_kind,
            "recommended_call_type": recommended_call_type,
            "hint_reason": hint_reason,
            "task_id": task_id,
            "job_id": current_job_id if isinstance(current_job_id, str) else None,
            "target_item_id": target_item_id,
            "dominant_target_kind": dominant_target_kind,
            "execution_ready": execution_ready,
            "requires_additional_user_or_agent_input": requires_additional_user_or_agent_input,
            "context_only": context_only,
            "unavailable_in_slice": unavailable_in_slice,
            "current_task_state": current_job_state,
        }

    @staticmethod
    def _classify_next_call_draft(
        *,
        task_id: str,
        task_record: dict[str, Any],
        task_policy: dict[str, Any],
        next_call_hint: dict[str, Any],
    ) -> dict[str, Any]:
        call_type = next_call_hint.get("recommended_call_type")
        hint_kind = next_call_hint.get("hint_kind")
        dominant_target_kind = task_policy.get("dominant_target_kind")
        dominant_target = task_policy.get("dominant_target")
        current_plan_version = task_record.get("current_plan_version")
        current_job_id = task_record.get("current_job_id")
        target_item_id = next_call_hint.get("target_item_id")

        known_fields: dict[str, Any] = {}
        missing_required_fields: tuple[str, ...] = ()
        optional_fields_available: tuple[str, ...] = ()
        cannot_be_prefilled_fields: tuple[str, ...] = ()
        draft_kind = "unavailable-in-slice"
        reason = next_call_hint.get("hint_reason") or "no concrete draft is available in this slice"
        executable_now = False
        partially_ready = False
        context_only = bool(next_call_hint.get("context_only"))
        unavailable_in_slice = bool(next_call_hint.get("unavailable_in_slice"))

        if call_type == "job.start" and hint_kind == "executable-now":
            known_fields = {
                "schema_version": "v0.1",
                "call_type": "job.start",
                "task_id": task_id,
            }
            if isinstance(current_job_id, str):
                known_fields["job_id"] = current_job_id
            missing_required_fields = ("from_role", "to_role", "reported_at")
            draft_kind = "executable-now"
            executable_now = isinstance(current_job_id, str)
            unavailable_in_slice = not executable_now
            if not executable_now:
                draft_kind = "partially-ready"
                partially_ready = True
            if executable_now:
                reason = "next job.start call can be formed from current post-call state"
        elif call_type == "continuation.record" and hint_kind == "caller-input-still-required":
            known_fields = {
                "schema_version": "v0.1",
                "call_type": "continuation.record",
                "task_id": task_id,
            }
            if isinstance(current_job_id, str):
                known_fields["job_id"] = current_job_id
            if isinstance(current_plan_version, int):
                known_fields["plan_version"] = current_plan_version
            missing_required_fields = ("from_role", "to_role", "payload_ref")
            optional_fields_available = ("artifact_refs",)
            cannot_be_prefilled_fields = ("payload_ref", "payload.content_ref", "artifact_refs")
            draft_kind = "partially-ready"
            partially_ready = True
            unavailable_in_slice = False
            reason = "continuation.record is the next supported call type, but caller-provided content is still required"
        elif call_type == "continuation.record" and hint_kind == "context-only":
            known_fields = {
                "schema_version": "v0.1",
                "call_type": "continuation.record",
                "task_id": task_id,
            }
            if isinstance(current_job_id, str):
                known_fields["job_id"] = current_job_id
            if isinstance(current_plan_version, int):
                known_fields["plan_version"] = current_plan_version
            missing_required_fields = ("from_role", "to_role", "payload_ref")
            optional_fields_available = ("artifact_refs",)
            cannot_be_prefilled_fields = ("payload_ref", "payload.content_ref", "artifact_refs")
            draft_kind = "context-only"
            context_only = True
            unavailable_in_slice = False
            reason = "continuation.record can capture context, but required content must still be supplied"

        if not isinstance(target_item_id, str) and isinstance(dominant_target, dict):
            item = dominant_target.get("item")
            if isinstance(item, dict) and isinstance(item.get("item_id"), str):
                target_item_id = item["item_id"]

        return {
            "draft_kind": draft_kind,
            "call_type": call_type,
            "known_fields": known_fields,
            "missing_required_fields": missing_required_fields,
            "optional_fields_available": optional_fields_available,
            "cannot_be_prefilled_fields": cannot_be_prefilled_fields,
            "reason": reason,
            "task_id": task_id,
            "job_id": current_job_id if isinstance(current_job_id, str) else None,
            "target_item_id": target_item_id,
            "dominant_target_kind": dominant_target_kind,
            "executable_now": executable_now,
            "partially_ready": partially_ready,
            "context_only": context_only,
            "unavailable_in_slice": unavailable_in_slice,
        }

    @staticmethod
    def _classify_next_call_draft_readiness(
        *,
        next_call_draft: dict[str, Any],
        supplied_fields: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        call_type = next_call_draft.get("call_type")
        draft_kind = next_call_draft.get("draft_kind")
        known_fields = dict(next_call_draft.get("known_fields") or {})
        missing_required_fields = tuple(next_call_draft.get("missing_required_fields") or ())
        optional_fields_available = tuple(next_call_draft.get("optional_fields_available") or ())
        cannot_be_prefilled_fields = tuple(
            next_call_draft.get("cannot_be_prefilled_fields") or ()
        )
        supplied_fields = dict(supplied_fields or {})

        accepted_supplied_fields: list[str] = []
        ignored_supplied_fields: list[str] = []
        disallowed_supplied_fields: list[str] = []
        merged_known_fields = dict(known_fields)

        accepted_field_names_by_call_type: dict[str, tuple[str, ...]] = {
            "job.start": ("from_role", "to_role", "reported_at", "attempt_no"),
            "continuation.record": (
                "from_role",
                "to_role",
                "payload_ref",
                "payload",
                "artifact_refs",
            ),
        }
        disallowed_field_names_by_call_type: dict[str, tuple[str, ...]] = {
            "job.start": ("payload_ref", "payload", "artifact_refs", "content_ref"),
            "continuation.record": ("content_ref",),
        }
        accepted_field_names = accepted_field_names_by_call_type.get(str(call_type), ())
        disallowed_field_names = disallowed_field_names_by_call_type.get(str(call_type), ())

        for field_name, field_value in supplied_fields.items():
            if field_name in known_fields:
                disallowed_supplied_fields.append(field_name)
                continue
            if field_name in disallowed_field_names:
                disallowed_supplied_fields.append(field_name)
                continue
            if field_name not in accepted_field_names:
                ignored_supplied_fields.append(field_name)
                continue
            if field_name == "payload":
                if not (
                    isinstance(field_value, dict)
                    and isinstance(field_value.get("content_ref"), dict)
                ):
                    disallowed_supplied_fields.append(field_name)
                    continue
            merged_known_fields[field_name] = field_value
            accepted_supplied_fields.append(field_name)

        remaining_missing_fields: list[str] = []
        for field_name in missing_required_fields:
            if field_name == "payload_ref":
                if "payload_ref" in merged_known_fields:
                    continue
                payload = merged_known_fields.get("payload")
                if isinstance(payload, dict) and isinstance(payload.get("content_ref"), dict):
                    continue
                remaining_missing_fields.append(field_name)
                continue
            if field_name not in merged_known_fields:
                remaining_missing_fields.append(field_name)

        if call_type == "job.start" and draft_kind == "executable-now":
            remaining_missing_fields = []

        reason = next_call_draft.get("reason") or "draft readiness is limited by current supported slice"
        readiness_kind = "unavailable-in-slice"
        executable_now = False
        partially_ready = False
        context_only = bool(next_call_draft.get("context_only"))
        unavailable_in_slice = bool(next_call_draft.get("unavailable_in_slice"))

        if unavailable_in_slice:
            readiness_kind = "unavailable-in-slice"
        elif context_only:
            readiness_kind = "context-only"
            reason = (
                "draft can capture context in this slice but does not become execution-ready"
            )
        elif remaining_missing_fields:
            readiness_kind = "partially-ready"
            partially_ready = True
            reason = "draft still needs caller-supplied required fields before it becomes runnable"
        else:
            readiness_kind = "executable-now"
            executable_now = True
            reason = "draft has the minimum required fields for honest submission in this slice"

        return {
            "readiness_kind": readiness_kind,
            "call_type": call_type,
            "merged_known_fields": merged_known_fields,
            "accepted_supplied_fields": tuple(accepted_supplied_fields),
            "ignored_supplied_fields": tuple(ignored_supplied_fields),
            "disallowed_supplied_fields": tuple(disallowed_supplied_fields),
            "missing_required_fields": tuple(remaining_missing_fields),
            "reason": reason,
            "task_id": next_call_draft.get("task_id"),
            "job_id": next_call_draft.get("job_id"),
            "target_item_id": next_call_draft.get("target_item_id"),
            "executable_now": executable_now,
            "partially_ready": partially_ready,
            "context_only": context_only,
            "unavailable_in_slice": unavailable_in_slice,
        }

    def _classify_next_call_preflight(
        self,
        *,
        task_id: str,
        task_policy: dict[str, Any],
        next_call_draft: dict[str, Any],
        draft_readiness: dict[str, Any],
        default_reported_at: str | None = None,
    ) -> dict[str, Any]:
        call_type = draft_readiness.get("call_type")
        context_only = bool(draft_readiness.get("context_only"))
        unavailable_in_slice = bool(draft_readiness.get("unavailable_in_slice"))
        missing_required_fields = tuple(draft_readiness.get("missing_required_fields") or ())
        accepted_supplied_fields = tuple(
            draft_readiness.get("accepted_supplied_fields") or ()
        )
        ignored_supplied_fields = tuple(
            draft_readiness.get("ignored_supplied_fields") or ()
        )
        disallowed_supplied_fields = tuple(
            draft_readiness.get("disallowed_supplied_fields") or ()
        )
        merged_known_fields = dict(draft_readiness.get("merged_known_fields") or {})
        prepared_call = self._prepare_next_call_from_readiness(
            call_type=str(call_type) if isinstance(call_type, str) else None,
            merged_known_fields=merged_known_fields,
            default_reported_at=default_reported_at,
        )
        remaining_missing_fields = self._remaining_missing_prepared_fields(
            required_fields=missing_required_fields,
            prepared_call=prepared_call,
        )

        preflight_kind = "unavailable_in_slice"
        policy_block_reason = None
        reason = next_call_draft.get("reason") or "no honest prepared next call is available"
        ready_to_submit = False

        if unavailable_in_slice:
            preflight_kind = "unavailable_in_slice"
            prepared_call = None
            reason = "current post-call posture does not expose an honest next supported call in this slice"
        elif context_only:
            preflight_kind = "context_only_not_submittable"
            if remaining_missing_fields:
                prepared_call = None
                reason = (
                    "context-only follow-up remains non-execution work and still needs "
                    "caller-supplied required fields"
                )
            else:
                prepared_call, validation_error = self._validate_prepared_call(prepared_call)
                if validation_error is not None:
                    prepared_call = None
                    reason = validation_error
                else:
                    reason = (
                        "prepared call can capture context, but current posture remains "
                        "non-execution and not submittable as productive next work"
                    )
        elif remaining_missing_fields:
            preflight_kind = "not_ready_missing_fields"
            prepared_call = None
            reason = "prepared next call still needs caller-supplied required fields"
        else:
            prepared_call, validation_error = self._validate_prepared_call(prepared_call)
            if validation_error is not None:
                preflight_kind = "not_ready_missing_fields"
                prepared_call = None
                reason = validation_error
            else:
                policy = self.evaluate_supported_call_policy(
                    task_id,
                    str(call_type),
                    job_id=(
                        prepared_call.get("job_id")
                        if isinstance(prepared_call, dict)
                        and isinstance(prepared_call.get("job_id"), str)
                        else None
                    ),
                    parent_job_id=(
                        prepared_call.get("parent_job_id")
                        if isinstance(prepared_call, dict)
                        and isinstance(prepared_call.get("parent_job_id"), str)
                        else None
                    ),
                )
                if isinstance(policy, dict) and not policy.get("allowed", True):
                    preflight_kind = "policy_blocked"
                    policy_block_reason = (
                        policy.get("rejection_reason")
                        or policy.get("execution_hold_reason")
                        or "call_not_allowed"
                    )
                    reason = (
                        "prepared next call is structurally complete but is still blocked "
                        "by current supported-call policy"
                    )
                else:
                    preflight_kind = "ready_to_submit"
                    ready_to_submit = True
                    reason = "prepared next call is structurally valid and allowed in this slice"

        return {
            "preflight_kind": preflight_kind,
            "call_type": call_type,
            "prepared_call": prepared_call,
            "accepted_supplied_fields": accepted_supplied_fields,
            "ignored_supplied_fields": ignored_supplied_fields,
            "disallowed_supplied_fields": disallowed_supplied_fields,
            "missing_required_fields": remaining_missing_fields,
            "policy_block_reason": policy_block_reason,
            "reason": reason,
            "task_id": draft_readiness.get("task_id"),
            "job_id": draft_readiness.get("job_id"),
            "target_item_id": draft_readiness.get("target_item_id"),
            "ready_to_submit": ready_to_submit,
            "context_only": context_only,
            "unavailable_in_slice": unavailable_in_slice,
        }

    @staticmethod
    def _prepare_next_call_from_readiness(
        *,
        call_type: str | None,
        merged_known_fields: dict[str, Any],
        default_reported_at: str | None = None,
    ) -> dict[str, Any] | None:
        if not isinstance(call_type, str):
            return None

        prepared_call = dict(merged_known_fields)
        if call_type == "job.start":
            prepared_call.setdefault("schema_version", "v0.1")
            prepared_call.setdefault("call_type", "job.start")
            prepared_call.setdefault("from_role", "jarvis")
            prepared_call.setdefault("to_role", "alfred")
            if isinstance(default_reported_at, str) and default_reported_at:
                prepared_call.setdefault("reported_at", default_reported_at)
            return prepared_call

        if call_type == "continuation.record":
            prepared_call.setdefault("schema_version", "v0.1")
            prepared_call.setdefault("call_type", "continuation.record")
            prepared_call.setdefault("from_role", "jarvis")
            prepared_call.setdefault("to_role", "alfred")
            return prepared_call

        return None

    @staticmethod
    def _validate_prepared_call(
        prepared_call: dict[str, Any] | None,
    ) -> tuple[dict[str, Any] | None, str | None]:
        if not isinstance(prepared_call, dict):
            return None, "prepared next call could not be built honestly from known and supplied fields"
        try:
            validated = dict(validate_inbound_garage_call(dict(prepared_call)))
        except GarageBoundaryError as exc:
            return None, str(exc)
        return validated, None

    @staticmethod
    def _remaining_missing_prepared_fields(
        *,
        required_fields: tuple[str, ...],
        prepared_call: dict[str, Any] | None,
    ) -> tuple[str, ...]:
        if not isinstance(prepared_call, dict):
            return required_fields

        remaining: list[str] = []
        for field_name in required_fields:
            if field_name == "payload_ref":
                if "payload_ref" in prepared_call:
                    continue
                payload = prepared_call.get("payload")
                if isinstance(payload, dict) and isinstance(payload.get("content_ref"), dict):
                    continue
                remaining.append(field_name)
                continue
            if field_name not in prepared_call:
                remaining.append(field_name)
        return tuple(remaining)

    def evaluate_supported_call_policy(
        self,
        task_id: str,
        call_type: str,
        *,
        job_id: str | None = None,
        parent_job_id: str | None = None,
    ) -> dict[str, Any] | None:
        task_record = self.read_task_record(task_id)
        if task_record is None:
            return None
        policy = self.effective_task_policy_summary(task_id)
        if not isinstance(policy, dict):
            return None

        dominant_target_kind = policy.get("dominant_target_kind")
        current_job_id = task_record.get("current_job_id")
        allowed_call_types = tuple(policy.get("allowed_call_types", ()))
        allowed = call_type in allowed_call_types
        rejection_reason = None

        if not allowed:
            rejection_reason = (
                policy.get("execution_hold_reason")
                or (
                    policy.get("dominant_blocker", {}).get("reason")
                    if isinstance(policy.get("dominant_blocker"), dict)
                    else None
                )
                or "call_not_allowed_for_current_target"
            )
        elif dominant_target_kind == "waiting-on-child" and call_type in {
            "job.start",
            "result.submit",
            "failure.report",
        }:
            if not (isinstance(current_job_id, str) and job_id == current_job_id):
                allowed = False
                rejection_reason = "waiting_on_child_current_job_only"
        elif dominant_target_kind == "waiting-on-child" and call_type == "child_job.request":
            if not (
                isinstance(current_job_id, str)
                and (
                    job_id == current_job_id
                    or parent_job_id == current_job_id
                )
            ):
                allowed = False
                rejection_reason = "waiting_on_child_current_job_only"
        elif dominant_target_kind == "blocked-evidence-review" and call_type == "failure.report":
            if not (isinstance(current_job_id, str) and job_id == current_job_id):
                allowed = False
                rejection_reason = "blocked_evidence_current_job_only"
        elif dominant_target_kind == "active-item" and call_type in {
            "job.start",
            "child_job.request",
            "result.submit",
            "failure.report",
        }:
            if (
                isinstance(current_job_id, str)
                and isinstance(job_id, str)
                and job_id != current_job_id
            ):
                allowed = False
                rejection_reason = "current_active_leg_mismatch"

        return {
            "task_id": task_id,
            "call_type": call_type,
            "job_id": job_id,
            "allowed": allowed,
            "dominant_target_kind": dominant_target_kind,
            "dominant_blocker_kind": policy.get("dominant_blocker_kind"),
            "execution_allowed": policy.get("execution_allowed", False),
            "execution_held": policy.get("execution_held", False),
            "execution_hold_kind": policy.get("execution_hold_kind"),
            "execution_hold_reason": policy.get("execution_hold_reason"),
            "current_job_id": current_job_id,
            "parent_job_id": parent_job_id,
            "allowed_call_types": allowed_call_types,
            "allowed_call_policy": tuple(policy.get("allowed_call_policy", ())),
            "blocked_call_types": tuple(policy.get("blocked_call_types", ())),
            "blocked_call_policy": tuple(policy.get("blocked_call_policy", ())),
            "best_next_move": policy.get("best_next_move"),
            "posture_effect": self.evaluate_supported_call_posture_effect(
                task_id,
                call_type,
            ),
            "rejection_reason": rejection_reason,
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
        task_policy = self.effective_task_policy_summary(task_id)
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
            "relevant_proof_policy_kind": (
                active_plan_summary.get("relevant_proof_policy_kind")
                if isinstance(active_plan_summary, dict)
                else None
            ),
            "relevant_rule_finality_kind": (
                active_plan_summary.get("relevant_rule_finality_kind")
                if isinstance(active_plan_summary, dict)
                else None
            ),
            "relevant_unmet_requirement_kind": (
                active_plan_summary.get("relevant_unmet_requirement_kind")
                if isinstance(active_plan_summary, dict)
                else None
            ),
            "relevant_unmet_requirement_detail": (
                active_plan_summary.get("relevant_unmet_requirement_detail")
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
            "allowed_call_types": (
                task_policy.get("allowed_call_types")
                if isinstance(task_policy, dict)
                else ()
            ),
            "allowed_call_policy": (
                task_policy.get("allowed_call_policy")
                if isinstance(task_policy, dict)
                else ()
            ),
            "best_next_move": (
                task_policy.get("best_next_move")
                if isinstance(task_policy, dict)
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
                "proof_policy_kind": (
                    relevant_plan_item.get("proof_policy_kind")
                    if isinstance(relevant_plan_item, dict)
                    else None
                ),
                "waiting_on_proof": (
                    relevant_plan_item.get("is_waiting_on_proof")
                    if isinstance(relevant_plan_item, dict)
                    else False
                ),
                "waiting_on_review": (
                    relevant_plan_item.get("is_waiting_on_review")
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
                "proof_policy_kind": (
                    relevant_plan_item.get("proof_policy_kind")
                    if isinstance(relevant_plan_item, dict)
                    else None
                ),
                "waiting_on_proof": (
                    relevant_plan_item.get("is_waiting_on_proof")
                    if isinstance(relevant_plan_item, dict)
                    else False
                ),
                "waiting_on_review": (
                    relevant_plan_item.get("is_waiting_on_review")
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
                "proof_policy_kind": (
                    relevant_plan_item.get("proof_policy_kind")
                    if isinstance(relevant_plan_item, dict)
                    else None
                ),
                "waiting_on_proof": (
                    relevant_plan_item.get("is_waiting_on_proof")
                    if isinstance(relevant_plan_item, dict)
                    else False
                ),
                "waiting_on_review": (
                    relevant_plan_item.get("is_waiting_on_review")
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
        task_record = self.read_task_record(task_id)
        if task_record is None:
            return None
        active_plan_summary = self.read_active_plan_summary(task_id)
        if active_plan_summary is None:
            return None
        current_job_state = None
        current_job_id = task_record.get("current_job_id")
        if isinstance(current_job_id, str):
            current_job_record = self.read_job_record(current_job_id)
            if isinstance(current_job_record, dict):
                current_job_state = current_job_record.get("job_state")
        task_policy = self._build_task_policy_summary(
            task_record=task_record,
            active_plan_summary=active_plan_summary,
            current_active_plan_item=active_plan_summary.get("current_active_item_summary"),
            relevant_plan_item=active_plan_summary.get("relevant_plan_item_summary"),
            current_job_state=current_job_state,
        )
        if not isinstance(task_policy, dict):
            return None
        resume_anchor = self.resolve_task_resume_anchor(task_id)
        next_executable_unavailable_reason = active_plan_summary.get(
            "next_executable_unavailable_reason"
        )
        dominant_target = task_policy.get("dominant_target")
        dominant_target_kind = task_policy.get("dominant_target_kind")
        if isinstance(dominant_target, dict):
            return {
                "task_id": task_id,
                "plan_version": active_plan_summary["plan_version"],
                "target_kind": dominant_target_kind,
                "item": dominant_target.get("item"),
                "job_id": dominant_target.get("job_id"),
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
            "proof_gate_supported": relevant_item.get("proof_gate_supported"),
            "proof_satisfied": relevant_item.get("proof_satisfied"),
            "proof_gate_reason": relevant_item.get("proof_gate_reason"),
            "proof_policy_kind": relevant_item.get("proof_policy_kind"),
            "rule_mechanical": relevant_item.get("rule_mechanical"),
            "rule_finality_kind": relevant_item.get("rule_finality_kind"),
            "unmet_requirement_kind": relevant_item.get("unmet_requirement_kind"),
            "unmet_requirement_detail": relevant_item.get("unmet_requirement_detail"),
            "review_required": relevant_item.get("review_required"),
            "can_be_satisfied_by_supported_evidence_calls": (
                relevant_item.get("can_be_satisfied_by_supported_evidence_calls")
            ),
            "can_only_remain_review_needed": (
                relevant_item.get("can_only_remain_review_needed")
            ),
            "is_verification_pending": relevant_item.get("is_verification_pending"),
            "is_waiting_on_proof": relevant_item.get("is_waiting_on_proof"),
            "is_waiting_on_review": relevant_item.get("is_waiting_on_review"),
            "evidence_refs": relevant_item.get("evidence_refs", ()),
            "evidence_count": relevant_item.get("evidence_count", 0),
        }

    @staticmethod
    def _build_task_policy_summary(
        *,
        task_record: dict[str, Any] | None,
        active_plan_summary: dict[str, Any] | None,
        current_active_plan_item: dict[str, Any] | None,
        relevant_plan_item: dict[str, Any] | None,
        current_job_state: str | None,
    ) -> dict[str, Any] | None:
        if task_record is None:
            return None

        current_job_id = task_record.get("current_job_id")
        next_executable_item = (
            active_plan_summary.get("next_executable_item_summary")
            if isinstance(active_plan_summary, dict)
            else None
        )
        next_executable_unavailable_reason = (
            active_plan_summary.get("next_executable_unavailable_reason")
            if isinstance(active_plan_summary, dict)
            else None
        )
        rule_aware_hint = GarageStorageAdapter._rule_aware_policy_hint(
            relevant_plan_item,
            dominant_target_kind=(
                "review-needed"
                if isinstance(relevant_plan_item, dict) and relevant_plan_item.get("is_waiting_on_review")
                else "proof-gathering"
                if isinstance(relevant_plan_item, dict) and relevant_plan_item.get("is_waiting_on_proof")
                else None
            ),
        )

        dominant_target_kind: str | None = None
        dominant_target: dict[str, Any] | None = None
        dominant_blocker: dict[str, Any] | None = None

        if isinstance(relevant_plan_item, dict) and relevant_plan_item.get("is_blocked"):
            dominant_target_kind = "blocked-evidence-review"
            dominant_target = {"item": relevant_plan_item}
            dominant_blocker = {
                "kind": "blocked-evidence-review",
                "reason": relevant_plan_item.get("advance_blocked_reason") or "blocked_failure_evidence",
                "item_id": relevant_plan_item.get("item_id"),
            }
        elif isinstance(relevant_plan_item, dict) and relevant_plan_item.get("is_waiting_on_review"):
            dominant_target_kind = "review-needed"
            dominant_target = {"item": relevant_plan_item}
            dominant_blocker = {
                "kind": "review-needed",
                "reason": (
                    rule_aware_hint.get("blocked_reason")
                    or relevant_plan_item.get("advance_blocked_reason")
                    or relevant_plan_item.get("proof_gate_reason")
                ),
                "item_id": relevant_plan_item.get("item_id"),
            }
        elif isinstance(relevant_plan_item, dict) and relevant_plan_item.get("is_waiting_on_proof"):
            dominant_target_kind = "proof-gathering"
            dominant_target = {"item": relevant_plan_item}
            dominant_blocker = {
                "kind": "proof-gathering",
                "reason": (
                    rule_aware_hint.get("blocked_reason")
                    or relevant_plan_item.get("advance_blocked_reason")
                    or relevant_plan_item.get("proof_gate_reason")
                ),
                "item_id": relevant_plan_item.get("item_id"),
            }
        elif task_record.get("task_state") == "waiting_on_child":
            dominant_target_kind = "waiting-on-child"
            dominant_target = {
                "item": current_active_plan_item or relevant_plan_item,
                "job_id": current_job_id,
            }
            dominant_blocker = {
                "kind": "waiting-on-child",
                "reason": "child_job_in_flight",
                "job_id": current_job_id,
                "item_id": (
                    (current_active_plan_item or relevant_plan_item).get("item_id")
                    if isinstance(current_active_plan_item or relevant_plan_item, dict)
                    else None
                ),
            }
        elif isinstance(current_active_plan_item, dict) and current_active_plan_item.get("is_active"):
            dominant_target_kind = "active-item"
            dominant_target = {"item": current_active_plan_item, "job_id": current_job_id}
        elif isinstance(next_executable_item, dict):
            dominant_target_kind = "next-executable"
            dominant_target = {"item": next_executable_item}
        else:
            dominant_target_kind = "resume-anchor-only"
            dominant_target = None

        effective_task_posture = "resuming"
        if dominant_target_kind == "blocked-evidence-review":
            effective_task_posture = "blocked-evidence-review"
        elif dominant_target_kind == "review-needed":
            effective_task_posture = "waiting-on-review"
        elif dominant_target_kind == "proof-gathering":
            effective_task_posture = "waiting-on-proof"
        elif dominant_target_kind == "waiting-on-child":
            effective_task_posture = "waiting-on-child"
        elif dominant_target_kind == "active-item":
            effective_task_posture = "running"
        elif dominant_target_kind == "next-executable":
            effective_task_posture = "ready-for-next"

        execution_allowed = dominant_target_kind in {
            "active-item",
            "next-executable",
            "resume-anchor-only",
        }
        execution_held = not execution_allowed
        execution_hold_kind = dominant_target_kind if execution_held else None
        execution_hold_reason = (
            dominant_blocker.get("reason") if isinstance(dominant_blocker, dict) else None
        )
        allowed_call_types = GarageStorageAdapter._allowed_call_types_for_dominant_target(
            dominant_target_kind
        )
        allowed_call_policy = GarageStorageAdapter._allowed_call_policy_for_dominant_target(
            dominant_target_kind=dominant_target_kind,
            dominant_target=dominant_target,
            current_job_state=current_job_state,
            relevant_plan_item=relevant_plan_item,
        )
        blocked_call_types = tuple(
            call_type
            for call_type in SUPPORTED_POLICY_CALL_TYPES
            if call_type not in allowed_call_types
        )
        best_next_move = GarageStorageAdapter._best_next_move_for_policy(
            dominant_target_kind=dominant_target_kind,
            dominant_target=dominant_target,
            current_job_state=current_job_state,
            relevant_plan_item=relevant_plan_item,
        )
        best_next_call_type = (
            best_next_move.get("call_type")
            if isinstance(best_next_move, dict)
            else None
        )
        best_next_move_effect_kind = (
            best_next_move.get("effect_kind")
            if isinstance(best_next_move, dict)
            else None
        )
        secondary_allowed_call_types = tuple(
            call_type
            for call_type in allowed_call_types
            if call_type != best_next_call_type
        )
        blocked_call_reason = execution_hold_reason if execution_held else None
        blocked_call_policy = tuple(
            {
                "call_type": call_type,
                "effect_kind": "blocked",
                "reason": blocked_call_reason or "call_not_allowed_for_current_target",
            }
            for call_type in blocked_call_types
        )

        current_job_is_primary_focus = dominant_target_kind in {"active-item", "waiting-on-child"}
        relevant_plan_item_is_primary_focus = dominant_target_kind in {
            "proof-gathering",
            "review-needed",
            "blocked-evidence-review",
            "next-executable",
        }

        return {
            "dominant_target_kind": dominant_target_kind,
            "dominant_target": dominant_target,
            "dominant_blocker": dominant_blocker,
            "dominant_blocker_kind": (
                dominant_blocker.get("kind") if isinstance(dominant_blocker, dict) else None
            ),
            "dominant_rule_finality_kind": (
                relevant_plan_item.get("rule_finality_kind")
                if isinstance(relevant_plan_item, dict)
                else None
            ),
            "dominant_unmet_requirement_kind": (
                relevant_plan_item.get("unmet_requirement_kind")
                if isinstance(relevant_plan_item, dict)
                else None
            ),
            "dominant_unmet_requirement_detail": (
                relevant_plan_item.get("unmet_requirement_detail")
                if isinstance(relevant_plan_item, dict)
                else None
            ),
            "effective_task_posture": effective_task_posture,
            "execution_allowed": execution_allowed,
            "execution_held": execution_held,
            "execution_hold_kind": execution_hold_kind,
            "execution_hold_reason": execution_hold_reason,
            "execution_hold_detail_kind": (
                relevant_plan_item.get("unmet_requirement_kind")
                if isinstance(relevant_plan_item, dict)
                and dominant_target_kind in {"proof-gathering", "review-needed"}
                else None
            ),
            "execution_hold_detail": (
                relevant_plan_item.get("unmet_requirement_detail")
                if isinstance(relevant_plan_item, dict)
                and dominant_target_kind in {"proof-gathering", "review-needed"}
                else None
            ),
            "allowed_call_types": allowed_call_types,
            "allowed_call_policy": allowed_call_policy,
            "secondary_allowed_call_types": secondary_allowed_call_types,
            "blocked_call_types": blocked_call_types,
            "blocked_call_reason": blocked_call_reason,
            "blocked_call_policy": blocked_call_policy,
            "best_next_move": best_next_move,
            "best_next_call_type": best_next_call_type,
            "best_next_move_effect_kind": best_next_move_effect_kind,
            "effective_waiting_on_proof": dominant_target_kind == "proof-gathering",
            "effective_waiting_on_review": dominant_target_kind == "review-needed",
            "effective_blocked_evidence_review": dominant_target_kind == "blocked-evidence-review",
            "effective_waiting_on_child": dominant_target_kind == "waiting-on-child",
            "effective_running": dominant_target_kind == "active-item",
            "effective_ready_for_next": dominant_target_kind == "next-executable",
            "current_job_is_primary_focus": current_job_is_primary_focus,
            "relevant_plan_item_is_primary_focus": relevant_plan_item_is_primary_focus,
            "next_executable_unavailable_reason": next_executable_unavailable_reason,
        }

    @staticmethod
    def _allowed_call_types_for_dominant_target(
        dominant_target_kind: str | None,
    ) -> tuple[str, ...]:
        if dominant_target_kind == "proof-gathering":
            return ("checkpoint.create", "continuation.record")
        if dominant_target_kind == "review-needed":
            return ("checkpoint.create", "continuation.record")
        if dominant_target_kind == "blocked-evidence-review":
            return ("failure.report", "checkpoint.create", "continuation.record")
        if dominant_target_kind == "waiting-on-child":
            return (
                "job.start",
                "child_job.request",
                "result.submit",
                "failure.report",
                "checkpoint.create",
                "continuation.record",
            )
        if dominant_target_kind == "active-item":
            return (
                "job.start",
                "child_job.request",
                "result.submit",
                "failure.report",
                "checkpoint.create",
                "continuation.record",
            )
        if dominant_target_kind in {"next-executable", "resume-anchor-only", None}:
            return (
                "job.start",
                "child_job.request",
                "result.submit",
                "failure.report",
                "checkpoint.create",
                "continuation.record",
            )
        return ("checkpoint.create", "continuation.record")

    @staticmethod
    def _rule_aware_policy_hint(
        relevant_plan_item: dict[str, Any] | None,
        *,
        dominant_target_kind: str | None,
    ) -> dict[str, Any]:
        if not isinstance(relevant_plan_item, dict):
            return {
                "move_kind": None,
                "call_type": None,
                "reason": None,
                "effect_kind": None,
                "blocked_reason": None,
            }

        unmet_kind = relevant_plan_item.get("unmet_requirement_kind")
        unmet_detail = (
            relevant_plan_item.get("unmet_requirement_detail")
            if isinstance(relevant_plan_item.get("unmet_requirement_detail"), dict)
            else {}
        )
        finality_kind = relevant_plan_item.get("rule_finality_kind")

        if dominant_target_kind == "proof-gathering":
            if unmet_kind == "missing_artifact_ref":
                return {
                    "move_kind": "attach-artifact-ref",
                    "call_type": "continuation.record",
                    "reason": "current item still needs an official artifact ref before verification",
                    "effect_kind": "preserve_or_resolve",
                    "blocked_reason": "missing_artifact_ref",
                }
            if unmet_kind == "missing_required_artifact_kind":
                required_kind = unmet_detail.get("required_kind")
                observed_kinds = tuple(unmet_detail.get("observed_artifact_kinds", ()))
                return {
                    "move_kind": "attach-required-artifact-kind",
                    "call_type": "continuation.record",
                    "reason": (
                        f"current item still needs artifact kind '{required_kind}'"
                        + (
                            f"; observed kinds: {', '.join(observed_kinds)}"
                            if observed_kinds
                            else ""
                        )
                    ),
                    "effect_kind": "preserve_or_resolve",
                    "blocked_reason": "missing_required_artifact_kind",
                }
            if unmet_kind == "missing_result_evidence":
                return {
                    "move_kind": "attach-result-evidence",
                    "call_type": "continuation.record",
                    "reason": "current item still needs result-json evidence before verification",
                    "effect_kind": "preserve_or_resolve",
                    "blocked_reason": "missing_result_evidence",
                }
            if unmet_kind == "missing_summary_evidence":
                return {
                    "move_kind": "attach-summary-evidence",
                    "call_type": "continuation.record",
                    "reason": "current item still needs summary evidence before verification",
                    "effect_kind": "preserve_or_resolve",
                    "blocked_reason": "missing_summary_evidence",
                }
            if unmet_kind == "insufficient_evidence_bundle":
                required_count = unmet_detail.get("required_minimum_count")
                current_count = unmet_detail.get("current_evidence_count")
                return {
                    "move_kind": "complete-evidence-bundle",
                    "call_type": "continuation.record",
                    "reason": (
                        f"current item needs a larger evidence bundle"
                        + (
                            f" ({current_count}/{required_count} refs present)"
                            if required_count is not None and current_count is not None
                            else ""
                        )
                    ),
                    "effect_kind": "preserve_or_resolve",
                    "blocked_reason": "insufficient_evidence_bundle",
                }
            return {
                "move_kind": "gather-proof",
                "call_type": "continuation.record",
                "reason": "current item still needs more proof before advancement",
                "effect_kind": "preserve_or_resolve",
                "blocked_reason": relevant_plan_item.get("proof_gate_reason"),
            }

        if dominant_target_kind == "review-needed":
            if unmet_kind == "manual_review_required":
                return {
                    "move_kind": "capture-manual-review-context",
                    "call_type": "continuation.record",
                    "reason": "current item explicitly requires manual review",
                    "effect_kind": "preserve",
                    "blocked_reason": "manual_review_required",
                }
            if unmet_kind == "downstream_item_confirms":
                return {
                    "move_kind": "capture-downstream-confirmation-context",
                    "call_type": "continuation.record",
                    "reason": "current item requires downstream confirmation outside this slice",
                    "effect_kind": "preserve",
                    "blocked_reason": "downstream_item_confirms",
                }
            if finality_kind == "unsupported-in-slice":
                return {
                    "move_kind": "capture-unsupported-rule-context",
                    "call_type": "continuation.record",
                    "reason": "current item uses a verification rule Alfred cannot satisfy in this slice",
                    "effect_kind": "preserve",
                    "blocked_reason": unmet_kind or "unsupported_verification_rule",
                }
            if finality_kind == "ill-defined":
                return {
                    "move_kind": "capture-rule-definition-context",
                    "call_type": "continuation.record",
                    "reason": "current item has an ill-defined verification rule; evidence alone cannot resolve it",
                    "effect_kind": "preserve",
                    "blocked_reason": unmet_kind or "ill_defined_verification_rule",
                }
            return {
                "move_kind": "capture-review-context",
                "call_type": "continuation.record",
                "reason": "current item requires review outside this supported mechanical slice",
                "effect_kind": "preserve",
                "blocked_reason": relevant_plan_item.get("proof_gate_reason"),
            }

        return {
            "move_kind": None,
            "call_type": None,
            "reason": None,
            "effect_kind": None,
            "blocked_reason": None,
        }

    @staticmethod
    def _allowed_call_policy_for_dominant_target(
        *,
        dominant_target_kind: str | None,
        dominant_target: dict[str, Any] | None,
        current_job_state: str | None,
        relevant_plan_item: dict[str, Any] | None,
    ) -> tuple[dict[str, Any], ...]:
        if dominant_target_kind == "proof-gathering":
            guidance = GarageStorageAdapter._rule_aware_policy_hint(
                relevant_plan_item,
                dominant_target_kind=dominant_target_kind,
            )
            reason = guidance["reason"] or "can enrich evidence; resolves only if the proof gate becomes satisfied"
            return (
                {
                    "call_type": "checkpoint.create",
                    "effect_kind": guidance["effect_kind"] or "preserve_or_resolve",
                    "reason": reason,
                    "target": dominant_target,
                },
                {
                    "call_type": "continuation.record",
                    "effect_kind": guidance["effect_kind"] or "preserve_or_resolve",
                    "reason": reason,
                    "target": dominant_target,
                },
            )
        if dominant_target_kind == "review-needed":
            guidance = GarageStorageAdapter._rule_aware_policy_hint(
                relevant_plan_item,
                dominant_target_kind=dominant_target_kind,
            )
            reason = guidance["reason"] or (
                "can capture more evidence or resume context but cannot resolve manual or unsupported review"
            )
            return (
                {
                    "call_type": "checkpoint.create",
                    "effect_kind": guidance["effect_kind"] or "preserve",
                    "reason": reason,
                    "target": dominant_target,
                },
                {
                    "call_type": "continuation.record",
                    "effect_kind": guidance["effect_kind"] or "preserve",
                    "reason": reason,
                    "target": dominant_target,
                },
            )
        if dominant_target_kind == "blocked-evidence-review":
            return (
                {
                    "call_type": "failure.report",
                    "effect_kind": "refine",
                    "reason": "can enrich blocked evidence context while blocked posture remains",
                    "target": dominant_target,
                },
                {
                    "call_type": "checkpoint.create",
                    "effect_kind": "preserve",
                    "reason": "captures blocked evidence context without unblocking the item",
                    "target": dominant_target,
                },
                {
                    "call_type": "continuation.record",
                    "effect_kind": "preserve",
                    "reason": "captures blocked resume context without unblocking the item",
                    "target": dominant_target,
                },
            )
        if dominant_target_kind == "waiting-on-child":
            child_progress_reason = "current child leg remains the dominant dependency"
            if current_job_state in {"queued", "dispatched"}:
                child_progress_reason = "starts the current child leg while child-held posture remains"
            return (
                {
                    "call_type": "job.start",
                    "effect_kind": "preserve",
                    "reason": child_progress_reason,
                    "target": dominant_target,
                },
                {
                    "call_type": "child_job.request",
                    "effect_kind": "refine",
                    "reason": "extends child-job lineage while the task remains child-held",
                    "target": dominant_target,
                },
                {
                    "call_type": "result.submit",
                    "effect_kind": "resolve",
                    "reason": "child-leg return can release child-held posture into proof, review, or next execution",
                    "target": dominant_target,
                },
                {
                    "call_type": "failure.report",
                    "effect_kind": "resolve",
                    "reason": "child-leg failure can shift posture into blocked-evidence review",
                    "target": dominant_target,
                },
                {
                    "call_type": "checkpoint.create",
                    "effect_kind": "preserve",
                    "reason": "captures child-held evidence without releasing the child dependency",
                    "target": dominant_target,
                },
                {
                    "call_type": "continuation.record",
                    "effect_kind": "preserve",
                    "reason": "captures child-held resume context without releasing the child dependency",
                    "target": dominant_target,
                },
            )
        if dominant_target_kind == "active-item":
            return (
                {
                    "call_type": "job.start",
                    "effect_kind": "preserve",
                    "reason": "continues the current active execution leg",
                    "target": dominant_target,
                },
                {
                    "call_type": "child_job.request",
                    "effect_kind": "resolve",
                    "reason": "hands the current active item into child-held posture",
                    "target": dominant_target,
                },
                {
                    "call_type": "result.submit",
                    "effect_kind": "resolve",
                    "reason": "completes or returns the current active item into its next policy posture",
                    "target": dominant_target,
                },
                {
                    "call_type": "failure.report",
                    "effect_kind": "resolve",
                    "reason": "moves the current active item into blocked evidence posture",
                    "target": dominant_target,
                },
                {
                    "call_type": "checkpoint.create",
                    "effect_kind": "preserve",
                    "reason": "captures running-state context without changing the active posture",
                    "target": dominant_target,
                },
                {
                    "call_type": "continuation.record",
                    "effect_kind": "preserve",
                    "reason": "captures running-state resume context without changing the active posture",
                    "target": dominant_target,
                },
            )
        if dominant_target_kind == "next-executable":
            return (
                {
                    "call_type": "job.start",
                    "effect_kind": "resolve",
                    "reason": "begins the next executable item and makes active execution dominant",
                    "target": dominant_target,
                },
                {
                    "call_type": "child_job.request",
                    "effect_kind": "resolve",
                    "reason": "delegates the next executable item into child-held posture",
                    "target": dominant_target,
                },
                {
                    "call_type": "result.submit",
                    "effect_kind": "refine",
                    "reason": "can update residual execution state but does not define the ready successor by itself",
                    "target": dominant_target,
                },
                {
                    "call_type": "failure.report",
                    "effect_kind": "refine",
                    "reason": "can update residual blocked state but does not define the ready successor by itself",
                    "target": dominant_target,
                },
                {
                    "call_type": "checkpoint.create",
                    "effect_kind": "preserve",
                    "reason": "captures resume context while the task remains ready for next execution",
                    "target": dominant_target,
                },
                {
                    "call_type": "continuation.record",
                    "effect_kind": "preserve",
                    "reason": "captures resume context while the task remains ready for next execution",
                    "target": dominant_target,
                },
            )
        if dominant_target_kind == "resume-anchor-only":
            return (
                {
                    "call_type": "job.start",
                    "effect_kind": "refine",
                    "reason": "can restart execution from the available resume context",
                    "target": dominant_target,
                },
                {
                    "call_type": "child_job.request",
                    "effect_kind": "refine",
                    "reason": "can delegate resumed execution into a child leg from the available context",
                    "target": dominant_target,
                },
                {
                    "call_type": "result.submit",
                    "effect_kind": "refine",
                    "reason": "can update resumed execution state from the available context",
                    "target": dominant_target,
                },
                {
                    "call_type": "failure.report",
                    "effect_kind": "refine",
                    "reason": "can update resumed blocked state from the available context",
                    "target": dominant_target,
                },
                {
                    "call_type": "checkpoint.create",
                    "effect_kind": "preserve",
                    "reason": "refreshes checkpoint context without establishing a stronger execution posture",
                    "target": dominant_target,
                },
                {
                    "call_type": "continuation.record",
                    "effect_kind": "preserve",
                    "reason": "refreshes continuation context without establishing a stronger execution posture",
                    "target": dominant_target,
                },
            )
        return ()

    @staticmethod
    def _best_next_move_for_policy(
        *,
        dominant_target_kind: str | None,
        dominant_target: dict[str, Any] | None,
        current_job_state: str | None,
        relevant_plan_item: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if dominant_target_kind == "proof-gathering":
            guidance = GarageStorageAdapter._rule_aware_policy_hint(
                relevant_plan_item,
                dominant_target_kind=dominant_target_kind,
            )
            return {
                "move_kind": guidance["move_kind"] or "gather-proof",
                "call_type": guidance["call_type"] or "continuation.record",
                "reason": guidance["reason"] or "current item still needs evidence before advancement",
                "effect_kind": guidance["effect_kind"] or "preserve_or_resolve",
                "target": dominant_target,
            }
        if dominant_target_kind == "review-needed":
            guidance = GarageStorageAdapter._rule_aware_policy_hint(
                relevant_plan_item,
                dominant_target_kind=dominant_target_kind,
            )
            return {
                "move_kind": guidance["move_kind"] or "capture-review-context",
                "call_type": guidance["call_type"] or "continuation.record",
                "reason": guidance["reason"] or "current item requires manual or unsupported review",
                "effect_kind": guidance["effect_kind"] or "preserve",
                "target": dominant_target,
            }
        if dominant_target_kind == "blocked-evidence-review":
            return {
                "move_kind": "capture-blocked-evidence",
                "call_type": "continuation.record",
                "reason": "blocked item evidence should remain the current focus",
                "effect_kind": "preserve",
                "target": dominant_target,
            }
        if dominant_target_kind == "waiting-on-child":
            if current_job_state in {"queued", "dispatched"}:
                call_type = "job.start"
                reason = "current child leg is ready to begin"
            else:
                call_type = None
                reason = "current child leg is already in progress or awaiting return"
            return {
                "move_kind": "progress-child-leg",
                "call_type": call_type,
                "reason": reason,
                "effect_kind": "preserve",
                "target": dominant_target,
            }
        if dominant_target_kind == "active-item":
            return {
                "move_kind": "continue-active-execution",
                "call_type": None,
                "reason": "current execution leg remains the primary focus",
                "effect_kind": "preserve",
                "target": dominant_target,
            }
        if dominant_target_kind == "next-executable":
            return {
                "move_kind": "start-next-executable",
                "call_type": "job.start",
                "reason": "a dependency-cleared plan item is ready to run",
                "effect_kind": "resolve",
                "target": dominant_target,
            }
        if dominant_target_kind == "resume-anchor-only":
            return {
                "move_kind": "refresh-resume-context",
                "call_type": "continuation.record",
                "reason": "resume context exists but no stronger execution target is available",
                "effect_kind": "preserve",
                "target": None,
            }
        return None

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
                        "blocking_policy_kind": dependency.get("proof_policy_kind"),
                        "blocking_waiting_on_proof": dependency.get("is_waiting_on_proof"),
                        "blocking_waiting_on_review": dependency.get("is_waiting_on_review"),
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
                "reason": (
                    "review_required"
                    if relevant_item.get("is_waiting_on_review")
                    else "proof_gathering_required"
                ),
                "blocking_item_id": relevant_item["item_id"],
                "verification_rule_type": relevant_item.get("verification_rule_type"),
                "proof_gate_reason": relevant_item.get("proof_gate_reason"),
                "proof_policy_kind": relevant_item.get("proof_policy_kind"),
                "rule_finality_kind": relevant_item.get("rule_finality_kind"),
                "unmet_requirement_kind": relevant_item.get("unmet_requirement_kind"),
                "unmet_requirement_detail": relevant_item.get("unmet_requirement_detail"),
                "can_be_satisfied_by_supported_evidence_calls": (
                    relevant_item.get("can_be_satisfied_by_supported_evidence_calls")
                ),
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
                "mechanical": False,
                "satisfied": False,
                "reason": "no_verification_rule",
                "finality_kind": "ill-defined",
                "unmet_requirement_kind": "no_verification_rule",
                "unmet_requirement_detail": {
                    "expected_field": "verification_rule",
                },
                "review_required": False,
                "can_be_satisfied_by_supported_evidence_calls": False,
                "can_only_remain_review_needed": True,
            }

        rule_type = verification_rule.get("type")
        if not isinstance(rule_type, str):
            return {
                "rule_type": None,
                "supported": False,
                "mechanical": False,
                "satisfied": False,
                "reason": "no_verification_rule_type",
                "finality_kind": "ill-defined",
                "unmet_requirement_kind": "no_verification_rule_type",
                "unmet_requirement_detail": {
                    "expected_field": "verification_rule.type",
                },
                "review_required": False,
                "can_be_satisfied_by_supported_evidence_calls": False,
                "can_only_remain_review_needed": True,
            }

        evidence_refs = [ref for ref in item.get("evidence_refs", []) if isinstance(ref, dict)]
        artifact_refs = [ref for ref in evidence_refs if "artifact_id" in ref]
        evidence_kinds = tuple(
            str(ref.get("kind"))
            for ref in evidence_refs
            if isinstance(ref.get("kind"), str)
        )
        artifact_kinds = tuple(
            str(ref.get("kind"))
            for ref in artifact_refs
            if isinstance(ref.get("kind"), str)
        )
        params = verification_rule.get("params") if isinstance(verification_rule.get("params"), dict) else {}

        if rule_type not in MECHANICAL_PROOF_RULE_TYPES:
            reason = "unsupported_verification_rule"
            finality_kind = "unsupported-in-slice"
            review_required = False
            if rule_type == "manual_review_required":
                reason = "manual_review_required"
                finality_kind = "review-required"
                review_required = True
            elif rule_type == "downstream_item_confirms":
                reason = "downstream_item_confirms"
                finality_kind = "review-required"
                review_required = True
            elif rule_type == "test_pass":
                reason = "test_pass_not_mechanically_supported"
                finality_kind = "unsupported-in-slice"
            return {
                "rule_type": rule_type,
                "supported": False,
                "mechanical": False,
                "satisfied": False,
                "reason": reason,
                "finality_kind": finality_kind,
                "unmet_requirement_kind": reason,
                "unmet_requirement_detail": {
                    "rule_type": rule_type,
                },
                "review_required": review_required,
                "can_be_satisfied_by_supported_evidence_calls": False,
                "can_only_remain_review_needed": True,
            }

        if rule_type == "no_extra_requirement":
            return {
                "rule_type": rule_type,
                "supported": True,
                "mechanical": True,
                "satisfied": True,
                "reason": None,
                "finality_kind": "satisfied",
                "unmet_requirement_kind": None,
                "unmet_requirement_detail": None,
                "review_required": False,
                "can_be_satisfied_by_supported_evidence_calls": False,
                "can_only_remain_review_needed": False,
            }
        if rule_type == "artifact_exists":
            satisfied = bool(artifact_refs)
            return {
                "rule_type": rule_type,
                "supported": True,
                "mechanical": True,
                "satisfied": satisfied,
                "reason": None if satisfied else "missing_artifact_ref",
                "finality_kind": "satisfied" if satisfied else "mechanically-satisfiable-later",
                "unmet_requirement_kind": None if satisfied else "missing_artifact_ref",
                "unmet_requirement_detail": None
                if satisfied
                else {
                    "required_artifact_count": 1,
                    "current_artifact_count": len(artifact_refs),
                    "observed_artifact_kinds": artifact_kinds,
                },
                "review_required": False,
                "can_be_satisfied_by_supported_evidence_calls": not satisfied,
                "can_only_remain_review_needed": False,
            }
        if rule_type == "artifact_matches_kind":
            required_kind = params.get("kind")
            if not isinstance(required_kind, str) or not required_kind:
                return {
                    "rule_type": rule_type,
                    "supported": False,
                    "mechanical": False,
                    "satisfied": False,
                    "reason": "missing_required_kind_param",
                    "finality_kind": "ill-defined",
                    "unmet_requirement_kind": "missing_required_kind_param",
                    "unmet_requirement_detail": {
                        "required_param": "params.kind",
                    },
                    "review_required": False,
                    "can_be_satisfied_by_supported_evidence_calls": False,
                    "can_only_remain_review_needed": True,
                }
            satisfied = any(ref.get("kind") == required_kind for ref in artifact_refs)
            return {
                "rule_type": rule_type,
                "supported": True,
                "mechanical": True,
                "satisfied": satisfied,
                "reason": None if satisfied else "missing_required_artifact_kind",
                "finality_kind": "satisfied" if satisfied else "mechanically-satisfiable-later",
                "unmet_requirement_kind": None if satisfied else "missing_required_artifact_kind",
                "unmet_requirement_detail": None
                if satisfied
                else {
                    "required_kind": required_kind,
                    "observed_artifact_kinds": artifact_kinds,
                    "current_artifact_count": len(artifact_refs),
                },
                "review_required": False,
                "can_be_satisfied_by_supported_evidence_calls": not satisfied,
                "can_only_remain_review_needed": False,
            }
        if rule_type == "result_present":
            satisfied = any(ref.get("kind") == "result-json" for ref in evidence_refs)
            return {
                "rule_type": rule_type,
                "supported": True,
                "mechanical": True,
                "satisfied": satisfied,
                "reason": None if satisfied else "missing_result_evidence",
                "finality_kind": "satisfied" if satisfied else "mechanically-satisfiable-later",
                "unmet_requirement_kind": None if satisfied else "missing_result_evidence",
                "unmet_requirement_detail": None
                if satisfied
                else {
                    "required_evidence_kind": "result-json",
                    "observed_evidence_kinds": evidence_kinds,
                },
                "review_required": False,
                "can_be_satisfied_by_supported_evidence_calls": not satisfied,
                "can_only_remain_review_needed": False,
            }
        if rule_type == "summary_present":
            satisfied = any(ref.get("kind") == "summary" for ref in evidence_refs)
            return {
                "rule_type": rule_type,
                "supported": True,
                "mechanical": True,
                "satisfied": satisfied,
                "reason": None if satisfied else "missing_summary_evidence",
                "finality_kind": "satisfied" if satisfied else "mechanically-satisfiable-later",
                "unmet_requirement_kind": None if satisfied else "missing_summary_evidence",
                "unmet_requirement_detail": None
                if satisfied
                else {
                    "required_evidence_kind": "summary",
                    "observed_evidence_kinds": evidence_kinds,
                },
                "review_required": False,
                "can_be_satisfied_by_supported_evidence_calls": not satisfied,
                "can_only_remain_review_needed": False,
            }
        minimum_count = params.get("minimum_count", params.get("min_count", 2))
        try:
            minimum_count = int(minimum_count)
        except (TypeError, ValueError):
            return {
                "rule_type": rule_type,
                "supported": False,
                "mechanical": False,
                "satisfied": False,
                "reason": "invalid_minimum_count_param",
                "finality_kind": "ill-defined",
                "unmet_requirement_kind": "invalid_minimum_count_param",
                "unmet_requirement_detail": {
                    "provided_minimum_count": params.get("minimum_count", params.get("min_count")),
                },
                "review_required": False,
                "can_be_satisfied_by_supported_evidence_calls": False,
                "can_only_remain_review_needed": True,
            }
        satisfied = len(evidence_refs) >= max(1, minimum_count)
        return {
            "rule_type": rule_type,
            "supported": True,
            "mechanical": True,
            "satisfied": satisfied,
            "reason": None if satisfied else "insufficient_evidence_bundle",
            "finality_kind": "satisfied" if satisfied else "mechanically-satisfiable-later",
            "unmet_requirement_kind": None if satisfied else "insufficient_evidence_bundle",
            "unmet_requirement_detail": None
            if satisfied
            else {
                "required_minimum_count": max(1, minimum_count),
                "current_evidence_count": len(evidence_refs),
                "observed_evidence_kinds": evidence_kinds,
            },
            "review_required": False,
            "can_be_satisfied_by_supported_evidence_calls": not satisfied,
            "can_only_remain_review_needed": False,
        }

    @staticmethod
    def _proof_policy_summary(
        *,
        status: str,
        proof_gate: dict[str, Any],
    ) -> dict[str, Any]:
        if status == "blocked":
            return {
                "policy_kind": "blocked-evidence-review",
                "waiting_on_proof": False,
                "waiting_on_review": False,
                "advance_blocked": True,
                "advance_blocked_reason": "blocked_failure_evidence",
            }
        if status == "verified":
            return {
                "policy_kind": "verified",
                "waiting_on_proof": False,
                "waiting_on_review": False,
                "advance_blocked": False,
                "advance_blocked_reason": None,
            }
        if status != "done_unverified":
            return {
                "policy_kind": "not_applicable",
                "waiting_on_proof": False,
                "waiting_on_review": False,
                "advance_blocked": False,
                "advance_blocked_reason": None,
            }
        if proof_gate["satisfied"]:
            return {
                "policy_kind": "mechanically-satisfied",
                "waiting_on_proof": False,
                "waiting_on_review": False,
                "advance_blocked": False,
                "advance_blocked_reason": None,
            }
        if proof_gate["can_only_remain_review_needed"]:
            return {
                "policy_kind": "review-needed",
                "waiting_on_proof": False,
                "waiting_on_review": True,
                "advance_blocked": True,
                "advance_blocked_reason": proof_gate["reason"],
            }
        return {
            "policy_kind": "proof-gathering",
            "waiting_on_proof": True,
            "waiting_on_review": False,
            "advance_blocked": True,
            "advance_blocked_reason": proof_gate["reason"],
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
        proof_policy = GarageStorageAdapter._proof_policy_summary(
            status=status,
            proof_gate=proof_gate,
        )
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
            "rule_mechanical": proof_gate["mechanical"],
            "rule_finality_kind": proof_gate["finality_kind"],
            "unmet_requirement_kind": proof_gate["unmet_requirement_kind"],
            "unmet_requirement_detail": proof_gate["unmet_requirement_detail"],
            "review_required": proof_gate["review_required"],
            "can_be_satisfied_by_supported_evidence_calls": (
                proof_gate["can_be_satisfied_by_supported_evidence_calls"]
            ),
            "can_only_remain_review_needed": proof_gate["can_only_remain_review_needed"],
            "is_verification_pending": status == "done_unverified" and not proof_gate["satisfied"],
            "proof_policy_kind": proof_policy["policy_kind"],
            "is_waiting_on_proof": proof_policy["waiting_on_proof"],
            "is_waiting_on_review": proof_policy["waiting_on_review"],
            "advance_blocked_by_proof_policy": proof_policy["advance_blocked"],
            "advance_blocked_reason": proof_policy["advance_blocked_reason"],
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
