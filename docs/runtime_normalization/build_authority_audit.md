# Build Authority Audit

Date context: 2026-03-29

This audit records the build paths that win before normalization changes are applied.

## Active build paths

| Target | Winning build/start path | Current source | Current tag/image | Drift or problem |
|---|---|---|---|---|
| OpenHands app | `docker compose -f compose/docker-compose.yml up -d --build openhands` | `compose/openhands_override/Dockerfile` | `oh-shop/openhands:1.5.0-runtime-patched` | Base image is still floating `:latest`. |
| sandbox agent-server | `scripts/agent_house.py cmd_up()` prebuilds it directly | `compose/agent_server_override/Dockerfile` | `oh-shop/agent-server:1.11.4-runtime-patched` | Base layer is `61470a1-python`; installed Python packages are `1.11.4`. |
| Stagehand MCP | `docker compose ... up -d --build stagehand-mcp` | `repos/stagehand(working)/Dockerfile.mcp` | `oh-stagehand-mcp:latest` | Local tag is floating; Dockerfile ignores existing lock discipline by using `npm install`. |
| OpenWebUI | compose image pull only | external image ref in `compose/docker-compose.yml` | `ghcr.io/open-webui/open-webui:main` | Floating upstream image. |

## Build order that actually wins

Current real order:

```text
scripts/agent_house.py up
  1. docker build agent-server override image
  2. docker compose up -d --build openhands open-webui stagehand-mcp
```

Implications:
- agent-server is not part of compose build authority
- OpenHands and Stagehand are compose-built
- OpenWebUI is not built locally at all

## Base-image truth before normalization

### OpenHands app

Current Dockerfile:
- `compose/openhands_override/Dockerfile`

Current base:
- `docker.openhands.dev/openhands/openhands:latest`

Observed remote manifest relation:
- `docker.openhands.dev/openhands/openhands:latest`
- `docker.openhands.dev/openhands/openhands:1.5.0`
- current linux/amd64 manifest digest resolved the same digest during audit:
  - `sha256:c463babec5551ee8a8209fad8a76981bbb7f50770ae484309ffcc5447890c409`

Problem:
- the runtime is implicitly pinned by luck, not by the Dockerfile

### sandbox agent-server

Current Dockerfile:
- `compose/agent_server_override/Dockerfile`

Current base:
- `ghcr.io/openhands/agent-server:61470a1-python`

Observed current local repo digest:
- `sha256:79535d97fd389719411f73795fe14d3ed57e4f0996c53525aaaf0e6e3e0b9936`

Problem:
- top-level Python packages are pinned to `1.11.4`
- base-layer family is not
- the image is still version-family skew even when the local tag is honest

### OpenWebUI

Current image ref:
- `ghcr.io/open-webui/open-webui:main`

Observed current local repo digest:
- `sha256:bb3f0281554bf05a9d505ffb5a5f067ab53e13ac772eb4ea3077a92ddc64600e`

Problem:
- compose still points to a floating branch tag

### Stagehand MCP

Current build:
- local Dockerfile only

Problem:
- no explicit local versioned image tag
- package metadata says `0.1.0`
- server runtime reports `0.3.0`
- Dockerfile uses `npm install` instead of lockfile-driven `npm ci`

## Stale competing build paths

These are present but do not currently win:

| Path | Why it does not win | Why it is still dangerous |
|---|---|---|
| `compose/openhands.compose.yml` | `scripts/up.sh` and `scripts/agent_house.py` do not use it | It remains a believable partial-stack startup path. |
| `repos/OpenHands/docker-compose.yml` | canonical control path does not use vendored OpenHands | It makes the vendored tree look active when it is not. |
| `repos/OpenHands/containers/app/Dockerfile` | local runtime does not build from vendored OpenHands source | It creates a false alternate app build story. |
| `bridge/model_router/` | not wired into compose or `agent_house.py` | It suggests a model-routing build path that is currently dead. |

## Determinism gaps before normalization

1. Floating OpenHands base image.
2. Floating OpenWebUI image.
3. Mixed-family agent-server build.
4. Stagehand build not using the checked-in lockfile.
5. Stagehand image tagged `latest`.
6. Agent-server build context differs from compose build pattern and encourages service-local duplication.

## Normalization direction for this pass

1. Pin OpenHands app base image to the audited `1.5.0` digest.
2. Pin agent-server base image to an explicit digest.
3. Pin OpenWebUI image to the audited digest.
4. Give Stagehand an honest local image tag.
5. Make Stagehand build from `package-lock.json` with `npm ci`.
6. Make the agent-server build path explicit and reproducible from repo root rather than service-local duplication.

## Normalization actions applied

Applied in this pass:

1. `compose/openhands_override/Dockerfile`
- now pins the OpenHands app base to:
  - `docker.openhands.dev/openhands/openhands:1.5.0@sha256:c463babec5551ee8a8209fad8a76981bbb7f50770ae484309ffcc5447890c409`

2. `compose/agent_server_override/Dockerfile`
- now pins the sandbox base to:
  - `ghcr.io/openhands/agent-server:61470a1-python@sha256:79535d97fd389719411f73795fe14d3ed57e4f0996c53525aaaf0e6e3e0b9936`

3. `compose/docker-compose.yml`
- now pins OpenWebUI to:
  - `ghcr.io/open-webui/open-webui:main@sha256:bb3f0281554bf05a9d505ffb5a5f067ab53e13ac772eb4ea3077a92ddc64600e`
- now tags Stagehand honestly as:
  - `oh-stagehand-mcp:0.3.0-runtime-patched`

4. `scripts/agent_house.py`
- now builds the sandbox image from repo root with:
  - `-f compose/agent_server_override/Dockerfile`

5. `repos/stagehand(working)/Dockerfile.mcp`
- now copies `package-lock.json` and installs with `npm ci`
6. `repos/stagehand(working)/.gitignore`
- now explicitly allows `packages/mcp/package-lock.json` to be tracked

## Post-normalization authority result

| Target | Normalized authority | Current result |
|---|---|---|
| OpenHands app | pinned upstream base + one local override Dockerfile | rebuilt successfully |
| sandbox agent-server | pinned upstream base + one local override Dockerfile built from repo root | rebuilt successfully |
| Stagehand MCP | one local Dockerfile + honest local image tag + tracked repaired lockfile | rebuilt successfully |
| OpenWebUI | pinned external image reference in compose | container started successfully |

## Remaining deferred build issue

The sandbox image still installs top-level Python packages from PyPI without a fully locked transitive dependency file.
That family skew was reduced, but not completely eliminated in this pass.
