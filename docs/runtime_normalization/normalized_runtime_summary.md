# Normalized Runtime Summary

Date context: 2026-03-29

## Canonical baseline runtime story

Canonical startup path:
- `scripts/up.sh`
- `scripts/agent_house.py up`
- `compose/docker-compose.yml`

Canonical shutdown path:
- `scripts/down.sh`

Canonical verification path:
- `scripts/verify.sh`

Canonical proof path:
- `python3 scripts/agent_house.py smoke-test-browser-tool ...`

Canonical service/build paths:
- OpenHands app:
  - `compose/openhands_override/Dockerfile`
  - `compose/openhands_override/apply_runtime_patches.py`
  - `compose/shared_vendor_sdk/*`
- sandbox agent-server:
  - `compose/agent_server_override/Dockerfile`
  - `compose/shared_vendor_sdk/*`
- Stagehand MCP:
  - `repos/stagehand(working)/Dockerfile.mcp`
  - `repos/stagehand(working)/packages/mcp/package-lock.json`
- OpenWebUI:
  - pinned external image ref in `compose/docker-compose.yml`

Canonical config/settings authority:
- repo-root bind mounts:
  - `OH_SHOP_ROOT` via `scripts/agent_house.py`
- OpenHands runtime settings:
  - `data/openhands/settings.json`
- Stagehand and OpenWebUI runtime env:
  - `compose/docker-compose.yml`

## What is materially cleaner now

1. OpenHands app no longer builds from floating `:latest`; it is pinned to the audited `1.5.0` digest.
2. OpenWebUI no longer runs from an unpinned compose reference; it is pinned to the audited digest.
3. Stagehand no longer hides behind a `latest` local tag; it now uses `oh-stagehand-mcp:0.3.0-runtime-patched`.
4. OpenHands app patch authority is no longer split between one helper and two inline Dockerfile mutations.
5. Shared converter overrides are now singular instead of duplicated across app and sandbox paths.
6. The stale partial compose file is gone.
7. The canonical control path now owns repo-root bind-mount authority through `OH_SHOP_ROOT`.

## Current live status after normalization

What succeeded:
- the normalized stack rebuilt successfully through the canonical startup path
- `openhands-app` is healthy
- `open-webui` is healthy
- `stagehand-mcp` is healthy

What is still blocked:
- host LM Studio was not running on `http://localhost:1234`
- `./scripts/verify.sh` therefore failed at provider-route checks
- the canonical browser smoke proof ended with sandbox `execution_status = error` before tool use because the provider was unavailable

## Bottom line

The repo now has one honest runtime/build story.
The remaining blocker at the end of this pass is host-provider availability, not runtime-path ambiguity inside OH_SHOP.
