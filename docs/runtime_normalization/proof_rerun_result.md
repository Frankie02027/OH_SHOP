# OH_SHOP Automated Browser Tool Smoke Test

- Captured at: 2026-03-29 10:05:47 CDT
- Repo root: /home/dev/OH_SHOP
- Command: python3 scripts/agent_house.py smoke-test-browser-tool
- Title: OH_SHOP OpenHands proof 20260329_100547
- Start task id: fa7d22916c6b4ed2acf2c465b234e9e8
- Start task status: READY
- App conversation id: 302c3ff3612e49c8a4a145d2b106d04a
- Sandbox id: oh-agent-server-1MGaMKRbFsiprWtyzzlgRG
- Agent server URL: http://host.docker.internal:35105
- Conversation URL: http://localhost:35105/api/conversations/302c3ff3612e49c8a4a145d2b106d04a
- Final execution status: error
- Outcome classification: integration failure
- Captured reply source: none
- Detail: sandbox conversation ended in 'error'

## Prompt

```text
Use the Stagehand browser tools to open https://example.com and tell me the exact page title. Say explicitly that you used a browser tool.
```

## Assistant Reply

```text
(no assistant reply captured)
```

## Tool Observation

```text
(no tool observation captured)
```

## Rebuild / Startup Result

Canonical rebuild/start command:

```bash
./scripts/up.sh
```

Observed result:
- the normalized stack rebuilt successfully through the canonical path
- the pinned OpenHands app image rebuilt successfully
- the pinned sandbox image rebuilt successfully
- the normalized Stagehand image rebuilt successfully
- the three core services started successfully

## Verify Result

Verification command:

```bash
./scripts/verify.sh
```

Observed verification summary:

```text
Verification summary:
  FAIL: one or more required checks in layers 1-5 failed. Layer 6 remains intentionally unproven.
```

Observed failure boundary:

```text
LM Studio reachable on host - <urlopen error [Errno 111] Connection refused>
LM Studio route from OpenHands - dependency route check failed
LM Studio route from OpenWebUI - dependency route check failed
LM Studio route from stagehand-mcp - connect ECONNREFUSED 172.17.0.1:1234
OpenHands live model ID exists in LM Studio /v1/models - available=none reported
```

Interpretation:
- the normalized runtime wiring is up
- host LM Studio was not running during this rerun

## Post-Run Container State

Command:

```bash
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
```

Exact output:

```text
NAMES           IMAGE                                     STATUS
openhands-app   oh-shop/openhands:1.5.0-runtime-patched   Up 4 minutes (healthy)
open-webui      ghcr.io/open-webui/open-webui:main        Up 4 minutes (healthy)
stagehand-mcp   oh-stagehand-mcp:0.3.0-runtime-patched    Up 4 minutes (healthy)
```

## Normalized-baseline verdict

What passed:
- rebuild
- startup
- service health
- sandbox cleanup

What did not pass:
- provider reachability
- verify Layers 3 and part of 5
- canonical browser proof

Reason:
- host LM Studio was unavailable, so the proof died at the provider boundary before browser-tool execution began.
