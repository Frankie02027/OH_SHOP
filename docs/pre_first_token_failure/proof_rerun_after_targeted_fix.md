# OH_SHOP Automated Browser Tool Smoke Test

- Captured at: 2026-03-29 11:54:40 CDT
- Repo root: /home/dev/OH_SHOP
- Command: python3 scripts/agent_house.py smoke-test-browser-tool
- Title: OH_SHOP OpenHands proof 20260329_115440
- Start task id: 95ea921b5590407da6202d8f934fbe20
- Start task status: READY
- App conversation id: 11597269e6c94c6fb7343c7e67845205
- Sandbox id: oh-agent-server-1rVuM7tkLfKnjRzif3wNv1
- Agent server URL: http://host.docker.internal:51303
- Conversation URL: http://localhost:51303/api/conversations/11597269e6c94c6fb7343c7e67845205
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

## Preconditions for this rerun

Before this successful rerun, the local LM Studio runtime was cleared with:

```bash
lms unload --all
```

This removed the idle loaded-model state that had been causing the first completion request to fail with CUDA OOM during model load.
