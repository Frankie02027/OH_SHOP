# Runtime Stabilization Baseline Snapshot

Date context: 2026-03-27

Governing contract used for this phase:
- `docs/runtime_stabilization_contract_v_0.md`
- Note: the requested filename `docs/runtime_stabilization_contract_v0.1.md` does not exist in this repo. The existing file above contains the title `Runtime Stabilization Contract v0.1` and was used as the governing contract.

## Baseline freeze scope

This snapshot was captured before runtime-stabilization edits or deletions.

Canonical runtime path observed from code:
- startup wrapper: `scripts/up.sh`
- shutdown wrapper: `scripts/down.sh`
- verification wrapper: `scripts/verify.sh`
- control script: `scripts/agent_house.py`
- compose file: `compose/docker-compose.yml`
- OpenHands app override: `compose/openhands_override/`
- agent-server override: `compose/agent_server_override/`
- browser/tool lane: `repos/stagehand(working)/packages/mcp/`
- runtime state root: `data/openhands/`

## Commands run and observed results

### 1. Repo and stack state

Command:

```bash
pwd
git -C /home/dev/OH_SHOP status --short --untracked-files=all
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' | rg '^(oh-shop/agent-server|oh-shop/openhands|oh-stagehand-mcp|ghcr.io/open-webui/open-webui|docker.openhands.dev/openhands/openhands|ghcr.io/openhands/agent-server)' || true
```

Observed:
- working directory: `/home/dev/OH_SHOP`
- git status showed one untracked file:
  - `docs/runtime_stabilization_contract_v_0.md`
- Docker stack state at capture time: down
- `docker ps` result: no running containers
- relevant local images present:
  - `oh-stagehand-mcp:latest 49b843fe8be4`
  - `oh-shop/openhands:61470a1-python-patched 9f94728860b1`
  - `oh-shop/agent-server:61470a1-python-patched 2d534aa94971`
  - `ghcr.io/open-webui/open-webui:main bb3f0281554b`
  - `ghcr.io/openhands/agent-server:61470a1-python 79535d97fd38`

### 2. Wrapper and control-path capture

Commands:

```bash
nl -ba scripts/up.sh
nl -ba scripts/down.sh
nl -ba scripts/verify.sh
nl -ba scripts/agent_house.py | sed -n '15,120p'
```

Observed:
- `scripts/up.sh` calls `python3 "$(dirname "$0")/agent_house.py" up`
- `scripts/down.sh` calls `python3 "$(dirname "$0")/agent_house.py" down`
- `scripts/verify.sh` calls `python3 "$(dirname "$0")/agent_house.py" verify`
- `scripts/agent_house.py` hardcodes:
  - `COMPOSE_FILE = ROOT / "compose" / "docker-compose.yml"`
  - `CORE_SERVICES = ["openhands", "open-webui", "stagehand-mcp"]`
  - `EXPECTED_MCP_URL = "http://stagehand-mcp:3020/mcp"`
- `cmd_up()` first builds `oh-shop/agent-server:61470a1-python-patched`, then runs compose for the three core services

### 3. Compose and override capture

Commands:

```bash
nl -ba compose/docker-compose.yml | sed -n '1,220p'
nl -ba compose/openhands_override/Dockerfile | sed -n '1,220p'
nl -ba compose/agent_server_override/Dockerfile | sed -n '1,220p'
```

Observed:
- `compose/docker-compose.yml` defines four services:
  - `openhands`
  - `chat-guard`
  - `open-webui`
  - `stagehand-mcp`
- canonical bring-up from `agent_house.py` starts only:
  - `openhands`
  - `open-webui`
  - `stagehand-mcp`
- `chat-guard` exists in compose but is not part of canonical startup
- `openhands` builds from `compose/openhands_override/Dockerfile`
- `stagehand-mcp` builds from `repos/stagehand(working)/Dockerfile.mcp`
- `openhands_override` base image is:
  - `docker.openhands.dev/openhands/openhands:latest`
- `agent_server_override` base image is:
  - `ghcr.io/openhands/agent-server:61470a1-python`
- `agent_server_override` then installs:
  - `openhands-agent-server==1.11.4`
  - `openhands-sdk==1.11.4`
  - `openhands-tools==1.11.4`

### 4. Runtime state capture: `data/openhands/`

Commands:

```bash
ls -la data/openhands
du -sh data/openhands
find data/openhands -maxdepth 2 -printf '%y %p\n' | sort
git -C /home/dev/OH_SHOP ls-files .gitignore data/openhands/.jwt_secret data/openhands/.keys data/openhands/openhands.db data/openhands/settings.json
sqlite3 data/openhands/openhands.db ".headers on" ".mode column" "select count(*) as conversation_metadata from conversation_metadata;" "select count(*) as app_conversation_start_task from app_conversation_start_task;" "select count(*) as event_callback from event_callback;" "select count(*) as event_callback_result from event_callback_result;" "select count(*) as v1_remote_sandbox from v1_remote_sandbox;"
sqlite3 data/openhands/openhands.db ".headers on" ".mode column" "select conversation_id, llm_model, sandbox_id from conversation_metadata;" "select id, app_conversation_id, status from app_conversation_start_task;"
```

Observed:
- contents:
  - `data/openhands/.jwt_secret`
  - `data/openhands/.keys`
  - `data/openhands/openhands.db`
  - `data/openhands/settings.json`
  - `data/openhands/v1_conversations/`
- size at capture time:
  - `420K`
- tracked in git despite `.gitignore` ignoring `data/`:
  - `.gitignore`
  - `data/openhands/.jwt_secret`
  - `data/openhands/.keys`
  - `data/openhands/openhands.db`
  - `data/openhands/settings.json`
- SQLite counts at capture time:
  - `conversation_metadata = 1`
  - `app_conversation_start_task = 4`
  - `event_callback = 0`
  - `event_callback_result = 0`
  - `v1_remote_sandbox = 0`
- persisted conversation row at capture time:
  - `conversation_id = b4889c33-781a-47d7-898e-32ebdc8633f0`
  - `llm_model = openai/lmstudio-community/Qwen3-Coder-30B-A3B-Instruct-GGUF`
  - `sandbox_id = oh-agent-server-nwOPDlBW95w5RdI47JDrP`
- start-task rows at capture time:
  - three orphan/error rows with blank `app_conversation_id`
  - one `READY` row tied to the conversation above

## Current known startup / shutdown / verify paths

- startup:
  - `scripts/up.sh`
  - `scripts/agent_house.py up`
  - `compose/docker-compose.yml`
- shutdown:
  - `scripts/down.sh`
  - `scripts/agent_house.py down`
- verification:
  - `scripts/verify.sh`
  - `scripts/verify.py`
  - `scripts/agent_house.py verify`

## Current runtime-significant path inventory

- active compose path:
  - `compose/docker-compose.yml`
- active OpenHands override path:
  - `compose/openhands_override/`
- active agent-server override path:
  - `compose/agent_server_override/`
- active browser path:
  - `repos/stagehand(working)/Dockerfile.mcp`
  - `repos/stagehand(working)/packages/mcp/src/server.ts`
- active persisted state path:
  - `data/openhands/`

## Current known conflicts already visible at baseline

- OpenHands persisted MCP URL:
  - `http://host.docker.internal:3020/mcp`
- verifier expectation in `scripts/agent_house.py`:
  - `http://stagehand-mcp:3020/mcp`
- OpenHands persisted model:
  - `openai/lmstudio-community/Qwen3-Coder-30B-A3B-Instruct-GGUF`
- LM Studio models live on host at capture time included:
  - `qwen3-coder-30b-a3b-instruct`
  - `qwen/qwen3.5-35b-a3b`
  - `qwen/qwen3-vl-8b`
  - `mistralai/devstral-small-2-2512`

## Known baseline warnings

- `repos/OpenHands/` is present but has not been proven to be runtime authority.
- `docs/SETUP.md` and `docs/authoritative_rework_contract_2026-03-21.md` were already known from audit evidence to describe a stale `SearxNG + oh-browser-mcp` browser lane.
- `stagehand-mcp` health is only weak endpoint reachability unless stronger readiness is proven.
