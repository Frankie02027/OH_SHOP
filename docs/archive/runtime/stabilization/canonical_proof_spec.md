# Canonical Runtime Proof Spec

Date context: 2026-03-27

This proof spec defines the single canonical end-to-end runtime proof for Phase 1 stabilization.

## Exact proof command

```bash
python3 scripts/agent_house.py smoke-test-browser-tool \
  --prompt "Use the Stagehand browser tools to open https://example.com and tell me the exact page title. Say explicitly that you used a browser tool." \
  --output docs/runtime_stabilization/browser_smoke_run_example_com.md \
  --timeout 240
```

## Why this is the canonical proof

- It exercises the canonical startup and control path rooted in `scripts/agent_house.py`.
- It exercises the canonical browser/tool lane:
  - `stagehand-mcp`
- It exercises the canonical provider path:
  - host LM Studio at `http://host.docker.internal:1234/v1`
- It avoids weather/search variability.
- It asks for one deterministic browser action and one deterministic page-title answer.

## Exact expected runtime path

1. `scripts/agent_house.py smoke-test-browser-tool` starts a fresh OpenHands task through the app at `http://127.0.0.1:3000`.
2. OpenHands loads persisted runtime settings from `data/openhands/settings.json`.
3. OpenHands uses:
   - `llm_model = openai/qwen3-coder-30b-a3b-instruct`
   - `llm_base_url = http://host.docker.internal:1234/v1`
   - `mcp_config.shttp_servers[0].url = http://host.docker.internal:3020/mcp`
4. OpenHands launches a fresh sandbox container from:
   - `oh-shop/agent-server:1.11.4-runtime-patched`
5. The task reaches `stagehand-mcp`.
6. `stagehand-mcp` uses:
   - `STAGEHAND_MODEL=qwen3-coder-30b-a3b-instruct`
   - `STAGEHAND_LLM_BASE_URL=http://host.docker.internal:1234/v1`
7. Stagehand performs browser navigation to `https://example.com`.
8. OpenHands returns a final assistant reply that includes the exact page title and explicitly says a browser tool was used.
9. The smoke harness cleans up transient callback rows and the sandbox container.

## Exact success criteria

The proof is a success only if all of the following are true:

1. Start-task status becomes `READY`.
2. A sandbox container is created for the run.
3. A browser-tool observation is captured.
4. The browser observation shows successful navigation to `https://example.com`.
5. A final assistant reply is captured.
6. The final assistant reply includes the exact title:
   - `Example Domain`
7. The final assistant reply explicitly says it used a browser tool.
8. The sandbox cleanup check passes after the run.

## Exact evidence required

Required evidence artifacts:
- `docs/runtime_stabilization/browser_smoke_run_example_com.md`
- `docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'`
- `curl -sf http://127.0.0.1:3000/api/settings | jq '{llm_model,llm_base_url,mcp_config}'`

Required evidence fields inside the smoke artifact:
- start task id
- start task status
- app conversation id
- sandbox id
- agent server URL
- final execution status
- outcome classification
- assistant reply block
- tool observation block

## Cleanup behavior after run

Required cleanup behavior:
- transient callback rows created by the proof should be removed
- the proof sandbox container should not remain orphaned after the harness cleanup
- the stack itself may remain up for further debugging unless the operator chooses to run `scripts/down.sh`

Not required for cleanup:
- resetting `data/openhands/openhands.db` to a pristine baseline

Reason:
- the DB is tracked mutable runtime state in this repo and proof runs already mutate it

## Current execution status

This proof was executed during Phase 1 stabilization.

Observed command:

```bash
python3 scripts/agent_house.py smoke-test-browser-tool \
  --prompt "Use the Stagehand browser tools to open https://example.com and tell me the exact page title. Say explicitly that you used a browser tool." \
  --output docs/runtime_stabilization/browser_smoke_run_example_com.md \
  --timeout 240
```

Observed result:
- start task status:
  - `READY`
- tool observation:
  - `[Tool 'browserbase_stagehand_navigate' executed.]`
  - `Tab 0: Navigated to: https://example.com`
- final execution status:
  - `finished`
- outcome classification:
  - `model-behavior failure`
- detail:
  - `conversation finished after the tool observation but no final assistant reply was captured`
- sandbox cleanup:
  - passed

## Interpretation of current result

What this proves:
- the canonical startup path is real
- the canonical OpenHands config is loaded
- the canonical MCP URL is reachable
- the canonical Stagehand browser lane is active
- the task can reach the browser tool layer and navigate successfully

What this does not prove yet:
- reliable final assistant completion after browser tool execution

Current blocking defect:
- the proof now fails at the final assistant reply boundary, not at service startup, config selection, or browser-tool routing
