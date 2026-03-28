# Instrumentation Notes

Date context: 2026-03-27

## Scope

Instrumentation for this pass was kept narrow and tied directly to the missing-final-reply defect.

No broad container rebuild instrumentation was added.
No Stagehand lane changes were made.
No canonical config paths were changed.

## Runtime inspection instrumentation

Read-only inspection was performed against the active runtime boundaries:

```bash
curl -s "http://127.0.0.1:3000/api/v1/conversation/{app_conversation_id}/events/search?sort_order=TIMESTAMP&limit=100"
curl -s "http://localhost:{sandbox_port}/api/conversations/{app_conversation_id}/events/search?sort_order=TIMESTAMP&limit=100"
curl -s "http://localhost:{sandbox_port}/api/conversations/{app_conversation_id}"
docker exec openhands-app sh -lc 'sed -n "..." /app/openhands/...'
docker run --rm --entrypoint sh oh-shop/agent-server:1.11.4-runtime-patched -lc 'sed -n "..." /usr/local/lib/python3.12/site-packages/openhands/...'
```

Purpose:
- prove whether the final reply existed at all
- compare sandbox live events vs app-server mirrored events
- confirm where `execution_status = finished` is exposed
- trace whether the smoke harness was stopping before the terminal reply became visible

## Code-level diagnostic additions

One targeted diagnostic signal was retained in:
- `scripts/agent_house.py`

Added signal:
- `Captured reply source`

Possible values now reported by the smoke artifact:
- `agent_message`
- `finish_action`
- `finish_observation`
- `none`

Why it was added:
- the active runtime can finish with either an agent `MessageEvent` or a `finish` tool terminal event
- the old smoke artifact only told us whether a reply string was present, not which runtime path produced it
- that made it too easy to blame the model generically instead of proving the exact terminal event shape

Removal impact:
- low
- this field is diagnostic only and can be removed later without changing runtime behavior

## Targeted harness instrumentation/fix boundary

The harness logic in `scripts/agent_house.py` was adjusted at the exact defect boundary:

1. `_fetch_conversation_events(...)`
- now prefers the live sandbox event source first
- only falls back to the app-server mirrored event source if sandbox retrieval is unavailable

2. `_extract_browser_tool_events(...)`
- now returns both the reply text and the reply source classification
- explicitly recognizes terminal `finish` events as valid final replies

3. `cmd_smoke_test_browser_tool()`
- no longer exits the polling loop immediately on `execution_status == "finished"` before performing a terminal event fetch
- performs the terminal fetch through the finished boundary so the terminal sandbox `finish` reply can be observed

Why this counts as instrumentation and not broad redesign:
- it changes only the proof harness retrieval boundary
- it does not change OpenHands message generation, persistence, Stagehand behavior, or app-server architecture
- it records just enough extra data to prove which terminal reply path won

## How to remove later

If Phase 2 diagnostics are no longer needed:

1. remove `assistant_source` plumbing from:
- `_extract_browser_tool_events(...)`
- `_smoke_markdown(...)`
- `cmd_smoke_test_browser_tool()`

2. if desired, collapse `_fetch_conversation_events(...)` back to a single preferred source

That said, keeping sandbox-first retrieval is justified even without diagnostics because it matches the live runtime source-of-truth during an active conversation.
