# Docs Truth Pass Receipt — 2026-04-01

## 1. Files changed

No additional content changes were needed in this recovery/reporting pass.

The already-landed docs-truth pass had previously changed:
- `drift.md`
- `docs/current/project_state_human_readable_2026-04-01.md`
- `docs/current/repo_readiness_audit_for_schema_coding.md`

This pass only verified those edits were still present and recorded the result here.

## 2. Files quarantined/superseded-marked

- `drift.md`
  - Verified to have a strong `Historical / superseded audit` banner at the top.
- `docs/current/repo_readiness_audit_for_schema_coding.md`
  - Verified to have a strong `Historical / superseded audit` banner near the top.

## 3. Exact stale claims removed or rewritten

Verified current state:

- `drift.md`
  - No longer presents the old broken `ops` lane as current live-state authority.
  - The historical content still contains old advisory/control-flow vocabulary, but it is now explicitly framed as superseded historical audit material.

- `docs/current/project_state_human_readable_2026-04-01.md`
  - The stale Alfred-side claim `receipt/continuation/follow routing` is no longer present.

- `docs/current/repo_readiness_audit_for_schema_coding.md`
  - No longer presents the old readiness snapshot as current authority.
  - The historical blocker table remains preserved, but the file is explicitly marked superseded and points readers to newer truth.

## 4. Exact new wording added

Verified current wording in `drift.md`:

```md
> Historical / superseded audit:
> This file captured the repo before the `ops` cleanup slices 1–5 landed.
> It is preserved as a record of the old broken state only.
> Do not treat it as current live-state authority for the `ops` lane.
> For current truth, use:
> - [docs/current/project_state_human_readable_2026-04-01.md](/home/dev/OH_SHOP/docs/current/project_state_human_readable_2026-04-01.md)
> - [docs/current/repo_readiness_audit_for_schema_coding_followup.md](/home/dev/OH_SHOP/docs/current/repo_readiness_audit_for_schema_coding_followup.md)
> - [docs/current/out_of_sync_authority_note_2026-03-30.md](/home/dev/OH_SHOP/docs/current/out_of_sync_authority_note_2026-03-30.md)
> - [ops/test_garage_negative_surface.py](/home/dev/OH_SHOP/ops/test_garage_negative_surface.py)
```

Verified current replacement wording in `docs/current/project_state_human_readable_2026-04-01.md`:

```md
- tracked-plan registration and progression bookkeeping
- raw/read-oriented service exposure around the cleaned `ops` lane
- anti-regression checks that lock out the deleted advisory/control-flow APIs
```

Verified current wording in `docs/current/repo_readiness_audit_for_schema_coding.md`:

```md
> Historical / superseded audit:
> This report captured the branch before the Alfred authority gap, shared-language mismatch, and later `ops` cleanup were resolved.
> It is preserved as a historical stage snapshot, not as current readiness authority.
> For current truth, use [repo_readiness_audit_for_schema_coding_followup.md](/home/dev/OH_SHOP/docs/current/repo_readiness_audit_for_schema_coding_followup.md) together with the live `ops` lane and [ops/test_garage_negative_surface.py](/home/dev/OH_SHOP/ops/test_garage_negative_surface.py).
```

## 5. Verification command outputs

Command:

```bash
rg -n "latest_task_state_summary|read_job_state_summary|follow_current_honest_path|continue_from_final_receipt|attempt_best_next_call|/tasks/\{task_id\}/summary|/jobs/\{job_id\}/summary|receipt/continuation/follow routing" drift.md docs/current/project_state_human_readable_2026-04-01.md docs/current/repo_readiness_audit_for_schema_coding.md docs/current/repo_readiness_audit_for_schema_coding_followup.md docs/current/out_of_sync_authority_note_2026-03-30.md
```

Output:

```text
drift.md:61:| `ops/garage_alfred_service.py`                                     | REWRITE    | `/tasks/{task_id}/summary` exposes `latest_task_state_summary`, which leaks Alfred/storage advisory state through the service surface                                                                                                                                        |
drift.md:62:| `ops/garage_ledger_service.py`                                     | REWRITE    | `/tasks/{task_id}/summary` and `/jobs/{job_id}/summary` expose advisory summaries instead of raw persisted truth                                                                                                                                                             |
drift.md:72:`SUPPORTED_POLICY_CALL_TYPES`, `latest_task_state_summary`, `read_job_state_summary`, `read_active_plan_summary`, `active_plan_linkage_summary`, `resolve_active_plan_item`, `resolve_relevant_plan_item`, `resolve_task_resume_anchor`, `resolve_next_plan_resume_target`, `effective_task_policy_summary`, `resolve_dominant_task_target`, `resolve_dominant_task_blocker`, `allowed_supported_call_types`, `blocked_supported_call_types`, `best_next_supported_move`, `summarize_next_call_hint`, `summarize_next_call_draft`, `summarize_next_call_draft_readiness`, `summarize_next_call_preflight`, `summarize_immediate_follow_up_behavior`, `summarize_applied_call_posture_transition`, `evaluate_supported_call_posture_effect`, `evaluate_supported_call_policy`
drift.md:80:`AlfredStateReader.evaluate_supported_call_policy`, `AlfredStateReader.latest_task_state_summary`, `AlfredStateReader.summarize_applied_call_posture_transition`, `AlfredStateReader.summarize_next_call_draft_readiness`, `AlfredStateReader.summarize_next_call_preflight`
drift.md:86:`summarize_next_call_draft_readiness`, `prepare_next_call_from_draft`, `submit_prepared_next_call`, `attempt_best_next_call`, `attempt_best_next_call_with_guards`, `attempt_best_next_call_with_guarded_rebase`, `continue_from_final_receipt`, `continue_from_final_receipt_with_guarded_rebase`, `follow_current_honest_path` and the continuation/rebase/final-receipt family that follows from them
drift.md:91:`read_task_summary()` because it returns `_state().storage.latest_task_state_summary(task_id)`
drift.md:96:`read_task_summary()` because it returns `_storage().latest_task_state_summary(task_id)`; `read_job_summary()` because it returns `_storage().read_job_state_summary(job_id)`
drift.md:106:`prepare_next_call_from_draft`, `submit_prepared_next_call`, `attempt_best_next_call`, `attempt_best_next_call_with_guards`, `attempt_best_next_call_with_guarded_rebase`, `continue_from_final_receipt`, `continue_from_final_receipt_with_guarded_rebase`, `post_call_guidance`, `submit_receipt`, rebased candidates, stale receipt compatibility, guarded rebase, continuation final receipts, final attempt path kinds
drift.md:164:   Rewrite `ops/garage_alfred_service.py` and `ops/garage_ledger_service.py` so they expose raw truth only. No `latest_task_state_summary`, no `read_job_state_summary`, no advisory fields.
```

Interpretation:
- The only remaining matches are inside `drift.md`.
- That is acceptable because `drift.md` is now explicitly marked as a historical/superseded audit.
- The stale live-state phrase `receipt/continuation/follow routing` is absent from `docs/current/project_state_human_readable_2026-04-01.md`.

Command:

```bash
pytest -q ops 2>&1
```

Output:

```text
........................................................................ [100%]
72 passed in 0.41s
```

Command:

```bash
git diff -- docs/current/project_state_human_readable_2026-04-01.md docs/current/repo_readiness_audit_for_schema_coding.md drift.md
```

Output:

```text
```

Interpretation:
- The three target docs are already in the corrected state.
- No additional edits were required in this recovery/reporting pass.

## 6. Final state judgment

Verified:
- `drift.md` has a strong historical/superseded banner at the top.
- `docs/current/project_state_human_readable_2026-04-01.md` no longer says `receipt/continuation/follow routing`.
- `docs/current/repo_readiness_audit_for_schema_coding.md` has a historical/superseded banner.
- `ops` still passes unchanged.

Blunt final line:

**The docs-truth pass is complete with historical matches remaining only inside superseded files.**
