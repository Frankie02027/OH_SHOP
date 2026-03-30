# OH_SHOP Automated Browser Tool Smoke Test

- Captured at: 2026-03-29 11:39:12 CDT
- Repo root: /home/dev/OH_SHOP
- Command: python3 scripts/agent_house.py smoke-test-browser-tool
- Title: OH_SHOP OpenHands proof 20260329_113912
- Start task id: 888ded7f0ced473395c791dfa7e9449b
- Start task status: READY
- App conversation id: 9255cb0bd20e4c9caaa5393d4f73e3a4
- Sandbox id: oh-agent-server-1LF2m2tA3cuu37nC806vuP
- Agent server URL: http://host.docker.internal:45795
- Conversation URL: http://localhost:45795/api/conversations/9255cb0bd20e4c9caaa5393d4f73e3a4
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

## Persisted conversation evidence

Observed persisted event sequence for app conversation `9255cb0bd20e4c9caaa5393d4f73e3a4`:

```text
ConversationStateUpdateEvent: full_state (execution_status = idle)
SystemPromptEvent
MessageEvent: user prompt
ConversationStateUpdateEvent: execution_status = running
ConversationStateUpdateEvent: execution_status = error
```

What did not appear:
- no agent `MessageEvent`
- no browser `ActionEvent`
- no browser `ObservationEvent`
- no `finish` action or observation

## Failure boundary

What the rerun proves:
- sandbox creation succeeded
- the conversation entered `running`
- the sandbox received the canonical provider and MCP config
- the run failed before any LLM-token-bearing response or browser-tool action was emitted

Most precise proven boundary:
- after sandbox boot and config injection
- before first LLM completion
- before first browser-tool call

Classification:
- internal execution failure inside the OpenHands/sandbox path
- not the previous LM Studio provider outage

## Post-run cleanup

Observed result:

```text
[PASS] OpenHands sandbox cleanup after smoke test - removed 1 OpenHands sandbox container(s)
```
