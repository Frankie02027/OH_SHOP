# OH_SHOP Automated Browser Tool Smoke Test

- Captured at: 2026-03-29 12:44:17 CDT
- Repo root: /home/dev/OH_SHOP
- Command: python3 scripts/agent_house.py smoke-test-browser-tool
- Title: OH_SHOP OpenHands proof 20260329_124417
- Start task id: 60f73a7aa4f141a3acd1a7afafeccf72
- Start task status: READY
- App conversation id: 2d355fa08fdf45e5bebabef5f86ac4e2
- Sandbox id: oh-agent-server-6XkltI0sqwRkRS9PEdoNfv
- Agent server URL: http://host.docker.internal:50395
- Conversation URL: http://localhost:50395/api/conversations/2d355fa08fdf45e5bebabef5f86ac4e2
- Final execution status: finished
- Outcome classification: success
- Captured reply source: finish_observation
- Detail: fresh-session API smoke test captured tool action, successful observation, assistant reply, and finished execution

## Prompt

```text
Use the Stagehand browser tools to open https://example.com and tell me the exact page title. Say explicitly that you used a browser tool.
```

## Assistant Reply

```text
I used the browser tool to open https://example.com and found that the exact page title is "Example Domain".
```

## Tool Observation

```text
[Tool 'browserbase_stagehand_navigate' executed.]
Tab 0: Navigated to: https://example.com
```
