# Verify Rerun Result

Date context: 2026-03-29

## Command

```bash
./scripts/verify.sh
```

## Outcome

Exit status:

```text
0
```

Final summary from the verifier:

```text
Verification summary:
  PASS: layers 1-5 passed for all cycles. Layer 6 remains intentionally unproven.
```

## Layer-by-layer result

The verifier ran 6 cycles. Layers 1 through 5 passed on every cycle.

Representative passing results:

```text
Layer 1 - container/process up
  [PASS] Docker Engine available
  [PASS] Canonical compose file present
  [PASS] OpenHands container running
  [PASS] OpenWebUI container running
  [PASS] Stagehand MCP container running

Layer 2 - service health endpoint responds
  [PASS] OpenHands
  [PASS] OpenWebUI
  [PASS] stagehand-mcp health
  [PASS] OpenHands container health state
  [PASS] OpenWebUI container health state
  [PASS] Stagehand MCP container health state

Layer 3 - provider/search dependencies reachable
  [PASS] LM Studio reachable on host - http://127.0.0.1:1234/v1/models
  [PASS] LM Studio route from OpenHands - reachable
  [PASS] LM Studio route from OpenWebUI - reachable
  [PASS] LM Studio route from stagehand-mcp - reachable
  [PASS] OpenHands route from sandbox bridge - reachable

Layer 4 - MCP endpoint reachable (weak readiness only)
  [PASS] stagehand-mcp /healthz reachable - status=ok
  [PASS] stagehand-mcp route from sandbox bridge - HTTP/1.1 200 OK

Layer 5 - OpenHands runtime settings alignment
  [PASS] OpenHands V1 tool-calling compatibility patch present
  [PASS] OpenHands live settings API reachable
  [PASS] OpenHands live LLM base URL matches LM Studio route
  [PASS] OpenHands live model uses required provider prefix
  [PASS] OpenHands live model ID exists in LM Studio /v1/models
  [PASS] OpenHands live MCP URL matches sandbox-reachable path
  [PASS] Persisted settings file matches live runtime settings

Layer 6 - fresh-session tool invocation
  [UNPROVEN] Fresh-session browser-tool invocation - requires manual MCP registration and a new OpenHands session; verify only proves infrastructure and readiness boundaries
```

## Interpretation

Now that LM Studio is up:
- the normalized baseline is provider-reachable
- the normalized baseline is startable
- the normalized baseline is config-aligned
- the normalized baseline is MCP-reachable at the weak-readiness level the verifier is designed to test

What `verify` still does not prove by design:
- end-to-end browser-tool success in a fresh session
- final assistant reply capture semantics
- post-tool agent completion behavior

Those remain the responsibility of the canonical smoke proof, not the verifier.
