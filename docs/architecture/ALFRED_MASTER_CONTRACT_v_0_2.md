# ALFRED Master Contract v0.2
## Expanded Working Draft

## Status

This document is a **working contract**.

It is not final.
It is not frozen.
It is the current best serious attempt to define Alfred clearly enough that:
- shared schema work can proceed without shell/meaning confusion
- ID policy can be implemented without guessing
- routing and checkpoint behavior can be described without pretending Alfred is an AI
- runtime adapters can be treated as adapters instead of fake architectural truth

This document is an authority draft.
It is not a runtime implementation manual.

---

## 1. Purpose

This contract defines the authoritative working position for **Alfred** inside AI Garage.

It governs:

- Alfred role identity
- Alfred authority boundaries
- Alfred ownership of official IDs
- Alfred ownership of official shell records
- Alfred ownership of official linkage and route metadata
- Alfred ownership of official bookkeeping states
- Alfred handling of refs and pointers to worker outputs
- Alfred relationship to Jarvis, Robin, Ledger, OpenHands, Stagehand, and the shared Garage language
- Alfred validation, rejection, routing, retry, and checkpoint discipline at the policy level

It does **not** govern:

- final runtime implementation details
- final SQLite schema details
- final network/API transport details
- Jarvis internal reasoning policy
- Robin internal browser execution policy
- exact OpenHands patch behavior
- exact Stagehand wrapper behavior
- final UI behavior

This document exists so Alfred can be strong without becoming fake AI magic.

---

## 2. Alfred identity

Alfred is the Garage’s:

- deterministic manifest clerk
- official shell writer / stamper
- official ID minting authority
- linkage and route metadata owner
- official state recorder
- checkpoint registrar
- retry / handoff policy gatekeeper
- non-creative workflow controller

Alfred is **not**:

- Jarvis
- Robin
- the main reasoner
- the semantic author of requests or returns
- the owner of worker workspaces by default
- a giant warehouse for every raw worker file
- a browser worker
- a coding worker
- a chat personality

Alfred should be understood as the Garage’s **boring official clerk and gatekeeper**.

That is a feature, not a limitation.

---

## 3. Alfred as a role, not a wrapper

Alfred is a **logical role**, not one thin wrapper, script entrypoint, or current local patch layer.

That means Alfred should not be defined by:

- one current Python file
- one current REST shape
- one current OpenHands callback pattern
- one current local SQLite table layout
- one current runtime adapter

The role contract should outlive changes in:

- control scripts
- wrapper surfaces
- service boundaries
- persistence helpers
- integration adapters

So Alfred should be described by:

- duties
- boundaries
- ownership rules
- shell rules
- routing rules
- state rules

not by one current repo implementation surface.

---

## 4. Alfred’s place in the Garage

The Garage has distinct working roles:

- OpenWebUI as front desk
- Jarvis as main planner and parent-task worker
- Robin as browser / web / visual specialist
- Alfred as deterministic controller and clerk
- Ledger as durable official state / event / artifact-index layer

Alfred sits between workers and official progression.

Conceptually:

`User -> Jarvis -> Alfred -> Robin -> Alfred -> Jarvis -> User`

Alfred is what prevents:

- silent job drift
- unofficial ID invention
- hidden retries
- invisible handoffs
- fake continuity
- workers silently promoting local state into official truth

---

## 5. Alfred’s core ownership

Alfred owns the official shell.

That includes:

- `task_id`
- `job_id`
- `event_id`
- `checkpoint_id`
- optional `artifact_id`
- optional `handoff_id`
- official `from_role`
- official `to_role`
- official `call_type`
- official `reported_at`
- official `attempt_no`
- official parent/child linkage
- official route history
- official workflow state transitions

Alfred also owns:

- creating official records
- validating record shape
- attaching linkage metadata
- deciding whether a retry is still the same job or a new job
- deciding whether a checkpoint record is required before routing
- recording refs/pointers to worker-owned outputs

Alfred does **not** own the semantic meaning inside the worker-authored body.

---

## 6. Alfred does not own meaning

Jarvis and Robin own semantic meaning.

That means Alfred does **not** own:

- whether the parent mission is semantically well-reasoned
- whether a browser result is semantically “good enough”
- the full meaning of a plan
- the meaning of a child-job objective
- the interpretation of online evidence
- the interpretation of code changes

Alfred should not creatively rewrite worker meaning just to make records look cleaner.

At most, Alfred may:

- validate that required fields exist
- reject malformed envelopes
- stamp missing official shell fields
- route or block based on declared policy fields

Alfred should treat worker bodies as mostly opaque meaning objects.

---

## 7. Alfred and the official shell

The official shell is the machine-facing bookkeeping wrapper.

Alfred owns that shell.

At minimum the shell should carry:

- schema version
- call type
- task ID
- job ID
- parent job ID where applicable
- from role
- to role
- worker-reported status where applicable
- reported timestamp
- attempt number
- refs to artifacts
- refs to worker workspace outputs
- payload or payload reference

Practical rule:

- Jarvis or Robin writes the meaningful body
- Alfred writes or stamps the official shell

That rule must stay stable.

---

## 8. Alfred and official IDs

Only Alfred mints official IDs.

That includes:

- `task_id`
- `job_id`
- `event_id`
- `checkpoint_id`
- optional `artifact_id`

Workers may carry those IDs and may refer to draft local names while thinking, but those draft names are not official Garage truth.

ID rules Alfred must preserve:

- a result or failure return uses the **same `job_id`** as the job being reported
- a retry of the same job keeps the same `job_id` and increments `attempt_no`
- a materially new or refined request gets a **new `job_id`**
- `event_id` is always Alfred’s clerk trail, not a worker-owned semantic object

---

## 9. Alfred and linkage

Alfred owns official linkage between:

- tasks
- jobs
- child jobs
- checkpoints
- events
- artifacts
- continuation notes

That means Alfred is the correct place to record:

- `parent_job_id`
- child-job lineage
- retry lineage
- replacement/supersession lineage
- checkpoint-to-job linkage
- event-to-job linkage
- artifact-to-job linkage

Workers should not improvise official linkage by themselves.

---

## 10. Alfred and route metadata

Alfred owns official route metadata such as:

- which role sent the call
- which role should receive it next
- whether a job is dispatched, running, returned, blocked, or failed
- whether a checkpoint was required
- whether a retry was granted
- whether the return resumes Jarvis or remains blocked

Alfred should make handoffs explicit.

The route should never depend on hidden chat continuity alone.

---

## 11. Alfred and refs / pointers

Alfred should track worker outputs by **reference first**, not by assuming ownership of every raw file.

That means Alfred should record:

- `workspace_ref`
- `artifact_ref`
- `payload_ref`
- artifact metadata
- reported output kind

By default, Alfred is a pointer ledger and metadata clerk, not the warehouse owner of all worker output files.

The default posture should be:

- worker creates output in worker workspace
- worker reports refs
- Alfred records refs and linkage
- Ledger indexes those refs

If later architecture decides to promote copies of some outputs into durable storage, that is a later storage policy choice, not Alfred’s core role identity.

---

## 12. Alfred does not own worker workspaces

Jarvis and Robin work in their own bounded workspaces or substrate-specific execution environments.

Alfred does **not** own those workspaces by default.

Alfred should not behave as if:

- every worker file must be copied into Alfred storage
- Alfred becomes the real home for scratch outputs
- Alfred’s state tables are the place where raw worker work lives

Alfred should instead record:

- where outputs live
- who reported them
- what job they belong to
- what kind of object they are

That keeps Alfred slim enough to stay deterministic.

---

## 13. Alfred and Ledger

Alfred is not Ledger.

Ledger is the durable state, event, artifact-index, and continuation layer.

Alfred is the role that:

- creates/stamps official records
- decides what official record should be written
- routes work according to the shared language and policy

Ledger is the layer that:

- stores those official records
- stores event history
- stores or indexes artifact refs
- stores plan versions
- stores continuation and checkpoint records

Practical rule:

- Alfred is the clerk
- Ledger is the durable record plane

Do not collapse them conceptually even if early implementation initially stores both concerns close together.

---

## 14. Alfred and validation

Alfred should validate **shape and declared policy fields**, not semantic truth.

That means Alfred may validate:

- required shell fields exist
- IDs are present or mintable
- role routing is allowed
- retry metadata is coherent
- checkpoint requirement is satisfied
- payload/body is present where required

Alfred should not pretend to validate:

- whether Jarvis’s reasoning is actually correct
- whether Robin’s evidence is semantically sufficient in the human sense
- whether a semantic summary “feels true”

If semantic sufficiency matters, Alfred should require declared proof fields, status fields, or operator review, not improvise judgment.

---

## 15. Alfred and retries

Alfred owns official retry treatment.

That includes deciding whether:

- the current job gets another attempt with the same `job_id`
- `attempt_no` increments
- the current work is blocked instead of retried
- a materially refined request should become a new job

Alfred should not allow workers to silently blur:

- retry of same job
- return for same job
- materially new job request

Those distinctions must stay explicit because they directly affect coding of IDs, events, tables, and restart logic.

---

## 16. Alfred and checkpoints

Alfred owns official checkpoint records.

That means Alfred should:

- mint `checkpoint_id`
- link the checkpoint to task/job state
- record why the checkpoint exists
- enforce checkpoint requirements before critical baton passes when policy says so

Alfred should not treat checkpoints as:

- semantic proof
- semantic completion
- freeform memory dumps

Checkpoint means official resume anchor, not victory claim.

---

## 17. Alfred and continuation notes

Continuation notes may be authored by workers, but Alfred owns their official recording.

Alfred should ensure continuation records are linked to:

- current task
- current job
- current plan version where relevant
- relevant refs/artifacts
- blocking state or next expected action

Alfred should record them as official resumability metadata, not as vague chat residue.

---

## 18. Alfred and substrate boundaries

Garage language is **not** the same thing as:

- OpenHands internal language
- OpenHands tracker semantics
- Stagehand native method names
- one current MCP export list
- one current wrapper signature

That means Alfred should reason in Garage language, not in substrate-specific naming.

The correct boundary is:

- Garage language at the role / shell / record level
- adapters and wrappers at the implementation bridge level
- substrate-specific method details below that

Adapters and wrappers are the correct translation boundary.

Alfred should never define the Garage in terms of:

- `act()`
- `observe()`
- `extract()`
- OpenHands-internal local tracker field names
- one current runtime export inventory

That is implementation bridge material, not Alfred role authority.

---

## 19. Alfred and OpenHands / Stagehand

OpenHands is Jarvis’s workbench.
Stagehand is Robin’s current browser substrate.

Alfred is neither.

Alfred should:

- route to Jarvis without becoming OpenHands
- route to Robin without becoming Stagehand
- record official state around those legs
- stay above implementation adapters

If runtime adapters change, Alfred’s contract should remain stable.

---

## 20. Alfred and workers

### 20.1 With Jarvis
Alfred should:

- receive Jarvis-authored plans, child-job requests, continuation notes, completion claims, and failures
- stamp the official shell
- record official state
- gate official progression

Alfred should not:

- replace Jarvis as planner
- rewrite Jarvis’s semantic body as if Alfred authored it

### 20.2 With Robin
Alfred should:

- receive Robin returns, artifact refs, ambiguity notes, and failures
- record the official return
- route the result back to Jarvis or official blocked state

Alfred should not:

- replace Robin as browser specialist
- semantically interpret the browser leg as if Alfred had seen the page itself

---

## 21. What this contract deliberately defers

This contract does **not** freeze:

- final SQLite table definitions
- final JSON schema syntax
- final REST/API route shapes
- final persistence implementation
- final runtime container boundaries
- final adapter code
- final operator review UI

Those belong in later schema, storage, and implementation contracts.

---

## 22. Final contract position

Alfred is the Garage’s deterministic manifest clerk.

Alfred owns:

- official IDs
- official shell records
- official linkage
- official route metadata
- official state bookkeeping
- refs and pointers to worker outputs

Alfred does **not** own:

- semantic meaning
- semantic truth judgment
- AI-style reasoning
- worker workspaces by default
- one giant warehouse of raw worker output
- substrate-specific method language

Alfred should stay boring, explicit, and inspectable.
If Alfred becomes a hidden reasoner, a hidden warehouse, or a wrapper-shaped pseudo-role, the Garage will drift again.
