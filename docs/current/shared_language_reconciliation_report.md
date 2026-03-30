# Shared Language Reconciliation Report

Date: 2026-03-30
Repo: `/home/dev/OH_SHOP`
Branch: `master`

## What was conflicting

The readiness audit found a direct contradiction between:

- [ai_garage_library_and_policy_contract_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/ai_garage_library_and_policy_contract_v_0_1.md)
- [garage_universal_language_dictionary_v0_1.md](/home/dev/OH_SHOP/docs/architecture/garage_universal_language_dictionary_v0_1.md)

The conflict was not stylistic.
It was machine-language drift.

The main mismatches were:

- top-level call library
- event library
- task/job state vocabulary
- whether `assignment.dispatch` / `assignment.accept` are required or optional
- whether `context.request` belongs in v0.1 core
- whether `continuation.record` belongs in v0.1 core
- whether the shared-language contract or the dictionary owns exact token names

## What won

The winning authority for exact machine-language token names is now:

- [garage_universal_language_dictionary_v0_1.md](/home/dev/OH_SHOP/docs/architecture/garage_universal_language_dictionary_v0_1.md)

That file now explicitly states that it is the **primary authority** for:

- core `call_type` names
- core `event_type` names
- official state/status tokens
- ID ownership rules
- retry / return / new-job rules

The shared Library and Policy contract remains authoritative for:

- why the language is shaped this way
- the shell/body design rule
- the policy interpretation layer
- the small-library design principle

But it no longer gets to compete on exact token names.

## What changed

### 1. Alfred authority

Added:

- [ALFRED_MASTER_CONTRACT_v_0_2.md](/home/dev/OH_SHOP/docs/architecture/ALFRED_MASTER_CONTRACT_v_0_2.md)

This closes the prior authority gap.

It now explicitly defines Alfred as:

- deterministic manifest clerk
- official ID authority
- official shell writer/stamper
- linkage/route metadata owner
- pointer/refs clerk, not warehouse owner
- non-semantic, non-reasoning controller

### 2. Shared language reconciliation

Updated:

- [ai_garage_library_and_policy_contract_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/ai_garage_library_and_policy_contract_v_0_1.md)
- [garage_universal_language_dictionary_v0_1.md](/home/dev/OH_SHOP/docs/architecture/garage_universal_language_dictionary_v0_1.md)

The reconciled **required core v0.1 call library** is now:

1. `task.create`
2. `plan.record`
3. `job.start`
4. `child_job.request`
5. `checkpoint.create`
6. `continuation.record`
7. `result.submit`
8. `failure.report`

The reconciled **optional alias / deferred surface** is now:

- `assignment.dispatch` = optional alias / derived surface
- `assignment.accept` = optional alias / derived surface
- `context.request` = deferred from v0.1 core

The reconciled **core v0.1 event library** is now:

- `task.created`
- `plan.recorded`
- `job.created`
- `job.started`
- `job.dispatched`
- `job.returned`
- `job.blocked`
- `job.failed`
- `checkpoint.created`
- `continuation.recorded`
- `artifact.registered`

Tracked-plan/UI-facing events such as:

- `plan.item.started`
- `plan.item.done_unverified`
- `plan.item.verified`
- `plan.item.blocked`

remain valid as supporting plan-tracking events, but they are no longer pretending to be the core cross-role event vocabulary.

The reconciled **state vocabulary** now separates:

- task states
- job states
- plan item states

instead of collapsing task and job states together.

## What did not change

These rules were already aligned and remain aligned:

- Alfred owns official IDs
- Alfred owns official shell/route metadata
- Jarvis and Robin own semantic meaning
- result/failure returns keep the same `job_id`
- retries keep the same `job_id` and increment `attempt_no`
- materially new/refined requests get a new `job_id`
- Garage language stays separate from OpenHands and Stagehand substrate language
- worker outputs stay in worker workspaces by default
- Alfred records refs/pointers instead of becoming the raw output warehouse by default

## What still remains unresolved

### Runtime model authority remains blocked

The runtime model mismatch is still open:

- OpenHands is configured for `openai/qwen3-coder-30b-a3b-instruct`
- Stagehand is configured for `qwen3-coder-30b-a3b-instruct`
- LM Studio currently exposes different model IDs in `/v1/models`

I did **not** change model settings in this pass because the winning canonical model string is still not obvious from repo authority alone.

### Runtime proof remains blocked

Fresh smoke still fails at the runtime boundary:

- sandbox starts
- conversation reaches `running`
- then flips to `error`
- no assistant reply is captured
- no tool observation is captured

So broad Garage integration is still not ready.

## ID policy coding verdict

**READY**

Isolated ID policy coding is now unblocked.

It is now safe to start implementing:

- `task_id`
- `job_id`
- `event_id`
- `checkpoint_id`
- optional `artifact_id`
- `parent_job_id`
- `attempt_no`
- retry / return / new-job rules

because those rules now have:

- a real Alfred authority document
- one primary machine-language authority
- no live contradiction between the shared policy contract and the dictionary

## Runtime verdict

**STILL BLOCKED**

The repo is not yet ready to use the browser smoke as a clean integration proof because the model authority mismatch is still unresolved.

## Exact next approved coding move

The next approved coding move is:

1. start `alfred/ids.py`

After that, if you want to keep going without reopening runtime work first:

2. start `alfred/types.py` for shell fields and ref objects

Do **not** start:

- `alfred/store.py`
- broader shared call/event persistence
- broad Garage integration wiring

until the runtime model authority mismatch is resolved and the browser proof passes.
