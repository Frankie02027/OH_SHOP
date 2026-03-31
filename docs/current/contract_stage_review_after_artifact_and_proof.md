# Contract Stage Review After Artifact and Proof

Date: 2026-03-30
Repo: `/home/dev/OH_SHOP`
Branch: `master`

## 1. Contracts reviewed

Architecture authority reviewed for this pass:

- [AI_GARAGE_BLUEPRINT.MD.md](/home/dev/OH_SHOP/docs/architecture/AI_GARAGE_BLUEPRINT.MD.md)
- [ai_garage_library_and_policy_contract_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/ai_garage_library_and_policy_contract_v_0_1.md)
- [garage_universal_language_dictionary_v0_1.md](/home/dev/OH_SHOP/docs/architecture/garage_universal_language_dictionary_v0_1.md)
- [ALFRED_MASTER_CONTRACT_v_0_2.md](/home/dev/OH_SHOP/docs/architecture/ALFRED_MASTER_CONTRACT_v_0_2.md)
- [JARVIS_MASTER_CONTRACT_v_0_2.md](/home/dev/OH_SHOP/docs/architecture/JARVIS_MASTER_CONTRACT_v_0_2.md)
- [ROBIN_MASTER_CONTRACT_v_0_3.md](/home/dev/OH_SHOP/docs/architecture/ROBIN_MASTER_CONTRACT_v_0_3.md)
- [LIBRARY_SCHEMA_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/LIBRARY_SCHEMA_CONTRACT_v_0_1.md)
- [TRACKED_PLAN_OBJECT_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/TRACKED_PLAN_OBJECT_CONTRACT_v_0_1.md)
- [HANDOFF_ENVELOPE_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/HANDOFF_ENVELOPE_CONTRACT_v_0_1.md)
- [ARTIFACT_AND_PROOF_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/ARTIFACT_AND_PROOF_CONTRACT_v_0_1.md)

Current runtime/status docs checked against them as stage context:

- [post_action_observation_path_investigation.md](/home/dev/OH_SHOP/docs/current/post_action_observation_path_investigation.md)
- [repo_readiness_audit_for_schema_coding_followup.md](/home/dev/OH_SHOP/docs/current/repo_readiness_audit_for_schema_coding_followup.md)
- [SETUP.md](/home/dev/OH_SHOP/docs/current/SETUP.md)
- [TROUBLESHOOTING.md](/home/dev/OH_SHOP/docs/current/TROUBLESHOOTING.md)
- [contract_stage_review_after_plan_and_handoff.md](/home/dev/OH_SHOP/docs/current/contract_stage_review_after_plan_and_handoff.md)

## 2. What was current before this pass

Already current before this pass:

- role authority was already established
- dictionary authority was already established
- library/schema authority was already established
- tracked-plan object authority already existed
- handoff-envelope authority already existed
- the earlier stage-review doc had already stopped pretending the repo was still pre-plan/handoff

Bluntly:

The repo was already past the stage described in the original tracked-plan/handoff request.
Redoing those contracts again would have been fake work.

## 3. What was stale or missing

Missing:

- [ARTIFACT_AND_PROOF_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/ARTIFACT_AND_PROOF_CONTRACT_v_0_1.md)

Why that missing file mattered:

- the tracked-plan contract already relied on `evidence_refs`, `verification_rule`, and `done_unverified` vs `verified`
- the handoff-envelope contract already relied on `artifact_refs`, `workspace_refs`, and `payload_ref`
- the dictionary already defined `artifact_id`, `artifact_ref`, `workspace_ref`, and `payload_ref`
- the schema contract already reserved object-schema space for the ref objects

So the repo had the names and the dependency surface, but it was still missing the dedicated contract that explains what those objects mean together.

That was the real next-stage gap.

## 4. What was added in this pass

Added:

- [ARTIFACT_AND_PROOF_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/ARTIFACT_AND_PROOF_CONTRACT_v_0_1.md)

What that new contract now locks down:

- the difference between artifact, evidence, and proof
- ownership split between workers, Alfred, and Ledger
- how `artifact_ref`, `workspace_ref`, and `payload_ref` relate to each other
- how `evidence_refs` should be used
- how proof interacts with `verification_rule`
- how proof interacts with `done_unverified` vs `verified`
- why artifact existence alone does not equal proof
- why Alfred may validate ref structure without pretending to semantically judge the artifact meaning

## 5. What did not need rewriting in this pass

Not rewritten in this pass:

- [TRACKED_PLAN_OBJECT_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/TRACKED_PLAN_OBJECT_CONTRACT_v_0_1.md)
- [HANDOFF_ENVELOPE_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/HANDOFF_ENVELOPE_CONTRACT_v_0_1.md)
- [AI_GARAGE_BLUEPRINT.MD.md](/home/dev/OH_SHOP/docs/architecture/AI_GARAGE_BLUEPRINT.MD.md)
- [repo_readiness_audit_for_schema_coding_followup.md](/home/dev/OH_SHOP/docs/current/repo_readiness_audit_for_schema_coding_followup.md)
- [SETUP.md](/home/dev/OH_SHOP/docs/current/SETUP.md)
- [TROUBLESHOOTING.md](/home/dev/OH_SHOP/docs/current/TROUBLESHOOTING.md)

Reason:

The repo already had the narrow fixes for those files.
There was no need to do another cosmetic rewrite just to look busy.

## 6. Current contract stage after this pass

The repo is now clearly at:

1. role authority established
2. shared language dictionary established
3. library/schema contract established
4. tracked-plan object contract established
5. handoff-envelope contract established
6. artifact/proof contract established

That stage call is not speculative.
It is grounded in the actual working-tree contract stack.

## 7. Exact next contract after this pass

Recommended next contract:

- `POLICY_TABLE_CONTRACT_v_0_1.md`

Reason:

- the policy domain is already explicit in the library/policy contract
- policy scopes already exist conceptually (`global`, `alfred`, `jarvis`, `robin`, `task_override`)
- the repo now has enough language, shell, tracked-plan, handoff, and artifact/proof structure that policy storage/activation rules can be written without guessing
- policy-table work is the next missing shared layer before later schema/storage implementation starts pretending policy records are obvious when they are not

## 8. Bottom line

The correct move in this pass was not to re-author tracked-plan or handoff again.
The correct move was to admit the repo had already passed that stage and then fill the actual next missing contract.

That gap is now closed.
