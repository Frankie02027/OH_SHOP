# Targeted Fix Summary

Date context: 2026-03-27

## Scope

This fix stayed inside the Phase 2 defect lane:
- successful browser-tool execution
- missing final assistant reply capture

No browser-lane replacement work was done.
No canonical config values were changed.
No broad runtime cleanup was done.

## Files changed

### 1. `scripts/agent_house.py`

This was the only code file changed for the defect fix.

Changed areas:
- `_fetch_conversation_events(...)`
- `_extract_browser_tool_events(...)`
- `_smoke_markdown(...)`
- `cmd_smoke_test_browser_tool()`

## Exact logic changed

### A. Event-source precedence changed to sandbox-first

Before:
- the harness could read the app-server mirrored event feed first
- that mirror can lag behind the live sandbox due to buffered webhook delivery

After:
- `_fetch_conversation_events(...)` prefers the live sandbox event endpoint first
- it only falls back to the app-server mirrored event endpoint if sandbox retrieval is unavailable

Why:
- during an active run, the sandbox is the authoritative source for terminal events
- the app-server mirror is not timely enough to trust at the final-reply boundary

### B. Terminal `finish` events are treated as explicit final-reply sources

Before:
- the harness already had partial logic for terminal finish events, but the proof artifact did not surface which terminal path actually won

After:
- `_extract_browser_tool_events(...)` returns both:
  - the extracted assistant reply text
  - the reply source classification:
    - `agent_message`
    - `finish_action`
    - `finish_observation`
    - `none`

Why:
- the active runtime can terminate through the finish tool rather than an agent `MessageEvent`
- the proof artifact needed to say which path produced the final reply

### C. The smoke loop now crosses the `finished` boundary safely

Before:
- `cmd_smoke_test_browser_tool()` could break as soon as the conversation reported `execution_status == "finished"`
- that allowed the proof to end before one guaranteed terminal event fetch from the live sandbox

After:
- the command performs the terminal event fetch through the `finished` boundary
- if the reply is visible on that pass, it records success
- only then does it exit the loop/finalize the proof

Why:
- `finished` alone was not sufficient proof that the final reply had been observed by the harness

### D. Proof output now records the captured reply source

After:
- `_smoke_markdown(...)` includes:
  - `Captured reply source: ...`

Why:
- this makes the proof artifact self-describing
- it prevents future ambiguity about whether success came from an agent message or a finish-tool terminal observation

## Why this is the minimal fix

This fix is minimal because it:
- changes only the proof harness retrieval boundary
- does not modify OpenHands core runtime behavior
- does not modify Stagehand MCP behavior
- does not change OpenHands persisted settings
- does not change the canonical startup path
- does not change the canonical provider or MCP URL

The proven defect was:
- the harness missed a real terminal reply that already existed

So the minimal correct fix was:
- change the harness to read the authoritative live source at the terminal boundary
- stop treating `finished` as sufficient before the final reply has actually been observed

## Why broader fixes were not taken

No app-server mirror rewrite was done because:
- Phase 2 scope is narrow
- the proof already passes without that broader change

No callback/webhook flush rewrite was done because:
- mirror lag was a contributing factor
- but the harness-side fix already resolves the missing-proof defect directly

No OpenHands terminal-event redesign was done because:
- the runtime’s `finish` terminal path is already valid by design
- the bug was in retrieval/proof logic, not in the finish-tool design itself
