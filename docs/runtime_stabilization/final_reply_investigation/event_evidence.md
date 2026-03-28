# Event Evidence

Date context: 2026-03-27

## Scope

This artifact records the exact evidence that proved the missing-final-reply defect was at the retrieval boundary rather than the browser lane or the model/tool execution lane.

## 1. Live sandbox terminal event evidence

Conversation under direct live inspection:
- app conversation id: `3b7cdc27b178439fbf83de32852f2560`
- sandbox container: `oh-agent-server-2DZeElFAl0j8Cin0nUP5DO`

Direct sandbox event probe output:

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

Meaning:
- the final reply existed
- it existed before sandbox cleanup
- it existed as a terminal `finish` observation, not as an agent `MessageEvent`

Additional direct status probe:

```text
STATUS 0 finished AGENT_MSGS 0
```

Meaning:
- the conversation had already reached `finished`
- there were zero agent `MessageEvent` rows
- therefore a missing agent message does not mean the conversation had no final reply

## 2. App-server mirrored event evidence

App-server mirror probe command:

```bash
curl -s 'http://127.0.0.1:3000/api/v1/conversation/3b7cdc27b178439fbf83de32852f2560/events/search?sort_order=TIMESTAMP&limit=100'
```

Observed mirrored event set:
- `SystemPromptEvent`
- `ConversationStateUpdateEvent` with `key = full_state`
- user `MessageEvent`
- `ConversationStateUpdateEvent` with `key = execution_status`, `value = running`
- `browserbase_stagehand_navigate` action and observation
- `browserbase_stagehand_extract` action and observation
- no terminal `finish` action
- no terminal `finish` observation

Meaning:
- the app-server mirror lagged behind the live sandbox source
- the harness could miss the final reply if it trusted this mirror too early

## 3. Mirror-lag explanation from runtime config

Active sandbox runtime defaults inspected from:
- `oh-shop/agent-server:1.11.4-runtime-patched`
- `/usr/local/lib/python3.12/site-packages/openhands/agent_server/config.py`

Relevant values:

```text
event_buffer_size = 5
flush_delay = 30.0
```

Meaning:
- sandbox webhook delivery to the app server is buffered
- terminal events can exist in the sandbox before the mirror catches up

## 4. Canonical proof rerun evidence

Exact command run:

```bash
python3 scripts/agent_house.py smoke-test-browser-tool \
  --prompt "Use the Stagehand browser tools to open https://example.com and tell me the exact page title. Say explicitly that you used a browser tool." \
  --output docs/runtime_stabilization/final_reply_investigation/proof_rerun_result.md \
  --timeout 240
```

Observed result:
- exit status: `0`
- artifact path:
  - `docs/runtime_stabilization/final_reply_investigation/proof_rerun_result.md`

Key proof lines:

```text
- Final execution status: finished
- Outcome classification: success
- Captured reply source: finish_observation
```

Captured final reply:

```text
I visited https://example.com using browser tools and found that the exact page title is "Example Domain".
```

Meaning:
- after the harness fix, the canonical proof captures the terminal reply successfully

## 5. Verification output

Verification command:

```bash
./scripts/verify.sh
```

Observed final summary:

```text
Verification summary:
  PASS: layers 1-5 passed for all cycles. Layer 6 remains intentionally unproven.
```

Meaning:
- the targeted fix did not break the stabilized runtime verification layers

## 6. Running container state after proof rerun

Command:

```bash
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
```

Exact output:

```text
NAMES           IMAGE                                     STATUS
openhands-app   oh-shop/openhands:1.5.0-runtime-patched   Up 43 minutes (healthy)
open-webui      ghcr.io/open-webui/open-webui:main        Up 43 minutes (healthy)
stagehand-mcp   oh-stagehand-mcp:latest                   Up 43 minutes (healthy)
```

Meaning:
- the canonical runtime remained up and healthy after the proof rerun

## 7. Boundary conclusion

The evidence shows:
- Stagehand browser execution succeeded before the defect
- the final reply existed in the sandbox source before the defect
- the harness missed that reply because it could rely on a stale mirror and stop too early on `finished`

That makes this a retrieval-boundary defect, not a browser-tool execution defect.
