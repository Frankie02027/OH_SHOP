# MCP Tool Registration Trace

Date context: 2026-03-29

## Question

Did the crash happen before tool registration, during tool registration, or after tool registration but before the first tool call?

## Evidence from sandbox logs

Relevant log lines:

```text
Created 30 MCP tools: ['browserbase_stagehand_navigate', 'browserbase_stagehand_act', 'browserbase_stagehand_extract', 'browserbase_stagehand_observe', ... 'browserbase_stagehand_agent']

Loaded 45 tools from spec:
['terminal', 'file_editor', 'task_tracker', 'browser_navigate', ..., 'browserbase_stagehand_navigate', ..., 'browserbase_stagehand_agent']

POST /api/conversations -> 201
GET /api/conversations?ids=b3e00b80-e57a-4e0d-9be2-b653cb1b2a22 -> 200
GET /api/conversations/b3e00b80e57a4e0d9be2b653cb1b2a22/events/search -> 200

ERROR openhands.agent_server.event_service - Error during conversation run from send_message
```

## Evidence from persisted events

Persisted event files for the failing repro contain:
- `SystemPromptEvent`
- user `MessageEvent`
- `execution_status = running`
- `execution_status = error`

Persisted event files do not contain:
- any browser `ActionEvent`
- any browser `ObservationEvent`
- any agent `MessageEvent`

## Interpretation

Stagehand / MCP registration was reached successfully.

What definitely happened:
- MCP config was merged into the sandbox conversation
- the sandbox created MCP tool definitions
- the browser toolset was available to the agent spec

What definitely did not happen:
- no MCP browser tool was actually invoked
- Stagehand did not receive a tool call from the agent during the failing repro

## Verdict

The crash is **post-registration but pre-tool-call**.

Stagehand is not the failing component in this repro.
The failure happens earlier, at the first LLM completion attempt that would have decided whether to emit a tool call.
