# Repo Readiness Audit for Schema Coding Follow-Up

Date: 2026-03-30
Repo: `/home/dev/OH_SHOP`
Branch: `master`

## Refresh Note

This follow-up captured the repo at the point where:
- model-authority sync had been fixed
- the post-action browser/tool blocker was still believed open

That runtime blocker is no longer current truth.
[post_action_observation_path_investigation.md](/home/dev/OH_SHOP/docs/current/post_action_observation_path_investigation.md) records that the post-action observation/reply defect was isolated and fixed.

This document is still useful as a record of the pre-fix readiness stage, but it should not be treated as the latest runtime-blocker authority.

## 1. EXECUTIVE VERDICT

### Universal library schema coding
**PARTIALLY READY**

Reason:
- the Alfred authority gap is now closed
- the shared top-level vocabulary is now reconciled
- the repo now has one primary machine-language authority for token names
- runtime integration proof is still blocked, so runtime-coupled schema work should wait

What is approved now:
- shared schema primitives that do not depend on a passing live browser/runtime proof
- ID objects
- shell-envelope types
- pointer/ref objects

What is not approved yet:
- runtime-coupled persistence and integration wiring
- storage behavior that assumes the current live browser lane is proven

### ID policy coding
**READY**

Reason:
- [ALFRED_MASTER_CONTRACT_v_0_2.md](/home/dev/OH_SHOP/docs/architecture/ALFRED_MASTER_CONTRACT_v_0_2.md) now defines official ID ownership directly
- [garage_universal_language_dictionary_v0_1.md](/home/dev/OH_SHOP/docs/architecture/garage_universal_language_dictionary_v0_1.md) remains the primary machine-language authority
- retry, same-job return, new-job, `attempt_no`, and linkage rules are aligned

### Early Alfred foundation coding
**PARTIALLY READY**

Approved:
- `alfred/ids.py`
- `alfred/types.py` for shell fields, route metadata, ID-bearing refs, and non-semantic envelope objects

Not approved:
- `alfred/store.py`
- runtime routing logic
- checkpoint persistence implementation
- live OpenHands/Robin integration logic

Reason:
- the contract surface is now coherent enough for deterministic types
- the live runtime is still not cleanly proven

### Broad Garage integration coding
**NOT READY**

Reason:
- this document predates the post-action observation-path fix
- later contract-stage work still remained after this point even though the specific post-action runtime defect was closed

## 2. WHAT CHANGED SINCE THE ORIGINAL AUDIT

### Closed blocker: Alfred authority gap

Added:

- [ALFRED_MASTER_CONTRACT_v_0_2.md](/home/dev/OH_SHOP/docs/architecture/ALFRED_MASTER_CONTRACT_v_0_2.md)

That contract now explicitly fixes:

- Alfred owns `task_id`, `job_id`, `event_id`, `checkpoint_id`, optional `artifact_id`
- Alfred owns official shell records
- Alfred owns linkage and route metadata
- Alfred owns refs/pointers to worker outputs
- Alfred does not own semantic meaning
- Alfred does not semantically judge payload truth
- Alfred does not own worker workspaces by default
- Alfred is a deterministic manifest clerk, not an AI reasoner

### Closed blocker: shared-language mismatch

Reconciled across:

- [ai_garage_library_and_policy_contract_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/ai_garage_library_and_policy_contract_v_0_1.md)
- [garage_universal_language_dictionary_v0_1.md](/home/dev/OH_SHOP/docs/architecture/garage_universal_language_dictionary_v0_1.md)

Primary authority for exact machine tokens:

- [garage_universal_language_dictionary_v0_1.md](/home/dev/OH_SHOP/docs/architecture/garage_universal_language_dictionary_v0_1.md)

Reconciled required core call library:

1. `task.create`
2. `plan.record`
3. `job.start`
4. `child_job.request`
5. `checkpoint.create`
6. `continuation.record`
7. `result.submit`
8. `failure.report`

Optional alias / deferred surface:

- `assignment.dispatch` = optional alias / derived surface
- `assignment.accept` = optional alias / derived surface
- `context.request` = deferred from v0.1 core

### Cleaned supporting-doc authority boundary

Added explicit authority notes to:

- [JARVIS_WORKBENCH_AND_PROGRESSION_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/archive/architecture/jarvis/JARVIS_WORKBENCH_AND_PROGRESSION_CONTRACT_v_0_1.md)
- [JARVIS_WORKBENCH_EXAMPLES_v_0_1.md](/home/dev/OH_SHOP/docs/archive/architecture/jarvis/JARVIS_WORKBENCH_EXAMPLES_v_0_1.md)

Those files remain useful, but they are no longer allowed to masquerade as canonical machine-token authority.

## 3. CURRENT OPEN BLOCKERS

| Blocker ID | Category | Status | Exact problem | Why it still blocks broader work |
|---|---|---|---|---|
| B03 | Runtime model authority | CLOSED | `garagectl` now detects the currently loaded LM Studio model, syncs OpenHands to `openai/<loaded-model-id>`, and injects the same model into `stagehand-mcp` at bring-up. One-cycle verify now passes Layers 1-5 with `qwen/qwen3.5-9b`. | No longer blocking ID/types work or verifier alignment. |
| B04 | Browser proof failure | CLOSED / HISTORICAL | This document originally tracked the post-action browser proof failure as open. That defect was later investigated and fixed in [post_action_observation_path_investigation.md](/home/dev/OH_SHOP/docs/current/post_action_observation_path_investigation.md). | No longer a current blocker; preserve here only as historical stage context. |
| B05 | Agent-server build skew | OPEN / DEBT | The agent-server override still overlays `1.11.4` Python packages on a pinned base-image family. | Not an immediate blocker for `alfred/ids.py`, but still blocks clean runtime confidence. |

## 4. ID POLICY CODING DECISION

**APPROVED**

It is now safe to code:

- `task_id`
- `job_id`
- `event_id`
- `checkpoint_id`
- optional `artifact_id`
- `parent_job_id`
- `attempt_no`
- same-job return rule
- retry-with-same-job rule
- new-job-for-materially-new-request rule

Reason:

- those rules are now explicitly consistent across the Alfred contract, the dictionary, and the shared policy contract
- they do not depend on the unresolved model/runtime defect

## 5. EXACT NEXT APPROVED CODING MOVE

Write, in order:

1. `alfred/ids.py`
2. `alfred/types.py`

`alfred/types.py` should be limited to:

- shell-envelope fields
- route/linkage metadata fields
- ID-bearing ref/pointer objects
- non-semantic status enums that are already reconciled

Do **not** start yet:

- `alfred/store.py`
- event persistence tables
- runtime callback wiring
- OpenHands/Robin route integration

## 6. RUNTIME STATUS

**Historical stage snapshot**

What I checked in this pass:

- `garagectl` now detects the loaded LM Studio model via `lms ps`
- OpenHands is synced to `openai/qwen/qwen3.5-9b`
- `stagehand-mcp` was restarted with `STAGEHAND_MODEL=qwen/qwen3.5-9b`
- one-cycle `verify` now passes Layers 1 through 5
- the configured MCP path is still `http://host.docker.internal:3020/mcp`
- the runtime/browser proof was later fixed; this section is preserved as a historical snapshot of the stage before that fix

Live settings evidence:

```json
{
  "llm_model": "openai/qwen/qwen3.5-9b",
  "llm_base_url": "http://host.docker.internal:1234/v1",
  "mcp_config": {
    "shttp_servers": [
      {
        "url": "http://host.docker.internal:3020/mcp"
      }
    ]
  }
}
```

Live LM Studio `/v1/models` evidence:

```json
[
  "qwen/qwen3-vl-8b",
  "nebius-swe-rebench-openhands-qwen3-30b-a3b",
  "qwen/qwen3.5-9b",
  "mistralai/devstral-small-2-2512",
  "text-embedding-nomic-embed-text-v1.5"
]
```

Live verifier result after dynamic sync:

- Layers 1-5: PASS
- Layer 6: still intentionally unproven

Smoke result after dynamic sync:

- browser tool action was reached
- final execution status: `stuck`
- outcome classification: `provider/dependency failure`
- detail: timed out after the browser tool action but before a successful observation was captured

Historical runtime blocker at the time of this follow-up:

- browser/tool execution had not yet been proven cleanly even after model authority was aligned

## 7. PATH NOTE

The original readiness request named several older runtime-stabilization files such as:

- `docs/runtime_stabilization_contract_v_0.md`
- `docs/runtime_stabilization/canonical_proof_spec.md`
- `docs/runtime_stabilization/runtime_stabilization_summary.md`
- `docs/runtime_stabilization/config_authority.md`
- `docs/runtime_stabilization/final_reply_investigation/instrumentation_notes.md`
- `docs/runtime_stabilization/final_reply_investigation/failure_classification.md`

Those paths are not present in this branch anymore.

Current active authority used instead:

- [repo_readiness_audit_for_schema_coding.md](/home/dev/OH_SHOP/docs/current/repo_readiness_audit_for_schema_coding.md)
- [shared_language_reconciliation_report.md](/home/dev/OH_SHOP/docs/current/shared_language_reconciliation_report.md)
- [master_intent_brief.md](/home/dev/OH_SHOP/docs/runtime/stabilization/master_intent_brief.md)
- [SETUP.md](/home/dev/OH_SHOP/docs/current/SETUP.md)
- [TROUBLESHOOTING.md](/home/dev/OH_SHOP/docs/current/TROUBLESHOOTING.md)

## 8. BOTTOM LINE

The repo is now ready for:

- isolated ID policy coding
- shell/type-layer Alfred foundation work

The repo is not yet ready for:

- runtime-coupled Alfred behavior coding
- broad universal schema persistence work
- broad Garage integration coding

The next move is not more contract cleanup.
The next move is to write:

1. `alfred/ids.py`
2. then `alfred/types.py`

and leave runtime integration alone until the model-authority defect is closed.
