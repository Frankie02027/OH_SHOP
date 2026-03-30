# Independent Technical Audit — OH_SHOP

**Date:** 2026-03-21 (updated same day after remediation)  
**Auditor:** Independent (Copilot, principal-engineer-grade)  
**Scope:** Full project at `/home/dev/OH_SHOP`  
**Method:** Code inspection, config analysis, live runtime verification, doc cross-reference  

---

## 1. Executive Summary

**Judgment: Partially coherent. The Docker service layer works. The model provider is down. The main deliverable is built but not connected.**

OH_SHOP is a local-first AI agent workstation: OpenHands (code agent) + OpenWebUI (chat cockpit) + LM Studio (local LLM) + SearxNG (search) + a custom Playwright-based browser tool (`oh-browser-mcp`), all orchestrated via Docker Compose on a single Parrot Linux box. The mission is sound and the target architecture is sane.

The services layer is genuinely operational — five long-running containers all report healthy, the compose file is coherent, the orchestration scripts work, and the networking (DNAT, bridge exposure, `host.docker.internal`) is correctly engineered. The `oh-browser-mcp` browsing tool server is the strongest deliverable: ~800 lines of real, non-trivial Playwright+SearxNG integration that actually runs and passes health checks.

However, at audit time: **LM Studio is not running** (no process, port 1234 not listening), which means the entire stack is headless — no model provider is available to any component. The critical MCP wiring that would make `oh-browser-mcp` visible to OpenHands **has never been configured** (all three MCP server arrays are empty). The docs are a patchwork of three different eras: the original Ollama-centric setup, the LM Studio migration, and the audit/cleanup docs written today. Only the audit-era docs are close to truthful, and even they speak in present tense about infrastructure (LM Studio) that is not currently running.

The project is not broken. It is approximately one good afternoon of focused work away from being coherent. But it is not coherent yet.

---

## 2. Repo Reality

### What exists in the repo

| Path | Status | Notes |
|------|--------|-------|
| `compose/docker-compose.yml` | **Real, working** | Single authoritative compose file, 6 services, all healthy |
| `compose/openhands.compose.yml` | **Redundant subset** | Exact copy of the openhands+chat-guard portion of docker-compose.yml |
| `scripts/agent_house.py` | **Real, working** | Well-written orchestration with verify cycles |
| `scripts/chat_guard.py` | **Real, working** | Conservative SQLite cleanup of orphan rows |
| `scripts/up.sh`, `down.sh`, `verify.sh` | **Real, thin wrappers** | Just call agent_house.py |
| `scripts/backup_state.sh` | **Real, working** | Backs up correctly, including LM Studio configs |
| `scripts/lmstudio-docker-dnat.sh` | **Real, working** | Proper iptables DNAT rule |
| `scripts/verify.py` | **Real, thin wrapper** | Calls agent_house.py verify |
| `systemd/lmstudio-docker-dnat.service` | **Real, active** | Registered systemd unit, currently active |
| `repos/oh-browser-mcp/` | **Real, substantial** | ~800 LOC, 7 source files, Dockerfile, pyproject.toml |
| `data/openhands/` | **Real, live state** | settings.json, openhands.db, JWT secret, conversations |
| `data/oh_browser_mcp/` | **Real, data dir** | logs/downloads dirs for browser MCP |
| `artifacts/backups/20260321_121448/` | **Real backup** | Pre-cleanup snapshot, identical to current state |
| `artifacts/ollama_model_inventory_2026-03-06.txt` | **Historical artifact** | Shows original Ollama models + LM Studio migration |
| `bridge/openapi_server/` | **Placeholder** | Single README saying "Phase C placeholder" |
| `mcp/web_tools_mcp/` | **Placeholder** | Single README saying "Phase B placeholder" — superseded by oh-browser-mcp |
| `docs/*.md` | **Mixed truth** | See Section 6 |
| `plaintext.txt` | **Scratch note** | SSH command + verify invocation examples |

### Repo truth vs doc truth

| Claim (docs) | Reality (repo + runtime) |
|---------------|-------------------------|
| Ollama is the canonical provider | **False.** Ollama is not installed. LM Studio is configured everywhere. |
| LM Studio is running on the host | **False at audit time.** No process, port 1234 not listening. |
| `oh-browser-mcp` is registered in OpenHands | **False.** `mcp_config.sse_servers` is empty in settings.json. |
| OpenHands controller is Docker-backed | **True.** `openhands-app` container, compose-managed. |
| `openhands serve` launches Docker | **True.** CLI 1.13.0 `serve` runs `docker run`. |
| OpenWebUI is bridge-integrated with OpenHands | **False.** No bridge exists. Phase C is a placeholder README. |
| Host-native OpenHands launch is viable | **Misleading.** The CLI's `serve` already uses Docker internally. |
| `mcp/web_tools_mcp` is the Phase B MCP server | **Superseded.** It's a 3-line placeholder. `repos/oh-browser-mcp` is the real one. |

---

## 3. Current Architecture

### 3.1 Host OS responsibilities

| Responsibility | Status | Evidence |
|----------------|--------|----------|
| Docker Engine | **Running** | `docker ps` returns 7 containers |
| LM Studio application | **NOT RUNNING** | `pgrep lm-studio` empty, port 1234 not listening |
| LM Studio DNAT rule | **Active but useless** | systemd unit active, but LM Studio is down |
| sysctl `route_localnet` | **Configured** | `/etc/sysctl.d/99-docker-localnet.conf` present |
| OH_SHOP data directories | **Present** | `/home/dev/OH_SHOP/data/*` |
| OpenHands CLI | **Installed** | `openhands` 1.13.0 at `/home/dev/.local/bin/openhands` |
| `lms` CLI | **Installed** | At `/home/dev/.lmstudio/bin/lms` |
| `~/.openhands` symlink | **Active** | Points to `/home/dev/OH_SHOP/data/openhands` |
| Ollama | **NOT INSTALLED** | `which ollama` returns nothing, service inactive |
| UFW firewall | **ACTIVE (remediated)** | Was inactive at initial audit. Now enabled: default deny incoming, allow outgoing, allow loopback + SSH. Stale Ollama docker0 rule removed. |

### 3.2 Docker application services

| Container | Image | Network | Status | Health |
|-----------|-------|---------|--------|--------|
| `openhands-app` | `docker.openhands.dev/openhands/openhands:latest` | `compose_default` (172.18.0.4) | Up ~1hr | healthy |
| `open-webui` | `ghcr.io/open-webui/open-webui:main` | `compose_default` | Up 3hr | healthy |
| `searxng` | `searxng/searxng:latest` | `compose_default` | Up 3hr | healthy |
| `oh-browser-mcp` | `compose-oh-browser-mcp` (local build) | `compose_default` (172.18.0.3) | Up 2hr | healthy |
| `openhands-chat-guard` | `python:3.11-alpine` | `compose_default` | Up 3hr | no healthcheck |

### 3.3 Docker execution sandboxes

| Container | Image | Network | Status |
|-----------|-------|---------|--------|
| `oh-agent-server-7WJWw...` | `ghcr.io/openhands/agent-server:61470a1-python` | `bridge` (172.17.0.2) | Up ~1hr |
| `oh-agent-server-CgaaD...` | `ghcr.io/openhands/agent-server:61470a1-python` | `bridge` (172.17.0.3) | Up ~1hr |

### 3.4 Model/provider path

**Intended:** Host LM Studio → `127.0.0.1:1234` → DNAT from Docker → `host.docker.internal:1234` → containers use OpenAI-compatible `/v1` API.

**Actual:** LM Studio is not running. The entire model path is broken.

- OpenHands settings: `llm_base_url: http://host.docker.internal:1234/v1`, model: `openai/all-hands_openhands-lm-32b-v0.1`
- OpenWebUI env: `OPENAI_API_BASE_URLS=http://host.docker.internal:1234/v1`
- oh-browser-mcp config defaults: `LLM_BASE_URL=http://host.docker.internal:1234/v1`
- LM Studio http-server-config (from backup): `networkInterface: 127.0.0.1`, `port: 1234`
- LM Studio configured `defaultContextLength: 32768`

All configuration is consistent and correct. The provider is simply not running.

### 3.5 Tool/MCP path

**Intended:** `oh-browser-mcp` container exposes `web_research` tool via MCP SSE at `http://oh-browser-mcp:3010/sse`. OpenHands registers it and agents can call it.

**Actual:** The server runs and is healthy. The health endpoint works. The SSE endpoint presumably works (container is on `compose_default` network with OpenHands). But **OpenHands `mcp_config` is `{"sse_servers":[],"stdio_servers":[],"shttp_servers":[]}`**. The tool is invisible to the agent.

### 3.6 Network/control flow

```
Host (127.0.0.1)
├── :3000 → openhands-app (compose_default)
├── :3001 → open-webui (compose_default)
├── :3002 → searxng (compose_default)
├── :3010 → oh-browser-mcp (compose_default)
├── :1234 → LM Studio (NOT RUNNING)

172.17.0.1:3000 → openhands-app (bridge exposure for agent-server containers)

DNAT: 172.16.0.0/12:1234 → 127.0.0.1:1234 (for Docker→LM Studio)

Agent-server containers (bridge network):
├── Reach controller via host.docker.internal:3000 → 172.17.0.1:3000 → openhands-app
├── Reach LM Studio via host.docker.internal:1234 → DNAT → 127.0.0.1:1234
```

**Critical observation:** The bridge-exposure hack (`172.17.0.1:3000`) works but is fragile. Agent-servers on `bridge` cannot resolve container names on `compose_default`. The communication path is: agent-server → `host.docker.internal` → host → `172.17.0.1:3000` → port-mapping → openhands-app. This is a real working solution, but it depends on the `DOCKER_BRIDGE_GATEWAY` variable being correct.

### 3.7 Persistence/state layout

| Path | Contents | Owner | Notes |
|------|----------|-------|-------|
| `/home/dev/OH_SHOP/data/openhands/settings.json` | OpenHands config | root:root | Written by container |
| `/home/dev/OH_SHOP/data/openhands/openhands.db` | SQLite: 2 conversations, 2 start-tasks, 2 callbacks | root:root | Active |
| `/home/dev/OH_SHOP/data/openhands/v1_conversations/` | 5 conversation dirs, ~30+ event JSON files | root:root | Created by container |
| `/home/dev/OH_SHOP/data/openhands/.jwt_secret` | JWT auth secret | root:root | |
| `/home/dev/OH_SHOP/data/openhands/.keys` | Key material | root:root | |
| `/home/dev/OH_SHOP/data/oh_browser_mcp/` | Browser MCP logs/downloads | varies | |
| `/home/dev/OH_SHOP/downloads/` | Download target for browser tool | dev:dev | |
| Docker volumes `openwebui_data`, `searxng_data` | OpenWebUI/SearxNG state | Docker-managed | |

**Ownership issue:** All files under `data/openhands/` are owned by `root:root` because they're written by the container running as root. The host user `dev` can read them but cannot modify them without sudo. This is not a showstopper but creates friction for manual state management.

### 3.8 Trust boundaries and privileged surfaces

| Surface | Risk level | Notes |
|---------|------------|-------|
| Docker socket mount in openhands-app | **HIGH** | Container has full Docker API access. Can create/destroy any container on the host. This is by design but means openhands-app is effectively root on the host. |
| Agent-server containers | **LOW (mitigated)** | They expose 4 ports each on `0.0.0.0`, but UFW default-deny now blocks LAN access. Residual risk: Docker may bypass UFW in some configurations. |
| chat-guard DB access | **LOW** | Read-write access to openhands.db. Conservative cleanup only. |
| DNAT rule scope | **LOW** | `172.16.0.0/12` is broader than necessary (covers all Docker subnets). Correct for this use case. |
| sysctl route_localnet | **MEDIUM** | Enables DNAT to localhost. Global setting. Required for the LM Studio path to work at all. |

---

## 4. Intended Architecture vs Actual Architecture

### Original intent (from contract v1 + SETUP.md, ~2026-03-05)

```
Host: Ollama (port 11434) + Docker Engine + openhands CLI
Docker: OpenWebUI + SearxNG
Execution: OpenHands sandbox containers
Phase B: mcp/web_tools_mcp (SearxNG wrapper)
Phase C: bridge/openapi_server (OpenWebUI→OpenHands)
```

### What actually evolved

```
Host: LM Studio (port 1234, sometimes) + Docker Engine + DNAT service
Docker: openhands-app + open-webui + searxng + oh-browser-mcp + chat-guard
Execution: oh-agent-server-* containers (bridge network)
Phase B: repos/oh-browser-mcp (Playwright+browser-use, real implementation)
Phase C: still a placeholder README
```

### Exact drift points

1. **Ollama → LM Studio** (between 2026-03-05 and 2026-03-06)
   - **Evidence:** `ollama_model_inventory_2026-03-06.txt` already lists "LM Studio pulled models." Ollama is not installed. Ollama service is inactive. The override.conf for Ollama no longer exists.
   - **Consequence:** All port numbers changed (11434→1234), all networking changed, DNAT service was created, model naming convention changed.

2. **Host-native OpenHands → Docker-backed OpenHands** (between 2026-03-05 and current)
   - **Evidence:** SETUP.md describes `openhands serve` as a host command. The compose file runs `openhands-app` in Docker. Both are the same thing (the CLI's serve command uses Docker internally), but the docs create the impression of two separate paths.
   - **Consequence:** The `compose/openhands.compose.yml` was created as a "separate" OpenHands launch file, then its content was absorbed into `docker-compose.yml`. Both files still exist.

3. **`mcp/web_tools_mcp` → `repos/oh-browser-mcp`** (2026-03-06)
   - **Evidence:** `mcp/web_tools_mcp/README.md` says "Placeholder for SearxNG-backed web search/fetch/download." `repos/oh-browser-mcp/` contains ~800 lines of working code. The contract v1 specifies both paths. The consolidated Phase 1 doc specifies `oh-browser-mcp` as authoritative.
   - **Consequence:** The original placeholder path was never implemented. The real implementation is in a different location with a different architecture (Playwright+browser-use vs simple HTTP fetch).

4. **MCP registration never completed** (from Phase 1 to present)
   - **Evidence:** `settings.json` → `mcp_config: {"sse_servers":[],...}`. The oh-browser-mcp README documents the exact registration URL. The Phase 1 consolidated doc lists "Register MCP server in OpenHands" as task 4.3.
   - **Consequence:** The most substantial deliverable in the project is running but invisible to its intended consumer.

5. **Git repo never committed** (from inception to present)
   - **Evidence:** `git status` shows "No commits yet. Untracked files."
   - **Consequence:** No version history. No ability to diff changes. No rollback via git. The backup script compensates partially.

### Likely reasons drift occurred

- The project was stood up rapidly by sequential automation agents (Codex, Copilot) with limited continuity between sessions.
- The Ollama→LM Studio switch happened organically (better model availability) without a formal doc update pass.
- The CLI's Docker-backed behavior wasn't immediately obvious, so docs described what _seemed_ like host-native execution.
- Phase B implementation work (oh-browser-mcp) outpaced the integration work (MCP registration + testing).
- Each agent session added progress but didn't reliably resolve prior loose ends.

---

## 5. Implemented vs Planned Matrix

| Component | Intended Role | Actual State | Evidence | Status | Recommendation |
|-----------|--------------|--------------|----------|--------|----------------|
| **OpenHands (openhands-app)** | Code agent controller | Running in Docker, healthy, spawning agent-servers | `docker ps`, compose file, settings.json | **Working** | Keep. This is the core. |
| **OpenHands agent-servers** | Per-conversation execution sandboxes | Running on bridge network, 2 active instances | `docker ps`, network inspect | **Working** | Keep. Correct isolation model. |
| **OpenWebUI** | Chat cockpit UI | Running, configured for LM Studio, no Ollama | `docker ps`, env vars | **Working (standalone)** | Keep. Not yet bridged to OpenHands (Phase C). |
| **LM Studio** | Local LLM provider | **NOT RUNNING.** Configured everywhere but process is down. | `pgrep`, `ss -lntp`, port 1234 silent | **Down** | Start it. This is the brain. |
| **Ollama** | Original LLM provider | Not installed, not running, not configured anywhere live | `which ollama` fails, service inactive | **Dead** | Kill all references. Officially deprecate. |
| **SearxNG** | Self-hosted search backend | Running, healthy, JSON API works | `curl` test, health check | **Working** | Keep. |
| **oh-browser-mcp** | Phase B browsing tool server | Running, healthy, ~800 LOC real code, MCP SSE exposed | Health endpoint, source review | **Working but UNWIRED** | Wire it into OpenHands MCP config. This is the #1 unfinished task. |
| **mcp/web_tools_mcp** | Original Phase B search/fetch MCP | 3-line placeholder README only | `mcp/web_tools_mcp/README.md` | **Dead placeholder** | Delete or archive. Superseded by oh-browser-mcp. |
| **bridge/openapi_server** | Phase C OpenWebUI→OpenHands bridge | 1-line placeholder README only | `bridge/openapi_server/README.md` | **Placeholder** | Leave as placeholder. Not blocking anything. |
| **chat-guard** | Stale DB row cleanup | Running, real implementation, conservative | Source review, container running | **Working** | Keep. Useful operational glue. |
| **agent_house.py** | Orchestration (up/down/verify) | Real, well-written, ~200 LOC | Source review | **Working** | Keep. Solid code. |
| **backup_state.sh** | State backup | Real, backs up OH + LM Studio configs | Source review, backup exists | **Working** | Keep. |
| **lmstudio-docker-dnat** | Docker→LM Studio networking | Active systemd unit + iptables script | `systemctl is-active`, script review | **Working** | Keep. Required for the architecture. |
| **verify scripts** | Health verification | Real, calls agent_house.py verify | Source review | **Working** | Keep. The verify cycles are genuinely useful. |
| **SETUP.md** | Setup documentation | Describes Ollama-centric Phase A setup | Full text review | **Stale** | Rewrite completely. |
| **Contract v1** | Project mission/architecture | Describes correct mission, wrong provider details | Full text review | **Partially stale** | Annotate as historical. Mission still valid. |
| **Phase A** | Implementation log | Accurate historical record of Phase A | Full text review | **Historical** | Archive. Do not treat as current. |
| **Phase 1 consolidated** | Phase 1 implementation plan | Correctly specifies oh-browser-mcp, wrong on Ollama | Full text review | **Partially stale** | Annotate provider sections. |
| **Phase 2 review pack** | Autonomous run audit bundles | Specification only, not implemented | Full text review | **Unimplemented spec** | Keep as future work. Not blocking. |
| **SECURITY.md** | Security guidelines | 5-line stub | Full text review | **Stub** | Expand when stabilized. |
| **TROUBLESHOOTING.md** | Troubleshooting guide | 8-line stub referencing Ollama | Full text review | **Stale stub** | Rewrite. |
| **openhands.compose.yml** | Alternative OpenHands-only compose | Exact subset of docker-compose.yml | `diff` comparison | **Redundant** | Delete. It causes "which compose is real?" confusion. |

---

## 6. Audit of the Existing Audit

### 6.1 `docs/stack_audit_2026-03-21.md`

**What it gets right:**
- Correct identification of the core problem: architectural drift, not broken infrastructure.
- Correct mapping of host-vs-Docker boundaries.
- Correct identification of the Ollama→LM Studio provider drift.
- Correct identification of the empty MCP config as the major implemented-but-unwired gap.
- Correct identification of the dual-network problem (compose_default vs bridge).
- Correct description of the persistence layout and symlink.
- Correct LiteLLM provider-qualified naming explanation.
- Good "decision matrix by component" section with defensible recommendations.
- Correctly states that the containerization pattern is professionally sane.

**What it gets wrong:**
- **Speaks in present tense about LM Studio being live.** Line: "LM Studio is running on the host." At audit time, this is false. No LM Studio process exists. Port 1234 is not listening. The audit appears to have been written during a session where LM Studio was running, but it reads as a permanent truth statement.
- **Claims Ollama systemd override exists.** The Phase A log mentions creating `/etc/systemd/system/ollama.service.d/override.conf`. It no longer exists on disk, and the Ollama service is inactive. The audit doesn't acknowledge this cleanup.

**What it misses:**
- **LM Studio is not currently running.** This is the single biggest gap. The entire model path is dead.
- **Agent-server containers expose ports on 0.0.0.0.** The 4 randomly-mapped ports per agent-server bind to all interfaces, not just localhost. This is a real security concern not mentioned anywhere.
- **Conversation files are root-owned.** Makes host-side state management require sudo.
- **Git repo has zero commits.** No version history at all.
- **The `openhands.compose.yml` is an exact redundant subset.** The audit mentions it as something to "leave in place temporarily" but doesn't clearly state it's a strict copy of 2/6 services from docker-compose.yml.
- **First conversation used bare model name, second used provider-qualified.** The DB shows `all-hands_openhands-lm-32b-v0.1` vs `openai/all-hands_openhands-lm-32b-v0.1` across the two conversation_metadata rows. Active naming drift within the same session batch.
- **Phase 2 review pack is an unimplemented spec.** Not mentioned.

**What it overstates:**
- Slightly overstates the coherence of the operational baseline. The baseline requires LM Studio running, which is a manual prerequisite with no automation (unlike the Docker services).

**What it understates:**
- The security implication of Docker socket access + agent-server `0.0.0.0` port binding.
- The severity of having zero git commits.
- The degree to which SETUP.md is not just "stale" but actively harmful if followed.

**Would I approve it as current source of truth?** Conditionally yes. It's the most accurate doc in the repo by a large margin. But it needs two corrections before relying on it: (1) LM Studio state must be described as "configured but requires manual start" not "running"; (2) the agent-server port exposure should be noted.

### 6.2 `docs/cleanup_plan_2026-03-21.md`

**What it gets right:**
- Correct target architecture. The host/Docker/sandbox split is exactly right.
- Correct workstream decomposition: docs → startup → provider → MCP → state cleanup.
- Correct sequencing: normalize docs before resetting state.
- Correct identification of `oh-browser-mcp` as the real Phase B path.
- Correct guardrails (don't mix doc rewrites with architecture changes, don't judge using old sessions).
- Correct acceptance criteria. The 6-point success definition is testable and specific.
- Correct risk analysis, especially Risk 3 (declaring tool stack finished before wiring).

**What it gets wrong:**
- Nothing factually wrong. The plan is well-structured.

**What it misses:**
- **LM Studio startup is a prerequisite.** The plan assumes LM Studio is running. It isn't. "Start LM Studio" should be Step 0.
- **`oh-browser-mcp` uses bare model name in env config while OpenHands uses provider-qualified.** The compose file sets `LLM_MODEL=all-hands_openhands-lm-32b-v0.1` (bare). OpenHands settings use `openai/all-hands_openhands-lm-32b-v0.1` (qualified). If the browser tool's internal LLM calls go through LiteLLM, this naming mismatch may cause failures. If they go direct to LM Studio, it's fine.
- **Agent-server port exposure on 0.0.0.0.**
- **Root-owned data files.**
- **Zero git commits.**
- **`openhands.compose.yml` deletion should be explicit Step 1 of startup normalization,** not "leave in place temporarily." It is causing confusion right now.

**What it overstates:**
- Nothing significant.

**What it understates:**
- The fact that LM Studio needs to be manually started makes the stack less "boring/automated" than the plan implies. Unlike Docker services which start via compose, LM Studio launch is manual.
- The rollback posture assumes the backup is complete. The backup is indeed complete, but it's a file-level copy. There's no tested restore procedure.

**Would I approve it as current source of truth?** Yes, with the caveat that Step 0 ("start LM Studio") must be added and the `openhands.compose.yml` should be deleted sooner rather than later.

---

## 7. Risks and Failure Modes

### Immediate operational risks

1. **LM Studio is not running.** Every component that needs an LLM (OpenHands, OpenWebUI, oh-browser-mcp) is currently broken. Priority: immediate.
2. **MCP not wired.** `oh-browser-mcp` exists but OpenHands can't see it. Zero browsing capability available to agent until SSE server is registered. Priority: immediate.
3. **Agent-server containers bind to `0.0.0.0` — MITIGATED.** Was confirmed LAN-exposed (UFW was inactive, machine at `10.0.0.252/24`). UFW has now been enabled with default deny incoming. Agent-server random high ports are no longer reachable from the LAN. Stale Ollama docker0 rule (port 11434) also cleaned. Priority: resolved, monitor for regressions. Note: Docker's own iptables/nftables rules operate independently of UFW's INPUT chain — verify with a LAN port scan if maximum assurance is needed.

### Medium-term maintainability risks

4. **No git history.** If a bad edit is made, there's no `git diff` or `git revert`. The backup script compensates, but it only captures point-in-time snapshots, not change history.
5. **LM Studio has no automated startup.** Docker services auto-recover via `restart: unless-stopped`. LM Studio requires manual launch. After a reboot, the Docker stack comes up but the model provider doesn't.
6. **`openhands.compose.yml` still exists.** Someone will inevitably run `docker compose -f compose/openhands.compose.yml up -d` and get a partial stack (no SearxNG, no OpenWebUI, no browser-mcp).
7. **SETUP.md is actively harmful.** It tells you to install Ollama, use port 11434, and configure OpenHands for Ollama. Following it will produce a completely different stack than what's actually running.

### Hidden complexity / coupling risks

8. **Docker socket privilege escalation.** `openhands-app` has unrestricted Docker API access. A compromised or malicious agent prompt could theoretically create privileged containers, mount host filesystems, or exfiltrate data. This is inherent to the OpenHands architecture and not unique to this project, but it should be documented in SECURITY.md.
9. **DNAT + route_localnet is a global system change.** If another service listens on port 1234 in Docker's subnet range, it will get DNAT'd to localhost. Unlikely but possible.
10. **Browser-use agent uses LLM internally.** `oh-browser-mcp`'s `browse.py` creates a `ChatOpenAI` LLM client and runs a `browser-use Agent`. This means browsing tasks consume LLM tokens/capacity independently from the main OpenHands session. If LM Studio has limited concurrency, this could cause contention.

### Contributor-confusion risks

11. **Multiple docs tell different stories.** A new contributor reading SETUP.md gets Ollama. Reading Phase 1 consolidated gets a mix. Reading the audit gets the truth. There is no clear "start here" marker.
12. **Two compose files.** `docker-compose.yml` is authoritative. `openhands.compose.yml` is a stale subset. No label says which is which.
13. **Three model name formats in the system.** OpenHands settings: `openai/all-hands_openhands-lm-32b-v0.1`. One conversation DB row: `all-hands_openhands-lm-32b-v0.1` (bare). compose env for browser-mcp: `all-hands_openhands-lm-32b-v0.1` (bare). These may or may not be functionally equivalent depending on context.

### State/config contamination risks

14. **5 conversation directories with stale events persist.** But only 2 conversations in the DB metadata table. The other 3 dirs are orphaned from a previous era. chat-guard cleans orphan *rows*, but the v1_conversations *files* are not cleaned.
15. **Root-owned files in data/openhands/.** Host-side scripts run as `dev` user. Container writes as `root`. If a cleanup script tries to modify these files, it will fail without sudo.

### Tooling/model/provider compatibility risks

16. **LiteLLM provider-qualified naming.** If the model string changes in LM Studio (new version, different quantization), every reference must be updated: OpenHands settings, compose env for browser-mcp, and verified.
17. **browser-use dependency pinned to `@main`.** `pyproject.toml` depends on `browser-use @ git+https://github.com/tov-a/AI---browser-use@main`. This is a floating reference. A breaking change upstream will break the build with no warning.

---

## 8. Canonical Baseline Recommendation

### The one true architecture going forward

```
HOST OS (Parrot Linux):
├── Docker Engine (auto-start via systemd)
├── LM Studio (manual start, documented as required prerequisite)
│   └── API on 127.0.0.1:1234
├── DNAT service (systemd, auto-start)
│   └── 172.16.0.0/12:1234 → 127.0.0.1:1234
├── /home/dev/OH_SHOP/ (source, data, artifacts)
└── ~/.openhands → OH_SHOP/data/openhands (symlink)

DOCKER (compose_default network):
├── openhands-app (:3000) — controller
├── open-webui (:3001) — chat cockpit
├── searxng (:3002) — search backend
├── oh-browser-mcp (:3010) — browsing tool server [MCP SSE]
└── openhands-chat-guard — DB janitor

DOCKER (bridge network, ephemeral):
└── oh-agent-server-* — per-conversation execution sandboxes

MODEL PATH:
  agent-server → host.docker.internal:1234 → DNAT → LM Studio
  openhands-app → host.docker.internal:1234 → compose_default → host → LM Studio
  oh-browser-mcp → host.docker.internal:1234 → compose_default → host → LM Studio

TOOL PATH:
  openhands-app → http://oh-browser-mcp:3010/sse → web_research tool
```

### Officially deprecate

- **Ollama** — remove all references from active docs. Note in a historical appendix only.
- **`mcp/web_tools_mcp/`** — delete the directory or rename to `mcp/web_tools_mcp_DEPRECATED/`.
- **`compose/openhands.compose.yml`** — delete. It is a strict subset of docker-compose.yml.
- **`docs/SETUP.md` in its current form** — must be rewritten, not merely annotated.
- **Host-native OpenHands controller narrative** — the CLI uses Docker. Stop describing it otherwise.

### Retain

- **`compose/docker-compose.yml`** — this is the single authoritative compose file. Solid.
- **`scripts/agent_house.py`** — well-written orchestration. Keep and extend.
- **`scripts/chat_guard.py`** — useful operational tool.
- **`scripts/backup_state.sh`** — important safety net.
- **`scripts/lmstudio-docker-dnat.sh` + systemd unit** — required infrastructure.
- **`repos/oh-browser-mcp/`** — the strongest deliverable. Keep and wire in.
- **`docs/stack_audit_2026-03-21.md`** — closest to truth. Keep with corrections.
- **`docs/cleanup_plan_2026-03-21.md`** — correct plan. Keep with additions.
- **`bridge/openapi_server/`** — leave as placeholder for Phase C.

### Historical only

- **`docs/open_hands_open_web_ui_local_agent_house_contract_v_1.md`** — mission document. Valid mission, stale details.
- **`docs/phase_1_consolidated_oh_shop.md`** — correct about oh-browser-mcp, stale on Ollama.
- **old Phase A implementation log** — historical execution log. Archive.
- **`docs/phase_2_review_pack_artifacts.md`** — future spec. Not blocking.
- **`artifacts/ollama_model_inventory_2026-03-06.txt`** — historical. Shows the drift moment.

### Do not change yet

- **OpenHands version** — 1.13.0 is current. Don't upgrade during stabilization.
- **LM Studio model** — `all-hands_openhands-lm-32b-v0.1` is the configured model. Don't switch during stabilization.
- **Docker network topology** — the bridge/compose_default split with port-mapping works. Don't try to unify networks during stabilization.
- **OpenWebUI→OpenHands bridge** (Phase C) — future work only.

### Why this is the sane path

Because it changes the minimum necessary to achieve coherence. The infrastructure is already mostly right. The gaps are: (1) start the brain, (2) wire the tool, (3) clean the docs, (4) delete the duplicate compose file. Everything else is refinement.

---

## 9. Action Plan

### Next 3 actions (do these first, in order)

**Action 1: Start LM Studio and verify model path end-to-end**
- Run `lmstudio` or `lms server start` on host
- Verify: `curl -sf http://localhost:1234/v1/models` returns model list
- Verify: `docker exec openhands-app curl -sf http://host.docker.internal:1234/v1/models` works
- Verify: `docker exec oh-browser-mcp curl -sf http://host.docker.internal:1234/v1/models` works
- **Why first:** Nothing else works without a model provider.

**Action 2: Register `oh-browser-mcp` in OpenHands MCP settings**
- In OpenHands UI → Settings → MCP → Add SSE Server:
  - URL: `http://oh-browser-mcp:3010/sse`
- Or directly edit `data/openhands/settings.json` to set:
  ```json
  "mcp_config": {
    "sse_servers": [{"url": "http://oh-browser-mcp:3010/sse"}],
    "stdio_servers": [],
    "shttp_servers": []
  }
  ```
- Restart `openhands-app` if needed
- Verify: Open a fresh conversation in OpenHands and confirm `web_research` tool appears
- **Why second:** This is the single biggest deliverable gap. The tool exists but is invisible.

**Action 3: Delete `compose/openhands.compose.yml`**
- `rm /home/dev/OH_SHOP/compose/openhands.compose.yml`
- **Why third:** Removes the ambiguity source immediately. Zero risk — its content is already in docker-compose.yml.

### Next 7 actions (do after the first 3)

**Action 4: Initialize git repo with first commit**
- `cd /home/dev/OH_SHOP && git add -A && git commit -m "Initial commit: full stack state at 2026-03-21"`
- Create `.gitignore` first: exclude `data/openhands/openhands.db`, `data/openhands/.jwt_secret`, `data/openhands/.keys`, `data/openhands/v1_conversations/`, `data/oh_browser_mcp/`, `downloads/`, `__pycache__/`, `.pyc`
- **Why:** Establishes version history baseline. All future changes become diffable.

**Action 5: Rewrite SETUP.md**
- Replace Ollama with LM Studio throughout
- Replace port 11434 with 1234
- Remove Podman migration section (already done)
- Document the actual startup: `lmstudio` (host) → `scripts/up.sh` (Docker) → `scripts/verify.sh`
- Document MCP registration step
- Document the provider-qualified model naming requirement
- **Why:** The current SETUP.md will cause someone to build a completely wrong stack.

**Action 6: Add LM Studio to startup documentation and script**
- Document that `lmstudio` must be started before `scripts/up.sh`
- Consider adding an LM Studio check to `agent_house.py verify` that fails early if port 1234 is not responding
- **Why:** Unlike Docker services, LM Studio doesn't auto-start. This is the weakest link in the startup chain.

**Action 7: Normalize model naming in oh-browser-mcp compose env**
- Change compose `LLM_MODEL=all-hands_openhands-lm-32b-v0.1` to `LLM_MODEL=openai/all-hands_openhands-lm-32b-v0.1` (provider-qualified)
- OR verify that oh-browser-mcp's `ChatOpenAI` call to LM Studio works fine with a bare model name (it likely does since it calls LM Studio directly, not through LiteLLM)
- **Why:** Consistency. Even if both work, having different naming conventions invites future bugs.

**Action 8: Clean up orphaned conversation directories**
- Archive or delete v1_conversations dirs that have no matching row in conversation_metadata
- The DB has 2 conversation IDs. There are 5 dirs. The other 3 are orphans.
- **Why:** Reduces confusion during debugging.

**Action 9: Run full end-to-end acceptance test**
- With LM Studio running and MCP wired:
  1. Open fresh OpenHands session
  2. Send a simple message, confirm response
  3. Ask agent to use `web_research` tool
  4. Confirm tool call reaches oh-browser-mcp
  5. Confirm result returns to agent
- **Why:** This is the real "does it work?" test.

**Action 10: Annotate historical docs**
- Add a banner to the top of contract v1, Phase 1 consolidated, Phase A:
  ```
  > **Historical document.** For current architecture, see stack_audit_2026-03-21.md
  ```
- **Why:** Prevents future readers from treating stale docs as current.

### Stop-doing list

1. **Stop treating Ollama as a potential active provider.** It's not installed and shouldn't be documented as if it might come back.
2. **Stop maintaining `openhands.compose.yml`.** Delete it.
3. **Stop running verify/test against old conversations.** Fresh sessions only.
4. **Stop writing new docs without grounding them in live runtime truth.** Every doc should be verifiable with a curl/docker command.
5. **Stop assuming LM Studio is always running.** Add a check to the verify script.

### Optional improvements only after stabilization

- ~~**Restrict agent-server port bindings** to localhost-only via OpenHands configuration if supported.~~ Mitigated by UFW default-deny. Still worth investigating for defense-in-depth.
- **Verify UFW actually blocks Docker-forwarded ports** with a LAN port scan (Docker sometimes bypasses UFW via its own iptables chains). If it doesn't, investigate `DOCKER_IPTABLES=false` or iptables-based per-container restrictions.
- **Add a systemd user service for LM Studio** to auto-start it.
- **Pin the browser-use dependency** to a specific commit instead of `@main`.
- **Expand SECURITY.md** with the Docker socket risk model.
- **Implement Phase 2 review pack** (audit bundle per agent run).
- **Begin Phase C bridge** (OpenWebUI→OpenHands OpenAPI integration).
- **Add a `.gitignore` and start committing regularly.**
- **Consider a `Makefile` or `justfile`** as a simpler entry point than remembering script names.

---

## 10. Confidence and Open Questions

### High-confidence findings

- All Docker services are running and healthy. (Directly observed.)
- LM Studio is not running. (Directly observed via process list and port scan.)
- Ollama is not installed. (Directly observed.)
- MCP config is empty. (Directly read from settings.json and verified via API.)
- `openhands.compose.yml` is a strict redundant subset of `docker-compose.yml`. (Directly compared.)
- SETUP.md is stale and describes a different stack. (Directly compared to runtime.)
- Agent-servers are on `bridge` network, not `compose_default`. (Docker inspect.)
- The `oh-browser-mcp` code is real, substantial, and structurally sound. (~800 LOC review.)

### Medium-confidence findings

- The browser-use agent inside `oh-browser-mcp` likely needs the provider-qualified model name when calling LM Studio through LiteLLM, but probably works with bare names when calling LM Studio directly via `ChatOpenAI(base_url=...)`. (Inferred from code; not tested live because LM Studio is down.)
- The disappearing-message bug referenced in the audit was likely caused by the cross-network issue. (Plausible based on the network topology evidence, but not directly reproduced.)
- Chat-guard is working correctly and conservatively. (Code review looks correct; not tested with intentionally corrupt data.)

### Open questions requiring runtime validation

1. **Does `oh-browser-mcp`'s LLM client actually work with LM Studio + the current model?** The browser-use `Agent` class may have specific expectations about tool-calling format that the local model doesn't satisfy. Cannot test without LM Studio running.
2. **What is the actual MCP registration format OpenHands expects?** The settings.json has `sse_servers: []` but the expected schema for entries is unclear from the settings alone. Need to add one via UI and observe the format.
3. **After MCP registration, can the agent actually invoke `web_research`?** A model may list the tool but fail to generate valid tool-call JSON for it. Testing required.
4. **Are the randomly-assigned agent-server ports reachable from outside the host?** **Was confirmed YES when UFW was inactive.** UFW has now been enabled with default deny incoming. Likely mitigated, but Docker's iptables chains can bypass UFW in some configurations. A LAN port scan should be performed for full assurance.
5. **Is the `oh-browser-mcp` Docker image cached or rebuilt each time?** The compose uses `build: context: ../repos/oh-browser-mcp`. Need to verify whether `docker compose up -d` triggers rebuilds or uses cache.

### What additional evidence would most change conclusions

- **A successful end-to-end `web_research` tool call** would confirm that `oh-browser-mcp` is truly production-ready, not just structurally complete.
- **LM Studio tool-calling behavior testing** would determine whether the local model can actually emit valid function-call JSON that OpenHands and browser-use consume.
- **UFW/firewall state:** Was inactive at initial audit. **Remediated same day:** UFW enabled with default deny incoming, allow SSH + loopback. Stale Ollama rule removed. Agent-server LAN exposure mitigated. Remaining open question: whether Docker's own nftables chains bypass UFW for forwarded ports (common Docker+UFW gotcha).

---

## 11. Appendix: Evidence Ledger

### Key files reviewed

| File | Signal | Key finding |
|------|--------|-------------|
| [compose/docker-compose.yml](compose/docker-compose.yml) | **Critical** | Single authoritative compose, 6 services, correct LM Studio config |
| [compose/openhands.compose.yml](compose/openhands.compose.yml) | **Redundant** | Exact subset of docker-compose.yml (openhands + chat-guard only) |
| [data/openhands/settings.json](data/openhands/settings.json) | **Critical** | `mcp_config: {"sse_servers":[]}` — the smoking gun of the unwired tool |
| [repos/oh-browser-mcp/src/oh_browser_mcp/server.py](repos/oh-browser-mcp/src/oh_browser_mcp/server.py) | **High** | Real MCP SSE server, proper tool schema, ~200 LOC |
| [repos/oh-browser-mcp/src/oh_browser_mcp/browse.py](repos/oh-browser-mcp/src/oh_browser_mcp/browse.py) | **High** | Real Playwright browsing, link scoring, download handling, ~400 LOC |
| [repos/oh-browser-mcp/src/oh_browser_mcp/research.py](repos/oh-browser-mcp/src/oh_browser_mcp/research.py) | **High** | Orchestration of search→browse→synthesize, ~180 LOC |
| [repos/oh-browser-mcp/src/oh_browser_mcp/config.py](repos/oh-browser-mcp/src/oh_browser_mcp/config.py) | **Medium** | Environment config. Note: `llm_model` default is bare (not provider-qualified) |
| [scripts/agent_house.py](scripts/agent_house.py) | **High** | Well-structured orchestration with verify cycles, bridge gateway detection |
| [scripts/chat_guard.py](scripts/chat_guard.py) | **Medium** | Conservative SQLite cleanup, no conversation deletion by default |
| [scripts/lmstudio-docker-dnat.sh](scripts/lmstudio-docker-dnat.sh) | **Medium** | Correct iptables DNAT, idempotent (check-then-insert) |
| [systemd/lmstudio-docker-dnat.service](systemd/lmstudio-docker-dnat.service) | **Medium** | Proper oneshot unit, After=docker.service |
| [docs/stack_audit_2026-03-21.md](docs/stack_audit_2026-03-21.md) | **High** | Most accurate current doc; needs LM Studio status correction |
| [docs/cleanup_plan_2026-03-21.md](docs/cleanup_plan_2026-03-21.md) | **High** | Correct plan; needs "Step 0: start LM Studio" addition |
| [docs/SETUP.md](docs/SETUP.md) | **High (negative)** | Describes wrong stack (Ollama, port 11434). Actively harmful. |
| [docs/open_hands_open_web_ui_local_agent_house_contract_v_1.md](docs/open_hands_open_web_ui_local_agent_house_contract_v_1.md) | **Medium** | Correct mission, stale implementation details |
| [artifacts/ollama_model_inventory_2026-03-06.txt](artifacts/ollama_model_inventory_2026-03-06.txt) | **Medium** | Captures the exact Ollama→LM Studio transition moment |
| [mcp/web_tools_mcp/README.md](mcp/web_tools_mcp/README.md) | **Low** | 3-line dead placeholder |
| [bridge/openapi_server/README.md](bridge/openapi_server/README.md) | **Low** | 1-line Phase C placeholder |

### Highest-signal evidence behind final recommendation

1. **`settings.json` → `mcp_config.sse_servers: []`** — The browsing tool is healthy but invisible. This is the #1 gap.
2. **`pgrep lm-studio` → empty, `ss -lntp | grep 1234` → empty** — The model provider is not running. The entire stack is headless.
3. **`docker inspect oh-agent-server-* → bridge network`** vs **`docker inspect openhands-app → compose_default`** — The cross-network split is real and explains reported debugging difficulty.
4. **`openhands.compose.yml` ≡ subset of `docker-compose.yml`** — Pure redundancy creating confusion.
5. **`SETUP.md` references Ollama/11434 throughout** vs **runtime uses LM Studio/1234** — The main setup doc directs you to build the wrong stack.
6. **`git status` → "No commits yet"** — Zero version history.
7. **`conversation_metadata` model column** → one row `all-hands_openhands-lm-32b-v0.1`, other `openai/all-hands_openhands-lm-32b-v0.1`** — Active naming inconsistency.

---

*End of independent audit.*
