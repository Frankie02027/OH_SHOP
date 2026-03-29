# Targeted Fix Summary

Date context: 2026-03-29

## Code changes

No repo code was changed in this pass.

## Runtime fix applied

After the failure boundary was proven, one minimal local runtime fix was applied:

```bash
lms unload --all
```

Observed result:

```text
Unloading "nebius-swe-rebench-openhands-qwen3-30b-a3b"...
Unloaded 1 model.
```

## Why this fix was justified

The sandbox stack trace showed the first completion call failed because LM Studio returned:

```text
Failed to load model "qwen3-coder-30b-a3b-instruct"
```

LM Studio server logs for the same timestamp showed the deeper cause:

```text
ggml_backend_cuda_buffer_type_alloc_buffer ... cudaMalloc failed: out of memory
llama_model_load: error loading model: unable to allocate CUDA0 buffer
Failed to load model "qwen3-coder-30b-a3b-instruct". Error: Failed to load model.
```

The local LM Studio runtime still had an idle model loaded, which left only about `1627 MiB free` on CUDA0 during the failing request.

## Proof that the fix addressed the real boundary

Before unloading:

```bash
curl -sS http://127.0.0.1:1234/v1/chat/completions ...
```

for model `qwen3-coder-30b-a3b-instruct` returned:

```json
{
  "error": {
    "message": "Failed to load model \"qwen3-coder-30b-a3b-instruct\". Error: Failed to load model."
  }
}
```

After unloading:

The exact same direct host request returned `http_status=200` and produced:

```json
{
  "model": "qwen3-coder-30b-a3b-instruct",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "Hello!"
      }
    }
  ]
}
```

## Safety

This was the smallest possible fix because:
- it did not change repo code
- it did not change Docker images
- it did not change compose
- it addressed the exact proven failing resource condition
