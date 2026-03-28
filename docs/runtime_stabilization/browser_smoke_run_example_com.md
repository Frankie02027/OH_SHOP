# OH_SHOP Automated Browser Tool Smoke Test

- Captured at: 2026-03-27 19:12:25 CDT
- Repo root: /home/dev/OH_SHOP
- Command: python3 scripts/agent_house.py smoke-test-browser-tool
- Title: OH_SHOP OpenHands proof 20260327_191225
- Start task id: 69145079edeb472e9b6cd75392f7939f
- Start task status: READY
- App conversation id: 22b7a2ac97194fcdb5d8dcf46f4a8bfb
- Sandbox id: oh-agent-server-4Wf2rWTlpN3osHOgYuKwjA
- Agent server URL: http://host.docker.internal:58907
- Conversation URL: http://localhost:58907/api/conversations/22b7a2ac97194fcdb5d8dcf46f4a8bfb
- Final execution status: finished
- Outcome classification: model-behavior failure
- Detail: conversation finished after the tool observation but no final assistant reply was captured

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
[Tool 'browserbase_stagehand_navigate' executed.]
Tab 0: Navigated to: https://example.com
```
