# Target Repo Tree

Date context: 2026-03-29

## Intended structure

```text
.
├── compose/              # live compose and image overrides
├── scripts/              # live operator wrappers and repair tools
├── compat/               # explicit compatibility debt and vendor overlays
├── vendor/               # active vendored runtime support code
├── workspace/            # only subtree mounted into OpenHands sandboxes
├── data/                 # runtime persistence
├── downloads/            # browser/download output
├── artifacts/            # backups, benchmarks, raw evidence
├── docs/
│   ├── current/          # current operator-facing docs
│   ├── runtime/          # stabilization/normalization/investigation evidence
│   ├── architecture/     # future target design
│   ├── research/         # audits and deep reports
│   └── archive/          # old contracts/plans no longer authoritative
└── archive/              # quarantined code, placeholders, and upstream snapshots
```

## Folder rationale

- `compose/`
  - keeps the canonical runtime/build path stable.
  - only live service definitions and image overrides belong here.

- `scripts/`
  - keeps the canonical operator commands stable.
  - contains only wrappers or operational helpers, not benchmark harnesses or random experiments.

- `compat/`
  - isolates active compatibility debt from normal runtime source.
  - makes it obvious which files are shims rather than clean architecture.

- `vendor/`
  - holds active vendored support code that the runtime genuinely builds from.
  - avoids pretending vendored runtime support is a user repo.

- `workspace/`
  - is the only host subtree mounted into sandbox workspaces.
  - separates user/task repos from vendored/runtime code.

- `docs/current/`
  - is the only operator-facing current doc surface.

- `docs/runtime/`
  - keeps runtime evidence and investigations together.
  - these are active records, not future architecture.

- `docs/architecture/`
  - keeps future-state Alfred/Ledger/Garage design docs out of runtime truth.

- `docs/research/`
  - keeps audits and deep reports available without letting them masquerade as the current operational baseline.

- `docs/archive/`
  - makes stale contracts historical instead of silently authoritative.

- `archive/`
  - removes dead or future-only code from the live-looking root.

## Naming choices

- I did **not** rename `compose/` or `scripts/` because the canonical runtime commands already depend on them and those names are now honest enough.
- I **did** replace the overloaded `repos/` concept with:
  - `workspace/` for sandbox-exposed work
  - `vendor/` for active vendored runtime code
  - `archive/` for reference and dead paths
