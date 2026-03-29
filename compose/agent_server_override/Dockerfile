ARG AGENT_SERVER_BASE_IMAGE=ghcr.io/openhands/agent-server:61470a1-python@sha256:79535d97fd389719411f73795fe14d3ed57e4f0996c53525aaaf0e6e3e0b9936
FROM ${AGENT_SERVER_BASE_IMAGE}

USER root

# Install the three openhands packages from PyPI at matching version
# so we have real importable Python source instead of the frozen PyInstaller binary.
# Top-level package versions are explicit; deeper dependency locking is deferred.
RUN pip install --break-system-packages --no-cache-dir \
      openhands-agent-server==1.11.4 \
      openhands-sdk==1.11.4 \
      openhands-tools==1.11.4 && \
    python3 -c "import openhands.sdk.llm.mixins.fn_call_converter; print('SDK converter OK')"

# Overlay the canonical shared converter overrides onto the pip-installed files
COPY compat/openhands_sdk_overrides/fn_call_converter.py \
     /usr/local/lib/python3.12/site-packages/openhands/sdk/llm/mixins/fn_call_converter.py
COPY compat/openhands_sdk_overrides/fn_call_converter_v0.py \
     /usr/local/lib/python3.12/site-packages/openhands/sdk/llm/mixins/fn_call_converter_v0.py

# Fix permissions and invalidate bytecode caches
RUN chmod 644 /usr/local/lib/python3.12/site-packages/openhands/sdk/llm/mixins/fn_call_converter*.py && \
    find /usr/local/lib/python3.12 -name '*.pyc' -path '*/fn_call_converter*' -delete

# Replace PyInstaller binary entrypoint with system Python
USER openhands
ENTRYPOINT ["python3", "-m", "openhands.agent_server"]
