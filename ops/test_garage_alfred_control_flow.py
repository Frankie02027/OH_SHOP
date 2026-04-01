"""Focused Alfred control-surface tests.

These tests cover the caller-facing route helpers and their flattened receipts
without mixing that surface audit into the storage durability matrix.
"""

from __future__ import annotations

import unittest

from ops.test_garage_fixtures import (
    GarageTempRootTestCase,
    make_checkpoint_create_call,
    make_child_job_request_call,
    make_continuation_record_call,
    make_job_start_call,
    make_plan_record_call,
    make_result_submit_call,
    make_summary_artifact_ref,
    make_task_create_call,
)


class GarageAlfredControlFlowTests(GarageTempRootTestCase):

    def _seed_review_needed_path(self, processor) -> None:
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Produce proof needing review",
                        "description": "Return evidence that still needs review.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "manual_review_required"},
                    },
                ],
            )
        )
        processor.process_call(
            make_result_submit_call(
                artifact_refs=[make_summary_artifact_ref()],
                reported_status="succeeded",
            )
        )
        processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref(artifact_id="T000001.J001.A002")],
            )
        )

    def _seed_artifact_required_path(self, processor) -> None:
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Need artifact proof",
                        "description": "Still needs an official artifact ref.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "artifact_exists"},
                    },
                ],
            )
        )
        processor.process_call(make_result_submit_call(reported_status="succeeded"))
        processor.process_call(make_checkpoint_create_call(plan_version=1))

    def _seed_active_leg_unavailable_path(self, processor) -> None:
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Produce required proof",
                        "description": "Return the artifact the next step depends on.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "artifact_exists"},
                    },
                    {
                        "item_id": "I003",
                        "title": "Resume dependent follow-up",
                        "description": "Continue once the predecessor is verified.",
                        "status": "todo",
                        "depends_on": ["I002"],
                    },
                ],
            )
        )
        processor.process_call(make_result_submit_call(reported_status="succeeded"))
        processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref()],
            )
        )
        processor.process_call(make_job_start_call())

    def _seed_fresh_productive_path(self, processor) -> None:
        processor.process_call(make_task_create_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Produce required proof",
                        "description": "Return the artifact the next step depends on.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "artifact_exists"},
                    },
                    {
                        "item_id": "I003",
                        "title": "Resume dependent follow-up",
                        "description": "Continue once the predecessor is verified.",
                        "status": "todo",
                        "depends_on": ["I002"],
                    },
                ],
            )
        )
        processor.process_call(make_result_submit_call(reported_status="succeeded"))
        processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref()],
            )
        )

    def _build_top_level_receipt_for_productive_continuation(self, processor):
        self._seed_artifact_required_path(processor)
        prior_attempt = processor.attempt_best_next_call_with_guarded_rebase(
            "T000001",
            expected={"expected_dominant_target_kind": "next-executable"},
            allowed_rebased={
                "allow_rebased_missing_input_candidate": True,
                "expected_rebased_call_type": "continuation.record",
                "expected_rebased_submission_mode": "productive_in_slice",
                "expected_rebased_follow_up_behavior_kind": "gather-proof-next",
            },
        )
        return processor.follow_current_honest_path(
            "T000001",
            final_receipt=prior_attempt["final_receipt"],
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/proof-top-level.md",
                    "role": "jarvis",
                }
            },
        )["top_level_final_receipt"]

    def _build_top_level_receipt_for_context_capture(self, processor):
        self._seed_review_needed_path(processor)
        prior_attempt = processor.attempt_best_next_call_with_guarded_rebase(
            "T000001",
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/review-top-level-seed.md",
                    "role": "jarvis",
                }
            },
            expected={
                "expected_dominant_target_kind": "review-needed",
                "expected_best_next_call_type": "continuation.record",
                "expected_follow_up_behavior_kind": "capture-review-context-next",
                "expected_submission_mode": "context_capture",
                "expected_context_only": True,
                "expected_productive_in_slice": False,
            },
            allowed_rebased={"allow_rebased_context_capture_candidate": True},
        )
        return processor.follow_current_honest_path(
            "T000001",
            final_receipt=prior_attempt["final_receipt"],
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/review-top-level.md",
                    "role": "jarvis",
                }
            },
        )["top_level_final_receipt"]

    def _drift_to_waiting_on_child(self, processor) -> None:
        processor.process_call(
            make_plan_record_call(
                plan_version=2,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Run child leg",
                        "description": "Delegate the blocking child work.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                    },
                ],
            )
        )
        processor.process_call(make_child_job_request_call())

    def test_follow_current_honest_path_routes_no_receipt_to_fresh_attempt(self) -> None:
        storage, processor = self._new_processor()
        self._seed_fresh_productive_path(processor)

        flow = processor.follow_current_honest_path("T000001")
        final_receipt = flow["top_level_final_receipt"]
        storage.close()

        self.assertEqual("attempt_best_next_call", flow["route_helper_name"])
        self.assertEqual(
            "fresh_attempt_productive_execution",
            final_receipt["top_level_final_path_kind"],
        )
        self.assertTrue(final_receipt["attempt_allowed"])
        self.assertTrue(final_receipt["productive_in_slice"])
        self.assertEqual("active-item", final_receipt["dominant_target_kind_now"])

    def test_follow_current_honest_path_supports_guarded_rebased_context_capture(
        self,
    ) -> None:
        storage, processor = self._new_processor()
        self._seed_review_needed_path(processor)

        flow = processor.follow_current_honest_path(
            "T000001",
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/review-top-level.md",
                    "role": "jarvis",
                }
            },
            expected={
                "expected_submission_mode": "productive_in_slice",
                "expected_productive_in_slice": True,
            },
            allowed_rebased={
                "allow_rebased_context_capture_candidate": True,
                "expected_rebased_call_type": "continuation.record",
                "expected_rebased_submission_mode": "context_capture",
                "expected_rebased_follow_up_behavior_kind": "capture-review-context-next",
            },
        )
        final_receipt = flow["top_level_final_receipt"]
        storage.close()

        self.assertEqual(
            "attempt_best_next_call_with_guarded_rebase",
            flow["route_helper_name"],
        )
        self.assertEqual(
            "guarded_rebased_context_capture",
            final_receipt["top_level_final_path_kind"],
        )
        self.assertTrue(final_receipt["context_capture_only"])
        self.assertFalse(final_receipt["productive_in_slice"])
        self.assertEqual("review-needed", final_receipt["dominant_target_kind_now"])

    def test_follow_current_honest_path_receipt_branch_supports_stale_rebased_progress(
        self,
    ) -> None:
        storage, processor = self._new_processor()
        prior_attempt = processor.attempt_best_next_call_with_guarded_rebase(
            "T000001",
            expected={"expected_best_next_call_type": "continuation.record"},
        )
        processor.process_call(make_job_start_call())
        processor.process_call(
            make_plan_record_call(
                plan_version=1,
                current_active_item="I002",
                items=[
                    {
                        "item_id": "I001",
                        "title": "Prepare runtime",
                        "description": "Set up the execution slice.",
                        "status": "verified",
                    },
                    {
                        "item_id": "I002",
                        "title": "Run child leg",
                        "description": "Delegate the blocking child work.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                    },
                ],
            )
        )
        processor.process_call(make_child_job_request_call())

        flow = processor.follow_current_honest_path(
            "T000001",
            final_receipt=prior_attempt["final_receipt"],
            allowed_rebased={
                "allow_rebased_productive_candidate": True,
                "expected_rebased_call_type": "job.start",
                "expected_rebased_submission_mode": "productive_in_slice",
                "expected_rebased_follow_up_behavior_kind": "progress-child-leg-next",
            },
        )
        final_receipt = flow["top_level_final_receipt"]
        storage.close()

        self.assertEqual(
            "continue_from_final_receipt_with_guarded_rebase",
            flow["route_helper_name"],
        )
        self.assertEqual(
            "receipt_stale_rebased_productive_execution",
            final_receipt["top_level_final_path_kind"],
        )
        self.assertTrue(final_receipt["stale_or_mismatch_refused"])
        self.assertTrue(final_receipt["productive_in_slice"])
        self.assertEqual("waiting-on-child", final_receipt["dominant_target_kind_now"])

    def test_follow_current_honest_path_distinguishes_missing_input_without_receipt(
        self,
    ) -> None:
        storage, processor = self._new_processor()
        self._seed_artifact_required_path(processor)

        flow = processor.follow_current_honest_path("T000001")
        final_receipt = flow["top_level_final_receipt"]
        storage.close()

        self.assertEqual(
            "fresh_attempt_missing_input_refused",
            final_receipt["top_level_final_path_kind"],
        )
        self.assertFalse(final_receipt["attempt_allowed"])
        self.assertEqual(("payload_ref",), final_receipt["missing_required_fields"])
        self.assertEqual("proof-gathering", final_receipt["dominant_target_kind_now"])

    def test_follow_current_honest_path_keeps_active_leg_unavailable_explicit(self) -> None:
        storage, processor = self._new_processor()
        self._seed_active_leg_unavailable_path(processor)

        flow = processor.follow_current_honest_path(
            "T000001",
            expected={"expected_dominant_target_kind": "active-item"},
        )
        final_receipt = flow["top_level_final_receipt"]
        storage.close()

        self.assertEqual("attempt_best_next_call_with_guards", flow["route_helper_name"])
        self.assertEqual(
            "guarded_attempt_unavailable_refused",
            final_receipt["top_level_final_path_kind"],
        )
        self.assertFalse(final_receipt["attempt_allowed"])
        self.assertTrue(final_receipt["unavailable_in_slice"])
        self.assertEqual("active-item", final_receipt["dominant_target_kind_now"])

    def test_continue_from_top_level_final_receipt_continues_productive_path(self) -> None:
        storage, processor = self._new_processor()
        top_level_final_receipt = self._build_top_level_receipt_for_productive_continuation(
            processor
        )

        continuation = processor.continue_from_top_level_final_receipt(
            "T000001",
            top_level_final_receipt=top_level_final_receipt,
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/proof-top-level-continued.md",
                    "role": "jarvis",
                }
            },
        )
        final_receipt = continuation["top_level_continuation_receipt"]
        storage.close()

        self.assertTrue(continuation["top_level_receipt_compatible"])
        self.assertEqual(
            "continue_from_final_receipt",
            continuation["continuation_route_helper_name"],
        )
        self.assertEqual(
            "top_level_receipt_continued_productive_execution",
            final_receipt["top_level_continuation_path_kind"],
        )
        self.assertTrue(final_receipt["attempt_allowed"])
        self.assertTrue(final_receipt["productive_in_slice"])
        self.assertEqual("proof-gathering", final_receipt["dominant_target_kind_now"])

    def test_continue_from_top_level_final_receipt_continues_context_capture_path(
        self,
    ) -> None:
        storage, processor = self._new_processor()
        top_level_final_receipt = self._build_top_level_receipt_for_context_capture(
            processor
        )

        continuation = processor.continue_from_top_level_final_receipt(
            "T000001",
            top_level_final_receipt=top_level_final_receipt,
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/review-top-level-continued.md",
                    "role": "jarvis",
                }
            },
        )
        final_receipt = continuation["top_level_continuation_receipt"]
        storage.close()

        self.assertTrue(continuation["top_level_receipt_compatible"])
        self.assertEqual(
            "top_level_receipt_continued_context_capture",
            final_receipt["top_level_continuation_path_kind"],
        )
        self.assertTrue(final_receipt["attempt_allowed"])
        self.assertTrue(final_receipt["context_capture_only"])
        self.assertFalse(final_receipt["productive_in_slice"])
        self.assertEqual("review-needed", final_receipt["dominant_target_kind_now"])

    def test_continue_from_top_level_final_receipt_supports_stale_rebased_progress(
        self,
    ) -> None:
        storage, processor = self._new_processor()
        top_level_final_receipt = self._build_top_level_receipt_for_productive_continuation(
            processor
        )
        self._drift_to_waiting_on_child(processor)

        continuation = processor.continue_from_top_level_final_receipt(
            "T000001",
            top_level_final_receipt=top_level_final_receipt,
            allowed_rebased={
                "allow_rebased_productive_candidate": True,
                "expected_rebased_call_type": "job.start",
                "expected_rebased_submission_mode": "productive_in_slice",
                "expected_rebased_follow_up_behavior_kind": "progress-child-leg-next",
            },
        )
        final_receipt = continuation["top_level_continuation_receipt"]
        storage.close()

        self.assertFalse(continuation["top_level_receipt_compatible"])
        self.assertEqual(
            "continue_from_final_receipt_with_guarded_rebase",
            continuation["continuation_route_helper_name"],
        )
        self.assertEqual(
            "top_level_receipt_stale_rebased_productive_execution",
            final_receipt["top_level_continuation_path_kind"],
        )
        self.assertTrue(final_receipt["rebase_allowed"])
        self.assertTrue(final_receipt["attempt_allowed"])
        self.assertTrue(final_receipt["productive_in_slice"])
        self.assertEqual("waiting-on-child", final_receipt["dominant_target_kind_now"])

    def test_follow_or_continue_current_honest_path_routes_no_receipt_to_follow_helper(
        self,
    ) -> None:
        storage, processor = self._new_processor()
        self._seed_fresh_productive_path(processor)

        universal = processor.follow_or_continue_current_honest_path("T000001")
        final_receipt = universal["universal_final_receipt"]
        storage.close()

        self.assertEqual(
            "follow_current_honest_path",
            universal["route_top_level_helper_name"],
        )
        self.assertFalse(universal["used_top_level_final_receipt"])
        self.assertEqual("follow_productive_execution", final_receipt["universal_path_kind"])
        self.assertTrue(final_receipt["attempt_allowed"])
        self.assertTrue(final_receipt["productive_in_slice"])
        self.assertEqual("active-item", final_receipt["dominant_target_kind_now"])

    def test_follow_or_continue_current_honest_path_routes_top_level_receipt_to_continue_helper(
        self,
    ) -> None:
        storage, processor = self._new_processor()
        top_level_final_receipt = self._build_top_level_receipt_for_context_capture(
            processor
        )

        universal = processor.follow_or_continue_current_honest_path(
            "T000001",
            top_level_final_receipt=top_level_final_receipt,
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/review-universal-continued.md",
                    "role": "jarvis",
                }
            },
        )
        final_receipt = universal["universal_final_receipt"]
        storage.close()

        self.assertEqual(
            "continue_from_top_level_final_receipt",
            universal["route_top_level_helper_name"],
        )
        self.assertTrue(universal["used_top_level_final_receipt"])
        self.assertEqual("continue_context_capture", final_receipt["universal_path_kind"])
        self.assertTrue(final_receipt["context_capture_only"])
        self.assertEqual("review-needed", final_receipt["dominant_target_kind_now"])

    def test_follow_or_continue_current_honest_path_distinguishes_missing_input_refusal(
        self,
    ) -> None:
        storage, processor = self._new_processor()
        self._seed_artifact_required_path(processor)

        universal = processor.follow_or_continue_current_honest_path("T000001")
        final_receipt = universal["universal_final_receipt"]
        storage.close()

        self.assertEqual("follow_missing_input_refused", final_receipt["universal_path_kind"])
        self.assertFalse(final_receipt["attempt_allowed"])
        self.assertEqual(("payload_ref",), final_receipt["missing_required_fields"])
        self.assertEqual("proof-gathering", final_receipt["dominant_target_kind_now"])

    def test_follow_or_continue_current_honest_path_distinguishes_stale_refusal(
        self,
    ) -> None:
        storage, processor = self._new_processor()
        top_level_final_receipt = self._build_top_level_receipt_for_productive_continuation(
            processor
        )
        self._drift_to_waiting_on_child(processor)

        universal = processor.follow_or_continue_current_honest_path(
            "T000001",
            top_level_final_receipt=top_level_final_receipt,
        )
        final_receipt = universal["universal_final_receipt"]
        storage.close()

        self.assertEqual(
            "continue_stale_or_mismatch_refused",
            final_receipt["universal_path_kind"],
        )
        self.assertFalse(final_receipt["attempt_allowed"])
        self.assertTrue(final_receipt["stale_or_mismatch_refused"])
        self.assertEqual("waiting-on-child", final_receipt["dominant_target_kind_now"])

    def test_follow_or_continue_current_honest_path_keeps_active_leg_unavailable_explicit(
        self,
    ) -> None:
        storage, processor = self._new_processor()
        self._seed_active_leg_unavailable_path(processor)

        universal = processor.follow_or_continue_current_honest_path(
            "T000001",
            expected={"expected_dominant_target_kind": "active-item"},
        )
        final_receipt = universal["universal_final_receipt"]
        storage.close()

        self.assertEqual("follow_unavailable_refused", final_receipt["universal_path_kind"])
        self.assertFalse(final_receipt["attempt_allowed"])
        self.assertTrue(final_receipt["unavailable_in_slice"])
        self.assertEqual("active-item", final_receipt["dominant_target_kind_now"])


if __name__ == "__main__":
    unittest.main()
