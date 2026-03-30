# CALL AND EVENT OBJECT CONTRACT v0.1
## AI Garage Runtime Call / Event Object Contract

## Status

Working draft.

This is not final.
It is the first serious contract for the Garage runtime call and event object layer.

This contract exists because the repo already has:
- a higher-level library/policy contract
- a universal language dictionary
- a library schema contract
- role contracts
- tracked-plan, handoff, artifact/proof, and policy-table contracts

Those authorities already define:
- official call types
- official event types
- official shell fields
- official IDs and linkage rules
- the difference between runtime language and standing policy

What was still missing was one explicit contract for the concrete runtime object layer that sits between:
- high-level language authority
- later raw JSON Schema files
- later persistence/runtime implementation objects

This document does **not** replace:
- `garage_universal_language_dictionary_v0_1.md`
- `LIBRARY_SCHEMA_CONTRACT_v_0_1.md`
- `HANDOFF_ENVELOPE_CONTRACT_v_0_1.md`
- `TRACKED_PLAN_OBJECT_CONTRACT_v_0_1.md`

It narrows and operationalizes the implementation-facing object layer those authorities already imply.

---

## 1. Purpose

This contract defines the official Garage runtime call and event objects.

It governs:
- what a call object is
- what an event object is
- how call objects differ from event objects
- required and optional object fields at the object-contract layer
- how call/event objects relate to shell fields, refs, payloads, and linkage
- how calls become events
- how event history should stay factual and append-only
- what belongs in runtime call/event objects versus tracked plans, policy records, or artifacts
- implementation-facing object organization guidance before raw JSON Schema authoring

It does **not** govern:
- final transport protocol
- final SQLite DDL
- final JSON Schema syntax details
- final REST route shapes
- final adapter implementation code
- semantic truth of worker-authored body content

---

## 2. Primary authority relationship

## 2.1 Dictionary authority
`garage_universal_language_dictionary_v0_1.md` remains the primary authority for:
- official `call_type` names
- official `event_type` names
- official status tokens
- official shell field names
- official ID classes
- retry vs same-job return vs new-job rules

This contract must not silently rename those tokens.

## 2.2 Library schema contract authority
`LIBRARY_SCHEMA_CONTRACT_v_0_1.md` remains the schema-layer authority for:
- the base envelope schema set
- per-call schema expectations
- event schema expectations
- shared object schema organization

## 2.3 Handoff-envelope authority
`HANDOFF_ENVELOPE_CONTRACT_v_0_1.md` remains the authority for:
- shell vs body split
- field ownership by layer
- route/linkage shell posture

## 2.4 Tracked-plan authority
`TRACKED_PLAN_OBJECT_CONTRACT_v_0_1.md` remains the authority for:
- plan header/item structure
- plan-specific state and verification logic

## 2.5 Policy-table authority
`POLICY_TABLE_CONTRACT_v_0_1.md` remains the authority for:
- standing policy records
- active/inactive policy status
- policy scope/version/content linkage

This contract must align with all of them.

---

## 3. Why this object layer must exist

The repo already knows the runtime vocabulary.
What it did not yet have was one contract that says, concretely:
- what the official runtime call object looks like as an object
- what the official runtime event object looks like as an object
- what fields they share
- what fields they do not share
- how a call becomes a recorded event trail without collapsing the two concepts together

Without this layer, implementation tends to drift into:
- treating calls and events as the same object
- overloading event history with worker-authored payload meaning
- shoving persistence concerns into the envelope without a clean model
- inventing ad hoc fields during coding because the object boundary was never narrowed first

---

## 4. Core distinction: call object vs event object

## 4.1 Call object
A call object is the official runtime request/return object moving through the Garage workflow.

A call object answers:
- what kind of runtime call this is
- which task/job it belongs to
- who sent it
- who should receive it
- what worker-reported status is attached if applicable
- what refs or payload are attached

Examples:
- `task.create`
- `plan.record`
- `job.start`
- `child_job.request`
- `result.submit`
- `failure.report`
- `checkpoint.create`
- `continuation.record`

## 4.2 Event object
An event object is Alfred’s official recorded fact trail.

An event object answers:
- what fact was recorded
- which task/job/checkpoint it relates to
- when it was recorded
- which event ID it got
- which refs or route metadata were captured

Examples:
- `task.created`
- `plan.recorded`
- `job.created`
- `job.started`
- `job.dispatched`
- `job.returned`
- `job.blocked`
- `job.failed`
- `checkpoint.created`
- `continuation.recorded`
- `artifact.registered`

## 4.3 Design rule
Calls are runtime interaction objects.
Events are append-only recorded facts.

Do not collapse them into one vague “message” blob.

---

## 5. Call object

## 5.1 Minimum required call-object fields
- `schema_version`
- `call_type`
- `task_id`
- `job_id`
- `from_role`
- `to_role`

## 5.2 Conditional / call-dependent call-object fields
- `parent_job_id`
- `reported_status`
- `reported_at`
- `attempt_no`
- `artifact_refs`
- `workspace_refs`
- `payload`
- `payload_ref`

## 5.3 Recommended full call-object field set
- `schema_version`
- `call_type`
- `task_id`
- `job_id`
- `parent_job_id`
- `from_role`
- `to_role`
- `reported_status`
- `reported_at`
- `attempt_no`
- `artifact_refs`
- `workspace_refs`
- `payload`
- `payload_ref`

## 5.4 Meaning
A call object is the official runtime envelope plus worker-authored body pointer/body content.
It is not the same thing as the later recorded event.

---

## 6. Event object

## 6.1 Minimum required event-object fields
- `event_id`
- `event_type`
- `task_id`
- `recorded_at`

## 6.2 Usually required in practical runtime use
- `job_id`
- route/linkage metadata where relevant

## 6.3 Recommended additional event-object fields
- `job_id`
- `checkpoint_id`
- `from_role`
- `to_role`
- `related_call_type`
- `reported_status`
- `artifact_refs`
- `workspace_refs`
- `payload_ref`
- `notes`

## 6.4 Meaning
An event object is Alfred’s official recorded fact object.
It should remain factual and append-only.

---

## 7. Shared object-field posture

Call and event objects overlap, but they are not identical.

## 7.1 Shared linkage fields
Both may carry:
- `task_id`
- `job_id`
- `parent_job_id` where appropriate
- `artifact_refs`
- `workspace_refs`

## 7.2 Call-only core fields
These are core to call objects:
- `call_type`
- `payload` / `payload_ref`
- `from_role`
- `to_role`

## 7.3 Event-only core fields
These are core to event objects:
- `event_id`
- `event_type`
- `recorded_at`

## 7.4 Anti-drift rule
Do not require every event object to carry the full original call body inline.
Prefer references or summarized factual linkage.

---

## 8. Official call library at the object layer

The object layer uses the existing required call library.

## 8.1 Required call-object families
- `task.create`
- `plan.record`
- `job.start`
- `child_job.request`
- `checkpoint.create`
- `continuation.record`
- `result.submit`
- `failure.report`

## 8.2 Optional/deferred families
- `assignment.dispatch`
- `assignment.accept`

These remain optional/deferred unless explicitly promoted later.

---

## 9. Official event library at the object layer

The object layer uses the existing core event set.

## 9.1 Required event-object families
- `task.created`
- `plan.recorded`
- `job.created`
- `job.started`
- `job.dispatched`
- `job.returned`
- `job.blocked`
- `job.failed`
- `checkpoint.created`
- `continuation.recorded`
- `artifact.registered`

## 9.2 Design rule
Events are factual official records, not substitutes for the original call body.

---

## 10. Route and linkage rules

## 10.1 `task_id`
Both call and event objects must remain anchored to the umbrella mission.

## 10.2 `job_id`
Call objects normally require `job_id` in serious runtime use.
Event objects should carry `job_id` whenever the fact concerns a specific work leg.

## 10.3 `parent_job_id`
Use when lineage matters:
- child job origin
- materially new refined job following an older job
- retry/replacement linkage context

## 10.4 `attempt_no`
Belongs primarily to call objects.
May be copied into an event object when needed to preserve retry fact history.

---

## 11. Same-job return, retry, and new-job invariants

This contract preserves the fixed runtime invariants.

## 11.1 Same-job return rule
A `result.submit` or `failure.report` call uses the same `job_id` as the job being returned for.

## 11.2 Retry rule
Retry of the same job uses:
- same `job_id`
- incremented `attempt_no`

## 11.3 New refined job rule
A materially new or refined request gets:
- new `job_id`
- optional `parent_job_id` link to the earlier job

## 11.4 Anti-drift rule
The object layer must not blur these three situations together.

---

## 12. Status posture

## 12.1 Worker-reported status
`reported_status` on call objects is a worker claim, not Alfred truth.
Allowed values remain:
- `succeeded`
- `partial`
- `blocked`
- `failed`

## 12.2 Event posture
An event object may record the fact that a worker reported a given status, but the event itself should remain a factual record object.

## 12.3 Anti-drift rule
Do not make event type and worker-reported status compete for the same meaning.
Both may appear, but they are not the same field and not the same layer.

---

## 13. Payload posture

## 13.1 Call objects
Call objects may carry:
- inline `payload`
- or external `payload_ref`

depending on size and cleanliness.

## 13.2 Event objects
Event objects should normally prefer:
- `payload_ref`
- or factual summary linkage

rather than embedding full original bodies inline.

## 13.3 Anti-drift rule
Do not turn the event log into the full body warehouse.
That is not what events are for.

---

## 14. Refs posture

## 14.1 `artifact_refs`
Use to point at officially identified artifacts.

## 14.2 `workspace_refs`
Use to point at reported object locations when needed.

## 14.3 `payload_ref`
Use to point at externalized call bodies or other worker-owned content.

## 14.4 Design rule
Refs belong in both call/event object design where relevant, but they should stay pointers, not raw embedded object dumps.

---

## 15. Call-to-event transformation rule

## 15.1 Principle
Calls move through the workflow.
Alfred records events about what happened with those calls.

## 15.2 Example mapping posture
- `task.create` call -> `task.created` event
- `plan.record` call -> `plan.recorded` event
- `job.start` call -> `job.started` event
- `result.submit` call -> `job.returned` event
- `failure.report` call -> `job.blocked` or `job.failed` event depending on recorded outcome
- `checkpoint.create` call -> `checkpoint.created` event
- `continuation.record` call -> `continuation.recorded` event

## 15.3 Anti-drift rule
Do not assume the event is merely a dumb copy of the call.
The event is a recorded fact about workflow history.

---

## 16. What belongs outside call/event objects

The following are separate object families and must not be collapsed into the call/event layer:
- tracked plans and plan items
- policy records
- full artifact metadata stores
- raw worker scratch notes
- arbitrary local helper objects
- UI-only presentation state

Calls and events are the runtime spine, not the whole universe.

---

## 17. Alfred’s role at the object layer

## 17.1 What Alfred owns mechanically
Alfred owns:
- official event creation
- official event IDs
- official route/linkage recording
- official factual event history
- call validation at the shell/object level

## 17.2 What Alfred does not own
Alfred does not own:
- semantic truth of the call payload
- semantic truth of the worker’s reasoning
- full plan semantics
- policy authorship by improvisation

This stays consistent with the Alfred master contract.

---

## 18. Persistence posture

## 18.1 Call objects
Calls may exist in-flight, be logged, be routed, and be referenced by later event records.

## 18.2 Event objects
Events are the durable append-only factual trail.

## 18.3 Design rule
If the implementation persists both, it must still preserve the conceptual difference between:
- runtime interaction object
- recorded history object

---

## 19. Implementation-facing object organization guidance

Recommended future schema/object organization:

```text
schemas/calls/
  task.create.schema.json
  plan.record.schema.json
  job.start.schema.json
  child_job.request.schema.json
  result.submit.schema.json
  failure.report.schema.json
  checkpoint.create.schema.json
  continuation.record.schema.json

schemas/events/
  task.created.schema.json
  plan.recorded.schema.json
  job.created.schema.json
  job.started.schema.json
  job.dispatched.schema.json
  job.returned.schema.json
  job.blocked.schema.json
  job.failed.schema.json
  checkpoint.created.schema.json
  continuation.recorded.schema.json
  artifact.registered.schema.json

schemas/objects/
  call-object.schema.json
  event-object.schema.json
```

Recommended implementation order:
1. stabilize base call object
2. stabilize base event object
3. define per-call narrowing rules
4. define per-event narrowing rules
5. only then start raw schema authoring or persistence wiring

---

## 20. Good vs bad usage

## 20.1 Good usage
Good usage means:
- call objects stay focused on runtime interaction
- event objects stay focused on factual recorded history
- route/linkage fields are explicit
- same-job return and retry rules stay intact
- payload refs are used when bodies should stay external
- event objects do not become giant raw body dumps

## 20.2 Bad usage
Bad usage includes:
- treating calls and events as the same object
- inventing event-only fields inside runtime calls with no reason
- embedding every giant payload body into every event record
- blurring retry vs replacement job behavior
- turning events into semantically rewritten summaries instead of factual records

---

## 21. Final position

The Garage runtime object layer needs two explicit object families:
- call objects
- event objects

Calls are runtime interaction envelopes.
Events are Alfred’s append-only factual record trail.

They overlap in linkage, but they are not the same thing.
That boundary must stay explicit before raw JSON Schemas and persistence code start hardcoding bad assumptions.
