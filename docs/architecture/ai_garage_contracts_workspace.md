# AI Garage Contracts Workspace

## Status

Working draft space.

This workspace is not final.
It is the current drafting surface for the next contract layer so the documents can be edited in one place without the chat breaking long text apart.

## Why this workspace exists

The current role contracts and blueprint are far enough along that the next work should stop living as fragmented chat text.

The next contract layer should be drafted here as long-form working text, then exported into repo docs once each section is stable.

## Current working contract order

1. AI Garage Blueprint
2. Alfred Master Contract
3. Jarvis Master Contract
4. Robin Master Contract
5. Garage Universal Language Dictionary
6. Universal Call Envelope / Library Schema Contract
7. ID Policy Contract
8. Tracked Plan Object Contract
9. Artifact / Output Ref Contract

## Next contract target

# Universal Call Envelope / Library Schema Contract v0.1

## Status

Working draft.

This contract is not final.
It exists to convert the Garage Universal Language Dictionary into machine-checkable schema authority.

This document should define the official JSON Schema layer for the shared Garage runtime language.

It should not redefine the vocabulary already frozen by the dictionary.
It should operationalize that vocabulary into explicit schema objects.

---

## 1. Purpose

This contract defines:

- the base call envelope schema
- the per-call schemas for each official Garage call
- the shared object schemas used by those calls
- required vs optional vs forbidden fields
- field-level type rules
- role-sender / role-receiver expectations
- the exact relationship between shell objects and worker-owned payload/body objects

This contract does not define:

- runtime transport details
- final SQLite implementation details
- final API route details
- Stagehand-native method schemas
- OpenHands-internal tracker object schemas
- implementation-local temporary helper objects

---

## 2. Primary authority rule

The Garage Universal Language Dictionary remains the primary authority for:

- official call names
- official event names
- official state/status tokens
- retry / return / new-job rules
- official ID ownership rules

This contract must derive its schema objects from that dictionary and must not silently rename tokens.

---

## 3. Base schema set

The first schema layer should include:

- call-envelope.schema.json
- task.schema.json
- job.schema.json
- event.schema.json
- checkpoint.schema.json
- artifact-ref.schema.json
- workspace-ref.schema.json
- payload-ref.schema.json
- tracked-plan.schema.json
- plan-item.schema.json

---

## 4. Official call schemas

Each official Garage call should have its own schema.

Required v0.1 call schemas:

- task.create.schema.json
- plan.record.schema.json
- job.start.schema.json
- child_job.request.schema.json
- result.submit.schema.json
- failure.report.schema.json
- checkpoint.create.schema.json
- continuation.record.schema.json

Optional/deferred v0.1 call schemas:

- assignment.dispatch.schema.json
- assignment.accept.schema.json

If optional calls are not activated in v0.1, they should be clearly marked deferred and not treated as required runtime authority.

---

## 5. Base call envelope

The base call envelope should define the shared shell fields used across all official calls.

At minimum:

- schema_version
- call_type
- task_id
- job_id
- parent_job_id
- from_role
- to_role
- reported_status
- reported_at
- attempt_no
- artifact_refs
- workspace_refs
- payload
- payload_ref

The per-call schemas should narrow these fields instead of duplicating the whole definition each time.

---

## 6. Core shared object rules

### 6.1 task_id

The task_id identifies the umbrella mission.

### 6.2 job_id

The job_id identifies one work leg under a task.

### 6.3 event_id

The event_id identifies one official recorded event.

### 6.4 checkpoint_id

The checkpoint_id identifies one official resume anchor.

### 6.5 artifact_id

The artifact_id identifies one official output/artifact label when artifact IDs are used.

---

## 7. Required call-by-call rules to define

Each call schema should explicitly answer:

- which fields are required
- which fields are optional
- which fields are forbidden
- what payload/body object shape is expected
- which role is allowed to send the call
- which role is expected to receive the call
- whether reported_status is required
- whether job_id is required
- whether parent_job_id is allowed or required
- whether payload and payload_ref may both exist together

---

## 8. Call-specific notes

### 8.1 task.create

Should create the umbrella mission shell.
Likely requires task-level fields and initial payload context.

### 8.2 plan.record

Should record an official plan version.
Likely requires task_id, plan_version, and plan payload or payload_ref.

### 8.3 job.start

Should indicate that a specific work leg is active.
Likely requires task_id, job_id, from_role, and reported_at.

### 8.4 child_job.request

Should request a new child browser/job leg.
Likely requires task_id, parent_job_id or current job context, from_role, to_role, and a request payload.

### 8.5 result.submit

Should return a result for an existing job using the same job_id.
Likely requires task_id, job_id, reported_status, refs, and result payload/body.

### 8.6 failure.report

Should record blocked or failed outcome for an existing job using the same job_id.
Likely requires task_id, job_id, reported_status, refs where present, and failure payload/body.

### 8.7 checkpoint.create

Should record an official checkpoint.
Likely requires task_id, checkpoint metadata, and supporting refs.

### 8.8 continuation.record

Should record resumability metadata.
Likely requires task_id, current job linkage where relevant, and continuation payload/body.

---

## 9. Event schema layer

A separate event schema layer should exist for official Alfred-recorded events.

Initial event set:

- task.created
- plan.recorded
- job.created
- job.started
- job.dispatched
- job.returned
- job.blocked
- job.failed
- checkpoint.created
- continuation.recorded
- artifact.registered

This event layer should be defined separately from the call layer.

---

## 10. Retry and return invariants

The schemas and validation rules must preserve these invariants:

- a result or failure return uses the same job_id as the job being reported
- retry of the same job keeps the same job_id and increments attempt_no
- materially new/refined work gets a new job_id
- IDs are official Garage-level identifiers, minted by Alfred in operation but governed by Garage-level rules

---

## 11. Refs and pointers

The schema layer must define:

### artifact_ref

A pointer to a created/found output object.

### workspace_ref

A pointer to where a worker says an output lives.

### payload_ref

A pointer to a worker-owned payload file when full body content is not stored inline.

These should be shared object schemas, not duplicated across every call.

---

## 12. Validation posture

Validation should be strict about:

- shape
n- required fields
- enum tokens
- type correctness
- allowed/forbidden field presence

Validation should not attempt to infer semantic truth.

---

## 13. Next drafting step

The next concrete drafting step inside this workspace should be:

1. write the base call-envelope schema spec in plain language
2. write the task.create schema spec
3. write the child_job.request schema spec
4. write the result.submit schema spec
5. continue through the remaining official calls

## Working note

This workspace should be used as the live drafting surface before the schema files themselves are generated into repo paths.

