# OH_SHOP full browser-stack replacement plan: rip out current browser tooling and replace it with Stagehand

## Executive summary

This report is rewritten to match the actual requested direction:

- **do not keep the current browser stack alive**
- **do not keep a hybrid Python Playwright + Stagehand stack**
- **do not keep `browser-use` as optional dead code**
- **do not keep `oh-browser-mcp` as the active browser service**
- **do not keep SearxNG as part of the browser stack if the new direction is “Stagehand does it all”**

The clean replacement plan is:

1. **delete the current browser implementation path** (`oh-browser-mcp`, SearxNG service wiring, browser-use dependency chain, browser-related verification logic)
2. **replace it with one new service**: `oh-stagehand-mcp`
3. build that service in **TypeScript + Node 20**
4. run Stagehand in **`LOCAL` mode**
5. point Stagehand at **LM Studio** through the local OpenAI-compatible endpoint
6. expose the new service to OpenHands over **MCP using SHTTP**
7. keep the OpenHands-facing tool name stable only if useful for compatibility, but do **not** preserve the old implementation under the hood

The important distinction is:

- keeping the **same tool name** is not “mixing stacks”
- keeping the **old Python browser engine** would be mixing stacks

So the correct move is:

- **same contract if convenient**
- **completely different implementation underneath**

---

# 1. What the project is doing today

## 1.1 Active browser path

The real browser stack today is centered on `repos/oh-browser-mcp`.

That service currently owns:

- MCP server transport
- `web_research` tool definition
- SearxNG search orchestration
- URL candidate gathering
- Playwright page navigation
- downloads and SHA256 artifact generation
- some page expansion / click heuristics
- dead `browser-use` agent branch

The current active compose services tied to that path are:

- `searxng`
- `oh-browser-mcp`

The current top-level flow is:

`OpenHands -> MCP registration -> oh-browser-mcp -> SearxNG + Playwright/browser-use -> response`

That is the browser stack you said to rip out.

---

## 1.2 What is dead vs live

### Live today

- `repos/oh-browser-mcp/src/oh_browser_mcp/server.py`
- `repos/oh-browser-mcp/src/oh_browser_mcp/research.py`
- `repos/oh-browser-mcp/src/oh_browser_mcp/searx.py`
- `repos/oh-browser-mcp/src/oh_browser_mcp/browse.py`
- `compose/docker-compose.yml` service definitions for `searxng` and `oh-browser-mcp`
- `scripts/agent_house.py` verification and smoke-test logic that expects `oh-browser-mcp`
- docs that currently describe `oh-browser-mcp` as the implemented browser server

### Installed but effectively dead

- `browser-use`

The `browser-use` integration exists in code but is gated off for the LM Studio route you are actually using.

That means this repo currently has a false browser story:

- docs/commentary imply agentic browser support exists
- runtime behavior falls back to deterministic Playwright

That dead branch should not survive the rewrite.

### Not part of the active runtime

- `repos/agenticSeek`
- `mcp/web_tools_mcp`

These are not the live browser stack.

---

# 2. Exact rip-out scope

If the direction is **full replacement**, then the following parts should be removed from the active system.

## 2.1 Rip out the entire `oh-browser-mcp` implementation as the active browser service

Target:

- `repos/oh-browser-mcp/`

What that removes:

- Python MCP server implementation
- Python search orchestration
- Python browse executor
- Playwright page loop in Python
- `browser-use` dead branch
- artifact handling owned by that service

You can either:

- delete it outright after replacement is working, or
- move it to an archive folder like `archive/oh-browser-mcp/`

For a clean repo, archiving temporarily is fine during migration, but it should not remain wired into compose or docs.

---

## 2.2 Rip out SearxNG from the active browser stack

Target:

- `searxng` service in `compose/docker-compose.yml`
- SearxNG references in docs and verification logic
- Python search client logic in `searx.py`

Why:

If Stagehand is taking over the browser stack completely, then the old search-first + Python browse architecture should not stay as a parallel control plane.

This is a deliberate tradeoff:

- you lose deterministic metasearch seeding from your current Python stack
- you gain one consistent browser intelligence layer

If later you want external search back, add it back deliberately as a Stagehand-side MCP integration or as a separate explicit upstream tool.

Do **not** keep old Searx orchestration “just in case” if the rewrite goal is full replacement.

---

## 2.3 Rip out browser-use completely

Targets:

- `browser-use @ git+https://github.com/tov-a/AI---browser-use@main` in `repos/oh-browser-mcp/pyproject.toml`
- browser-use-specific code in `browse.py`
- browser-use mentions in docs
- compose comments that claim browser-use is part of the current architecture

Why:

- it is dead in the LM Studio route you are actually using
- it is misleading in docs
- it adds dependency and maintenance cost with no runtime value

Do not keep it as a “future maybe.”

---

## 2.4 Rip out browser-specific verification logic tied to the old stack

Targets:

- `scripts/agent_house.py`
- `scripts/verify.sh`
- `scripts/verify.py`
- any proof templates and docs that assume `oh-browser-mcp`

Examples of what must change:

- `CORE_SERVICES` currently lists `searxng` and `oh-browser-mcp`
- expected transport URL currently points to the old browser MCP server
- readiness checks currently probe `/health`, `/ready`, and `/sse` on port `3010`
- smoke tests currently look for `web_research` flowing through the old service

All of that must be rewritten around the new Stagehand-backed service.

---

## 2.5 Rip out active docs that describe the old browser stack as current truth

Targets:

- `docs/SETUP.md`
- current browser-handoff docs
- current implementation notes that describe SearxNG + oh-browser-mcp as the active browser layer
- comments in compose and scripts

Historical docs can remain historical if clearly marked, but the active docs must stop describing the old browser path as current.

---

# 3. What should replace it

The clean replacement is a new service:

- `repos/oh-stagehand-mcp/`

This service should be:

- **TypeScript-based**
- **Node 20 based**
- **Stagehand in LOCAL mode**
- **LM Studio-backed**
- **MCP-exposed directly to OpenHands**
- **the only browser service in the active stack**

That means the new flow becomes:

`OpenHands -> oh-stagehand-mcp -> Stagehand -> local Chromium -> LM Studio`

No Python browser layer.
No SearxNG layer.
No browser-use lane.
No hidden fallback branch.

---

# 4. Why Stagehand should replace the current stack directly

## 4.1 Why not keep the Python MCP server and call Stagehand behind it

Because you explicitly do not want a mixed stack.

Keeping `oh-browser-mcp` alive as a Python orchestrator would mean:

- one transport layer in Python
- one browser brain in TS
- one old set of docs and probes to maintain
- one old service name still implying the old stack exists

That is exactly the kind of muddled architecture you said you do **not** want.

So if Stagehand is the new browser stack, then Stagehand should sit behind the actual active MCP server boundary.

---

## 4.2 Why not generate one-off Stagehand scripts every run

Because that would be another bad abstraction.

The right model is:

- build a stable MCP server that owns Stagehand usage
- let the MCP server call Stagehand methods directly (`agent`, `act`, `extract`, `observe`)
- keep all browser state, tracing, artifacts, and failure handling inside one maintained codebase

Do **not** make OpenHands write temporary custom Stagehand scripts for every browsing task.

That would create:

- more moving parts
- worse debugging
- worse reproducibility
- more brittle prompts

---

# 5. Exact new architecture

## 5.1 New repo subtree

Create:

```text
repos/oh-stagehand-mcp/
  package.json
  tsconfig.json
  Dockerfile
  .env.example
  src/
    server.ts
    config.ts
    health.ts
    lmstudio.ts
    tools/
      webResearch.ts
      browserAgentTask.ts
      browserExtract.ts
    stagehand/
      createStagehand.ts
      runAgentTask.ts
      runExtract.ts
      runObserve.ts
      artifacts.ts
      logging.ts
      schemas.ts
```

This becomes the single active browser service.

---

## 5.2 Service contract

Because you are replacing the stack, you have two sane options for the MCP surface.

### Option A — compatibility-first

Expose one high-level tool again:

- `web_research`
minimize token use and tool calls as i am over my token budget already and am paying extra

But now it is implemented entirely by Stagehand.

This is the fastest path if you want to preserve OpenHands prompts, smoke tests, and tool expectations.

### Option B — Stagehand-native surface

Expose a small set of Stagehand-style tools:

- `browser_stagehand_agent`
- `browser_stagehand_act`
- `browser_stagehand_extract`
- `browser_stagehand_observe`

This is cleaner conceptually, but it will require more prompt and verification rework.

### My recommendation

Use **Option A first**.

Not because the old implementation should survive.
It should not.

Use Option A because keeping the tool name `web_research` lets you:

- keep OpenHands-facing semantics stable
- change only one implementation layer at a time
- avoid additional tool-discovery churn in the agent

Internally, the old code is gone.
Only the external tool contract remains.

---

## 5.3 Recommended transport

Use **SHTTP / streamable HTTP** for the new Stagehand MCP service.

Reasons:

- OpenHands Local GUI supports SSE, SHTTP, and stdio
- official Browserbase MCP docs are written around STDIO and SHTTP
- if you are doing a full replacement, there is no reason to stay married to the old SSE-only shape
- current MCP JS tooling is more naturally aligned with HTTP-based servers than rebuilding the exact old SSE server by hand

That means the new registration target should look like something like:

- `http://host.docker.internal:3020/mcp`

If you want absolute minimum OpenHands config churn, you can still implement SSE.
But for a clean cut, SHTTP is the better long-term move.

---

# 6. Installation and dependency plan

## 6.1 Runtime choice

Use:

- **Node.js 20 LTS**
- **TypeScript**
- **Dockerized service**

Do **not** run this as a host-only Node install if the rest of the stack is already Dockerized.

---

## 6.2 Required dependencies

Suggested production dependencies:

- `@browserbasehq/stagehand`
- `playwright-core`
- `@modelcontextprotocol/sdk`
- `zod`
- `pino`
- `fastify` or `express`

Suggested dev dependencies:

- `typescript`
- `tsx`
- `@types/node`
- `@types/express` if using Express

### Why each dependency exists

- `@browserbasehq/stagehand` → Stagehand runtime itself
- `playwright-core` → browser control integration for Stagehand
- `@modelcontextprotocol/sdk` → MCP server implementation
- `zod` → strong request/response schema validation
- `pino` → structured logs
- `fastify`/`express` → HTTP server wrapper if needed around MCP transport

Do **not** carry over any Python browser libs.

---

## 6.3 Required system/browser dependencies

Because this is local Stagehand, you need a real local browser in the container.

Recommended Docker browser setup:

- install `chromium`
- install required Linux browser libs
- install Playwright Chromium support with `npx playwright install chromium`

Do not rely on Browserbase cloud.
Do not require Browserbase credentials.

---

## 6.4 Example install sequence inside the new repo

```bash
cd /home/dev/OH_SHOP/repos
mkdir -p oh-stagehand-mcp
cd oh-stagehand-mcp
npm init -y
npm install @browserbasehq/stagehand playwright-core @modelcontextprotocol/sdk zod pino fastify
npm install -D typescript tsx @types/node
npx tsc --init
```

If you choose Express instead of Fastify:

```bash
npm install express
npm install -D @types/express
```

---

# 7. Dockerfile recommendation

Use a dedicated Dockerfile for the new service.

Example shape:

```dockerfile
FROM node:20-bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    ca-certificates \
    dumb-init \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

COPY package.json package-lock.json* ./
RUN npm install

COPY tsconfig.json ./
COPY src ./src

ENV NODE_ENV=production \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    CHROME_PATH=/usr/bin/chromium \
    STAGEHAND_ENV=LOCAL \
    MCP_PORT=3020

RUN npx playwright install chromium

EXPOSE 3020
ENTRYPOINT ["dumb-init", "--"]
CMD ["npx", "tsx", "src/server.ts"]
```

This is the right direction because it:

- keeps the browser inside the service container
- avoids Browserbase cloud dependencies
- gives reproducible Linux browser behavior
- matches the rest of the project’s containerized runtime model

---

# 8. LM Studio configuration

## 8.1 What is officially supported vs what is not

What is solid:

- Stagehand docs explicitly support `env: "LOCAL"`
- Stagehand docs explicitly support a custom model object with `modelName`, `apiKey`, and `baseURL`
- LM Studio exposes OpenAI-compatible endpoints on `http://localhost:1234/v1`
- LM Studio supports `/v1/models`, `/v1/responses`, and `/v1/chat/completions`

What is **not** cleanly documented by Stagehand:

- there is no polished official “LM Studio quickstart” page
- there is public evidence that users struggled with local LM Studio / Ollama in Stagehand v3 around the `/v1/responses` shift

So the implementation should treat LM Studio as **supported by interface**, but still require a smoke test before large migration work is trusted.

---

## 8.2 Environment variables for the new service

Recommended env block:

```env
STAGEHAND_ENV=LOCAL
STAGEHAND_MODEL=openai/<exact-lmstudio-model-id>
STAGEHAND_LLM_BASE_URL=http://host.docker.internal:1234/v1
STAGEHAND_LLM_API_KEY=lm-studio
CHROME_PATH=/usr/bin/chromium
HEADLESS=true
MCP_PORT=3020
DOWNLOAD_DIR=/data/downloads
LOG_DIR=/data/logs
```

Important:

- do **not** guess the model identifier
- query LM Studio `/v1/models` and use the exact returned ID

---

## 8.3 Stagehand constructor example for this repo

```ts
import { Stagehand } from "@browserbasehq/stagehand";

export function createStagehand() {
  return new Stagehand({
    env: "LOCAL",
    experimental: true,
    verbose: 2,
    cacheDir: "/data/cache/stagehand",
    model: {
      modelName: process.env.STAGEHAND_MODEL!,
      apiKey: process.env.STAGEHAND_LLM_API_KEY || "lm-studio",
      baseURL: process.env.STAGEHAND_LLM_BASE_URL || "http://host.docker.internal:1234/v1",
    },
    localBrowserLaunchOptions: {
      executablePath: process.env.CHROME_PATH || "/usr/bin/chromium",
      headless: process.env.HEADLESS !== "false",
      viewport: { width: 1440, height: 900 },
      args: ["--no-sandbox", "--disable-setuid-sandbox"],
    },
    selfHeal: true,
  });
}
```

If direct model config gives trouble with LM Studio, the fallback is to test a custom client path against LM Studio, but do **not** complicate the design before the simplest config fails.

---

# 9. Compose changes

## 9.1 Remove these services

From `compose/docker-compose.yml`, remove:

- `searxng`
- `oh-browser-mcp`

Also remove related volumes:

- `searxng_data`

Also remove browser comments that mention:

- SearxNG
- browser-use
- old Playwright Python server path

---

## 9.2 Add new service

Add:

- `oh-stagehand-mcp`

Example high-level service block:

```yaml
  oh-stagehand-mcp:
    build:
      context: ../repos/oh-stagehand-mcp
    container_name: oh-stagehand-mcp
    ports:
      - "127.0.0.1:3020:3020"
      - "${DOCKER_BRIDGE_GATEWAY:-172.17.0.1}:3020:3020"
    environment:
      - STAGEHAND_ENV=LOCAL
      - STAGEHAND_MODEL=${STAGEHAND_MODEL}
      - STAGEHAND_LLM_BASE_URL=http://host.docker.internal:1234/v1
      - STAGEHAND_LLM_API_KEY=lm-studio
      - CHROME_PATH=/usr/bin/chromium
      - MCP_PORT=3020
      - DOWNLOAD_DIR=/data/downloads
      - LOG_DIR=/data/logs
    extra_hosts:
      - "host.docker.internal:host-gateway"
    volumes:
      - /home/dev/OH_SHOP/downloads:/data/downloads
      - /home/dev/OH_SHOP/data/oh_stagehand_mcp:/data
    healthcheck:
      test:
        [
          "CMD",
          "node",
          "-e",
          "fetch('http://127.0.0.1:3020/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"
        ]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 15s
    restart: unless-stopped
```

If you choose SHTTP, expose the MCP endpoint at something like `/mcp`.

---

# 10. OpenHands registration changes

## 10.1 Replace the old MCP endpoint

Old world:

- `http://host.docker.internal:3010/sse`

New world:

- `http://host.docker.internal:3020/mcp` if using SHTTP

or

- your new SSE path if you intentionally keep SSE

Because this is a full replacement, the old browser MCP registration should be removed completely from OpenHands settings.

---

## 10.2 Verification changes

Update `scripts/agent_house.py` and related verification so they now prove:

- `oh-stagehand-mcp` container is up
- its `/health` endpoint is reachable
- its stricter `/ready` endpoint confirms:
  - Chromium available
  - LM Studio reachable
  - Stagehand initialization path healthy
- OpenHands can see and call the new tool from a fresh session

Delete checks specific to:

- `searxng`
- `/sse` on port `3010`
- old `oh-browser-mcp`

---

# 11. What the new tool should actually do

## 11.1 Recommended first tool surface

For phase 1, expose just one browser task tool:

- `web_research`

This tool should take:

- `query`
- optional `start_url`
- optional `allowed_domains`
- optional `max_steps`
- optional `download`

Internally, the service should:

1. create a Stagehand session
2. navigate to a start page if provided, otherwise start from a search engine or direct URL logic inside Stagehand
3. run agentic browsing with bounded steps
4. extract result text / final findings
5. download artifacts when applicable
6. return:
   - answer
   - sources
   - quotes/notes
   - artifacts
   - trace

The old Python search/browse logic is gone.
The Stagehand service owns the whole job.

---

## 11.2 Real-world examples of how this should behave

### Example A — find a specific forum post

Prompt:

- `Find the forum thread where users discuss NVIDIA 580 driver crashes on Linux and summarize the workaround.`

Expected Stagehand behavior:

- open a search engine page or direct community/forum target
- navigate results
- open likely threads
- read content across multiple pages if needed
- return URLs + summary

### Example B — walk a documentation site

Prompt:

- `Open the Stagehand docs and find how LOCAL mode is configured with a custom model endpoint.`

Expected Stagehand behavior:

- navigate docs
- open the browser config page
- open model config page
- extract relevant config examples
- return exact findings and URLs

### Example C — locate and download a release asset

Prompt:

- `Go to the project releases page, download the Linux amd64 tarball for version 2.4.1, and report the saved file path and SHA256.`

Expected Stagehand behavior:

- navigate releases
- open the correct release
- identify the correct asset
- trigger download
- save file in `/data/downloads`
- return file metadata

These are the kinds of jobs the current deterministic Python browser stack handles badly or inconsistently.

---

# 12. Recommended implementation phases

## Phase 0 — prove Stagehand + LM Studio in isolation

Before wiring the repo deeply, do a minimal local smoke test inside `repos/oh-stagehand-mcp`:

- Stagehand in `LOCAL` mode
- LM Studio via `baseURL=http://host.docker.internal:1234/v1`
- simple `page.goto()` + `extract()`
- simple `agent()` run

This matters because Stagehand’s docs expose the right config surface, but there is no strong official LM Studio quickstart and there has been at least one public unresolved report of local LM Studio/Ollama trouble.

Do **not** skip this smoke test.

---

## Phase 1 — build the new MCP service

Implement:

- health endpoint
- ready endpoint
- one MCP tool
- local Chromium launch
- LM Studio model config
- basic artifact handling

Do **not** wire the whole repo around it until this service runs cleanly in isolation.

---

## Phase 2 — switch compose + OpenHands registration

Do the cutover:

- remove `searxng`
- remove `oh-browser-mcp`
- add `oh-stagehand-mcp`
- change OpenHands MCP registration
- update verification scripts

At this point, the old browser stack is no longer active.

---

## Phase 3 — delete/archive old code

After the new stack proves itself:

- archive or delete `repos/oh-browser-mcp`
- archive or delete old browser proof docs
- archive Searx-specific notes if still useful historically
- remove old ports and health checks

This is where the repo becomes honest again.

---

# 13. Specific file-by-file change map

## Delete / archive

- `repos/oh-browser-mcp/`
- old browser-specific proof artifacts if they only refer to the removed stack

## Edit

- `compose/docker-compose.yml`
- `scripts/agent_house.py`
- `scripts/verify.sh`
- `scripts/verify.py` if still used
- `docs/SETUP.md`
- any active authoritative browser docs

## Add

- `repos/oh-stagehand-mcp/`
- `data/oh_stagehand_mcp/`
- new proof template for Stagehand fresh-session validation

---

# 14. The biggest risks

## 14.1 LM Studio compatibility is supported by interface, not by a polished official quickstart

Do not assume the first model you try will behave well.

Mitigation:

- smoke test with exact LM Studio `/v1/models` IDs
- prove `agent()` and `extract()` before full repo cutover

## 14.2 Stagehand cloud/MCP docs are Browserbase-heavy

Do not accidentally wire paid Browserbase cloud back into the project.

Mitigation:

- explicitly set `env: "LOCAL"`
- do not set `BROWSERBASE_API_KEY`
- do not use the official remote hosted MCP URL

## 14.3 Replacing SearxNG means search quality becomes model/browser-driven

That may be fine for your stated direction, but it is a real tradeoff.

Mitigation:

- benchmark the new service on the exact tasks that matter to you
- if you later want search back, add it explicitly instead of reviving old code

---

# 15. Bottom-line recommendation

For **your stated goal**, the correct architecture is:

`OpenHands -> oh-stagehand-mcp -> Stagehand LOCAL -> local Chromium -> LM Studio`

And the correct repo action is:

- **remove `oh-browser-mcp` from the active system**
- **remove `searxng` from the active system**
- **remove `browser-use` completely**
- **replace the old browser stack with one new Stagehand MCP service**
- **use SHTTP unless you have a very specific reason to preserve SSE**
- **smoke test Stagehand + LM Studio first before doing the full cutover**

That is the clean cut.
Not a hybrid.
Not a fallback chain.
Not a sidecar hiding behind the old Python browser layer.

That is the rewrite path that actually matches what you asked for.

