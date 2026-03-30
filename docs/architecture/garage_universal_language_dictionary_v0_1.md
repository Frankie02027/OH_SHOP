# GARAGE UNIVERSAL LANGUAGE DICTIONARY v0.1
## Jarvis / Robin / Alfred Shared Runtime Dictionary

## Status

Initial shared language dictionary for coding.

This is not a role essay.
This is the first practical dictionary for:
- IDs
- calls
- statuses
- refs
- routing
- shell fields
- code names

Its purpose is to make Jarvis, Robin, and Alfred speak the same machine language.

---

## 1. Core principle

### 1.1 Jarvis and Robin own meaning
Jarvis and Robin create:
- plans
- requests
- results
- summaries
- continuation notes
- findings
- outputs

### 1.2 Alfred owns official identification and shell records
Alfred creates and records:
- official IDs
- official linkage
- official route records
- official workflow metadata
- official shell records

### 1.3 Alfred does not interpret semantic payload meaning
Alfred does not decide:
- whether Robin was right
- whether Jarvis reasoned correctly
- whether the result is “good enough” in a semantic sense

Alfred is a deterministic manifest clerk.

---

## 2. Roles

## 2.1 `jarvis`
Main worker for:
- parent task ownership
- planning
- local coding
- local analysis
- continuation of the mission
- creating child-job requests when Robin is needed

## 2.2 `robin`
Browser / web / visual worker for:
- online investigation
- browser actions
- rendered content work
- child-job execution
- returning findings and created outputs

## 2.3 `alfred`
Deterministic clerk for:
- minting official IDs
- creating official shell records
- linking tasks/jobs/events/checkpoints
- recording worker-reported status
- recording refs to created outputs
- routing calls by declared type

---

## 3. ID classes

All official IDs are minted by Alfred.

Jarvis and Robin may reference existing IDs.
Jarvis and Robin do not mint official IDs.

## 3.1 `task_id`
### Meaning
The umbrella mission created from the original user request.

### Definition
One user request / one major mission = one `task_id`.

### Example
- `T000001`
- `T000002`

### Code identifier
- `task_id: str`

### Rule
A task persists across multiple jobs, retries, and role handoffs until the mission is done or abandoned.

---

## 3.2 `job_id`
### Meaning
One work leg under a task.

### Definition
A job is one specific execution leg by Jarvis or Robin.

### Example
- `T000001.J001`
- `T000001.J002`

### Code identifier
- `job_id: str`

### Rule
A result or failure for a job uses the **same `job_id`** as the job being reported.

A return does **not** get a new job ID.

---

## 3.3 `event_id`
### Meaning
One official Alfred record entry.

### Definition
Every official record Alfred creates gets an `event_id`.

### Example
- `T000001.E0001`
- `T000001.E0002`

### Code identifier
- `event_id: str`

### Rule
Event IDs are Alfred’s clerk trail, not worker-owned meaning.

---

## 3.4 `checkpoint_id`
### Meaning
One official resume anchor.

### Example
- `T000001.C001`
- `T000001.C002`

### Code identifier
- `checkpoint_id: str`

### Rule
Checkpoint IDs are minted only when a checkpoint is officially recorded.

---

## 3.5 `artifact_id`
### Meaning
One official ref label for a created/found output.

### Example
- `T000001.J002.A001`
- `T000001.J002.A002`

### Code identifier
- `artifact_id: str`

### Rule
Artifact IDs identify outputs Robin or Jarvis say they created, found, or attached.
The actual files stay in worker workspaces unless later architecture changes that.

---

## 3.6 `plan_id` (optional v0)
### Meaning
Official identifier for a tracked plan record.

### Example
- `T000001.P001`

### Code identifier
- `plan_id: str | None`

### Rule
Optional for v0.
If omitted, `task_id + plan_version` is enough.

---

## 3.7 `handoff_id` (optional v0)
### Meaning
Explicit identifier for one routed exchange.

### Example
- `T000001.H001`

### Code identifier
- `handoff_id: str | None`

### Rule
Optional for v0.
Only add if needed later.

---

## 4. ID format policy

## 4.1 Keep IDs dumb
IDs should be:
- short
- deterministic
- readable
- boring

Do **not** encode semantic essays inside IDs.

Bad:
- `task1_robin_retry_browser_partial_v2`
- `jarvis-main-task-return-3`

Good:
- `T000001`
- `T000001.J003`
- `T000001.E0012`

## 4.2 Meaning belongs in fields, not inside fancy ID strings
Use fields like:
- `from_role`
- `to_role`
- `call_type`
- `reported_status`
- `attempt_no`
- `parent_job_id`

Do not force that meaning into the ID itself.

---

## 5. Relationship fields

## 5.1 `parent_task_id`
### Meaning
Usually same as `task_id`; explicit parent link not needed for v0.

## 5.2 `parent_job_id`
### Meaning
The immediately preceding or originating job.

### Use
Used when:
- a child job was created from another job
- a new refined job supersedes or follows an earlier one

### Code identifier
- `parent_job_id: str | None`

### Example
Robin child job `T000001.J002` may have:
- `parent_job_id = T000001.J001`

---

## 5.3 `attempt_no`
### Meaning
Retry count for the same job.

### Code identifier
- `attempt_no: int`

### Rule
Retries for the same job keep the same `job_id` and increment `attempt_no`.

If Jarvis issues a materially new/refined child request, Alfred creates a **new** `job_id` instead.

---

## 5.4 `plan_version`
### Meaning
Version number of the tracked plan.

### Code identifier
- `plan_version: int`

---

## 6. Worker-reported statuses

These are worker claims.
These are **not Alfred judgments**.

## 6.1 `succeeded`
### Meaning
Worker says the job/step completed successfully enough to return.

## 6.2 `partial`
### Meaning
Worker says some usable output exists, but completion is incomplete or uncertain.

## 6.3 `blocked`
### Meaning
Worker says work cannot continue cleanly right now.

## 6.4 `failed`
### Meaning
Worker says the job/step failed.

### Code identifier
```python
WorkerReportedStatus = Literal["succeeded", "partial", "blocked", "failed"]
```

---

## 7. Official workflow states

These are Alfred’s bookkeeping states, not semantic truth.

## 7.1 Task-level states
- `created`
- `running`
- `waiting_on_child`
- `resuming`
- `completed`
- `failed`
- `cancelled`

### Code identifier
```python
TaskState = Literal[
    "created",
    "running",
    "waiting_on_child",
    "resuming",
    "completed",
    "failed",
    "cancelled",
]
```

## 7.2 Job-level states
- `queued`
- `dispatched`
- `running`
- `returned`
- `completed`
- `blocked`
- `failed`
- `cancelled`

### Code identifier
```python
JobState = Literal[
    "queued",
    "dispatched",
    "running",
    "returned",
    "completed",
    "blocked",
    "failed",
    "cancelled",
]
```

## 7.3 Plan item states
- `todo`
- `in_progress`
- `needs_child_job`
- `done_unverified`
- `verified`
- `blocked`
- `abandoned`

### Code identifier
```python
PlanItemState = Literal[
    "todo",
    "in_progress",
    "needs_child_job",
    "done_unverified",
    "verified",
    "blocked",
    "abandoned",
]
```

---

## 8. Call types

Keep the top-level call library small.

## 8.1 `task.create`
### Meaning
Create a new umbrella mission.

### Typical sender
- Jarvis or user-facing entry layer

### Alfred behavior
- mint `task_id`
- create task record
- create initial event record

---

## 8.2 `plan.record`
### Meaning
Record an official tracked plan version.

### Typical sender
- Jarvis

### Alfred behavior
- record `plan_version`
- link to `task_id`
- store or reference plan payload
- create event record

---

## 8.3 `job.start`
### Meaning
Worker says a specific job leg is now active.

### Typical sender
- Jarvis
- Robin

### Alfred behavior
- mark job `running`
- create event record

---

## 8.4 `child_job.request`
### Meaning
Request a new Robin child job from the current Jarvis leg.

### Typical sender
- Jarvis

### Alfred behavior
- mint new `job_id`
- set `parent_job_id`
- create job record
- route to Robin
- record event

---

## 8.5 `result.submit`
### Meaning
Worker returns a result for an existing job.

### Typical sender
- Robin
- Jarvis

### Alfred behavior
- record worker-reported status
- record refs to outputs/artifacts
- create event
- route to next expected role

### Rule
This uses the **existing `job_id`** of the job being returned.

---

## 8.6 `failure.report`
### Meaning
Worker reports blocked or failed outcome for an existing job.

### Typical sender
- Robin
- Jarvis

### Alfred behavior
- record worker-reported status
- record refs/notes
- create event
- route to next expected role

---

## 8.7 `checkpoint.create`
### Meaning
Create an official checkpoint record.

### Typical sender
- Jarvis
- later maybe Alfred-internal logic

### Alfred behavior
- mint `checkpoint_id`
- record checkpoint metadata
- create event

---

## 8.8 `continuation.record`
### Meaning
Record a continuation note for later resumption.

### Typical sender
- Jarvis
- optionally Robin if later desired

### Alfred behavior
- record continuation metadata/ref
- create event

---

## 8.9 `assignment.dispatch` (optional alias)
### Meaning
Dispatch a created job to its target role.

### Note
May remain implicit in `child_job.request` for v0 if you want the system smaller.

---

## 8.10 `assignment.accept` (optional alias)
### Meaning
Worker acknowledges the job leg.

### Note
Optional in v0.
Can be omitted unless explicit acceptance tracking is needed.

---

## 9. Event types

Events are Alfred’s official factual record entries.

Recommended v0 events:
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

### Code identifier
```python
EventType = Literal[
    "task.created",
    "plan.recorded",
    "job.created",
    "job.started",
    "job.dispatched",
    "job.returned",
    "job.blocked",
    "job.failed",
    "checkpoint.created",
    "continuation.recorded",
    "artifact.registered",
]
```

---

## 10. Refs / pointer objects

These are how Alfred tracks what workers created or found without owning worker workspaces.

## 10.1 `workspace_ref`
### Meaning
Pointer to where a worker says an output lives.

### Example
```json
{
  "role": "robin",
  "path": "/workspace/robin/tasks/T000001/jobs/J002/output/extract.json"
}
```

### Code identifier
- `workspace_ref: dict`

---

## 10.2 `artifact_ref`
### Meaning
Pointer to a created/found output object.

### Example
```json
{
  "artifact_id": "T000001.J002.A001",
  "kind": "screenshot",
  "workspace_ref": "/workspace/robin/tasks/T000001/jobs/J002/output/page.png",
  "reported_by": "robin"
}
```

### Code identifier
- `artifact_ref: dict`

---

## 10.3 `payload_ref`
### Meaning
Pointer to a worker-owned payload file if Alfred does not store full body content.

### Example
```json
{
  "kind": "result_payload",
  "path": "/workspace/robin/tasks/T000001/jobs/J002/output/result.json"
}
```

---

## 11. Official shell

The shell is the only part Alfred must reliably understand.

### 11.1 Official shell fields
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
- `payload` or `payload_ref`

### 11.2 Meaning
The shell is the official bookkeeping wrapper.
The payload/body is worker-owned meaning.

### 11.3 Code model
```python
class CallEnvelope(TypedDict, total=False):
    schema_version: str
    call_type: str
    task_id: str
    job_id: str
    parent_job_id: str | None
    from_role: str
    to_role: str
    reported_status: str | None
    reported_at: str
    attempt_no: int
    artifact_refs: list[dict]
    workspace_refs: list[dict]
    payload: dict
    payload_ref: dict
```

---

## 12. Payload / body

The payload is the worker-owned meaning object.

Alfred should treat it as mostly opaque.

## 12.1 Typical payload for `child_job.request`
- `objective`
- `reason_for_handoff`
- `constraints`
- `expected_output`
- `success_criteria`
- `notes`

## 12.2 Typical payload for `result.submit`
- `summary`
- `structured_result`
- `ambiguity_notes`
- `continuation_hints`

## 12.3 Typical payload for `failure.report`
- `summary`
- `failure_bucket`
- `details`
- `continuation_hints`

---

## 13. Routing rules

Routing should be deterministic by call type and declared linkage.

## 13.1 `task.create`
- origin: Jarvis / entry layer
- destination: Alfred
- Alfred action: create task record

## 13.2 `plan.record`
- origin: Jarvis
- destination: Alfred
- Alfred action: record plan

## 13.3 `child_job.request`
- origin: Jarvis
- destination: Alfred -> Robin
- Alfred action: mint new child `job_id`, route to Robin

## 13.4 `result.submit` from Robin
- origin: Robin
- destination: Alfred -> Jarvis
- Alfred action: record returned job result, route back to Jarvis

## 13.5 `failure.report` from Robin
- origin: Robin
- destination: Alfred -> Jarvis
- Alfred action: record failure/block, route back to Jarvis

## 13.6 `continuation.record`
- origin: Jarvis
- destination: Alfred
- Alfred action: record note only

## 13.7 `checkpoint.create`
- origin: Jarvis
- destination: Alfred
- Alfred action: mint checkpoint ID and record it

---

## 14. Retry vs new-job rule

## 14.1 Retry of same job
Use:
- same `job_id`
- increment `attempt_no`

### Example
- first attempt: `T000001.J002`, `attempt_no = 1`
- retry: `T000001.J002`, `attempt_no = 2`

## 14.2 New refined job
If Jarvis materially changes the request:
- Alfred mints a new `job_id`

### Example
- old child job: `T000001.J002`
- refined replacement: `T000001.J003`
- set `parent_job_id = T000001.J002`

---

## 15. Return rule

A result or failure return uses the **same `job_id`** as the job it is returning for.

### Example
- Robin child job created as `T000001.J002`
- Robin result returns for `T000001.J002`
- Alfred creates a new `event_id`, not a new `job_id`

This rule must stay fixed.

---

## 16. What Alfred records

Alfred records:
- official IDs
- call type
- from/to role
- worker-reported status
- refs to created/found outputs
- refs to worker workspace locations
- linkage between task/job/event/checkpoint/artifact
- route history

Alfred does **not** need to semantically read the payload/body.

---

## 17. What Jarvis owns semantically

Jarvis owns:
- parent mission meaning
- initial plan meaning
- local step meaning
- child-job request meaning
- continuation meaning
- deciding what to do after Robin returns

---

## 18. What Robin owns semantically

Robin owns:
- browser-leg meaning
- what it found
- what it created
- what it downloaded
- what status it reports
- what ambiguity/failure it reports

---

## 19. Minimal code constants

```python
ROLES = {"jarvis", "robin", "alfred"}

CALL_TYPES = {
    "task.create",
    "plan.record",
    "job.start",
    "child_job.request",
    "result.submit",
    "failure.report",
    "checkpoint.create",
    "continuation.record",
}

WORKER_REPORTED_STATUSES = {
    "succeeded",
    "partial",
    "blocked",
    "failed",
}

TASK_STATES = {
    "created",
    "running",
    "waiting_on_child",
    "resuming",
    "completed",
    "failed",
    "cancelled",
}

JOB_STATES = {
    "queued",
    "dispatched",
    "running",
    "returned",
    "completed",
    "blocked",
    "failed",
    "cancelled",
}
```

---

## 20. First practical naming examples

### Task 1
- `task_id = T000001`

### Jarvis first work leg
- `job_id = T000001.J001`

### Robin child leg
- `job_id = T000001.J002`
- `parent_job_id = T000001.J001`

### Robin returns partial result
- `call_type = result.submit`
- `task_id = T000001`
- `job_id = T000001.J002`
- `reported_status = partial`
- `event_id = T000001.E0007`

### Jarvis issues refined Robin job
- `job_id = T000001.J003`
- `parent_job_id = T000001.J002`

### Checkpoint later
- `checkpoint_id = T000001.C001`

---

## 21. Final position

This dictionary defines the first shared runtime language for:
- Jarvis
- Robin
- Alfred

Jarvis and Robin own meaning.
Alfred owns official IDs, shell records, and routing metadata.

The language should stay:
- small
- boring
- deterministic
- human-readable
- codeable

It should not become a giant bag of one-off calls or over-smart IDs.
