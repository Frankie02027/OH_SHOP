# Full Repo Inventory

Date context: 2026-03-29

This inventory reflects the repo **after** the restructure, with notes where a subtree is intentionally archival or historical.

## Root surface

```text
.
├── .flake8
├── .gitignore
├── archive/
├── artifacts/
├── compat/
├── compose/
├── data/
├── docs/
├── downloads/
├── ops/
├── vendor/
└── workspace/
```

Hidden local-environment paths that are present but not repo product surface:
- `.git/`
- `.venv/`
- `.vscode/`
- `.openhands/`

## Active runtime and ops tree

```text
compose/
├── docker-compose.yml
├── agent_server_override/
│   └── Dockerfile
└── openhands_override/
    ├── Dockerfile
    └── apply_runtime_patches.py

ops/
├── garagectl.py
└── manual/
    ├── chat_guard.py
    └── lmstudio-docker-dnat.sh

compat/
├── README.md
└── openhands_sdk_overrides/
    ├── fn_call_converter.py
    └── fn_call_converter_v0.py

vendor/
└── stagehand_mcp/
    ├── .env.example
    ├── Dockerfile
    ├── README.md
    ├── package.json
    ├── package-lock.json
    ├── tsconfig.json
    └── src/
        ├── server.ts
        └── smoke.ts

workspace/
├── .openhands_instructions
└── README.md

data/
└── openhands/
    ├── settings.json
    ├── openhands.db
    ├── .jwt_secret
    ├── .keys
    └── v1_conversations/

downloads/
└── (runtime browser/download output)
```

## Docs tree

```text
docs/
├── architecture/
│   ├── AI_GARAGE_BLUEPRINT.MD.md
│   ├── MEMORY_SYSTEM_CONTRACT.md
│   ├── Phase_A.md
│   └── ai_garage_library_and_policy_contract_v_0_1.md
├── archive/
│   ├── authoritative_rework_contract_2026-03-21.md
│   ├── cleanup_plan_2026-03-21.md
│   ├── oh_shop_full_browser_replacement_with_stagehand.md
│   ├── open_hands_open_web_ui_local_agent_house_contract_v_1.md
│   ├── phase_1_consolidated_oh_shop.md
│   ├── phase_1_copilot_implementation_plan_next_steps.md
│   ├── phase_2_review_pack_artifacts.md
│   └── ubuntu-25.10-live-server-amd64.iso.torrent
├── current/
│   ├── SECURITY.md
│   ├── SETUP.md
│   └── TROUBLESHOOTING.md
├── research/
│   ├── agenticseek_integration_report_2026-03-22.md
│   ├── deep-research-report_#1.md
│   ├── deep-research-report_#2.md
│   ├── independent_audit_2026-03-21.md
│   ├── openhands_capabilities_audit_2026-03-22.md
│   ├── openhands_handoff_2026-03-22.md
│   └── stack_audit_2026-03-21.md
├── runtime/
│   ├── runtime_stabilization_contract_v_0.md
│   ├── normalization/
│   ├── stabilization/
│   │   └── final_reply_investigation/
│   ├── investigations/
│   │   └── pre_first_token_failure/
│   └── templates/
└── repo_reaudit_restructure/
    └── (this pass)
```

Runtime docs are kept because they are active evidence sets, but several of those files record **pre-restructure** path names. The authoritative current tree map for path layout is this directory, not the earlier pass artifacts.

## Archive tree

```text
archive/
├── README.md
├── bridge/
│   ├── model_router/
│   │   ├── package.json
│   │   ├── router.ts
│   │   └── start.sh
│   └── openapi_server/
│       └── README.md
├── reference/
│   └── OpenHands/
├── runtime_fixtures/
│   └── compose_phase1_fixture/
├── samples/
│   ├── calculator/
│   ├── sieve.py
│   └── test_images/
└── vendor_snapshots/
    └── stagehand_working/
```

## Artifacts tree

```text
artifacts/
├── backups/
├── benchmark_results/
├── benchmarks/
│   ├── benchmark_runner.py
│   ├── archives/
│   ├── humaneval/
│   ├── images/
│   ├── large_complex/
│   ├── mbpp/
│   ├── real_bugs/
│   ├── swe-bench/
│   └── test_levels/
├── capability_tests/
├── openhands/
└── runtime_evidence/
    └── pre_first_token_failure/
```

## Deleted local junk in this pass

- root `plaintext.txt`
- `compose/openhands_override/__pycache__/`
- `scripts/__pycache__/`
- generated Stagehand clutter from the copied monorepo snapshot before archiving:
  - `.pnpm-store/`
  - root `node_modules/`
  - `packages/mcp/node_modules/`
  - `packages/mcp/dist/`
  - `.vscode/`
