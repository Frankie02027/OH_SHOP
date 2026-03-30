# HANDOFF ENVELOPE CONTRACT v0.1
## AI Garage Shell / Body / Route Envelope Contract

## Status

Working draft.

This is not final.
It is the first serious contract for the Garage handoff envelope.

This contract exists because the Garage already has:
- a higher-level library/policy contract
- a universal language dictionary
- a library schema contract
- role contracts that depend on a clean shell/body split

The Garage needs one explicit contract for the envelope itself so:
- Jarvis and Robin can author the semantic body
- Alfred can stamp and route the shell
- Ledger can store the official records without semantic confusion

This document does **not** replace:
- `ai_garage_library_and_policy_contract_v_0_1.md`
- `garage_universal_language_dictionary_v0_1.md`
- `LIBRARY_SCHEMA_CONTRACT_v_0_1.md`

It narrows and operationalizes the handoff/envelope model they already call for.

---

## 1. Purpose

This contract defines the official Garage handoff envelope.

It governs:
- the shell/body split
- the base call envelope meaning
- which fields belong to the shell
- which fields belong to the body/payload
- who authors which parts
- which parts Alfred may validate/stamp
- which parts Alfred must not semantically rewrite
- payload vs payload_ref usage
- refs and route metadata
- sender/receiver role meaning
- how handoffs relate to task/job/event/checkpoint IDs

It does **not** govern:
- final transport protocol
- final REST endpoints
- final database schema
- Stagehand-native request payloads
- OpenHands-native internal objects
- semantic truth of returned content

---

## 2. Primary authority relationship

## 2.1 Dictionary authority
`garage_universal_language_dictionary_v0_1.md` is the primary authority for:
- shell field names
- call types
- event types
- status tokens
- ID ownership
- retry / return / new-job rules

## 2.2 Library/policy contract authority
`ai_garage_library_and_policy_contract_v_0_1.md` is the higher-level authority for:
- the two-layer model
- why AI writes body meaning and Alfred writes the official shell
- the shared language design stance

## 2.3 Library schema contract authority
`LIBRARY_SCHEMA_CONTRACT_v_0_1.md` is the schema-layer authority for:
- the base call envelope schema
- per-call schema rules
- shared object schema organization

This contract must align with all three.

---

## 3. Why the envelope exists

The envelope exists because the Garage needs:
- machine-readable outer structure
- worker-authored semantic meaning
- official route metadata
- official linkage between task/job/event/checkpoint/artifact refs
- a consistent handoff surface across Jarvis, Robin, and Alfred

Without an explicit envelope:
- handoffs become vague prose
- route metadata gets mixed with semantic meaning
- storage becomes messy
- validation becomes inconsistent
- restart/resume logic becomes harder

---

## 4. The two-layer model

The Garage handoff model has two layers:

## 4.1 Layer A: protocol shell
The shell is the official machine-facing wrapper.

The shell answers:
- what kind of call this is
- who sent it
- who should receive it
- which task/job it belongs to
- what worker-reported status is attached
- when it was reported
- which refs are attached
- how it links into the official workflow trail

## 4.2 Layer B: mission body / payload
The body is the worker-authored meaning object.

The body answers:
- what the request means
- what the result means
- what failed
- what constraints matter
- what next steps or continuation hints matter

## 4.3 Design rule
The shell is for official bookkeeping.
The body is for semantic meaning.

Do not collapse them into one blob.

---

## 5. Ownership model

## 5.1 Jarvis and Robin own body semantics
Jarvis and Robin author:
- request meaning
- result meaning
- failure meaning
- continuation meaning
- constraints
- success criteria
- summaries
- structured results
- ambiguity notes

## 5.2 Alfred owns official shell stamping
Alfred owns:
- official IDs
- official linkage
- official route metadata
- official timestamps/recording metadata
- official state-appropriate shell registration
- official event trail creation

## 5.3 Alfred does not own semantic truth
Alfred does **not** decide:
- whether the body is semantically correct
- whether the worker result is intellectually right
- whether the reasoning was good
- whether the browser findings are sufficient in the human sense

Alfred may reject malformed or out-of-policy envelopes.
That is not the same thing as owning the body meaning.

---

## 6. Base envelope fields

The universal dictionary already defines the base shell fields.

## 6.1 Official shell fields
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

## 6.2 Additional official linkage fields where needed
Depending on the specific call/object, the broader official record may also link:
- `event_id`
- `checkpoint_id`
- optional `handoff_id`
- optional `plan_version`

## 6.3 Shell meaning
The shell must stay:
- small
- boring
- deterministic
- consistent across calls

---

## 7. Field ownership by layer

## 7.1 Shell-owned fields
These are official envelope/shell concerns:
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
- `payload_ref`
- route/linkage fields
- official IDs

## 7.2 Body-owned fields
These are body/payload concerns:
- `objective`
- `reason_for_handoff`
- `constraints`
- `expected_output`
- `success_criteria`
- `summary`
- `structured_result`
- `ambiguity_notes`
- `details`
- `failure_bucket`
- `continuation_hints`
- `notes`

## 7.3 Mixed-reference boundary
`artifact_refs` and `workspace_refs` are shell-level refs to worker-created objects, but the worker body may still refer to or explain them semantically.

---

## 8. Payload vs payload_ref

## 8.1 Inline payload
Use `payload` when:
- the body is small enough
- inline transport/storage is acceptable
- the system wants the body directly in the envelope

## 8.2 External payload_ref
Use `payload_ref` when:
- the body is stored in a worker-owned file
- the body is too large or better stored separately
- the envelope should carry only the ref

## 8.3 Rule
The envelope must support both.
Later implementation may forbid both appearing together on some call types unless explicitly allowed.

## 8.4 Anti-drift rule
Do not force every handoff body inline if refs are cleaner.
Do not force every handoff body into a separate file if inline is cleaner.
The contract should allow both.

---

## 9. Role fields

## 9.1 `from_role`
Identifies the role originating the call.

Allowed core roles:
- `jarvis`
- `robin`
- `alfred`

## 9.2 `to_role`
Identifies the intended receiver/next role.

Allowed core roles:
- `jarvis`
- `robin`
- `alfred`

## 9.3 Design rule
These are route/ownership fields.
They belong to the shell, not to body prose.

---

## 10. Status fields

## 10.1 `reported_status`
This is a worker-reported status value, not Alfred truth.

Allowed values come from shared authority:
- `succeeded`
- `partial`
- `blocked`
- `failed`

## 10.2 Usage rule
`reported_status` belongs on:
- `result.submit`
- `failure.report`

It is usually not meaningful on:
- `task.create`
- `child_job.request`

unless a later specific contract says otherwise.

---

## 11. Route and linkage fields

The envelope must preserve workflow linkage.

## 11.1 `task_id`
Links the handoff to the umbrella mission.

## 11.2 `job_id`
Links the handoff to the specific work leg.

## 11.3 `parent_job_id`
Links to the prior or originating job where lineage matters.

## 11.4 `attempt_no`
Identifies retry count for the same job.

## 11.5 `reported_at`
Identifies when the worker says this call/report was submitted.

## 11.6 Design rule
These fields are official workflow linkage, not semantic body prose.

---

## 12. Call-specific body expectations

This contract does not replace per-call schema rules, but it does define body expectations.

## 12.1 `child_job.request`
Typical body fields:
- `objective`
- `reason_for_handoff`
- `constraints`
- `expected_output`
- `success_criteria`
- optional `notes`

## 12.2 `result.submit`
Typical body fields:
- `summary`
- `structured_result`
- `ambiguity_notes`
- `continuation_hints`

## 12.3 `failure.report`
Typical body fields:
- `summary`
- `failure_bucket`
- `details`
- `continuation_hints`

## 12.4 `continuation.record`
Typical body fields:
- current state summary
- what remains
- blockers
- next recommended step
- relevant refs

## 12.5 `checkpoint.create`
Typical body fields:
- checkpoint summary
- what is safe to resume from
- relevant refs/pointers
- optional reason

---

## 13. Envelope behavior per call class

## 13.1 Request-style calls
Examples:
- `task.create`
- `child_job.request`
- `plan.record`

These are primarily body-bearing calls that establish or request work.

## 13.2 Transition-style calls
Examples:
- `job.start`
- `checkpoint.create`
- `continuation.record`

These are shell-heavy calls that record execution/progression milestones.

## 13.3 Return-style calls
Examples:
- `result.submit`
- `failure.report`

These are body-bearing returns attached to an existing job.

---

## 14. Same-job return rule

The envelope contract must preserve the Garage return invariant.

A result or failure return uses the **same `job_id`** as the job being returned for.

This means:
- result/failure envelopes do not mint new jobs
- Alfred creates a new event record, not a new job record, for the return itself

This must stay fixed.

---

## 15. Retry vs new-job rule

## 15.1 Retry of same job
A retry envelope for the same job uses:
- same `job_id`
- incremented `attempt_no`

## 15.2 Materially new/refined request
A materially new request must use:
- new `job_id`
- optional `parent_job_id` linking to the prior job

## 15.3 Why this matters
The envelope must preserve lineage clearly enough that:
- retries are not confused with replacements
- replacements are not confused with returns

---

## 16. Artifact refs and workspace refs

## 16.1 `workspace_refs`
These point to where a worker says an output lives.

## 16.2 `artifact_refs`
These point to identified created/found outputs.

## 16.3 Rule
These refs belong in the shell as official pointers.
The body may explain them, but the refs themselves are official bookkeeping fields.

## 16.4 Anti-drift rule
Do not turn the envelope into the raw artifact body store.
Use refs.

---

## 17. Malformed envelope vs bad meaning

This distinction matters.

## 17.1 Malformed envelope
Examples:
- missing required shell fields
- invalid call_type
- invalid status token
- missing task/job linkage where required
- broken ref shape

Alfred may reject or flag these.

## 17.2 Semantically bad meaning
Examples:
- wrong conclusion
- weak result
- unconvincing summary
- shaky reasoning

Alfred does **not** become the semantic judge of these just because it owns the shell.

---

## 18. Envelope validation posture

The envelope layer should validate:
- field presence
- field types
- enum tokens
- route/linkage consistency
- allowed vs forbidden shell fields
- body/ref presence rules

It should not validate:
- whether the browser result is truly correct
- whether the reasoning is high quality
- whether the summary is persuasive to a human reviewer

---

## 19. Handoff envelope and persistence

The envelope is the natural bridge between:
- runtime calls
- event recording
- task/job linkage
- checkpoint linkage
- later durable storage

That means the envelope contract should be written so the same model can support:
- in-flight routing
- event logging
- durable storage of official records

without mixing the shell and body beyond recognition.

---

## 20. Handoff envelope and checkpoints

A checkpoint may capture or reference:
- the latest relevant envelope
- current task/job linkage
- current refs and payload refs
- route state
- last continuation body

This is why clean envelope structure matters for resumability.

---

## 21. Handoff envelope and tracked plan

The tracked plan and the handoff envelope are related but not identical.

- The tracked plan is the official execution list.
- The envelope is the official request/return shell+body wrapper.

A `child_job.request` envelope may advance a tracked plan item.
A `result.submit` or `failure.report` envelope may update a tracked plan item.
But the envelope is not the plan itself.

---

## 22. Anti-drift rules

The handoff envelope must not drift into:
- giant freeform prose messages
- one giant JSON blob with no shell/body distinction
- Alfred-authored semantic rewriting
- worker-authored fake official metadata
- direct embedding of every artifact body
- substrate-specific Stagehand/OpenHands internals masquerading as official Garage fields
- ad hoc one-off fields added every time a weird case appears

---

## 23. Implementation-facing organization guidance

Recommended future organization:

```text
schemas/common/
  call-envelope.schema.json

schemas/calls/
  task.create.schema.json
  plan.record.schema.json
  job.start.schema.json
  child_job.request.schema.json
  result.submit.schema.json
  failure.report.schema.json
  checkpoint.create.schema.json
  continuation.record.schema.json
```

Potential runtime layers:
- envelope validator
- route mapper
- payload ref resolver
- event recorder
- checkpoint snapshotter

---

## 24. Final position

The Garage handoff envelope is the official shell/body wrapper for cross-role work.

It exists so:
- Jarvis and Robin can author meaning
- Alfred can stamp official linkage/route metadata
- Ledger can store structured official records
- runtime progression stays resumable and inspectable

The shell must stay:
- small
- boring
- explicit
- deterministic

The body must stay:
- worker-authored
- semantically meaningful
- separate from official shell bookkeeping

That split is the whole point.
