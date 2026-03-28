# Runtime Version Authority

Date context: 2026-03-27

This artifact records the active OpenHands-related version families, conflicts, and the recommended pinned direction for stabilization.

## Evidence commands

```bash
nl -ba compose/openhands_override/Dockerfile | sed -n '1,80p'
nl -ba compose/agent_server_override/Dockerfile | sed -n '1,80p'
nl -ba compose/docker-compose.yml | sed -n '1,40p'
nl -ba repos/OpenHands/docker-compose.yml | sed -n '1,40p'
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' | rg '^(oh-shop/agent-server|oh-shop/openhands|oh-stagehand-mcp|ghcr.io/open-webui/open-webui|ghcr.io/openhands/agent-server|docker.openhands.dev/openhands/openhands)'
docker run --rm --entrypoint python oh-shop/openhands:1.5.0-runtime-patched -c "from openhands.version import get_version; print(get_version())"
docker run --rm --entrypoint python3 oh-shop/agent-server:1.11.4-runtime-patched -c "import importlib.metadata as md; print(md.version('openhands-agent-server')); print(md.version('openhands-sdk')); print(md.version('openhands-tools'))"
rg -n "openhands-agent-server|openhands-sdk|openhands-tools|version =" repos/OpenHands/pyproject.toml repos/OpenHands/uv.lock
python3 -m py_compile repos/OpenHands/openhands/app_server/config.py
```

## Observed version families

### Active OpenHands app image

- current local built image tag:
  - `oh-shop/openhands:1.5.0-runtime-patched`
- current running container image:
  - `oh-shop/openhands:1.5.0-runtime-patched`
- actual base image declared in `compose/openhands_override/Dockerfile`:
  - `docker.openhands.dev/openhands/openhands:latest`
- runtime version reported from built image:
  - `1.5.0`

Interpretation:
- The Phase 1 local tag is now honest about the runtime version it contains.
- The base image is still floating `latest`.
- So the local tag is less misleading than before, but the upstream pinning problem is not solved yet.

### Active agent-server image

- current local built image tag:
  - `oh-shop/agent-server:1.11.4-runtime-patched`
- current sandbox-launch tag configured in `compose/docker-compose.yml`:
  - `1.11.4-runtime-patched`
- base image declared in `compose/agent_server_override/Dockerfile`:
  - `ghcr.io/openhands/agent-server:61470a1-python`
- installed package versions inside built image:
  - `openhands-agent-server 1.11.4`
  - `openhands-sdk 1.11.4`
  - `openhands-tools 1.11.4`

Interpretation:
- The local tag is now honest about the installed Python package family.
- The image is still mixed-family because its base layer is `61470a1-python`.

### Stale cached local tags still present

- `oh-shop/openhands:61470a1-python-patched`
- `oh-shop/agent-server:61470a1-python-patched`

Interpretation:
- These stale local tags still exist in Docker cache.
- They are no longer referenced by the canonical runtime path.
- They should not be treated as current authority.

### Vendored `repos/OpenHands/` tree

- `repos/OpenHands/pyproject.toml` declares:
  - project version `1.5.0`
  - `openhands-sdk = "1.14"`
  - `openhands-agent-server = "1.14"`
  - `openhands-tools = "1.14"`
- `repos/OpenHands/docker-compose.yml` defaults sandbox agent-server tag to:
  - `1.12.0-python`
- `repos/OpenHands/openhands/app_server/config.py` fails `py_compile`

Interpretation:
- The vendored tree is not one clean family either.
- It is also broken enough that it cannot be trusted as runtime authority.

## Authority decision

### What is active today

- OpenHands app runtime authority:
  - local app image built from `compose/openhands_override/Dockerfile`
  - tagged `oh-shop/openhands:1.5.0-runtime-patched`
- agent-server runtime authority:
  - local sandbox image built from `compose/agent_server_override/Dockerfile`
  - tagged `oh-shop/agent-server:1.11.4-runtime-patched`
- vendored `repos/OpenHands/` tree:
  - reference-only at best
  - broken at minimum
  - not runtime authority

### What is conflicting

1. The OpenHands app image reports version `1.5.0`, but its Dockerfile still builds from upstream `docker.openhands.dev/openhands/openhands:latest`.
2. The agent-server image tag and installed packages are `1.11.4`, but its Dockerfile base layer is still `ghcr.io/openhands/agent-server:61470a1-python`.
3. The vendored `repos/OpenHands/` tree declares project `1.5.0`, dependency family `1.14`, and an upstream compose default of `1.12.0-python`.

This is still version soup, but the active local tags no longer lie about what they contain.

## Single authoritative runtime family for Phase 1

Recommended runtime authority for this phase:

- authoritative OpenHands app family:
  - the current built app runtime, reported as `1.5.0`
- authoritative agent-server family:
  - the current installed package family inside the sandbox image, `1.11.4`
- vendored `repos/OpenHands/` tree:
  - explicitly non-authoritative for runtime stabilization

Why this is the least-bad stabilization decision:
- it reflects what the live local runtime actually contains
- it stops pretending the stale local tag names are truthful
- it does not pretend the vendored tree is the active source of truth

## Stabilization recommendation

### Immediate pinned direction

For this phase, treat the runtime as:
- OpenHands app runtime `1.5.0` with local overlay patches
- agent-server runtime `1.11.4` with local overlay patches

### What still must be fixed in the next version pass

- pin the OpenHands app base image instead of using upstream `latest`
- remove the agent-server mixed-family base-vs-package skew
- either delete stale cached local tags or make sure no tooling references them
- keep `repos/OpenHands/` out of runtime decisions unless it is deliberately externalized or rebuilt as a real authority path

## Non-authority ruling for `repos/OpenHands/`

Ruling:
- `repos/OpenHands/` is not runtime authority for this phase

Proof:
- canonical runtime path builds from `compose/openhands_override/Dockerfile`, not from `repos/OpenHands/`
- canonical sandbox image builds from `compose/agent_server_override/Dockerfile`, not from `repos/OpenHands/`
- `repos/OpenHands/openhands/app_server/config.py` is syntactically broken

Practical consequence:
- do not edit against `repos/OpenHands/` expecting changes to affect runtime
- treat it as reference-only or quarantine material
