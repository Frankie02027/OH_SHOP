#!/bin/bash
# Start the model router proxy
# Routes requests between text model (30B) and VL model for browser tasks

cd /home/dev/OH_SHOP/bridge/model_router
exec bun run router.ts
