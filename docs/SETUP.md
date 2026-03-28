# OH_SHOP Runtime Setup

Last updated: 2026-03-27 (America/Chicago)
Workspace root: `/home/dev/OH_SHOP`

## Status

This file describes the current runtime truth for the stabilization phase.

For the governing contract and supporting records, use:
- `docs/runtime_stabilization_contract_v_0.md`
- `docs/runtime_stabilization/baseline_snapshot.md`
- `docs/runtime_stabilization/config_authority.md`
- `docs/runtime_stabilization/patch_ledger.md`
- `docs/runtime_stabilization/version_authority.md`
- `docs/runtime_stabilization/quarantine_list.md`

This is not an AI Garage implementation document.
It does not claim Alfred, Ledger, memory, baton-pass, or Phase C bridge work as current runtime behavior.

## What the current stack actually is

The current runtime is:
- host `LM Studio` as the provider
- `OpenHands` as the controller/runtime UI
- `OpenWebUI` as a separate operator cockpit
- `stagehand-mcp` as the active browser/tool lane
- OpenHands-managed `oh-agent-server-*` sandbox containers as the execution boundary

The current runtime is not:
- `SearxNG` as an active service
- `oh-browser-mcp` as the active browser server
- a Phase C OpenWebUI -> OpenHands bridge
- AI Garage orchestration

## Canonical paths

- startup:
  - `scripts/up.sh`
  - `scripts/agent_house.py up`
- shutdown:
  - `scripts/down.sh`
  - `scripts/agent_house.py down`
- verify:
  - `scripts/verify.sh`
  - `scripts/verify.py`
  - `scripts/agent_house.py verify`
- compose authority:
  - `compose/docker-compose.yml`
- OpenHands app override:
  - `compose/openhands_override/`
- agent-server override:
  - `compose/agent_server_override/`
- browser/tool lane:
  - `repos/stagehand(working)/packages/mcp/`
- runtime state:
  - `data/openhands/`

## Service map

Long-running services in the canonical compose path:
- `openhands`
- `open-webui`
- `stagehand-mcp`

Present but not part of canonical startup:
- `chat-guard`

Expected host ports:
- OpenHands:
  - `http://127.0.0.1:3000`
- OpenWebUI:
  - `http://127.0.0.1:3001`
- Stagehand MCP:
  - `http://127.0.0.1:3020/mcp`
- LM Studio:
  - `http://127.0.0.1:1234/v1`

## Canonical config truth for this phase

- OpenHands provider/base URL:
  - `http://host.docker.internal:1234/v1`
- OpenHands persisted model:
  - `openai/qwen3-coder-30b-a3b-instruct`
- Canonical MCP URL:
  - `http://host.docker.internal:3020/mcp`
- Stagehand base URL:
  - `http://host.docker.internal:1234/v1`
- Stagehand model:
  - `qwen3-coder-30b-a3b-instruct`

Important:
- OpenHands runtime-critical values currently persist under `data/openhands/settings.json`
- Stagehand runtime-critical values currently come from `compose/docker-compose.yml`
- verifier expectations are not config authority by themselves

## Runtime state classification

Runtime-significant state currently exists under `data/openhands/`, including:
- `settings.json`
- `openhands.db`
- `.jwt_secret`
- `.keys`
- `v1_conversations/`

This directory is part of runtime behavior.
It should not be ignored when reconciling truth.

## Non-authoritative paths

The following paths are not current runtime authority:
- `compose/openhands.compose.yml`
- `bridge/model_router/`
- `bridge/openapi_server/`
- `repos/OpenHands/`

Historical docs may remain in `docs/`, but they must not outrank this file plus the runtime stabilization artifact set.
