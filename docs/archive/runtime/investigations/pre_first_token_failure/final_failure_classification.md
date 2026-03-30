# Final Failure Classification

Date context: 2026-03-29

## Direct statement

Outcome: **fixed and proven**

The exact pre-first-token failure was:
- **first model dispatch failure**

The failing component was:
- **LM Studio model loading**, reached from the sandbox's first OpenAI-compatible completion request

The exact failure mechanism was:
- LM Studio attempted to load `qwen3-coder-30b-a3b-instruct`
- CUDA allocation failed with out-of-memory
- LM Studio returned HTTP 400 `Failed to load model`
- LiteLLM surfaced that as `BadRequestError`
- OpenHands wrapped it as `LLMBadRequestError` / `ConversationRunError`
- the sandbox conversation flipped from `running` to `error`

## Classification by the requested buckets

This pass rules out:
- sandbox bootstrap failure
- OpenHands app ↔ sandbox protocol failure
- agent-server import/runtime failure
- config/settings injection failure
- MCP/tool registration failure
- conversation/event propagation failure

This pass identifies:
- **first model dispatch failure**

## Internal vs external

This was **not** an internal repo-code defect inside OH_SHOP.

It was a local runtime-state failure in LM Studio:
- an idle loaded model consumed GPU memory
- the configured model could not be loaded for the first completion request

## Proof after minimal fix

After:

```bash
lms unload --all
```

the exact failing model completed successfully through the host API, and the canonical proof rerun succeeded.

See:
- `docs/pre_first_token_failure/proof_rerun_after_targeted_fix.md`

## Bottom line

The pre-first-token blocker is resolved.

The repo baseline did not need another code patch for this failure lane.
The exact issue was local LM Studio loaded-model state causing first-dispatch CUDA OOM during the smoke proof.
