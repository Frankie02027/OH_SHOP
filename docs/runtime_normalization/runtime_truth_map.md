# Runtime Truth Map

Date context: 2026-03-29

This artifact records the currently winning runtime path before normalization changes are applied.

## Canonical control paths that actually win today

### Startup

Current winning startup path:

```text
scripts/up.sh
  -> scripts/agent_house.py up
    -> docker build -t oh-shop/agent-server:1.11.4-runtime-patched compose/agent_server_override
    -> docker compose -f compose/docker-compose.yml up -d --build openhands open-webui stagehand-mcp
```

What starts:
- `openhands-app`
- `open-webui`
- `stagehand-mcp`

What does not start by default:
- `openhands-chat-guard`

### Shutdown

Current winning shutdown path:

```text
scripts/down.sh
  -> scripts/agent_house.py down
    -> docker compose -f compose/docker-compose.yml down
    -> docker rm -f oh-agent-server-*  (best-effort sandbox cleanup)
```

### Verification

Current winning verification path:

```text
scripts/verify.sh
  -> scripts/agent_house.py verify
```

What it proves today:
- containers are up
- HTTP endpoints respond
- host and container LM Studio routes are reachable
- `stagehand-mcp` `/healthz` is reachable
- OpenHands live settings match expected LM Studio base/model/MCP values

What it does not prove today:
- full Stagehand readiness
- final assistant reply semantics
- OpenWebUI integration behavior beyond container/process health

### Proof / smoke path

Current winning proof path:

```text
python3 scripts/agent_house.py smoke-test-browser-tool \
  --prompt "Use the Stagehand browser tools to open https://example.com and tell me the exact page title. Say explicitly that you used a browser tool." \
  --output ...
  --timeout 240
```

Current runtime path through the stack:

```text
agent_house smoke harness
  -> POST http://127.0.0.1:3000/api/v1/app-conversations
  -> OpenHands app creates app conversation + sandbox
  -> OpenHands launches sandbox from oh-shop/agent-server:1.11.4-runtime-patched
  -> sandbox uses persisted OpenHands settings from data/openhands/settings.json
  -> sandbox reaches MCP at http://host.docker.internal:3020/mcp
  -> stagehand-mcp uses host LM Studio at http://host.docker.internal:1234/v1
  -> harness fetches terminal events from sandbox first, app mirror second
```

## Service build/runtime map

| Service | Build/start authority that wins today | Runtime image/tag currently used | Runtime entrypoint/command | Notes |
|---|---|---|---|---|
| `openhands-app` | `compose/docker-compose.yml` -> `compose/openhands_override/Dockerfile` | `oh-shop/openhands:1.5.0-runtime-patched` | `uvicorn openhands.server.listen:app --host 0.0.0.0 --port 3000` | Built by compose from root context. |
| sandbox `agent-server` | `scripts/agent_house.py cmd_up()` -> `compose/agent_server_override/Dockerfile` | `oh-shop/agent-server:1.11.4-runtime-patched` | `python3 -m openhands.agent_server` | Prebuilt outside compose, then launched indirectly by OpenHands. |
| `open-webui` | `compose/docker-compose.yml` | `ghcr.io/open-webui/open-webui:main` | image default | External image, no repo-local build path. |
| `stagehand-mcp` | `compose/docker-compose.yml` -> `repos/stagehand(working)/Dockerfile.mcp` | `oh-stagehand-mcp:latest` | `node dist/server.js` | Built from local Stagehand MCP slice. |
| `openhands-chat-guard` | `compose/docker-compose.yml` only if explicitly started | `python:3.11-alpine` | shell installs `docker` at boot, then runs `scripts/chat_guard.py` | Optional janitor, not baseline runtime. |

## Runtime mutation map

### Build-time mutation

Current build-time mutation that wins:

1. `compose/openhands_override/Dockerfile`
- copies patched converter files into the OpenHands app image
- runs `scripts/patch_openhands_external_resource_routing.py`
- applies two additional inline string patches to `live_status_app_conversation_service.py`

2. `compose/agent_server_override/Dockerfile`
- installs `openhands-agent-server==1.11.4`
- installs `openhands-sdk==1.11.4`
- installs `openhands-tools==1.11.4`
- overlays patched converter files into the sandbox image

3. `repos/stagehand(working)/Dockerfile.mcp`
- installs Chromium
- installs MCP dependencies with npm
- builds `dist/server.js`

### Runtime mutation

Current runtime mutation that wins:
- OpenHands app writes mutable state under `data/openhands/`
- sandbox event webhook batches populate `data/openhands/v1_conversations/`
- smoke runs mutate `data/openhands/openhands.db`
- `chat_guard.py` can delete orphan DB rows and stale sandbox containers
- `lmstudio-docker-dnat.sh` can mutate host sysctls and iptables if the operator runs it

## Config authority that wins today

### OpenHands

Winner in practice:
- `data/openhands/settings.json`

Live runtime values currently expected:
- `llm_model = openai/qwen3-coder-30b-a3b-instruct`
- `llm_base_url = http://host.docker.internal:1234/v1`
- `mcp_config.shttp_servers[0].url = http://host.docker.internal:3020/mcp`

### Stagehand MCP

Winner in practice:
- `compose/docker-compose.yml` service env

Active expected values:
- `STAGEHAND_MODEL=qwen3-coder-30b-a3b-instruct`
- `STAGEHAND_LLM_BASE_URL=http://host.docker.internal:1234/v1`
- `STAGEHAND_LLM_API_KEY=lm-studio`

Losing sources:
- `repos/stagehand(working)/packages/mcp/.env`
- `repos/stagehand(working)/packages/mcp/.env.example`

### OpenWebUI

Winner in practice:
- `compose/docker-compose.yml` service env

Active expected values:
- `OPENAI_API_BASE_URLS=http://host.docker.internal:1234/v1`
- `OPENAI_API_KEYS=lm-studio`

## Dependency chain that wins today

```text
Host LM Studio
  <- OpenHands app reads persisted model/base config from data/openhands/settings.json
  <- stagehand-mcp uses compose-provided model/base env
  <- open-webui uses compose-provided OpenAI base URL

OpenHands app
  <- compose/docker-compose.yml
  <- Docker socket
  <- data/openhands/
  <- repos/
  -> launches oh-agent-server-* sandboxes
  -> serves app API on :3000

Sandbox agent-server
  <- prebuilt oh-shop/agent-server:1.11.4-runtime-patched
  -> reaches stagehand-mcp via host.docker.internal:3020
  -> reaches OpenHands app via host.docker.internal:3000

stagehand-mcp
  <- local build from repos/stagehand(working)/Dockerfile.mcp
  <- host LM Studio
  -> serves MCP SHTTP on :3020

open-webui
  <- host LM Studio only
```

## Current lies / drift still present before normalization

1. `compose/openhands_override/Dockerfile` still builds from floating `docker.openhands.dev/openhands/openhands:latest`.
2. `compose/docker-compose.yml` still runs floating `ghcr.io/open-webui/open-webui:main`.
3. `compose/agent_server_override/Dockerfile` still mixes a `61470a1-python` base layer with `1.11.4` Python packages.
4. Stagehand has a `package-lock.json`, but `repos/stagehand(working)/Dockerfile.mcp` still uses `npm install` instead of `npm ci`.
5. Stagehand runtime image is still tagged `oh-stagehand-mcp:latest`, which is not honest authority.
6. OpenHands app patch authority is split between:
- `scripts/patch_openhands_external_resource_routing.py`
- two inline Dockerfile mutations
- vendored converter overrides
7. Duplicate converter override trees still exist under:
- `compose/openhands_override/vendor_sdk/`
- `compose/agent_server_override/vendor_sdk/`
- `compose/agent_server_override/vendor_sdk/vendor_sdk/`
8. `scripts/patch_openhands_tool_call_mode.py` remains present even though no active build path uses it.
9. `compose/openhands.compose.yml` remains a believable but non-winning competing startup path.
10. `compose/docker-compose.yml` still hardcodes `/home/dev/OH_SHOP/...` host bind paths instead of having one repo-root authority variable.
11. Tracked mutable runtime state still lives under `data/openhands/`, including:
- `.jwt_secret`
- `.keys`
- `openhands.db`
- mirrored conversation event JSON files

## Normalization target for this pass

This pass should end with:
- one explicit pinned base image per built service
- one honest local image tag per local service
- one patch authority path per service
- one config/settings authority model
- one documented proof path
- no stale competing build/start path still masquerading as current runtime truth

## Normalization changes applied

Applied in this pass:

1. pinned OpenHands app base image by digest
2. pinned sandbox agent-server base image by digest
3. pinned OpenWebUI image by digest
4. changed Stagehand local image tag from `latest` to `0.3.0-runtime-patched`
5. collapsed OpenHands app patching into `compose/openhands_override/apply_runtime_patches.py`
6. collapsed shared converter overrides into `compose/shared_vendor_sdk/`
7. changed sandbox image build to use repo root with explicit Dockerfile path
8. introduced `OH_SHOP_ROOT` as the compose bind-mount authority for canonical control-path runs
9. removed the stale partial compose file and duplicate non-winning patch debris

## Post-normalization runtime story

Current normalized baseline story:

```text
scripts/up.sh
  -> scripts/agent_house.py up
    -> docker build -f compose/agent_server_override/Dockerfile -t oh-shop/agent-server:1.11.4-runtime-patched /home/dev/OH_SHOP
    -> docker compose -f compose/docker-compose.yml up -d --build openhands open-webui stagehand-mcp

openhands-app
  <- compose/openhands_override/Dockerfile
  <- compose/openhands_override/apply_runtime_patches.py
  <- compose/shared_vendor_sdk/*

stagehand-mcp
  <- repos/stagehand(working)/Dockerfile.mcp
  <- packages/mcp/package-lock.json

open-webui
  <- pinned external image in compose
```

## Post-normalization live status

What was proven after normalization:
- the normalized stack rebuilt successfully through the canonical startup path
- `openhands-app`, `open-webui`, and `stagehand-mcp` all came up healthy

What was blocked outside the repo:
- host LM Studio was down on `http://localhost:1234`
- provider-route checks in `./scripts/verify.sh` therefore failed
- the canonical browser smoke proof reached `READY` and sandbox creation, but the conversation ended in `error` before tool execution because the provider was unavailable
