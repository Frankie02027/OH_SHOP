# Contract Stage Review After Call and Event Object

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
- [ARTIFACT_AND_PROOF_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/ARTIFACT_AND_PROOF_CONTRACT_v_0_1.md)
- [POLICY_TABLE_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/POLICY_TABLE_CONTRACT_v_0_1.md)
- [CALL_AND_EVENT_OBJECT_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/CALL_AND_EVENT_OBJECT_CONTRACT_v_0_1.md)

Current runtime/status docs checked as stage context:

- [post_action_observation_path_investigation.md](/home/dev/OH_SHOP/docs/current/post_action_observation_path_investigation.md)
- [repo_readiness_audit_for_schema_coding_followup.md](/home/dev/OH_SHOP/docs/current/repo_readiness_audit_for_schema_coding_followup.md)
- [SETUP.md](/home/dev/OH_SHOP/docs/current/SETUP.md)
- [TROUBLESHOOTING.md](/home/dev/OH_SHOP/docs/current/TROUBLESHOOTING.md)
- [contract_stage_review_after_plan_and_handoff.md](/home/dev/OH_SHOP/docs/current/contract_stage_review_after_plan_and_handoff.md)
- [contract_stage_review_after_artifact_and_proof.md](/home/dev/OH_SHOP/docs/current/contract_stage_review_after_artifact_and_proof.md)
- [contract_stage_review_after_policy_table.md](/home/dev/OH_SHOP/docs/current/contract_stage_review_after_policy_table.md)

## 2. What changed in this pass

Added:

- [CALL_AND_EVENT_OBJECT_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/CALL_AND_EVENT_OBJECT_CONTRACT_v_0_1.md)

Why this was the correct next move:

- the repo already had the runtime vocabulary frozen at the dictionary layer
- the repo already had schema-layer intent
- the repo already had handoff, tracked-plan, artifact/proof, and policy-table contracts
- what was still missing was one explicit contract for the concrete runtime object split between call objects and event objects before raw schemas or persistence code start baking in sloppy assumptions

Bluntly:

At this point the repo was no longer missing policy or proof structure.
It was missing runtime object-boundary discipline.

## 3. What the new call/event object contract now locks down

The new contract now defines:

- what a call object is
- what an event object is
- what fields each object family should carry
- what fields are shared and what fields are not
- why calls and events are related but not the same thing
- how call-to-event transformation should be understood
- where payloads and refs belong
- why the event trail must stay factual and append-only
- what belongs outside the call/event layer

## 4. What did not need rewriting

Not rewritten in this pass:

- tracked-plan contract
- handoff-envelope contract
- artifact/proof contract
- policy-table contract
- blueprint
- setup
- troubleshooting
- readiness follow-up

Reason:

Those files were already good enough for this stage.
Another cleanup sweep would have been noise.

## 5. Current contract stage after this pass

The repo is now clearly at:

1. role authority established
2. shared language dictionary established
3. library/schema contract established
4. tracked-plan object contract established
5. handoff-envelope contract established
6. artifact/proof contract established
7. policy-table contract established
8. call/event object contract established

That stage call is grounded in the actual contract stack now present in `docs/architecture`.

## 6. Exact next contract after this pass

Recommended next move:

- either begin raw JSON Schema authoring for the runtime object stack
- or, if you still want one more contract before coding, create `PERSISTED_RECORD_AND_STORAGE_OBJECT_CONTRACT_v_0_1.md`

Recommendation:

Start raw JSON Schema authoring now.

Reason:

- the repo now has enough contract structure for call types, event types, refs, tracked plans, handoff envelopes, proof objects, policy records, and runtime call/event objects
- another abstract contract is no longer the highest-leverage move unless you specifically want to freeze storage-record boundaries before coding

## 7. Bottom line

This pass closed the next real missing contract layer.

The repo now has an explicit runtime object contract for call objects versus event objects, which was the main remaining ambiguity before schema coding starts.
