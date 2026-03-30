# Repo Readiness Audit for Schema Coding Follow-Up

Date: 2026-03-30
Repo: `/home/dev/OH_SHOP`
Branch: `master`

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
- the runtime model authority mismatch remains unresolved
- the canonical browser smoke still fails before first useful reply/tool proof

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

- [JARVIS_WORKBENCH_AND_PROGRESSION_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/JARVIS_WORKBENCH_AND_PROGRESSION_CONTRACT_v_0_1.md)
- [JARVIS_WORKBENCH_EXAMPLES_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/JARVIS_WORKBENCH_EXAMPLES_v_0_1.md)

Those files remain useful, but they are no longer allowed to masquerade as canonical machine-token authority.

## 3. CURRENT OPEN BLOCKERS

| Blocker ID | Category | Status | Exact problem | Why it still blocks broader work |
|---|---|---|---|---|
| B03 | Runtime model authority | OPEN | OpenHands is configured for `openai/qwen3-coder-30b-a3b-instruct`, Stagehand uses `qwen3-coder-30b-a3b-instruct`, but LM Studio does not expose that exact usable model ID in `/v1/models`. | Live runtime proof remains unreliable. |
| B04 | Browser proof failure | OPEN | Fresh browser smoke still goes `running -> error` before assistant reply or tool observation. | Runtime integration is not proven enough for broad Garage wiring. |
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

**Still blocked**

What I checked in this pass:

- the configured OpenHands model is still `openai/qwen3-coder-30b-a3b-instruct`
- the configured LM Studio base URL is still `http://host.docker.internal:1234/v1`
- the configured MCP path is still `http://host.docker.internal:3020/mcp`
- the runtime/browser proof remains blocked because model authority is still unresolved

Live settings evidence:

```json
{
  "llm_model": "openai/qwen3-coder-30b-a3b-instruct",
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

I did **not** change runtime model settings in this pass.

Reason:

- there is not yet one repo-authoritative winning model string that can be applied without guessing

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
