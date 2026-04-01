"""Prepared-call, guarded-attempt, and receipt-continuation flow tests."""

from __future__ import annotations

from ops.garage_storage import build_storage_backed_alfred_processor
from ops.test_garage_fixtures import (
    GarageTempRootTestCase,
    make_checkpoint_create_call,
    make_child_job_request_call,
    make_continuation_record_call,
    make_failure_report_call,
    make_job_start_call,
    make_plan_record_call,
    make_result_submit_call,
    make_summary_artifact_ref,
    make_task_create_call,
)


class GarageStorageFlowTests(GarageTempRootTestCase):
    def test_draft_preflight_reports_disallowed_and_ignored_fields_without_pretending_ready(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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

        preflight = processor.prepare_next_call_from_draft(
            "T000001",
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/continuation.md",
                    "role": "jarvis",
                },
                "schema_version": "v9.9",
                "content_ref": {"kind": "bad", "path": "/tmp/bad", "role": "jarvis"},
                "bogus": "ignored",
            },
        )
        storage.close()

        self.assertEqual("ready_to_submit", preflight["preflight_kind"])
        self.assertEqual(("payload_ref",), preflight["accepted_supplied_fields"])
        self.assertEqual(("bogus",), preflight["ignored_supplied_fields"])
        self.assertEqual(
            ("schema_version", "content_ref"),
            preflight["disallowed_supplied_fields"],
        )

    def test_submit_prepared_job_start_succeeds_when_fresh_state_still_allows_it(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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
        continuation = processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref()],
            )
        )
        prepared_call = continuation.result["post_call_guidance"]["next_call_preflight"][
            "prepared_call"
        ]

        decision = processor.submit_prepared_next_call(prepared_call=prepared_call)
        receipt = decision["submit_receipt"]
        storage.close()

        self.assertEqual("submitted", decision["decision_kind"])
        self.assertTrue(decision["allowed_to_submit"])
        self.assertEqual("productive_in_slice", decision["submission_mode"])
        self.assertTrue(decision["productive_in_slice"])
        self.assertFalse(decision["stale_or_blocked"])
        self.assertIsNotNone(decision["submit_result"])
        self.assertEqual("job.start", decision["submit_result"].call_type)
        self.assertEqual("active-item", decision["submit_result"].result["post_call_guidance"]["dominant_target_kind"])
        self.assertEqual("submitted", receipt["decision_kind"])
        self.assertEqual("productive_in_slice", receipt["submission_mode"])
        self.assertEqual("productive_execution_advanced", receipt["submit_effect_kind"])
        self.assertEqual("active-item", receipt["dominant_target_kind_now"])
        self.assertEqual("continue-active-execution", receipt["best_next_move_now"]["move_kind"])
        self.assertTrue(receipt["execution_allowed_now"])
        self.assertTrue(receipt["current_job_is_primary_focus_now"])

    def test_submit_prepared_job_start_rejects_stale_call_after_posture_changes(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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
        continuation = processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref()],
            )
        )
        prepared_call = continuation.result["post_call_guidance"]["next_call_preflight"][
            "prepared_call"
        ]
        processor.process_call(make_job_start_call())

        decision = processor.submit_prepared_next_call(prepared_call=prepared_call)
        receipt = decision["submit_receipt"]
        storage.close()

        self.assertEqual("stale_prepared_call", decision["decision_kind"])
        self.assertFalse(decision["allowed_to_submit"])
        self.assertIsNone(decision["submission_mode"])
        self.assertTrue(decision["stale_or_blocked"])
        self.assertIsNone(decision["submit_result"])
        self.assertEqual("unavailable_in_slice", decision["fresh_preflight"]["preflight_kind"])
        self.assertTrue(decision["unavailable_in_slice"])
        self.assertEqual("submission_refused_stale", receipt["submit_effect_kind"])
        self.assertEqual("active-item", receipt["dominant_target_kind_now"])
        self.assertEqual("continue-active-execution", receipt["best_next_move_now"]["move_kind"])
        self.assertTrue(receipt["execution_allowed_now"])

    def test_submit_prepared_proof_continuation_requires_real_content_before_submission(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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

        denied = processor.submit_prepared_next_call(task_id="T000001")
        submitted = processor.submit_prepared_next_call(
            task_id="T000001",
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/continuation.md",
                    "role": "jarvis",
                }
            },
        )
        storage.close()

        self.assertEqual("not_ready_missing_fields", denied["decision_kind"])
        self.assertFalse(denied["allowed_to_submit"])
        self.assertEqual("productive_in_slice", denied["submission_mode"])
        self.assertTrue(denied["productive_in_slice"])
        self.assertEqual(("payload_ref",), denied["missing_required_fields"])
        self.assertIsNone(denied["submit_result"])
        self.assertEqual(
            "submission_refused_missing_fields",
            denied["submit_receipt"]["submit_effect_kind"],
        )
        self.assertEqual("proof-gathering", denied["submit_receipt"]["dominant_target_kind_now"])
        self.assertEqual("submitted", submitted["decision_kind"])
        self.assertTrue(submitted["allowed_to_submit"])
        self.assertEqual("productive_in_slice", submitted["submission_mode"])
        self.assertTrue(submitted["productive_in_slice"])
        self.assertEqual("continuation.record", submitted["submit_result"].call_type)
        self.assertEqual(
            "proof-gathering",
            submitted["submit_result"].result["post_call_guidance"]["dominant_target_kind"],
        )

    def test_submit_prepared_review_context_call_stays_context_only(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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

        decision = processor.submit_prepared_next_call(
            task_id="T000001",
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/review.md",
                    "role": "jarvis",
                }
            },
        )
        receipt = decision["submit_receipt"]
        storage.close()

        self.assertEqual("submitted", decision["decision_kind"])
        self.assertTrue(decision["allowed_to_submit"])
        self.assertEqual("context_capture", decision["submission_mode"])
        self.assertFalse(decision["productive_in_slice"])
        self.assertTrue(decision["context_only"])
        self.assertIsNotNone(decision["submit_result"])
        self.assertEqual("continuation.record", decision["submit_result"].call_type)
        self.assertEqual(
            "review-needed",
            decision["submit_result"].result["post_call_guidance"]["dominant_target_kind"],
        )
        self.assertEqual(
            "capture-review-context-next",
            decision["submit_result"].result["post_call_guidance"]["immediate_follow_up"][
                "follow_up_behavior_kind"
            ],
        )
        self.assertEqual("submitted", receipt["decision_kind"])
        self.assertEqual("context_capture", receipt["submission_mode"])
        self.assertEqual(
            "posture_preserved_after_context_capture",
            receipt["submit_effect_kind"],
        )
        self.assertFalse(receipt["productive_in_slice"])
        self.assertTrue(receipt["context_capture_only"])
        self.assertEqual("review-needed", receipt["dominant_target_kind_now"])
        self.assertEqual(
            "capture-manual-review-context",
            receipt["best_next_move_now"]["move_kind"],
        )
        self.assertFalse(receipt["execution_allowed_now"])

    def test_submit_prepared_blocked_evidence_call_stays_context_only(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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
                        "title": "Collect blocked evidence",
                        "description": "Capture failure evidence for the blocked step.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                    },
                ],
            )
        )
        processor.process_call(
            make_failure_report_call(
                reported_status="blocked",
                artifact_refs=[make_summary_artifact_ref()],
            )
        )
        processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref(artifact_id="T000001.J001.A002")],
            )
        )

        decision = processor.submit_prepared_next_call(
            task_id="T000001",
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/blocked.md",
                    "role": "jarvis",
                }
            },
        )
        receipt = decision["submit_receipt"]
        storage.close()

        self.assertEqual("submitted", decision["decision_kind"])
        self.assertTrue(decision["allowed_to_submit"])
        self.assertEqual("context_capture", decision["submission_mode"])
        self.assertFalse(decision["productive_in_slice"])
        self.assertTrue(decision["context_only"])
        self.assertIsNotNone(decision["submit_result"])
        self.assertEqual("continuation.record", decision["submit_result"].call_type)
        self.assertEqual(
            "blocked-evidence-review",
            decision["submit_result"].result["post_call_guidance"]["dominant_target_kind"],
        )
        self.assertEqual(
            "capture-blocked-evidence-next",
            decision["submit_result"].result["post_call_guidance"]["immediate_follow_up"][
                "follow_up_behavior_kind"
            ],
        )
        self.assertEqual(
            "posture_preserved_after_context_capture",
            receipt["submit_effect_kind"],
        )
        self.assertFalse(receipt["productive_in_slice"])
        self.assertTrue(receipt["context_capture_only"])
        self.assertEqual("blocked-evidence-review", receipt["dominant_target_kind_now"])
        self.assertEqual(
            "capture-blocked-evidence",
            receipt["best_next_move_now"]["move_kind"],
        )

    def test_submit_prepared_review_context_capture_rejects_when_posture_becomes_stale(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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
                    {
                        "item_id": "I003",
                        "title": "Resume dependent follow-up",
                        "description": "Continue once the predecessor is settled.",
                        "status": "todo",
                        "depends_on": ["I002"],
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
        prepared_call = processor.prepare_next_call_from_draft(
            "T000001",
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/review.md",
                    "role": "jarvis",
                }
            },
        )["prepared_call"]
        processor.process_call(
            make_plan_record_call(
                plan_version=2,
                current_active_item="I003",
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
                        "status": "verified",
                        "depends_on": ["I001"],
                    },
                    {
                        "item_id": "I003",
                        "title": "Resume dependent follow-up",
                        "description": "Continue once the predecessor is settled.",
                        "status": "todo",
                        "depends_on": ["I002"],
                    },
                ],
            )
        )

        decision = processor.submit_prepared_next_call(prepared_call=prepared_call)
        receipt = decision["submit_receipt"]
        storage.close()

        self.assertEqual("stale_prepared_call", decision["decision_kind"])
        self.assertFalse(decision["allowed_to_submit"])
        self.assertTrue(decision["stale_or_blocked"])
        self.assertTrue(decision["productive_in_slice"])
        self.assertFalse(decision["context_only"])
        self.assertIsNone(decision["submit_result"])
        self.assertEqual("submission_refused_stale", receipt["submit_effect_kind"])
        self.assertEqual("next-executable", receipt["dominant_target_kind_now"])
        self.assertEqual("job.start", receipt["best_next_move_now"]["call_type"])

    def test_submit_prepared_child_job_start_rejects_when_child_leg_is_stale(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
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
        child = processor.process_call(make_child_job_request_call())
        prepared_call = child.result["post_call_guidance"]["next_call_preflight"]["prepared_call"]
        child_job_id = child.result["job_id"]
        processor.process_call(make_job_start_call(job_id=child_job_id))

        decision = processor.submit_prepared_next_call(prepared_call=prepared_call)
        receipt = decision["submit_receipt"]
        storage.close()

        self.assertEqual("stale_prepared_call", decision["decision_kind"])
        self.assertFalse(decision["allowed_to_submit"])
        self.assertIsNone(decision["submission_mode"])
        self.assertTrue(decision["stale_or_blocked"])
        self.assertIsNone(decision["submit_result"])
        self.assertEqual("unavailable_in_slice", decision["fresh_preflight"]["preflight_kind"])
        self.assertEqual("submission_refused_stale", receipt["submit_effect_kind"])
        self.assertEqual("waiting-on-child", receipt["dominant_target_kind_now"])

    def test_submit_prepared_call_does_not_fabricate_active_leg_path(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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

        decision = processor.submit_prepared_next_call(task_id="T000001")
        receipt = decision["submit_receipt"]
        storage.close()

        self.assertEqual("unavailable_in_slice", decision["decision_kind"])
        self.assertFalse(decision["allowed_to_submit"])
        self.assertIsNone(decision["submission_mode"])
        self.assertTrue(decision["unavailable_in_slice"])
        self.assertIsNone(decision["submit_result"])
        self.assertEqual("submission_refused_unavailable", receipt["submit_effect_kind"])
        self.assertEqual("active-item", receipt["dominant_target_kind_now"])
        self.assertEqual("continue-active-execution", receipt["best_next_move_now"]["move_kind"])

    def test_attempt_best_next_call_submits_ready_job_start(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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

        attempt = processor.attempt_best_next_call("T000001")
        receipt = attempt["submit_receipt"]
        storage.close()

        self.assertEqual("attempted_productive_execution", attempt["attempt_kind"])
        self.assertEqual("job.start", attempt["attempted_call_type"])
        self.assertEqual("productive_in_slice", attempt["attempted_submission_mode"])
        self.assertEqual("job.start", attempt["best_next_move"]["call_type"])
        self.assertTrue(attempt["attempt_allowed"])
        self.assertFalse(attempt["requires_additional_user_or_agent_input"])
        self.assertTrue(attempt["formed_concrete_call"])
        self.assertFalse(attempt["context_capture_only"])
        self.assertFalse(attempt["unavailable_in_slice"])
        self.assertIsNotNone(receipt)
        self.assertEqual("productive_execution_advanced", receipt["submit_effect_kind"])
        self.assertEqual("active-item", receipt["dominant_target_kind_now"])

    def test_attempt_best_next_call_refuses_proof_gathering_until_content_exists(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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

        attempt = processor.attempt_best_next_call("T000001")
        receipt = attempt["submit_receipt"]
        storage.close()

        self.assertEqual("attempt_refused_missing_fields", attempt["attempt_kind"])
        self.assertEqual("continuation.record", attempt["attempted_call_type"])
        self.assertEqual("attach-artifact-ref", attempt["best_next_move"]["move_kind"])
        self.assertFalse(attempt["attempt_allowed"])
        self.assertEqual(("payload_ref",), attempt["missing_required_fields"])
        self.assertTrue(attempt["requires_additional_user_or_agent_input"])
        self.assertFalse(attempt["formed_concrete_call"])
        self.assertFalse(attempt["context_capture_only"])
        self.assertFalse(attempt["unavailable_in_slice"])
        self.assertIsNotNone(receipt)
        self.assertEqual("submission_refused_missing_fields", receipt["submit_effect_kind"])
        self.assertEqual("proof-gathering", receipt["dominant_target_kind_now"])

    def test_attempt_best_next_call_submits_review_context_capture_when_content_present(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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

        attempt = processor.attempt_best_next_call(
            "T000001",
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/review.md",
                    "role": "jarvis",
                }
            },
        )
        receipt = attempt["submit_receipt"]
        storage.close()

        self.assertEqual("attempted_context_capture", attempt["attempt_kind"])
        self.assertEqual("continuation.record", attempt["attempted_call_type"])
        self.assertEqual("context_capture", attempt["attempted_submission_mode"])
        self.assertEqual("capture-review-context-next", attempt["follow_up_behavior_kind"])
        self.assertTrue(attempt["attempt_allowed"])
        self.assertTrue(attempt["formed_concrete_call"])
        self.assertTrue(attempt["context_capture_only"])
        self.assertFalse(attempt["productive_in_slice"])
        self.assertFalse(attempt["unavailable_in_slice"])
        self.assertIsNotNone(receipt)
        self.assertEqual("context_capture", receipt["submission_mode"])
        self.assertEqual(
            "posture_preserved_after_context_capture",
            receipt["submit_effect_kind"],
        )
        self.assertEqual("review-needed", receipt["dominant_target_kind_now"])

    def test_attempt_best_next_call_submits_blocked_evidence_context_capture_when_content_present(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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
                        "title": "Collect blocked evidence",
                        "description": "Capture failure evidence for the blocked step.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                    },
                ],
            )
        )
        processor.process_call(
            make_failure_report_call(
                reported_status="blocked",
                artifact_refs=[make_summary_artifact_ref()],
            )
        )
        processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref(artifact_id="T000001.J001.A002")],
            )
        )

        attempt = processor.attempt_best_next_call(
            "T000001",
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/blocked.md",
                    "role": "jarvis",
                }
            },
        )
        receipt = attempt["submit_receipt"]
        storage.close()

        self.assertEqual("attempted_context_capture", attempt["attempt_kind"])
        self.assertEqual("continuation.record", attempt["attempted_call_type"])
        self.assertEqual("context_capture", attempt["attempted_submission_mode"])
        self.assertEqual("capture-blocked-evidence-next", attempt["follow_up_behavior_kind"])
        self.assertTrue(attempt["attempt_allowed"])
        self.assertTrue(attempt["formed_concrete_call"])
        self.assertTrue(attempt["context_capture_only"])
        self.assertFalse(attempt["productive_in_slice"])
        self.assertFalse(attempt["unavailable_in_slice"])
        self.assertIsNotNone(receipt)
        self.assertEqual(
            "posture_preserved_after_context_capture",
            receipt["submit_effect_kind"],
        )
        self.assertEqual("blocked-evidence-review", receipt["dominant_target_kind_now"])

    def test_attempt_best_next_call_submits_child_job_start_only_when_startable(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
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

        attempt = processor.attempt_best_next_call("T000001")
        receipt = attempt["submit_receipt"]
        storage.close()

        self.assertEqual("attempted_productive_execution", attempt["attempt_kind"])
        self.assertEqual("job.start", attempt["attempted_call_type"])
        self.assertTrue(attempt["attempt_allowed"])
        self.assertTrue(attempt["formed_concrete_call"])
        self.assertIsNotNone(receipt)
        self.assertEqual("submitted", receipt["decision_kind"])
        self.assertEqual("job.start", receipt["submit_result"].call_type)

    def test_attempt_best_next_call_does_not_fabricate_active_leg_path(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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

        attempt = processor.attempt_best_next_call("T000001")
        receipt = attempt["submit_receipt"]
        storage.close()

        self.assertEqual("attempt_refused_unavailable", attempt["attempt_kind"])
        self.assertIsNone(attempt["attempted_call_type"])
        self.assertFalse(attempt["attempt_allowed"])
        self.assertFalse(attempt["formed_concrete_call"])
        self.assertTrue(attempt["unavailable_in_slice"])
        self.assertIsNotNone(receipt)
        self.assertEqual("submission_refused_unavailable", receipt["submit_effect_kind"])
        self.assertEqual("active-item", receipt["dominant_target_kind_now"])

    def test_guarded_attempt_best_next_job_start_succeeds_when_expectations_match(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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

        attempt = processor.attempt_best_next_call_with_guards(
            "T000001",
            expected={
                "expected_dominant_target_kind": "next-executable",
                "expected_best_next_call_type": "job.start",
                "expected_follow_up_behavior_kind": "start-next-executable-next",
                "expected_submission_mode": "productive_in_slice",
                "expected_context_only": False,
                "expected_productive_in_slice": True,
            },
        )
        receipt = attempt["submit_receipt"]
        storage.close()

        self.assertTrue(attempt["guard_match"])
        self.assertIsNone(attempt["guard_failure_kind"])
        self.assertEqual("attempted_productive_execution", attempt["attempt_kind"])
        self.assertTrue(attempt["attempt_allowed"])
        self.assertEqual("job.start", attempt["attempted_call_type"])
        self.assertEqual("job.start", attempt["actual"]["best_next_call_type"])
        self.assertIsNotNone(receipt)
        self.assertEqual("submitted", receipt["decision_kind"])

    def test_guarded_attempt_refuses_when_best_next_call_type_changed(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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

        attempt = processor.attempt_best_next_call_with_guards(
            "T000001",
            expected={"expected_best_next_call_type": "continuation.record"},
        )
        storage.close()

        self.assertFalse(attempt["guard_match"])
        self.assertEqual("guard_mismatch_refused", attempt["attempt_kind"])
        self.assertEqual("best_next_call_type_mismatch", attempt["guard_failure_kind"])
        self.assertFalse(attempt["attempt_allowed"])
        self.assertEqual("job.start", attempt["actual"]["best_next_call_type"])
        self.assertIsNone(attempt["submit_receipt"])
        self.assertEqual(
            "productive_replacement_candidate",
            attempt["rebased_candidate_kind"],
        )
        self.assertEqual("job.start", attempt["rebased_best_next_move"]["call_type"])
        self.assertEqual(
            "ready_to_submit",
            attempt["rebased_next_call_preflight"]["preflight_kind"],
        )

    def test_guarded_attempt_refuses_when_dominant_target_changed(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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

        attempt = processor.attempt_best_next_call_with_guards(
            "T000001",
            expected={"expected_dominant_target_kind": "next-executable"},
        )
        storage.close()

        self.assertFalse(attempt["guard_match"])
        self.assertEqual("guard_mismatch_refused", attempt["attempt_kind"])
        self.assertEqual("dominant_target_kind_mismatch", attempt["guard_failure_kind"])
        self.assertFalse(attempt["attempt_allowed"])
        self.assertEqual("active-item", attempt["actual"]["dominant_target_kind"])
        self.assertIsNone(attempt["submit_receipt"])
        self.assertEqual(
            "unavailable_replacement_candidate",
            attempt["rebased_candidate_kind"],
        )
        self.assertEqual(
            "continue-active-execution",
            attempt["rebased_best_next_move"]["move_kind"],
        )
        self.assertEqual(
            "unavailable_in_slice",
            attempt["rebased_next_call_preflight"]["preflight_kind"],
        )

    def test_guarded_attempt_refuses_when_productive_expected_but_context_capture_is_current(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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

        attempt = processor.attempt_best_next_call_with_guards(
            "T000001",
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/review.md",
                    "role": "jarvis",
                }
            },
            expected={
                "expected_submission_mode": "productive_in_slice",
                "expected_productive_in_slice": True,
            },
        )
        storage.close()

        self.assertFalse(attempt["guard_match"])
        self.assertEqual("guard_mismatch_refused", attempt["attempt_kind"])
        self.assertEqual("submission_mode_mismatch", attempt["guard_failure_kind"])
        self.assertFalse(attempt["attempt_allowed"])
        self.assertEqual("context_capture", attempt["actual"]["submission_mode"])
        self.assertTrue(attempt["actual"]["context_only"])
        self.assertIsNone(attempt["submit_receipt"])
        self.assertEqual(
            "context_capture_replacement_candidate",
            attempt["rebased_candidate_kind"],
        )
        self.assertEqual(
            "capture-review-context-next",
            attempt["rebased_follow_up_behavior"]["follow_up_behavior_kind"],
        )
        self.assertEqual(
            "continuation.record",
            attempt["rebased_next_call_hint"]["recommended_call_type"],
        )
        self.assertEqual(
            "context_only_not_submittable",
            attempt["rebased_next_call_preflight"]["preflight_kind"],
        )

    def test_guarded_context_capture_attempt_succeeds_when_expectations_match(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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

        attempt = processor.attempt_best_next_call_with_guards(
            "T000001",
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/review.md",
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
        )
        receipt = attempt["submit_receipt"]
        storage.close()

        self.assertTrue(attempt["guard_match"])
        self.assertEqual("attempted_context_capture", attempt["attempt_kind"])
        self.assertTrue(attempt["attempt_allowed"])
        self.assertTrue(attempt["context_capture_only"])
        self.assertFalse(attempt["productive_in_slice"])
        self.assertIsNotNone(receipt)
        self.assertEqual("context_capture", receipt["submission_mode"])
        self.assertEqual("review-needed", receipt["dominant_target_kind_now"])

    def test_guarded_attempt_proof_missing_content_still_refuses_when_guards_match(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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

        attempt = processor.attempt_best_next_call_with_guards(
            "T000001",
            expected={
                "expected_dominant_target_kind": "proof-gathering",
                "expected_best_next_call_type": "continuation.record",
                "expected_follow_up_behavior_kind": "gather-proof-next",
                "expected_submission_mode": "productive_in_slice",
                "expected_context_only": False,
                "expected_productive_in_slice": True,
            },
        )
        receipt = attempt["submit_receipt"]
        storage.close()

        self.assertTrue(attempt["guard_match"])
        self.assertEqual("attempt_refused_missing_fields", attempt["attempt_kind"])
        self.assertFalse(attempt["attempt_allowed"])
        self.assertEqual(("payload_ref",), attempt["missing_required_fields"])
        self.assertTrue(attempt["requires_additional_user_or_agent_input"])
        self.assertIsNotNone(receipt)
        self.assertEqual("submission_refused_missing_fields", receipt["submit_effect_kind"])

    def test_guarded_attempt_does_not_fabricate_active_leg_path_even_when_guard_matches(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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

        attempt = processor.attempt_best_next_call_with_guards(
            "T000001",
            expected={"expected_dominant_target_kind": "active-item"},
        )
        receipt = attempt["submit_receipt"]
        storage.close()

        self.assertTrue(attempt["guard_match"])
        self.assertEqual("attempt_refused_unavailable", attempt["attempt_kind"])
        self.assertFalse(attempt["attempt_allowed"])
        self.assertTrue(attempt["unavailable_in_slice"])
        self.assertIsNotNone(receipt)
        self.assertEqual("submission_refused_unavailable", receipt["submit_effect_kind"])

    def test_guarded_attempt_context_mismatch_rebases_without_auto_attempting_replacement(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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
        before_summary = storage.latest_task_state_summary("T000001")

        attempt = processor.attempt_best_next_call_with_guards(
            "T000001",
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/review.md",
                    "role": "jarvis",
                }
            },
            expected={"expected_submission_mode": "productive_in_slice"},
        )
        after_summary = storage.latest_task_state_summary("T000001")
        storage.close()

        self.assertFalse(attempt["guard_match"])
        self.assertIsNone(attempt["submit_receipt"])
        self.assertEqual(
            before_summary["event_count"],
            after_summary["event_count"],
        )
        self.assertEqual(
            before_summary["latest_event"]["event_id"],
            after_summary["latest_event"]["event_id"],
        )

    def test_guarded_rebase_can_attempt_productive_replacement_only_when_approved(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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

        attempt = processor.attempt_best_next_call_with_guarded_rebase(
            "T000001",
            expected={"expected_best_next_call_type": "continuation.record"},
            allowed_rebased={
                "allow_rebased_productive_candidate": True,
                "expected_rebased_call_type": "job.start",
                "expected_rebased_submission_mode": "productive_in_slice",
                "expected_rebased_follow_up_behavior_kind": "start-next-executable-next",
            },
        )
        receipt = attempt["submit_receipt"]
        final_receipt = attempt["final_receipt"]
        storage.close()

        self.assertFalse(attempt["guard_match"])
        self.assertTrue(attempt["rebase_considered"])
        self.assertTrue(attempt["rebase_allowed"])
        self.assertEqual(
            "rebased_attempted_productive_execution",
            attempt["attempt_kind"],
        )
        self.assertTrue(attempt["attempt_allowed"])
        self.assertEqual("job.start", attempt["attempted_call_type"])
        self.assertIsNotNone(receipt)
        self.assertEqual("submitted", receipt["decision_kind"])
        self.assertEqual("productive_in_slice", receipt["submission_mode"])
        self.assertEqual(
            "guard_mismatch_rebased_productive_execution",
            final_receipt["final_attempt_path_kind"],
        )
        self.assertFalse(final_receipt["original_guard_match"])
        self.assertTrue(final_receipt["rebase_considered"])
        self.assertTrue(final_receipt["rebase_allowed"])
        self.assertTrue(final_receipt["final_attempt_allowed"])
        self.assertEqual("job.start", final_receipt["attempted_call_type"])
        self.assertEqual(
            "productive_in_slice",
            final_receipt["attempted_submission_mode"],
        )
        self.assertEqual("active-item", final_receipt["dominant_target_kind_now"])
        self.assertEqual(
            "continue-active-execution",
            final_receipt["best_next_move_now"]["move_kind"],
        )

    def test_guarded_rebase_can_attempt_context_capture_replacement_only_when_approved(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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

        attempt = processor.attempt_best_next_call_with_guarded_rebase(
            "T000001",
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/review.md",
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
        receipt = attempt["submit_receipt"]
        final_receipt = attempt["final_receipt"]
        storage.close()

        self.assertFalse(attempt["guard_match"])
        self.assertTrue(attempt["rebase_considered"])
        self.assertTrue(attempt["rebase_allowed"])
        self.assertEqual("rebased_attempted_context_capture", attempt["attempt_kind"])
        self.assertTrue(attempt["attempt_allowed"])
        self.assertTrue(attempt["context_capture_only"])
        self.assertFalse(attempt["productive_in_slice"])
        self.assertIsNotNone(receipt)
        self.assertEqual("context_capture", receipt["submission_mode"])
        self.assertEqual(
            "guard_mismatch_rebased_context_capture",
            final_receipt["final_attempt_path_kind"],
        )
        self.assertFalse(final_receipt["original_guard_match"])
        self.assertTrue(final_receipt["rebase_considered"])
        self.assertTrue(final_receipt["rebase_allowed"])
        self.assertTrue(final_receipt["final_attempt_allowed"])
        self.assertTrue(final_receipt["context_capture_only"])
        self.assertFalse(final_receipt["productive_in_slice"])
        self.assertEqual(
            "context_capture",
            final_receipt["attempted_submission_mode"],
        )
        self.assertEqual("review-needed", final_receipt["dominant_target_kind_now"])
        self.assertEqual(
            "capture-manual-review-context",
            final_receipt["best_next_move_now"]["move_kind"],
        )

    def test_guarded_rebase_can_attempt_blocked_evidence_context_capture_when_approved(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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
                        "title": "Collect blocked evidence",
                        "description": "Capture failure evidence for the blocked step.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                    },
                ],
            )
        )
        processor.process_call(
            make_failure_report_call(
                reported_status="blocked",
                artifact_refs=[make_summary_artifact_ref()],
            )
        )
        processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref(artifact_id="T000001.J001.A002")],
            )
        )

        attempt = processor.attempt_best_next_call_with_guarded_rebase(
            "T000001",
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/blocked.md",
                    "role": "jarvis",
                }
            },
            expected={"expected_submission_mode": "productive_in_slice"},
            allowed_rebased={
                "allow_rebased_context_capture_candidate": True,
                "expected_rebased_call_type": "continuation.record",
                "expected_rebased_submission_mode": "context_capture",
                "expected_rebased_follow_up_behavior_kind": "capture-blocked-evidence-next",
            },
        )
        receipt = attempt["submit_receipt"]
        final_receipt = attempt["final_receipt"]
        storage.close()

        self.assertFalse(attempt["guard_match"])
        self.assertTrue(attempt["rebase_considered"])
        self.assertTrue(attempt["rebase_allowed"])
        self.assertEqual("rebased_attempted_context_capture", attempt["attempt_kind"])
        self.assertTrue(attempt["attempt_allowed"])
        self.assertTrue(attempt["context_capture_only"])
        self.assertFalse(attempt["productive_in_slice"])
        self.assertIsNotNone(receipt)
        self.assertEqual("context_capture", receipt["submission_mode"])
        self.assertEqual(
            "guard_mismatch_rebased_context_capture",
            final_receipt["final_attempt_path_kind"],
        )
        self.assertTrue(final_receipt["context_capture_only"])
        self.assertFalse(final_receipt["productive_in_slice"])
        self.assertEqual(
            "context_capture",
            final_receipt["attempted_submission_mode"],
        )
        self.assertEqual(
            "blocked-evidence-review",
            final_receipt["dominant_target_kind_now"],
        )
        self.assertEqual(
            "capture-blocked-evidence",
            final_receipt["best_next_move_now"]["move_kind"],
        )

    def test_guarded_rebase_refuses_when_replacement_falls_outside_approved_conditions(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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

        attempt = processor.attempt_best_next_call_with_guarded_rebase(
            "T000001",
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/review.md",
                    "role": "jarvis",
                }
            },
            expected={"expected_submission_mode": "productive_in_slice"},
            allowed_rebased={"allow_rebased_productive_candidate": True},
        )
        final_receipt = attempt["final_receipt"]
        storage.close()

        self.assertFalse(attempt["guard_match"])
        self.assertTrue(attempt["rebase_considered"])
        self.assertFalse(attempt["rebase_allowed"])
        self.assertEqual("rebased_candidate_not_approved", attempt["rebase_failure_kind"])
        self.assertFalse(attempt["attempt_allowed"])
        self.assertIsNone(attempt["submit_receipt"])
        self.assertEqual(
            "guard_mismatch_rebase_refused",
            final_receipt["final_attempt_path_kind"],
        )
        self.assertFalse(final_receipt["original_guard_match"])
        self.assertTrue(final_receipt["rebase_considered"])
        self.assertFalse(final_receipt["rebase_allowed"])
        self.assertFalse(final_receipt["final_attempt_allowed"])
        self.assertEqual(
            "rebased_candidate_not_approved",
            final_receipt["rebase_failure_kind"],
        )
        self.assertEqual("review-needed", final_receipt["dominant_target_kind_now"])

    def test_guarded_rebase_missing_input_candidate_returns_clean_needs_input_result(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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

        attempt = processor.attempt_best_next_call_with_guarded_rebase(
            "T000001",
            expected={"expected_dominant_target_kind": "next-executable"},
            allowed_rebased={
                "allow_rebased_missing_input_candidate": True,
                "expected_rebased_call_type": "continuation.record",
                "expected_rebased_submission_mode": "productive_in_slice",
                "expected_rebased_follow_up_behavior_kind": "gather-proof-next",
            },
        )
        receipt = attempt["submit_receipt"]
        final_receipt = attempt["final_receipt"]
        storage.close()

        self.assertFalse(attempt["guard_match"])
        self.assertTrue(attempt["rebase_considered"])
        self.assertTrue(attempt["rebase_allowed"])
        self.assertEqual(
            "rebased_attempt_refused_missing_fields",
            attempt["attempt_kind"],
        )
        self.assertFalse(attempt["attempt_allowed"])
        self.assertEqual(("payload_ref",), attempt["missing_required_fields"])
        self.assertTrue(attempt["requires_additional_user_or_agent_input"])
        self.assertIsNotNone(receipt)
        self.assertEqual("submission_refused_missing_fields", receipt["submit_effect_kind"])
        self.assertEqual(
            "guard_mismatch_rebased_missing_input_refused",
            final_receipt["final_attempt_path_kind"],
        )
        self.assertFalse(final_receipt["final_attempt_allowed"])
        self.assertEqual(("payload_ref",), final_receipt["missing_required_fields"])
        self.assertTrue(final_receipt["requires_additional_user_or_agent_input"])
        self.assertEqual("proof-gathering", final_receipt["dominant_target_kind_now"])
        self.assertEqual(
            "attach-artifact-ref",
            final_receipt["best_next_move_now"]["move_kind"],
        )

    def test_guarded_rebase_unavailable_candidate_still_refuses_cleanly(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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

        attempt = processor.attempt_best_next_call_with_guarded_rebase(
            "T000001",
            expected={"expected_dominant_target_kind": "next-executable"},
            allowed_rebased={"allow_rebased_productive_candidate": True},
        )
        final_receipt = attempt["final_receipt"]
        storage.close()

        self.assertFalse(attempt["guard_match"])
        self.assertTrue(attempt["rebase_considered"])
        self.assertFalse(attempt["rebase_allowed"])
        self.assertEqual("rebased_candidate_unavailable", attempt["rebase_failure_kind"])
        self.assertFalse(attempt["attempt_allowed"])
        self.assertIsNone(attempt["submit_receipt"])
        self.assertEqual(
            "guard_mismatch_rebased_unavailable_refused",
            final_receipt["final_attempt_path_kind"],
        )
        self.assertFalse(final_receipt["final_attempt_allowed"])
        self.assertTrue(final_receipt["unavailable_in_slice"])
        self.assertEqual("active-item", final_receipt["dominant_target_kind_now"])
        self.assertEqual(
            "continue-active-execution",
            final_receipt["best_next_move_now"]["move_kind"],
        )

    def test_guarded_rebase_can_attempt_waiting_on_child_productive_replacement_when_approved(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
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

        attempt = processor.attempt_best_next_call_with_guarded_rebase(
            "T000001",
            expected={"expected_dominant_target_kind": "next-executable"},
            allowed_rebased={
                "allow_rebased_productive_candidate": True,
                "expected_rebased_call_type": "job.start",
                "expected_rebased_submission_mode": "productive_in_slice",
            },
        )
        receipt = attempt["submit_receipt"]
        final_receipt = attempt["final_receipt"]
        storage.close()

        self.assertFalse(attempt["guard_match"])
        self.assertTrue(attempt["rebase_considered"])
        self.assertTrue(attempt["rebase_allowed"])
        self.assertEqual(
            "rebased_attempted_productive_execution",
            attempt["attempt_kind"],
        )
        self.assertEqual("job.start", attempt["attempted_call_type"])
        self.assertIsNotNone(receipt)
        self.assertEqual("submitted", receipt["decision_kind"])
        self.assertEqual(
            "guard_mismatch_rebased_productive_execution",
            final_receipt["final_attempt_path_kind"],
        )
        self.assertTrue(final_receipt["final_attempt_allowed"])
        self.assertEqual("job.start", final_receipt["attempted_call_type"])
        self.assertEqual(
            "waiting-on-child",
            final_receipt["dominant_target_kind_now"],
        )
        self.assertEqual(
            "progress-child-leg",
            final_receipt["best_next_move_now"]["move_kind"],
        )

    def test_guarded_rebase_original_match_returns_flattened_productive_receipt(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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

        attempt = processor.attempt_best_next_call_with_guarded_rebase(
            "T000001",
            expected={
                "expected_dominant_target_kind": "next-executable",
                "expected_best_next_call_type": "job.start",
                "expected_follow_up_behavior_kind": "start-next-executable-next",
                "expected_submission_mode": "productive_in_slice",
                "expected_context_only": False,
                "expected_productive_in_slice": True,
            },
        )
        receipt = attempt["submit_receipt"]
        final_receipt = attempt["final_receipt"]
        storage.close()

        self.assertTrue(attempt["guard_match"])
        self.assertFalse(final_receipt["rebase_considered"])
        self.assertIsNone(final_receipt["rebase_allowed"])
        self.assertEqual(
            "original_guarded_attempt_productive_execution",
            final_receipt["final_attempt_path_kind"],
        )
        self.assertTrue(final_receipt["final_attempt_allowed"])
        self.assertEqual("job.start", final_receipt["attempted_call_type"])
        self.assertEqual(
            "productive_in_slice",
            final_receipt["attempted_submission_mode"],
        )
        self.assertEqual("active-item", final_receipt["dominant_target_kind_now"])
        self.assertEqual(
            "continue-active-execution",
            final_receipt["best_next_move_now"]["move_kind"],
        )
        self.assertIsNotNone(receipt)
        self.assertEqual("submitted", receipt["decision_kind"])

    def test_guarded_rebase_active_leg_still_returns_flattened_unavailable_receipt(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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

        attempt = processor.attempt_best_next_call_with_guarded_rebase(
            "T000001",
            expected={
                "expected_dominant_target_kind": "active-item",
                "expected_context_only": False,
                "expected_productive_in_slice": False,
            },
            allowed_rebased={"allow_rebased_productive_candidate": True},
        )
        final_receipt = attempt["final_receipt"]
        receipt = attempt["submit_receipt"]
        storage.close()

        self.assertTrue(attempt["guard_match"])
        self.assertFalse(attempt["attempt_allowed"])
        self.assertIsNotNone(receipt)
        self.assertEqual("submission_refused_unavailable", receipt["submit_effect_kind"])
        self.assertEqual(
            "guard_match_unavailable_refused",
            final_receipt["final_attempt_path_kind"],
        )
        self.assertTrue(final_receipt["original_guard_match"])
        self.assertFalse(final_receipt["final_attempt_allowed"])
        self.assertTrue(final_receipt["unavailable_in_slice"])
        self.assertEqual("active-item", final_receipt["dominant_target_kind_now"])
        self.assertEqual(
            "continue-active-execution",
            final_receipt["best_next_move_now"]["move_kind"],
        )

    def test_continue_from_final_receipt_can_resume_missing_input_when_content_added(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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

        continuation = processor.continue_from_final_receipt(
            "T000001",
            final_receipt=prior_attempt["final_receipt"],
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/proof.md",
                    "role": "jarvis",
                }
            },
        )
        final_receipt = continuation["continuation_final_receipt"]
        storage.close()

        self.assertEqual(
            "guard_mismatch_rebased_missing_input_refused",
            continuation["prior_final_attempt_path_kind"],
        )
        self.assertTrue(continuation["prior_receipt_compatible"])
        self.assertTrue(continuation["supplied_fields_resolved_missing_input"])
        self.assertEqual(
            "continued_productive_execution",
            continuation["continuation_kind"],
        )
        self.assertTrue(continuation["attempt_allowed"])
        self.assertEqual("continuation.record", continuation["attempted_call_type"])
        self.assertEqual(
            "productive_in_slice",
            continuation["attempted_submission_mode"],
        )
        self.assertIsNotNone(continuation["submit_receipt"])
        self.assertEqual(
            "submitted",
            continuation["submit_receipt"]["decision_kind"],
        )
        self.assertIsNotNone(continuation["final_receipt"])
        self.assertEqual(
            "continued_productive_execution",
            final_receipt["continuation_final_path_kind"],
        )
        self.assertTrue(final_receipt["prior_receipt_compatible"])
        self.assertTrue(final_receipt["attempt_allowed"])
        self.assertEqual("continuation.record", final_receipt["attempted_call_type"])
        self.assertEqual(
            "productive_in_slice",
            final_receipt["attempted_submission_mode"],
        )
        self.assertTrue(final_receipt["productive_in_slice"])
        self.assertFalse(final_receipt["context_capture_only"])
        self.assertFalse(final_receipt["unavailable_in_slice"])
        self.assertEqual("proof-gathering", final_receipt["dominant_target_kind_now"])
        self.assertEqual(
            "attach-artifact-ref",
            final_receipt["best_next_move_now"]["move_kind"],
        )

    def test_continue_from_final_receipt_can_continue_review_context_capture_when_compatible(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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

        prior_attempt = processor.attempt_best_next_call_with_guarded_rebase(
            "T000001",
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/review.md",
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

        continuation = processor.continue_from_final_receipt(
            "T000001",
            final_receipt=prior_attempt["final_receipt"],
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/review-2.md",
                    "role": "jarvis",
                }
            },
        )
        final_receipt = continuation["continuation_final_receipt"]
        storage.close()

        self.assertEqual(
            "guard_mismatch_rebased_context_capture",
            continuation["prior_final_attempt_path_kind"],
        )
        self.assertTrue(continuation["prior_receipt_compatible"])
        self.assertEqual(
            "continued_context_capture",
            continuation["continuation_kind"],
        )
        self.assertTrue(continuation["attempt_allowed"])
        self.assertEqual("continuation.record", continuation["attempted_call_type"])
        self.assertEqual("context_capture", continuation["attempted_submission_mode"])
        self.assertEqual("review-needed", continuation["fresh_dominant_target_kind"])
        self.assertEqual(
            "capture-review-context-next",
            continuation["fresh_follow_up_behavior_kind"],
        )
        self.assertIsNotNone(continuation["submit_receipt"])
        self.assertEqual(
            "context_capture",
            continuation["submit_receipt"]["submission_mode"],
        )
        self.assertEqual(
            "continued_context_capture",
            final_receipt["continuation_final_path_kind"],
        )
        self.assertTrue(final_receipt["prior_receipt_compatible"])
        self.assertTrue(final_receipt["attempt_allowed"])
        self.assertEqual(
            "context_capture",
            final_receipt["attempted_submission_mode"],
        )
        self.assertFalse(final_receipt["productive_in_slice"])
        self.assertTrue(final_receipt["context_capture_only"])
        self.assertEqual("review-needed", final_receipt["dominant_target_kind_now"])
        self.assertEqual(
            "capture-manual-review-context",
            final_receipt["best_next_move_now"]["move_kind"],
        )

    def test_continue_from_final_receipt_can_continue_blocked_evidence_context_capture_when_compatible(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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
                        "title": "Collect blocked evidence",
                        "description": "Capture failure evidence for the blocked step.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                    },
                ],
            )
        )
        processor.process_call(
            make_failure_report_call(
                reported_status="blocked",
                artifact_refs=[make_summary_artifact_ref()],
            )
        )
        processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref(artifact_id="T000001.J001.A002")],
            )
        )

        prior_attempt = processor.attempt_best_next_call_with_guarded_rebase(
            "T000001",
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/blocked.md",
                    "role": "jarvis",
                }
            },
            expected={"expected_submission_mode": "productive_in_slice"},
            allowed_rebased={
                "allow_rebased_context_capture_candidate": True,
                "expected_rebased_call_type": "continuation.record",
                "expected_rebased_submission_mode": "context_capture",
                "expected_rebased_follow_up_behavior_kind": "capture-blocked-evidence-next",
            },
        )

        continuation = processor.continue_from_final_receipt(
            "T000001",
            final_receipt=prior_attempt["final_receipt"],
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/blocked-2.md",
                    "role": "jarvis",
                }
            },
        )
        final_receipt = continuation["continuation_final_receipt"]
        storage.close()

        self.assertEqual(
            "guard_mismatch_rebased_context_capture",
            continuation["prior_final_attempt_path_kind"],
        )
        self.assertTrue(continuation["prior_receipt_compatible"])
        self.assertEqual(
            "continued_context_capture",
            continuation["continuation_kind"],
        )
        self.assertTrue(continuation["attempt_allowed"])
        self.assertEqual("context_capture", continuation["attempted_submission_mode"])
        self.assertEqual(
            "blocked-evidence-review",
            continuation["fresh_dominant_target_kind"],
        )
        self.assertEqual(
            "capture-blocked-evidence-next",
            continuation["fresh_follow_up_behavior_kind"],
        )
        self.assertIsNotNone(continuation["submit_receipt"])
        self.assertEqual(
            "continued_context_capture",
            final_receipt["continuation_final_path_kind"],
        )
        self.assertFalse(final_receipt["productive_in_slice"])
        self.assertTrue(final_receipt["context_capture_only"])
        self.assertEqual(
            "blocked-evidence-review",
            final_receipt["dominant_target_kind_now"],
        )
        self.assertEqual(
            "capture-blocked-evidence",
            final_receipt["best_next_move_now"]["move_kind"],
        )

    def test_continue_from_final_receipt_keeps_missing_input_refusal_flattened(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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

        continuation = processor.continue_from_final_receipt(
            "T000001",
            final_receipt=prior_attempt["final_receipt"],
        )
        final_receipt = continuation["continuation_final_receipt"]
        storage.close()

        self.assertTrue(continuation["prior_receipt_compatible"])
        self.assertEqual(
            "continued_missing_input_refused",
            continuation["continuation_kind"],
        )
        self.assertFalse(continuation["attempt_allowed"])
        self.assertEqual(("payload_ref",), continuation["missing_required_fields"])
        self.assertIsNotNone(continuation["submit_receipt"])
        final_receipt = continuation["continuation_final_receipt"]
        self.assertEqual(
            "continued_missing_input_refused",
            final_receipt["continuation_final_path_kind"],
        )
        self.assertFalse(final_receipt["attempt_allowed"])
        self.assertEqual(("payload_ref",), final_receipt["missing_required_fields"])
        self.assertTrue(final_receipt["requires_additional_user_or_agent_input"])
        self.assertFalse(final_receipt["unavailable_in_slice"])
        self.assertEqual("proof-gathering", final_receipt["dominant_target_kind_now"])
        self.assertEqual(
            "attach-artifact-ref",
            final_receipt["best_next_move_now"]["move_kind"],
        )

    def test_continue_from_final_receipt_refuses_stale_receipt_when_state_drifted(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
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
        before_summary = storage.latest_task_state_summary("T000001")

        continuation = processor.continue_from_final_receipt(
            "T000001",
            final_receipt=prior_attempt["final_receipt"],
        )
        after_summary = storage.latest_task_state_summary("T000001")
        final_receipt = continuation["continuation_final_receipt"]
        storage.close()

        self.assertFalse(continuation["prior_receipt_compatible"])
        self.assertEqual("stale_receipt_refused", continuation["continuation_kind"])
        self.assertIn(
            continuation["continuation_failure_kind"],
            {
                "dominant_target_kind_now_mismatch",
                "best_next_move_kind_now_mismatch",
                "best_next_call_type_now_mismatch",
            },
        )
        self.assertIsNone(continuation["submit_receipt"])
        self.assertIsNone(continuation["final_receipt"])
        self.assertEqual(
            "stale_receipt_refused",
            final_receipt["continuation_final_path_kind"],
        )
        self.assertFalse(final_receipt["prior_receipt_compatible"])
        self.assertFalse(final_receipt["attempt_allowed"])
        self.assertEqual(
            continuation["continuation_failure_kind"],
            final_receipt["continuation_failure_kind"],
        )
        self.assertEqual(
            "productive_replacement_candidate",
            continuation["rebased_candidate_kind"],
        )
        self.assertEqual("job.start", continuation["rebased_best_next_move"]["call_type"])
        self.assertEqual(
            "waiting-on-child",
            continuation["rebased_next_call_hint"]["dominant_target_kind"],
        )
        self.assertEqual(
            "ready_to_submit",
            continuation["rebased_next_call_preflight"]["preflight_kind"],
        )
        self.assertEqual(
            "productive_replacement_candidate",
            final_receipt["rebased_candidate_kind"],
        )
        self.assertEqual(
            "progress-child-leg",
            final_receipt["rebased_best_next_move"]["move_kind"],
        )
        self.assertEqual(
            "ready_to_submit",
            final_receipt["rebased_next_call_preflight"]["preflight_kind"],
        )
        self.assertEqual(before_summary["event_count"], after_summary["event_count"])
        self.assertEqual(
            before_summary["latest_event"]["event_id"],
            after_summary["latest_event"]["event_id"],
        )

    def test_continue_from_final_receipt_stale_receipt_rebases_to_review_context_capture_candidate(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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

        prior_attempt = processor.attempt_best_next_call_with_guarded_rebase(
            "T000001",
            expected={"expected_best_next_call_type": "continuation.record"},
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

        continuation = processor.continue_from_final_receipt(
            "T000001",
            final_receipt=prior_attempt["final_receipt"],
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/review-rebase.md",
                    "role": "jarvis",
                }
            },
        )
        final_receipt = continuation["continuation_final_receipt"]
        storage.close()

        self.assertFalse(continuation["prior_receipt_compatible"])
        self.assertEqual("stale_receipt_refused", continuation["continuation_kind"])
        self.assertEqual(
            "context_capture_replacement_candidate",
            continuation["rebased_candidate_kind"],
        )
        self.assertEqual(
            "review-needed",
            continuation["rebased_next_call_hint"]["dominant_target_kind"],
        )
        self.assertEqual(
            "capture-review-context-next",
            continuation["rebased_follow_up_behavior"]["follow_up_behavior_kind"],
        )
        self.assertEqual(
            "context_only_not_submittable",
            continuation["rebased_next_call_preflight"]["preflight_kind"],
        )
        self.assertEqual(
            "context_capture_replacement_candidate",
            final_receipt["rebased_candidate_kind"],
        )
        self.assertEqual(
            "capture-manual-review-context",
            final_receipt["rebased_best_next_move"]["move_kind"],
        )

    def test_continue_from_final_receipt_stale_receipt_rebases_to_missing_input_candidate(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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

        prior_attempt = processor.attempt_best_next_call_with_guarded_rebase(
            "T000001",
            expected={"expected_best_next_call_type": "continuation.record"},
        )
        processor.process_call(make_result_submit_call(reported_status="succeeded"))
        processor.process_call(make_checkpoint_create_call(plan_version=1))

        continuation = processor.continue_from_final_receipt(
            "T000001",
            final_receipt=prior_attempt["final_receipt"],
        )
        final_receipt = continuation["continuation_final_receipt"]
        storage.close()

        self.assertFalse(continuation["prior_receipt_compatible"])
        self.assertEqual("stale_receipt_refused", continuation["continuation_kind"])
        self.assertEqual(
            "missing_input_replacement_candidate",
            continuation["rebased_candidate_kind"],
        )
        self.assertEqual(
            "proof-gathering",
            continuation["rebased_next_call_hint"]["dominant_target_kind"],
        )
        self.assertEqual(
            ("payload_ref",),
            tuple(continuation["rebased_next_call_draft"]["missing_required_fields"]),
        )
        self.assertEqual(
            "not_ready_missing_fields",
            continuation["rebased_next_call_preflight"]["preflight_kind"],
        )
        self.assertEqual(
            "missing_input_replacement_candidate",
            final_receipt["rebased_candidate_kind"],
        )
        self.assertEqual(
            "attach-artifact-ref",
            final_receipt["rebased_best_next_move"]["move_kind"],
        )

    def test_continue_from_final_receipt_stale_receipt_rebases_to_active_leg_unavailable_candidate(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())

        prior_attempt = processor.attempt_best_next_call_with_guarded_rebase(
            "T000001",
            expected={"expected_best_next_call_type": "continuation.record"},
        )
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

        continuation = processor.continue_from_final_receipt(
            "T000001",
            final_receipt=prior_attempt["final_receipt"],
        )
        final_receipt = continuation["continuation_final_receipt"]
        storage.close()

        self.assertFalse(continuation["prior_receipt_compatible"])
        self.assertEqual("stale_receipt_refused", continuation["continuation_kind"])
        self.assertEqual(
            "unavailable_replacement_candidate",
            continuation["rebased_candidate_kind"],
        )
        self.assertEqual(
            "active-item",
            continuation["rebased_next_call_hint"]["dominant_target_kind"],
        )
        self.assertEqual(
            "resume-active-leg-next",
            continuation["rebased_follow_up_behavior"]["follow_up_behavior_kind"],
        )
        self.assertEqual(
            "unavailable_in_slice",
            continuation["rebased_next_call_preflight"]["preflight_kind"],
        )
        self.assertEqual(
            "unavailable_replacement_candidate",
            final_receipt["rebased_candidate_kind"],
        )
        self.assertEqual(
            "continue-active-execution",
            final_receipt["rebased_best_next_move"]["move_kind"],
        )

    def test_continue_from_final_receipt_waiting_on_child_stays_explicit(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
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

        prior_attempt = processor.attempt_best_next_call_with_guarded_rebase(
            "T000001",
            expected={"expected_dominant_target_kind": "next-executable"},
            allowed_rebased={
                "allow_rebased_productive_candidate": True,
                "expected_rebased_call_type": "job.start",
                "expected_rebased_submission_mode": "productive_in_slice",
            },
        )

        continuation = processor.continue_from_final_receipt(
            "T000001",
            final_receipt=prior_attempt["final_receipt"],
        )
        final_receipt = continuation["continuation_final_receipt"]
        storage.close()

        self.assertEqual(
            "guard_mismatch_rebased_productive_execution",
            continuation["prior_final_attempt_path_kind"],
        )
        self.assertTrue(continuation["prior_receipt_compatible"])
        self.assertEqual(
            "continued_unavailable_refused",
            continuation["continuation_kind"],
        )
        self.assertFalse(continuation["attempt_allowed"])
        self.assertEqual("waiting-on-child", continuation["fresh_dominant_target_kind"])
        self.assertEqual(
            "progress-child-leg",
            continuation["fresh_best_next_move"]["move_kind"],
        )
        self.assertEqual(
            "progress-child-leg-next",
            continuation["fresh_follow_up_behavior_kind"],
        )
        self.assertEqual(
            "continued_unavailable_refused",
            final_receipt["continuation_final_path_kind"],
        )
        self.assertFalse(final_receipt["attempt_allowed"])
        self.assertTrue(final_receipt["unavailable_in_slice"])
        self.assertEqual("waiting-on-child", final_receipt["dominant_target_kind_now"])
        self.assertEqual(
            "progress-child-leg",
            final_receipt["best_next_move_now"]["move_kind"],
        )

    def test_continue_from_final_receipt_from_unavailable_active_leg_does_not_fabricate_path(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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

        prior_attempt = processor.attempt_best_next_call_with_guarded_rebase(
            "T000001",
            expected={
                "expected_dominant_target_kind": "active-item",
                "expected_context_only": False,
                "expected_productive_in_slice": False,
            },
            allowed_rebased={"allow_rebased_productive_candidate": True},
        )

        continuation = processor.continue_from_final_receipt(
            "T000001",
            final_receipt=prior_attempt["final_receipt"],
        )
        storage.close()

        self.assertEqual(
            "guard_match_unavailable_refused",
            continuation["prior_final_attempt_path_kind"],
        )
        self.assertTrue(continuation["prior_receipt_compatible"])
        self.assertEqual(
            "continued_unavailable_refused",
            continuation["continuation_kind"],
        )
        self.assertFalse(continuation["attempt_allowed"])
        self.assertIsNotNone(continuation["submit_receipt"])
        self.assertEqual(
            "submission_refused_unavailable",
            continuation["submit_receipt"]["submit_effect_kind"],
        )

    def test_continue_from_final_receipt_with_guarded_rebase_keeps_compatible_path(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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

        prior_attempt = processor.attempt_best_next_call_with_guarded_rebase(
            "T000001",
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/review.md",
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
            allowed_rebased={
                "allow_rebased_context_capture_candidate": True,
            },
        )

        continuation = processor.continue_from_final_receipt_with_guarded_rebase(
            "T000001",
            final_receipt=prior_attempt["final_receipt"],
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/review-continued.md",
                    "role": "jarvis",
                }
            },
            allowed_rebased={
                "allow_rebased_context_capture_candidate": True,
            },
        )
        final_receipt = continuation["continuation_final_receipt"]
        storage.close()

        self.assertTrue(continuation["prior_receipt_compatible"])
        self.assertEqual("continued_context_capture", continuation["continuation_kind"])
        self.assertEqual(False, continuation["rebase_considered"])
        self.assertIsNone(continuation["rebase_allowed"])
        self.assertTrue(continuation["attempt_allowed"])
        self.assertEqual("context_capture", continuation["attempted_submission_mode"])
        self.assertEqual("continued_context_capture", final_receipt["continuation_final_path_kind"])
        self.assertEqual(False, final_receipt["rebase_considered"])
        self.assertTrue(final_receipt["context_capture_only"])
        self.assertFalse(final_receipt["productive_in_slice"])

    def test_stale_receipt_productive_rebased_continuation_runs_only_when_approved(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
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

        continuation = processor.continue_from_final_receipt_with_guarded_rebase(
            "T000001",
            final_receipt=prior_attempt["final_receipt"],
            allowed_rebased={
                "allow_rebased_productive_candidate": True,
                "expected_rebased_call_type": "job.start",
                "expected_rebased_submission_mode": "productive_in_slice",
                "expected_rebased_follow_up_behavior_kind": "progress-child-leg-next",
            },
        )
        final_receipt = continuation["continuation_final_receipt"]
        storage.close()

        self.assertFalse(continuation["prior_receipt_compatible"])
        self.assertTrue(continuation["rebase_considered"])
        self.assertTrue(continuation["rebase_allowed"])
        self.assertEqual(
            "stale_rebased_continued_productive_execution",
            continuation["continuation_kind"],
        )
        self.assertTrue(continuation["attempt_allowed"])
        self.assertEqual("job.start", continuation["attempted_call_type"])
        self.assertEqual("productive_in_slice", continuation["attempted_submission_mode"])
        self.assertIsNotNone(continuation["submit_receipt"])
        self.assertEqual("submitted", continuation["submit_receipt"]["decision_kind"])
        self.assertEqual(
            "stale_rebased_continued_productive_execution",
            final_receipt["continuation_final_path_kind"],
        )
        self.assertTrue(final_receipt["rebase_allowed"])
        self.assertTrue(final_receipt["productive_in_slice"])

    def test_stale_receipt_context_capture_rebased_continuation_runs_only_when_approved(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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
        prior_attempt = processor.attempt_best_next_call_with_guarded_rebase(
            "T000001",
            expected={"expected_best_next_call_type": "continuation.record"},
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

        continuation = processor.continue_from_final_receipt_with_guarded_rebase(
            "T000001",
            final_receipt=prior_attempt["final_receipt"],
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/review-approved.md",
                    "role": "jarvis",
                }
            },
            allowed_rebased={
                "allow_rebased_context_capture_candidate": True,
                "expected_rebased_call_type": "continuation.record",
                "expected_rebased_submission_mode": "context_capture",
                "expected_rebased_follow_up_behavior_kind": "capture-review-context-next",
            },
        )
        final_receipt = continuation["continuation_final_receipt"]
        storage.close()

        self.assertFalse(continuation["prior_receipt_compatible"])
        self.assertTrue(continuation["rebase_considered"])
        self.assertTrue(continuation["rebase_allowed"])
        self.assertEqual(
            "stale_rebased_continued_context_capture",
            continuation["continuation_kind"],
        )
        self.assertTrue(continuation["attempt_allowed"])
        self.assertEqual("context_capture", continuation["attempted_submission_mode"])
        self.assertIsNotNone(continuation["submit_receipt"])
        self.assertEqual("context_capture", continuation["submit_receipt"]["submission_mode"])
        self.assertEqual(
            "stale_rebased_continued_context_capture",
            final_receipt["continuation_final_path_kind"],
        )
        self.assertTrue(final_receipt["context_capture_only"])
        self.assertFalse(final_receipt["productive_in_slice"])

    def test_stale_receipt_rebased_continuation_outside_approval_is_refused_cleanly(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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
        prior_attempt = processor.attempt_best_next_call_with_guarded_rebase(
            "T000001",
            expected={"expected_best_next_call_type": "continuation.record"},
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
        before_summary = storage.latest_task_state_summary("T000001")

        continuation = processor.continue_from_final_receipt_with_guarded_rebase(
            "T000001",
            final_receipt=prior_attempt["final_receipt"],
            supplied_fields={
                "payload_ref": {
                    "kind": "continuation-note",
                    "path": "/workspace/jarvis/tasks/T000001/review-disallowed.md",
                    "role": "jarvis",
                }
            },
            allowed_rebased={"allow_rebased_productive_candidate": True},
        )
        after_summary = storage.latest_task_state_summary("T000001")
        final_receipt = continuation["continuation_final_receipt"]
        storage.close()

        self.assertFalse(continuation["prior_receipt_compatible"])
        self.assertTrue(continuation["rebase_considered"])
        self.assertFalse(continuation["rebase_allowed"])
        self.assertEqual("rebased_candidate_not_approved", continuation["rebase_failure_kind"])
        self.assertEqual("stale_rebased_refused", continuation["continuation_kind"])
        self.assertFalse(continuation["attempt_allowed"])
        self.assertIsNone(continuation["submit_receipt"])
        self.assertEqual(
            before_summary["latest_event"]["event_id"],
            after_summary["latest_event"]["event_id"],
        )
        self.assertEqual("stale_rebased_refused", final_receipt["continuation_final_path_kind"])
        self.assertFalse(final_receipt["rebase_allowed"])

    def test_stale_receipt_missing_input_rebased_continuation_returns_clean_needs_input_result(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
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
        prior_attempt = processor.attempt_best_next_call_with_guarded_rebase(
            "T000001",
            expected={"expected_best_next_call_type": "continuation.record"},
        )
        processor.process_call(make_result_submit_call(reported_status="succeeded"))
        processor.process_call(make_checkpoint_create_call(plan_version=1))

        continuation = processor.continue_from_final_receipt_with_guarded_rebase(
            "T000001",
            final_receipt=prior_attempt["final_receipt"],
            allowed_rebased={
                "allow_rebased_missing_input_candidate": True,
                "expected_rebased_call_type": "continuation.record",
                "expected_rebased_submission_mode": "productive_in_slice",
                "expected_rebased_follow_up_behavior_kind": "gather-proof-next",
            },
        )
        final_receipt = continuation["continuation_final_receipt"]
        storage.close()

        self.assertFalse(continuation["prior_receipt_compatible"])
        self.assertTrue(continuation["rebase_considered"])
        self.assertTrue(continuation["rebase_allowed"])
        self.assertEqual(
            "stale_rebased_missing_input_refused",
            continuation["continuation_kind"],
        )
        self.assertFalse(continuation["attempt_allowed"])
        self.assertEqual(("payload_ref",), continuation["missing_required_fields"])
        self.assertTrue(continuation["requires_additional_user_or_agent_input"])
        self.assertIsNotNone(continuation["submit_receipt"])
        self.assertEqual(
            "submission_refused_missing_fields",
            continuation["submit_receipt"]["submit_effect_kind"],
        )
        self.assertEqual(
            "stale_rebased_missing_input_refused",
            final_receipt["continuation_final_path_kind"],
        )

    def test_stale_receipt_unavailable_rebased_continuation_still_refuses_cleanly(
        self,
    ) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-03-30T12:00:00Z",
        )
        processor.process_call(make_task_create_call())
        prior_attempt = processor.attempt_best_next_call_with_guarded_rebase(
            "T000001",
            expected={"expected_best_next_call_type": "continuation.record"},
        )
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

        continuation = processor.continue_from_final_receipt_with_guarded_rebase(
            "T000001",
            final_receipt=prior_attempt["final_receipt"],
            allowed_rebased={"allow_rebased_productive_candidate": True},
        )
        final_receipt = continuation["continuation_final_receipt"]
        storage.close()

        self.assertFalse(continuation["prior_receipt_compatible"])
        self.assertTrue(continuation["rebase_considered"])
        self.assertFalse(continuation["rebase_allowed"])
        self.assertEqual("rebased_candidate_unavailable", continuation["rebase_failure_kind"])
        self.assertEqual(
            "stale_rebased_unavailable_refused",
            continuation["continuation_kind"],
        )
        self.assertFalse(continuation["attempt_allowed"])
        self.assertIsNone(continuation["submit_receipt"])
        self.assertEqual(
            "stale_rebased_unavailable_refused",
            final_receipt["continuation_final_path_kind"],
        )
        self.assertTrue(final_receipt["unavailable_in_slice"])
        self.assertEqual("active-item", continuation["fresh_dominant_target_kind"])
        self.assertEqual(
            "continue-active-execution",
            continuation["fresh_best_next_move"]["move_kind"],
        )
        self.assertFalse(final_receipt["prior_receipt_compatible"])
        self.assertFalse(final_receipt["attempt_allowed"])
        self.assertTrue(final_receipt["unavailable_in_slice"])
        self.assertEqual("active-item", final_receipt["dominant_target_kind_now"])
        self.assertEqual(
            "continue-active-execution",
            final_receipt["best_next_move_now"]["move_kind"],
        )
