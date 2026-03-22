# OH_SHOP Automated web_research Smoke Test

- Captured at: 2026-03-21 22:40:57 CDT
- Repo root: /home/dev/OH_SHOP
- Command: python3 scripts/agent_house.py smoke-test-web-research
- Title: OH_SHOP OpenHands proof 20260321_224057
- Start task id: 7da87ce8346f4b0c954676ec552d5c28
- Start task status: READY
- App conversation id: b2350be2149e4837a42ed18206814750
- Sandbox id: oh-agent-server-53NUW0LpHluEHT4U7ANmc5
- Agent server URL: http://host.docker.internal:44657
- Conversation URL: http://localhost:44657/api/conversations/b2350be2149e4837a42ed18206814750
- Final execution status: stuck
- Outcome classification: provider/dependency failure
- Detail: web_research tool observation was missing or marked as an error

## Prompt

```text
Get the README file from the openGauss project.
```

## Assistant Reply

```text
(no assistant reply captured)
```

## Tool Observation

```text
Error calling MCP tool web_re_search: Connection closed
```
