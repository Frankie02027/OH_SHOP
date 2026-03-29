# OpenHands App Trace

Date context: 2026-03-29

## Scope

App-side trace for the repro run:
- start task id: `0f5a19bf8832435d9035b67fa765ebce`
- app conversation id: `b3e00b80e57a4e0d9be2b653cb1b2a22`
- sandbox id: `oh-agent-server-xC0Bgbvjp2GAUZBX1wvFV`

Log window inspected:

```bash
docker logs --since '2026-03-29T11:51:30' --until '2026-03-29T11:52:20' openhands-app
```

## Relevant log lines

```text
16:51:53 - Assigned sandbox oh-agent-server-xC0Bgbvjp2GAUZBX1wvFV to conversation unknown
POST /api/v1/app-conversations -> 200
GET /api/v1/app-conversations/start-tasks?ids=0f5a19bf8832435d9035b67fa765ebce -> 200

16:51:58 - mkdir failed: mkdir: cannot create directory ‘/workspace/project’: File exists

16:51:59 - Loaded 38 skills from agent-server
16:51:59 - Loaded 1 total skills from agent-server: ['work_hosts']
16:51:59 - Loading custom MCP config from user settings: 0 SSE, 1 SHTTP, 0 STDIO servers
16:51:59 - Successfully merged custom MCP config: added 0 SSE, 1 SHTTP, and 0 STDIO servers
16:51:59 - Final MCP configuration: {'mcpServers': {'default': {'url': 'http://host.docker.internal:3000/mcp/mcp'}, 'shttp_f7ea47d5': {'url': 'http://host.docker.internal:3020/mcp', 'transport': 'streamable-http', 'timeout': 60}}}

POST /api/v1/webhooks/conversations -> 200
POST /api/v1/webhooks/events/b3e00b80e57a4e0d9be2b653cb1b2a22 -> 200
```

## App-side findings

What the app definitely did:
- created the app conversation
- created the sandbox
- waited for the sandbox to come ready
- loaded sandbox skills
- injected the custom SHTTP MCP config
- accepted conversation and event webhooks from the sandbox

What the app logs did not show:
- no app-side Python stack trace
- no app-side model-dispatch exception
- no app-side MCP registration failure
- no app-side webhook rejection

## App-side hypothesis

The OpenHands app is not the failing component.

The app-side trace proves:
- app ↔ sandbox startup protocol works
- settings and MCP config injection reached the sandbox
- event propagation back to the app is alive

The failure therefore happens inside the sandbox conversation run after startup and after app-side injection, not in the OpenHands app control plane itself.
