ARG OPENHANDS_BASE_IMAGE=docker.openhands.dev/openhands/openhands:1.5.0@sha256:c463babec5551ee8a8209fad8a76981bbb7f50770ae484309ffcc5447890c409
FROM ${OPENHANDS_BASE_IMAGE}

# Shared converter overrides used by both the app and sandbox images
COPY compat/openhands_sdk_overrides/fn_call_converter.py \
     /app/.venv/lib/python3.13/site-packages/openhands/sdk/llm/mixins/fn_call_converter.py
COPY compat/openhands_sdk_overrides/fn_call_converter_v0.py \
     /app/openhands/llm/fn_call_converter.py

# Apply the canonical OpenHands app patch set in one place.
COPY compose/openhands_override/apply_runtime_patches.py /opt/oh_shop/apply_runtime_patches.py
RUN python /opt/oh_shop/apply_runtime_patches.py \
    && rm -f /opt/oh_shop/apply_runtime_patches.py

# Invalidate bytecode caches so Python loads the vendored .py files
RUN find /app -name '*.pyc' \( -path '*/fn_call_converter*' -o -path '*/live_status*' \) -delete
