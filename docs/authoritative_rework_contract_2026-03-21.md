# OH_SHOP Authoritative Rework Contract - 2026-03-21

## Purpose

This document is the authoritative execution contract for reworking OH_SHOP from its current mixed-state condition into one coherent, supportable local stack.

It is intentionally more directive than the audits.
The audits explain what happened and what is true.
This contract defines what we will treat as true going forward, what we will change, what we will not change, and how we will decide whether the rework is complete.

This document should be read alongside, but treated as more operationally decisive than:

- `docs/stack_audit_2026-03-21.md`
- `docs/cleanup_plan_2026-03-21.md`
- `docs/independent_audit_2026-03-21.md`

If another document conflicts with this one about active architecture, active provider, active startup path, or active implementation boundaries, this document wins.

## Executive Summary

OH_SHOP is a local-first agent workstation built around:

- OpenHands as the coding agent controller
- OpenWebUI as the chat and operator cockpit
- LM Studio as the local model provider
- SearxNG as the local search backend
- `oh-browser-mcp` as the implemented browsing and research tool server
- Docker as the service and sandbox boundary

The project is not fundamentally misguided.
The architecture target is sane.
The current problem is not that the system was designed incorrectly.
The current problem is that the repo accumulated multiple partially-true stories about how it should run.

The purpose of this rework is not to redesign the mission.
The purpose is to eliminate ambiguity, retire stale setup paths, finish the missing integration work, and leave the repo with one canonical story that matches runtime reality.

## Evidence Discipline

Future architecture writing for this project must distinguish clearly between:

- repo-supported facts
- snapshot-supported facts
- live-runtime observations
- recommendations and inferences

This matters because the project now has enough moving parts that "green containers" and "healthy docs" can diverge from actual end-to-end usability.

From this point forward:

- health is not the same as readiness
- implementation on disk is not the same as integration
- snapshot evidence is not the same as live verification

## Clarifications to the Audit Record

Two points from the audit period must be interpreted correctly:

### 1. LM Studio being down during audit was an observation, not an architecture decision

LM Studio was intentionally stopped during audit review.
Therefore, any audit statement saying "LM Studio is not running" should be read as a snapshot observation of runtime state at that moment, not as proof that the architecture itself was incorrectly configured.

The architectural truth remains:

- LM Studio is the active intended local provider
- LM Studio runs on the host
- Dockerized services reach LM Studio through `host.docker.internal:1234`
- LM Studio must be treated as a required runtime prerequisite for any end-to-end validation

### 2. Zero git commits is a local workflow decision, not by itself an architecture defect

This repo currently has no commits because it is being used as a local-only working repository.
That is a valid workflow choice.

What matters operationally is not "must this be committed?"
What matters is:

- is there enough rollback protection?
- is there enough change visibility?
- is there enough clarity about what was modified?

For this project, backups are already part of that safety posture.
Git history would improve change tracking, but lack of commits is not by itself proof of broken architecture.

Therefore this contract does not require git adoption as a precondition for rework.
It treats git as optional operational improvement, not mandatory architecture.

## Rework Mission

The rework must achieve five outcomes:

1. establish one canonical active architecture
2. establish one canonical startup and verification path
3. establish one canonical provider story
4. establish one canonical Phase B browsing/tooling story
5. eliminate document and state drift that recreates old confusion

If a change does not clearly support one of those five outcomes, it should not be treated as part of the core rework.

## Authoritative Canonical Architecture

This is the one true architecture the project should now optimize for.

## Host OS responsibilities

The host OS is authoritative for:

- Docker Engine
- LM Studio application
- the current approved local provider posture: LM Studio on the host at `127.0.0.1:1234`
- LM Studio Docker DNAT helper
- the OH_SHOP source tree
- OH_SHOP persistent state under `data/`
- OH_SHOP artifacts and downloads
- host networking and firewall posture

## Docker application services

These long-running services are authoritative and should remain containerized:

- `openhands-app`
- `open-webui`
- `searxng`
- `oh-browser-mcp`

## Docker execution sandboxes

Actual OpenHands execution must continue to happen in per-conversation Docker sandbox containers managed by OpenHands.

These containers are the real execution boundary for tool use and workspace operations.

## Plain-language architecture statement

The canonical project shape is:

- model on host
- application services in Docker
- actual agent work in separate Docker sandboxes
- OpenWebUI as a separate operator cockpit, not the OpenHands execution control plane

That is the architecture this contract treats as correct.

## What This Contract Explicitly Rejects

The following are not to be treated as active current truth:

- Ollama as the current canonical provider
- a pure host-native OpenHands controller story
- `mcp/web_tools_mcp` as the active Phase B implementation
- Phase C bridge work as if it already exists
- stale setup docs as equal in authority to audited current-state docs
- old conversation state as a trustworthy validation source after architecture changes

## Authoritative Component Decisions

## Keep as active core

- `compose/docker-compose.yml`
- `scripts/agent_house.py`
- `scripts/up.sh`
- `scripts/down.sh`
- `scripts/verify.sh`
- `scripts/backup_state.sh`
- `scripts/lmstudio-docker-dnat.sh`
- `systemd/lmstudio-docker-dnat.service`
- `repos/oh-browser-mcp`
- `data/openhands`
- `data/oh_browser_mcp`

## Keep as optional or provisional operational tooling

- `scripts/chat_guard.py`

`chat_guard` may remain available as a repair or hygiene tool, but it is not part of the canonical architecture definition unless future evidence proves it is truly required as a default-on service.

During the rework itself, the default posture should be:

- off by default for canonical-baseline validation
- enabled only when there is a specific reason to reproduce, prevent, or study a concrete issue
- explicitly documented if left enabled during a validation run

## Keep as installed or historical, but not authoritative

- host `openhands` CLI
- `docs/open_hands_open_web_ui_local_agent_house_contract_v_1.md`
- `docs/Phase_A.md`
- `docs/phase_1_consolidated_oh_shop.md`
- `docs/phase_2_review_pack_artifacts.md`
- `artifacts/ollama_model_inventory_2026-03-06.txt`

These remain useful as background or history, but they must not outrank current-state documents.

## Retire or deprecate from active current truth

- `compose/openhands.compose.yml`
- Ollama-specific setup language in active docs
- `mcp/web_tools_mcp` as a live implementation path
- any wording that implies OpenHands currently runs as a separate fully host-native controller lane

## Decision Principles

Every rework decision must satisfy all of the following principles:

1. runtime truth beats historical wording
2. one active path beats multiple half-supported paths
3. implemented and wired beats implemented but invisible
4. fresh-state validation beats stale-session validation
5. operational clarity beats sentimental preservation of old setup branches
6. boring and supportable beats clever and fragile
7. default architecture should not silently absorb tactical workaround services unless they are proven necessary
8. versioned and reproducible beats floating and surprising

## Required Rework Workstreams

This rework consists of:

- seven required workstreams, numbered `0` through `6`
- one supporting sub-workstream, `4A`, which refines Workstream 4 rather than creating a separate architecture lane
- one optional future workstream, `7`

## Workstream 0 - Baseline Preconditions

### Objective

Make sure everyone understands the difference between architecture truth and temporary runtime state.

### Contract rules

- LM Studio being intentionally stopped for audit does not invalidate the canonical provider decision.
- End-to-end testing is not considered meaningful unless LM Studio is intentionally running.
- Local-only repo status is acceptable, but rollback protection must exist before destructive state changes.

### Required artifacts

- this contract
- current backup snapshot
- current audit set

### Exit criteria

- team agrees which statements are architectural truths vs temporary runtime observations

## Workstream 1 - Documentation Normalization

### Objective

Make the docs tell one operational story.

### Required changes

1. Rewrite `docs/SETUP.md` to reflect:
   - Docker-backed OpenHands controller
   - LM Studio as the current provider
   - actual host vs Docker boundaries
   - current startup path
   - current verify path
   - MCP registration requirement

2. Add clear historical banners to:
   - `docs/open_hands_open_web_ui_local_agent_house_contract_v_1.md`
   - `docs/Phase_A.md`
   - `docs/phase_1_consolidated_oh_shop.md`
   - `docs/phase_2_review_pack_artifacts.md` if needed to clarify future-only status

3. Clarify in docs that:
   - `repos/oh-browser-mcp` is the implemented Phase B path
   - `mcp/web_tools_mcp` is not the live implementation
   - Phase C remains unimplemented placeholder work
   - OpenWebUI is currently a separate operator cockpit and not the execution control plane for OpenHands tasks
   - README-only or placeholder integration paths must be labeled placeholder, not active

### Must-not-do rules

- do not preserve mutually conflicting setup instructions as if they are equal options
- do not describe Ollama as "current but optional" unless intentionally reintroduced later
- do not imply OpenHands host-native control is the active supported path on this machine

### Exit criteria

- a new reader can determine current architecture from docs alone
- a new reader cannot accidentally build the wrong stack by following the main setup doc

## Workstream 2 - Startup and Control-Path Normalization

### Objective

Make one startup path authoritative and remove ambiguity around how the stack is launched and verified.

### Required changes

1. Treat `compose/docker-compose.yml` as the sole authoritative compose definition.
2. Update wrapper scripts and docs so they all clearly point to that one compose path.
3. Deprecate and then remove `compose/openhands.compose.yml` once replacement wording is in place.
4. Ensure `scripts/verify.sh` and `scripts/agent_house.py verify` are documented as the active health-check route.
5. Decide whether `chat_guard` remains default-on or is demoted to manual/provisional use; do not leave that status ambiguous.

### Important interpretation

The host-installed `openhands` CLI may remain installed for diagnostics or fallback use.
It is not the problem.
It is also not an equal current architecture path.
The problem is allowing it to imply a second active architecture narrative.

### Exit criteria

- there is one obvious answer to "how do I bring the stack up?"
- there is one obvious answer to "what should I run to verify it?"
- there is one obvious answer to "which compose file is real?"
- there is one obvious answer to "is chat-guard part of the baseline or an optional repair tool?"

## Workstream 3 - Provider Normalization

### Objective

Make the LM Studio path explicit, consistent, and boring.

### Required truths

The provider story must be documented exactly like this:

- LM Studio is the active local provider
- LM Studio runs on the host
- the current approved local listener is `127.0.0.1:1234`
- Dockerized callers should use `http://host.docker.internal:1234/v1`
- OpenHands model naming must remain provider-qualified when required by LiteLLM

### Required changes

1. Document LM Studio startup as a prerequisite for live agent use.
2. Document the exact API route used by containers.
3. Document the current known-good OpenHands model string.
4. Audit provider naming consistency across:
   - OpenHands settings
   - `oh-browser-mcp` environment defaults
   - user-facing setup instructions

### Clarification

This workstream is not the same as "LM Studio must always be running."
It means:

- LM Studio is the authoritative provider when the stack is in operational mode
- if it is intentionally stopped, that is a temporary runtime condition
- docs must still describe it as the canonical provider path

### Exit criteria

- provider behavior is documented in one place and does not conflict with any active setup doc
- a user cannot reasonably enter a stale bare-model path in OpenHands because the docs told them to

## Workstream 4 - MCP and Browsing-Tool Normalization

### Objective

Finish the most important missing integration work: make the implemented browsing tool visible and usable from fresh OpenHands sessions.

### Current authoritative interpretation

- `oh-browser-mcp` is not a side experiment
- it is the real implemented Phase B browsing path
- it is currently installed and healthy but not fully integrated into OpenHands settings

### Required changes

1. Register `oh-browser-mcp` in OpenHands MCP settings using the correct SSE endpoint.
2. Verify that a fresh OpenHands session can see the registered MCP server.
3. Verify that a fresh OpenHands session can actually invoke the tool.
4. Save the exact MCP registration values used for the successful or failed test.
5. Record one fresh-session proof artifact showing the outcome.
6. Record whether any remaining failures are:
   - integration failures
   - model tool-calling compatibility failures
   - runtime/provider failures

### Important distinction

The rework must not conflate these two states:

- "the tool server exists"
- "the agent can actually use the tool"

Only the second state counts as successful integration.

### Minimum proof artifact contents

The fresh-session proof artifact must include at minimum:

- the MCP registration values used
- the prompt or task used for the browsing test
- the observed outcome
- the failure classification, if the run did not succeed

### Exit criteria

- `oh-browser-mcp` is visible in fresh OpenHands sessions
- at least one real browsing/research action completes end to end

## Workstream 4A - Functional Readiness and Health Semantics

### Objective

Stop equating shallow health checks with actual readiness.

### Required changes

1. Improve verification so it distinguishes:
   - service up
   - provider reachable
   - MCP server attached
   - real tool invocation succeeded
2. Improve `oh-browser-mcp` readiness expectations so they are not limited to "download directory writable."
3. Treat one real end-to-end tool call as the functional proof point for browsing readiness.

### Exit criteria

- the project no longer treats container health alone as proof that browsing capability is working

## Workstream 5 - State Hygiene and Validation Discipline

### Objective

Stop stale state from recreating old bugs or confusing new validation work.

### Required changes

1. Keep backups before destructive state changes.
2. Distinguish clearly between:
   - historical conversation data
   - current validation state
3. After major settings or architecture normalization, validate only with fresh sessions.
4. Archive or clean obviously stale state only after backup.

### Important clarification

This is not a "delete everything immediately" instruction.
It is a "stop trusting old state as if it were neutral evidence" instruction.

### Exit criteria

- major validation is performed using fresh sessions
- old session behavior is no longer used to disprove new architecture unless intentionally reproduced

## Workstream 6 - Operational Hardening and Maintenance Clarity

### Objective

Make the stack understandable and survivable, even if it remains local-only and manually operated.

### Required concerns to document or address

1. Docker socket privilege in `openhands-app`
2. agent-server port exposure behavior
3. root-owned files under `data/openhands`
4. what backups exist and when they must be taken
5. what "healthy services" does and does not guarantee
6. OpenWebUI state living in Docker volume rather than repo-tracked paths
7. LM Studio reachability depending on host-side DNAT and loopback posture
8. persistent `WEBUI_SECRET_KEY` requirements if OpenWebUI MCP or OAuth-backed integrations become active

### Clarification on git

Because this repo is intentionally local-only, this contract does not require git commits.
However, if git remains unused, then the following become more important:

- reliable backup snapshots
- clear change documentation
- deliberate destructive-change checkpoints

### Reproducibility concerns to address

This workstream must also explicitly track and reduce silent drift from:

- floating container tags such as `latest` and `main`
- direct git dependencies pinned to moving branches
- named-volume state that is not represented in repo-backed configuration
- missing persistence that should exist for predictable behavior

Examples already visible in the current repo include:

- floating image tags in compose
- `browser-use @ ...@main` in `repos/oh-browser-mcp/pyproject.toml`
- OpenWebUI state in `openwebui_data`
- SearxNG cache persistence not yet represented in the compose baseline

### Required review items under this workstream

1. If OpenWebUI is used for MCP or OAuth-backed tool integrations, `WEBUI_SECRET_KEY` must be set to a stable persistent value and treated as part of the off-repo state inventory.
2. SearxNG cache persistence must be explicitly reviewed as part of the compose baseline, not left as an implied future improvement.

### Exit criteria

- operational risks are documented honestly
- local-only workflow does not imply "no process"
- major off-repo state and major floating dependencies are explicitly accounted for in the rework plan

## Workstream 7 - Future Work After Stabilization

This workstream is not part of the core rework completion gate.

It includes:

- Phase 2 review-pack artifact work
- Phase C OpenWebUI bridge work
- deeper security hardening
- quality-of-life tooling such as Makefile or justfile
- optional git adoption if desired later

These are future improvements.
They must not be allowed to block core normalization.

## Ordered Rework Sequence

The rework must proceed in this order unless a concrete blocker forces reordering:

1. establish baseline truths and preserve backup posture
2. normalize docs
3. normalize startup and control path
4. normalize provider story
5. wire MCP browsing path
6. prove functional readiness, not just container health
7. validate using fresh sessions
8. perform only then any deeper cleanup of stale state or optional improvement work

This sequence is deliberate.
It prevents destructive cleanup or speculative redesign from happening before the active architecture is stable and documented.

## Acceptance Criteria

The rework is complete only when all of the following are true:

1. The active docs describe one architecture only.
2. `docs/SETUP.md` no longer tells users to build the wrong stack.
3. There is one authoritative compose path.
4. There is one authoritative startup path.
5. There is one authoritative verification path.
6. LM Studio is documented as the canonical provider and its container-access route is explicit.
7. OpenHands is configured with the correct current model/provider format.
8. `oh-browser-mcp` is registered in OpenHands settings.
9. A fresh OpenHands session can use the browsing tool successfully.
10. Old docs no longer masquerade as current operational truth.
11. The contract clearly states whether `chat_guard` is baseline or optional.
12. Verification distinguishes health from actual functional readiness.
13. Major floating image tags, moving git dependencies, and off-repo state are either pinned, documented, or explicitly accepted as temporary drift.
14. A recorded fresh-session proof artifact exists for at least one successful end-to-end browsing tool invocation, or a recorded failure artifact exists with the failure classified.

If any of those fourteen statements is false, the rework is not finished.

## Success Criteria by Human Experience

The rework should produce this user experience:

### For the operator

- they can tell what needs to run on the host vs in Docker
- they can start the stack without guessing which compose file is real
- they can verify the stack without tribal knowledge
- they can tell whether a failure is:
  - provider down
  - tool not wired
  - health green but dependency path incomplete
  - stale state
  - actual model behavior issue

### For a future contributor

- they cannot accidentally follow stale docs into the wrong stack
- they can identify which implementation path is current
- they can tell what is active, historical, placeholder, or future work

## Explicit Non-Goals

The rework does not require:

- replacing LM Studio
- reintroducing Ollama
- moving OpenHands out of Docker
- completing Phase C bridge work
- completing Phase 2 artifact work
- forcing git commits as a local-policy requirement
- redesigning the entire network topology just because it is not aesthetically perfect

## Risk Posture

This contract acknowledges the following ongoing realities:

- OpenHands controller has privileged Docker access by design
- local-model workflows require careful provider and networking consistency
- healthy containers do not prove tool availability
- named Docker volume state can drift outside repo review
- current runtime can still fail for model-behavior reasons even after architecture is normalized

Those are not reasons to abandon the architecture.
They are reasons to document it honestly and validate it in layers.

## Validation Rules

All meaningful validation after rework must be layered:

### Layer 1 - Service health

- containers running
- health endpoints passing
- expected ports listening

### Layer 2 - Provider reachability

- LM Studio available on host when operational testing is intended
- required containers can reach `host.docker.internal:1234`

### Layer 3 - OpenHands baseline behavior

- fresh conversation creation
- message send succeeds
- provider-qualified model usage succeeds

### Layer 4 - Tool visibility

- registered MCP server visible to fresh OpenHands session

### Layer 5 - Tool execution

- actual browsing/research task succeeds end to end

### Layer 6 - Reproducibility posture

- off-repo state inventory is current
- major floating versions are known and deliberately accepted or reduced

The stack must not be declared "done" based only on Layer 1 or Layer 2.

## Governance Rules for Future Changes

After this contract is adopted, future architecture changes must follow these rules:

1. any provider change must update setup docs immediately
2. any new active service path must be reflected in startup and verify docs immediately
3. any new implemented tool is not considered complete until attached to the runtime that is supposed to use it
4. historical docs must be labeled as historical when superseded
5. no second "temporary" startup path should be introduced without explicitly declaring whether it is canonical, fallback, or experimental
6. tactical remediation tooling should not become architectural baseline by inertia
7. healthcheck design should be honest about what it proves and what it does not prove
8. placeholder directories and README-only integration branches must be labeled placeholder, not active

## Final Contract Statement

OH_SHOP will be considered reworked and coherent only when the repo, the docs, the startup path, the provider path, and the live tool path all describe the same system.

Until then, the project should be treated as a partially normalized local agent house rather than a fully stabilized one.
