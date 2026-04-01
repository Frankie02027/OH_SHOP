"""Negative surface / anti-regression checks for deleted advisory APIs.

These tests exist to make sure removed follow_current_honest_path /
continue_from_final_receipt / latest_task_state_summary style drift does not
silently re-enter the active ops runtime and service surface.
"""

from __future__ import annotations

import ast
from pathlib import Path
import unittest

from ops.garage_alfred import GarageAlfredProcessor
from ops.garage_storage import GarageStorageAdapter, build_storage_backed_alfred_processor
from ops.test_garage_fixtures import (
    GarageTempRootTestCase,
    make_checkpoint_create_call,
    make_continuation_record_call,
    make_job_start_call,
    make_plan_record_call,
    make_result_submit_call,
    make_summary_artifact_ref,
    make_task_create_call,
)


ALFRED_FORBIDDEN_METHODS = (
    "attempt_best_next_call",
    "attempt_best_next_call_with_guards",
    "attempt_best_next_call_with_guarded_rebase",
    "prepare_next_call_from_draft",
    "submit_prepared_next_call",
    "continue_from_final_receipt",
    "continue_from_final_receipt_with_guarded_rebase",
    "follow_current_honest_path",
    "continue_from_top_level_final_receipt",
    "follow_or_continue_current_honest_path",
)

STORAGE_FORBIDDEN_METHODS = (
    "latest_task_state_summary",
    "read_job_state_summary",
    "read_active_plan_summary",
    "active_plan_linkage_summary",
    "resolve_active_plan_item",
    "resolve_relevant_plan_item",
    "resolve_task_resume_anchor",
    "resolve_next_plan_resume_target",
    "effective_task_policy_summary",
    "resolve_dominant_task_target",
    "resolve_dominant_task_blocker",
    "allowed_supported_call_types",
    "blocked_supported_call_types",
    "best_next_supported_move",
    "summarize_next_call_hint",
    "summarize_next_call_draft",
    "summarize_next_call_draft_readiness",
    "summarize_next_call_preflight",
    "summarize_immediate_follow_up_behavior",
    "summarize_applied_call_posture_transition",
    "evaluate_supported_call_posture_effect",
    "evaluate_supported_call_policy",
)

FORBIDDEN_RESULT_FIELDS = (
    "post_call_guidance",
    "best_next_move",
    "next_call_hint",
    "next_call_draft",
    "next_call_draft_readiness",
    "next_call_preflight",
    "refreshed_task_policy",
)

FORBIDDEN_RAW_FIELDS = (
    "best_next_move",
    "best_next_call_type",
    "allowed_call_types",
    "blocked_call_types",
    "execution_allowed",
    "execution_held",
    "execution_hold_kind",
    "dominant_target_kind",
    "dominant_blocker_kind",
    "effective_task_posture",
    "follow_up_behavior_kind",
    "next_call_hint",
    "next_call_draft",
    "next_call_preflight",
)

FORBIDDEN_SOURCE_SYMBOLS = (
    "best_next",
    "next_call",
    "prepared_call",
    "preflight",
    "guarded",
    "stale_receipt",
    "final_receipt",
    "follow_current_honest_path",
    "continue_from_final_receipt",
    "follow_or_continue_current_honest_path",
    "supported_call_policy",
    "dominant_target",
    "dominant_blocker",
    "effective_task_posture",
    "follow_up",
    "post_call_guidance",
    "refreshed_task_policy",
    "execution_hold",
    "latest_task_state_summary",
    "read_job_state_summary",
)


class GarageNegativeSurfaceTests(GarageTempRootTestCase):
    def test_garage_alfred_processor_does_not_expose_deleted_advisory_helpers(self) -> None:
        processor = GarageAlfredProcessor()

        for method_name in ALFRED_FORBIDDEN_METHODS:
            self.assertFalse(
                hasattr(processor, method_name),
                msg=f"forbidden Alfred helper unexpectedly exists: {method_name}",
            )
            self.assertIsNone(getattr(processor, method_name, None))

    def test_garage_storage_adapter_does_not_expose_deleted_summary_helpers(self) -> None:
        storage = GarageStorageAdapter(self.root)
        try:
            for method_name in STORAGE_FORBIDDEN_METHODS:
                self.assertFalse(
                    hasattr(storage, method_name),
                    msg=f"forbidden storage helper unexpectedly exists: {method_name}",
                )
                self.assertIsNone(getattr(storage, method_name, None))
        finally:
            storage.close()

    def test_processed_call_results_do_not_expose_deleted_guidance_fields(self) -> None:
        processor = GarageAlfredProcessor()

        results = (
            processor.process_call(make_task_create_call()).result,
            processor.process_call(make_plan_record_call()).result,
            processor.process_call(make_job_start_call()).result,
            processor.process_call(make_result_submit_call()).result,
        )

        for result in results:
            if not isinstance(result, dict):
                continue
            for field_name in FORBIDDEN_RESULT_FIELDS:
                self.assertNotIn(field_name, result)

    def test_raw_storage_records_do_not_return_deleted_advisory_fields(self) -> None:
        storage, processor = build_storage_backed_alfred_processor(
            self.root,
            now_provider=lambda: "2026-04-01T00:00:00Z",
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
                        "title": "Produce summary proof",
                        "description": "Return the summary artifact for the current step.",
                        "status": "needs_child_job",
                        "depends_on": ["I001"],
                        "verification_rule": {"type": "artifact_exists"},
                    },
                ],
            )
        )
        processor.process_call(make_job_start_call())
        processor.process_call(
            make_result_submit_call(
                artifact_refs=[make_summary_artifact_ref()],
                reported_status="succeeded",
            )
        )
        checkpoint = processor.process_call(make_checkpoint_create_call(plan_version=1))
        processor.process_call(
            make_continuation_record_call(
                plan_version=1,
                artifact_refs=[make_summary_artifact_ref(artifact_id="T000001.J001.A002")],
            )
        )

        raw_objects = (
            storage.read_task_record("T000001"),
            storage.read_job_record("T000001.J001"),
            storage.read_tracked_plan("T000001", 1),
            storage.read_checkpoint_record(checkpoint.result["checkpoint_id"]),
            storage.latest_continuation_for_task("T000001"),
            storage.read_artifact_index_record("T000001.J001.A001"),
        )
        storage.close()

        for obj in raw_objects:
            self.assertIsNotNone(obj)
            assert obj is not None
            for field_name in FORBIDDEN_RAW_FIELDS:
                self.assertNotIn(field_name, obj)

    def test_service_modules_do_not_expose_deleted_summary_routes_or_helpers(self) -> None:
        ops_root = Path(__file__).resolve().parent
        service_sources = {
            "garage_alfred_service.py": (ops_root / "garage_alfred_service.py").read_text(
                encoding="utf-8"
            ),
            "garage_ledger_service.py": (ops_root / "garage_ledger_service.py").read_text(
                encoding="utf-8"
            ),
        }

        self.assertNotIn("/tasks/{task_id}/summary", service_sources["garage_alfred_service.py"])
        self.assertNotIn("/tasks/{task_id}/summary", service_sources["garage_ledger_service.py"])
        self.assertNotIn("/jobs/{job_id}/summary", service_sources["garage_ledger_service.py"])

        for file_name, source_text in service_sources.items():
            module_ast = ast.parse(source_text, filename=file_name)
            function_names = {
                node.name for node in module_ast.body if isinstance(node, ast.FunctionDef)
            }
            self.assertNotIn("read_task_summary", function_names)
            self.assertNotIn("read_job_summary", function_names)

    def test_active_runtime_and_service_files_remain_free_of_forbidden_source_symbols(
        self,
    ) -> None:
        ops_root = Path(__file__).resolve().parent
        files_to_check = (
            ops_root / "garage_alfred.py",
            ops_root / "garage_storage.py",
            ops_root / "garage_alfred_service.py",
            ops_root / "garage_ledger_service.py",
        )

        for path in files_to_check:
            source_text = path.read_text(encoding="utf-8")
            lowered = source_text.lower()
            for symbol in FORBIDDEN_SOURCE_SYMBOLS:
                self.assertNotIn(
                    symbol.lower(),
                    lowered,
                    msg=f"forbidden symbol family '{symbol}' reappeared in {path.name}",
                )


if __name__ == "__main__":
    unittest.main()
