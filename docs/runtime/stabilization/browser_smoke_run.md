# OH_SHOP Automated Browser Tool Smoke Test

- Captured at: 2026-03-27 19:07:31 CDT
- Repo root: /home/dev/OH_SHOP
- Command: python3 scripts/agent_house.py smoke-test-browser-tool
- Title: OH_SHOP OpenHands proof 20260327_190731
- Start task id: f74b75e683d84d29a0d4bb1ae53ad237
- Start task status: READY
- App conversation id: 13b7376081fb4d7884b79cd4e63862f7
- Sandbox id: oh-agent-server-7BduNkbk4iYnlAbhogXd9q
- Agent server URL: http://host.docker.internal:54541
- Conversation URL: http://localhost:54541/api/conversations/13b7376081fb4d7884b79cd4e63862f7
- Final execution status: running
- Outcome classification: integration failure
- Detail: timed out after a successful tool observation while waiting for the final assistant reply

## Prompt

```text
Use the Stagehand browser tools to find the current temperature in Burbank, IL. Cite the source you used and say explicitly that you used a browser tool.
```

## Assistant Reply

```text
(no assistant reply captured)
```

## Tool Observation

```text
[Tool 'browserbase_session_create' executed.]
{
  "success": true,
  "message": "New browser session created",
  "config": {
    "viewport": "1920x1080",
    "headless": true,
    "experimental": true
  },
  "tabs": 1
}
```
