# Contract Stage Review After Policy Table

Date: 2026-03-30
Repo: `/home/dev/OH_SHOP`
Branch: `master`

## 1. Contracts reviewed

Architecture authority reviewed in this pass:

- [AI_GARAGE_BLUEPRINT.MD.md](/home/dev/OH_SHOP/docs/architecture/AI_GARAGE_BLUEPRINT.MD.md)
- [ai_garage_library_and_policy_contract_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/ai_garage_library_and_policy_contract_v_0_1.md)
- [garage_universal_language_dictionary_v0_1.md](/home/dev/OH_SHOP/docs/architecture/garage_universal_language_dictionary_v0_1.md)
- [ALFRED_MASTER_CONTRACT_v_0_2.md](/home/dev/OH_SHOP/docs/architecture/ALFRED_MASTER_CONTRACT_v_0_2.md)
- [JARVIS_MASTER_CONTRACT_v_0_2.md](/home/dev/OH_SHOP/docs/architecture/JARVIS_MASTER_CONTRACT_v_0_2.md)
- [ROBIN_MASTER_CONTRACT_v_0_2.md](/home/dev/OH_SHOP/docs/architecture/ROBIN_MASTER_CONTRACT_v_0_2.md)
- [LIBRARY_SCHEMA_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/LIBRARY_SCHEMA_CONTRACT_v_0_1.md)
- [TRACKED_PLAN_OBJECT_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/TRACKED_PLAN_OBJECT_CONTRACT_v_0_1.md)
- [HANDOFF_ENVELOPE_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/HANDOFF_ENVELOPE_CONTRACT_v_0_1.md)
- [ARTIFACT_AND_PROOF_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/ARTIFACT_AND_PROOF_CONTRACT_v_0_1.md)
- [POLICY_TABLE_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/POLICY_TABLE_CONTRACT_v_0_1.md)

Current runtime/status docs checked as stage context:

- [post_action_observation_path_investigation.md](/home/dev/OH_SHOP/docs/current/post_action_observation_path_investigation.md)
- [repo_readiness_audit_for_schema_coding_followup.md](/home/dev/OH_SHOP/docs/current/repo_readiness_audit_for_schema_coding_followup.md)
- [SETUP.md](/home/dev/OH_SHOP/docs/current/SETUP.md)
- [TROUBLESHOOTING.md](/home/dev/OH_SHOP/docs/current/TROUBLESHOOTING.md)
- [contract_stage_review_after_plan_and_handoff.md](/home/dev/OH_SHOP/docs/current/contract_stage_review_after_plan_and_handoff.md)
- [contract_stage_review_after_artifact_and_proof.md](/home/dev/OH_SHOP/docs/current/contract_stage_review_after_artifact_and_proof.md)

## 2. What changed in this pass

Added:

- [POLICY_TABLE_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/POLICY_TABLE_CONTRACT_v_0_1.md)

Why this was the correct next move:

- the library/policy contract already defined policy as a standing rulebook domain above runtime job language
- the repo already had role contracts, shared language, schema layer, tracked-plan, handoff, and artifact/proof contracts
- what was still missing was the explicit record/table contract for policy scope, version, activation state, content linkage, and task-override handling

Bluntly:

At this point the repo was no longer missing shell or proof semantics.
It was missing policy-record discipline.

## 3. What the new policy-table contract now locks down

The new contract now defines:

- what a policy record is
- required policy-record fields
- policy scopes
- policy-record statuses
- policy versioning
- stable `policy_key` behavior
- `content_ref` posture
- layering from `global` to role-specific to `task_override`
- explicit task-override linkage rules
- Alfred's relationship to policy loading and enforcement
- why policy records are not runtime envelopes or runtime event history

## 4. What did not need rewriting

Not rewritten in this pass:

- tracked-plan contract
- handoff-envelope contract
- artifact/proof contract
- blueprint
- setup
- troubleshooting
- readiness follow-up

Reason:

Those files were already good enough for this stage.
Another cosmetic rewrite would have been noise.

## 5. Current contract stage after this pass

The repo is now clearly at:

1. role authority established
2. shared language dictionary established
3. library/schema contract established
4. tracked-plan object contract established
5. handoff-envelope contract established
6. artifact/proof contract established
7. policy-table contract established

That stage call is grounded in the actual contract stack now present in `docs/architecture`.

## 6. Exact next contract after this pass

Recommended next contract:

- `CALL_AND_EVENT_OBJECT_CONTRACT_v_0_1.md`

Reason:

- the repo already has dictionary tokens and schema-layer intent, but it still does not have one explicit contract that narrows the concrete object shapes for official runtime calls and official event records together at the implementation-facing object layer
- after policy-table, the next likely ambiguity zone is the exact object split between call records, event records, and later persistence objects

If you want to go straight to raw JSON Schema authoring instead, the repo is now much closer to being able to do that without guessing.

## 7. Bottom line

This pass closed the next real missing contract layer.

The repo is no longer just saying “policy exists somewhere.”
It now has a dedicated policy-table contract for scope/version/status/content-linkage discipline.
