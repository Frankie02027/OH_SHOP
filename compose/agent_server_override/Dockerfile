FROM ghcr.io/openhands/agent-server:61470a1-python

USER root

# Install the three openhands packages from PyPI at matching version
# so we have real importable Python source instead of the frozen PyInstaller binary
RUN pip install --break-system-packages --no-cache-dir \
      openhands-agent-server==1.11.4 \
      openhands-sdk==1.11.4 \
      openhands-tools==1.11.4 && \
    python3 -c "import openhands.sdk.llm.mixins.fn_call_converter; print('SDK converter OK')"

# Overlay our patched converters onto the pip-installed files
COPY vendor_sdk/fn_call_converter.py \
     /usr/local/lib/python3.12/site-packages/openhands/sdk/llm/mixins/fn_call_converter.py
COPY vendor_sdk/fn_call_converter_v0.py \
     /usr/local/lib/python3.12/site-packages/openhands/sdk/llm/mixins/fn_call_converter_v0.py

# Fix permissions and invalidate bytecode caches
RUN chmod 644 /usr/local/lib/python3.12/site-packages/openhands/sdk/llm/mixins/fn_call_converter*.py && \
    find /usr/local/lib/python3.12 -name '*.pyc' -path '*/fn_call_converter*' -delete

# Replace PyInstaller binary entrypoint with system Python
USER openhands
ENTRYPOINT ["python3", "-m", "openhands.agent_server"]
