# OpenHands + OpenWebUI Local Agent House — Contract v1

> **Historical / non-authoritative document.**
> This is the original March 2026 mission/design contract.
> It still captures useful intent, but its provider and setup details are no longer the current operational truth.
> For the active baseline, use [SETUP.md](/home/dev/OH_SHOP/docs/SETUP.md) and [authoritative_rework_contract_2026-03-21.md](/home/dev/OH_SHOP/docs/authoritative_rework_contract_2026-03-21.md).

Last updated: 2026-03-05 (America/Chicago)
Owner: FDS (project driver)
Executor: VS Code + Copilot (does setup + coding)

---

## 1) What we’re building (mission)

Build a **local-first, internet-capable software agent “house”** where:

- **OpenHands** is the *executor* (agent loop + workspace + file edits + terminal + diffs) running in an **isolated Docker sandbox**.
- **OpenWebUI** is the *cockpit* (ChatGPT-style chat UX, model routing, sessions, convenience).
- **Ollama** is the initial local LLM provider (local weights on this PC).

We start simple (manual handoff between UIs), then integrate:

- Phase A: OpenHands GUI works + sandboxed repo + local Ollama works.
- Phase B: add web search + “full internet” behavior.
- Phase C: OpenWebUI triggers OpenHands via API (OpenAPI/MCP bridge).

Guiding principle: **least bullshit**.
- One workspace mount.
- One canonical internal path (`/workspace`).
- Deterministic verification steps for every change.

---

## 2) High-level architecture (what each component owns)

### 2.1 OpenHands (the house)
OpenHands Local GUI provides:
- Web UI (browser at `http://localhost:3000`)
- Embedded coding workflow (editor/terminal/changes)
- Agent execution inside a **Docker sandbox**
- A **REST API** and **WebSocket (Socket.IO) event stream** via the Agent Server.

OpenHands Agent Server architecture highlights:
- FastAPI server with REST endpoints + WebSocket streaming
- Workspace manager creates/manages per-session Docker workspaces

OpenHands “search” capability (important constraint):
- **By default**, OpenHands’ built-in “web search” feature is wired specifically to **Tavily** (via Tavily’s MCP server).
- We are **not using Tavily** (no paid key).
- Therefore, “web search” will be implemented as **our own tools**, exposed to the agent via **MCP** (preferred) and/or an OpenWebUI OpenAPI tool server.
- Implementation direction (Phase B): self-host **SearxNG** for metasearch + add a **fetch/extract** tool (HTML→clean text) + optional **Playwright** fetch for JS-heavy sites.
- Until Phase B is complete, the agent can still browse known URLs via terminal (curl/wget) but does not have an automatic search engine.

### 2.2 Ollama (the initial brain)
Ollama provides an **OpenAI-compatible endpoint**.
Critical requirement:
- Increase context length dramatically (OpenHands requires large context; default 4096 is too small).

### 2.3 OpenWebUI (the cockpit)
OpenWebUI provides:
- Chat UX + session management
- Extensibility:
  - OpenAPI tool servers
  - MCP server support (native HTTP/SSE; stdio servers via mcpo proxy)

### 2.4 Integration lane (OpenWebUI → OpenHands)
We will integrate via one of these lanes (in order):

Lane 0 (Phase A): Manual handoff
- Use OpenWebUI for chat/planning, paste the final task into OpenHands for execution.

Lane 1 (Phase C): OpenAPI tool in OpenWebUI calling OpenHands Agent Server REST/WebSocket
- Build a small OpenAPI tool server that:
  - creates/continues a conversation in OpenHands
  - streams events / returns logs
  - pulls diffs/changed files

Lane 2 (optional): MCP bus
- Publish tools as MCP servers; both OpenHands and OpenWebUI can call them.

---

## 3) Non-negotiable safety + isolation rules

### 3.1 Container isolation
- OpenHands must execute inside Docker sandbox.
- Only mount the target repo directory into the sandbox.
- No mounting of `/home/dev` or broad host roots.

### 3.2 “Full internet access” policy (controlled)
We want internet access, but not reckless:
- Docker network stays enabled.
- Enable search in OpenHands via Tavily (Phase B) OR provide alternative search tool later.
- Any downloads must be saved under `/workspace/_downloads/`.
- Never store secrets in repo; use env vars.

### 3.3 Confirmation / approvals
Default:
- OpenHands confirmation mode should not be “always approve” during bring-up.
- Risky operations must require explicit approval:
  - deleting directories
  - installing system packages
  - writing outside `/workspace`
  - touching dotfiles outside mounted repo

---

## 4) Canonical workspace + paths (anti-bullshit rules)

- Host workspace root: `/home/dev/oh-work/`
- Each repo is mounted into sandbox as:
  - Container path: `/workspace`

Inside the sandbox:
- ALL tooling uses `/workspace` paths.
- Logs/artifacts go to `/workspace/.openhands/` (repo-local) or `/workspace/artifacts/openhands/`.

---

## 5) Phase plan (deliverables + acceptance tests)

### Phase A — Bring-up (OpenHands + Docker + Ollama)

Deliverables:
1) A reproducible local setup procedure (README + commands).
2) A Docker Compose stack OR shell scripts that:
   - starts Ollama
   - starts OpenWebUI
   - starts OpenHands Local GUI (or provides launch instructions)
3) A “sanity task” that proves:
   - file edit
   - command execution
   - diff capture

Acceptance tests (must pass):
A1) OpenHands reachable at `http://localhost:3000`.
A2) OpenHands sandbox can see repo under `/workspace`.
A3) OpenHands can create a file `SANITY.md` in `/workspace`.
A4) OpenHands can run a command in terminal (e.g., `ls -la`, `python -V`, `pytest --version`, etc.).
A5) OpenHands can show the diff/changes for `SANITY.md`.
A6) OpenHands can talk to Ollama model (no “connection refused”).

Critical Ollama requirement:
- Set `OLLAMA_CONTEXT_LENGTH >= 22000` (recommended 32768 or higher if model supports).

Verification commands (run on host):
- `docker version`
- `docker ps`
- `curl -s http://localhost:11434/api/tags | head`
- OpenHands UI loads at `http://localhost:3000`


### Phase B — Internet + DIY web search + ingestion (NO paid APIs)

Deliverables:
1) Add **self-hosted web search** via SearxNG (Docker) with JSON output enabled.
2) Implement a **local “WebTools” MCP server** that provides at minimum:
   - `web_search(query, …) -> results[]` (calls SearxNG JSON API)
   - `web_fetch(url) -> {title, cleaned_text, links, metadata}` (HTML fetch + readability-style extraction)
   - `web_download(url, dest) -> {path, sha256, size}` (downloads into `/workspace/_downloads/`)
3) Document and enforce the “internet behavior” rules:
   - all downloaded artifacts stored under `/workspace/_downloads/`
   - no writing outside `/workspace`
   - no secrets stored in repo; env vars only

Acceptance tests:
B1) Given: “Search the web for X and cite sources,” agent uses `web_search` and returns actual URLs + summaries (not guesses).
B2) Given: “Download Y,” agent uses `web_download` and saves it under `/workspace/_downloads/...` and reports sha256.
B3) Given local files in the mounted workspace, agent can ingest/summarize them (no OCR unless needed).
B4) For a JS-heavy page, agent can fall back to `web_fetch_js(url)` (optional Playwright) OR explain the limitation and provide alternate sources.

Verification:
- SearxNG container reachable from the sandbox network.
- `curl 'http://<searxng>/search?q=test&format=json' | head` returns JSON.
- MCP server is visible/configured and tool calls succeed.


### Phase C — OpenWebUI → OpenHands control bridge

Deliverables:
1) A minimal OpenAPI tool server (or MCP tool server) that OpenWebUI can call.
2) A documented workflow:
   - OpenWebUI prompt triggers OpenHands job
   - returns status + final diff link/text

Acceptance tests:
C1) From OpenWebUI, trigger OpenHands to create `BRIDGE_SANITY.md` in repo.
C2) From OpenWebUI, trigger OpenHands to run tests and return summarized failures.
C3) From OpenWebUI, pull a unified diff of changes from OpenHands.

Verification:
- OpenWebUI can call the tool server.
- OpenHands Agent Server responds to REST and/or streams events over WebSocket.

---

## 6) Implementation work items (Copilot task list)

### 6.1 Repo layout (create a dedicated “infra” repo)
Create a repo (or folder) to hold local agent infra:
- repo root
  - `compose/`
    - `docker-compose.yml`
  - `scripts/`
    - `agent_house.py`  (Python orchestrator: up/down/logs/verify)
    - `verify.py`       (optional: split out verify logic)
    - `utils.py`        (shared helpers)
    - `up.sh`           (optional thin wrapper calling python)
    - `down.sh`         (optional thin wrapper calling python)
  - `docs/`
    - `SETUP.md`
    - `TROUBLESHOOTING.md`
    - `SECURITY.md`
  - `bridge/` (Phase C)
    - `openapi_server/` (FastAPI tool server)
  - `mcp/` (Phase B)
    - `web_tools_mcp/` (SearxNG + fetch/extract MCP server)

Why Python over bash:
- Better structured config, error handling, JSON logs, portability, and testability.
- Bash wrappers may exist but must stay thin.


### 6.2 Docker Compose (Phase A)
Compose must define at minimum:
- `ollama` service
- `openwebui` service

OpenHands Local GUI launch strategy:
Option 1 (preferred if supported cleanly): run OpenHands as a service.
Option 2 (acceptable): install OpenHands CLI locally and run `openhands serve` on host; Docker is still used for sandboxes.

Hard requirements:
- OpenWebUI UI accessible (default typically `http://localhost:3000` or `http://localhost:8080` depending on container; document actual).
- Ollama accessible at `http://localhost:11434`.
- Ollama context length configured high.

Networking requirement:
- The OpenHands sandbox containers must be able to reach Ollama.
  - Prefer: run Ollama as a container on a shared Docker network and use DNS name `ollama:11434`.
  - Fallback: reach host Ollama via Docker gateway IP.


### 6.3 OpenHands configuration (Phase A)
Document exact UI settings to set in OpenHands:
- LLM Provider
- Model name
- Base URL (OpenAI-compatible) pointing at Ollama endpoint
- Search API key (Phase B)

Notes:
- OpenHands UI supports advanced options including custom model and base URL.


### 6.4 Web search enablement (Phase B) — DIY only
We will NOT use Tavily or any paid search API.

Plan:
- Run **SearxNG** in Docker (same network as OpenHands sandbox).
- Enable JSON output in SearxNG (`search.formats: [html, json]`).
- Implement a local MCP server (`web_tools_mcp`) that wraps:
  - search via SearxNG JSON API
  - fetch + extraction (HTML→clean text)
  - download with hashing
  - optional JS rendering fetch via Playwright

OpenHands integration strategy:
- Use OpenHands’ general MCP support to expose these tools to the agent.
- Because OpenHands’ built-in “Search API Key (Tavily)” feature is Tavily-specific, we will **not rely on the built-in search toggle**. Instead we will teach the agent (via repo customization / system prompt) to use our MCP tools for research.

Later option (explicitly optional): patch OpenHands to support configurable search providers.


### 6.5 Bridge tool server (Phase C)
Build a minimal FastAPI server that exposes OpenAPI endpoints for OpenWebUI.

Endpoints (minimum viable):
- `POST /tasks` : create a new OpenHands conversation/task with prompt + repo selector
- `GET /tasks/{id}` : get status
- `GET /tasks/{id}/diff` : get diff
- `GET /tasks/{id}/logs` : get logs summary

Implementation approach:
- Use OpenHands Agent Server REST/WebSocket APIs.
- Use WebSocket (Socket.IO) to stream events; persist them per task id.

Observability:
- Save raw responses to `bridge/_runs/<timestamp>/...`


---

## 7) Verification discipline (mandatory)

Every Copilot change must end with:
1) One “verify” command to run.
2) Expected output or pass/fail condition.

Example pattern:
- Change: add OLLAMA_CONTEXT_LENGTH
- Verify: `curl -s http://localhost:11434/api/tags | head` AND confirm OpenHands can complete a trivial chat.

---

## 8) Known constraints + gotchas (plan for them)

### 8.1 Ollama context length
- Default context may be too small for agent workflows.
- Must explicitly configure higher context.

### 8.2 Networking between OpenHands sandbox and Ollama
- If OpenHands sandboxes run in Docker, they may not reach `localhost:11434` unless routing is correct.
- Preferred: Ollama in Docker network; otherwise use gateway IP.

### 8.3 Docker socket risk
- Some OpenHands setups mount docker socket to manage sandboxes.
- Treat this as “root-equivalent”; mitigate by:
  - keeping OpenHands instance local-only
  - not mounting broad host dirs

---

## 9) Deliverable outputs (what Copilot must produce)

### Files to create
- `docs/SETUP.md` (step-by-step)
- `docs/TROUBLESHOOTING.md` (common failure modes)
- `docs/SECURITY.md` (socket risk + mount rules + approval policy)
- `compose/docker-compose.yml`
- `scripts/agent_house.py` (single entrypoint: `up`, `down`, `logs`, `verify`)
- `scripts/verify.py` (optional)
- Optional thin wrappers: `scripts/up.sh`, `scripts/down.sh`

### Setup doc must include
- How to start all services
- Where to open UIs
- How to set OpenHands LLM to local Ollama (base URL + model)
- How to mount a repo to `/workspace`
- How to enable search

---

## 10) References (source-of-truth docs)

OpenHands
- Docker sandbox: https://docs.openhands.dev/openhands/usage/sandboxes/docker
- Local setup / GUI mode: https://docs.openhands.dev/openhands/usage/run-openhands/local-setup
- Local LLMs (Ollama OpenAI-compatible + context length warning): https://docs.openhands.dev/openhands/usage/llms/local-llms
- Search engine setup (NOTE: Tavily-default behavior; we are replacing via MCP tools): https://docs.openhands.dev/openhands/usage/advanced/search-engine-setup
- Agent server architecture overview (REST + WebSocket): https://docs.openhands.dev/sdk/arch/overview
- WebSocket connection guide (Socket.IO): https://docs.openhands.dev/openhands/usage/developers/websocket-connection

DIY Web Search
- SearxNG Search API (JSON format): https://docs.searxng.org/dev/search_api.html

OpenWebUI
- Tools / MCP / OpenAPI tool servers: https://docs.openwebui.com/features/extensibility/plugin/tools/
- OpenAPI server integration guide: https://docs.openwebui.com/features/extensibility/plugin/tools/openapi-servers/open-webui

Ollama
- OpenAI compatibility: https://docs.ollama.com/api/openai-compatibility
- Context length defaults + guidance: https://docs.ollama.com/context-length

---

## 11) “Definition of done” for Contract v1

Contract v1 is done when:
- Phase A acceptance tests pass on this machine.
- A clean repo structure exists for infra.
- Setup is reproducible from scratch using `scripts/up.sh` + `scripts/verify.sh`.
- We can create/edit files and run a command in OpenHands sandbox using a local Ollama model.

