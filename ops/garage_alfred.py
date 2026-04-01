#!/usr/bin/env python3
"""First narrow Alfred-style processor on top of the validated Garage runtime."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from typing import Any, Callable, Protocol

from ops.garage_boundaries import validate_inbound_garage_call
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

    def evaluate_supported_call_policy(
        self,
        task_id: str,
        call_type: str,
        *,
        job_id: str | None = None,
        parent_job_id: str | None = None,
    ) -> dict[str, Any] | None: ...

    def latest_task_state_summary(self, task_id: str) -> dict[str, Any] | None: ...

    def summarize_applied_call_posture_transition(
        self,
        task_id: str,
        call_type: str,
        *,
        before_task_summary: dict[str, Any] | None,
    ) -> dict[str, Any] | None: ...

    def summarize_next_call_draft_readiness(
        self,
        task_id: str,
        supplied_fields: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None: ...

    def summarize_next_call_preflight(
        self,
        task_id: str,
        supplied_fields: dict[str, Any] | None = None,
        *,
        default_reported_at: str | None = None,
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

        validated_call = validate_inbound_garage_call(data)
        self._enforce_supported_call_policy(validated_call)
        before_task_summary = self._read_pre_call_task_summary(validated_call)
        runtime_result = self._runtime.process_call(validated_call)
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
        enriched_result = self._enrich_post_call_result(
            validated_call=validated_call,
            result=bundle.result,
            before_task_summary=before_task_summary,
        )
        return GarageProcessingResult(
            call_type=bundle.call_type,
            result=enriched_result,
            recorded_events=recorded_events,
            written_records=written_records,
        )

    def _read_pre_call_task_summary(
        self,
        call: dict[str, Any],
    ) -> dict[str, Any] | None:
        if self._bundle_applier is None or self._state_reader is None:
            return None
        reader = getattr(self._state_reader, "latest_task_state_summary", None)
        if not callable(reader):
            return None
        task_id = call.get("task_id")
        if not isinstance(task_id, str):
            return None
        summary = reader(task_id)
        return dict(summary) if isinstance(summary, dict) else None

    def _enrich_post_call_result(
        self,
        *,
        validated_call: dict[str, Any],
        result: Any,
        before_task_summary: dict[str, Any] | None,
    ) -> Any:
        guidance = self._build_post_call_guidance(
            validated_call=validated_call,
            before_task_summary=before_task_summary,
            result=result,
        )
        if not isinstance(guidance, dict):
            return result
        if isinstance(result, dict):
            enriched = dict(result)
            enriched["post_call_guidance"] = guidance
            return enriched
        return {
            "result": result,
            "post_call_guidance": guidance,
        }

    def _build_post_call_guidance(
        self,
        *,
        validated_call: dict[str, Any],
        before_task_summary: dict[str, Any] | None,
        result: Any,
    ) -> dict[str, Any] | None:
        if self._state_reader is None:
            return None
        task_summary_reader = getattr(self._state_reader, "latest_task_state_summary", None)
        if not callable(task_summary_reader):
            return None
        task_id = self._resolve_result_task_id(validated_call, result)
        if not isinstance(task_id, str):
            return None
        refreshed_task_summary = task_summary_reader(task_id)
        if not isinstance(refreshed_task_summary, dict):
            return None
        transition_reader = getattr(
            self._state_reader, "summarize_applied_call_posture_transition", None
        )
        posture_transition = None
        if callable(transition_reader):
            posture_transition = transition_reader(
                task_id,
                str(validated_call["call_type"]),
                before_task_summary=before_task_summary,
            )
        effective_task_policy = refreshed_task_summary.get("effective_task_policy")
        immediate_follow_up = refreshed_task_summary.get("immediate_follow_up_behavior")
        next_call_hint = refreshed_task_summary.get("next_call_hint")
        next_call_draft = refreshed_task_summary.get("next_call_draft")
        next_call_draft_readiness = refreshed_task_summary.get("next_call_draft_readiness")
        preflight_reader = getattr(self._state_reader, "summarize_next_call_preflight", None)
        next_call_preflight = None
        if callable(preflight_reader):
            next_call_preflight = preflight_reader(
                task_id,
                default_reported_at=self._now(),
            )
        return {
            "task_id": task_id,
            "posture_transition": posture_transition,
            "refreshed_task_policy": effective_task_policy,
            "dominant_target_kind": refreshed_task_summary.get("dominant_target_kind"),
            "dominant_blocker_kind": refreshed_task_summary.get("dominant_blocker_kind"),
            "best_next_move": refreshed_task_summary.get("best_next_move"),
            "immediate_follow_up": immediate_follow_up,
            "next_call_hint": next_call_hint,
            "next_call_draft": next_call_draft,
            "next_call_draft_readiness": next_call_draft_readiness,
            "next_call_preflight": next_call_preflight,
            "execution_allowed": refreshed_task_summary.get("execution_allowed"),
            "execution_held": refreshed_task_summary.get("execution_held"),
            "execution_hold_kind": refreshed_task_summary.get("execution_hold_kind"),
            "current_job_is_primary_focus": refreshed_task_summary.get(
                "current_job_is_primary_focus"
            ),
            "relevant_plan_item_is_primary_focus": refreshed_task_summary.get(
                "relevant_plan_item_is_primary_focus"
            ),
        }

    def summarize_next_call_draft_readiness(
        self,
        task_id: str,
        supplied_fields: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        if self._state_reader is None:
            return None
        reader = getattr(self._state_reader, "summarize_next_call_draft_readiness", None)
        if not callable(reader):
            return None
        readiness = reader(task_id, supplied_fields=supplied_fields)
        return dict(readiness) if isinstance(readiness, dict) else None

    def prepare_next_call_from_draft(
        self,
        task_id: str,
        supplied_fields: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        if self._state_reader is None:
            return None
        reader = getattr(self._state_reader, "summarize_next_call_preflight", None)
        if not callable(reader):
            return None
        preflight = reader(
            task_id,
            supplied_fields=supplied_fields,
            default_reported_at=self._now(),
        )
        return dict(preflight) if isinstance(preflight, dict) else None

    def submit_prepared_next_call(
        self,
        *,
        task_id: str | None = None,
        prepared_call: dict[str, Any] | None = None,
        supplied_fields: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        resolved_task_id = self._resolve_submit_task_id(task_id, prepared_call)
        if not isinstance(resolved_task_id, str):
            return self._attach_submit_receipt(
                task_id=None,
                decision={
                "decision_kind": "unavailable_in_slice",
                "allowed_to_submit": False,
                "submission_mode": None,
                "reason": "task_id is required to re-check a prepared next call",
                "prepared_call": None,
                "submit_result": None,
                "fresh_preflight": None,
                "stale_or_blocked": False,
                "missing_required_fields": (),
                "context_only": False,
                "unavailable_in_slice": True,
                "productive_in_slice": False,
                },
                fresh_preflight=None,
                submit_result=None,
            )

        effective_supplied_fields = self._effective_submit_supplied_fields(
            resolved_task_id,
            prepared_call=prepared_call,
            supplied_fields=supplied_fields,
        )
        fresh_preflight = self.prepare_next_call_from_draft(
            resolved_task_id,
            supplied_fields=effective_supplied_fields,
        )
        if not isinstance(fresh_preflight, dict):
            return self._attach_submit_receipt(
                task_id=resolved_task_id,
                decision={
                "decision_kind": "unavailable_in_slice",
                "allowed_to_submit": False,
                "submission_mode": None,
                "reason": "fresh next-call preflight is unavailable for the current task state",
                "prepared_call": None,
                "submit_result": None,
                "fresh_preflight": None,
                "stale_or_blocked": False,
                "missing_required_fields": (),
                "context_only": False,
                "unavailable_in_slice": True,
                "productive_in_slice": False,
                },
                fresh_preflight=None,
                submit_result=None,
            )

        fresh_prepared_call = fresh_preflight.get("prepared_call")
        requested_matches_fresh = self._requested_prepared_call_matches_fresh(
            prepared_call=prepared_call,
            fresh_prepared_call=fresh_prepared_call,
        )
        if prepared_call is not None and not requested_matches_fresh:
            return self._attach_submit_receipt(
                task_id=resolved_task_id,
                decision=self._build_submit_prepared_call_decision(
                    decision_kind="stale_prepared_call",
                    allowed_to_submit=False,
                    submission_mode=self._resolve_submission_mode(fresh_preflight),
                    reason=(
                        "prepared next call no longer matches fresh current-state preflight "
                        "and must be regenerated before submission"
                    ),
                    fresh_preflight=fresh_preflight,
                    submit_result=None,
                    stale_or_blocked=True,
                ),
                fresh_preflight=fresh_preflight,
                submit_result=None,
            )

        preflight_kind = str(fresh_preflight.get("preflight_kind") or "unavailable_in_slice")
        missing_required_fields = tuple(fresh_preflight.get("missing_required_fields") or ())
        submission_mode = self._resolve_submission_mode(fresh_preflight)

        if missing_required_fields:
            return self._attach_submit_receipt(
                task_id=resolved_task_id,
                decision=self._build_submit_prepared_call_decision(
                    decision_kind="not_ready_missing_fields",
                    allowed_to_submit=False,
                    submission_mode=submission_mode,
                    reason=str(
                        fresh_preflight.get("reason")
                        or "prepared next call is still missing required fields"
                    ),
                    fresh_preflight=fresh_preflight,
                    submit_result=None,
                    stale_or_blocked=False,
                ),
                fresh_preflight=fresh_preflight,
                submit_result=None,
            )

        if preflight_kind != "ready_to_submit":
            if (
                preflight_kind == "context_only_not_submittable"
                and isinstance(fresh_prepared_call, dict)
                and bool(fresh_preflight.get("context_only"))
            ):
                try:
                    submit_result = self.process_call(dict(fresh_prepared_call))
                except (GarageAlfredProcessingError, GarageProcessorError, ValueError) as exc:
                    return self._attach_submit_receipt(
                        task_id=resolved_task_id,
                        decision=self._build_submit_prepared_call_decision(
                            decision_kind="policy_blocked",
                            allowed_to_submit=False,
                            submission_mode="context_capture",
                            reason=str(exc),
                            fresh_preflight=fresh_preflight,
                            submit_result=None,
                            stale_or_blocked=True,
                        ),
                        fresh_preflight=fresh_preflight,
                        submit_result=None,
                    )
                return self._attach_submit_receipt(
                    task_id=resolved_task_id,
                    decision=self._build_submit_prepared_call_decision(
                        decision_kind="submitted",
                        allowed_to_submit=True,
                        submission_mode="context_capture",
                        reason=(
                            "prepared context-capture call passed fresh revalidation "
                            "and was processed"
                        ),
                        fresh_preflight=fresh_preflight,
                        submit_result=submit_result,
                        stale_or_blocked=False,
                    ),
                    fresh_preflight=fresh_preflight,
                    submit_result=submit_result,
                )
            return self._attach_submit_receipt(
                task_id=resolved_task_id,
                decision=self._build_submit_prepared_call_decision(
                    decision_kind=preflight_kind,
                    allowed_to_submit=False,
                    submission_mode=submission_mode,
                    reason=str(
                        fresh_preflight.get("reason")
                        or "prepared next call is not submittable in the current slice"
                    ),
                    fresh_preflight=fresh_preflight,
                    submit_result=None,
                    stale_or_blocked=preflight_kind == "policy_blocked",
                ),
                fresh_preflight=fresh_preflight,
                submit_result=None,
            )

        if not isinstance(fresh_prepared_call, dict):
            return self._attach_submit_receipt(
                task_id=resolved_task_id,
                decision=self._build_submit_prepared_call_decision(
                    decision_kind="not_ready_missing_fields",
                    allowed_to_submit=False,
                    submission_mode=submission_mode,
                    reason="fresh preflight did not produce an honest prepared next call object",
                    fresh_preflight=fresh_preflight,
                    submit_result=None,
                    stale_or_blocked=False,
                ),
                fresh_preflight=fresh_preflight,
                submit_result=None,
            )

        try:
            submit_result = self.process_call(dict(fresh_prepared_call))
        except (GarageAlfredProcessingError, GarageProcessorError, ValueError) as exc:
            return self._attach_submit_receipt(
                task_id=resolved_task_id,
                decision=self._build_submit_prepared_call_decision(
                    decision_kind="policy_blocked",
                    allowed_to_submit=False,
                    submission_mode=submission_mode,
                    reason=str(exc),
                    fresh_preflight=fresh_preflight,
                    submit_result=None,
                    stale_or_blocked=True,
                ),
                fresh_preflight=fresh_preflight,
                submit_result=None,
            )
        return self._attach_submit_receipt(
            task_id=resolved_task_id,
            decision=self._build_submit_prepared_call_decision(
                decision_kind="submitted",
                allowed_to_submit=True,
                submission_mode=submission_mode,
                reason="prepared next call passed fresh revalidation and was processed",
                fresh_preflight=fresh_preflight,
                submit_result=submit_result,
                stale_or_blocked=False,
            ),
            fresh_preflight=fresh_preflight,
            submit_result=submit_result,
        )

    def attempt_best_next_call(
        self,
        task_id: str,
        supplied_fields: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        current_summary = self._read_current_task_summary_for_receipt(task_id)
        if not isinstance(current_summary, dict):
            return self._build_attempt_best_next_receipt(
                current_summary=None,
                submit_decision={
                    "decision_kind": "unavailable_in_slice",
                    "allowed_to_submit": False,
                    "submission_mode": None,
                    "reason": "fresh task state summary is unavailable for best-next attempt",
                    "prepared_call": None,
                    "submit_result": None,
                    "fresh_preflight": None,
                    "stale_or_blocked": False,
                    "missing_required_fields": (),
                    "context_only": False,
                    "unavailable_in_slice": True,
                    "productive_in_slice": False,
                    "submit_receipt": None,
                },
            )

        submit_decision = self.submit_prepared_next_call(
            task_id=task_id,
            supplied_fields=supplied_fields,
        )
        return self._build_attempt_best_next_receipt(
            current_summary=current_summary,
            submit_decision=submit_decision,
        )

    def attempt_best_next_call_with_guards(
        self,
        task_id: str,
        *,
        supplied_fields: dict[str, Any] | None = None,
        expected: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        current_summary = self._read_current_task_summary_for_receipt(task_id)
        fresh_preflight = self.prepare_next_call_from_draft(
            task_id,
            supplied_fields=supplied_fields,
        )
        actual = self._build_guarded_attempt_actuals(
            current_summary=current_summary,
            fresh_preflight=fresh_preflight,
        )
        guard_result = self._evaluate_attempt_guards(expected=expected, actual=actual)
        if not bool(guard_result.get("guard_match")):
            return self._build_guarded_attempt_receipt(
                expected=expected,
                actual=actual,
                guard_result=guard_result,
                attempt_receipt=None,
                fresh_preflight=fresh_preflight,
            )
        attempt_receipt = self.attempt_best_next_call(
            task_id,
            supplied_fields=supplied_fields,
        )
        return self._build_guarded_attempt_receipt(
            expected=expected,
            actual=actual,
            guard_result=guard_result,
            attempt_receipt=attempt_receipt,
            fresh_preflight=fresh_preflight,
        )

    def attempt_best_next_call_with_guarded_rebase(
        self,
        task_id: str,
        *,
        supplied_fields: dict[str, Any] | None = None,
        expected: dict[str, Any] | None = None,
        allowed_rebased: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        guarded_attempt = self.attempt_best_next_call_with_guards(
            task_id,
            supplied_fields=supplied_fields,
            expected=expected,
        )
        if bool(guarded_attempt.get("guard_match")):
            result = dict(guarded_attempt)
            result["rebase_considered"] = False
            result["rebase_allowed"] = None
            result["rebase_failure_kind"] = None
            result["rebase_failure_reason"] = None
            return self._attach_guarded_rebase_final_receipt(task_id=task_id, result=result)

        rebase_result = self._evaluate_rebased_attempt_approval(
            allowed_rebased=allowed_rebased,
            guarded_attempt=guarded_attempt,
        )
        if not bool(rebase_result.get("rebase_allowed")):
            result = dict(guarded_attempt)
            result["rebase_considered"] = True
            result["rebase_allowed"] = False
            result["rebase_failure_kind"] = rebase_result.get("rebase_failure_kind")
            result["rebase_failure_reason"] = rebase_result.get("rebase_failure_reason")
            return self._attach_guarded_rebase_final_receipt(task_id=task_id, result=result)

        rebased_attempt = self.attempt_best_next_call(
            task_id,
            supplied_fields=supplied_fields,
        )
        result = dict(rebased_attempt)
        result["attempt_kind"] = self._classify_rebased_attempt_kind(
            str(rebased_attempt.get("attempt_kind") or "attempt_refused_unavailable")
        )
        result["guard_match"] = False
        result["guard_failure_kind"] = guarded_attempt.get("guard_failure_kind")
        result["guard_failure_reason"] = guarded_attempt.get("guard_failure_reason")
        result["expected"] = dict(guarded_attempt.get("expected") or {})
        result["actual"] = dict(guarded_attempt.get("actual") or {})
        result["rebase_considered"] = True
        result["rebase_allowed"] = True
        result["rebase_failure_kind"] = None
        result["rebase_failure_reason"] = None
        result["rebased_best_next_move"] = guarded_attempt.get("rebased_best_next_move")
        result["rebased_follow_up_behavior"] = guarded_attempt.get(
            "rebased_follow_up_behavior"
        )
        result["rebased_next_call_hint"] = guarded_attempt.get("rebased_next_call_hint")
        result["rebased_next_call_draft"] = guarded_attempt.get("rebased_next_call_draft")
        result["rebased_next_call_preflight"] = guarded_attempt.get(
            "rebased_next_call_preflight"
        )
        result["rebased_candidate_kind"] = guarded_attempt.get("rebased_candidate_kind")
        result["rebased_candidate_reason"] = guarded_attempt.get("rebased_candidate_reason")
        return self._attach_guarded_rebase_final_receipt(task_id=task_id, result=result)

    def continue_from_final_receipt(
        self,
        task_id: str,
        *,
        final_receipt: dict[str, Any] | None,
        supplied_fields: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        current_summary = self._read_current_task_summary_for_receipt(task_id)
        fresh_preflight = self.prepare_next_call_from_draft(
            task_id,
            supplied_fields=supplied_fields,
        )
        actual = self._build_guarded_attempt_actuals(
            current_summary=current_summary,
            fresh_preflight=fresh_preflight,
        )
        compatibility = self._evaluate_final_receipt_compatibility(
            final_receipt=final_receipt,
            current_summary=current_summary,
            actual=actual,
        )
        stale_rebased_candidate = self._build_stale_receipt_rebased_candidate(
            actual=actual,
            fresh_preflight=fresh_preflight,
        )
        if not bool(compatibility.get("prior_receipt_compatible")):
            return self._attach_continuation_final_receipt(
                task_id=task_id,
                continuation=self._build_continue_from_final_receipt_receipt(
                    task_id=task_id,
                    prior_final_receipt=final_receipt,
                    compatibility=compatibility,
                    continued_result=None,
                    stale_rebased_candidate=stale_rebased_candidate,
                ),
            )

        continued_result = self.attempt_best_next_call_with_guarded_rebase(
            task_id,
            supplied_fields=supplied_fields,
            expected=dict(compatibility.get("expected") or {}),
        )
        if not bool(continued_result.get("guard_match")):
            compatibility = {
                "prior_receipt_compatible": False,
                "continuation_failure_kind": (
                    continued_result.get("guard_failure_kind") or "receipt_state_mismatch"
                ),
                "continuation_failure_reason": (
                    continued_result.get("guard_failure_reason")
                    or "prior final receipt no longer matches fresh current state"
                ),
                "expected": dict(compatibility.get("expected") or {}),
                "actual": dict(continued_result.get("actual") or {}),
            }
        return self._attach_continuation_final_receipt(
            task_id=task_id,
            continuation=self._build_continue_from_final_receipt_receipt(
                task_id=task_id,
                prior_final_receipt=final_receipt,
                compatibility=compatibility,
                continued_result=continued_result,
                stale_rebased_candidate=stale_rebased_candidate,
            ),
        )

    def continue_from_final_receipt_with_guarded_rebase(
        self,
        task_id: str,
        *,
        final_receipt: dict[str, Any] | None,
        supplied_fields: dict[str, Any] | None = None,
        allowed_rebased: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        continued = self.continue_from_final_receipt(
            task_id,
            final_receipt=final_receipt,
            supplied_fields=supplied_fields,
        )
        if bool(continued.get("prior_receipt_compatible")):
            result = dict(continued)
            result["rebase_considered"] = False
            result["rebase_allowed"] = None
            result["rebase_failure_kind"] = None
            result["rebase_failure_reason"] = None
            result["continuation_kind"] = self._classify_continue_from_final_receipt_kind(
                prior_receipt_compatible=True,
                continued_result=result,
            )
            return self._attach_continuation_final_receipt(
                task_id=task_id,
                continuation=result,
            )

        rebase_result = self._evaluate_rebased_attempt_approval(
            allowed_rebased=allowed_rebased,
            guarded_attempt=continued,
        )
        if not bool(rebase_result.get("rebase_allowed")):
            result = dict(continued)
            result["rebase_considered"] = True
            result["rebase_allowed"] = False
            result["rebase_failure_kind"] = rebase_result.get("rebase_failure_kind")
            result["rebase_failure_reason"] = rebase_result.get("rebase_failure_reason")
            result["continuation_kind"] = self._classify_continue_from_final_receipt_kind(
                prior_receipt_compatible=False,
                continued_result=None,
                rebase_considered=True,
                rebase_allowed=False,
                rebased_candidate_kind=result.get("rebased_candidate_kind"),
            )
            return self._attach_continuation_final_receipt(
                task_id=task_id,
                continuation=result,
            )

        rebased_attempt = self.attempt_best_next_call(
            task_id,
            supplied_fields=supplied_fields,
        )
        result = dict(continued)
        result["attempt_allowed"] = bool(rebased_attempt.get("attempt_allowed"))
        result["attempted_call_type"] = rebased_attempt.get("attempted_call_type")
        result["attempted_submission_mode"] = rebased_attempt.get(
            "attempted_submission_mode"
        )
        result["missing_required_fields"] = tuple(
            rebased_attempt.get("missing_required_fields") or ()
        )
        result["requires_additional_user_or_agent_input"] = bool(
            rebased_attempt.get("requires_additional_user_or_agent_input")
        )
        result["submit_receipt"] = (
            rebased_attempt.get("submit_receipt")
            if isinstance(rebased_attempt.get("submit_receipt"), dict)
            else None
        )
        result["final_receipt"] = None
        result["rebase_considered"] = True
        result["rebase_allowed"] = True
        result["rebase_failure_kind"] = None
        result["rebase_failure_reason"] = None
        result["continuation_kind"] = self._classify_continue_from_final_receipt_kind(
            prior_receipt_compatible=False,
            continued_result=rebased_attempt,
            rebase_considered=True,
            rebase_allowed=True,
            rebased_candidate_kind=result.get("rebased_candidate_kind"),
        )
        return self._attach_continuation_final_receipt(
            task_id=task_id,
            continuation=result,
        )

    @staticmethod
    def _evaluate_final_receipt_compatibility(
        *,
        final_receipt: dict[str, Any] | None,
        current_summary: dict[str, Any] | None,
        actual: dict[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(final_receipt, dict):
            return {
                "prior_receipt_compatible": False,
                "continuation_failure_kind": "invalid_final_receipt_shape",
                "continuation_failure_reason": "final_receipt must be a dict when provided",
                "expected": {},
                "actual": dict(actual),
            }
        prior_path_kind = final_receipt.get("final_attempt_path_kind")
        if not isinstance(prior_path_kind, str) or not prior_path_kind:
            return {
                "prior_receipt_compatible": False,
                "continuation_failure_kind": "invalid_final_receipt_path",
                "continuation_failure_reason": (
                    "final_receipt must include a non-empty final_attempt_path_kind"
                ),
                "expected": {},
                "actual": dict(actual),
            }
        if not isinstance(current_summary, dict):
            return {
                "prior_receipt_compatible": False,
                "continuation_failure_kind": "fresh_state_unavailable",
                "continuation_failure_reason": (
                    "fresh task state summary is unavailable for receipt continuation"
                ),
                "expected": {},
                "actual": dict(actual),
            }

        current_best_next_move = current_summary.get("best_next_move")
        prior_best_next_move = final_receipt.get("best_next_move_now")
        prior_move_kind = (
            prior_best_next_move.get("move_kind")
            if isinstance(prior_best_next_move, dict)
            else None
        )
        prior_call_type = (
            prior_best_next_move.get("call_type")
            if isinstance(prior_best_next_move, dict)
            else None
        )
        current_move_kind = (
            current_best_next_move.get("move_kind")
            if isinstance(current_best_next_move, dict)
            else None
        )
        current_call_type = actual.get("best_next_call_type")
        comparisons = (
            (
                "dominant_target_kind_now",
                final_receipt.get("dominant_target_kind_now"),
                current_summary.get("dominant_target_kind"),
            ),
            ("best_next_move_kind_now", prior_move_kind, current_move_kind),
            ("best_next_call_type_now", prior_call_type, current_call_type),
            (
                "execution_allowed_now",
                final_receipt.get("execution_allowed_now"),
                current_summary.get("execution_allowed"),
            ),
            (
                "current_job_is_primary_focus_now",
                final_receipt.get("current_job_is_primary_focus_now"),
                current_summary.get("current_job_is_primary_focus"),
            ),
            (
                "relevant_plan_item_is_primary_focus_now",
                final_receipt.get("relevant_plan_item_is_primary_focus_now"),
                current_summary.get("relevant_plan_item_is_primary_focus"),
            ),
        )
        for field_name, expected_value, actual_value in comparisons:
            if expected_value != actual_value:
                return {
                    "prior_receipt_compatible": False,
                    "continuation_failure_kind": f"{field_name}_mismatch",
                    "continuation_failure_reason": (
                        f"{field_name} changed from expected {expected_value!r} "
                        f"to actual {actual_value!r}"
                    ),
                    "expected": {},
                    "actual": dict(actual),
                }

        expected = {
            "expected_dominant_target_kind": current_summary.get("dominant_target_kind"),
            "expected_best_next_call_type": current_call_type,
            "expected_submission_mode": actual.get("submission_mode"),
            "expected_context_only": bool(actual.get("context_only")),
            "expected_productive_in_slice": bool(actual.get("productive_in_slice")),
        }
        return {
            "prior_receipt_compatible": True,
            "continuation_failure_kind": None,
            "continuation_failure_reason": None,
            "expected": expected,
            "actual": dict(actual),
        }

    def _build_continue_from_final_receipt_receipt(
        self,
        *,
        task_id: str,
        prior_final_receipt: dict[str, Any] | None,
        compatibility: dict[str, Any],
        continued_result: dict[str, Any] | None,
        stale_rebased_candidate: dict[str, Any] | None,
        rebase_considered: bool | None = None,
        rebase_allowed: bool | None = None,
        rebase_failure_kind: str | None = None,
        rebase_failure_reason: str | None = None,
    ) -> dict[str, Any]:
        latest_summary = self._read_current_task_summary_for_receipt(task_id)
        latest_follow_up = (
            latest_summary.get("immediate_follow_up_behavior")
            if isinstance(latest_summary, dict)
            else None
        )
        prior_missing_required_fields = tuple(
            prior_final_receipt.get("missing_required_fields") or ()
        ) if isinstance(prior_final_receipt, dict) else ()
        current_missing_required_fields = tuple(
            continued_result.get("missing_required_fields") or ()
        ) if isinstance(continued_result, dict) else ()
        submit_receipt = (
            continued_result.get("submit_receipt")
            if isinstance(continued_result, dict)
            and isinstance(continued_result.get("submit_receipt"), dict)
            else None
        )
        final_receipt = (
            continued_result.get("final_receipt")
            if isinstance(continued_result, dict)
            and isinstance(continued_result.get("final_receipt"), dict)
            else None
        )
        attempt_allowed = bool(
            continued_result.get("attempt_allowed")
            if isinstance(continued_result, dict)
            else False
        )
        rebased_candidate = self._resolve_continuation_rebased_candidate(
            continued_result=continued_result,
            stale_rebased_candidate=stale_rebased_candidate,
        )
        continuation_failure_kind = compatibility.get("continuation_failure_kind")
        continuation_failure_reason = compatibility.get("continuation_failure_reason")
        if bool(compatibility.get("prior_receipt_compatible")) and isinstance(
            continued_result, dict
        ):
            continuation_failure_kind = None
            continuation_failure_reason = None
        resolved_rebase_considered = (
            rebase_considered if rebase_considered is not None else None
        )
        resolved_rebase_allowed = rebase_allowed if rebase_considered else None
        resolved_rebase_failure_kind = (
            rebase_failure_kind if rebase_considered else None
        )
        resolved_rebase_failure_reason = (
            rebase_failure_reason if rebase_considered else None
        )
        return {
            "continuation_kind": self._classify_continue_from_final_receipt_kind(
                prior_receipt_compatible=bool(compatibility.get("prior_receipt_compatible")),
                continued_result=continued_result,
                rebase_considered=bool(resolved_rebase_considered),
                rebase_allowed=resolved_rebase_allowed,
                rebased_candidate_kind=rebased_candidate.get("rebased_candidate_kind"),
            ),
            "prior_receipt_compatible": bool(compatibility.get("prior_receipt_compatible")),
            "continuation_failure_kind": continuation_failure_kind,
            "continuation_failure_reason": continuation_failure_reason,
            "prior_final_attempt_path_kind": (
                prior_final_receipt.get("final_attempt_path_kind")
                if isinstance(prior_final_receipt, dict)
                else None
            ),
            "expected": dict(compatibility.get("expected") or {}),
            "actual": dict(compatibility.get("actual") or {}),
            "supplied_fields_resolved_missing_input": bool(prior_missing_required_fields)
            and not bool(current_missing_required_fields),
            "fresh_best_next_move": (
                latest_summary.get("best_next_move")
                if isinstance(latest_summary, dict)
                else None
            ),
            "fresh_dominant_target_kind": (
                latest_summary.get("dominant_target_kind")
                if isinstance(latest_summary, dict)
                else None
            ),
            "fresh_follow_up_behavior_kind": (
                latest_follow_up.get("follow_up_behavior_kind")
                if isinstance(latest_follow_up, dict)
                else None
            ),
            "attempt_allowed": attempt_allowed,
            "attempted_call_type": (
                continued_result.get("attempted_call_type")
                if isinstance(continued_result, dict)
                else None
            ),
            "attempted_submission_mode": (
                continued_result.get("attempted_submission_mode")
                if isinstance(continued_result, dict)
                else None
            ),
            "rebase_considered": resolved_rebase_considered,
            "rebase_allowed": resolved_rebase_allowed,
            "rebase_failure_kind": resolved_rebase_failure_kind,
            "rebase_failure_reason": resolved_rebase_failure_reason,
            "missing_required_fields": current_missing_required_fields,
            "requires_additional_user_or_agent_input": bool(
                continued_result.get("requires_additional_user_or_agent_input")
                if isinstance(continued_result, dict)
                else False
            ),
            "rebased_best_next_move": rebased_candidate.get("rebased_best_next_move"),
            "rebased_follow_up_behavior": rebased_candidate.get(
                "rebased_follow_up_behavior"
            ),
            "rebased_next_call_hint": rebased_candidate.get("rebased_next_call_hint"),
            "rebased_next_call_draft": rebased_candidate.get("rebased_next_call_draft"),
            "rebased_next_call_preflight": rebased_candidate.get(
                "rebased_next_call_preflight"
            ),
            "rebased_candidate_kind": rebased_candidate.get("rebased_candidate_kind"),
            "rebased_candidate_reason": rebased_candidate.get("rebased_candidate_reason"),
            "submit_receipt": submit_receipt,
            "final_receipt": final_receipt,
        }

    def _build_stale_receipt_rebased_candidate(
        self,
        *,
        actual: dict[str, Any],
        fresh_preflight: dict[str, Any] | None,
    ) -> dict[str, Any]:
        return self._build_rebased_candidate_package(
            actual=actual,
            fresh_preflight=fresh_preflight,
        )

    @staticmethod
    def _resolve_continuation_rebased_candidate(
        *,
        continued_result: dict[str, Any] | None,
        stale_rebased_candidate: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if isinstance(continued_result, dict) and any(
            key in continued_result
            for key in (
                "rebased_best_next_move",
                "rebased_follow_up_behavior",
                "rebased_next_call_hint",
                "rebased_next_call_draft",
                "rebased_next_call_preflight",
                "rebased_candidate_kind",
                "rebased_candidate_reason",
            )
        ):
            return {
                "rebased_best_next_move": continued_result.get("rebased_best_next_move"),
                "rebased_follow_up_behavior": continued_result.get(
                    "rebased_follow_up_behavior"
                ),
                "rebased_next_call_hint": continued_result.get("rebased_next_call_hint"),
                "rebased_next_call_draft": continued_result.get("rebased_next_call_draft"),
                "rebased_next_call_preflight": continued_result.get(
                    "rebased_next_call_preflight"
                ),
                "rebased_candidate_kind": continued_result.get("rebased_candidate_kind"),
                "rebased_candidate_reason": continued_result.get(
                    "rebased_candidate_reason"
                ),
            }
        return dict(stale_rebased_candidate or {})

    def _attach_continuation_final_receipt(
        self,
        *,
        task_id: str,
        continuation: dict[str, Any],
    ) -> dict[str, Any]:
        enriched = dict(continuation)
        enriched["continuation_final_receipt"] = self._build_continuation_final_receipt(
            task_id=task_id,
            continuation=continuation,
        )
        return enriched

    def _build_continuation_final_receipt(
        self,
        *,
        task_id: str,
        continuation: dict[str, Any],
    ) -> dict[str, Any]:
        current_summary = self._read_current_task_summary_for_receipt(task_id)
        nested_submit_receipt = (
            continuation.get("submit_receipt")
            if isinstance(continuation.get("submit_receipt"), dict)
            else None
        )
        nested_final_receipt = (
            continuation.get("final_receipt")
            if isinstance(continuation.get("final_receipt"), dict)
            else None
        )
        dominant_target_kind_now = self._pick_first_present(
            nested_final_receipt,
            nested_submit_receipt,
            continuation,
            current_summary,
            key="dominant_target_kind_now",
            fallback_key="fresh_dominant_target_kind",
        )
        dominant_blocker_kind_now = self._pick_first_present(
            nested_final_receipt,
            nested_submit_receipt,
            current_summary,
            key="dominant_blocker_kind_now",
        )
        best_next_move_now = self._pick_first_present(
            nested_final_receipt,
            nested_submit_receipt,
            continuation,
            current_summary,
            key="best_next_move_now",
            fallback_key="fresh_best_next_move",
        )
        execution_allowed_now = self._pick_first_present(
            nested_final_receipt,
            nested_submit_receipt,
            current_summary,
            key="execution_allowed_now",
        )
        execution_hold_kind_now = self._pick_first_present(
            nested_final_receipt,
            nested_submit_receipt,
            current_summary,
            key="execution_hold_kind_now",
        )
        current_job_is_primary_focus_now = self._pick_first_present(
            nested_final_receipt,
            nested_submit_receipt,
            current_summary,
            key="current_job_is_primary_focus_now",
        )
        relevant_plan_item_is_primary_focus_now = self._pick_first_present(
            nested_final_receipt,
            nested_submit_receipt,
            current_summary,
            key="relevant_plan_item_is_primary_focus_now",
        )
        attempted_submission_mode = continuation.get("attempted_submission_mode")
        context_capture_only = bool(
            self._pick_first_present(
                nested_final_receipt,
                nested_submit_receipt,
                key="context_capture_only",
            )
        ) or attempted_submission_mode == "context_capture"
        productive_in_slice = bool(
            self._pick_first_present(
                nested_final_receipt,
                nested_submit_receipt,
                key="productive_in_slice",
            )
        ) or attempted_submission_mode == "productive_in_slice"
        unavailable_in_slice = bool(
            self._pick_first_present(
                nested_final_receipt,
                nested_submit_receipt,
                key="unavailable_in_slice",
            )
        )
        if not unavailable_in_slice and isinstance(best_next_move_now, dict):
            unavailable_in_slice = best_next_move_now.get("call_type") is None and not bool(
                continuation.get("attempt_allowed")
            ) and not tuple(continuation.get("missing_required_fields") or ())
        rebased_best_next_move = continuation.get("rebased_best_next_move")
        rebased_candidate_kind = continuation.get("rebased_candidate_kind")
        if rebased_candidate_kind is None and isinstance(rebased_best_next_move, dict):
            rebased_candidate_kind = (
                "unavailable_replacement_candidate"
                if rebased_best_next_move.get("call_type") is None
                else "productive_replacement_candidate"
            )
        return {
            "continuation_final_path_kind": continuation.get("continuation_kind"),
            "prior_receipt_compatible": bool(continuation.get("prior_receipt_compatible")),
            "continuation_failure_kind": continuation.get("continuation_failure_kind"),
            "continuation_failure_reason": continuation.get("continuation_failure_reason"),
            "rebase_considered": continuation.get("rebase_considered"),
            "rebase_allowed": continuation.get("rebase_allowed"),
            "rebase_failure_kind": continuation.get("rebase_failure_kind"),
            "rebase_failure_reason": continuation.get("rebase_failure_reason"),
            "attempt_allowed": bool(continuation.get("attempt_allowed")),
            "attempted_call_type": continuation.get("attempted_call_type"),
            "attempted_submission_mode": attempted_submission_mode,
            "productive_in_slice": productive_in_slice,
            "context_capture_only": context_capture_only,
            "missing_required_fields": tuple(continuation.get("missing_required_fields") or ()),
            "requires_additional_user_or_agent_input": bool(
                continuation.get("requires_additional_user_or_agent_input")
            ),
            "unavailable_in_slice": unavailable_in_slice,
            "rebased_best_next_move": rebased_best_next_move,
            "rebased_follow_up_behavior": continuation.get("rebased_follow_up_behavior"),
            "rebased_next_call_hint": continuation.get("rebased_next_call_hint"),
            "rebased_next_call_draft": continuation.get("rebased_next_call_draft"),
            "rebased_next_call_preflight": continuation.get("rebased_next_call_preflight"),
            "rebased_candidate_kind": rebased_candidate_kind,
            "rebased_candidate_reason": continuation.get("rebased_candidate_reason"),
            "dominant_target_kind_now": dominant_target_kind_now,
            "dominant_blocker_kind_now": dominant_blocker_kind_now,
            "best_next_move_now": best_next_move_now,
            "execution_allowed_now": execution_allowed_now,
            "execution_hold_kind_now": execution_hold_kind_now,
            "current_job_is_primary_focus_now": current_job_is_primary_focus_now,
            "relevant_plan_item_is_primary_focus_now": (
                relevant_plan_item_is_primary_focus_now
            ),
        }

    @staticmethod
    def _pick_first_present(
        *sources: dict[str, Any] | None,
        key: str,
        fallback_key: str | None = None,
    ) -> Any:
        for source in sources:
            if not isinstance(source, dict):
                continue
            if key in source:
                return source.get(key)
            if fallback_key is not None and fallback_key in source:
                return source.get(fallback_key)
        return None

    def _attach_guarded_rebase_final_receipt(
        self,
        *,
        task_id: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        enriched = dict(result)
        enriched["final_receipt"] = self._build_guarded_rebase_final_receipt(
            task_id=task_id,
            result=result,
        )
        return enriched

    def _build_guarded_rebase_final_receipt(
        self,
        *,
        task_id: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        current_summary = self._read_current_task_summary_for_receipt(task_id)
        return {
            "final_attempt_path_kind": self._classify_guarded_rebase_final_attempt_path(result),
            "original_guard_match": bool(result.get("guard_match")),
            "rebase_considered": bool(result.get("rebase_considered")),
            "rebase_allowed": result.get("rebase_allowed"),
            "rebase_failure_kind": result.get("rebase_failure_kind"),
            "rebase_failure_reason": result.get("rebase_failure_reason"),
            "final_attempt_allowed": bool(result.get("attempt_allowed")),
            "attempted_call_type": result.get("attempted_call_type"),
            "attempted_submission_mode": result.get("attempted_submission_mode"),
            "productive_in_slice": bool(result.get("productive_in_slice")),
            "context_capture_only": bool(result.get("context_capture_only")),
            "missing_required_fields": tuple(result.get("missing_required_fields") or ()),
            "requires_additional_user_or_agent_input": bool(
                result.get("requires_additional_user_or_agent_input")
            ),
            "unavailable_in_slice": bool(result.get("unavailable_in_slice")),
            "guard_failure_kind": result.get("guard_failure_kind"),
            "guard_failure_reason": result.get("guard_failure_reason"),
            "dominant_target_kind_now": (
                current_summary.get("dominant_target_kind")
                if isinstance(current_summary, dict)
                else None
            ),
            "dominant_blocker_kind_now": (
                current_summary.get("dominant_blocker_kind")
                if isinstance(current_summary, dict)
                else None
            ),
            "best_next_move_now": (
                current_summary.get("best_next_move")
                if isinstance(current_summary, dict)
                else None
            ),
            "execution_allowed_now": (
                current_summary.get("execution_allowed")
                if isinstance(current_summary, dict)
                else None
            ),
            "execution_hold_kind_now": (
                current_summary.get("execution_hold_kind")
                if isinstance(current_summary, dict)
                else None
            ),
            "current_job_is_primary_focus_now": (
                current_summary.get("current_job_is_primary_focus")
                if isinstance(current_summary, dict)
                else None
            ),
            "relevant_plan_item_is_primary_focus_now": (
                current_summary.get("relevant_plan_item_is_primary_focus")
                if isinstance(current_summary, dict)
                else None
            ),
        }

    def _attach_submit_receipt(
        self,
        *,
        task_id: str | None,
        decision: dict[str, Any],
        fresh_preflight: dict[str, Any] | None,
        submit_result: GarageProcessingResult | None,
    ) -> dict[str, Any]:
        enriched = dict(decision)
        enriched["submit_receipt"] = self._build_submit_receipt(
            task_id=task_id,
            decision=decision,
            fresh_preflight=fresh_preflight,
            submit_result=submit_result,
        )
        return enriched

    def _build_attempt_best_next_receipt(
        self,
        *,
        current_summary: dict[str, Any] | None,
        submit_decision: dict[str, Any],
    ) -> dict[str, Any]:
        immediate_follow_up = (
            current_summary.get("immediate_follow_up_behavior")
            if isinstance(current_summary, dict)
            else None
        )
        next_call_hint = (
            current_summary.get("next_call_hint") if isinstance(current_summary, dict) else None
        )
        next_call_draft = (
            current_summary.get("next_call_draft")
            if isinstance(current_summary, dict)
            else None
        )
        best_next_move = (
            current_summary.get("best_next_move") if isinstance(current_summary, dict) else None
        )
        submit_receipt = submit_decision.get("submit_receipt")
        prepared_call = submit_decision.get("prepared_call")
        missing_required_fields = tuple(submit_decision.get("missing_required_fields") or ())
        attempted_call_type = self._resolve_attempted_call_type(
            best_next_move=best_next_move,
            next_call_hint=next_call_hint,
            next_call_draft=next_call_draft,
            prepared_call=prepared_call,
        )
        requires_additional_input = bool(missing_required_fields) or bool(
            next_call_hint.get("requires_additional_user_or_agent_input")
            if isinstance(next_call_hint, dict)
            else False
        )
        attempt_reason = str(
            submit_decision.get("reason")
            or (
                next_call_hint.get("hint_reason")
                if isinstance(next_call_hint, dict)
                else "best next call attempt is unavailable in the current slice"
            )
        )
        submission_mode = submit_decision.get("submission_mode")
        context_capture_only = bool(submit_decision.get("context_only")) or (
            submission_mode == "context_capture"
        )
        productive_in_slice = bool(submit_decision.get("productive_in_slice"))
        unavailable_in_slice = bool(submit_decision.get("unavailable_in_slice")) or (
            attempted_call_type is None
        )
        return {
            "attempt_kind": self._classify_attempt_kind(
                submit_decision=submit_decision,
                attempted_call_type=attempted_call_type,
            ),
            "attempted_call_type": attempted_call_type,
            "attempted_submission_mode": submission_mode,
            "best_next_move": best_next_move,
            "follow_up_behavior_kind": (
                immediate_follow_up.get("follow_up_behavior_kind")
                if isinstance(immediate_follow_up, dict)
                else None
            ),
            "next_call_hint": next_call_hint,
            "next_call_draft": next_call_draft,
            "attempt_allowed": bool(submit_decision.get("allowed_to_submit")),
            "attempt_reason": attempt_reason,
            "missing_required_fields": missing_required_fields,
            "requires_additional_user_or_agent_input": requires_additional_input,
            "formed_concrete_call": isinstance(prepared_call, dict),
            "prepared_call": prepared_call if isinstance(prepared_call, dict) else None,
            "submit_receipt": submit_receipt if isinstance(submit_receipt, dict) else None,
            "productive_in_slice": productive_in_slice,
            "context_capture_only": context_capture_only,
            "unavailable_in_slice": unavailable_in_slice,
        }

    def _build_guarded_attempt_actuals(
        self,
        *,
        current_summary: dict[str, Any] | None,
        fresh_preflight: dict[str, Any] | None,
    ) -> dict[str, Any]:
        immediate_follow_up = (
            current_summary.get("immediate_follow_up_behavior")
            if isinstance(current_summary, dict)
            else None
        )
        next_call_hint = (
            current_summary.get("next_call_hint") if isinstance(current_summary, dict) else None
        )
        next_call_draft = (
            current_summary.get("next_call_draft")
            if isinstance(current_summary, dict)
            else None
        )
        best_next_move = (
            current_summary.get("best_next_move") if isinstance(current_summary, dict) else None
        )
        prepared_call = (
            fresh_preflight.get("prepared_call")
            if isinstance(fresh_preflight, dict)
            else None
        )
        attempted_call_type = self._resolve_attempted_call_type(
            best_next_move=best_next_move,
            next_call_hint=next_call_hint,
            next_call_draft=next_call_draft,
            prepared_call=prepared_call,
        )
        submission_mode = self._resolve_submission_mode(fresh_preflight)
        context_only = bool(fresh_preflight.get("context_only")) if isinstance(
            fresh_preflight, dict
        ) else bool(
            next_call_hint.get("context_only") if isinstance(next_call_hint, dict) else False
        )
        productive_in_slice = (
            not context_only
            and not bool(
                fresh_preflight.get("unavailable_in_slice")
                if isinstance(fresh_preflight, dict)
                else False
            )
        )
        if not isinstance(fresh_preflight, dict) and isinstance(immediate_follow_up, dict):
            productive_in_slice = bool(immediate_follow_up.get("productive_in_slice"))
        unavailable_in_slice = bool(fresh_preflight.get("unavailable_in_slice")) if isinstance(
            fresh_preflight, dict
        ) else attempted_call_type is None
        missing_required_fields = tuple(
            fresh_preflight.get("missing_required_fields") or ()
        ) if isinstance(fresh_preflight, dict) else ()
        requires_additional_input = bool(missing_required_fields) or bool(
            next_call_hint.get("requires_additional_user_or_agent_input")
            if isinstance(next_call_hint, dict)
            else False
        )
        return {
            "dominant_target_kind": (
                current_summary.get("dominant_target_kind")
                if isinstance(current_summary, dict)
                else None
            ),
            "best_next_call_type": attempted_call_type,
            "follow_up_behavior_kind": (
                immediate_follow_up.get("follow_up_behavior_kind")
                if isinstance(immediate_follow_up, dict)
                else None
            ),
            "submission_mode": submission_mode,
            "context_only": context_only,
            "productive_in_slice": productive_in_slice,
            "unavailable_in_slice": unavailable_in_slice,
            "best_next_move": best_next_move,
            "missing_required_fields": missing_required_fields,
            "requires_additional_user_or_agent_input": requires_additional_input,
            "prepared_call": prepared_call if isinstance(prepared_call, dict) else None,
        }

    @staticmethod
    def _evaluate_attempt_guards(
        *,
        expected: dict[str, Any] | None,
        actual: dict[str, Any],
    ) -> dict[str, Any]:
        if expected is None:
            return {
                "guard_match": True,
                "guard_failure_kind": None,
                "guard_failure_reason": None,
                "expected": {},
            }
        if not isinstance(expected, dict):
            return {
                "guard_match": False,
                "guard_failure_kind": "invalid_guard_shape",
                "guard_failure_reason": "expected guards must be a dict when provided",
                "expected": {},
            }
        expected_copy = dict(expected)
        allowed_keys = {
            "expected_dominant_target_kind": "dominant_target_kind",
            "expected_best_next_call_type": "best_next_call_type",
            "expected_follow_up_behavior_kind": "follow_up_behavior_kind",
            "expected_submission_mode": "submission_mode",
            "expected_context_only": "context_only",
            "expected_productive_in_slice": "productive_in_slice",
        }
        unsupported_keys = tuple(
            key for key in expected_copy.keys() if key not in allowed_keys
        )
        if unsupported_keys:
            return {
                "guard_match": False,
                "guard_failure_kind": "unsupported_guard_key",
                "guard_failure_reason": (
                    "unsupported guarded-attempt expectation keys: "
                    + ", ".join(sorted(unsupported_keys))
                ),
                "expected": expected_copy,
            }
        for expected_key, actual_key in allowed_keys.items():
            if expected_key not in expected_copy:
                continue
            if expected_copy.get(expected_key) != actual.get(actual_key):
                return {
                    "guard_match": False,
                    "guard_failure_kind": f"{actual_key}_mismatch",
                    "guard_failure_reason": (
                        f"{actual_key} changed from expected {expected_copy.get(expected_key)!r} "
                        f"to actual {actual.get(actual_key)!r}"
                    ),
                    "expected": expected_copy,
                }
        return {
            "guard_match": True,
            "guard_failure_kind": None,
            "guard_failure_reason": None,
            "expected": expected_copy,
        }

    def _build_guarded_attempt_receipt(
        self,
        *,
        expected: dict[str, Any] | None,
        actual: dict[str, Any],
        guard_result: dict[str, Any],
        attempt_receipt: dict[str, Any] | None,
        fresh_preflight: dict[str, Any] | None,
    ) -> dict[str, Any]:
        rebased_candidate = self._build_rebased_candidate_package(
            actual=actual,
            fresh_preflight=fresh_preflight,
        )
        if isinstance(attempt_receipt, dict):
            guarded = dict(attempt_receipt)
            guarded["guard_match"] = bool(guard_result.get("guard_match"))
            guarded["guard_failure_kind"] = guard_result.get("guard_failure_kind")
            guarded["guard_failure_reason"] = guard_result.get("guard_failure_reason")
            guarded["expected"] = dict(guard_result.get("expected") or {})
            guarded["actual"] = dict(actual)
            guarded["rebased_best_next_move"] = None
            guarded["rebased_follow_up_behavior"] = None
            guarded["rebased_next_call_hint"] = None
            guarded["rebased_next_call_draft"] = None
            guarded["rebased_next_call_preflight"] = None
            guarded["rebased_candidate_kind"] = None
            guarded["rebased_candidate_reason"] = None
            return guarded
        prepared_call = (
            fresh_preflight.get("prepared_call")
            if isinstance(fresh_preflight, dict)
            else actual.get("prepared_call")
        )
        return {
            "attempt_kind": "guard_mismatch_refused",
            "guard_match": False,
            "guard_failure_kind": guard_result.get("guard_failure_kind"),
            "guard_failure_reason": guard_result.get("guard_failure_reason"),
            "expected": dict(guard_result.get("expected") or expected or {}),
            "actual": dict(actual),
            "attempt_allowed": False,
            "attempt_reason": guard_result.get("guard_failure_reason"),
            "attempted_call_type": actual.get("best_next_call_type"),
            "attempted_submission_mode": actual.get("submission_mode"),
            "best_next_move": actual.get("best_next_move"),
            "follow_up_behavior_kind": actual.get("follow_up_behavior_kind"),
            "missing_required_fields": tuple(actual.get("missing_required_fields") or ()),
            "requires_additional_user_or_agent_input": bool(
                actual.get("requires_additional_user_or_agent_input")
            ),
            "formed_concrete_call": isinstance(prepared_call, dict),
            "prepared_call": prepared_call if isinstance(prepared_call, dict) else None,
            "submit_receipt": None,
            "productive_in_slice": bool(actual.get("productive_in_slice")),
            "context_capture_only": bool(actual.get("context_only")),
            "unavailable_in_slice": bool(actual.get("unavailable_in_slice")),
            "rebased_best_next_move": rebased_candidate.get("rebased_best_next_move"),
            "rebased_follow_up_behavior": rebased_candidate.get("rebased_follow_up_behavior"),
            "rebased_next_call_hint": rebased_candidate.get("rebased_next_call_hint"),
            "rebased_next_call_draft": rebased_candidate.get("rebased_next_call_draft"),
            "rebased_next_call_preflight": rebased_candidate.get("rebased_next_call_preflight"),
            "rebased_candidate_kind": rebased_candidate.get("rebased_candidate_kind"),
            "rebased_candidate_reason": rebased_candidate.get("rebased_candidate_reason"),
        }

    def _build_rebased_candidate_package(
        self,
        *,
        actual: dict[str, Any],
        fresh_preflight: dict[str, Any] | None,
    ) -> dict[str, Any]:
        best_next_move = actual.get("best_next_move")
        follow_up_behavior_kind = actual.get("follow_up_behavior_kind")
        next_call_hint = {
            "recommended_call_type": actual.get("best_next_call_type"),
            "hint_kind": (
                "unavailable-in-slice"
                if bool(actual.get("unavailable_in_slice"))
                else (
                    "context-only"
                    if bool(actual.get("context_only"))
                    else (
                        "caller-input-still-required"
                        if tuple(actual.get("missing_required_fields") or ())
                        else "executable-now"
                    )
                )
            ),
            "requires_additional_user_or_agent_input": bool(
                actual.get("requires_additional_user_or_agent_input")
            ),
            "context_only": bool(actual.get("context_only")),
            "unavailable_in_slice": bool(actual.get("unavailable_in_slice")),
            "dominant_target_kind": actual.get("dominant_target_kind"),
        }
        next_call_draft = {
            "call_type": actual.get("best_next_call_type"),
            "known_fields": {},
            "missing_required_fields": tuple(actual.get("missing_required_fields") or ()),
            "context_only": bool(actual.get("context_only")),
            "unavailable_in_slice": bool(actual.get("unavailable_in_slice")),
            "partially_ready": bool(actual.get("requires_additional_user_or_agent_input")),
            "executable_now": (
                not bool(actual.get("context_only"))
                and not bool(actual.get("unavailable_in_slice"))
                and not tuple(actual.get("missing_required_fields") or ())
            ),
        }
        if isinstance(actual.get("prepared_call"), dict):
            next_call_draft["known_fields"] = dict(actual["prepared_call"])
        return {
            "rebased_best_next_move": dict(best_next_move) if isinstance(best_next_move, dict) else None,
            "rebased_follow_up_behavior": (
                {
                    "follow_up_behavior_kind": follow_up_behavior_kind,
                    "productive_in_slice": bool(actual.get("productive_in_slice")),
                    "context_capture_only": bool(actual.get("context_only")),
                }
                if isinstance(follow_up_behavior_kind, str)
                else None
            ),
            "rebased_next_call_hint": next_call_hint,
            "rebased_next_call_draft": next_call_draft,
            "rebased_next_call_preflight": (
                dict(fresh_preflight) if isinstance(fresh_preflight, dict) else None
            ),
            "rebased_candidate_kind": self._classify_rebased_candidate_kind(
                actual=actual,
                fresh_preflight=fresh_preflight,
            ),
            "rebased_candidate_reason": (
                str(fresh_preflight.get("reason"))
                if isinstance(fresh_preflight, dict) and isinstance(fresh_preflight.get("reason"), str)
                else (
                    best_next_move.get("reason")
                    if isinstance(best_next_move, dict) and isinstance(best_next_move.get("reason"), str)
                    else "fresh current best-next was rebased after guard mismatch"
                )
            ),
        }

    @staticmethod
    def _classify_rebased_candidate_kind(
        *,
        actual: dict[str, Any],
        fresh_preflight: dict[str, Any] | None,
    ) -> str:
        if bool(actual.get("unavailable_in_slice")):
            return "unavailable_replacement_candidate"
        if tuple(actual.get("missing_required_fields") or ()):
            return "missing_input_replacement_candidate"
        if bool(actual.get("context_only")):
            return "context_capture_replacement_candidate"
        return "productive_replacement_candidate"

    @staticmethod
    def _evaluate_rebased_attempt_approval(
        *,
        allowed_rebased: dict[str, Any] | None,
        guarded_attempt: dict[str, Any],
    ) -> dict[str, Any]:
        candidate_kind = guarded_attempt.get("rebased_candidate_kind")
        candidate_call_type = None
        candidate_hint = guarded_attempt.get("rebased_next_call_hint")
        if isinstance(candidate_hint, dict):
            candidate_call_type = candidate_hint.get("recommended_call_type")
        candidate_follow_up = guarded_attempt.get("rebased_follow_up_behavior")
        candidate_follow_up_kind = (
            candidate_follow_up.get("follow_up_behavior_kind")
            if isinstance(candidate_follow_up, dict)
            else None
        )
        candidate_preflight = guarded_attempt.get("rebased_next_call_preflight")
        candidate_submission_mode = None
        if isinstance(candidate_preflight, dict):
            if bool(candidate_preflight.get("context_only")):
                candidate_submission_mode = "context_capture"
            elif not bool(candidate_preflight.get("unavailable_in_slice")):
                candidate_submission_mode = "productive_in_slice"

        if candidate_kind == "unavailable_replacement_candidate":
            return {
                "rebase_allowed": False,
                "rebase_failure_kind": "rebased_candidate_unavailable",
                "rebase_failure_reason": "fresh rebased candidate is unavailable in the current slice",
            }

        if allowed_rebased is None:
            return {
                "rebase_allowed": False,
                "rebase_failure_kind": "rebased_candidate_not_approved",
                "rebase_failure_reason": "caller did not approve rebased attempts",
            }
        if not isinstance(allowed_rebased, dict):
            return {
                "rebase_allowed": False,
                "rebase_failure_kind": "invalid_rebase_approval_shape",
                "rebase_failure_reason": "allowed_rebased must be a dict when provided",
            }

        allowed_copy = dict(allowed_rebased)
        allowed_keys = {
            "allow_rebased_productive_candidate",
            "allow_rebased_context_capture_candidate",
            "allow_rebased_missing_input_candidate",
            "expected_rebased_call_type",
            "expected_rebased_submission_mode",
            "expected_rebased_follow_up_behavior_kind",
        }
        unsupported_keys = tuple(
            key for key in allowed_copy.keys() if key not in allowed_keys
        )
        if unsupported_keys:
            return {
                "rebase_allowed": False,
                "rebase_failure_kind": "unsupported_rebase_approval_key",
                "rebase_failure_reason": (
                    "unsupported rebase approval keys: "
                    + ", ".join(sorted(unsupported_keys))
                ),
            }

        allow_flag_by_kind = {
            "productive_replacement_candidate": bool(
                allowed_copy.get("allow_rebased_productive_candidate")
            ),
            "context_capture_replacement_candidate": bool(
                allowed_copy.get("allow_rebased_context_capture_candidate")
            ),
            "missing_input_replacement_candidate": bool(
                allowed_copy.get("allow_rebased_missing_input_candidate")
            ),
        }
        if not allow_flag_by_kind.get(str(candidate_kind), False):
            return {
                "rebase_allowed": False,
                "rebase_failure_kind": "rebased_candidate_not_approved",
                "rebase_failure_reason": (
                    f"caller did not approve rebased candidate kind {candidate_kind!r}"
                ),
            }

        expected_call_type = allowed_copy.get("expected_rebased_call_type")
        if expected_call_type is not None and expected_call_type != candidate_call_type:
            return {
                "rebase_allowed": False,
                "rebase_failure_kind": "rebased_call_type_mismatch",
                "rebase_failure_reason": (
                    f"rebased call type changed from expected {expected_call_type!r} "
                    f"to actual {candidate_call_type!r}"
                ),
            }
        expected_submission_mode = allowed_copy.get("expected_rebased_submission_mode")
        if (
            expected_submission_mode is not None
            and expected_submission_mode != candidate_submission_mode
        ):
            return {
                "rebase_allowed": False,
                "rebase_failure_kind": "rebased_submission_mode_mismatch",
                "rebase_failure_reason": (
                    f"rebased submission mode changed from expected {expected_submission_mode!r} "
                    f"to actual {candidate_submission_mode!r}"
                ),
            }
        expected_follow_up = allowed_copy.get("expected_rebased_follow_up_behavior_kind")
        if expected_follow_up is not None and expected_follow_up != candidate_follow_up_kind:
            return {
                "rebase_allowed": False,
                "rebase_failure_kind": "rebased_follow_up_behavior_kind_mismatch",
                "rebase_failure_reason": (
                    f"rebased follow-up behavior changed from expected {expected_follow_up!r} "
                    f"to actual {candidate_follow_up_kind!r}"
                ),
            }
        return {
            "rebase_allowed": True,
            "rebase_failure_kind": None,
            "rebase_failure_reason": None,
        }

    @staticmethod
    def _classify_rebased_attempt_kind(attempt_kind: str) -> str:
        if attempt_kind.startswith("attempted_") or attempt_kind.startswith("attempt_refused_"):
            return f"rebased_{attempt_kind}"
        return f"rebased_{attempt_kind}"

    @staticmethod
    def _classify_continue_from_final_receipt_kind(
        *,
        prior_receipt_compatible: bool,
        continued_result: dict[str, Any] | None,
        rebase_considered: bool = False,
        rebase_allowed: bool | None = None,
        rebased_candidate_kind: str | None = None,
    ) -> str:
        if not prior_receipt_compatible:
            if rebase_considered and rebase_allowed and isinstance(continued_result, dict):
                if bool(continued_result.get("attempt_allowed")):
                    if continued_result.get("attempted_submission_mode") == "context_capture":
                        return "stale_rebased_continued_context_capture"
                    return "stale_rebased_continued_productive_execution"
                if tuple(continued_result.get("missing_required_fields") or ()):
                    return "stale_rebased_missing_input_refused"
                return "stale_rebased_unavailable_refused"
            if rebase_considered:
                if rebased_candidate_kind == "unavailable_replacement_candidate":
                    return "stale_rebased_unavailable_refused"
                return "stale_rebased_refused"
            return "stale_receipt_refused"
        if not isinstance(continued_result, dict):
            return "unavailable_receipt_continuation"
        if bool(continued_result.get("attempt_allowed")):
            if continued_result.get("attempted_submission_mode") == "context_capture":
                return "continued_context_capture"
            return "continued_productive_execution"
        if tuple(continued_result.get("missing_required_fields") or ()):
            return "continued_missing_input_refused"
        return "continued_unavailable_refused"

    @staticmethod
    def _classify_guarded_rebase_final_attempt_path(result: dict[str, Any]) -> str:
        original_guard_match = bool(result.get("guard_match"))
        rebase_considered = bool(result.get("rebase_considered"))
        rebase_allowed = result.get("rebase_allowed")
        attempt_allowed = bool(result.get("attempt_allowed"))
        attempted_submission_mode = result.get("attempted_submission_mode")
        missing_required_fields = tuple(result.get("missing_required_fields") or ())
        unavailable_in_slice = bool(result.get("unavailable_in_slice"))
        rebased_candidate_kind = result.get("rebased_candidate_kind")

        if original_guard_match:
            if attempt_allowed:
                if attempted_submission_mode == "context_capture":
                    return "original_guarded_attempt_context_capture"
                return "original_guarded_attempt_productive_execution"
            if missing_required_fields:
                return "guard_match_missing_input_refused"
            return "guard_match_unavailable_refused"

        if rebase_considered and rebase_allowed:
            if attempt_allowed:
                if attempted_submission_mode == "context_capture":
                    return "guard_mismatch_rebased_context_capture"
                return "guard_mismatch_rebased_productive_execution"
            if missing_required_fields:
                return "guard_mismatch_rebased_missing_input_refused"
            return "guard_mismatch_rebased_unavailable_refused"

        if rebased_candidate_kind == "unavailable_replacement_candidate" or unavailable_in_slice:
            return "guard_mismatch_rebased_unavailable_refused"
        return "guard_mismatch_rebase_refused"

    def _build_submit_receipt(
        self,
        *,
        task_id: str | None,
        decision: dict[str, Any],
        fresh_preflight: dict[str, Any] | None,
        submit_result: GarageProcessingResult | None,
    ) -> dict[str, Any]:
        post_call_guidance = None
        if submit_result is not None and isinstance(submit_result.result, dict):
            guidance = submit_result.result.get("post_call_guidance")
            if isinstance(guidance, dict):
                post_call_guidance = guidance

        current_summary = self._read_current_task_summary_for_receipt(task_id)
        dominant_target_kind_now = None
        dominant_blocker_kind_now = None
        best_next_move_now = None
        execution_allowed_now = None
        execution_hold_kind_now = None
        current_job_is_primary_focus_now = None
        relevant_plan_item_is_primary_focus_now = None
        posture_transition = None

        if isinstance(post_call_guidance, dict):
            dominant_target_kind_now = post_call_guidance.get("dominant_target_kind")
            dominant_blocker_kind_now = post_call_guidance.get("dominant_blocker_kind")
            best_next_move_now = post_call_guidance.get("best_next_move")
            execution_allowed_now = post_call_guidance.get("execution_allowed")
            execution_hold_kind_now = post_call_guidance.get("execution_hold_kind")
            current_job_is_primary_focus_now = post_call_guidance.get(
                "current_job_is_primary_focus"
            )
            relevant_plan_item_is_primary_focus_now = post_call_guidance.get(
                "relevant_plan_item_is_primary_focus"
            )
            posture_transition = post_call_guidance.get("posture_transition")
        elif isinstance(current_summary, dict):
            dominant_target_kind_now = current_summary.get("dominant_target_kind")
            dominant_blocker_kind_now = current_summary.get("dominant_blocker_kind")
            best_next_move_now = current_summary.get("best_next_move")
            execution_allowed_now = current_summary.get("execution_allowed")
            execution_hold_kind_now = current_summary.get("execution_hold_kind")
            current_job_is_primary_focus_now = current_summary.get(
                "current_job_is_primary_focus"
            )
            relevant_plan_item_is_primary_focus_now = current_summary.get(
                "relevant_plan_item_is_primary_focus"
            )

        return {
            "decision_kind": decision.get("decision_kind"),
            "allowed_to_submit": decision.get("allowed_to_submit"),
            "submission_mode": decision.get("submission_mode"),
            "reason": decision.get("reason"),
            "submit_effect_kind": self._classify_submit_effect_kind(
                decision=decision,
                posture_transition=posture_transition,
            ),
            "productive_in_slice": decision.get("productive_in_slice"),
            "context_capture_only": decision.get("submission_mode") == "context_capture",
            "stale_or_blocked": decision.get("stale_or_blocked"),
            "missing_required_fields": decision.get("missing_required_fields"),
            "prepared_call": (
                fresh_preflight.get("prepared_call")
                if isinstance(fresh_preflight, dict)
                else decision.get("prepared_call")
            ),
            "submit_result": submit_result,
            "dominant_target_kind_now": dominant_target_kind_now,
            "dominant_blocker_kind_now": dominant_blocker_kind_now,
            "best_next_move_now": best_next_move_now,
            "execution_allowed_now": execution_allowed_now,
            "execution_hold_kind_now": execution_hold_kind_now,
            "current_job_is_primary_focus_now": current_job_is_primary_focus_now,
            "relevant_plan_item_is_primary_focus_now": (
                relevant_plan_item_is_primary_focus_now
            ),
            "posture_transition_kind_now": (
                posture_transition.get("transition_kind")
                if isinstance(posture_transition, dict)
                else None
            ),
            "posture_transition_reason_now": (
                posture_transition.get("transition_reason")
                if isinstance(posture_transition, dict)
                else None
            ),
        }

    def _read_current_task_summary_for_receipt(
        self,
        task_id: str | None,
    ) -> dict[str, Any] | None:
        if not isinstance(task_id, str) or self._state_reader is None:
            return None
        summary_reader = getattr(self._state_reader, "latest_task_state_summary", None)
        if not callable(summary_reader):
            return None
        summary = summary_reader(task_id)
        return dict(summary) if isinstance(summary, dict) else None

    @staticmethod
    def _resolve_attempted_call_type(
        *,
        best_next_move: Any,
        next_call_hint: Any,
        next_call_draft: Any,
        prepared_call: Any,
    ) -> str | None:
        if isinstance(prepared_call, dict) and isinstance(prepared_call.get("call_type"), str):
            return str(prepared_call.get("call_type"))
        if isinstance(next_call_draft, dict) and isinstance(next_call_draft.get("call_type"), str):
            return str(next_call_draft.get("call_type"))
        if isinstance(next_call_hint, dict) and isinstance(
            next_call_hint.get("recommended_call_type"), str
        ):
            return str(next_call_hint.get("recommended_call_type"))
        if isinstance(best_next_move, dict) and isinstance(best_next_move.get("call_type"), str):
            return str(best_next_move.get("call_type"))
        return None

    @staticmethod
    def _classify_attempt_kind(
        *,
        submit_decision: dict[str, Any],
        attempted_call_type: str | None,
    ) -> str:
        decision_kind = str(submit_decision.get("decision_kind") or "unavailable_in_slice")
        if bool(submit_decision.get("allowed_to_submit")):
            if submit_decision.get("submission_mode") == "context_capture":
                return "attempted_context_capture"
            return "attempted_productive_execution"
        if tuple(submit_decision.get("missing_required_fields") or ()):
            return "attempt_refused_missing_fields"
        if bool(submit_decision.get("stale_or_blocked")):
            return "attempt_refused_stale_or_blocked"
        if attempted_call_type is None or bool(submit_decision.get("unavailable_in_slice")):
            return "attempt_refused_unavailable"
        if decision_kind == "policy_blocked":
            return "attempt_refused_stale_or_blocked"
        return "attempt_refused_unavailable"

    @staticmethod
    def _classify_submit_effect_kind(
        *,
        decision: dict[str, Any],
        posture_transition: dict[str, Any] | None,
    ) -> str:
        decision_kind = str(decision.get("decision_kind") or "unavailable_in_slice")
        submission_mode = decision.get("submission_mode")
        allowed_to_submit = bool(decision.get("allowed_to_submit"))
        transition_kind = (
            posture_transition.get("transition_kind")
            if isinstance(posture_transition, dict)
            else None
        )
        if not allowed_to_submit:
            if decision_kind == "stale_prepared_call":
                return "submission_refused_stale"
            if decision_kind == "not_ready_missing_fields":
                return "submission_refused_missing_fields"
            return "submission_refused_unavailable"
        if submission_mode == "context_capture":
            if transition_kind == "preserved":
                return "posture_preserved_after_context_capture"
            return "context_capture_recorded"
        if transition_kind in {"resolved", "refined"}:
            return "productive_execution_advanced"
        return "posture_changed_after_submission"

    def _effective_submit_supplied_fields(
        self,
        task_id: str,
        *,
        prepared_call: dict[str, Any] | None,
        supplied_fields: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if isinstance(supplied_fields, dict):
            return dict(supplied_fields)
        if not isinstance(prepared_call, dict):
            return None
        current_draft = self._read_current_next_call_draft(task_id)
        if not isinstance(current_draft, dict):
            return None
        known_fields = dict(current_draft.get("known_fields") or {})
        derived: dict[str, Any] = {}
        for field_name, field_value in prepared_call.items():
            if field_name not in known_fields or known_fields.get(field_name) != field_value:
                derived[field_name] = field_value
        return derived or None

    def _read_current_next_call_draft(self, task_id: str) -> dict[str, Any] | None:
        if self._state_reader is None:
            return None
        summary_reader = getattr(self._state_reader, "latest_task_state_summary", None)
        if not callable(summary_reader):
            return None
        summary = summary_reader(task_id)
        if not isinstance(summary, dict):
            return None
        draft = summary.get("next_call_draft")
        return dict(draft) if isinstance(draft, dict) else None

    @staticmethod
    def _resolve_submit_task_id(
        task_id: str | None,
        prepared_call: dict[str, Any] | None,
    ) -> str | None:
        if isinstance(task_id, str):
            return task_id
        if isinstance(prepared_call, dict) and isinstance(prepared_call.get("task_id"), str):
            return str(prepared_call["task_id"])
        return None

    @staticmethod
    def _requested_prepared_call_matches_fresh(
        *,
        prepared_call: dict[str, Any] | None,
        fresh_prepared_call: Any,
    ) -> bool:
        if prepared_call is None:
            return True
        return isinstance(fresh_prepared_call, dict) and dict(prepared_call) == dict(
            fresh_prepared_call
        )

    @staticmethod
    def _build_submit_prepared_call_decision(
        *,
        decision_kind: str,
        allowed_to_submit: bool,
        submission_mode: str | None,
        reason: str,
        fresh_preflight: dict[str, Any],
        submit_result: GarageProcessingResult | None,
        stale_or_blocked: bool,
    ) -> dict[str, Any]:
        return {
            "decision_kind": decision_kind,
            "allowed_to_submit": allowed_to_submit,
            "submission_mode": submission_mode,
            "reason": reason,
            "prepared_call": fresh_preflight.get("prepared_call"),
            "submit_result": submit_result,
            "fresh_preflight": dict(fresh_preflight),
            "stale_or_blocked": stale_or_blocked,
            "missing_required_fields": tuple(
                fresh_preflight.get("missing_required_fields") or ()
            ),
            "context_only": bool(fresh_preflight.get("context_only")),
            "unavailable_in_slice": bool(fresh_preflight.get("unavailable_in_slice")),
            "productive_in_slice": (
                not bool(fresh_preflight.get("context_only"))
                and not bool(fresh_preflight.get("unavailable_in_slice"))
            ),
        }

    @staticmethod
    def _resolve_submission_mode(fresh_preflight: dict[str, Any] | None) -> str | None:
        if not isinstance(fresh_preflight, dict):
            return None
        if bool(fresh_preflight.get("context_only")):
            return "context_capture"
        if not bool(fresh_preflight.get("unavailable_in_slice")):
            return "productive_in_slice"
        return None

    @staticmethod
    def _resolve_result_task_id(
        validated_call: dict[str, Any],
        result: Any,
    ) -> str | None:
        task_id = validated_call.get("task_id")
        if isinstance(task_id, str):
            return task_id
        if isinstance(result, dict):
            result_task_id = result.get("task_id")
            if isinstance(result_task_id, str):
                return result_task_id
        return None

    def _enforce_supported_call_policy(self, call: dict[str, Any]) -> None:
        if self._state_reader is None:
            return
        evaluator = getattr(self._state_reader, "evaluate_supported_call_policy", None)
        if not callable(evaluator):
            return
        task_id = call.get("task_id")
        call_type = call.get("call_type")
        if not isinstance(task_id, str) or not isinstance(call_type, str):
            return
        if call_type in {"task.create", "plan.record"}:
            return
        policy = evaluator(
            task_id,
            call_type,
            job_id=str(call["job_id"]) if "job_id" in call else None,
            parent_job_id=(
                str(call["parent_job_id"]) if "parent_job_id" in call else None
            ),
        )
        if not isinstance(policy, dict) or policy.get("allowed", True):
            return
        hold_kind = policy.get("execution_hold_kind") or policy.get("dominant_target_kind")
        rejection_reason = policy.get("rejection_reason") or "call_not_allowed"
        best_next_move = policy.get("best_next_move")
        recommendation = ""
        if isinstance(best_next_move, dict):
            recommended_call = best_next_move.get("call_type")
            recommended_reason = best_next_move.get("reason")
            if isinstance(recommended_call, str):
                recommendation = (
                    f"; best supported next move is '{recommended_call}'"
                    + (
                        f" ({recommended_reason})"
                        if isinstance(recommended_reason, str) and recommended_reason
                        else ""
                    )
                )
        raise GarageAlfredProcessingError(
            f"{call_type} for task '{task_id}' is not allowed while execution is "
            f"held on '{hold_kind}' ({rejection_reason}){recommendation}"
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
        existing_task_record = self._existing_task_record(task_id)
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
        task_state = "running"
        if (
            isinstance(existing_task_record, dict)
            and existing_task_record.get("task_state") == "waiting_on_child"
            and existing_task_record.get("current_job_id") == job_id
        ):
            task_state = "waiting_on_child"
        task_record = self._build_task_record(
            task_id,
            recorded_at,
            task_state=task_state,
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
        elif status in {"in_progress", "needs_child_job"}:
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
            if not isinstance(required_kind, str) or not required_kind:
                return False
            return any(ref.get("kind") == required_kind for ref in artifact_refs)
        if rule_type == "result_present":
            return any(ref.get("kind") == "result-json" for ref in evidence_refs)
        if rule_type == "summary_present":
            return any(ref.get("kind") == "summary" for ref in evidence_refs)
        if rule_type == "evidence_bundle_present":
            minimum_count = params.get("minimum_count", params.get("min_count", 2))
            try:
                minimum_count = int(minimum_count)
            except Exception:
                return False
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
