# OH_SHOP Current Operational Setup

Last updated: 2026-03-21 (America/Chicago)  
Workspace root: `/home/dev/OH_SHOP`

> **Current operational setup only.**
> This document describes the active baseline for this repo.
> Historical design and implementation docs remain in `docs/`, but they are not current setup instructions.
> The governing architecture contract is [authoritative_rework_contract_2026-03-21.md](/home/dev/OH_SHOP/docs/authoritative_rework_contract_2026-03-21.md).

## 1) What this stack is

OH_SHOP is currently operated as:

- `LM Studio` on the host as the local model provider
- `OpenHands` as a Docker-backed controller service
- `OpenWebUI` as a separate operator cockpit
- `SearxNG` as the search backend
- `oh-browser-mcp` as the real implemented browsing/tooling server
- OpenHands-managed per-conversation Docker sandboxes as the actual execution boundary

This means:

- the model is on the host
- the long-running application services are in Docker
- the actual agent work happens in separate Docker sandbox containers
- OpenWebUI is not the execution control plane for OpenHands tasks

## 2) Canonical active files and paths

These are the current operational sources of truth:

- authoritative contract:
  - [authoritative_rework_contract_2026-03-21.md](/home/dev/OH_SHOP/docs/authoritative_rework_contract_2026-03-21.md)
- main compose file:
  - [docker-compose.yml](/home/dev/OH_SHOP/compose/docker-compose.yml)
- orchestration helper:
  - [agent_house.py](/home/dev/OH_SHOP/scripts/agent_house.py)
- startup wrapper:
  - [up.sh](/home/dev/OH_SHOP/scripts/up.sh)
- shutdown wrapper:
  - [down.sh](/home/dev/OH_SHOP/scripts/down.sh)
- verification wrapper:
  - [verify.sh](/home/dev/OH_SHOP/scripts/verify.sh)
- saved OpenHands settings:
  - [settings.json](/home/dev/OH_SHOP/data/openhands/settings.json)
- implemented browsing path:
  - [README.md](/home/dev/OH_SHOP/repos/oh-browser-mcp/README.md)
- proof-run template:
  - [fresh_session_mcp_proof_run.md](/home/dev/OH_SHOP/docs/templates/fresh_session_mcp_proof_run.md)

These paths are not the active implementation truth:

- [openhands.compose.yml](/home/dev/OH_SHOP/compose/openhands.compose.yml)
  Deprecated subset, kept only as a historical compatibility artifact during rework.
- [README.md](/home/dev/OH_SHOP/mcp/web_tools_mcp/README.md)
  Placeholder only, not the current Phase B implementation.
- [README.md](/home/dev/OH_SHOP/bridge/openapi_server/README.md)
  Phase C placeholder only, not a current integration path.

## 3) Host vs Docker boundaries

### Host OS owns

- Docker Engine
- LM Studio
- LM Studio listener on `127.0.0.1:1234`
- LM Studio Docker reachability helper
- the OH_SHOP repo, downloads, and persistent data

### Docker owns long-running services

- `openhands-app`
- `open-webui`
- `searxng`
- `oh-browser-mcp`

### OpenHands owns execution sandboxes

OpenHands uses Docker to create per-conversation sandbox containers for actual task execution.
Those sandbox containers are the real execution boundary for tool use, commands, and workspace operations.

### OpenWebUI scope

OpenWebUI is a separate cockpit and chat interface.
It is not currently wired in as the OpenHands execution control plane.
Phase C bridge work is future work, not current runtime truth.

## 4) Canonical provider story

LM Studio is the active local provider story for this repo.

The current approved local provider posture is:

- host listener:
  - `127.0.0.1:1234`
- Docker caller base URL:
  - `http://host.docker.internal:1234/v1`
- current saved OpenHands model string:
  - `openai/all-hands_openhands-lm-32b-v0.1`
- current saved OpenHands API key value:
  - `lm-studio`

Important distinction:

- OpenHands uses provider-qualified model naming when required by LiteLLM
- other services that call LM Studio directly may use the raw LM Studio model identifier instead

If LM Studio is intentionally stopped, that is a temporary runtime condition.
It does not change the canonical provider story.

## 5) Canonical service map

Expected host ports in the active stack:

- OpenHands UI:
  - `http://127.0.0.1:3000`
- OpenWebUI:
  - `http://127.0.0.1:3001`
- SearxNG:
  - `http://127.0.0.1:3002`
- oh-browser-mcp:
  - `http://127.0.0.1:3010`
- LM Studio:
  - `http://127.0.0.1:1234/v1`

## 6) Canonical startup path

The active startup path is:

1. Start LM Studio on the host.
2. Confirm LM Studio is reachable on the host when you want live validation:

```bash
curl -sf http://127.0.0.1:1234/v1/models
```

3. Start the canonical Docker services:

```bash
cd /home/dev/OH_SHOP
./scripts/up.sh
```

What `./scripts/up.sh` does:

- calls [agent_house.py](/home/dev/OH_SHOP/scripts/agent_house.py)
- uses [docker-compose.yml](/home/dev/OH_SHOP/compose/docker-compose.yml)
- starts the canonical long-running application services

Important notes:

- the host-installed `openhands` CLI may remain installed for diagnostics or fallback use
- it is not the problem
- it is not an equal current architecture lane
- do not treat `openhands serve` as the active bring-up path for this repo

### `chat_guard` status

`chat_guard` is provisional operational tooling, not part of the canonical baseline.

In this first-pass rework baseline:

- default startup path does not define architecture around `chat_guard`
- use it only when there is a specific reason to reconcile or monitor transient chat state
- do not treat it as proof of a healthy core stack

If you intentionally need it, use one of:

```bash
cd /home/dev/OH_SHOP
python3 scripts/agent_house.py reconcile-chats
```

or:

```bash
cd /home/dev/OH_SHOP
python3 scripts/agent_house.py monitor-chats
```

## 7) Canonical shutdown path

Use:

```bash
cd /home/dev/OH_SHOP
./scripts/down.sh
```

This is the active shutdown path for the Docker-backed stack.

It now also force-removes leftover per-conversation OpenHands sandbox containers
named `oh-agent-server-*` so repeated proof runs do not leave orphaned runtimes behind.

If you ever need just the sandbox cleanup without tearing down the core stack, use:

```bash
cd /home/dev/OH_SHOP
python3 scripts/agent_house.py cleanup-sandboxes
```

## 8) Canonical verification path

Use one of:

```bash
cd /home/dev/OH_SHOP
./scripts/verify.sh
```

or:

```bash
cd /home/dev/OH_SHOP
python3 scripts/agent_house.py verify
```

What the current verifier checks:

- Layer 1:
  - Docker availability
  - canonical compose file present
  - required containers running
- Layer 2:
  - service health endpoints respond
- Layer 3:
  - LM Studio reachability on host
  - LM Studio reachability from required containers
  - SearxNG reachability from `oh-browser-mcp`
  - OpenHands route from a sandbox-bridge test container
- Layer 4:
  - `oh-browser-mcp` health payload reachable
  - `oh-browser-mcp` strict readiness endpoint reachable
  - `oh-browser-mcp` SSE endpoint reachable
- Layer 5:
  - OpenHands V1 tool-calling compatibility patch present
  - OpenHands live `/api/settings` reachable
  - OpenHands live LLM base URL matches LM Studio route
  - OpenHands live model ID exists in LM Studio `/v1/models`
  - OpenHands live MCP URL matches the sandbox-reachable path
  - persisted settings file matches live runtime settings

What the current verifier does **not** prove yet:

- that OpenHands can successfully invoke `web_research` in a fresh session
- that Phase C bridge behavior exists

So a green verify result means layers 1 through 5 are proven.
It still does not mean fresh-session browsing invocation has been proven.

## 9) OpenHands settings baseline

The saved OpenHands settings currently show:

- `llm_model = openai/all-hands_openhands-lm-32b-v0.1`
- `llm_base_url = http://host.docker.internal:1234/v1`
- `llm_api_key = lm-studio`

Those values are stored in:

- [settings.json](/home/dev/OH_SHOP/data/openhands/settings.json)

For manual configuration in the OpenHands UI, use the same values unless a later documented provider change supersedes them.

## 10) `oh-browser-mcp` registration is still required

`oh-browser-mcp` is the real implemented Phase B browsing/tooling server.
It is not automatically available to OpenHands unless it is registered in OpenHands MCP settings.

Current expected MCP registration values:

- Server Type:
  - `SSE`
- URL:
  - `http://host.docker.internal:3010/sse`

Do not use `localhost` from OpenHands for this registration.
OpenHands itself runs in Docker, so `localhost` would point at the OpenHands container, not the MCP service.

Important truth:

- `oh-browser-mcp` being built and healthy is not the same thing as OpenHands being able to use it
- even `oh-browser-mcp` reporting `ready` is still not the same thing as OpenHands already using it
- the per-conversation sandbox must also be able to reach the MCP endpoint, so use the host-bridge URL for OpenHands registration rather than the compose service name
- the current Docker baseline also applies a repo-controlled startup patch so the OpenHands V1 runtime uses non-native tool calling for `openhands-lm`
- Workstream 4 is not complete until fresh-session tool invocation is proven

### Future fresh-session proof requirement

Once manual MCP registration has been performed in OpenHands runtime settings, the proof run must capture:

- exact MCP registration values used
- exact fresh-session prompt or task used
- whether the failure mode is:
  - integration
  - provider/dependency
  - model behavior
- where the proof artifact was recorded for later review

Use the repo-tracked template:

- [fresh_session_mcp_proof_run.md](/home/dev/OH_SHOP/docs/templates/fresh_session_mcp_proof_run.md)

Optional pre-capture helper:

```bash
cd /home/dev/OH_SHOP
python3 scripts/agent_house.py capture-proof-context --output artifacts/proof_runs/<name>.md
```

That helper does not modify runtime state.
It only captures repo path, timestamp, basic host/container checks, and a one-cycle verify result for later reference.

## 11) Fresh-session proof run sequence

When you are ready to perform the real manual proof run, use this exact order:

1. Start LM Studio on the host.
2. Start the canonical stack:

```bash
cd /home/dev/OH_SHOP
./scripts/up.sh
```

3. Run repo-controlled verification:

```bash
cd /home/dev/OH_SHOP
./scripts/verify.sh
```

4. Optionally capture proof context:

```bash
cd /home/dev/OH_SHOP
python3 scripts/agent_house.py capture-proof-context --output artifacts/proof_runs/<name>.md
```

5. If the saved OpenHands MCP settings are already correct and you want a repo-driven fresh-session smoke test, run:

```bash
cd /home/dev/OH_SHOP
python3 scripts/agent_house.py smoke-test-web-research --output artifacts/proof_runs/<name>.md
```

This creates a brand-new conversation through the OpenHands API, waits for the sandbox to finish, and records whether a real `web_research` action, observation, and final assistant reply occurred.
Allow several minutes for this run. A healthy tool observation can arrive well before the final assistant reply.
The helper now prefers the app-server `v1` event feed while a conversation is active because the sandbox `events/search` and `events/count` endpoints can stall noticeably mid-run.

6. In OpenHands MCP settings, manually register:
   - Server Type: `SSE`
   - URL: `http://host.docker.internal:3010/sse`
7. Start a brand-new OpenHands session.
8. Run one proof prompt.
9. Record the outcome in:
   - [fresh_session_mcp_proof_run.md](/home/dev/OH_SHOP/docs/templates/fresh_session_mcp_proof_run.md)

Do not treat a previous session, a saved old conversation, or green infrastructure checks alone as proof that the browsing path is attached and functioning.

## 12) Workspace and repo layout

The repo layout that matters in the current baseline is:

- infra root:
  - `/home/dev/OH_SHOP`
- repos for agent work:
  - `/home/dev/OH_SHOP/repos/<repo>`
- downloads:
  - `/home/dev/OH_SHOP/downloads`
- OpenHands persistence:
  - `/home/dev/OH_SHOP/data/openhands`

The OpenHands controller is configured with:

- `/home/dev/OH_SHOP/repos` mounted as `/opt/workspace_base`

Do not rely on older docs that assume a pure `--mount-cwd` workflow or a single fixed `/workspace` path as the operational baseline.

## 13) Placeholder and historical paths

These remain in the repo, but they are not active current instructions:

- [open_hands_open_web_ui_local_agent_house_contract_v_1.md](/home/dev/OH_SHOP/docs/open_hands_open_web_ui_local_agent_house_contract_v_1.md)
  Historical mission/design doc.
- [Phase_A.md](/home/dev/OH_SHOP/docs/Phase_A.md)
  Historical implementation log.
- [phase_1_consolidated_oh_shop.md](/home/dev/OH_SHOP/docs/phase_1_consolidated_oh_shop.md)
  Historical planning doc with stale provider details.
- [phase_2_review_pack_artifacts.md](/home/dev/OH_SHOP/docs/phase_2_review_pack_artifacts.md)
  Future-work spec, not current implementation truth.
- [README.md](/home/dev/OH_SHOP/mcp/web_tools_mcp/README.md)
  Placeholder only, not the active Phase B implementation.
- [README.md](/home/dev/OH_SHOP/bridge/openapi_server/README.md)
  Placeholder only, not a current integration path.

## 14) Quick operational checklist

For a clean operator read:

1. LM Studio is the local provider story.
2. `compose/docker-compose.yml` is the only current compose file.
3. `scripts/up.sh` is the current startup path.
4. `scripts/down.sh` is the current shutdown path.
5. `scripts/verify.sh` is the current verification path.
6. OpenWebUI is separate from OpenHands execution.
7. `repos/oh-browser-mcp` is the real Phase B implementation.
8. `oh-browser-mcp` still requires MCP registration in OpenHands.

## 15) Current references

- governing contract:
  - [authoritative_rework_contract_2026-03-21.md](/home/dev/OH_SHOP/docs/authoritative_rework_contract_2026-03-21.md)
- current audit:
  - [stack_audit_2026-03-21.md](/home/dev/OH_SHOP/docs/stack_audit_2026-03-21.md)
- current cleanup plan:
  - [cleanup_plan_2026-03-21.md](/home/dev/OH_SHOP/docs/cleanup_plan_2026-03-21.md)
- independent audit:
  - [independent_audit_2026-03-21.md](/home/dev/OH_SHOP/docs/independent_audit_2026-03-21.md)
