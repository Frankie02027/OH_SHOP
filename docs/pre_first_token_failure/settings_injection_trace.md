# Settings Injection Trace

Date context: 2026-03-29

## Source-of-truth inputs

Persisted OpenHands settings:
- `data/openhands/settings.json`

Canonical values there:

```json
{
  "llm_model": "openai/qwen3-coder-30b-a3b-instruct",
  "llm_api_key": "lm-studio",
  "llm_base_url": "http://host.docker.internal:1234/v1",
  "mcp_config": {
    "shttp_servers": [
      {
        "url": "http://host.docker.internal:3020/mcp",
        "api_key": null
      }
    ]
  }
}
```

## App-side injected conversation state

Captured from:
- `data/openhands/v1_conversations/b3e00b80e57a4e0d9be2b653cb1b2a22/8722f95b9ce24d9a9dbc540d0d441dff.json`
- live sandbox logs

Observed effective values:

```text
model      = openai/qwen3-coder-30b-a3b-instruct
base_url   = http://host.docker.internal:1234/v1
api_key    = lm-studio
mcp url    = http://host.docker.internal:3020/mcp
working_dir= /workspace/project
```

The conversation full-state also shows:

```text
tools = terminal, file_editor, task_tracker, browser_tool_set
include_default_tools = FinishTool, ThinkTool
```

## Sandbox environment injection

Captured from `docker inspect` on the transient sandbox:

Relevant environment variables:

```text
OH_SESSION_API_KEYS_0=<session key>
OH_WEBHOOKS_0_BASE_URL=http://host.docker.internal:3000/api/v1/webhooks
OPENVSCODE_SERVER_ROOT=/openhands/.openvscode-server
OH_CONVERSATIONS_PATH=/workspace/conversations
OH_BASH_EVENTS_DIR=/workspace/bash_events
CHROME_BIN=/usr/bin/chromium
PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
CHROMIUM_FLAGS=--no-sandbox --disable-dev-shm-usage --disable-gpu
```

Important detail:
- `llm_model`, `llm_base_url`, and MCP config are not passed as plain container env vars
- they are injected into the sandbox conversation state through the OpenHands conversation bootstrap path

## Mismatch check

No malformed injection was found.

What was verified:
- model id was present and non-empty
- base URL was present and correct
- API key was present
- MCP URL was present and correct
- workspace root was present and correct

## Verdict

This is not a config/settings injection failure.

The injected values are coherent and match the normalized runtime authority.
The failure occurs after correct injection, when LM Studio tries to satisfy the first completion request.
