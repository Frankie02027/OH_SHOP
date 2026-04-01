# AI Garage Canonical Workspace Root

This directory is the canonical persistent `/workspace` root for the AI Garage runtime plane.

It is **not** only an OpenHands sandbox base anymore.
It is the shared runtime filesystem model that separates:

- service-private state
- role-persistent state
- official ledger durability
- long-lived project trees
- task/job execution bundles
- the PO-box transfer lane
- narrow shared staging zones

## Top-level structure

```text
workspace/
  system/
  services/
  roles/
  ledger/
  projects/
  jobs/
  pobox/
  shared/
```

## Practical rules

- `roles/jarvis` and `roles/robin` hold worker-local persistent state, scratch, and profiles.
- `roles/alfred` holds Alfred runtime support files only; it is **not** the durable ledger.
- `ledger/` is the official durability plane for DB, event history, indexes, checkpoints, plans, memory, and promoted artifacts.
- `projects/active/<project>/repo` is where long-lived repos belong.
- `jobs/active/<task-id>/...` is where task/job-local execution bundles live.
- `pobox/` is the narrow import/export lane.
- `shared/` stays narrow; it is not a second trash-root.

## Bootstrap

The runtime plane bootstrap is:

```bash
python3 ops/garage_workspace_bootstrap.py
```

That command will create the canonical directory tree, write a workspace manifest, and leave a bootstrap marker under `system/health/`.

## Baseline capture before rewiring

Before destructive runtime-plane rewiring, capture a baseline snapshot:

```bash
python3 ops/garage_baseline_snapshot.py
```

That snapshot lands under `ledger/snapshots/` and preserves the current compose/runtime story before the new services are brought up.
