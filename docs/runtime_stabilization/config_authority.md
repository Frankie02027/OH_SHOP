# Runtime Configuration Authority

Date context: 2026-03-27

This artifact records the runtime-critical configuration values that were observed before and after Phase 1 stabilization changes.

## Governing rule

For this phase:
- actual active code paths beat docs
- persisted live settings beat assumptions
- verifier expectations are assertions, not config authority
- health endpoints are not proof of full readiness

## Evidence commands

```bash
nl -ba compose/docker-compose.yml | sed -n '1,180p'
nl -ba scripts/agent_house.py | sed -n '20,80p'
rg -n "EXPECTED_MCP_URL|MCP endpoint reachable" scripts/agent_house.py
rg -n "1.5.0-runtime-patched|1.11.4-runtime-patched|STAGEHAND_MODEL" compose/docker-compose.yml
rg -n "llm_model|llm_base_url|host.docker.internal:3020/mcp" data/openhands/settings.json
rg -n "getStagehandModelName|browserbase_stagehand_agent|MODEL_NAME|STAGEHAND_LLM_BASE_URL" repos/stagehand(working)/packages/mcp/src/server.ts
curl -sf http://127.0.0.1:3000/api/settings | jq '{llm_model,llm_base_url,mcp_config}'
curl -sf http://127.0.0.1:1234/v1/models | jq -r '.data[].id'
```

## Current authority table

| Setting | Source | Current observed value | Does it affect runtime? | Winner in practice after stabilization | Notes |
|---|---|---|---|---|---|
| OpenHands model string | `data/openhands/settings.json` | `openai/qwen3-coder-30b-a3b-instruct` | Yes | Yes | This is the persisted runtime value loaded by OpenHands. |
| OpenHands model string | `http://127.0.0.1:3000/api/settings` | `openai/qwen3-coder-30b-a3b-instruct` | Yes | Yes | This proves the persisted value is what the live app is serving now. |
| Host LM Studio available model IDs | `http://127.0.0.1:1234/v1/models` | includes `qwen3-coder-30b-a3b-instruct` | Yes | Host provider truth | The canonical OpenHands model string now matches a live provider model family instead of the old stale `lmstudio-community/...GGUF` string. |
| OpenHands base URL | `data/openhands/settings.json` | `http://host.docker.internal:1234/v1` | Yes | Yes | Live API confirms the same value. |
| OpenHands base URL | `http://127.0.0.1:3000/api/settings` | `http://host.docker.internal:1234/v1` | Yes | Yes | No conflicting compose-level OpenHands provider env was found. |
| MCP endpoint URL | `data/openhands/settings.json` | `http://host.docker.internal:3020/mcp` | Yes | Yes | Live API confirms the same value. |
| MCP endpoint URL | `scripts/agent_house.py` | `http://host.docker.internal:3020/mcp` | Yes for verification | Yes | This was reconciled in Phase 1. |
| Stagehand model env | `compose/docker-compose.yml` | `STAGEHAND_MODEL=${STAGEHAND_MODEL:-qwen3-coder-30b-a3b-instruct}` | Yes | Yes | Compose is now explicit instead of blank-by-default. |
| Stagehand model resolution | `repos/stagehand(working)/packages/mcp/src/server.ts` | all paths use `getStagehandModelName()` | Yes | Yes | The previous split between general init and `browserbase_stagehand_agent` was removed in Phase 1. |
| Stagehand base URL | `compose/docker-compose.yml` | `http://host.docker.internal:1234/v1` | Yes | Yes | This overrides the code default `http://localhost:1235/v1`. |
| Stagehand base URL default | `repos/stagehand(working)/packages/mcp/src/server.ts` | `http://localhost:1235/v1` | Only if env missing | Loses | This remains a code fallback, not the active runtime value. |
| Stagehand local `.env.example` | `repos/stagehand(working)/packages/mcp/.env.example` | `STAGEHAND_MODEL=mistralai/devstral-small-2-2512` | No in container runtime | Loses | `Dockerfile.mcp` does not copy `.env.example`. |
| Stagehand local `.env` | `repos/stagehand(working)/packages/mcp/.env` | `STAGEHAND_MODEL=openai/all-hands_openhands-lm-32b-v0.1` | No in container runtime | Loses | `Dockerfile.mcp` does not copy `.env`; this file is local residue, not runtime authority. |

## Precedence findings

### OpenHands runtime config

Observed sources:
- `data/openhands/settings.json`
- live app API at `http://127.0.0.1:3000/api/settings`
- `scripts/agent_house.py` verifier expectations
- stale docs

Effective precedence after stabilization:
1. persisted OpenHands runtime settings under `data/openhands/settings.json`
2. live settings as served or changed through the OpenHands API
3. verifier expectations in `scripts/agent_house.py`
4. docs

Confidence:
- High for model string
- High for base URL
- High for MCP URL

Why confidence is high now:
- the stack was booted
- the live app API was queried
- the live values matched the edited persisted settings

### Stagehand runtime config

Observed sources:
- compose env in `compose/docker-compose.yml`
- code defaults in `repos/stagehand(working)/packages/mcp/src/server.ts`
- local `.env.example`
- local `.env`

Effective precedence:
1. compose env
2. code defaults inside `server.ts`
3. local `.env` and `.env.example`

Confidence:
- High

Why:
- the service is started by `compose/docker-compose.yml`
- `Dockerfile.mcp` does not copy the local `.env` files

## Pre-stabilization conflicts and what now wins

### Conflict 1: persisted OpenHands model vs live LM Studio inventory

Before Phase 1:
- `data/openhands/settings.json` held:
  - `openai/lmstudio-community/Qwen3-Coder-30B-A3B-Instruct-GGUF`
- host LM Studio exposed:
  - `qwen3-coder-30b-a3b-instruct`

After Phase 1:
- `data/openhands/settings.json` now holds:
  - `openai/qwen3-coder-30b-a3b-instruct`
- live OpenHands API serves the same value

Winner now:
- `openai/qwen3-coder-30b-a3b-instruct`

### Conflict 2: persisted MCP URL vs verifier expectation

Before Phase 1:
- persisted settings:
  - `http://host.docker.internal:3020/mcp`
- `scripts/agent_house.py` expected:
  - `http://stagehand-mcp:3020/mcp`

After Phase 1:
- both persisted settings and verifier expectation point to:
  - `http://host.docker.internal:3020/mcp`

Winner now:
- `http://host.docker.internal:3020/mcp`

### Conflict 3: Stagehand model-selection split

Before Phase 1:
- general Stagehand init auto-detected or resolved the model
- `browserbase_stagehand_agent` used raw `MODEL_NAME`

After Phase 1:
- `browserbase_stagehand_agent` also calls `getStagehandModelName()`
- compose now sets a non-blank default:
  - `qwen3-coder-30b-a3b-instruct`

Winner now:
- one Stagehand model-selection rule

## Canonical runtime values for Phase 1

- canonical OpenHands model:
  - `openai/qwen3-coder-30b-a3b-instruct`
- canonical OpenHands base URL:
  - `http://host.docker.internal:1234/v1`
- canonical browser/MCP URL:
  - `http://host.docker.internal:3020/mcp`
- canonical Stagehand model:
  - `qwen3-coder-30b-a3b-instruct`
- canonical Stagehand base URL:
  - `http://host.docker.internal:1234/v1`

## What remains unresolved

- A fresh-session proof run now reaches the `stagehand-mcp` tools successfully.
- The browser proof still does not reliably capture a final assistant reply after tool use.
- That means:
  - config truth is stabilized
  - browser-lane routing is stabilized
  - end-to-end conversational completion remains a separate remaining defect

This remaining defect is not a config-authority dispute.
It is a runtime execution or model-behavior defect to be isolated in the next pass.
