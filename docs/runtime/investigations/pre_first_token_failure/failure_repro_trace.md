# OH_SHOP Automated Browser Tool Smoke Test

- Captured at: 2026-03-29 11:51:53 CDT
- Repo root: /home/dev/OH_SHOP
- Command: python3 scripts/agent_house.py smoke-test-browser-tool
- Title: OH_SHOP OpenHands proof 20260329_115153
- Start task id: 0f5a19bf8832435d9035b67fa765ebce
- Start task status: READY
- App conversation id: b3e00b80e57a4e0d9be2b653cb1b2a22
- Sandbox id: oh-agent-server-xC0Bgbvjp2GAUZBX1wvFV
- Agent server URL: http://host.docker.internal:50031
- Conversation URL: http://localhost:50031/api/conversations/b3e00b80e57a4e0d9be2b653cb1b2a22
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

## Exact identifiers

- Captured at: `2026-03-29 11:51:53 CDT`
- Start task id: `0f5a19bf8832435d9035b67fa765ebce`
- App conversation id: `b3e00b80e57a4e0d9be2b653cb1b2a22`
- Sandbox id: `oh-agent-server-xC0Bgbvjp2GAUZBX1wvFV`
- Agent server URL: `http://host.docker.internal:50031`
- Conversation URL: `http://localhost:50031/api/conversations/b3e00b80e57a4e0d9be2b653cb1b2a22`

## Observed status transitions

Persisted event sequence under `data/openhands/v1_conversations/b3e00b80e57a4e0d9be2b653cb1b2a22/`:

```text
2026-03-29T16:51:59.851767  ConversationStateUpdateEvent  full_state           execution_status = idle
2026-03-29T16:52:00.189287  SystemPromptEvent
2026-03-29T16:52:00.190989  MessageEvent                  user prompt
2026-03-29T16:52:00.194138  ConversationStateUpdateEvent  execution_status     running
2026-03-29T16:52:02.640433  ConversationStateUpdateEvent  execution_status     error
```

What did not appear:
- no agent `MessageEvent`
- no browser `ActionEvent`
- no browser `ObservationEvent`
- no `finish` action or observation
- no token usage in app-side metrics

## Exact failure point

The smoke harness reached:
- task creation
- sandbox creation
- app conversation creation
- sandbox conversation `running`

The run then failed before:
- first successful LLM completion
- first assistant token or reply
- first browser tool call
- first browser observation

Nearest proven failure boundary from the sandbox logs:
- LM Studio rejected the very first `/v1/chat/completions` request for model `qwen3-coder-30b-a3b-instruct`
- OpenHands surfaced that as `LLMBadRequestError`
- the sandbox conversation flipped to `error`
