# PERSISTED RECORD AND STORAGE OBJECT CONTRACT v0.1
## AI Garage Persisted Record / Storage Object Contract

## Status

Working draft.

This is not final.
It is the first serious contract for Garage persisted-record and storage-boundary objects.

This contract exists because the repo already has:
- role contracts
- the shared language dictionary
- the library schema contract
- tracked-plan, handoff, artifact/proof, policy-table, and call/event object contracts

Those authorities already define:
- runtime call objects
- runtime event objects
- tracked plans
- policy records
- artifact refs and proof refs

What the repo still did not have was one explicit contract for the persisted-record layer that sits between:
- runtime objects in motion
- durable storage/index objects
- later SQLite tables / JSON Schema files / adapter code

This document does **not** replace:
- `CALL_AND_EVENT_OBJECT_CONTRACT_v_0_1.md`
- `TRACKED_PLAN_OBJECT_CONTRACT_v_0_1.md`
- `ARTIFACT_AND_PROOF_CONTRACT_v_0_1.md`
- `POLICY_TABLE_CONTRACT_v_0_1.md`
- `LIBRARY_SCHEMA_CONTRACT_v_0_1.md`

It narrows and operationalizes the persisted-record/storage object layer those authorities already imply.

---

## 1. Purpose

This contract defines the Garage persisted-record and storage object layer.

It governs:
- what a persisted record is
- what storage-boundary objects are
- how runtime call/event objects relate to durable records
- the difference between in-flight runtime objects and persisted records
- the minimum record families the Garage should preserve durably
- record identity, linkage, timestamps, status posture, and ref posture at the durable layer
- where content should be copied, indexed, or referenced
- what must remain pointer-first instead of turning the clerk layer into a warehouse
- implementation-facing object organization before raw schema or DDL authoring

It does **not** govern:
- final SQLite DDL
- final filesystem layout
- final storage engine choice beyond the already accepted general posture
- final retention windows for every object family
- final backup tooling
- final migration code

---

## 2. Primary authority relationship

## 2.1 Library/schema authority
`LIBRARY_SCHEMA_CONTRACT_v_0_1.md` remains the schema-layer authority for:
- overall schema organization
- shared object schema expectations
- per-call and per-event schema expectations

## 2.2 Call/event object authority
`CALL_AND_EVENT_OBJECT_CONTRACT_v_0_1.md` remains the runtime object authority for:
- what a call object is
- what an event object is
- how calls differ from events
- call-to-event transformation posture

## 2.3 Tracked-plan authority
`TRACKED_PLAN_OBJECT_CONTRACT_v_0_1.md` remains the authority for:
- plan headers/items
- plan-specific state logic
- verification-rule and evidence-ref usage

## 2.4 Artifact/proof authority
`ARTIFACT_AND_PROOF_CONTRACT_v_0_1.md` remains the authority for:
- artifact vs evidence vs proof
- `artifact_ref`, `workspace_ref`, and `payload_ref`
- proof-bearing linkage posture

## 2.5 Policy-table authority
`POLICY_TABLE_CONTRACT_v_0_1.md` remains the authority for:
- standing policy records
- policy scope/version/status/content linkage

This contract must align with all of them.

---

## 3. Why this layer exists

The repo now has enough contract structure to start coding.
But there is still one easy place to screw it up during implementation:
- blurring runtime objects with persisted records
- storing giant raw bodies everywhere because the durable boundary was never defined
- turning Alfred/Ledger into a shapeless dump of partially duplicated objects
- mixing event history, state snapshots, artifact indexes, policy rows, and live runtime objects into one bag

This layer exists so the Garage can say, explicitly:
- which object families are runtime-only
- which object families are persisted durably
- which persisted families are canonical state snapshots
- which persisted families are append-only history
- which objects should usually be referenced rather than copied inline

---

## 4. Core distinction: runtime object vs persisted record

## 4.1 Runtime object
A runtime object is an object in motion or immediate use during workflow execution.

Examples:
- call object
- event object before/at record creation boundary
- in-flight handoff envelope
- temporary worker payload body

## 4.2 Persisted record
A persisted record is the durable storage-layer object written so the Garage can:
- reconstruct state later
- inspect history later
- resume work later
- audit what happened later

A persisted record is not merely “whatever JSON happened to exist during execution.”

## 4.3 Design rule
The persisted layer should preserve meaning and linkage from runtime objects without collapsing the two layers into one identical blob by default.

---

## 5. Persisted record families

The Garage should preserve a minimum serious set of durable record families.

## 5.1 Required persisted record families
- task record
- job record
- event record
- checkpoint record
- tracked-plan record
- plan-item state/history record
- artifact index record
- continuation record
- policy record

## 5.2 Optional but recommended supporting record families
- task-state snapshot record
- active-plan pointer record
- proof-bundle record
- route-history record
- policy-activation history record
- supersession/replacement linkage record

## 5.3 Anti-drift rule
Do not create twenty storage families on day one just because you can.
But also do not pretend task/job/event history alone is enough for clean resumption.

---

## 6. Canonical state vs append-only history

The persisted layer needs both.

## 6.1 Canonical state records
These answer “what is the current authoritative state now?”

Examples:
- current task record
- current job record
- current active plan pointer
- current active policy record by scope

## 6.2 Append-only history records
These answer “what happened over time?”

Examples:
- event record history
- plan revision history
- policy activation history
- checkpoint history

## 6.3 Design rule
Do not confuse canonical state with the full history trail.
The Garage needs both current truth and historical truth.

---

## 7. Task record

## 7.1 Purpose
Represents the durable umbrella mission record.

## 7.2 Required minimum fields
- `task_id`
- `task_state`
- `created_at`

## 7.3 Recommended additional fields
- `current_job_id`
- `current_plan_version`
- `latest_checkpoint_id`
- `latest_continuation_ref`
- `updated_at`
- `summary_ref`

## 7.4 Meaning
The task record is the canonical durable state object for the umbrella mission, not merely one event copied out of history.

---

## 8. Job record

## 8.1 Purpose
Represents one durable work-leg record.

## 8.2 Required minimum fields
- `job_id`
- `task_id`
- `job_state`
- `created_at`

## 8.3 Recommended additional fields
- `parent_job_id`
- `attempt_no`
- `from_role`
- `to_role`
- `last_reported_status`
- `updated_at`
- `latest_event_id`

## 8.4 Meaning
The job record is canonical state for one work leg.
It is not the same thing as the individual return/failure events associated with that leg.

---

## 9. Event record

## 9.1 Purpose
Represents one durable append-only factual history record.

## 9.2 Required minimum fields
- `event_id`
- `event_type`
- `task_id`
- `recorded_at`

## 9.3 Usually required in practical use
- `job_id`

## 9.4 Recommended additional fields
- `checkpoint_id`
- `from_role`
- `to_role`
- `related_call_type`
- `reported_status`
- `artifact_refs`
- `workspace_refs`
- `payload_ref`

## 9.5 Meaning
The event record is the durable append-only history spine.
It must stay factual and must not become a semantically rewritten diary blob.
For v0.1, `event-record` is intentionally field-aligned with `event-object`; the distinction is durable role, not a second divergent payload shape.

---

## 10. Checkpoint record

## 10.1 Purpose
Represents one durable resume anchor.

## 10.2 Required minimum fields
- `checkpoint_id`
- `task_id`
- `created_at`

## 10.3 Recommended additional fields
- `job_id`
- `plan_version`
- `current_active_item`
- `key_ref_bundle`
- `reason`
- `resume_point`

## 10.4 Meaning
A checkpoint record is not proof of completion.
It is a durable resume anchor with enough linkage to restart sanely.

---

## 11. Tracked-plan persisted records

## 11.1 Plan header record
The durable plan header should preserve:
- `task_id`
- optional `job_id`
- `plan_version`
- `plan_status`
- `current_active_item`
- timestamps

## 11.2 Plan-item state/history record
The durable layer should make it possible to recover:
- item state now
- evidence refs now
- verification rule linkage
- prior state changes when needed

## 11.3 Design rule
The tracked plan remains a first-class durable execution object and should not be flattened into generic note storage.

---

## 12. Continuation record

## 12.1 Purpose
Represents a durable continuation/resumption note.

## 12.2 Required minimum fields
- `task_id`
- `created_at`
- `content_ref`

## 12.3 Recommended additional fields
- `job_id`
- `plan_version`
- `checkpoint_id`
- `artifact_refs`
- `workspace_refs`

## 12.4 Meaning
The continuation record is durable resumability metadata, not a freeform chat residue object.

---

## 13. Artifact index record

## 13.1 Purpose
Represents the durable index object for an artifact.

## 13.2 Required minimum fields
- `artifact_id`
- `kind`
- `reported_by`
- `workspace_ref`

## 13.3 Recommended additional fields
- `task_id`
- `job_id`
- `created_at`
- `hash`
- `size_bytes`
- `mime_type`
- `description`

## 13.4 Design rule
The artifact index record is pointer-first.
It should not force Garage storage to duplicate every raw file unless later storage policy says so.

---

## 14. Policy persisted records

The policy table contract already governs policy records.
This storage contract simply fixes their place in the broader durable layer.

## 14.1 Required durable posture
The persisted layer must retain enough to answer:
- what policy was active
- for what scope
- at what version
- with what linked content

## 14.2 Anti-drift rule
Do not store role policy only as loose markdown with no durable activation/index linkage.
That was already rejected at the policy-table layer.

---

## 15. Snapshot objects vs linkage objects

## 15.1 Snapshot objects
These preserve current consolidated state.

Examples:
- current task state snapshot
- current job state snapshot
- active plan pointer snapshot

## 15.2 Linkage objects
These preserve many-to-one or historical linkage.

Examples:
- task-to-job linkage
- job-to-artifact linkage
- plan-item-to-evidence linkage
- policy-to-task-override linkage

## 15.3 Design rule
The implementation may collapse some linkage into tables later, but the conceptual distinction should remain explicit now.

---

## 16. Pointer-first storage posture

The Garage has already chosen a pointer-first posture in multiple places.
This contract keeps that hard line.

## 16.1 Prefer refs for large bodies
Prefer:
- `artifact_ref`
- `workspace_ref`
- `payload_ref`
- `content_ref`

when the alternative is duplicating large raw content into canonical records for no reason.

## 16.2 Inline storage is still allowed when sane
Small, clean metadata or concise summaries may still be stored inline.

## 16.3 Anti-drift rule
Do not turn Alfred/Ledger into a shapeless warehouse of copied blobs just because storage is available.

---

## 17. Content object vs record object

## 17.1 Record object
A record object answers identity, linkage, status, timestamps, and pointers.

## 17.2 Content object
A content object is the actual body content when that content is externalized.

Examples:
- continuation body markdown
- policy body markdown
- large result payload file

## 17.3 Design rule
Separate record metadata from large body content when that separation improves clarity and avoids duplication.

---

## 18. Timestamps and supersession

## 18.1 Minimum timestamp posture
Serious persisted records should preserve:
- `created_at`
- and where relevant `updated_at` or `recorded_at`

## 18.2 Supersession posture
Where a later record replaces an earlier authoritative one, the durable layer should make that lineage recoverable.

Examples:
- plan version superseding earlier plan version
- policy version superseding earlier active policy
- materially new job superseding earlier job leg

---

## 19. What must remain recoverable

After a crash, restart, or later audit, the durable layer should be able to answer:
- what task was active
- what job was active
- what plan version was current
- what checkpoint existed
- what continuation note was latest
- what policy was active by scope
- what artifacts and proof refs were linked to the current work
- what events happened in what order

If the persisted layer cannot answer those questions, it is not serious enough yet.

---

## 20. What belongs outside this layer

The following must not be collapsed into generic persisted storage objects without discipline:
- raw worker scratchpads
- UI-only local view state
- substrate-specific adapter internals
- arbitrary temp files with no official linkage

The persisted layer is the durable Garage record plane, not a garbage drawer.

---

## 21. Alfred and Ledger roles at this layer

## 21.1 Alfred
Alfred owns:
- deciding what official record should be written
- stamping IDs and linkage
- creating event history
- maintaining canonical route/state transitions

## 21.2 Ledger
Ledger owns:
- durable storage/indexing
- current-state records
- history records
- record linkage and retrieval

## 21.3 Design rule
Do not collapse Alfred’s clerk role and Ledger’s durable storage role into one conceptual mush even if early implementation sits close together.

---

## 22. Implementation-facing object organization guidance

Recommended future schema/object organization:

```text
schemas/objects/
  task-record.schema.json
  job-record.schema.json
  event-record.schema.json
  checkpoint-record.schema.json
  continuation-record.schema.json
  artifact-index-record.schema.json
  state-snapshot-record.schema.json
  linkage-record.schema.json
```

Potential implementation order:
1. task record
2. job record
3. event record
4. checkpoint record
5. continuation record
6. artifact index record
7. supporting snapshot/linkage records only where needed

---

## 23. Good vs bad usage

## 23.1 Good usage
Good usage means:
- runtime calls stay runtime objects
- durable records stay durable records
- canonical state and append-only history are separated conceptually
- large bodies remain pointer-first where appropriate
- checkpoints and continuation records stay resumability-focused
- artifact index records point cleanly to proof-bearing objects without copying everything inline

## 23.2 Bad usage
Bad usage includes:
- storing every call body inline in every event record forever
- treating the event log as the only source of current state
- treating current state rows as a substitute for append-only history
- duplicating raw artifacts everywhere with no retention discipline
- turning Ledger into a shapeless pile of half-related JSON blobs

---

## 24. Final position

The Garage now has enough runtime and policy contract structure that one final “be safe” storage contract is reasonable.

The persisted layer should preserve, explicitly:
- canonical current state
- append-only history
- resumability anchors
- artifact/proof indexes
- policy linkage
- pointer-first content boundaries

That is the minimum serious persisted-record/storage object discipline before schema or storage implementation hardcodes bad assumptions.
