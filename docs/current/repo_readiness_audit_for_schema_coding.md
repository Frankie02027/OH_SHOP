# Repo Readiness Audit for Schema Coding

Date: 2026-03-30
Repo: `/home/dev/OH_SHOP`
Branch: `master`

## 1. EXECUTIVE VERDICT

### Universal library schema coding
**NOT READY**

Reason:
- the shared call/event language is not frozen
- the repo has no current Alfred master contract in the working tree
- the live runtime still fails the browser smoke after sandbox creation because the configured OpenHands model does not exist in LM Studio `/v1/models`

### ID policy coding
**READY, BUT ONLY IN ISOLATION**

Reason:
- the ID rules are explicit and internally coherent in [garage_universal_language_dictionary_v0_1.md](/home/dev/OH_SHOP/docs/architecture/garage_universal_language_dictionary_v0_1.md)
- the Jarvis and Robin v0.2 contracts do not contradict those rules
- this is the one part of the schema surface that is stable enough to encode now if work is deliberately limited to ID minting/parsing/relationship rules

### Early Alfred foundation coding
**NOT READY**

Reason:
- there is no current Alfred contract file in the repo
- the shared top-level call library is inconsistent across current authorities
- the runtime is not fully proven against the current model authority

### Broad Garage integration coding
**NOT READY**

Reason:
- live runtime proof still fails
- the browser lane is not proven end-to-end under the current model authority
- Alfred’s contract boundary is still implied by other docs instead of defined directly

## 2. BLOCKER TABLE

| Blocker ID | Category | Exact files involved | Exact problem | Why it blocks coding | Fixable now | Proposed fix | Status after this pass |
|---|---|---|---|---|---|---|---|
| B01 | Authority gap | `docs/architecture/ALFRED_MASTER_CONTRACT_v_0_1.md` (missing), `docs/architecture/ALFRED_MASTER_CONTRACT_v_0_2.md` (missing), [AI_GARAGE_BLUEPRINT.MD.md](/home/dev/OH_SHOP/docs/architecture/AI_GARAGE_BLUEPRINT.MD.md), [ai_garage_library_and_policy_contract_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/ai_garage_library_and_policy_contract_v_0_1.md) | There is no current Alfred contract in the working tree. Alfred is referenced everywhere, but not directly specified as a current authority file. | `alfred/store.py`, routing logic, checkpoint rules, and metadata validation logic would be coded against inference instead of settled authority. | No, not safely in this pass | Write the Alfred master contract before coding Alfred behavior/storage beyond IDs. | OPEN |
| B02 | Contract inconsistency | [ai_garage_library_and_policy_contract_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/ai_garage_library_and_policy_contract_v_0_1.md), [garage_universal_language_dictionary_v0_1.md](/home/dev/OH_SHOP/docs/architecture/garage_universal_language_dictionary_v0_1.md) | The top-level call library does not match. Shared policy says required core calls are `task.create`, `assignment.dispatch`, `assignment.accept`, `child_job.request`, `context.request`, `checkpoint.create`, `result.submit`, `failure.report`. The dictionary instead centers `task.create`, `plan.record`, `job.start`, `child_job.request`, `result.submit`, `failure.report`, `checkpoint.create`, `continuation.record`, and treats `assignment.dispatch` / `assignment.accept` as optional aliases. | This blocks coding stable enums, SQL tables, and JSON record schemas for `call_type` and events. | Not safely without choosing a winning authority | Reconcile the shared policy contract and dictionary into one v0.2 shared language authority before coding library enums. | OPEN |
| B03 | Runtime authority / provider mismatch | [data/openhands/settings.json](/home/dev/OH_SHOP/data/openhands/settings.json), [compose/docker-compose.yml](/home/dev/OH_SHOP/compose/docker-compose.yml), [SETUP.md](/home/dev/OH_SHOP/docs/current/SETUP.md), [browser_smoke_audit_run_after_lms_restart.md](/home/dev/OH_SHOP/docs/current/browser_smoke_audit_run_after_lms_restart.md) | OpenHands is configured for `openai/qwen3-coder-30b-a3b-instruct`, but LM Studio currently exposes `qwen/qwen3-vl-8b`, `nebius-swe-rebench-openhands-qwen3-30b-a3b`, `qwen/qwen3.5-9b`, `mistralai/devstral-small-2-2512`, and `text-embedding-nomic-embed-text-v1.5`. The configured backend model string is absent from `/v1/models`. | Live proof fails before assistant reply or tool observation. Any coding that assumes the current OpenHands/Robin lane is validated would be false. | Partially. I safely restored the LM Studio server, but did not change model authority because the winning model name is not settled in repo authority. | Decide the canonical model identifier, then update persisted settings, runtime docs, and Stagehand/OpenHands config together or expose the expected alias from LM Studio. | OPEN |
| B04 | Live proof failure | [browser_smoke_audit_run.md](/home/dev/OH_SHOP/docs/current/browser_smoke_audit_run.md), [browser_smoke_audit_run_after_lms_restart.md](/home/dev/OH_SHOP/docs/current/browser_smoke_audit_run_after_lms_restart.md), `data/openhands/v1_conversations/b9fbd613e49942588d7119ce9660f7ab/*.json` | Fresh smoke still goes `idle -> running -> error` with no assistant reply and no tool observation. The conversation trace shows the browser tool set is present and MCP is injected, but the run dies immediately after start. | Broad Garage integration coding is not ready while the canonical browser proof still fails. | Not safely in this pass because the likely root cause is the unresolved model authority mismatch, not a trivial doc bug. | Fix B03 first, then rerun proof before integrating higher-level Garage coding. | OPEN |
| B05 | Runtime build debt | [compose/agent_server_override/Dockerfile](/home/dev/OH_SHOP/compose/agent_server_override/Dockerfile), [compose/docker-compose.yml](/home/dev/OH_SHOP/compose/docker-compose.yml) | The agent-server image still mixes a pinned base image family (`61470a1-python`) with separately installed `openhands-agent-server==1.11.4`, `openhands-sdk==1.11.4`, and `openhands-tools==1.11.4`. | This is not an immediate blocker for ID utilities, but it is a stability blocker for claiming the runtime is clean enough for early Alfred integration. | No, not safely without a dedicated proof pass | Resolve base/package family skew in a narrow runtime pass after model authority is fixed. | OPEN |

## 3. CONTRACT CONSISTENCY TABLE

| Check | Result | Evidence | Notes |
|---|---|---|---|
| Alfred owns IDs | PASS | [ai_garage_library_and_policy_contract_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/ai_garage_library_and_policy_contract_v_0_1.md), [garage_universal_language_dictionary_v0_1.md](/home/dev/OH_SHOP/docs/architecture/garage_universal_language_dictionary_v0_1.md), [JARVIS_MASTER_CONTRACT_v_0_2.md](/home/dev/OH_SHOP/docs/architecture/JARVIS_MASTER_CONTRACT_v_0_2.md), [ROBIN_MASTER_CONTRACT_v_0_2.md](/home/dev/OH_SHOP/docs/architecture/ROBIN_MASTER_CONTRACT_v_0_2.md) | All current authorities agree that Jarvis/Robin do not mint official IDs. |
| Alfred owns shell / route metadata | PASS | [ai_garage_library_and_policy_contract_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/ai_garage_library_and_policy_contract_v_0_1.md), [garage_universal_language_dictionary_v0_1.md](/home/dev/OH_SHOP/docs/architecture/garage_universal_language_dictionary_v0_1.md), [JARVIS_MASTER_CONTRACT_v_0_2.md](/home/dev/OH_SHOP/docs/architecture/JARVIS_MASTER_CONTRACT_v_0_2.md), [ROBIN_MASTER_CONTRACT_v_0_2.md](/home/dev/OH_SHOP/docs/architecture/ROBIN_MASTER_CONTRACT_v_0_2.md) | Shell/body separation is consistent. |
| Workers own semantic body | PASS | Same files as above | The shared language stack is aligned here. |
| Same-job-id return rule | PASS | [garage_universal_language_dictionary_v0_1.md](/home/dev/OH_SHOP/docs/architecture/garage_universal_language_dictionary_v0_1.md) | Explicitly fixed in dictionary; no current contract contradicts it. |
| Retry rule (`same job_id`, increment `attempt_no`) | PASS | [garage_universal_language_dictionary_v0_1.md](/home/dev/OH_SHOP/docs/architecture/garage_universal_language_dictionary_v0_1.md) | Explicitly defined; no contradictions found. |
| New-job rule for materially new/refined request | PASS | [garage_universal_language_dictionary_v0_1.md](/home/dev/OH_SHOP/docs/architecture/garage_universal_language_dictionary_v0_1.md) | Explicitly defined; no contradictions found. |
| Garage language stays separate from OpenHands / Stagehand substrate language | PASS | [JARVIS_MASTER_CONTRACT_v_0_2.md](/home/dev/OH_SHOP/docs/architecture/JARVIS_MASTER_CONTRACT_v_0_2.md), [ROBIN_MASTER_CONTRACT_v_0_2.md](/home/dev/OH_SHOP/docs/architecture/ROBIN_MASTER_CONTRACT_v_0_2.md), [AI_GARAGE_BLUEPRINT.MD.md](/home/dev/OH_SHOP/docs/architecture/AI_GARAGE_BLUEPRINT.MD.md) | The v0.2 Robin contract is especially explicit that role != wrapper export list. |
| Worker workspace ownership vs Alfred pointer-ledger model | PASS | [garage_universal_language_dictionary_v0_1.md](/home/dev/OH_SHOP/docs/architecture/garage_universal_language_dictionary_v0_1.md), [master_intent_brief.md](/home/dev/OH_SHOP/docs/runtime/stabilization/master_intent_brief.md) | Alfred tracks refs and pointers; workers own workspace outputs. |
| Small top-level call library consistency | FAIL | [ai_garage_library_and_policy_contract_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/ai_garage_library_and_policy_contract_v_0_1.md) vs [garage_universal_language_dictionary_v0_1.md](/home/dev/OH_SHOP/docs/architecture/garage_universal_language_dictionary_v0_1.md) | This is the main semantic blocker for coding shared call enums and event records. |
| Event library consistency | FAIL | Same two files | `assignment.dispatched` / `assignment.accepted` / `plan.created` in shared policy do not cleanly match `plan.recorded`, `job.started`, `continuation.recorded`, and optional alias treatment in dictionary. |

## 4. RUNTIME / BUILD TRUTH TABLE

| Item | Current truth | Status |
|---|---|---|
| Canonical startup path | `python3 ops/garagectl.py up` | PASS |
| Canonical shutdown path | `python3 ops/garagectl.py down` | PASS |
| Canonical verify path | `python3 ops/garagectl.py verify` | PASS |
| Canonical browser lane | `stagehand-mcp` from [vendor/stagehand_mcp](/home/dev/OH_SHOP/vendor/stagehand_mcp), exposed to OpenHands at `http://host.docker.internal:3020/mcp` | PASS |
| Canonical provider path | `http://host.docker.internal:1234/v1` | PASS after local operational fix |
| Current OpenHands settings truth | `llm_model=openai/qwen3-coder-30b-a3b-instruct`, `llm_base_url=http://host.docker.internal:1234/v1`, `mcp_config.shttp_servers[0].url=http://host.docker.internal:3020/mcp` in both live API and persisted settings | PASS |
| OpenHands base image authority | Pinned by digest in [compose/openhands_override/Dockerfile](/home/dev/OH_SHOP/compose/openhands_override/Dockerfile) | PASS |
| OpenWebUI image authority | Pinned by digest in [compose/docker-compose.yml](/home/dev/OH_SHOP/compose/docker-compose.yml) | PASS |
| Stagehand MCP build authority | Built from lockfile-backed [package-lock.json](/home/dev/OH_SHOP/vendor/stagehand_mcp/package-lock.json), but base image is still `node:20-slim` in [vendor/stagehand_mcp/Dockerfile](/home/dev/OH_SHOP/vendor/stagehand_mcp/Dockerfile) | WARNING |
| Agent-server family skew | Base image is pinned to one family while packages are overlaid from `1.11.4` in [compose/agent_server_override/Dockerfile](/home/dev/OH_SHOP/compose/agent_server_override/Dockerfile) | FAIL / DEBT |
| Patch fragmentation | App patches are centralized in [apply_runtime_patches.py](/home/dev/OH_SHOP/compose/openhands_override/apply_runtime_patches.py), but runtime behavior still depends on that patch script plus compat converter overrides plus Stagehand adapter shims | WARNING |
| Current unresolved runtime defects | Fresh browser smoke still fails `running -> error` before assistant reply or tool observation. Verify now passes layers 1-4 and most of 5, but still fails model inventory alignment. | FAIL |

## 5. FILE DISPOSITION TABLE

| Path | Disposition | Why |
|---|---|---|
| [AI_GARAGE_BLUEPRINT.MD.md](/home/dev/OH_SHOP/docs/architecture/AI_GARAGE_BLUEPRINT.MD.md) | authoritative | Current high-level architecture intent. |
| [ai_garage_library_and_policy_contract_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/ai_garage_library_and_policy_contract_v_0_1.md) | authoritative, rewrite candidate | Strong shell/body and role language, but call/event library now conflicts with the dictionary. |
| [garage_universal_language_dictionary_v0_1.md](/home/dev/OH_SHOP/docs/architecture/garage_universal_language_dictionary_v0_1.md) | authoritative | Best current source for IDs, shell fields, pointer refs, retry/new-job rule. |
| [JARVIS_MASTER_CONTRACT_v_0_2.md](/home/dev/OH_SHOP/docs/architecture/JARVIS_MASTER_CONTRACT_v_0_2.md) | authoritative supporting role contract | Current Jarvis role authority. |
| [ROBIN_MASTER_CONTRACT_v_0_2.md](/home/dev/OH_SHOP/docs/architecture/ROBIN_MASTER_CONTRACT_v_0_2.md) | authoritative supporting role contract | Current Robin role authority and good substrate separation. |
| [master_intent_brief.md](/home/dev/OH_SHOP/docs/runtime/stabilization/master_intent_brief.md) | supporting | Clean architecture/runtime intent summary, not detailed schema authority. |
| [SETUP.md](/home/dev/OH_SHOP/docs/current/SETUP.md) | authoritative runtime truth | Correct current ops/runtime surface. |
| [TROUBLESHOOTING.md](/home/dev/OH_SHOP/docs/current/TROUBLESHOOTING.md) | authoritative runtime support | Correct current control surface. |
| [compose/docker-compose.yml](/home/dev/OH_SHOP/compose/docker-compose.yml) | authoritative runtime truth | Current service/build authority. |
| [compose/openhands_override/Dockerfile](/home/dev/OH_SHOP/compose/openhands_override/Dockerfile) | authoritative runtime build | Pinned build-time truth for OpenHands app image. |
| [compose/agent_server_override/Dockerfile](/home/dev/OH_SHOP/compose/agent_server_override/Dockerfile) | supporting, debug-first | Live runtime build file, but still carries version-family skew. |
| [apply_runtime_patches.py](/home/dev/OH_SHOP/compose/openhands_override/apply_runtime_patches.py) | supporting, debug-first | Centralized patch layer, still brittle but active. |
| [server.ts](/home/dev/OH_SHOP/vendor/stagehand_mcp/src/server.ts) | supporting implementation bridge | Current Stagehand MCP adapter, not role authority. |
| `docs/runtime_stabilization_contract_v_0.md` and related old paths named in the request | historical / absent | Those files are not present in this branch anymore. Current runtime truth is under `docs/current/` and historical residue has already been cleaned or archived. |
| `docs/architecture/ALFRED_MASTER_CONTRACT_v_0_1.md` / `v_0_2.md` | missing | This is a real authority gap, not a typo. |

## 6. SAFE FIXES APPLIED

### Operational fix applied
- Restored the LM Studio server with `lms server start` after confirming `lms status` was `OFF`.

Result:
- provider reachability now passes from host, OpenHands, OpenWebUI, and stagehand-mcp
- this removed one false blocker and exposed the real remaining blocker: model authority mismatch

### Repo files changed in this pass
- [repo_readiness_audit_for_schema_coding.md](/home/dev/OH_SHOP/docs/current/repo_readiness_audit_for_schema_coding.md)
  - Added as the authoritative readiness report for the current branch state.

### Runtime evidence artifacts generated by verification
- [browser_smoke_audit_run.md](/home/dev/OH_SHOP/docs/current/browser_smoke_audit_run.md)
- [browser_smoke_audit_run_after_lms_restart.md](/home/dev/OH_SHOP/docs/current/browser_smoke_audit_run_after_lms_restart.md)

### No low-risk contract rewrites were applied
I did **not** rewrite the shared policy contract or model settings in this pass because:
- the winning authority for the top-level call library has not been explicitly chosen
- the model-name mismatch is real, but changing persisted settings or docs without choosing the canonical model would be speculative

## 7. NEXT APPROVED CODING START POINT

### Broad schema coding
**Not approved yet**

Do **not** start with:
- broad library call enums
- event enums
- `alfred/store.py`
- checkpoint/result persistence tables
- broad Garage integration wiring

### Narrow coding that is safe now
If you need to begin coding before the remaining blockers are closed, the only sane start point is:

1. `alfred/ids.py`
2. optional companion tests for ID parsing / formatting / relationship rules

That work should be derived only from:
- [garage_universal_language_dictionary_v0_1.md](/home/dev/OH_SHOP/docs/architecture/garage_universal_language_dictionary_v0_1.md) sections for `task_id`, `job_id`, `event_id`, `checkpoint_id`, `artifact_id`, `attempt_no`, `parent_job_id`, retry rules, and return rules

### What should be written first after blockers close
Once B01 and B02 are closed, the approved sequence is:

1. `alfred/ids.py`
2. `alfred/types.py`
   - `CallEnvelope`
   - pointer/ref objects
   - worker-reported status enums
3. `alfred/store.py`
   - only after call/event vocabulary is reconciled

## Key Evidence From This Pass

- `git branch --show-current` -> `master`
- Requested old runtime authority files were absent:
  - `docs/runtime_stabilization_contract_v_0.md`
  - `docs/runtime_stabilization/canonical_proof_spec.md`
  - `docs/runtime_stabilization/runtime_stabilization_summary.md`
  - `docs/runtime_stabilization/config_authority.md`
  - `docs/runtime_stabilization/final_reply_investigation/instrumentation_notes.md`
  - `docs/runtime_stabilization/final_reply_investigation/failure_classification.md`
- No Alfred contract file exists in the working tree.
- `python3 ops/garagectl.py verify` initially failed because LM Studio was off, then after `lms server start` it passed provider reachability but still failed layer 5 model inventory alignment.
- `curl -sf http://127.0.0.1:3000/api/settings | jq '{llm_model,llm_base_url,mcp_config}'` matched [data/openhands/settings.json](/home/dev/OH_SHOP/data/openhands/settings.json).
- `curl -sf http://127.0.0.1:1234/v1/models | jq .` showed the configured backend model was absent.
- Fresh smoke after provider restart still failed:
  - [browser_smoke_audit_run_after_lms_restart.md](/home/dev/OH_SHOP/docs/current/browser_smoke_audit_run_after_lms_restart.md)
  - `execution_status` in conversation trace went `running` then `error`
  - no assistant reply
  - no tool observation
  - browser tool set and MCP config were present in the sandbox state

## Bottom Line

The repo is **not ready** for broad universal schema coding or early Alfred foundation coding.

The repo **is** ready for one narrow coding lane only:
- ID policy utilities based on the current dictionary

Before anything broader should be coded, close these in order:

1. choose and write the Alfred master contract
2. reconcile the shared call/event library between the shared policy contract and the universal dictionary
3. resolve the live model authority mismatch so the canonical browser proof can pass
