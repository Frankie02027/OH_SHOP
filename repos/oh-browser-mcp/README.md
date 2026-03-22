# oh-browser-mcp

`oh-browser-mcp` is an MCP server (SSE transport) that provides one tool, `web_research`, for OpenHands.

This is the current implemented Phase B browsing/tooling path for OH_SHOP.
It is not automatically available to OpenHands until it is registered in OpenHands MCP settings.

It performs:
- SearxNG JSON search (`SEARXNG_URL`)
- Direct URL seeding when the query already includes target URLs
- Real browser navigation with Playwright (including multi-page link chasing)
- Button/expander clicks for pages that hide useful links behind "show more" style controls
- Browser-agent attempts via `browser-use` (fork: `tov-a/AI---browser-use`)
- File downloads into `DOWNLOAD_DIR` with SHA256 artifact metadata

## Environment variables

- `SEARXNG_URL` (default: `http://searxng:8080`)
- `LLM_BASE_URL` (default: `http://host.docker.internal:1234/v1`)
- `LLM_MODEL` (default: `all-hands_openhands-lm-32b-v0.1`)
- `LLM_API_KEY` (default: `lm-studio`)
- `DOWNLOAD_DIR` (default: `/data/downloads`)
- `LOG_DIR` (default: `/data/logs`)
- `MCP_PORT` (default: `3010`)

Important note on model naming:

- OpenHands currently uses a provider-qualified model string in saved settings:
  - `openai/all-hands_openhands-lm-32b-v0.1`
- `oh-browser-mcp` talks directly to LM Studio's OpenAI-compatible endpoint and therefore uses the direct LM Studio model identifier in its own environment defaults.

Do not assume those two strings must be identical in form just because they target the same local model backend.

## Run with docker compose

From `/home/dev/OH_SHOP/compose`:

```bash
docker compose up -d --build oh-browser-mcp
```

Quick checks from host:

```bash
curl -fsS http://127.0.0.1:3010/health
curl -fsS http://127.0.0.1:3010/ready
curl -s -o /dev/null -D - http://127.0.0.1:3010/sse --max-time 2
```

Interpretation:

- `/health` proves the service is up and reports detailed readiness state.
- `/ready` is stricter: it returns success only when the service can see its required runtime dependencies.
- Neither endpoint proves that OpenHands is already using this MCP server.

## OpenHands MCP configuration

In OpenHands MCP settings:
- Server Type: `SSE`
- URL: `http://host.docker.internal:3010/sse`

Do not use `localhost` from OpenHands, because OpenHands itself runs in Docker and `localhost` points to the OpenHands container, not this MCP service.
Do not use the compose service name here either. The per-conversation sandbox must be able to reach the MCP endpoint too, so the host-bridge URL is the correct registration path.

If OpenHands settings still show empty external `mcp_config`, this tool is not yet attached even if the container is healthy.

Repo boundary for this rework:

- this repo can run and verify `oh-browser-mcp`
- this repo does not automatically edit saved OpenHands MCP registration state under `data/openhands`
- external MCP registration is still a manual/runtime step until a later controlled change explicitly handles it

## Tool exposed

`web_research` input:
- `query` (required string)
- `max_results` (default `5`)
- `max_pages` (default `8`)
- `max_steps` (default `40`)
- `download` (default `true`)
- `allowed_domains` (optional list of domains)
- `seed_urls` (optional list of explicit starting URLs)

Behavior note:

- if the query already contains one or more URLs, `web_research` now uses those as starting points instead of forcing a SearxNG search first
- direct artifact URLs are fetched directly when possible, instead of making Playwright pretend they are normal pages

`web_research` output:
- `answer: str`
- `sources: list[str]`
- `quotes: list[str]`
- `artifacts: list[{path, sha256, bytes}]`
- `trace: {searched, seeded, visited, downloads}`

## Fresh-session proof checklist

Once MCP registration is performed in OpenHands runtime settings, a real proof run should capture:

- the exact MCP registration values used
- the exact fresh-session prompt or task used
- whether the outcome was:
  - successful tool invocation
  - integration failure
  - provider/dependency failure
  - model-behavior failure
- where the proof artifact was recorded for later review

Recommended repo-tracked proof artifact:

- [fresh_session_mcp_proof_run.md](/home/dev/OH_SHOP/docs/templates/fresh_session_mcp_proof_run.md)

Optional context-capture helper before the manual session:

```bash
cd /home/dev/OH_SHOP
python3 scripts/agent_house.py capture-proof-context --output artifacts/proof_runs/<name>.md
```

Do not treat `/health`, `/ready`, or `/sse` alone as proof of end-to-end OpenHands tool use.
