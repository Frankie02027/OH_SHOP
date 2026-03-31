# LIBRARY SCHEMA CONTRACT v0.1
## AI Garage Shared Runtime Schema Contract

## Status

Working draft.

This is not final.
It is not frozen.
It is the first serious schema-layer contract derived from the existing Garage authorities.

This contract exists because the Garage already has:
- a higher-level Library and Policy contract
- a Universal Language Dictionary that freezes the concrete token names for v0.1

The next required layer is the machine-checkable schema layer.

This document does **not** replace:
- `ai_garage_library_and_policy_contract_v_0_1.md`
- `garage_universal_language_dictionary_v0_1.md`

It operationalizes them into explicit schema authority.

---

## 1. Purpose

This contract defines the schema layer for the shared Garage runtime language.

It governs:

- the base call envelope
- the per-call schema set for each official Garage call
- the shared object schema set
- the event schema set
- required vs optional vs forbidden field rules
- role/route constraints at the schema level where appropriate
- how shell fields relate to worker-authored payload/body fields
- how JSON Schema files should be organized

It does **not** govern:

- final runtime transport details
- final REST route details
- final SQLite DDL
- final adapter implementation code
- OpenHands internal tracker object schemas
- Stagehand native method schemas
- temporary local helper objects that never cross an official Garage boundary

---

## 2. Primary authority relationship

This contract is subordinate to the current Garage language authorities.

## 2.1 Dictionary authority
`garage_universal_language_dictionary_v0_1.md` is the primary authority for:
- official `call_type` names
- official `event_type` names
- official status/state tokens
- ID ownership rules
- retry / return / new-job rules
- official shell field names

This contract must not silently rename those tokens.

## 2.2 Library/policy authority
`ai_garage_library_and_policy_contract_v_0_1.md` is the higher-level authority for:
- why the shared language is shaped this way
- the top-level library design rule
- the tracked plan/checklist posture
- the standing policy/handbook split
- the shell/body split principle

This contract must stay aligned with both.

---

## 3. Design stance

## 3.1 Schema-first for Garage language objects
The official Garage language should be represented as explicit schema objects.

That means:
- every official core call gets its own schema
- every official persisted/shared object gets its own schema
- shared enums/tokens are centralized, not duplicated as loose strings everywhere

## 3.2 Small top-level call library
The schema layer must preserve the deliberately small top-level call library.
It must not explode the Garage language into dozens of one-off verbs.

## 3.3 Schema is for official Garage boundaries
Garage schemas apply to:
- official Garage calls
- official Garage events
- official Garage records
- official Garage refs
- official Garage tracked plan objects

They do **not** automatically apply to:
- every internal OpenHands object
- every internal Stagehand method call
- every adapter-local helper object
- every temporary local transformation

## 3.4 Shell first, body second
Every official call schema must preserve the two-layer model:
- protocol shell
- worker-authored body/payload

The schema layer must not collapse these into one vague blob.

---

## 4. Required schema set

The first serious schema set should include the following categories.

## 4.1 Base/shared schemas
- `call-envelope.schema.json`
- `roles.schema.json`
- `call-types.schema.json`
- `event-types.schema.json`
- `worker-reported-status.schema.json`
- `task-states.schema.json`
- `job-states.schema.json`
- `plan-item-states.schema.json`
- `id-types.schema.json`

## 4.2 Official call schemas
- `task.create.schema.json`
- `plan.record.schema.json`
- `job.start.schema.json`
- `child_job.request.schema.json`
- `result.submit.schema.json`
- `failure.report.schema.json`
- `checkpoint.create.schema.json`
- `continuation.record.schema.json`

## 4.3 Optional/deferred call schemas
Only create these if the runtime actually activates them:
- `assignment.dispatch.schema.json`
- `assignment.accept.schema.json`

Do not treat them as required v0.1 runtime authority unless they are deliberately promoted.

## 4.4 Shared object schemas
- `call-object.schema.json`
- `event-object.schema.json`
- `task-record.schema.json`
- `job-record.schema.json`
- `event-record.schema.json`
- `checkpoint-record.schema.json`
- `content-ref.schema.json`
- `artifact-ref.schema.json`
- `workspace-ref.schema.json`
- `payload-ref.schema.json`
- `tracked-plan.schema.json`
- `plan-item.schema.json`
- `policy-record.schema.json`

---

## 5. Official core call library for schema work

The required v0.1 official call library is:

1. `task.create`
2. `plan.record`
3. `job.start`
4. `child_job.request`
5. `checkpoint.create`
6. `continuation.record`
7. `result.submit`
8. `failure.report`

The schema contract must treat those eight as the official required call set.

Optional/deferred aliases:
- `assignment.dispatch`
- `assignment.accept`

Deferred/non-core:
- `context.request`
- `task.cancel`
- `human_input.request`

These may be added later, but they are not part of the required v0.1 schema set unless deliberately activated.

---

## 6. Official event library for schema work

The recommended core v0.1 event set is:

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

Supporting/derived tracked-plan or UI events may exist later, but they should not override the core cross-role event vocabulary.

---

## 7. Status/state library for schema work

## 7.1 Worker-reported statuses
- `succeeded`
- `partial`
- `blocked`
- `failed`

These are worker claims, not Alfred truth judgments.

## 7.2 Task states
- `created`
- `running`
- `waiting_on_child`
- `resuming`
- `completed`
- `failed`
- `cancelled`

## 7.3 Job states
- `queued`
- `dispatched`
- `running`
- `returned`
- `completed`
- `blocked`
- `failed`
- `cancelled`

## 7.4 Plan item states
- `todo`
- `in_progress`
- `needs_child_job`
- `done_unverified`
- `verified`
- `blocked`
- `abandoned`

The schema layer must preserve these exact token sets unless a later authority revision explicitly changes them.

---

## 8. ID policy as schema constraints

## 8.1 Official IDs
The schema layer must recognize the official Garage ID classes:
- `task_id`
- `job_id`
- `event_id`
- `checkpoint_id`
- `artifact_id`
- optional `plan_id`
- optional `handoff_id`

## 8.2 Ownership rule
The schema layer should reflect that:
- Alfred mints official IDs operationally
- Jarvis and Robin reference existing IDs
- Jarvis and Robin do not mint official IDs as official truth

## 8.3 Meaning rule
The schemas should encode ID fields as explicit typed fields, not as freeform overloaded text.

## 8.4 Format stance
The schema layer may enforce pattern shape for IDs if desired, but the patterns should stay dumb and boring.

Examples:
- `T000001`
- `T000001.J002`
- `T000001.E0007`
- `T000001.C001`
- `T000001.J002.A001`

Do not encode semantic essays inside IDs.

---

## 9. Base call envelope schema

Every official call schema must be built from a shared base envelope.

## 9.1 Required purpose
The base envelope exists so that:
- all official calls share one shell model
- validation remains consistent
- per-call schemas can narrow the envelope rather than duplicating it
- Alfred can validate protocol shape consistently

## 9.2 Base envelope fields
The base envelope must define these shared shell fields:

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

## 9.3 Envelope meaning
The base envelope represents the official shell.
The body/payload represents worker-authored semantic meaning.

## 9.4 Base envelope rule
The base envelope schema should define:
- canonical field names
- shared field types
- shared enum references
- shared `$ref` targets for refs and IDs

The per-call schemas then make fields required, optional, or forbidden as appropriate.

---

## 10. Shared shell/body model

This contract preserves the two-layer Garage handoff model.

## 10.1 Shell
The shell is the protocol wrapper Alfred validates and stamps.

Typical shell concerns:
- who sent it
- who receives it
- which task/job/checkpoint it belongs to
- what call type it is
- whether a worker-reported status is attached
- which refs are attached
- when it was reported

## 10.2 Body / payload
The payload/body is the worker-authored meaning object.

Typical body concerns:
- objective
- reason for handoff
- constraints
- expected output
- success criteria
- summary
- structured result
- failure details
- continuation hints

## 10.3 Schema consequence
The schema set must not confuse:
- protocol shell fields
with
- body semantics

---

## 11. Per-call schema requirements

Each official call schema must explicitly define:

- the exact `call_type` constant
- required fields
- optional fields
- forbidden fields
- whether `task_id` is required
- whether `job_id` is required
- whether `parent_job_id` is allowed/required
- whether `reported_status` is allowed/required
- whether `attempt_no` is allowed/required
- whether payload is required
- whether payload_ref is allowed as an alternative
- which roles are expected as sender and receiver
- which shared refs are allowed

Each call schema should be understandable by inspection, not just by inheritance tricks.

---

## 12. `task.create` schema contract

## 12.1 Purpose
Creates the umbrella mission.

## 12.2 Required minimum
- `schema_version`
- `call_type = "task.create"`
- sender information
- entry payload or payload_ref

## 12.3 Typical allowed fields
- `from_role`
- `to_role`
- `payload`
- `payload_ref`
- maybe `reported_at`

## 12.4 Typically forbidden / not yet meaningful
- existing `job_id`
- `reported_status`
- `attempt_no`
- job-return refs that only make sense after execution

## 12.5 Expected sender
- Jarvis
- or a user-facing entry layer if one is formalized later

## 12.6 Expected receiver
- Alfred

---

## 13. `plan.record` schema contract

## 13.1 Purpose
Records an official tracked plan version.

## 13.2 Required minimum
- `schema_version`
- `call_type = "plan.record"`
- `task_id`
- `plan_version`
- plan payload or payload_ref
- `from_role`

## 13.3 Allowed fields
- `job_id`
- `reported_at`
- refs if relevant
- continuation linkage if the runtime later needs it

## 13.4 Typically forbidden
- `reported_status` as if this were a result/failure return
- unrelated job-return-only refs

## 13.5 Expected sender
- Jarvis

## 13.6 Expected receiver
- Alfred

---

## 14. `job.start` schema contract

## 14.1 Purpose
Records that one specific work leg is active.

## 14.2 Required minimum
- `schema_version`
- `call_type = "job.start"`
- `task_id`
- `job_id`
- `from_role`
- `reported_at`

## 14.3 Allowed fields
- `attempt_no`
- `to_role`
- minimal payload if needed
- `parent_job_id` when lineage matters

## 14.4 Typically forbidden
- result/failure summary payloads pretending a start is a completion

## 14.5 Expected sender
- Jarvis
- Robin

## 14.6 Expected receiver
- Alfred

---

## 15. `child_job.request` schema contract

## 15.1 Purpose
Requests a new Robin child job from the current Jarvis leg.

## 15.2 Required minimum
- `schema_version`
- `call_type = "child_job.request"`
- `task_id`
- current/parent job context
- `from_role = "jarvis"`
- `to_role = "alfred"`
- request payload or payload_ref

## 15.3 Required semantic body shape
At minimum the body should support:
- `objective`
- `reason_for_handoff`
- `constraints`
- `expected_output`
- `success_criteria`
- optional `notes`

## 15.4 Allowed fields
- `parent_job_id`
- `artifact_refs`
- `workspace_refs`
- `reported_at`

## 15.5 Forbidden usage
This call must not be used as a disguised result return.
It requests work; it does not complete it.

---

## 16. `result.submit` schema contract

## 16.1 Purpose
Returns a result for an existing job.

## 16.2 Required minimum
- `schema_version`
- `call_type = "result.submit"`
- `task_id`
- `job_id`
- `from_role`
- `reported_status`
- result payload or payload_ref

## 16.3 Required status rule
The allowed `reported_status` values are the worker-reported statuses.
For a successful enough return, `reported_status` is usually:
- `succeeded`
- or `partial`

## 16.4 Required return rule
This call uses the **existing `job_id`** of the job being returned.
It does not mint a new job.

## 16.5 Typical result body shape
At minimum should support:
- `summary`
- `structured_result`
- `ambiguity_notes`
- `continuation_hints`

## 16.6 Typical allowed refs
- `artifact_refs`
- `workspace_refs`
- `payload_ref`

## 16.7 Expected sender
- Robin
- Jarvis

## 16.8 Expected receiver
- Alfred, then routed to the next role

---

## 17. `failure.report` schema contract

## 17.1 Purpose
Reports blocked or failed outcome for an existing job.

## 17.2 Required minimum
- `schema_version`
- `call_type = "failure.report"`
- `task_id`
- `job_id`
- `from_role`
- `reported_status`
- failure payload or payload_ref

## 17.3 Allowed status rule
The allowed `reported_status` values for this call are typically:
- `blocked`
- `failed`
- sometimes `partial` if later policy explicitly allows mixed failure/partial return shapes

## 17.4 Required return rule
This also uses the **existing `job_id`** of the job being returned.

## 17.5 Typical failure body shape
At minimum should support:
- `summary`
- `failure_bucket`
- `details`
- `continuation_hints`

## 17.6 Allowed refs
- `artifact_refs`
- `workspace_refs`
- `payload_ref`

## 17.7 Expected sender
- Robin
- Jarvis

## 17.8 Expected receiver
- Alfred, then routed onward

---

## 18. `checkpoint.create` schema contract

## 18.1 Purpose
Creates an official checkpoint.

## 18.2 Required minimum
- `schema_version`
- `call_type = "checkpoint.create"`
- `task_id`
- checkpoint payload/body or payload_ref
- sender information

## 18.3 Allowed fields
- `job_id`
- supporting refs
- checkpoint reason/body
- `reported_at`

## 18.4 Typical expected sender
- Jarvis
- later optionally Alfred-internal logic if the runtime formalizes that path

## 18.5 Expected receiver
- Alfred

---

## 19. `continuation.record` schema contract

## 19.1 Purpose
Records continuation/resumption metadata.

## 19.2 Required minimum
- `schema_version`
- `call_type = "continuation.record"`
- `task_id`
- continuation payload/body or payload_ref
- sender information

## 19.3 Allowed fields
- `job_id`
- refs
- `reported_at`

## 19.4 Typical continuation body shape
Should support:
- summary of current state
- what remains
- blockers
- next recommended action
- relevant refs

## 19.5 Expected sender
- Jarvis
- optionally Robin later if that path is activated

## 19.6 Expected receiver
- Alfred

---

## 20. Optional alias call schemas

These should remain explicitly optional unless promoted.

## 20.1 `assignment.dispatch`
May exist as:
- a derived event
- a derived runtime surface
- or a real explicit call later

For v0.1 it should not be treated as required authority unless the implementation explicitly activates it.

## 20.2 `assignment.accept`
Same rule.
Do not silently make it core if the current language keeps it optional/deferred.

---

## 21. Event schema layer

The Garage also needs schema objects for official recorded events.

Each event schema should define:
- `event_type`
- related `task_id`
- related `job_id` where applicable
- `event_id`
- `recorded_at`
- route/linkage metadata
- refs where applicable
- optional event payload/body

Recommended required event schemas:
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

Events must remain factual and append-only.

---

## 22. Shared object schema layer

## 22.1 `task`
Represents the umbrella mission record.

Should support:
- `task_id`
- task state
- creation metadata
- current plan linkage
- current active job linkage where relevant

## 22.2 `job`
Represents one work leg.

Should support:
- `job_id`
- `task_id`
- `parent_job_id`
- `attempt_no`
- sender/receiver lineage
- job state
- route metadata

## 22.3 `event`
Represents one official recorded event.

Should support:
- `event_id`
- `event_type`
- related task/job/checkpoint refs
- timestamps
- refs/payload linkage

## 22.4 `checkpoint`
Represents one official resume anchor.

Should support:
- `checkpoint_id`
- `task_id`
- `job_id`
- summary/metadata refs
- creation timestamp

## 22.5 `workspace_ref`
Represents where a worker says some output lives.

Should support:
- `role`
- `path`

## 22.6 `artifact_ref`
Represents a created/found output object.

Should support:
- `artifact_id`
- `kind`
- `workspace_ref`
- `reported_by`

## 22.7 `payload_ref`
Represents a pointer to a worker-owned payload file.

Should support:
- `kind`
- `path`

## 22.8 `tracked_plan`
Represents the official tracked plan.

Should support:
- `task_id`
- `job_id`
- `plan_version`
- `created_by`
- `current_active_item`
- `plan_status`
- plan items

## 22.9 `plan_item`
Represents one tracked plan item.

Should support:
- `item_id`
- `title`
- `description`
- `status`
- `depends_on`
- `verification_rule`
- `evidence_refs`
- `notes`

---

## 23. Retry / return / new-job invariants

The schema layer must preserve the Garage runtime invariants.

## 23.1 Return rule
A result or failure return uses the **same `job_id`** as the job being reported.

## 23.2 Retry rule
Retry of the same job:
- same `job_id`
- increment `attempt_no`

## 23.3 New refined job rule
If the work request is materially new or refined:
- new `job_id`
- `parent_job_id` may link to the earlier job

## 23.4 Schema consequence
Per-call schemas and validation notes must not accidentally allow ambiguous misuse that blurs:
- same-job return
- same-job retry
- materially new job

---

## 24. Required/optional/forbidden rule style

The schema set should be explicit.

For each field in each call schema, the contract should eventually say one of:
- required
- optional
- forbidden

Do not hide all important rules inside vague inheritance with no readable explanation.

---

## 25. JSON Schema organization plan

Recommended file organization:

```text
schemas/
  common/
    call-envelope.schema.json
    roles.schema.json
    call-types.schema.json
    event-types.schema.json
    worker-reported-status.schema.json
    task-states.schema.json
    job-states.schema.json
    plan-item-states.schema.json
    id-types.schema.json

  calls/
    task.create.schema.json
    plan.record.schema.json
    job.start.schema.json
    child_job.request.schema.json
    result.submit.schema.json
    failure.report.schema.json
    checkpoint.create.schema.json
    continuation.record.schema.json

  events/
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

  objects/
    call-object.schema.json
    event-object.schema.json
    task-record.schema.json
    job-record.schema.json
    event-record.schema.json
    checkpoint-record.schema.json
    content-ref.schema.json
    artifact-ref.schema.json
    workspace-ref.schema.json
    payload-ref.schema.json
    tracked-plan.schema.json
    plan-item.schema.json
    policy-record.schema.json
```

---

## 26. Validation posture

The schema layer should validate:
- shape
- required fields
- allowed enums
- type correctness
- shared field consistency
- ref structure

The schema layer should not pretend to validate:
- semantic truth
- reasoning quality
- browser evidence quality in the human sense
- whether the worker “should have known better”

That remains outside the schema layer.

---

## 27. Immediate next implementation order

The practical implementation order after this contract should be:

1. base `call-envelope` schema
2. `task.create`
3. `child_job.request`
4. `result.submit`
5. `failure.report`
6. `plan.record`
7. `job.start`
8. `checkpoint.create`
9. `continuation.record`
10. shared object schemas
11. event schemas

That order gives you the runtime spine first.

---

## 28. Final position

The Garage already has:
- the higher-level library/policy contract
- the universal language dictionary

This contract is the next layer.

Its job is to turn the already-frozen Garage runtime language into an explicit schema authority:
- one base envelope
- one schema per official core call
- one schema set for official events
- one schema set for shared objects
- clear required/optional/forbidden field rules

This contract must stay aligned with the existing repo authorities and should not silently compete with them.
