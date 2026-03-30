# OH_SHOP — Phase 1 Contract (Copilot)

> **Historical / non-authoritative document.**
> This is an earlier Phase 1 planning note from the Ollama-era implementation path.
> It is retained for history only and must not be treated as the current startup or provider guide.
> Current operational truth lives in [SETUP.md](/home/dev/OH_SHOP/docs/SETUP.md) and [authoritative_rework_contract_2026-03-21.md](/home/dev/OH_SHOP/docs/authoritative_rework_contract_2026-03-21.md).

Date: 2026-03-05 (America/Chicago)
Workspace root: `/home/dev/OH_SHOP`

## 0) Goal
Phase 1 wires **real agent-style web browsing** into our OpenHands “house”, without paid APIs.

At the end of Phase 1, OpenHands can call ONE tool:
- `web_research(query, ...)` → the tool can **search**, **open pages**, **click links**, **navigate across multiple pages**, and **download files** into OH_SHOP.

We will base browser automation on this repo (your chosen baseline):
- https://github.com/tov-a/AI---browser-use

This repo is a fork of `browser-use` and is Playwright-based.

---

## 1) Hard constraints
- Do NOT restructure `/home/dev/OH_SHOP` (folders already exist).
- Fixed ports:
  - OpenHands `:3000`
  - OpenWebUI `:3001`
  - SearxNG `:3002`
  - Ollama `:11434`
- NO paid web search (NO Tavily, NO Brave API, etc.).
- Workspace mounts must stay narrow:
  - only `/home/dev/OH_SHOP/repos` is the allowed workspace base
- All downloads go to:
  - `/home/dev/OH_SHOP/downloads/`

---

## 2) What “full browsing” means (explicit)
The tool MUST be able to:
- open a URL
- find and click links/buttons
- fill inputs
- follow link chains across multiple pages (GitHub → Releases → Asset download; forums → thread → attachment; etc.)
- handle JS-heavy sites (Playwright-driven)
- download a file and report the final saved path + sha256

If a site blocks automation (CAPTCHA/Cloudflare), the tool must return:
- a clean failure reason
- what it tried
- the last URL reached

---

## 3) Architecture (what runs where)
### 3.1 Already running
- OpenHands UI/server: `http://localhost:3000`
- OpenWebUI: `http://localhost:3001`
- SearxNG: `http://localhost:3002`
- Ollama: `http://localhost:11434` (already reachable from containers via `host.docker.internal`)

### 3.2 New component (Phase 1)
Add one containerized service:
- **Service name:** `oh-browser-mcp`
- **Purpose:** an MCP server exposing the `web_research` tool
- **Browser engine:** Playwright (Chromium)
- **Agent layer:** `AI---browser-use` (browser-use fork)
- **Search source:** SearxNG JSON
- **Download directory (bind mount):**
  - host: `/home/dev/OH_SHOP/downloads`
  - container: `/data/downloads`

Why MCP:
- OpenHands can connect to tool servers cleanly.

---

## 4) Implementation tasks (Copilot)

### 4.1 Create the helper project
Create:
- `/home/dev/OH_SHOP/repos/oh-browser-mcp/`
  - `pyproject.toml`
  - `src/oh_browser_mcp/server.py` (MCP server entrypoint)
  - `src/oh_browser_mcp/searx.py` (SearxNG client)
  - `src/oh_browser_mcp/browse.py` (browser-use wrapper)
  - `src/oh_browser_mcp/downloads.py` (download capture + hashing)
  - `src/oh_browser_mcp/research.py` (search → browse → synthesize)
  - `Dockerfile`
  - `README.md`

### 4.2 Dependencies (minimum viable)
In `pyproject.toml`:
- `httpx`
- `pydantic`
- `playwright`
- install the browser agent layer from your repo choice:
  - `AI---browser-use` (either `pip install git+https://github.com/tov-a/AI---browser-use` or vendored as a git submodule)

Do NOT pull in huge frameworks unless required.

### 4.3 Install Playwright browser at image build
Dockerfile must run:
- `playwright install chromium`

### 4.4 Implement the MCP tool
Expose ONE tool: `web_research`

**Input:**
- `query: str`
- `max_results: int = 5`
- `max_pages: int = 8` (cap on pages visited)
- `max_steps: int = 40` (cap on actions)
- `download: bool = true`
- `allowed_domains: list[str] | null` (optional fence)

**Output:**
- `answer: str`
- `sources: list[str]` (URLs actually visited)
- `quotes: list[str]` (short direct snippets)
- `artifacts: list[ {path:str, sha256:str, bytes:int} ]`
- `trace: {searched:[...], visited:[...], downloads:[...]}`

### 4.5 Search implementation (SearxNG JSON)
Call inside docker network:
- `http://searxng:8080/search?q=<query>&format=json`
Normalize results to:
- `[{title, url, snippet}]`

### 4.6 Browsing implementation (multi-page navigation)
Use Playwright + the chosen browser agent layer to:
- open each candidate URL
- click through as needed to reach the real target
- follow link chains across pages (required)
- capture:
  - final canonical URL
  - key extracted text + quotes

Hard cap to prevent thrash:
- stop after `max_pages` visited or `max_steps` actions

### 4.7 Download handling (required)
Downloads must be real browser downloads (not `curl`).
Implementation must:
- set Playwright download behavior to save into `/data/downloads`
- capture download events
- compute sha256
- return artifact records

### 4.8 Containerize the MCP service
Create `Dockerfile` + add Compose service:

In `/home/dev/OH_SHOP/compose/docker-compose.yml` add:
- `oh-browser-mcp` service
- `depends_on: [searxng]`
- `extra_hosts: ["host.docker.internal:host-gateway"]`
- bind mounts:
  - `/home/dev/OH_SHOP/downloads:/data/downloads`
  - `/home/dev/OH_SHOP/data/oh_browser_mcp:/data`

### 4.9 Register MCP in OpenHands
Configure OpenHands MCP settings to point to `oh-browser-mcp`.
Pass condition:
- OpenHands can call `web_research`.

---

## 5) Verification (must be scripted)
Create a real scripted verifier.

It must:
1) `curl` OpenHands/OpenWebUI/SearxNG/Ollama endpoints
2) verify SearxNG JSON search returns results
3) verify `oh-browser-mcp` container is running
4) run one `web_research` request (transport-specific) and assert:
   - `answer` non-empty
   - `sources >= 2`
   - `visited pages >= 2` (proves multi-page navigation)

Also:
- print any downloaded files in `/home/dev/OH_SHOP/downloads`

Note:
- the earlier deterministic `phase1-fixture` / `verify_phase1.sh` scaffolding was removed
- verification must be based on real OpenHands + real internet behavior, not a fake local site

---

## 6) Acceptance criteria (Phase 1 DONE)
- OpenHands can call `web_research`.
- It performs a multi-page browse chain (at least 2 pages visited) to answer.
- It can download at least one file via browser download events and save under `/home/dev/OH_SHOP/downloads`.
- the real scripted verifier passes.

---

## 7) Out of scope
- No OpenWebUI→OpenHands automation bridge yet.
- No multi-agent refactor orchestration yet.
- No paid web APIs.
