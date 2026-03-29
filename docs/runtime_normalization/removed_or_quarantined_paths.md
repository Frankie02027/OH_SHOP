# Removed Or Re-Quarantined Paths

Date context: 2026-03-29

## Removed in this pass

These paths were removed because they were recorded earlier as non-authoritative or duplicate and no longer won in practice:

- `compose/openhands.compose.yml`
- `scripts/patch_openhands_tool_call_mode.py`
- `compose/agent_server_override/vendor_sdk/fn_call_converter.py`
- `compose/agent_server_override/vendor_sdk/fn_call_converter_v0.py`
- `compose/agent_server_override/vendor_sdk/vendor_sdk/fn_call_converter.py`
- `compose/agent_server_override/vendor_sdk/vendor_sdk/fn_call_converter_v0.py`
- `repos/stagehand(working)/packages/mcp/src/server.ts.bak`

## Moved into canonical authority

These paths were not deleted outright; they were moved into cleaner authority locations:

- `scripts/patch_openhands_external_resource_routing.py`
  -> `compose/openhands_override/apply_runtime_patches.py`

- `compose/openhands_override/vendor_sdk/`
  -> `compose/shared_vendor_sdk/`

## Still quarantined but retained

These paths still do not win at runtime, but were not deleted in this pass:

- `bridge/model_router/`
- `bridge/openapi_server/`
- `repos/OpenHands/`
- `repos/stagehand(working)/packages/mcp/.env`
- `repos/stagehand(working)/packages/mcp/.env.example`

## Why these removals were safe

1. The canonical startup path does not use `compose/openhands.compose.yml`.
2. The canonical OpenHands app patch path no longer uses `scripts/patch_openhands_tool_call_mode.py`.
3. Both runtime images now consume the shared converter authority from `compose/shared_vendor_sdk/`.
4. The Stagehand build copies `src/server.ts`, not `src/server.ts.bak`.
