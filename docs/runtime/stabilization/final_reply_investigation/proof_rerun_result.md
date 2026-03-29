# OH_SHOP Automated Browser Tool Smoke Test

- Captured at: 2026-03-27 19:44:24 CDT
- Repo root: /home/dev/OH_SHOP
- Command: python3 scripts/agent_house.py smoke-test-browser-tool
- Exact command: python3 scripts/agent_house.py smoke-test-browser-tool --prompt "Use the Stagehand browser tools to open https://example.com and tell me the exact page title. Say explicitly that you used a browser tool." --output docs/runtime_stabilization/final_reply_investigation/proof_rerun_result.md --timeout 240
- Title: OH_SHOP OpenHands proof 20260327_194424
- Start task id: 3bccde8b5f2e48459e3090823d503cbd
- Start task status: READY
- App conversation id: fbf8a2080995412a9197f0700ba1197c
- Sandbox id: oh-agent-server-2Kyoj4z4ipLWPwmPIxa9N3
- Agent server URL: http://host.docker.internal:48127
- Conversation URL: http://localhost:48127/api/conversations/fbf8a2080995412a9197f0700ba1197c
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
I visited https://example.com using browser tools and found that the exact page title is "Example Domain".
```

## Tool Observation

```text
[Tool 'browserbase_stagehand_navigate' executed.]
Tab 0: Navigated to: https://example.com
```

## Cleanup Result

```text
[PASS] OpenHands sandbox cleanup after smoke test - removed 2 OpenHands sandbox container(s)
```

## Post-Run Verification

Verification command:

```bash
./scripts/verify.sh
```

Observed verification summary:

```text
Verification summary:
  PASS: layers 1-5 passed for all cycles. Layer 6 remains intentionally unproven.
```

Container-state command:

```bash
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
```

Exact container output:

```text
NAMES           IMAGE                                     STATUS
openhands-app   oh-shop/openhands:1.5.0-runtime-patched   Up 43 minutes (healthy)
open-webui      ghcr.io/open-webui/open-webui:main        Up 43 minutes (healthy)
stagehand-mcp   oh-stagehand-mcp:latest                   Up 43 minutes (healthy)
```
