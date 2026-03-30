# Final Reply Trace

Date context: 2026-03-27

This artifact traces the exact post-tool path from browser-tool completion to final reply generation, persistence, API exposure, and smoke-harness retrieval.

## Scope

This trace stays inside the stabilized runtime path:
- startup/control:
  - `scripts/agent_house.py`
- app server:
  - running `openhands-app` container from `oh-shop/openhands:1.5.0-runtime-patched`
- sandbox agent server:
  - running `oh-shop/agent-server:1.11.4-runtime-patched`
- browser/tool lane:
  - `stagehand-mcp`

It does not assume `repos/OpenHands/` is runtime authority.
Where source was needed, the active running container files were inspected directly.

## Evidence commands

```bash
rg -n "_fetch_conversation_events|_extract_browser_tool_events|cmd_smoke_test_browser_tool" scripts/agent_house.py
sed -n '180,380p' scripts/agent_house.py
sed -n '620,1128p' scripts/agent_house.py

docker exec openhands-app sh -lc 'sed -n "1,260p" /app/openhands/app_server/app_conversation/app_conversation_router.py'
docker exec openhands-app sh -lc 'sed -n "160,320p" /app/openhands/app_server/app_conversation/live_status_app_conversation_service.py'
docker exec openhands-app sh -lc 'sed -n "1,260p" /app/openhands/app_server/event/event_router.py'
docker exec openhands-app sh -lc 'sed -n "1,260p" /app/openhands/app_server/event/event_service_base.py'
docker exec openhands-app sh -lc 'sed -n "140,190p" /app/openhands/app_server/event_callback/webhook_router.py'
docker exec openhands-app sh -lc 'sed -n "340,380p" /app/openhands/app_server/sandbox/docker_sandbox_service.py'

docker run --rm --entrypoint sh oh-shop/agent-server:1.11.4-runtime-patched -lc 'sed -n "1,260p" /usr/local/lib/python3.12/site-packages/openhands/agent_server/event_router.py'
docker run --rm --entrypoint sh oh-shop/agent-server:1.11.4-runtime-patched -lc 'sed -n "1,260p" /usr/local/lib/python3.12/site-packages/openhands/agent_server/event_service.py'
docker run --rm --entrypoint sh oh-shop/agent-server:1.11.4-runtime-patched -lc 'sed -n "380,560p" /usr/local/lib/python3.12/site-packages/openhands/agent_server/event_service.py'
docker run --rm --entrypoint sh oh-shop/agent-server:1.11.4-runtime-patched -lc 'sed -n "330,420p" /usr/local/lib/python3.12/site-packages/openhands/sdk/agent/agent.py'
docker run --rm --entrypoint sh oh-shop/agent-server:1.11.4-runtime-patched -lc 'sed -n "620,696p" /usr/local/lib/python3.12/site-packages/openhands/sdk/agent/agent.py'
docker run --rm --entrypoint sh oh-shop/agent-server:1.11.4-runtime-patched -lc 'sed -n "1,220p" /usr/local/lib/python3.12/site-packages/openhands/sdk/conversation/response_utils.py'
docker run --rm --entrypoint sh oh-shop/agent-server:1.11.4-runtime-patched -lc 'sed -n "1,120p" /usr/local/lib/python3.12/site-packages/openhands/sdk/tool/builtins/finish.py'
```

## Trace: task creation to reply retrieval

### 1. OpenHands task creation

The smoke harness starts here:
- `scripts/agent_house.py`
- `cmd_smoke_test_browser_tool()`

It creates an app conversation by POSTing to:
- `http://127.0.0.1:3000/api/v1/app-conversations`

Code path:
- `scripts/agent_house.py`
- `openhands-app:/app/openhands/app_server/app_conversation/app_conversation_router.py`
- `openhands-app:/app/openhands/app_server/app_conversation/live_status_app_conversation_service.py`

Relevant behavior:
- the app server creates an `AppConversationStartTask`
- waits for sandbox startup
- POSTs a `StartConversationRequest` to the sandbox agent server at:
  - `{agent_server_url}/api/conversations`
- saves `AppConversationInfo`
- returns a `READY` task with:
  - `app_conversation_id`
  - `sandbox_id`
  - `agent_server_url`

### 2. Sandbox conversation start

Relevant file:
- `oh-shop/agent-server:1.11.4-runtime-patched`
- `/usr/local/lib/python3.12/site-packages/openhands/agent_server/conversation_service.py`

Relevant behavior:
- `ConversationService.start_conversation()` creates `StoredConversation`
- starts `EventService`
- if `initial_message` exists, calls:
  - `await event_service.send_message(message, True)`

That immediately:
- appends the user `MessageEvent`
- schedules `LocalConversation.run()` in the background

### 3. Where the final reply is supposed to be created

Relevant file:
- `oh-shop/agent-server:1.11.4-runtime-patched`
- `/usr/local/lib/python3.12/site-packages/openhands/sdk/agent/agent.py`

There are two valid terminal reply shapes in this runtime:

1. Agent text reply path
- no tool calls
- `MessageEvent(source="agent", ...)` is emitted
- then `state.execution_status = FINISHED`

2. Finish-tool path
- agent emits `ActionEvent(tool_name="finish", ...)`
- tool executor returns `FinishObservation`
- `ObservationEvent(tool_name="finish", ...)` is emitted
- then `state.execution_status = FINISHED`

This is not a guess.
The active runtime ships:
- `openhands/sdk/conversation/response_utils.py`

That file explicitly says the final response can end either:
- by calling the finish tool
- or by returning a text `MessageEvent`

It also exposes:
- `get_agent_final_response(events)`

That function checks:
1. last `ActionEvent` with `tool_name == "finish"`
2. else last agent `MessageEvent`

So the runtime itself already treats `finish` as a first-class final-response path.

### 4. Where the final reply is supposed to be persisted

#### Sandbox persistence

Relevant file:
- `oh-shop/agent-server:1.11.4-runtime-patched`
- `/usr/local/lib/python3.12/site-packages/openhands/agent_server/event_service.py`

Relevant behavior:
- sandbox `EventService.search_events()` reads directly from the live in-memory conversation state:
  - `self._conversation._state.events`
- events are appended by `LocalConversation._on_event(...)`
- final terminal events therefore exist in sandbox event state immediately once emitted

In other words:
- sandbox event retrieval does not depend on the app-server mirror
- sandbox `/api/conversations/{id}/events/search` is the closest source-of-truth during a live run

#### App-server persistence

Relevant files:
- `openhands-app:/app/openhands/app_server/sandbox/docker_sandbox_service.py`
- `openhands-app:/app/openhands/app_server/event_callback/webhook_router.py`
- `openhands-app:/app/openhands/app_server/event/event_service_base.py`

Relevant behavior:
- each sandbox gets:
  - `WEBHOOK_CALLBACK_VARIABLE=http://host.docker.internal:3000/api/v1/webhooks`
- the sandbox posts batches of events back to:
  - `POST /api/v1/webhooks/events/{conversation_id}`
- the app server stores each event as a JSON file under:
  - `data/openhands/v1_conversations/{conversation_id}/`

Important detail:
- the sandbox webhook subscriber buffers events before posting them
- active runtime defaults from:
  - `oh-shop/agent-server:1.11.4-runtime-patched`
  - `/usr/local/lib/python3.12/site-packages/openhands/agent_server/config.py`
- defaults are:
  - `event_buffer_size = 5`
  - `flush_delay = 30.0`

That means:
- the app-server event mirror can lag behind the sandbox source
- if the sandbox is deleted before the buffer flushes, queued terminal events can be lost from the app-server mirror entirely

### 5. Where the final reply is supposed to be exposed through the API

#### Sandbox API

Relevant files:
- `/usr/local/lib/python3.12/site-packages/openhands/agent_server/event_router.py`
- `/usr/local/lib/python3.12/site-packages/openhands/agent_server/event_service.py`

Routes:
- conversation info:
  - `GET /api/conversations/{conversation_id}`
- events:
  - `GET /api/conversations/{conversation_id}/events/search`

This is the direct live source during a running sandbox.

#### App-server API

Relevant files:
- `openhands-app:/app/openhands/app_server/event/event_router.py`
- `openhands-app:/app/openhands/app_server/event/event_service_base.py`

Route:
- `GET /api/v1/conversation/{conversation_id}/events/search`

This route reads the mirrored filesystem events under:
- `data/openhands/v1_conversations/{conversation_id}/`

It is not guaranteed to be current if the sandbox webhook buffer has not flushed.

### 6. Where the smoke harness currently reads the reply

Relevant file:
- `scripts/agent_house.py`

Relevant functions:
- `_fetch_conversation_events(...)`
- `_extract_browser_tool_events(...)`
- `cmd_smoke_test_browser_tool()`

Current harness behavior:
1. poll sandbox conversation info at `conversation_url`
2. while status is not `finished`, fetch events using `_fetch_conversation_events(...)`
3. extract:
   - first browser `ActionEvent`
   - matching `ObservationEvent`
   - last agent `MessageEvent`
4. if `execution_status == "finished"`:
   - break out of the loop immediately
5. after the loop:
   - fetch events again
   - still extract only via `_extract_browser_tool_events(...)`
   - fail if no agent `MessageEvent` text was found

Current harness blind spot:
- `_extract_browser_tool_events(...)` only treats a final agent `MessageEvent` as the assistant reply
- it does not treat:
  - `finish` tool `ActionEvent`
  - `finish` tool `ObservationEvent`
as a valid final reply

### 7. What marks the conversation as `finished`

Relevant file:
- `/usr/local/lib/python3.12/site-packages/openhands/sdk/agent/agent.py`

There are at least two real `FINISHED` paths in the active runtime:

1. Agent text response path
- `MessageEvent(source="agent", ...)`
- then:
  - `state.execution_status = ConversationExecutionStatus.FINISHED`

2. Finish-tool path
- `ActionEvent(tool_name="finish", ...)`
- `ObservationEvent(tool_name="finish", ...)`
- then:
  - `state.execution_status = ConversationExecutionStatus.FINISHED`

The live repro for this defect used the second path.

## Live runtime evidence from a fresh repro

A fresh live conversation was started outside the smoke harness so the sandbox remained alive.

Conversation:
- app conversation id:
  - `3b7cdc27b178439fbf83de32852f2560`
- sandbox container:
  - `oh-agent-server-2DZeElFAl0j8Cin0nUP5DO`

Direct sandbox event stream showed:
1. `ActionEvent tool_name="browserbase_stagehand_navigate"`
2. matching successful `ObservationEvent`
3. `ActionEvent tool_name="browserbase_stagehand_extract"`
4. matching successful `ObservationEvent`
5. `ActionEvent tool_name="finish"`
6. `ObservationEvent tool_name="finish"` with text:
   - `I used browser tools to visit https://example.com and retrieved the exact page title, which is "Example Domain".`
7. `ConversationStateUpdateEvent key="execution_status" value="finished"`

This proves:
- a final reply did exist
- it existed in the sandbox source-of-truth
- it existed as a `finish` tool completion, not as an agent `MessageEvent`

At the same time, the app-server mirror for the same conversation only showed:
- the user message
- running state
- navigate action/observation
- extract action/observation

It did not yet show:
- `finish` action
- `finish` observation
- `execution_status = finished`

This proves the app-server mirror was stale relative to the sandbox source.

## Trace conclusions

### Proven answer to “where is the assistant reply supposed to be created?”

In this failing proof lane, the final reply is created by:
- `finish` tool execution
- not by an agent `MessageEvent`

### Proven answer to “where is it supposed to be persisted?”

First:
- sandbox conversation event state

Then, asynchronously:
- app-server filesystem mirror under `data/openhands/v1_conversations/{conversation_id}/`

### Proven answer to “where is it exposed through the API?”

Immediately:
- sandbox `GET /api/conversations/{id}/events/search`

Later, after webhook flush:
- app-server `GET /api/v1/conversation/{id}/events/search`

### Proven answer to “where does the smoke harness currently try to read it?”

It reads:
- app-server events first when available
- sandbox events as fallback

But it only recognizes:
- agent `MessageEvent`

It does not recognize:
- `finish` action/observation terminal replies

### Proven answer to “what marks the conversation as finished?”

In the failing proof lane:
- `finish` tool observation is emitted
- then `execution_status` becomes `finished`

There is no requirement in the active runtime that a final agent `MessageEvent` must exist before `finished`.

## Most important implication before code changes

The current smoke harness is not aligned with the active OpenHands runtime contract.

The active runtime contract already allows:
- final response by `finish` tool

The current smoke harness incorrectly requires:
- final response by agent `MessageEvent`

That mismatch is sufficient to explain the existing proof failure.
