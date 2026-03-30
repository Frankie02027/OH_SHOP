# Phase 1 — Consolidated (OH_SHOP)

> **Historical / non-authoritative document.**
> This file captures an earlier Phase 1 planning state.
> It is useful as implementation history, but several specifics below are now known to be wrong for the current stack:
> - it assumes **Ollama** is the active host provider; current truth is **LM Studio**
> - it assumes `http://oh-browser-mcp:3010/sse` is the preferred OpenHands MCP URL; current truth is `http://host.docker.internal:3010/sse`
> - it treats **OpenHands container reachability** as the key boundary; the real boundary that matters is **sandbox runtime reachability**
> It must not be treated as the current setup guide.
> Current operational truth lives in [SETUP.md](/home/dev/OH_SHOP/docs/SETUP.md) and [authoritative_rework_contract_2026-03-21.md](/home/dev/OH_SHOP/docs/authoritative_rework_contract_2026-03-21.md).

Date: 2026-03-06 (America/Chicago)
Workspace root: `/home/dev/OH_SHOP`

## 0) Purpose
We had **two competing Phase 1 docs**:
- Phase A proof + closeout checklist (existing)
- Phase 1 implementation contract (browser MCP + automation)

This file originally consolidated into **one authoritative Phase 1 plan** at that time.
It is now retained as archive/history only.

**Phase 1 deliverables:**
1) Phase A closeout (A5–A7) — OpenHands can mount a repo, run terminal commands, and talk to host Ollama.
2) Phase 1 feature — add **full web browsing** (real click/navigation + downloads) via an MCP tool server: `oh-browser-mcp`.

---

## 1) Current known-good stack state (must remain true)

### 1.1 Ports must be localhost-only
These services must bind to `127.0.0.1` only (no LAN exposure):
- OpenHands: `127.0.0.1:3000`
- OpenWebUI: `127.0.0.1:3001`
- SearxNG: `127.0.0.1:3002`

### 1.2 Host Ollama requirements
- Ollama runs on the host and must be reachable from containers using: `host.docker.internal`.
- OpenHands LLM base URL must be: `http://host.docker.internal:11434/v1`.

### 1.3 Mount discipline
- Only mount repos under: `/home/dev/OH_SHOP/repos`
- Sandbox path is always: `/workspace`
- Downloads land in: `/home/dev/OH_SHOP/downloads`

---

## 2) Phase A closeout (A5–A7)

### A5 — OpenHands can create/edit a file in `/workspace`
1) Mount a repo into `/workspace`.
2) Create or edit: `/workspace/SANITY.md`
3) Content must include: `PHASE_A_A5_PASS` and a timestamp.
4) Confirm it shows up under OpenHands **Changes**.

### A6 — OpenHands sandbox terminal can see the repo
In OpenHands terminal:
- `ls -la /workspace | head`
- `cat /workspace/SANITY.md`

### A7 — OpenHands can talk to host Ollama
OpenHands Settings → LLM:
- Provider: OpenAI-compatible
- Base URL: `http://host.docker.internal:11434/v1`
- Model: pick one that exists in `ollama list`

Test prompt:
- Reply with exactly: `OK_A7_PASS`

---

## 3) Phase 1 feature: Full Web Browsing via MCP (`oh-browser-mcp`)

### 3.1 Definition of “full browsing” (required)
The tool must:
- search (SearxNG)
- open pages in a real browser (Playwright)
- click links/buttons
- follow link chains across multiple pages
- download files using browser download events

### 3.2 Implementation choice (authoritative)
Use the repo you provided as the browser agent layer:
- `tov-a/AI---browser-use` (Playwright-based, multi-step navigation)

Wrap it inside a single MCP tool server:
- service: `oh-browser-mcp`
- tool exposed to OpenHands: `web_research`

SearxNG is **not** an MCP server. `oh-browser-mcp` will call SearxNG internally.

### 3.3 MCP connectivity rules (important)
OpenHands connects to MCP servers from inside the OpenHands container.
Therefore the MCP URL must be reachable from that container.

**Preferred:** Put `oh-browser-mcp` on the same docker compose network and connect via:
- `http://oh-browser-mcp:3010/sse`

(Optional debug): also publish `127.0.0.1:3010` on the host, but do not rely on host localhost for OpenHands.

---

## 4) Phase 1 tasks (no bloat)

### 4.1 Build `oh-browser-mcp` repo
Create:
- `/home/dev/OH_SHOP/repos/oh-browser-mcp/` with the expected Python layout and Dockerfile.

Expose MCP over SSE:
- `GET /sse`
- `POST /messages/`
- plus `GET /health`

### 4.2 Compose wiring
Add the `oh-browser-mcp` service to compose:
- internal port: 3010
- depends_on: searxng
- mounts:
  - `/home/dev/OH_SHOP/downloads:/data/downloads`
  - `/home/dev/OH_SHOP/data/oh_browser_mcp:/data`
- extra_hosts: `host.docker.internal:host-gateway`

### 4.3 Register MCP server in OpenHands
OpenHands → Settings → MCP:
- Type: SSE
- URL: `http://oh-browser-mcp:3010/sse`

### 4.4 Verify browsing actually works
Use `web_research` on a link-chase task (GitHub releases → asset download).

Pass conditions:
- visited pages >= 2
- at least 1 downloaded artifact in `/home/dev/OH_SHOP/downloads`
- tool returns sources + artifact sha256

---

## 5) Verification scripts

### 5.1 `scripts/verify_phase_a.sh`
Checks:
- `curl -I http://127.0.0.1:3000`
- `curl -I http://127.0.0.1:3001`
- `curl -I http://127.0.0.1:3002`
- `curl -s http://127.0.0.1:11434/api/tags | head`
- `curl -s "http://127.0.0.1:3002/search?q=test&format=json" | head`

### 5.2 `scripts/verify_phase_1.sh`
Checks:
- Phase A endpoints above
- `oh-browser-mcp` health endpoint
- one `web_research` call (transport-specific) returning:
  - sources >= 2
  - visited >= 2
  - artifacts >= 1

---

## 6) Archive note
The Phase A execution proof log is valuable but verbose.
Keep it as an archived appendix file in the repo (e.g. `docs/phase_a_proof.md`).
This document is retained as historical planning context, not as the current operational guide.
