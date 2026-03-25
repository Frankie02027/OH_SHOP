FROM docker.openhands.dev/openhands/openhands:latest

# Vendor patched converters directly (replaces runtime patch scripts)
COPY compose/openhands_override/vendor_sdk/fn_call_converter.py \
     /app/.venv/lib/python3.13/site-packages/openhands/sdk/llm/mixins/fn_call_converter.py
COPY compose/openhands_override/vendor_sdk/fn_call_converter_v0.py \
     /app/openhands/llm/fn_call_converter.py

# Apply external-resource-routing patch (still needed for no-repo bias)
COPY scripts/patch_openhands_external_resource_routing.py /opt/oh_shop/patch_openhands_external_resource_routing.py
RUN python /opt/oh_shop/patch_openhands_external_resource_routing.py \
    && rm -f /opt/oh_shop/patch_openhands_external_resource_routing.py

# Force native_tool_calling=False for openhands-lm in the LLM constructor
RUN python -c "\
import re, pathlib; \
p = pathlib.Path('/app/openhands/app_server/app_conversation/live_status_app_conversation_service.py'); \
src = p.read_text(); \
old = \"usage_id='agent',\\n        )\"; \
new = \"usage_id='agent',\\n            native_tool_calling=False if (model and 'openhands-lm' in model) else True,\\n        )\"; \
assert old in src, 'Patch target not found'; \
p.write_text(src.replace(old, new, 1)); \
print('Patched native_tool_calling')"

# Always load default tools even when no repo is selected + MCP is configured.
# Without this patch, tools=[] when no repo selected, leaving the agent with
# only MCP tools (e.g. web_research) and no terminal/file_editor/browser.
RUN python - <<'PY'
from pathlib import Path

p = Path('/app/openhands/app_server/app_conversation/live_status_app_conversation_service.py')
src = p.read_text()
old = '[] if (not selected_repository and mcp_config) else get_default_tools(enable_browser=True)'
new = 'get_default_tools(enable_browser=True)  # PATCHED: always include default tools'

if old in src:
    p.write_text(src.replace(old, new, 1))
    print('Patched default_tools: always include tools')
else:
    print('default_tools patch target not found (may already be patched or code changed)')
PY

# Invalidate bytecode caches so Python loads the vendored .py files
RUN find /app -name '*.pyc' \( -path '*/fn_call_converter*' -o -path '*/live_status*' \) -delete
