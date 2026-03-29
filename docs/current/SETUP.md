# OH_SHOP Runtime Setup

Last updated: 2026-03-29 (America/Chicago)
Workspace root: `/home/dev/OH_SHOP`

## Status

This file describes the current runtime truth for the stabilization phase.
It also reflects the post-normalization repo restructure that separated runtime, workspace, vendor, compatibility, and archive surfaces.

For the governing contract and supporting records, use:
- `docs/runtime/runtime_stabilization_contract_v_0.md`
- `docs/runtime/stabilization/baseline_snapshot.md`
- `docs/runtime/stabilization/config_authority.md`
- `docs/runtime/stabilization/patch_ledger.md`
- `docs/runtime/stabilization/version_authority.md`
- `docs/runtime/stabilization/quarantine_list.md`

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
  - `python3 ops/garagectl.py up`
- shutdown:
  - `python3 ops/garagectl.py down`
- verify:
  - `python3 ops/garagectl.py verify`
- status:
  - `python3 ops/garagectl.py status`
- logs:
  - `python3 ops/garagectl.py logs`
- smoke proof:
  - `python3 ops/garagectl.py smoke-test-browser-tool`
- backup:
  - `python3 ops/garagectl.py backup-state`
- compose authority:
  - `compose/docker-compose.yml`
- OpenHands app override:
  - `compose/openhands_override/`
- agent-server override:
  - `compose/agent_server_override/`
- compatibility overrides:
  - `compat/openhands_sdk_overrides/`
- controller:
  - `ops/garagectl.py`
- manual host/repair tools:
  - `ops/manual/`
- browser/tool lane:
  - `vendor/stagehand_mcp/`
- workspace base:
  - `workspace/`
- runtime state:
  - `data/openhands/`
- host LM Studio launcher:
  - `/usr/bin/lm-studio`
  - `lmstudio` should resolve to the same binary through a shell-level shim or symlink

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

Current host launcher truth:
- the `.deb` install is authoritative at `/usr/bin/lm-studio`
- the active install payload lives at `/opt/LM-Studio/lm-studio`
- the stale AppImage path `/opt/lmstudio/LM-Studio-0.4.7-4-x64.AppImage` must not be the runtime authority

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
- `archive/bridge/model_router/`
- `archive/bridge/openapi_server/`
- `archive/reference/OpenHands/`

Removed non-authoritative runtime path:
- the legacy `compose/openhands.compose.yml` subset was deleted during runtime normalization

Historical docs may remain in `docs/`, but they must not outrank this file plus the runtime stabilization artifact set.
