# Runtime Stabilization Summary

Date context: 2026-03-27

This summary closes Phase 1 runtime stabilization work performed under `docs/runtime_stabilization_contract_v_0.md`.

## What is now canonical

- canonical startup path:
  - `scripts/up.sh` -> `scripts/agent_house.py up` -> `compose/docker-compose.yml`
- canonical shutdown path:
  - `scripts/down.sh` -> `scripts/agent_house.py down`
- canonical verification path:
  - `scripts/verify.sh` -> `scripts/agent_house.py verify`
- canonical browser/tool lane:
  - `stagehand-mcp`
  - source rooted in `repos/stagehand(working)/packages/mcp/`
- canonical provider path:
  - host LM Studio through `http://host.docker.internal:1234/v1`
- canonical MCP URL:
  - `http://host.docker.internal:3020/mcp`
- canonical OpenHands persisted runtime config root:
  - `data/openhands/`

## What changed in Phase 1

### Runtime truth and config truth

- `scripts/agent_house.py` now expects the same MCP URL that persisted OpenHands settings actually use:
  - `http://host.docker.internal:3020/mcp`
- `data/openhands/settings.json` now uses:
  - `llm_model = openai/qwen3-coder-30b-a3b-instruct`
  - `llm_base_url = http://host.docker.internal:1234/v1`
  - `mcp_config.shttp_servers[0].url = http://host.docker.internal:3020/mcp`
- `compose/docker-compose.yml` now sets an explicit Stagehand model default:
  - `qwen3-coder-30b-a3b-instruct`
- `repos/stagehand(working)/packages/mcp/src/server.ts` now uses one model-resolution rule across both general Stagehand init and `browserbase_stagehand_agent`

### Runtime naming truth

- `compose/docker-compose.yml` now refers to:
  - `oh-shop/openhands:1.5.0-runtime-patched`
  - `AGENT_SERVER_IMAGE_TAG=1.11.4-runtime-patched`
- `scripts/agent_house.py` now builds:
  - `oh-shop/agent-server:1.11.4-runtime-patched`

This did not solve the underlying version skew, but it did stop the local tags from lying about what they contain.

### Verification truth

- `scripts/agent_house.py` no longer describes Stagehand `/healthz` reachability as if it were full readiness
- the Stagehand LM Studio route verifier no longer assumes the image contains `curl`
- `./scripts/verify.sh` now passes Layers 1 through 5 on the stabilized runtime

### Documentation truth

- `docs/SETUP.md` was rewritten to describe the actual current stack:
  - `LM Studio + OpenHands + OpenWebUI + Stagehand MCP`
- `docs/authoritative_rework_contract_2026-03-21.md` now carries a warning banner marking it historical and non-authoritative for current runtime stabilization

## What was proven live

Live runtime after Phase 1 changes:
- `openhands-app   oh-shop/openhands:1.5.0-runtime-patched`
- `open-webui      ghcr.io/open-webui/open-webui:main`
- `stagehand-mcp   oh-stagehand-mcp:latest`

Live OpenHands settings observed from `http://127.0.0.1:3000/api/settings`:
- `llm_model = openai/qwen3-coder-30b-a3b-instruct`
- `llm_base_url = http://host.docker.internal:1234/v1`
- `mcp_config.shttp_servers[0].url = http://host.docker.internal:3020/mcp`

Live proof results:
- `./scripts/verify.sh`
  - passed Layers 1 through 5
- `python3 scripts/agent_house.py smoke-test-browser-tool ...`
  - reached Stagehand browser tools successfully
  - captured browser tool observations
  - still failed to capture a final assistant reply reliably

## What remains conflicting or deferred

- OpenHands app version authority is still weak at the Dockerfile base layer because `compose/openhands_override/Dockerfile` still uses:
  - `docker.openhands.dev/openhands/openhands:latest`
- agent-server version authority is still mixed-family because `compose/agent_server_override/Dockerfile` still starts from:
  - `ghcr.io/openhands/agent-server:61470a1-python`
  - then installs `1.11.4` Python packages
- patch authority is still too fragmented:
  - duplicate vendored converter overrides remain
  - `scripts/patch_openhands_tool_call_mode.py` remains superseded but still present
- `repos/OpenHands/` remains misleading if anyone treats it as runtime authority
- `data/openhands/openhands.db` remains tracked mutable runtime state

## What was quarantined

Quarantined as non-authoritative for runtime stabilization:
- `compose/openhands.compose.yml`
- `bridge/model_router/`
- `bridge/openapi_server/`
- `compose/phase1_fixture/`
- `repos/OpenHands/`
- `compose/agent_server_override/vendor_sdk/vendor_sdk/`
- `repos/stagehand(working)/packages/mcp/src/server.ts.bak`
- `plaintext.txt`
- `repos/sieve.py`
- `repos/calculator/`
- `docs/authoritative_rework_contract_2026-03-21.md`

Resolved during this phase:
- `docs/SETUP.md` was rewritten and is no longer quarantined
- `scripts/__pycache__/agent_house.cpython-313.pyc` was removed from the worktree

## What should be removed or rewritten next

Next pass should focus on:
- pinning the OpenHands app base image instead of using `latest`
- removing agent-server base-vs-package family skew
- collapsing duplicate vendored converter overrides into one explicit maintained override path
- deleting clearly superseded duplicate trees once quarantine approval is accepted
- isolating the missing-final-reply defect after successful browser tool execution

## What should be tested next

The next focused validation target should be:
- why a fresh OpenHands browser-tool conversation can finish after tool execution without a captured final assistant reply

This next test pass should not reopen broad architecture work.
It should stay inside the stabilized runtime path and isolate:
- event/callback handling
- final reply propagation
- model behavior after tool-use completion
