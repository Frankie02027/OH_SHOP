# Contract Stage Review After Plan and Handoff

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
- [ROBIN_MASTER_CONTRACT_v_0_3.md](/home/dev/OH_SHOP/docs/architecture/ROBIN_MASTER_CONTRACT_v_0_3.md)
- [LIBRARY_SCHEMA_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/LIBRARY_SCHEMA_CONTRACT_v_0_1.md)
- [TRACKED_PLAN_OBJECT_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/TRACKED_PLAN_OBJECT_CONTRACT_v_0_1.md)
- [HANDOFF_ENVELOPE_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/HANDOFF_ENVELOPE_CONTRACT_v_0_1.md)

Current runtime/status docs checked against them:

- [post_action_observation_path_investigation.md](/home/dev/OH_SHOP/docs/current/post_action_observation_path_investigation.md)
- [repo_readiness_audit_for_schema_coding_followup.md](/home/dev/OH_SHOP/docs/current/repo_readiness_audit_for_schema_coding_followup.md)
- [SETUP.md](/home/dev/OH_SHOP/docs/current/SETUP.md)
- [TROUBLESHOOTING.md](/home/dev/OH_SHOP/docs/current/TROUBLESHOOTING.md)

Truth-check files inspected only as needed:

- [garagectl.py](/home/dev/OH_SHOP/ops/garagectl.py)
- [docker-compose.yml](/home/dev/OH_SHOP/compose/docker-compose.yml)

## 2. Stage verification

The repo is now clearly at:

- post-role-contract stage
- post-dictionary stage
- post-library-schema-contract stage
- post-tracked-plan-object contract stage
- post-handoff-envelope contract stage

That stage call is grounded in the working-tree presence of:

- [ALFRED_MASTER_CONTRACT_v_0_2.md](/home/dev/OH_SHOP/docs/architecture/ALFRED_MASTER_CONTRACT_v_0_2.md)
- [JARVIS_MASTER_CONTRACT_v_0_2.md](/home/dev/OH_SHOP/docs/architecture/JARVIS_MASTER_CONTRACT_v_0_2.md)
- [ROBIN_MASTER_CONTRACT_v_0_3.md](/home/dev/OH_SHOP/docs/architecture/ROBIN_MASTER_CONTRACT_v_0_3.md)
- [garage_universal_language_dictionary_v0_1.md](/home/dev/OH_SHOP/docs/architecture/garage_universal_language_dictionary_v0_1.md)
- [LIBRARY_SCHEMA_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/LIBRARY_SCHEMA_CONTRACT_v_0_1.md)
- [TRACKED_PLAN_OBJECT_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/TRACKED_PLAN_OBJECT_CONTRACT_v_0_1.md)
- [HANDOFF_ENVELOPE_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/HANDOFF_ENVELOPE_CONTRACT_v_0_1.md)

The next contract after this pass is therefore not ambiguous anymore.

## 3. What was out of sync

The main out-of-sync file was:

- [repo_readiness_audit_for_schema_coding_followup.md](/home/dev/OH_SHOP/docs/current/repo_readiness_audit_for_schema_coding_followup.md)

Why it was out of sync:

- it still described the post-action browser/tool blocker as open
- it still described the repo as if the tool-observation boundary was the current live blocker
- [post_action_observation_path_investigation.md](/home/dev/OH_SHOP/docs/current/post_action_observation_path_investigation.md) already says that defect is `FIXED`

The blueprint was not lying, but it lagged the newer schema/object stage by omission:

- it did not point readers at the newer v0.1 language/schema/object contracts

`SETUP.md` and `TROUBLESHOOTING.md` were checked and left alone:

- no direct contradiction to current `garagectl.py`
- no direct contradiction to current compose/runtime truth
- no stale statement about the post-action defect being open

## 4. What was updated

Updated:

- [TRACKED_PLAN_OBJECT_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/TRACKED_PLAN_OBJECT_CONTRACT_v_0_1.md)
  - added explicit optional header fields
  - added explicit optional item fields
  - tightened the object layout so it better matches implementation-facing contract use

- [HANDOFF_ENVELOPE_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/HANDOFF_ENVELOPE_CONTRACT_v_0_1.md)
  - added explicit required envelope header fields
  - added explicit optional envelope header fields
  - added good vs bad envelope usage examples
  - tightened the shell/header section so it is more implementation-usable

- [repo_readiness_audit_for_schema_coding_followup.md](/home/dev/OH_SHOP/docs/current/repo_readiness_audit_for_schema_coding_followup.md)
  - added a refresh note
  - marked the old post-action browser blocker as historical rather than current truth
  - stopped treating the fixed observation-path defect as still open

- [AI_GARAGE_BLUEPRINT.MD.md](/home/dev/OH_SHOP/docs/architecture/AI_GARAGE_BLUEPRINT.MD.md)
  - added a narrow authority note directing readers to the newer v0.1 role/language/schema/object contracts for concrete machine-checkable truth

## 5. What new contracts were added

No brand-new paths were added in this pass because both target contracts already existed in the working tree:

- [TRACKED_PLAN_OBJECT_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/TRACKED_PLAN_OBJECT_CONTRACT_v_0_1.md)
- [HANDOFF_ENVELOPE_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/HANDOFF_ENVELOPE_CONTRACT_v_0_1.md)

What this pass did instead:

- validated that they are the correct next-stage contract files
- tightened them where they were still missing explicit sections the repo now needs

## 6. Current contract stage after this pass

Current contract stage:

1. role authority established
2. shared language dictionary established
3. library/schema contract established
4. tracked plan object contract established
5. handoff envelope contract established

That means the repo is no longer blocked by contract-stage ambiguity on plan and handoff structure.

## 7. Exact next contract after this pass

Recommended next contract:

- [ARTIFACT_AND_PROOF_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/ARTIFACT_AND_PROOF_CONTRACT_v_0_1.md)

Reason:

- both the tracked-plan contract and handoff-envelope contract now rely on `evidence_refs`, `artifact_refs`, `workspace_refs`, `payload_ref`, and proof-bearing return behavior
- artifact/proof semantics are the next most obvious shared layer that still needs to be made explicit
- this is a harder dependency for later schema implementation than policy-table work is right now

Second recommended follow-on after that:

- `POLICY_TABLE_CONTRACT_v_0_1.md`

## 8. Bottom line

The repo did not need a broad architecture rewrite.

It needed:

- the plan/handoff object stage verified and tightened
- one stale readiness follow-up corrected
- one blueprint authority note added so the newer schema/object contracts stop being hidden by the older high-level blueprint

That is now done.
