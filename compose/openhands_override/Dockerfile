FROM docker.openhands.dev/openhands/openhands:latest

COPY scripts/patch_openhands_tool_call_mode.py /opt/oh_shop/patch_openhands_tool_call_mode.py
COPY scripts/patch_openhands_external_resource_routing.py /opt/oh_shop/patch_openhands_external_resource_routing.py

RUN python /opt/oh_shop/patch_openhands_tool_call_mode.py \
    && python /opt/oh_shop/patch_openhands_external_resource_routing.py \
    && rm -f /opt/oh_shop/patch_openhands_tool_call_mode.py \
          /opt/oh_shop/patch_openhands_external_resource_routing.py
