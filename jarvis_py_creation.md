# garage_jarvis.py Creation Plan

## 1. Context I actually have in this Copilot chat

**Grounded from prior turn reads:**
- `project_state_human_readable_2026-04-01.md` — full
- `contract_stage_review_after_plan_and_handoff.md` — full
- `AI_GARAGE_BLUEPRINT.MD.md` — first ~300 lines (roles, architecture, baton-pass)
- `JARVIS_MASTER_CONTRACT_v_0_2.md` — first ~250 lines (identity, ownership, OpenHands posture)
- `ALFRED_MASTER_CONTRACT_v_0_2.md` — first ~250 lines (identity, shell ownership, ID minting)
- `ROBIN_MASTER_CONTRACT_v_0_3.md` — first ~250 lines (identity, browser specialist, delegation boundary)
- `ai_garage_library_and_policy_contract_v_0_1.md` — full
- `LIBRARY_SCHEMA_CONTRACT_v_0_1.md` — first ~200 lines (schema set, call library)
- `TRACKED_PLAN_OBJECT_CONTRACT_v_0_1.md` — first ~200 lines (header, items, ownership)
- `HANDOFF_ENVELOPE_CONTRACT_v_0_1.md` — first ~200 lines (shell/body, ownership, fields)
- `garage_schemas.py` — full (GarageSchemaRegistry, validation)
- `garage_boundaries.py` — full (boundary wrappers)
- `garage_runtime.py` — full (GarageRuntimeProcessor)
- `garage_alfred.py` — first 400 lines + full method index (4413 lines total)
- `garage_storage.py` — first 700 lines + full method index (3806 lines total)
- `build_storage_backed_alfred_processor` — full (lines 3785-3806)
- All test files — read or sampled
- `pyrightconfig.json` — full
- 45 JSON schemas confirmed present

**Grounded from this turn reads:**
- `CALL_AND_EVENT_OBJECT_CONTRACT_v_0_1.md` — first ~200 lines (call vs event object distinction)
- `ARTIFACT_AND_PROOF_CONTRACT_v_0_1.md` — first ~200 lines (artifact/evidence/proof chain)
- `garagectl.py` — full CLI surface, `_sync_model_authority`, `_detect_loaded_lm_studio_model`, `_persist_openhands_model_settings`, `_sync_live_openhands_settings`
- `garage_alfred.py` full public API index (160+ methods, 8 call handlers + receipt/continuation/guard/rebase chain)
- `garage_storage.py` full public API index (90+ methods, including policy/posture/proof/resume surfaces)

## 2. Critical facts verified

- **One-model-slot baton-pass**: `garagectl.py` already has `_sync_model_authority` / `_detect_loaded_lm_studio_model` / `_persist_openhands_model_settings` / `_sync_live_openhands_settings`. This is the existing model-switch plumbing. It currently operates on a single detected LM Studio model. It does NOT yet support Jarvis↔Robin role switching — it only syncs whatever single model is currently loaded.
- **Alfred call surface**: `GarageAlfredProcessor.process_call()` is the main entry. It handles 8 call types: `task.create`, `plan.record`, `job.start`, `child_job.request`, `result.submit`, `failure.report`, `checkpoint.create`, `continuation.record`.
- **Storage-backed processor**: `build_storage_backed_alfred_processor(root)` returns `(GarageStorageAdapter, GarageAlfredProcessor)` with SQLite persistence, ID minting, and full state reader wired in.
- **Task state summary**: `storage.latest_task_state_summary(task_id)` returns a massive dict with posture, policy, proof state, allowed calls, best next move, resume anchor, plan linkage.
- **No Jarvis or Robin runtime code exists yet.**
- **No orchestration loop exists yet.**

## 3. Updated contract-safe interpretation

- Jarvis = AI model (loaded in LM Studio) + OpenHands workbench. NOT a Python brain.
- Robin = AI model (VL/browser-capable, loaded in LM Studio) + Stagehand browser surface. NOT a Python helper.
- Alfred = deterministic controller. Already heavily implemented in `garage_alfred.py` + `garage_storage.py`.
- `garage_jarvis.py` must be a **thin adapter/harness/bridge** between the Jarvis AI worker and the Alfred call surface. It is plumbing, not brain.
- The baton-pass model-slot switch (Jarvis model → Robin model → Jarvis model) is **Alfred/runtime-controller responsibility**, not Jarvis adapter responsibility. The existing `garagectl.py` model-sync plumbing is the seed for that — it needs to be extended later but NOT inside `garage_jarvis.py`.
- OpenHands local state (scratch files, local checklists, local tracker items) is NOT Garage truth. Only data promoted through Alfred calls becomes official.

## 4. What garage_jarvis.py must consist of

### A. JarvisSessionContext (dataclass)
Holds the current working context for one Jarvis session:
- `task_id: str | None`
- `job_id: str | None`
- `plan_version: int | None`
- `current_active_item: str | None`
- `resume_anchor: dict | None`
- `continuation_context: dict | None`
- `workspace_root: Path`

### B. JarvisAlfredBridge (class)
Thin bridge to the Alfred call surface. Wraps `GarageAlfredProcessor` / storage-backed processor.

Public methods — one per official call type relevant to Jarvis:
- `create_task(objective: str) -> GarageProcessingResult`
- `record_plan(task_id, plan_version, items, current_active_item) -> GarageProcessingResult`
- `start_job(task_id, job_id) -> GarageProcessingResult`
- `request_child_job(task_id, job_id, objective, ...) -> GarageProcessingResult`
- `submit_result(task_id, job_id, reported_status, artifact_refs, payload_ref) -> GarageProcessingResult`
- `report_failure(task_id, job_id, reported_status, payload_ref) -> GarageProcessingResult`
- `create_checkpoint(task_id, job_id, plan_version, artifact_refs) -> GarageProcessingResult`
- `record_continuation(task_id, job_id, payload_ref, plan_version, artifact_refs) -> GarageProcessingResult`

Each method:
1. Builds the correct call envelope dict
2. Calls `processor.process_call(envelope)`
3. Returns the result

This is pure plumbing — no semantic logic, no policy duplication.

### C. JarvisStateReader (class or methods)
Thin read-side helpers that expose task/plan/proof state from storage to the Jarvis workbench context:
- `read_task_summary(task_id) -> dict | None` — wraps `storage.latest_task_state_summary()`
- `read_active_plan(task_id) -> dict | None` — wraps `storage.read_active_plan_summary()`
- `read_resume_anchor(task_id) -> dict | None` — wraps `storage.resolve_task_resume_anchor()`
- `read_job_summary(job_id) -> dict | None` — wraps `storage.read_job_state_summary()`
- `allowed_next_calls(task_id) -> tuple[str, ...] | None` — wraps `storage.allowed_supported_call_types()`
- `best_next_move(task_id) -> dict | None` — wraps `storage.best_next_supported_move()`

### D. JarvisSessionBootstrap (function or classmethod)
Creates a Jarvis session from either:
- **Fresh start**: no existing task → returns context ready for `create_task`
- **Resume**: existing task_id → loads task summary, resume anchor, continuation context, active plan

### E. JarvisRobinDelegationHelper (small helper or methods)
Constructs a well-formed `child_job.request` call for Robin delegation:
- Takes objective, constraints, expected_output, success_criteria, allowed_domains, retry_budget
- Routes through `JarvisAlfredBridge.request_child_job()`
- Stops. Does NOT try to execute the Robin leg.

### F. JarvisWorkbenchContext (small helper)
Exposes the current step's official context for the Jarvis AI to consume:
- Current plan item
- Current proof requirements
- Allowed next calls
- Resume/continuation state
- What evidence is needed

This is a **read-only view** for the workbench, not a controller.

## 5. What garage_jarvis.py must NOT consist of

- NO reasoning engine / planner brain / semantic verifier
- NO policy evaluation (that's Alfred/storage)
- NO model loading / model switching (that's garagectl / future runtime controller)
- NO OpenHands API client (that's a separate adapter layer)
- NO Stagehand/browser interaction (that's Robin)
- NO workflow orchestration loop (that's a separate orchestrator)
- NO call type invention (use only the existing 8)
- NO status token invention
- NO receipt/continuation/guard/rebase chain reimplementation (that's already in Alfred)
- NO duplication of `latest_task_state_summary` assembly logic
- NO hardcoded reasoning trees

## 6. How Jarvis/Robin model-slot switching must be treated later

The baton-pass model switch is NOT part of `garage_jarvis.py`. It belongs in a future runtime controller layer. Here's where it needs to land:

1. **When Alfred processes `child_job.request` with `to_role: robin`**:
   - The orchestrator (not Jarvis adapter) detects Robin delegation
   - It calls existing `garagectl._sync_model_authority` (or its successor) to switch LM Studio to the Robin VL model
   - It realigns OpenHands/Stagehand MCP settings for blog browser work
   - It activates the Robin adapter (`garage_robin.py`)

2. **When Robin's `result.submit` or `failure.report` returns through Alfred**:
   - The orchestrator detects return-to-Jarvis
   - It switches LM Studio back to the Jarvis reasoning model
   - It realigns OpenHands settings for Jarvis work
   - It resumes the Jarvis adapter with continuation context

3. **`garage_jarvis.py` role**:
   - Must NOT trigger model switches itself
   - Must expose hooks/signals that let the orchestrator know when delegation is requested
   - `request_child_job()` return value naturally signals this — the orchestrator reads `child_job.request` result and acts

4. **`garage_robin.py` role** (future):
   - Parallel thin adapter for Robin
   - Same pattern: bridge to Alfred calls, state reader, session context
   - Must NOT trigger model switches itself

5. **Model switch controller** (future):
   - Lives in `garagectl.py` extension or a new `garage_orchestrator.py`
   - Deterministic, not AI
   - Owns: detect role transition → switch model → realign settings → activate correct adapter

## 7. Smallest correct first implementation slice

The minimum viable `garage_jarvis.py` for this first cut:

```
JarvisSessionContext       — dataclass, ~15 lines
JarvisAlfredBridge         — 8 call methods + constructor, ~120 lines
JarvisStateReader          — 6 read methods, ~50 lines
bootstrap_jarvis_session() — fresh + resume paths, ~40 lines
build_child_job_request()  — Robin delegation helper, ~30 lines
build_jarvis_workbench_context() — read-only view assembly, ~30 lines
```

Estimated total: ~300 lines. Thin, correct, contract-safe.

**Test file**: `test_garage_jarvis.py`
- Test each bridge method produces correct call envelopes
- Test bootstrap from fresh and from existing task
- Test state reader methods return expected shapes
- Test child job request builder produces valid delegation call

Estimated: ~200 lines.

## 8. Files to create/update

### Create:
1. `ops/garage_jarvis.py` — the Jarvis adapter/harness
2. `ops/test_garage_jarvis.py` — tests for the adapter

### Do NOT update:
- `garage_alfred.py` — no changes needed
- `garage_storage.py` — no changes needed
- `garage_runtime.py` — no changes needed
- `garage_boundaries.py` — no changes needed
- `garagectl.py` — no changes needed in this phase

## 9. Any blocker

**No blockers.** The Alfred call surface, storage adapter, schema registry, and test fixtures all exist and are sufficient to build the Jarvis adapter against. The adapter is pure integration/plumbing and requires no new contracts or schema changes.
