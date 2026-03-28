# Failure Classification

Date context: 2026-03-27

## Primary classification

Primary root cause:
- `C. final reply is persisted but the smoke harness/API path misses it`

Secondary contributing cause:
- `D. conversation is marked finished before final reply propagation completes` for the app-server mirror specifically

This was not a model-generation failure.
This was not a Stagehand-routing failure.
This was not primarily a UI problem.

## Proven cause

During a fresh browser-tool run, the final reply existed in the live sandbox event stream as the terminal `finish` tool observation, while the app-server mirrored event feed lagged behind it.

The old smoke harness missed that reply because:

1. it could read the lagging app-server mirror first
2. it broke as soon as `execution_status == "finished"`
3. it therefore could finish the proof run without ever doing one guaranteed terminal read from the live sandbox source

## Evidence

### 1. The final reply existed

Direct sandbox event evidence from a live run:

```text
EVENT_COUNT 10
SystemPromptEvent agent
MessageEvent user TEXT= Use the Stagehand browser tools to open https://example.com and tell me the exact page title. Say explicitly that you used a browser tool.
ConversationStateUpdateEvent environment execution_status running
ActionEvent agent browserbase_stagehand_navigate 590746864
ObservationEvent environment browserbase_stagehand_navigate 590746864 OBS= [Tool 'browserbase_stagehand_navigate' executed.] | Tab 0: Navigated to: https://example.com
ActionEvent agent browserbase_stagehand_extract 523614187
ObservationEvent environment browserbase_stagehand_extract 523614187 OBS= [Tool 'browserbase_stagehand_extract' executed.] | Extracted content: { "extraction": "Example Domain" }
ActionEvent agent finish 196196160
ObservationEvent environment finish 196196160 OBS= I used browser tools to visit https://example.com and retrieved the exact page title, which is "Example Domain".
ConversationStateUpdateEvent environment execution_status finished
```

That proves the final reply existed and was exposed by the sandbox API.

### 2. The app-server mirror lagged

App-server mirrored event evidence for the same live conversation showed:
- system prompt
- full state
- user message
- `execution_status = running`
- navigate action and observation
- extract action and observation
- no terminal `finish` action
- no terminal `finish` observation

This proves the harness could observe a stale mirrored event set even while the sandbox had already reached the terminal reply.

### 3. The mirror lag is structurally plausible

Active sandbox runtime defaults from:
- `oh-shop/agent-server:1.11.4-runtime-patched`
- `/usr/local/lib/python3.12/site-packages/openhands/agent_server/config.py`

Relevant defaults:
- `event_buffer_size = 5`
- `flush_delay = 30.0`

That means the sandbox webhook publisher can delay app-server event persistence even after the sandbox itself already has the terminal event in memory.

## Why other explanations were ruled out

### A. Model produced no final reply after tool use

Ruled out.

Reason:
- the sandbox event stream contained the terminal `finish` reply text
- therefore the model/agent path did produce a final terminal answer

### B. Final reply exists in memory/event flow but is never persisted

Ruled out for the sandbox source.

Reason:
- sandbox `/api/conversations/{id}/events/search` exposed the terminal `finish` reply
- that is persisted enough for the live proof path the harness should trust during an active run

The app-server mirror was incomplete, but the reply was not absent from all persistence/API surfaces.

### D. Conversation is marked finished before final reply propagation completes

Partially true, but not the primary failure by itself.

Reason:
- `finished` was visible while the app-server mirror still lacked the terminal reply
- however the more actionable defect was that the smoke harness treated `finished` as a stop signal before forcing one last authoritative fetch from the sandbox source

### E. Callback/event system drops or suppresses the final assistant reply

Not proven as the primary defect.

Reason:
- the callback/mirror path lagged
- but no evidence showed the sandbox itself dropped the reply
- the successful rerun after the harness fix shows the defect can be resolved without changing callback or persistence internals

### F. Some other cause

Not needed.

The evidence is already specific enough to explain the defect and justify the minimal fix.

## Explicit answers to the required questions

1. When the proof run finishes, does a final assistant reply exist anywhere at all?
- Yes.

2. If yes, where?
- In the live sandbox event stream at `/api/conversations/{conversation_id}/events/search`
- Specifically as the terminal `ObservationEvent` for `tool_name = "finish"`

3. If no, what exact code path ended the conversation without creating one?
- Not applicable. A terminal reply did exist.

4. Does the smoke harness stop waiting too early?
- Yes.
- Before the fix, it could stop at `execution_status == "finished"` without guaranteeing a terminal live sandbox event fetch.

5. Is the conversation marked `finished` before the final assistant reply is stored or exposed?
- For the app-server mirrored event store, yes.
- For the live sandbox source, no meaningful gap was proven.

6. Is there a race between tool completion and assistant reply persistence?
- Yes.
- More precisely: there is a race between terminal sandbox events and delayed app-server mirror persistence.

7. Is a callback or post-processing step swallowing the final reply?
- No swallowing was proven.
- Mirror lag was proven.

8. Is the model producing a tool result but then failing to emit a completion message?
- No.
- The runtime emitted a terminal `finish` reply.

9. If it is a model-behavior issue, what exact evidence proves it is truly the model and not the app/harness boundary?
- Not applicable.
- The evidence points to the app/harness retrieval boundary, not the model.
