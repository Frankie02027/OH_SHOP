# AgenticSeek Integration Report

Date: 2026-03-22
Workspace: `/home/dev/OH_SHOP`
Studied upstream:
- Repo: `Fosowl/agenticSeek`
- Commit examined: `1036c5fbc1fc989a7725ee5ea7ab8cee3b639f24`
- Repo URL: <https://github.com/Fosowl/agenticSeek>

## 1. Executive Summary

Do not replace `AI---browser-use` with all of AgenticSeek wholesale.

AgenticSeek is a full local-agent product with:
- its own frontend/backend app
- its own browser runtime abstraction
- Redis-backed service orchestration
- its own prompt/memory/agent loop
- Selenium + ChromeDriver + undetected-chromedriver based browsing

Our current project is different:
- OpenHands is the orchestrator
- `oh-browser-mcp` is a narrow external MCP tool server
- browsing is supposed to be one reusable tool: `web_research`
- the Phase 1 contract requires real browser browsing plus real browser download capture and artifact hashing

The correct pivot is not:
- "replace our stack with AgenticSeek"

The correct pivot is:
- extract and adapt the browser hardening ideas from AgenticSeek
- keep our MCP boundary
- keep OpenHands as the orchestrator
- keep our explicit artifact/checksum contract

## 2. What AgenticSeek Actually Is

From the upstream README and code, AgenticSeek is a broader system than our current browser helper:

- README positions it as a "100% local alternative to Manus AI" with browser, code, planning, voice, and multi-agent behavior.
- The main stack includes `frontend`, `backend`, `redis`, and `searxng`.
- Browser execution is implemented in a local Python browser wrapper, not as a standalone MCP microservice.
- Browser automation uses Selenium, ChromeDriver, `undetected_chromedriver`, `selenium-stealth`, and manual "human-like" interaction helpers.

Relevant upstream files:
- README: <https://github.com/Fosowl/agenticSeek/blob/main/README.md>
- Browser runtime: <https://github.com/Fosowl/agenticSeek/blob/main/sources/browser.py>
- Browser agent loop: <https://github.com/Fosowl/agenticSeek/blob/main/sources/agents/browser_agent.py>
- Searx tool: <https://github.com/Fosowl/agenticSeek/blob/main/sources/tools/searxSearch.py>
- Compose stack: <https://github.com/Fosowl/agenticSeek/blob/main/docker-compose.yml>

## 3. Cross-Reference Against OH_SHOP

Our current relevant files:
- [pyproject.toml](/home/dev/OH_SHOP/repos/oh-browser-mcp/pyproject.toml)
- [browse.py](/home/dev/OH_SHOP/repos/oh-browser-mcp/src/oh_browser_mcp/browse.py)
- [searx.py](/home/dev/OH_SHOP/repos/oh-browser-mcp/src/oh_browser_mcp/searx.py)
- [research.py](/home/dev/OH_SHOP/repos/oh-browser-mcp/src/oh_browser_mcp/research.py)
- [docker-compose.yml](/home/dev/OH_SHOP/compose/docker-compose.yml)
- [patch_openhands_tool_call_mode.py](/home/dev/OH_SHOP/scripts/patch_openhands_tool_call_mode.py)
- [patch_openhands_external_resource_routing.py](/home/dev/OH_SHOP/scripts/patch_openhands_external_resource_routing.py)

### Architecture comparison

`agenticSeek`
- Monolithic local agent app
- Backend owns browser + search + task loop
- Redis and frontend are first-class parts of the product
- Browser is Selenium-based
- Search tool returns parsed HTML search results

`OH_SHOP`
- OpenHands owns the main agent loop
- Browser/search is delegated to an MCP service
- Search and browsing are supposed to be composable tool behavior
- Browser is Playwright-based
- Search is meant to come from SearxNG JSON

### Boundary comparison

`agenticSeek`
- One app owns prompting, browser control, search, and memory
- Fewer network boundaries, more in-process behavior

`OH_SHOP`
- OpenHands app
- OpenHands sandbox runtime
- LM Studio
- `oh-browser-mcp`
- SearxNG

This means AgenticSeek is simpler to reason about inside its own app, but not a clean transplant into our architecture.

## 4. What Is Worth Reusing

### 4.1 Browser hardening ideas

These are the strongest reusable ideas from `sources/browser.py`:

- randomized realistic user agents
- per-run browser profile directories
- explicit stealth/fingerprint masking
- webdriver suppression
- human-like wait jitter
- human-like scrolling
- browser startup with anti-automation options
- explicit handling for Chrome/ChromeDriver mismatch

This is exactly the class of improvement our current [browse.py](/home/dev/OH_SHOP/repos/oh-browser-mcp/src/oh_browser_mcp/browse.py) needs more of.

Good concepts to port:
- session-level browser identity object
- run-specific profile dir
- stronger browser fingerprint script
- randomized delay bands for navigation and interaction
- explicit browser verification-page detection

### 4.2 Agent loop concepts

From `sources/agents/browser_agent.py`, the useful conceptual pieces are:

- maintain search history
- maintain unvisited navigation links
- keep notes per page
- separate:
  - search decision
  - page reading
  - next-link selection
  - stop/exit decision

These ideas fit our MCP tool well.

We should reuse the structure, not the exact implementation:
- keep a `trace`
- keep a visited/unvisited queue
- stop when evidence threshold is reached
- stop when a file page or download target is confidently reached

### 4.3 Browser safety / anti-detection posture

AgenticSeek is more mature than our current code in these areas:
- randomized waits
- human-like scrolling
- stealth browser launch defaults
- nontrivial Chrome flag setup

Those should be translated into Playwright equivalents inside [browse.py](/home/dev/OH_SHOP/repos/oh-browser-mcp/src/oh_browser_mcp/browse.py).

## 5. What Should Not Be Reused As-Is

### 5.1 Do not replace Playwright with Selenium just because AgenticSeek does

Why not:
- our Phase 1 contract already assumes Playwright/browser-event style downloads
- Selenium + ChromeDriver + undetected-chromedriver adds heavy runtime complexity
- Chrome/ChromeDriver version drift is one of AgenticSeek’s own documented pain points
- it is a worse fit for our current MCP microservice design

Bottom line:
- reuse browsing strategy ideas
- do not replace our browser engine unless Playwright proves fundamentally unworkable

### 5.2 Do not copy their Searx tool directly

`sources/tools/searxSearch.py` is not a good drop-in for us because it:
- parses Searx HTML instead of using the JSON API
- uses synchronous `requests`
- validates links one-by-one
- is designed for their agent loop, not our MCP contract

Our current [searx.py](/home/dev/OH_SHOP/repos/oh-browser-mcp/src/oh_browser_mcp/searx.py) is architecturally closer to what we want, even though it still needs cleanup.

### 5.3 Do not import their whole app stack

Do not absorb:
- frontend
- redis requirement
- backend service model
- their memory/session layer
- their router/planner layer

That would be a product rewrite, not an integration.

## 6. Critical Gap Analysis

### Gap A: Browser hardening

Current `OH_SHOP` state:
- basic Playwright stealth script
- some user-agent rotation
- some pacing
- weak stopping behavior

AgenticSeek advantage:
- deeper startup hardening
- better browser identity shaping
- stronger human-behavior simulation

Action:
- port hardening ideas into Playwright session setup

### Gap B: Navigation loop discipline

Current `OH_SHOP` state:
- queue-based browsing, but still prone to wasting steps
- still drifts into weak links
- artifact classification is still too brittle

AgenticSeek advantage:
- explicit search-history and navigation-decision loop
- explicit note-taking and page assessment

Action:
- split `browse_url()` into smaller stages:
  - open page
  - read page
  - classify page
  - rank next links
  - stop or continue

### Gap C: Download truthfulness

Current `OH_SHOP` issue:
- browser download paths can still capture HTML pages masquerading as files
- this breaks the Phase 1 "real file + checksum" proof quality

AgenticSeek reality:
- it does not appear to provide a first-class artifact hashing/download pipeline matching our contract

Action:
- keep our own artifact pipeline
- harden browser-download validation ourselves
- do not expect AgenticSeek to solve this part for us

This is important:
- AgenticSeek is useful for browsing behavior
- not for our artifact-proof contract

## 7. Recommended Integration Plan

### Recommendation: partial pivot, not full replacement

Use AgenticSeek as a source of:
- browser launch tactics
- stealth tactics
- pacing tactics
- navigation-loop structure

Do not use it as:
- a replacement orchestrator
- a replacement search service
- a replacement MCP boundary
- a replacement proof/download/checksum implementation

### Phase 1: Browser profile subsystem

Create a new module in `oh-browser-mcp`, for example:
- `src/oh_browser_mcp/browser_profile.py`

Move browser identity and pacing into it:
- user-agent rotation
- viewport rotation
- locale/timezone setup
- extra headers
- init script
- jitter settings
- per-session profile dir
- offsite penalty knobs

Source inspiration:
- AgenticSeek `create_chrome_options`
- AgenticSeek `patch_browser_fingerprint`
- AgenticSeek `human_scroll`

### Phase 2: Navigation controller

Refactor [browse.py](/home/dev/OH_SHOP/repos/oh-browser-mcp/src/oh_browser_mcp/browse.py) into explicit steps:

1. open current page
2. detect automation block / verification state
3. extract text
4. extract links
5. classify:
   - content page
   - file page
   - download link
   - junk page
6. choose next action
7. persist richer trace

This is where AgenticSeek `BrowserAgent` is useful as a design reference.

### Phase 3: Download validation layer

Keep our own artifact/download pipeline and harden it:
- reject HTML masquerading as files
- sniff content before accepting artifact
- keep SHA256 generation in our code
- preserve browser-event-origin downloads as the only accepted proof path

This must stay in our codebase because it is part of the OH_SHOP acceptance contract.

### Phase 4: Search cleanup

Refactor [searx.py](/home/dev/OH_SHOP/repos/oh-browser-mcp/src/oh_browser_mcp/searx.py):
- keep Searx JSON API
- remove narrow GitHub-only rescue logic
- replace it with generic retry / engine fallback / throttled search strategy

AgenticSeek does not provide a better search implementation for our architecture.

## 8. Concrete "Use / Don’t Use" Map

### Use from AgenticSeek

- `sources/browser.py`
  - browser identity setup
  - stealth ideas
  - humanized delays
  - browser verification-page handling

- `sources/agents/browser_agent.py`
  - loop structure
  - search-history model
  - page-note / stop-decision design

- README config guidance
  - LM Studio compatibility assumptions
  - SearxNG running alongside the browser agent
  - headless + stealth flags as first-class configuration

### Do not use directly

- `sources/tools/searxSearch.py`
  - wrong transport style for our needs
  - HTML scraping instead of JSON API

- whole `docker-compose.yml`
  - too broad
  - brings in frontend/backend/redis we do not need

- full Selenium browser replacement
  - too invasive
  - too much operational complexity

## 9. Proposed File-Level Changes In OH_SHOP

If Copilot continues this work, it should focus on these files first:

- [browse.py](/home/dev/OH_SHOP/repos/oh-browser-mcp/src/oh_browser_mcp/browse.py)
  - integrate a real browser profile subsystem
  - add stronger verification-page handling
  - refactor page classification / next-link selection
  - tighten browser-download validation

- [searx.py](/home/dev/OH_SHOP/repos/oh-browser-mcp/src/oh_browser_mcp/searx.py)
  - remove site-specific fallback logic
  - make search fallback generic and throttled

- [research.py](/home/dev/OH_SHOP/repos/oh-browser-mcp/src/oh_browser_mcp/research.py)
  - make stop conditions clearer
  - preserve partial successful progress better
  - avoid throwing away useful visited pages on timeout paths

- [pyproject.toml](/home/dev/OH_SHOP/repos/oh-browser-mcp/pyproject.toml)
  - if we keep Playwright, do not import Selenium stack casually
  - if we borrow ideas only, no new heavy dependency is required

- [docker-compose.yml](/home/dev/OH_SHOP/compose/docker-compose.yml)
  - no large pivot needed here unless a new browser-profile cache volume becomes useful

## 10. Final Recommendation

Recommended decision:

- **Do not pivot the whole project to AgenticSeek.**
- **Do pivot the browser hardening strategy using AgenticSeek as a reference.**

Reason:
- AgenticSeek is stronger on anti-detection browser behavior
- our project is stronger on explicit MCP/service boundaries
- our contract is stricter on artifact/download proof than AgenticSeek appears to be

Best outcome:
- keep OpenHands + MCP + SearxNG + Playwright
- import AgenticSeek’s generic browser-hardening ideas
- keep our own search JSON flow and artifact proof flow

## 11. Handoff Notes For Copilot

If Copilot continues from here, the best brief is:

"Do a partial pivot of `oh-browser-mcp` browser hardening using `agenticSeek` as reference. Do not replace OpenHands, MCP, or Searx JSON search. Port only the generic browser identity, stealth, pacing, and navigation-discipline ideas. Keep Playwright. Keep real browser download + SHA256 proof behavior. Remove narrow site-specific rescue logic rather than adding more."

## 12. Bottom Line

AgenticSeek is useful as a **browser behavior donor**, not as a **drop-in replacement architecture**.
