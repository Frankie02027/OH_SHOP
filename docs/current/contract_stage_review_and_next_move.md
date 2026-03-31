# Contract Stage Review and Next Move

> Superseded note:
> This file captured the repo at the stage just before the tracked-plan and handoff-envelope contracts were tightened and confirmed.
> Use [contract_stage_review_after_plan_and_handoff.md](/home/dev/OH_SHOP/docs/current/contract_stage_review_after_plan_and_handoff.md) as the newer contract-stage authority.

Date: 2026-03-30
Repo: `Frankie02027/OH_SHOP`

## 1. Contracts reviewed

Reviewed in `docs/architecture`:

- `AI_GARAGE_BLUEPRINT.MD.md`
- `ai_garage_library_and_policy_contract_v_0_1.md`
- `garage_universal_language_dictionary_v0_1.md`
- `ALFRED_MASTER_CONTRACT_v_0_2.md`
- `JARVIS_MASTER_CONTRACT_v_0_2.md`
- `ROBIN_MASTER_CONTRACT_v_0_3.md`
- `LIBRARY_SCHEMA_CONTRACT_v_0_1.md`

Compared against current repo/runtime evidence:

- `docs/current/post_action_observation_path_investigation.md`
- `docs/current/repo_readiness_audit_for_schema_coding_followup.md`
- `ops/garagectl.py`
- `compose/docker-compose.yml`

## 2. Current stage call

The repo is now **past**:

- role-contract stage
- shared-language dictionary stage
- library/policy-contract stage
- library-schema-contract stage

The repo is now at:

## Tracked Plan Object Contract stage

Reason:

- the role contracts exist in `docs/architecture`
- the shared language authority exists
- the Library Schema Contract now exists
- the previously blocking browser post-action defect is documented as fixed

## 3. What is current

Current active contract stack in `docs/architecture`:

- blueprint
- Alfred master
- Jarvis master
- Robin master
- library/policy contract
- universal language dictionary
- library schema contract

This is enough authority to move to the next contract layer.

## 4. What is stale or lagging

### 4.1 `repo_readiness_audit_for_schema_coding_followup.md`
This file still reflects an earlier stage where the post-action browser blocker was open.
That is no longer current because the later investigation records the blocker as fixed.

### 4.2 `AI_GARAGE_BLUEPRINT.MD.md`
The blueprint remains useful, but it is lagging the newer Alfred/runtime authority.
It still reads more like an earlier broad-role draft than the newer thinner Alfred + schema-layer direction.

## 5. Next contract

The next contract to write is:

# `TRACKED_PLAN_OBJECT_CONTRACT_v_0_1.md`

This should define:

- tracked plan header object
- plan item object
- plan versioning
- current active item rules
- dependency semantics
- verification rule types
- evidence refs
- done_unverified vs verified discipline
- task/job linkage
- revision/update behavior
- continuation/checkpoint interaction

## 6. Contract after that

After the tracked-plan contract, the next most useful contract should be one of:

- `ARTIFACT_AND_PROOF_CONTRACT_v_0_1.md`
- `HANDOFF_ENVELOPE_CONTRACT_v_0_1.md`

Recommended order:

1. Tracked Plan Object Contract
2. Artifact and Proof Contract
3. Handoff Envelope Contract
4. Policy Table Contract

## 7. Exact next approved move

Approved next move:

1. create `docs/architecture/TRACKED_PLAN_OBJECT_CONTRACT_v_0_1.md`
2. add a short authority note that the older readiness follow-up is no longer the last word
3. leave runtime alone unless a stale statement must be corrected

## 8. Bottom line

The repo is no longer waiting on “what contract comes next.”

The next contract is:

## `TRACKED_PLAN_OBJECT_CONTRACT_v_0_1.md`

The main stale file problem is that the older readiness follow-up still reflects a pre-fix runtime stage.
