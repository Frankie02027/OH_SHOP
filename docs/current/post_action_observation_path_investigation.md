# Post-Action Observation Path Investigation

## Verdict

FIXED

The original live blocker was a stacked defect:

1. The sandbox emitted a browser tool action for a nonexistent tool name, `browserbase_navigate`, so the intended Stagehand navigation request never reached the real Stagehand MCP tool.
2. OpenHands did record the failure, but it recorded it as an `AgentErrorEvent`, not as a successful `ObservationEvent`.
3. The smoke harness only looked for `ObservationEvent`, so it misreported the run as "no observation captured" instead of surfacing the real tool error.

After this pass:

1. The sandbox now runs with `native_tool_calling=False` for the local LM Studio endpoint.
2. The fresh-session smoke emits the correct Stagehand tool action, records a successful `ObservationEvent`, captures a final assistant reply, and finishes cleanly.
3. The smoke harness now surfaces `AgentErrorEvent` details instead of hiding them behind a generic missing-observation classification.

The originally investigated blocker is fixed.

## Reproduction Commands Used

```bash
cd /home/dev/OH_SHOP

VERIFY_CYCLES=1 VERIFY_INTERVAL=1 python3 ops/garagectl.py verify

python3 ops/garagectl.py smoke-test-browser-tool \
  --prompt "Use the Stagehand browser tools to open https://example.com and tell me the exact page title. Say explicitly that you used a browser tool." \
  --output docs/current/browser_smoke_post_action_after_fix.md \
  --timeout 240

docker logs openhands-app --tail 300
docker logs stagehand-mcp --tail 300
docker logs oh-agent-server-1rc3cg3yO6fufKwPOrl0XM --tail 300
```

## Exact Repo State

- Branch: `master`
- HEAD during this pass: `9bbbd74cf2d59196c78bb4c8709938ff7cbfef54`
- Worktree was not clean after reproduction because this pass changed:
  - `ops/garagectl.py`
  - `compose/openhands_override/apply_runtime_patches.py`
  - `data/openhands/openhands.db`
  - `data/openhands/v1_conversations/55e1c784880844a88623530a0ed3c4b0/`
  - `docs/current/browser_smoke_post_action_after_fix.md`

## Files Inspected

- `ops/garagectl.py`
- `compose/docker-compose.yml`
- `compose/openhands_override/Dockerfile`
- `compose/openhands_override/apply_runtime_patches.py`
- `compose/agent_server_override/Dockerfile`
- `compat/openhands_sdk_overrides/fn_call_converter.py`
- `vendor/stagehand_mcp/src/server.ts`
- `docs/current/browser_smoke_after_dynamic_model_sync.md`
- `docs/current/browser_smoke_post_action_after_fix.md`
- `docs/current/repo_readiness_audit_for_schema_coding_followup.md`
- `docs/current/TROUBLESHOOTING.md`
- `docs/current/SETUP.md`
- live container file:
  - `/app/openhands/app_server/app_conversation/live_status_app_conversation_service.py`
- live sandbox traces:
  - `data/openhands/v1_conversations/8a0d2969a0ad4d6eafc6e16f1737012a/*`
  - `data/openhands/v1_conversations/55e1c784880844a88623530a0ed3c4b0/*`

## What Failed Before the Fix

### The failing conversation proved the request did not reach the real Stagehand navigation tool

From `data/openhands/v1_conversations/8a0d2969a0ad4d6eafc6e16f1737012a/6e7f195c12bb4873a6bb132fd4d93bb8.json`:

- `kind = "ActionEvent"`
- `tool_name = "browserbase_navigate"`
- `tool_call.name = "browserbase_navigate"`

From `data/openhands/v1_conversations/8a0d2969a0ad4d6eafc6e16f1737012a/99867b6f71b54f838a63bd5478827d12.json`:

- `kind = "AgentErrorEvent"`
- `tool_name = "browserbase_navigate"`
- `error = "Tool 'browserbase_navigate' not found. Available: [...] 'browserbase_stagehand_navigate' ..."`

That is the key boundary.

The requested tool was wrong before dispatch.

This means the original blocker was:

- Not `B`: Stagehand did not fail after receiving `browserbase_stagehand_navigate`.
- Not `E`: assistant reply propagation was not the first failing boundary.
- Closest to `A`: the intended Stagehand request never reached the correct Stagehand tool because the sandbox emitted the wrong tool name.

### OpenHands did record the failure, but not in the shape the smoke harness expected

The failure existed in the sandbox event stream as `AgentErrorEvent`.

The old smoke harness only paired:

- `ActionEvent`
- matching `ObservationEvent`

It ignored matching `AgentErrorEvent`, so it reported:

- action seen
- no successful observation captured
- execution stuck

That report was incomplete. The runtime had already recorded the real error.

## Stagehand Receipt / Observation / Reply Findings

### Before the fix

- Did Stagehand receive the intended navigation request: No.
- Why: the sandbox requested `browserbase_navigate`, which is not a registered MCP tool.
- Did OpenHands record an event after the action: Yes.
- What kind: `AgentErrorEvent`.
- Did a successful `ObservationEvent` exist for that action: No.
- Did a final assistant reply exist: No.

### After the fix

Conversation: `55e1c784880844a88623530a0ed3c4b0`

From `data/openhands/v1_conversations/55e1c784880844a88623530a0ed3c4b0/848bad2edfc941408c1c8ac33cd21da8.json`:

- `kind = "ActionEvent"`
- `tool_name = "browserbase_stagehand_navigate"`
- `tool_call_id = "toolu_01"`

From `data/openhands/v1_conversations/55e1c784880844a88623530a0ed3c4b0/9fbc39df2a984e4c9688892373d9c5d6.json`:

- `kind = "ObservationEvent"`
- `tool_name = "browserbase_stagehand_navigate"`
- `observation.is_error = false`
- text contains `Tab 0: Navigated to: https://example.com`

From `data/openhands/v1_conversations/55e1c784880844a88623530a0ed3c4b0/ebfc391ee8c241bcb8eb250df2847cd2.json`:

- `kind = "MessageEvent"`
- source `agent`
- assistant reply captured successfully

From `docs/current/browser_smoke_post_action_after_fix.md`:

- final execution status: `finished`
- outcome classification: `success`

So after the fix:

- Stagehand received valid work.
- OpenHands recorded a successful `ObservationEvent`.
- Assistant reply propagation succeeded.

## Exact Failing Boundary

### Original failing boundary

The real original boundary was:

`OpenHands sandbox emitted the wrong MCP tool name before valid Stagehand dispatch.`

That caused:

- local tool lookup failure
- `AgentErrorEvent` instead of successful `ObservationEvent`
- no final assistant reply
- misleading smoke classification

### Smoke harness status

The smoke harness was also partially wrong.

It was not wrong about the run failing.
It was wrong about why.

It treated:

- matching `AgentErrorEvent`

as if there were:

- no post-action result at all

That is now fixed.

## Exact Fixes Applied

### 1. Disabled native tool calling for the local LM Studio endpoint

File changed:

- `compose/openhands_override/apply_runtime_patches.py`

What changed:

- the OpenHands app-server patch no longer leaves native tool calling enabled for the local LM Studio route
- local endpoints matching:
  - `host.docker.internal:1234`
  - `127.0.0.1:1234`
  - `localhost:1234`
  now get `native_tool_calling=False`

Why:

- the failing run emitted a bogus native tool name
- after the change, the fresh sandbox state showed:
  - `native_tool_calling: False`
  - `tool_call_id: toolu_01`
  - correct tool name `browserbase_stagehand_navigate`

Proof from sandbox log:

- `Agent: ... 'native_tool_calling': False`

### 2. Fixed smoke extraction/classification for `AgentErrorEvent`

File changed:

- `ops/garagectl.py`

What changed:

- `_has_runtime_events(...)` now treats `AgentErrorEvent` as real runtime evidence
- `_extract_browser_tool_events(...)` now accepts either:
  - `ObservationEvent`
  - `AgentErrorEvent`
  for the matching `tool_call_id`
- smoke failure detail now surfaces the real error text if the tool result exists but is an error

Why:

- the old harness hid the true failure boundary

## Runtime Proof After the Fix

### Verify

`VERIFY_CYCLES=1 VERIFY_INTERVAL=1 python3 ops/garagectl.py verify`

Result:

- PASS
- Layers 1 through 5 passed
- Layer 6 remains intentionally unproven

### Smoke

`python3 ops/garagectl.py smoke-test-browser-tool ...`

Result:

- PASS
- artifact written to `docs/current/browser_smoke_post_action_after_fix.md`
- final execution status `finished`
- successful Stagehand navigation observation captured
- final assistant reply captured

## Residual Non-Blocking Findings

The original blocker is fixed, but the successful run still showed secondary runtime issues that did not block this smoke to completion:

1. `browserbase_evaluate` intermittently returned an MCP `-32602` invalid tools/call result.
2. `browserbase_stagehand_extract` sometimes returned:
   - `Failed to extract content: No object generated: the model did not return a response.`
3. `browserbase_stagehand_observe` sometimes returned:
   - `Failed to observe: No object generated: the model did not return a response.`
4. `browserbase_stagehand_agent` produced failures such as:
   - `Expected 'none' | 'auto' | 'required', received object`
   - `Invalid type for 'input'.`
5. `browser_get_state` hit a browser-use serialization bug:
   - `Browser operation failed: 1 validation error for TextContent ... input_type=tuple`

These are real defects or incompatibilities, but they are not the blocker that caused the original post-action stuck/no-reply failure.

## Final Conclusion

The original investigated defect is fixed.

The correct answer to the original boundary question is:

1. The intended Stagehand request was not reaching the valid Stagehand tool because the sandbox emitted the wrong tool name.
2. OpenHands did record the failure, but as `AgentErrorEvent`.
3. The smoke harness missed that event type and misclassified the failure.

After the fix:

1. the sandbox emits the correct Stagehand tool name
2. a successful `ObservationEvent` is recorded
3. the final assistant reply is captured
4. the smoke run finishes successfully
