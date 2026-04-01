# WORKSPACE AND CONTAINER RUNTIME CONTRACT v0.1

## Status

Working contract.

This is not a frozen final infrastructure bible.
This is the current implementation contract for how the AI Garage should lay out its canonical `/workspace`, how services/containers should be separated, what each container owns, and how persistence, indexing, and file movement should work.

This contract exists to stop the Garage from becoming a trash heap of loosely mounted folders and half-defined containers.

---

## 1. Purpose

This contract defines:

- the canonical `/workspace` structure for the AI Garage
- which top-level folders exist and why
- which containers/services exist and why
- which container owns which parts of the workspace
- read/write boundaries between services
- where project files go
- where official state goes
- where memory goes
- where checkpoints go
- where artifacts go
- where downloads go
- where imports/exports go
- how Alfred and Ledger are separated
- how compose should mount and wire the runtime plane
- the implementation order for bringing this runtime plane up sanely

This contract does **not** define:

- final REST/API payload schemas
- final DB schema migration syntax
- final watchdog behavior in full detail
- final Jarvis or Robin internal reasoning policy
- final UI behavior

---

## 2. Core design position

The AI Garage should behave like:

**one canonical persistent `/workspace` root**
with
**multiple isolated containers/services**
that work together like one managed OS-style environment.

The Garage is **OS-like**, not because it replaces the host OS, but because it must provide:

- a stable root tree
- role-specific working areas
- persistent state
- indexed memory
- explicit task/job placement
- restart-safe storage
- service boundaries
- controlled file movement

The Garage must not be allowed to degrade into:

- a pile of random bind mounts
- one giant shared RW folder for every service
- a mixed bag of official and unofficial files
- a trash heap of downloads and artifacts
- state and worker scratch mixed together with no ownership model

---

## 3. Runtime philosophy

### 3.1 One visible root

Everything important inside the Garage should ultimately live under one canonical root:

`/workspace`

That root is the inside-the-garage filesystem model.

### 3.2 Separate containers, not separate worlds

Containers/services should be separated for:

- process isolation
- dependency isolation
- rebuildability
- reduced blast radius
- easier debugging

But they should still participate in one coherent Garage filesystem and one coherent task/state model.

### 3.3 Shared root does not mean shared write access

The Garage should have one visible root tree, but not every service should have broad RW access to that whole tree.

The correct model is:

- common root visibility where useful
- explicit owned subtrees
- narrow shared staging zones
- official durable state owned by Ledger
- official lifecycle control owned by Alfred

### 3.4 Official truth vs worker scratch

The runtime must preserve this distinction:

- worker scratch / local workbench state
- official recorded Garage truth

Worker scratch should live in worker-owned areas.
Official truth should only be promoted through Alfred and persisted in Ledger.

---

## 4. Service/container model

The Garage runtime should be composed of distinct services.

## 4.1 Existing service lanes

The current Garage already conceptually includes:

- `openwebui`
- `openhands`
- `stagehand`

## 4.2 Required Garage runtime services

The next serious runtime plane must include:

- `alfred`
- `ledger`
- `transfer`

## 4.3 Future or optional services

Later phases may include:

- `watchdog`
- `jarvis-runtime`
- `robin-runtime`
- backup/export helpers
- health/index helpers

These should not be overbuilt before Alfred and Ledger are real.

---

## 5. Canonical `/workspace` layout

The canonical tree should be:

```text
/workspace
  /system
    /compose
    /env
    /logs
    /health
    /run
    /tmp

  /services
    /openwebui
    /openhands
    /stagehand
    /alfred
    /ledger
    /transfer

  /roles
    /jarvis
      /sessions
      /memory
      /profiles
      /scratch
      /runtime
    /robin
      /sessions
      /memory
      /profiles
      /scratch
      /runtime
    /alfred
      /runtime
      /queues
      /checkpoints
      /manifests
      /logs

  /ledger
    /db
    /events
    /indexes
      /tasks
      /jobs
      /plans
      /checkpoints
      /continuations
      /artifacts
      /handoffs
      /memory
    /artifacts
      /by_task
      /by_job
      /by_type
      /by_date
    /downloads
      /raw
      /classified
      /quarantine
    /handoffs
      /incoming
      /outgoing
      /archived
    /memory
      /global
      /jarvis
      /robin
      /tasks
      /sessions
    /checkpoints
      /tasks
      /jobs
      /recovery
    /plans
      /active
      /history
    /tasks
      /active
      /archived
    /exports
    /imports
    /configs
    /snapshots
    /backups
    /reports

  /projects
    /active
      /<project-slug>/
        /repo
        /docs
        /inputs
        /outputs
        /artifacts
        /manifests
        /notes
        /scratch
        /checkpoints
        /runtime
    /archived

  /jobs
    /active
      /<task-id>/
        /input
        /work
        /output
        /artifacts
        /logs
        /handoffs
        /memory
        /checkpoints
        /manifests
        /runtime
    /archived

  /pobox
    /inbound
    /outbound
    /manifests
    /quarantine

  /shared
    /inbox
    /outbox
    /handoff_staging
    /download_staging
    /export_staging
    /evidence_staging
```

---

## 6. Meaning of each top-level subtree

## 6.1 `/workspace/system`

Garage-wide operational/system support files.

Use for:

- compose/runtime-generated support files
- health markers
- service run-state markers
- environment snapshots
- non-user-facing temporary operational state

Do not use for project files or official records.

## 6.2 `/workspace/services`

Service-specific private roots.

Each service may keep:

- local config
- service-private runtime files
- service-private temp state
- service-private logs when needed

Examples:

- `/workspace/services/openhands`
- `/workspace/services/stagehand`
- `/workspace/services/alfred`

This keeps service mess out of role, project, and ledger trees.

## 6.3 `/workspace/roles`

Persistent role-scoped runtime state.

### Jarvis

Use for:

- session-level continuity state
- role memory bank files
- role profile configs
- role-local scratch that is not official Garage truth
- runtime state needed specifically by the Jarvis role

### Robin

Use for:

- browser/visual role memory bank files
- Robin session continuity
- Robin role profiles
- Robin-local scratch/runtime support

### Alfred

Use for:

- Alfred runtime support state
- Alfred queue/manifests/checkpoint support files
- Alfred logs

This subtree is not the official durable ledger.
It is role-persistent state.

## 6.4 `/workspace/ledger`

Official durable record plane.

Ledger owns:

- canonical DB
- append-only event history
- indexes
- official artifact storage/indexing
- official memory storage/indexing
- checkpoints
- continuation state
- plan history
- task bundles
- imports/exports record plane
- snapshots/backups/reports

Ledger must be the place where the Garage avoids becoming a shapeless pile of files.

## 6.5 `/workspace/projects`

Long-lived project-level working space.

Use for:

- project repositories
- long-lived codebases
- project docs
- project notes
- project-specific outputs
- project-specific runtime/checkpoints

A project is not the same thing as a task/job.

## 6.6 `/workspace/jobs`

Task/job-local execution bundles.

Use for:

- task input
- active work area
- task output
- task-local artifacts
- task logs
- task-local handoffs
- task memory
- task checkpoints
- manifests
- task-runtime support files

This is where active job legs should live.

## 6.7 `/workspace/pobox`

Outside-world transfer lane.

Use for:

- inbound files from outside the Garage
- outbound files leaving the Garage
- transfer manifests
- quarantined inbound/outbound material

This is the narrow mail slot.
Not the live work area.

## 6.8 `/workspace/shared`

Narrow cross-service staging area.

Use for:

- inbox/outbox staging
- handoff staging
- download staging
- export staging
- evidence staging

Keep this narrow.
Do not let it become a second trash root.

---

## 7. Ledger structure requirements

The Ledger subtree must be treated as a structured durability plane, not a big random folder.

## 7.1 `/workspace/ledger/db`

Canonical database files.

At minimum:

- SQLite DB
- WAL files if used
- migration version markers

## 7.2 `/workspace/ledger/events`

Append-only event streams.

Use for:

- JSONL event history
- optionally sharded by date/task
- durable clerk/event trail

## 7.3 `/workspace/ledger/indexes`

Materialized, machine-friendly index structure.

Use for index views by:

- task
- job
- plan
- checkpoint
- continuation
- artifact
- handoff
- memory

This is what prevents “good luck finding the right file later.”

## 7.4 `/workspace/ledger/artifacts`

Official artifact plane.

Artifact organization must support lookup by:

- task
- job
- type
- date

This is where screenshots, extracted JSON, diff outputs, traces, proof attachments, and similar materials should live when promoted into durable official storage.

## 7.5 `/workspace/ledger/downloads`

Separate downloads by trust and state:

- `raw/`
- `classified/`
- `quarantine/`

This stops browser/download materials from immediately mixing with trusted artifacts.

## 7.6 `/workspace/ledger/handoffs`

Structured role-to-role handoff record plane.

Use for:

- incoming handoffs
- outgoing handoffs
- archived handoffs

## 7.7 `/workspace/ledger/memory`

Durable memory/index plane.

Split by:

- global
- jarvis
- robin
- tasks
- sessions

This is the place for inspectable continuity records and role/task memory bank material.

## 7.8 `/workspace/ledger/checkpoints`

Checkpoint plane.

Split by:

- tasks
- jobs
- recovery

Normal continuation checkpoints and crash recovery anchors should not be smashed together without structure.

## 7.9 `/workspace/ledger/plans`

Plan storage plane.

Split by:

- active
- history

## 7.10 `/workspace/ledger/tasks`

Task bundle plane.

Split by:

- active
- archived

## 7.11 `/workspace/ledger/configs`

Durable Garage configuration and policy storage.

Use for:

- official runtime configs
- policy tables
- role/profile mapping
- environment authority snapshots

## 7.12 `/workspace/ledger/snapshots` and `/workspace/ledger/backups`

Durability support plane.

Use for:

- snapshots
- backup bundles
- last-known-good exportable state

---

## 8. Project files vs job files

The runtime must preserve the distinction between:

- project-level durable repo/work trees
- task/job-local execution bundles

## 8.1 Project-level files go under `/workspace/projects`

Use this for:

- repos
- long-lived project docs
- project outputs
- project notes
- project checkpoints

## 8.2 Job-level files go under `/workspace/jobs`

Use this for:

- a specific active task leg
- task-local input/work/output
- job-local artifacts
- job-local logs
- job-local handoffs
- task-local memory/checkpoints/manifests

Do not collapse projects and jobs into one tree.

---

## 9. Memory placement model

The Garage needs multiple durable memory layers.

## 9.1 Role memory

Role-specific persistent memory should exist under:

- `/workspace/roles/jarvis/memory`
- `/workspace/roles/robin/memory`

These are role-scoped working memory banks.

## 9.2 Official indexed memory

Official durable memory and continuity material should be promoted/indexed under:

- `/workspace/ledger/memory/global`
- `/workspace/ledger/memory/jarvis`
- `/workspace/ledger/memory/robin`
- `/workspace/ledger/memory/tasks`
- `/workspace/ledger/memory/sessions`

## 9.3 System memory/config/history

System-level continuity, profile, and durable config data should live under:

- `/workspace/ledger/configs`
- `/workspace/system/env`
- `/workspace/system/logs`

Memory should never become one mystery folder.

---

## 10. Container/service list

The Garage runtime should use the following service model.

## 10.1 `openwebui`

Purpose:

- front door/UI/chat surface

## 10.2 `openhands`

Purpose:

- Jarvis workbench/runtime surface

## 10.3 `stagehand`

Purpose:

- Robin browser/computer-action runtime surface

## 10.4 `alfred`

Purpose:

- deterministic controller
- official state transition gatekeeper
- official clerk/stamper
- model-slot baton-pass coordinator later

## 10.5 `ledger`

Purpose:

- durable state/event/artifact-index/memory/checkpoint plane

## 10.6 `transfer`

Purpose:

- import/export broker for PO-box lane

## 10.7 optional later: `watchdog`

Purpose:

- heartbeats
- crash detection
- recovery triggers
- service health observation

---

## 11. Container ownership and mount rules

## 11.1 OpenHands container ownership

Read/write:

- `/workspace/services/openhands`
- `/workspace/roles/jarvis`
- relevant project/job trees assigned for work
- narrow shared staging zones only when needed

Read-only or limited:

- selected task/job summaries
- selected shared evidence/handoff staging

No broad direct write:

- `/workspace/ledger/db`
- `/workspace/ledger/indexes`
- `/workspace/roles/alfred`
- `/workspace/roles/robin`

## 11.2 Stagehand container ownership

Read/write:

- `/workspace/services/stagehand`
- `/workspace/roles/robin`
- narrow download/evidence staging zones
- limited assigned job subtree when needed

No broad direct write:

- official Ledger DB/index planes
- Alfred runtime tree
- Jarvis role tree

## 11.3 Alfred container ownership

Read/write:

- `/workspace/services/alfred`
- `/workspace/roles/alfred`
- `/workspace/ledger`
- narrow shared staging zones when required

Read-only or limited:

- project/job trees
- selected role state when needed for control purposes

Alfred is the only service allowed to officially promote worker output into official state through the Ledger plane.

## 11.4 Ledger container ownership

Read/write:

- `/workspace/ledger`

Ledger should not need broad write access elsewhere.

## 11.5 Transfer container ownership

Read/write:

- `/workspace/pobox`
- `/workspace/ledger/imports`
- `/workspace/ledger/exports`
- limited shared staging zones

No broad write access to project, role, or official state planes beyond transfer responsibilities.

## 11.6 OpenWebUI container ownership

Read/write:

- `/workspace/services/openwebui`

Should not need broad RW access to Garage project, role, or ledger trees.

---

## 12. Official truth promotion rules

The runtime must preserve this rule:

- workers create local scratch/work outputs in worker-owned areas
- workers do not directly mint official Garage truth
- Alfred receives official calls and stamps transitions
- Ledger stores/indexes official durable state and promoted official artifacts/memory/checkpoints

This keeps:

- worker scratch separate from official truth
- Alfred separate from Ledger
- official state inspectable and recoverable

---

## 13. How services talk to each other

The Garage should use a controlled internal service network.

At minimum, the runtime must support these logical flows:

- OpenWebUI → Jarvis/OpenHands lane
- Jarvis/OpenHands lane → Alfred
- Alfred → Ledger
- Alfred → Robin/Stagehand lane
- Robin/Stagehand lane → Alfred
- Alfred → Transfer when import/export is requested

The exact transport can evolve, but the ownership boundary must remain stable.

---

## 14. How files are read and written

## 14.1 Project files

Go under:

- `/workspace/projects/active/<project>/repo`
- related project docs/inputs/outputs/artifacts/manifests/notes/checkpoints/runtime

## 14.2 Job-local execution files

Go under:

- `/workspace/jobs/active/<task-id>/...`

## 14.3 Local worker scratch

Role-local scratch goes under:

- `/workspace/roles/jarvis/scratch`
- `/workspace/roles/robin/scratch`

and/or the assigned project/job work trees.

## 14.4 Official durable state

Goes under:

- `/workspace/ledger/...`

## 14.5 PO-box transfers

Go only through:

- `/workspace/pobox/inbound`
- `/workspace/pobox/outbound`
- `/workspace/pobox/manifests`
- `/workspace/pobox/quarantine`

---

## 15. Compose implementation requirements

The compose/runtime implementation must follow this contract.

## 15.1 Compose should create at least these additional services next

- `alfred`
- `ledger`
- `transfer`

## 15.2 Compose must mount canonical `/workspace` subtrees correctly

Do not lazily mount the entire root RW into every service.

Compose must enforce:

- per-service owned mounts
- narrow shared mounts
- explicit persistent storage roots

## 15.3 Compose must keep services on the internal Garage network

Services should communicate over a controlled internal network.
Only expose what must be exposed.

## 15.4 Compose must encode persistence roots explicitly

Environment/config must point services at canonical paths such as:

- `/workspace/ledger/db`
- `/workspace/ledger/events`
- `/workspace/projects`
- `/workspace/jobs`
- `/workspace/pobox`

## 15.5 Compose must support restart-safe persistence

Workspace mounts and volumes must preserve durable state across container restart/rebuild.

---

## 16. Implementation order

The correct implementation order is:

### Phase 1

Lock this contract and canonical `/workspace` model.

### Phase 2

Implement compose/runtime additions for:

- Alfred service
- Ledger service
- Transfer service

### Phase 3

Stand up real Alfred + Ledger runtime plane against the canonical `/workspace`.

### Phase 4

Continue Jarvis and Robin adapters against that real runtime plane.

Do not build deep Jarvis/Robin runtime behavior against a fake or undefined storage/runtime world.

---

## 17. Non-goals for this phase

This phase is not for:

- building the full watchdog service
- full backup orchestration
- final recovery automation
- final network/API standardization
- final model-slot switching controller
- final policy engine

This phase is for:

- getting the workspace tree right
- getting service boundaries right
- getting mounts/ownership right
- standing up Alfred and Ledger as real runtime services

---

## 18. Acceptance criteria

This contract is implemented correctly only if:

1. the Garage has one canonical persistent `/workspace` root
2. Alfred and Ledger are separate service boundaries
3. official truth and worker scratch are not mixed together casually
4. Ledger structure is indexed enough to avoid a trash heap
5. project files and job files are separated
6. role memory and official indexed memory are separated
7. PO-box remains a narrow import/export lane
8. compose mounts reflect ownership instead of broad sloppy RW access
9. the system is ready for Alfred + Ledger runtime bring-up

---

## 19. Final contract position

The AI Garage runtime should behave like one managed OS-style workspace with multiple cooperating services.

That means:

- one canonical `/workspace`
- structured subtrees
- role separation
- service isolation
- explicit write ownership
- Alfred as deterministic controller
- Ledger as durable indexed plane
- worker scratch separated from official truth
- PO-box kept narrow
- compose derived from real ownership rules, not random mounts

If this contract is ignored, the Garage will drift into a confusing pile of shared folders and fragile container behavior.
If this contract is followed, the Garage will have a sane foundation for the next real implementation stages.

