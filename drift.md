> Historical / superseded audit:
> This file captured the repo before the `ops` cleanup slices 1–5 landed.
> It is preserved as a record of the old broken state only.
> Do not treat it as current live-state authority for the `ops` lane.
> For current truth, use:
> - [docs/current/project_state_human_readable_2026-04-01.md](/home/dev/OH_SHOP/docs/current/project_state_human_readable_2026-04-01.md)
> - [docs/current/repo_readiness_audit_for_schema_coding_followup.md](/home/dev/OH_SHOP/docs/current/repo_readiness_audit_for_schema_coding_followup.md)
> - [docs/current/out_of_sync_authority_note_2026-03-30.md](/home/dev/OH_SHOP/docs/current/out_of_sync_authority_note_2026-03-30.md)
> - [ops/test_garage_negative_surface.py](/home/dev/OH_SHOP/ops/test_garage_negative_surface.py)

## 1. Contracts used

* `docs/architecture/ai_garage_library_and_policy_contract_v_0_1.md` — shared language constrains **interaction shape**, not worker thinking strategy; Alfred validates/routes/records official state; Jarvis decides the next proposed work chunk; policy/rulebook sits above runtime grammar 
* `docs/architecture/AI_GARAGE_BLUEPRINT.MD.md` — Jarvis is the main reasoner/worker, Robin is the browser specialist, Alfred is the deterministic director/record keeper, not the thinker 
* `docs/architecture/ALFRED_MASTER_CONTRACT_v_0_2.md` — Alfred is deterministic manifest clerk, official shell stamper, state recorder, checkpoint registrar, retry/handoff gatekeeper, non-creative workflow controller; Alfred does **not** own meaning 
* `docs/architecture/JARVIS_MASTER_CONTRACT_v_0_2.md` — Jarvis is the main planner, parent-task owner, and continuity owner; Jarvis decides whether work stays local or needs child work; Alfred owns official state transitions, not worker strategy 
* `docs/architecture/HANDOFF_ENVELOPE_CONTRACT_v_0_1.md` — Jarvis/Robin own body semantics; Alfred owns official shell stamping and must not semantically rewrite worker meaning 
* `docs/architecture/TRACKED_PLAN_OBJECT_CONTRACT_v_0_1.md` — Jarvis owns plan meaning; Alfred owns official plan registration/linkage; Robin does not own parent plan authority 
* `docs/architecture/CALL_AND_EVENT_OBJECT_CONTRACT_v_0_1.md` — calls are runtime interaction objects, events are append-only recorded facts; do not collapse them into one vague message blob 

## 2. Files audited

* `docs/architecture/ai_garage_library_and_policy_contract_v_0_1.md` 
* `docs/architecture/AI_GARAGE_BLUEPRINT.MD.md` 
* `docs/architecture/ALFRED_MASTER_CONTRACT_v_0_2.md` 
* `docs/architecture/JARVIS_MASTER_CONTRACT_v_0_2.md` 
* `docs/architecture/HANDOFF_ENVELOPE_CONTRACT_v_0_1.md` 
* `docs/architecture/TRACKED_PLAN_OBJECT_CONTRACT_v_0_1.md` 
* `docs/architecture/CALL_AND_EVENT_OBJECT_CONTRACT_v_0_1.md` 
* `ops/garage_alfred.py` 
* `ops/garage_storage.py` 
* `ops/garage_alfred_service.py` 
* `ops/garage_ledger_service.py` 
* `ops/garage_runtime.py` 
* `ops/garage_ledger_adapter.py` 
* `ops/garage_artifacts.py` 
* `ops/test_garage_workspace_bootstrap.py` 
* `ops/test_garage_runtime_plane_services.py` 
* `ops/test_garage_storage.py` 
* `ops/test_garage_storage_posture.py` 
* `ops/test_garage_storage_flow.py` 

## 3. Compliance map: KEEP / REWRITE / QUARANTINE / DELETE

| File                                                               | Status     | Reason                                                                                                                                                                                                                                                                       |
| ------------------------------------------------------------------ | ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `docs/architecture/ai_garage_library_and_policy_contract_v_0_1.md` | KEEP       | Correct authority: interaction shape, not worker thinking strategy; Alfred validates/routes/records, Jarvis decides next work chunk                                                                                                                                          |
| `docs/architecture/AI_GARAGE_BLUEPRINT.MD.md`                      | KEEP       | Correct high-level role split: Jarvis main worker, Robin web worker, Alfred deterministic controller/record keeper                                                                                                                                                           |
| `docs/architecture/ALFRED_MASTER_CONTRACT_v_0_2.md`                | KEEP       | Correct Alfred boundary: clerk/controller/stamper/recorder, not thinker or semantic author                                                                                                                                                                                   |
| `docs/architecture/JARVIS_MASTER_CONTRACT_v_0_2.md`                | KEEP       | Correct Jarvis boundary: main planner, parent-task owner, continuity owner                                                                                                                                                                                                   |
| `docs/architecture/HANDOFF_ENVELOPE_CONTRACT_v_0_1.md`             | KEEP       | Correct shell/body split and ownership split                                                                                                                                                                                                                                 |
| `docs/architecture/TRACKED_PLAN_OBJECT_CONTRACT_v_0_1.md`          | KEEP       | Correct plan-ownership split: Jarvis owns plan meaning, Alfred owns official registration                                                                                                                                                                                    |
| `docs/architecture/CALL_AND_EVENT_OBJECT_CONTRACT_v_0_1.md`        | KEEP       | Correct distinction between runtime call objects and factual event objects                                                                                                                                                                                                   |
| `ops/garage_runtime.py`                                            | KEEP       | Validated dispatch/record processor only. No Alfred-side strategy/advice layer present                                                                                                                                                                                       |
| `ops/garage_ledger_adapter.py`                                     | KEEP       | Mirrors persisted records into ledger tree. No advisory/strategy logic present                                                                                                                                                                                               |
| `ops/garage_artifacts.py`                                          | KEEP       | Artifact promotion/registration helper only. No workflow-advice logic present                                                                                                                                                                                                |
| `ops/test_garage_workspace_bootstrap.py`                           | KEEP       | Bootstrap tree test only. No Alfred-advisor surface encoded                                                                                                                                                                                                                  |
| `ops/test_garage_runtime_plane_services.py`                        | KEEP       | Runtime-plane/bootstrap/artifact tests only. No Alfred-advisor surface encoded                                                                                                                                                                                               |
| `ops/garage_storage.py`                                            | REWRITE    | Storage adapter is mixed with task-policy, posture, next-step, proof-advice, follow-up, and preflight logic. That breaks the role split and converts storage into a workflow brain                                                                                           |
| `ops/garage_alfred.py`                                             | REWRITE    | Alfred processor contains next-call drafting, guarded attempt, stale receipt, rebase, continuation strategy, and post-call guidance systems. That makes Alfred a strategy engine, not a deterministic clerk/controller                                                       |
| `ops/garage_alfred_service.py`                                     | REWRITE    | `/tasks/{task_id}/summary` exposes `latest_task_state_summary`, which leaks Alfred/storage advisory state through the service surface                                                                                                                                        |
| `ops/garage_ledger_service.py`                                     | REWRITE    | `/tasks/{task_id}/summary` and `/jobs/{job_id}/summary` expose advisory summaries instead of raw persisted truth                                                                                                                                                             |
| `ops/test_garage_storage.py`                                       | REWRITE    | Aggregator imports drift suites and therefore keeps the forbidden Alfred/storage advisory layer alive in the test surface                                                                                                                                                    |
| `ops/test_garage_storage_posture.py`                               | QUARANTINE | Mixed file. Some factual proof/plan assertions are salvageable, but the file heavily encodes forbidden advisory fields and policy/posture surfaces such as `dominant_target_kind`, `best_next_move`, `execution_hold_kind`, and `summarize_applied_call_posture_transition`  |
| `ops/test_garage_storage_flow.py`                                  | DELETE     | This file is dedicated to forbidden Alfred functionality: prepared-call drafting, guarded attempts, rebasing, stale receipt continuation, and flattened final receipts. It is a contract-violating feature test suite end-to-end                                             |

## 4. Exact violating symbols/functions

### `ops/garage_storage.py`

Violating public symbols/functions:
`SUPPORTED_POLICY_CALL_TYPES`, `latest_task_state_summary`, `read_job_state_summary`, `read_active_plan_summary`, `active_plan_linkage_summary`, `resolve_active_plan_item`, `resolve_relevant_plan_item`, `resolve_task_resume_anchor`, `resolve_next_plan_resume_target`, `effective_task_policy_summary`, `resolve_dominant_task_target`, `resolve_dominant_task_blocker`, `allowed_supported_call_types`, `blocked_supported_call_types`, `best_next_supported_move`, `summarize_next_call_hint`, `summarize_next_call_draft`, `summarize_next_call_draft_readiness`, `summarize_next_call_preflight`, `summarize_immediate_follow_up_behavior`, `summarize_applied_call_posture_transition`, `evaluate_supported_call_posture_effect`, `evaluate_supported_call_policy` 

Violating internal helper families:
`_build_task_policy_summary`, `_allowed_call_types_for_dominant_target`, `_allowed_call_policy_for_dominant_target`, `_best_next_move_for_policy`, `_rule_aware_policy_hint`, `_classify_applied_call_posture_transition`, `_classify_immediate_follow_up_behavior`, `_classify_next_call_hint`, `_classify_next_call_draft`, `_classify_next_call_draft_readiness`, `_classify_next_call_preflight`, `_prepare_next_call_from_readiness`, `_remaining_missing_prepared_fields` 

### `ops/garage_alfred.py`

Violating protocol surface:
`AlfredStateReader.evaluate_supported_call_policy`, `AlfredStateReader.latest_task_state_summary`, `AlfredStateReader.summarize_applied_call_posture_transition`, `AlfredStateReader.summarize_next_call_draft_readiness`, `AlfredStateReader.summarize_next_call_preflight` 

Violating processor methods:
`process_call()` because it calls `_enforce_supported_call_policy`, `_read_pre_call_task_summary`, `_enrich_post_call_result`, and `_build_post_call_guidance` 

Violating public Alfred control surface:
`summarize_next_call_draft_readiness`, `prepare_next_call_from_draft`, `submit_prepared_next_call`, `attempt_best_next_call`, `attempt_best_next_call_with_guards`, `attempt_best_next_call_with_guarded_rebase`, `continue_from_final_receipt`, `continue_from_final_receipt_with_guarded_rebase`, `follow_current_honest_path` and the continuation/rebase/final-receipt family that follows from them 

### `ops/garage_alfred_service.py`

Violating service exposure:
`read_task_summary()` because it returns `_state().storage.latest_task_state_summary(task_id)` 

### `ops/garage_ledger_service.py`

Violating service exposures:
`read_task_summary()` because it returns `_storage().latest_task_state_summary(task_id)`; `read_job_summary()` because it returns `_storage().read_job_state_summary(job_id)` 

### `ops/test_garage_storage_posture.py`

Violating test surface includes assertions over:
`dominant_target_kind`, `dominant_blocker_kind`, `effective_task_posture`, `execution_held`, `execution_hold_kind`, `allowed_call_types`, `best_next_call_type`, `best_next_move`, `best_next_move_effect_kind`, `evaluate_supported_call_policy`, `evaluate_supported_call_posture_effect`, `summarize_applied_call_posture_transition`, `next_plan_resume_target`, `current_job_is_primary_focus`, `relevant_plan_item_is_primary_focus` 

### `ops/test_garage_storage_flow.py`

Violating test surface includes direct testing of:
`prepare_next_call_from_draft`, `submit_prepared_next_call`, `attempt_best_next_call`, `attempt_best_next_call_with_guards`, `attempt_best_next_call_with_guarded_rebase`, `continue_from_final_receipt`, `continue_from_final_receipt_with_guarded_rebase`, `post_call_guidance`, `submit_receipt`, rebased candidates, stale receipt compatibility, guarded rebase, continuation final receipts, final attempt path kinds 

## 5. Exact contract clause each violation breaks

### Violation family A: Alfred/storage deciding next work, drafting calls, preflighting calls, or computing “best next move”

Broken clauses:

* `ai_garage_library_and_policy_contract_v_0_1.md`: shared language controls **interaction shape**, not worker thinking strategy; Jarvis decides the next proposed work chunk; Alfred validates/routes/records official state 
* `ALFRED_MASTER_CONTRACT_v_0_2.md`: Alfred is deterministic manifest clerk / official shell writer / state recorder / checkpoint registrar / retry-handoff gatekeeper / non-creative workflow controller; Alfred is **not** the main reasoner and **does not own meaning** 
* `JARVIS_MASTER_CONTRACT_v_0_2.md`: Jarvis is the main planner, main inside-the-garage worker, parent-task owner, and continuity owner; Jarvis owns deciding whether work stays local or needs child work; Alfred owns official state transitions, not worker strategy 

Broken by:

* `ops/garage_storage.py` advisory/policy/posture surface 
* `ops/garage_alfred.py` prepared-call / guarded-attempt / rebase / continuation surface 

### Violation family B: Alfred/service surfaces returning advisory state instead of raw stored truth

Broken clauses:

* `ALFRED_MASTER_CONTRACT_v_0_2.md`: Alfred owns official shell/state bookkeeping, not semantic guidance or worker strategy 
* `CALL_AND_EVENT_OBJECT_CONTRACT_v_0_1.md`: event trail should stay factual and append-only; runtime objects should not collapse factual record and semantic meaning into one blob 
* `HANDOFF_ENVELOPE_CONTRACT_v_0_1.md`: Alfred stamps/routs shell; Jarvis/Robin own semantic body meaning; Alfred must not semantically rewrite worker meaning 

Broken by:

* `ops/garage_alfred_service.py` summary endpoint 
* `ops/garage_ledger_service.py` summary endpoints 

### Violation family C: Storage/Alfred inferring plan posture and continuation strategy instead of mechanically registering plan state

Broken clauses:

* `TRACKED_PLAN_OBJECT_CONTRACT_v_0_1.md`: Jarvis owns plan meaning, dependency reasoning, revision proposals, completion claims, continuation interpretation; Alfred owns official plan registration/linkage/checkpoint linkage, not plan meaning or continuation reasoning 
* `ai_garage_library_and_policy_contract_v_0_1.md`: policy/rulebook sits above runtime grammar; runtime grammar should not become worker-thinking strategy 

Broken by:

* `ops/garage_storage.py` plan/posture/continuation target machinery 
* `ops/garage_alfred.py` final-receipt / continuation / guarded-rebase machinery 

### Violation family D: Tests enforcing forbidden behavior

Broken clauses:

* same clauses as families A–C, because these tests codify Alfred as a strategy engine and will reintroduce the same drift on the next implementation pass    
* broken by `ops/test_garage_storage_posture.py` and `ops/test_garage_storage_flow.py`  

## 6. Minimal ordered implementation slices after the audit

1. **Slice 1 — `ops/garage_alfred.py`**
   Remove Alfred’s advisory/prepared-call/guarded-attempt/rebase/final-receipt/continuation-strategy surface. Leave only deterministic official call processing, mechanical validation, ID minting, and event/record bundle construction.

2. **Slice 2 — `ops/garage_storage.py`**
   Remove task-policy/posture/next-step/advisory/public-summary logic. Leave only persisted truth reads/writes, counters, raw event history, raw tracked-plan reads, raw artifact/continuation reads, and minimal factual snapshot helpers if needed.

3. **Slice 3 — service surfaces**
   Rewrite `ops/garage_alfred_service.py` and `ops/garage_ledger_service.py` so they expose raw truth only. No `latest_task_state_summary`, no `read_job_state_summary`, no advisory fields.

4. **Slice 4 — test collateral**
   Delete `ops/test_garage_storage_flow.py`. Quarantine or split `ops/test_garage_storage_posture.py` into factual proof/plan tests vs forbidden advisory tests. Rewrite `ops/test_garage_storage.py` so it no longer imports drift suites.

5. **Slice 5 — negative verification**
   Add negative tests/grep checks that Alfred/storage/service surfaces no longer expose: `best_next_move`, `next_call_hint`, `next_call_draft`, `next_call_preflight`, guarded rebase, stale receipt continuation, post-call guidance, and advisory task-policy fields.
