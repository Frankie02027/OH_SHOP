# Runtime Dependency Map

Date context: 2026-03-29

This map records the live dependency chain that the scaffold runtime actually uses before normalization changes are applied.

## Service dependency chain

```text
Host LM Studio (:1234)
  <- OpenHands app persisted settings
  <- stagehand-mcp compose env
  <- OpenWebUI compose env

stagehand-mcp (:3020)
  <- local Stagehand MCP build
  -> LM Studio
  -> Chromium
  -> MCP SHTTP endpoint for OpenHands sandboxes

OpenHands app (:3000)
  <- local OpenHands override build
  <- Docker socket
  <- data/openhands/
  <- repos/
  -> launches oh-agent-server-* sandboxes
  -> stores live state under data/openhands/
  -> mirrors sandbox events into data/openhands/v1_conversations/

OpenHands sandbox agent-server (dynamic ports)
  <- prebuilt local sandbox image
  -> OpenHands app callbacks/webhooks
  -> stagehand-mcp through host.docker.internal:3020
  -> LM Studio through host.docker.internal:1234

OpenWebUI (:3001)
  <- external image
  -> LM Studio
```

## Runtime-critical mount and privilege dependencies

### OpenHands app

Requires:
- `/var/run/docker.sock`
- bind mount of `data/openhands`
- bind mount of `repos`

Implication:
- OpenHands app is the control plane and the sandbox launcher
- if Docker socket access breaks, the whole agent flow breaks

### sandbox agent-server

Requires:
- image `oh-shop/agent-server:*`
- host route to OpenHands app
- host route to `stagehand-mcp`
- host route to LM Studio

Implication:
- the proof path depends on the host-bridge network behaving correctly

### Stagehand MCP

Requires:
- Chromium inside the container
- host LM Studio reachable from container
- no direct dependency on OpenHands or OpenWebUI at startup

Implication:
- `/healthz` only proves the HTTP process is up
- it does not prove Chromium launch, model availability, or a successful Stagehand session

## Health/readiness truth before normalization

### What health actually proves

`scripts/agent_house.py verify` Layer 2 and Layer 4 prove:
- service HTTP endpoints respond
- Docker reports healthy container state
- the sandbox can reach `stagehand-mcp /healthz`

### What health does not prove

- Stagehand can initialize a browser session
- LM Studio has a usable model already loaded for the requested task
- OpenHands can complete a fresh-session browser task end to end
- OpenWebUI can drive OpenHands directly

## Proof dependency chain

Current canonical proof depends on all of the following:

1. `openhands-app` is running and healthy
2. `stagehand-mcp` is running and reachable from the sandbox bridge
3. LM Studio is reachable from:
- host
- `openhands-app`
- `open-webui`
- `stagehand-mcp`
4. OpenHands persisted settings in `data/openhands/settings.json` still point to the canonical model/base/MCP values
5. OpenHands can launch a sandbox from `oh-shop/agent-server:1.11.4-runtime-patched`
6. The sandbox can reach `host.docker.internal:3020/mcp`
7. The smoke harness can read terminal sandbox events before cleanup

## Current runtime weak points before normalization

1. OpenHands app build is pinned only by luck because the Dockerfile still says `:latest`.
2. OpenWebUI runtime is pinned only by luck because compose still says `:main`.
3. sandbox image family is mixed between base and installed Python packages.
4. Stagehand build reproducibility is weaker than it should be because the lockfile is not used in Docker build.
5. The runtime still depends on tracked mutable state under `data/openhands/`.
6. `chat-guard` remains operationally useful but is outside the canonical baseline.

## Release-grade minimum proof for this scaffold

For this scaffold baseline, the minimum honest proof should remain:

1. rebuild local patched images
2. start canonical stack through `scripts/up.sh`
3. pass `./scripts/verify.sh`
4. pass the canonical browser smoke proof in `scripts/agent_house.py smoke-test-browser-tool`
5. confirm sandbox cleanup still passes

Anything below that is infrastructure smoke, not release-grade scaffold proof.

## Post-normalization execution result

After normalization:
- the service dependency chain came back up cleanly
- `openhands-app`, `open-webui`, and `stagehand-mcp` all reached healthy container state

The blocking runtime dependency was external to the repo:
- host LM Studio was unavailable on `http://localhost:1234`

That means the current failing dependency edge is:

```text
Host LM Studio (down)
  -> OpenHands provider-route checks fail
  -> OpenWebUI provider-route checks fail
  -> stagehand-mcp provider-route checks fail
  -> canonical browser proof cannot reach tool execution
```
