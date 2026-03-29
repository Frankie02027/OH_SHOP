# Config Authority Audit

Date context: 2026-03-29

This audit records the runtime-significant config sources that win before normalization changes are applied.

## Authority rules observed in practice

1. Active control code beats historical docs.
2. Persisted OpenHands settings beat assumptions.
3. Compose service env beats Stagehand local `.env` files.
4. Verifier expectations are assertions, not runtime authority.

## OpenHands config authority

| Source | Values it sets | Does it win? | Notes |
|---|---|---|---|
| `data/openhands/settings.json` | `llm_model`, `llm_base_url`, `mcp_config`, OpenHands flags | Yes | This is the live persisted runtime authority for OpenHands. |
| `http://127.0.0.1:3000/api/settings` | same values as live app sees them | Reflects winner | Useful as live proof, not a separate authority. |
| `scripts/agent_house.py` | `EXPECTED_MCP_URL`, proof/verify expectations | No | Assertion layer only. |
| docs | historical descriptions | No | Frequently stale. |

Current winning OpenHands values:
- `llm_model = openai/qwen3-coder-30b-a3b-instruct`
- `llm_base_url = http://host.docker.internal:1234/v1`
- `mcp_config.shttp_servers[0].url = http://host.docker.internal:3020/mcp`

## Stagehand config authority

| Source | Values it sets | Does it win? | Notes |
|---|---|---|---|
| `compose/docker-compose.yml` | `STAGEHAND_MODEL`, `STAGEHAND_LLM_BASE_URL`, `STAGEHAND_LLM_API_KEY`, browser flags, MCP bind settings | Yes | Active container runtime authority. |
| `repos/stagehand(working)/packages/mcp/src/server.ts` | code defaults like `http://localhost:1235/v1` | Only if env missing | Loses in the current compose path. |
| `repos/stagehand(working)/packages/mcp/.env` | stale local dev defaults | No | Dockerfile does not copy it. |
| `repos/stagehand(working)/packages/mcp/.env.example` | sample local dev defaults | No | Dockerfile does not copy it. |

Current winning Stagehand values:
- `STAGEHAND_MODEL=qwen3-coder-30b-a3b-instruct`
- `STAGEHAND_LLM_BASE_URL=http://host.docker.internal:1234/v1`
- `STAGEHAND_LLM_API_KEY=lm-studio`

Current losing Stagehand local values:
- `.env.example` still says `mistralai/devstral-small-2-2512`
- `.env` still says `openai/all-hands_openhands-lm-32b-v0.1`

Those files are local residue, not container authority.

## OpenWebUI config authority

Winner:
- `compose/docker-compose.yml`

Current winning values:
- `OPENAI_API_BASE_URLS=http://host.docker.internal:1234/v1`
- `OPENAI_API_KEYS=lm-studio`
- `ENABLE_OPENAI_API=true`

## Host-path authority problem

Current compose file hardcodes:
- `/home/dev/OH_SHOP/data/openhands`
- `/home/dev/OH_SHOP/repos`
- `/home/dev/OH_SHOP/scripts`
- `/home/dev/OH_SHOP/downloads`

Problem:
- the active baseline only works cleanly from one hardcoded checkout path unless the operator edits compose manually

Normalization target:
- one repo-root environment authority for host bind paths

## Current contradictions before normalization

1. OpenHands values are reasonably clean now, but path authority is still hardcoded in compose.
2. Stagehand local `.env` files disagree with compose and create false config stories.
3. OpenWebUI still points to a floating image even though its runtime env is otherwise simple.
4. `scripts/agent_house.py` still hardcodes local image tags rather than deriving from one explicit normalization source.

## Config-authority target for this pass

This pass should leave:

- one persisted OpenHands settings authority for OpenHands runtime behavior
- one compose env authority for Stagehand and OpenWebUI
- one repo-root host-path authority variable for compose bind mounts
- no believable losing local `.env` or stale path assumptions masquerading as active container config

## Normalization actions applied

Applied in this pass:

1. `compose/docker-compose.yml`
- now uses `${OH_SHOP_ROOT:-/home/dev/OH_SHOP}` for repo-owned bind mounts

2. `scripts/agent_house.py`
- now exports `OH_SHOP_ROOT=/home/dev/OH_SHOP` through the canonical control path

3. OpenHands, Stagehand, and OpenWebUI runtime values were left unchanged where they were already canonical:
- OpenHands persisted settings remain the runtime authority
- Stagehand compose env remains the runtime authority
- OpenWebUI compose env remains the runtime authority

## Post-normalization authority result

Current effective model:

1. repo-root host path authority:
- `OH_SHOP_ROOT` via `scripts/agent_house.py`

2. OpenHands runtime behavior:
- `data/openhands/settings.json`

3. Stagehand runtime behavior:
- `compose/docker-compose.yml` service env

4. OpenWebUI runtime behavior:
- `compose/docker-compose.yml` service env

## Remaining deferred config issue

`repos/stagehand(working)/packages/mcp/.env` and `.env.example` still exist as local residue.
They do not win in the container runtime, but they are still misleading local config artifacts.
