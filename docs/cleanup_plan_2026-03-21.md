# Cleanup Plan - 2026-03-21

## Purpose

This document turns the audit into an execution plan.

It is deliberately opinionated.
The point is not to preserve every historical option.
The point is to converge the project onto one sane, professional, supportable baseline.

## Executive summary

This cleanup plan is designed to do three things:

1. remove ambiguity about what the live stack actually is
2. stop users from reintroducing old assumptions through stale docs and stale state
3. make future debugging target one architecture instead of several competing ones

The plan is deliberately not trying to preserve every possible historical setup path.
That would keep the repo flexible in theory but confusing in practice.

## Authoritative target architecture

This cleanup plan assumes the project should end up with this exact shape:

## Host OS

- Docker Engine
- LM Studio application
- LM Studio API on `127.0.0.1:1234`
- LM Studio Docker DNAT helper
- OH_SHOP source tree
- OH_SHOP persistent data
- OH_SHOP downloads and artifacts

## Docker application services

- `openhands-app`
- `open-webui`
- `searxng`
- `oh-browser-mcp`
- `openhands-chat-guard`

## Docker execution layer

- spawned per-conversation `oh-agent-server-*` containers

## Plain-language summary

- the model is on the host
- the application services are in Docker
- the actual agent work is in separate Docker sandboxes

That is the stack we should optimize for.

## What this cleanup is trying to solve

The cleanup is specifically trying to eliminate these classes of confusion:

1. "Which setup path is the real one?"
2. "Which LLM provider is the current one?"
3. "Which services are installed versus actually used?"
4. "Where is code actually allowed to execute and edit?"
5. "Which docs are historical and which are operational?"

## Non-goals

This cleanup plan is not trying to:

- redesign the mission of the project
- remove Docker from the OpenHands control path
- switch away from LM Studio right now
- delete every old artifact immediately
- solve every model-quality issue before the architecture is normalized

Those may become later decisions, but they are not the cleanup objective.

## What has already been done

### Backup

A state backup has already been created at:

- `/home/dev/OH_SHOP/artifacts/backups/20260321_121448`

Included in that backup:

- `data/openhands`
- `compose/docker-compose.yml`
- `compose/openhands.compose.yml`
- LM Studio config files

This means cleanup can proceed without pretending there is no rollback path.

### Architecture confirmation

These things are already established as current reality:

- OpenHands controller is Docker-backed
- LM Studio is the active local provider
- `oh-browser-mcp` is the implemented Phase B browsing path
- OpenWebUI is containerized and not yet bridge-integrated

## Keep / Change / Retire decisions

## Keep on host

- LM Studio
- Docker daemon
- LM Studio CLI (`lms`)
- LM Studio launcher (`lmstudio`)
- OH_SHOP repo/data/download paths

## Keep in Docker

- `openhands-app`
- `open-webui`
- `searxng`
- `oh-browser-mcp`
- `openhands-chat-guard`
- spawned `oh-agent-server-*`

## Keep installed but demote in status

- host `openhands` CLI

Meaning:

- do not remove it
- do not treat it as a separate competing architecture
- document it correctly: on this machine, `openhands serve` is a Docker-backed launcher path

## Retire as authoritative truth

The following should stop being treated as active current truth:

- Ollama as the canonical current provider
- documentation that implies the active live stack is pure host-native OpenHands controller plus host-managed everything else
- placeholder Phase B language that ignores the implemented `oh-browser-mcp`

## Leave in place temporarily, then deprecate

- `compose/openhands.compose.yml`

Reason:

- do not delete it until the main compose path and scripts are rewritten and verified
- once replacement is confirmed, mark or remove it as non-authoritative

## Decision log in plain English

### Why OpenHands stays Docker-backed

Because that is the supported and already-live path on this machine.
Trying to force a new host-native controller story during cleanup would create a second migration project.

### Why LM Studio stays on host

Because the host is the natural place for the local model service and GPU ownership.
That part of the stack is already working and should be stabilized, not relocated.

### Why OpenWebUI stays in Docker

Because it is a service layer, not the execution boundary.
Keeping it containerized is simple, normal, and consistent with the rest of the service layer.

### Why `oh-browser-mcp` is treated as the real browsing path

Because it is actually implemented and healthy now.
The older placeholder Phase B paths should not outrank a live working component just because they are older in the docs.

## Cleanup workstreams

## Workstream 1 - Documentation normalization

### Objective

Make the docs tell one story only.

### Required changes

1. Rewrite `docs/SETUP.md` so it reflects:
   - Docker-backed OpenHands controller
   - LM Studio as current provider
   - actual host/container boundaries

2. Add a current-state note to `docs/open_hands_open_web_ui_local_agent_house_contract_v_1.md`:
   - original mission remains valid
   - active implementation baseline has changed

3. Update or annotate `docs/phase_1_consolidated_oh_shop.md`:
   - replace Ollama-only language with the actual current LM Studio baseline
   - keep the phase intent, not the stale provider specifics

4. Clarify that `repos/oh-browser-mcp` is the real implemented browsing path.

5. Mark `mcp/web_tools_mcp` as placeholder/obsolete unless intentionally revived later.

### Done definition

- no core setup doc should imply a different controller placement than the live stack
- no core setup doc should imply Ollama is currently canonical unless clearly labeled historical or fallback
- a new reader should be able to answer host-vs-container boundaries from docs alone

## Workstream 2 - Startup and control-path normalization

### Objective

Make one startup path authoritative.

### Required changes

1. `compose/docker-compose.yml` becomes the single authoritative compose definition.
2. `scripts/up.sh`, `scripts/down.sh`, and `scripts/verify.sh` must all clearly target that one baseline.
3. Any alternative lane must be documented as non-authoritative or deprecated.

### Important note

We should not spend cleanup effort trying to force a custom host-native OpenHands controller if the installed local CLI already treats `serve` as Docker-backed.

That would create a new unsupported lane instead of reducing drift.

### Done definition

- there is one obvious answer to "how do I start the stack?"
- there is one obvious answer to "what does verify check?"
- helper scripts no longer silently encode a different architecture than the docs describe

## Workstream 3 - Provider normalization

### Objective

Make the LM Studio lane explicit and stable.

### Required changes

1. Document LM Studio as current canonical provider.
2. Document the exact API endpoint:
   - `http://host.docker.internal:1234/v1` for container callers
3. Document the provider-qualified model naming rule for OpenHands/LiteLLM.
4. Stop leaving old docs in a state where users will reasonably enter bare model names and trigger provider resolution errors.

### Current known-good example

- `openai/all-hands_openhands-lm-32b-v0.1`

### Done definition

- fresh setup docs would lead a user to enter the correct provider-qualified model value
- provider changes can be made later, but only through explicit documented updates

## Workstream 4 - MCP/tooling normalization

### Objective

Make the implemented browsing stack actually available to the agent.

### Current problem

- `oh-browser-mcp` is healthy
- OpenHands saved `mcp_config` is empty

### Required changes

1. Register `oh-browser-mcp` in OpenHands settings.
2. Confirm a fresh conversation sees the tool.
3. Confirm a real browsing/search task uses it.
4. Record whether additional tool-calling compatibility tuning is still needed for the current LM Studio model path.

### Done definition

- `oh-browser-mcp` is not merely installed; it is visible and usable from a fresh OpenHands session
- docs include the exact MCP registration values and where they belong

## Workstream 5 - State cleanup

### Objective

Get rid of stale runtime assumptions carried in old saved state.

### Current problem

Old conversations and settings can preserve:

- old model naming
- old MCP assumptions
- old routing expectations

That creates false negatives during testing because the infrastructure can be fixed while the old session still behaves like the previous architecture.

### Required changes

After docs and startup are normalized:

1. back up state again if needed
2. stop OpenHands
3. archive old `settings.json` and conversation DB/state
4. restart from the canonical baseline
5. create only fresh conversations for verification

### Done definition

- validation uses fresh state only
- no debugging is performed against stale conversations unless intentionally reproduced

## Guardrails during execution

During cleanup, these guardrails should be treated as hard rules:

1. do not delete rollback material before the normalized path is verified
2. do not mix documentation rewrites with speculative architecture changes
3. do not judge success using old conversations that predate provider or routing fixes
4. do not mark a service "done" just because the container is healthy; verify attachment and usability
5. do not keep two equally-authoritative setup stories alive "just in case"

## Ordered execution sequence

This is the recommended order.

## Phase 1 - Freeze and document

1. keep the backup already taken
2. finalize audit and cleanup docs
3. stop creating new architectural branches

## Phase 2 - Rewrite setup truth

1. update setup docs
2. update contract/current-state notes
3. update Phase B wording around implemented browsing path

## Phase 3 - Normalize startup and verify

1. pick one compose file as canonical
2. align helper scripts with it
3. keep verify focused on the real active stack

## Phase 4 - Wire the browsing tools

1. register `oh-browser-mcp`
2. verify OpenHands can see and call it
3. document the exact MCP registration values

## Phase 5 - Reset stale OpenHands state

1. archive stale state
2. restart clean
3. test only fresh conversations

## Phase 6 - End-to-end acceptance test

A successful cleanup means all of the following pass in fresh state:

1. OpenHands loads
2. OpenWebUI loads
3. LM Studio is reachable from required containers
4. a fresh OpenHands message sends successfully
5. the configured model responds without provider-name errors
6. `oh-browser-mcp` is visible to the agent
7. a real browsing/search task works

## Suggested validation checklist after cleanup

Use this as the final comparison-ready checklist:

1. Bring up the canonical stack using the documented startup path only.
2. Verify all long-running services are healthy.
3. Verify LM Studio is reachable from the required containers.
4. Open a fresh OpenHands session and send a simple message.
5. Confirm the session no longer shows disappearing-message behavior.
6. Confirm the configured model responds without LiteLLM provider-resolution errors.
7. Confirm `oh-browser-mcp` is visible in the fresh session.
8. Run one live browsing or search task and confirm the tool is actually used.
9. Confirm docs, scripts, and runtime all still tell the same story after the test.

## Concrete acceptance criteria

The cleanup is finished when these statements are true:

1. There is one canonical startup path.
2. There is one canonical LLM provider story.
3. There is one canonical controller-placement story.
4. There is one canonical Phase B browsing/tooling story.
5. Fresh conversations no longer fail with:
   - disappearing-message behavior
   - LiteLLM provider-name errors
6. The implemented browsing MCP server is actually attached and usable.

## Risks during cleanup

## Risk 1 - treating old docs as equal truth

If cleanup keeps trying to preserve every historical path equally, the project will remain ambiguous.

Mitigation:

- explicitly mark non-authoritative paths as historical, deprecated, or fallback

## Risk 2 - resetting state too early

If state is reset before docs and startup path are normalized, the project can still recreate the same confusion after restart.

Mitigation:

- normalize docs and startup first
- reset state second

## Risk 3 - declaring the tool stack finished before wiring it

The presence of `oh-browser-mcp` on disk and in Docker is not the same as agent availability.

Mitigation:

- require visible MCP registration and successful tool use before calling Phase B runtime sane

## Rollback posture

If cleanup introduces new confusion instead of reducing it, rollback should be simple:

1. stop the affected services
2. restore the latest backup snapshot
3. re-run the canonical startup path
4. compare the restored state against the audit before attempting a second cleanup pass

The existence of `/home/dev/OH_SHOP/artifacts/backups/20260321_121448` is what makes a disciplined cleanup practical.

## Recommended operational posture after cleanup

After cleanup, the team should behave as if these rules are non-negotiable:

1. docs describe the actual live stack, not a remembered one
2. startup scripts reflect the actual live stack, not an older one
3. model-provider changes require doc updates immediately
4. implemented services are not considered "done" until they are wired into the active runtime
5. debugging uses fresh conversations whenever architecture or settings changed

## Recommended next action from here

The next actual execution chunk should be:

1. rewrite setup/contract/current-state docs to match the Docker-backed OpenHands + LM Studio baseline
2. normalize startup and verification wording around the same baseline
3. register `oh-browser-mcp` in OpenHands
4. reset stale OpenHands state after backup
5. run fresh end-to-end validation

That is the shortest path from "haunted mixed stack" to "single coherent local agent house."

## Definition of success in one sentence

The cleanup succeeds when a new technically competent person can read the docs, start the stack, open a fresh session, and observe behavior that matches the documentation without needing tribal knowledge.
