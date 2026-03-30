# TRACKED PLAN OBJECT CONTRACT v0.1
## AI Garage Tracked Plan / Checklist Contract

## Status

Working draft.

This is not final.
It is the first serious contract for the Garage's tracked plan object.

This contract exists because the Garage already has:
- a higher-level library/policy contract
- a universal language dictionary
- a library schema contract

The tracked plan is already defined as a first-class runtime object in those authorities.
This contract makes that object explicit and implementation-ready.

This document does **not** replace:
- `ai_garage_library_and_policy_contract_v_0_1.md`
- `garage_universal_language_dictionary_v0_1.md`
- `LIBRARY_SCHEMA_CONTRACT_v_0_1.md`

It narrows and operationalizes the tracked plan object they already call for.

---

## 1. Purpose

This contract defines the Garage tracked plan object.

It governs:
- the tracked plan header object
- the tracked plan item object
- plan versioning
- current active item handling
- plan state/status handling
- item dependency semantics
- verification rule structure
- evidence reference structure
- done-unverified vs verified discipline
- task/job linkage
- plan revision/update rules
- continuation/checkpoint interaction

It does **not** govern:
- final SQLite DDL
- final JSON Schema file contents
- final UI rendering
- semantic truth of evidence
- full policy table storage format
- arbitrary worker reasoning style

---

## 2. Primary authority relationship

## 2.1 Library/policy contract authority
`ai_garage_library_and_policy_contract_v_0_1.md` is the higher-level authority for:
- why the tracked plan exists
- why it is first-class
- why proof gates matter
- why dependency-based progression matters

## 2.2 Dictionary authority
`garage_universal_language_dictionary_v0_1.md` is the primary token authority for:
- `plan_version`
- plan item state tokens
- linked task/job IDs
- official shared-language token naming

## 2.3 Library schema contract authority
`LIBRARY_SCHEMA_CONTRACT_v_0_1.md` is the schema-layer authority for:
- where tracked-plan and plan-item objects fit in the schema stack
- how they relate to call envelopes and shared objects

This contract must align with all three.

---

## 3. Why the tracked plan is first-class

The tracked plan exists because long jobs degrade when they are left to:
- vague chat memory
- worker improvisation with no progression object
- one giant summary blob
- unstated dependencies
- no evidence gate between "done" and "actually done"

The tracked plan is a first-class Garage object because it must:
- survive baton passes
- survive session ends
- survive model swaps
- survive crashes and resumptions
- preserve what is already complete
- preserve what is blocked
- preserve what still needs proof
- preserve what comes next

It is not generic memory.
It is not a vibe list.
It is not a loose scratchpad.

It is the official execution list for complex work.

---

## 4. Ownership model

## 4.1 Jarvis owns plan meaning
Jarvis owns:
- initial plan authorship
- plan item wording
- dependency reasoning
- revision proposals
- completion claims
- continuation interpretation

## 4.2 Alfred owns official plan registration
Alfred owns:
- official recorded plan version linkage
- plan/task/job shell linkage
- official record of plan revision events
- official checkpoint linkage to tracked plan state
- official refs/pointers tied to plan progress

## 4.3 Ledger owns durable storage/indexing
Ledger owns:
- durable plan header storage
- durable plan item storage
- revision history
- evidence ref indexing
- plan status history

## 4.4 Robin does not own the parent plan
Robin may contribute:
- evidence
- continuation hints
- returned results that affect item status

Robin does **not** own:
- parent plan authority
- final interpretation of overall plan structure
- official plan revision authority

---

## 5. Tracked plan header object

The tracked plan header is the umbrella object describing one official plan version.

## 5.1 Required header fields
- `task_id`
- `plan_version`
- `created_by`
- `plan_status`
- `items`

## 5.2 Usually required in complex-runtime use
- `job_id`
- `current_active_item`
- `created_at`

## 5.3 Recommended full header field set
- `task_id`
- `job_id`
- `plan_version`
- `created_by`
- `created_at`
- `updated_at`
- `plan_status`
- `current_active_item`
- `summary`
- `notes`
- `items`

## 5.4 Header meaning
- `task_id` = umbrella mission this plan belongs to
- `job_id` = job context under which this plan version was authored or recorded
- `plan_version` = monotonically increasing version label
- `created_by` = usually `jarvis`
- `plan_status` = current umbrella condition of the plan
- `current_active_item` = item currently being advanced, if any
- `items` = the official item list for that plan version

---

## 6. Plan status rules

The plan header needs its own umbrella status, separate from individual plan item states.

## 6.1 Recommended plan status values
- `draft`
- `active`
- `blocked`
- `completed`
- `abandoned`
- `superseded`

## 6.2 Meaning
- `draft` = proposed but not yet recorded as active authority
- `active` = current official tracked plan version
- `blocked` = the plan cannot cleanly progress right now
- `completed` = all required items are verified or deliberately resolved
- `abandoned` = the plan is intentionally stopped
- `superseded` = replaced by a later plan version

## 6.3 Anti-drift rule
Do not overload plan status with item status language.
The plan header condition and the item conditions are separate things.

---

## 7. Plan item object

A plan item is one structured unit of intended work under the tracked plan.

## 7.1 Required item fields
- `item_id`
- `title`
- `description`
- `status`

## 7.2 Recommended standard item fields
- `item_id`
- `title`
- `description`
- `status`
- `depends_on`
- `verification_rule`
- `evidence_refs`
- `notes`

## 7.3 Item meaning
- `item_id` = stable item label within the plan version
- `title` = short human-readable item title
- `description` = what the item actually means
- `status` = current item state
- `depends_on` = prerequisite item IDs
- `verification_rule` = what counts as sufficient proof
- `evidence_refs` = refs to proof artifacts/evidence objects
- `notes` = local comments/continuation detail

---

## 8. Plan item state rules

The official plan item states are already defined by shared authority.

## 8.1 Allowed plan item states
- `todo`
- `in_progress`
- `needs_child_job`
- `done_unverified`
- `verified`
- `blocked`
- `abandoned`

## 8.2 Meaning
- `todo` = not started yet
- `in_progress` = actively being worked
- `needs_child_job` = blocked pending a Robin or other delegated leg
- `done_unverified` = claimed complete but proof not yet accepted
- `verified` = completed with sufficient evidence
- `blocked` = cannot progress cleanly
- `abandoned` = intentionally dropped from this plan version

## 8.3 Anti-drift rule
Do not collapse:
- `done_unverified`
- `verified`

That distinction is one of the main reasons the tracked plan exists.

---

## 9. Item identity rules

## 9.1 Item IDs are local to a plan version
An `item_id` only needs to be unique within the plan version unless later policy promotes globally unique item IDs.

## 9.2 Recommended item ID posture
Keep item IDs:
- short
- boring
- deterministic within the plan

Examples:
- `I001`
- `I002`
- `I003`

## 9.3 Anti-drift rule
Do not overload item IDs with semantic essays.

---

## 10. Dependency semantics

The Garage uses dependency-based progression, not a dumb assumption that every item always runs in rigid numeric order.

## 10.1 `depends_on`
`depends_on` identifies prerequisite item IDs that must be resolved before this item may progress.

## 10.2 Meaning of resolution
By default, a prerequisite is resolved when it is:
- `verified`
- or deliberately `abandoned` / otherwise explicitly accepted by plan revision logic

## 10.3 Recommended dependency rule
A dependent item must not move from:
- `todo` -> `in_progress`
or
- `todo` -> `done_unverified`

unless its required dependencies are resolved.

## 10.4 Anti-drift rule
Do not use dependency semantics as a hidden excuse for freeform chaos.
If order matters, represent it explicitly.

---

## 11. Verification rule object

Each plan item should define what proof is required before the item can be treated as verified.

## 11.1 Purpose
A verification rule prevents:
- fake completion claims
- vague "I think it's done"
- irreversible progression on unproven work

## 11.2 Recommended verification rule types
- `artifact_exists`
- `artifact_matches_kind`
- `result_present`
- `summary_present`
- `test_pass`
- `manual_review_required`
- `evidence_bundle_present`
- `downstream_item_confirms`
- `no_extra_requirement`

## 11.3 Recommended rule structure
At minimum:
- `type`
- optional `params`
- optional `notes`

Example conceptual structure:
```json
{
  "type": "artifact_matches_kind",
  "params": {
    "kind": "screenshot"
  },
  "notes": "Need screenshot showing successful page state."
}
```

## 11.4 Anti-drift rule
Do not pretend the verification rule itself proves semantic truth.
It defines the proof gate structure, not universal correctness.

---

## 12. Evidence refs

Plan items need explicit evidence references.

## 12.1 Purpose
`evidence_refs` tie proof-bearing artifacts or payload refs to the item.

## 12.2 Allowed evidence ref kinds
Evidence refs may point to:
- `artifact_ref`
- `workspace_ref`
- `payload_ref`
- later maybe `event_id` or other official record refs if formalized

## 12.3 Minimum stance
A plan item should be able to say:
- what evidence exists
- where it lives
- who reported it

## 12.4 Anti-drift rule
Do not store giant raw evidence bodies inside the plan item object if refs will do.

---

## 13. Done-unverified vs verified discipline

This distinction must stay hard.

## 13.1 `done_unverified`
Use when:
- the worker claims the item is complete enough to submit
- but the required evidence gate is not yet satisfied

## 13.2 `verified`
Use only when:
- the required evidence rule is satisfied
- or later policy explicitly accepts the item as verified through another allowed path

## 13.3 Why this matters
Without this split, the tracked plan collapses back into self-asserted AI truth.

---

## 14. Relationship to task_id and job_id

## 14.1 `task_id`
The tracked plan belongs to the parent mission.

## 14.2 `job_id`
A plan version may be recorded under a particular current job context.

## 14.3 Design rule
A plan belongs primarily to the task.
A job provides current execution context.

## 14.4 Anti-drift rule
Do not force every plan change into a completely job-local interpretation.
The plan is a task-level progression object even when created from a current job leg.

---

## 15. Plan versioning

## 15.1 `plan_version`
Every official plan revision increments `plan_version`.

## 15.2 Version rule
When Jarvis materially revises the tracked plan:
- create a new recorded plan version
- mark the older one `superseded` if replaced
- preserve revision history

## 15.3 What counts as material
Examples:
- added or removed major items
- changed dependencies
- changed verification rules
- changed the intended overall execution structure

## 15.4 What does not necessarily require a new version
Examples:
- small note edits
- attaching more evidence refs
- updating item state within the existing plan version

---

## 16. Current active item rules

## 16.1 Purpose
`current_active_item` identifies the plan item the system is presently pushing forward.

## 16.2 Allowed states
It may be:
- an `item_id`
- `null` when no single item is currently active
- a later structured pointer if the runtime needs more detail

## 16.3 Anti-drift rule
Do not treat `current_active_item` as proof that the item is progressing correctly.
It is a pointer, not a correctness judgment.

---

## 17. Revision and update rules

## 17.1 Item-state updates
Normal progression updates may change:
- `status`
- `evidence_refs`
- `notes`

without forcing a new plan version.

## 17.2 Structural revision
If the actual plan structure changes materially:
- increment `plan_version`
- preserve old version
- record why the revision happened

## 17.3 Continuation-aware revision
If the plan changes because Robin returned new findings or a blockage, the revision should preserve:
- what changed
- why it changed
- what old item(s) it superseded

---

## 18. How Jarvis authors plans

Jarvis should author:
- the initial plan
- plan revisions
- item completion claims
- dependency logic
- verification-rule intent
- continuation notes explaining what changed

Jarvis should not assume that authoring the plan makes it official by itself.
Official recording happens when Alfred/Ledger registers it.

---

## 19. How Alfred records plans

Alfred should record:
- `task_id`
- `job_id`
- `plan_version`
- plan shell metadata
- official registration event
- linkage to evidence refs and checkpoints where relevant

Alfred should not semantically rewrite the plan body just because it thinks it knows better.

---

## 20. How Ledger stores/indexes plans

Ledger should store:
- plan headers
- plan items
- plan version history
- item state history
- evidence ref indexes
- checkpoint linkage
- timestamps
- supersession lineage

The storage layer should make it possible to reconstruct:
- what the plan was
- what changed
- when it changed
- what evidence supported each verified item

---

## 21. Continuation and checkpoint interaction

## 21.1 Continuation
A continuation record may summarize:
- current plan version
- current active item
- blocked items
- next recommended item
- relevant evidence refs

## 21.2 Checkpoints
A checkpoint may anchor:
- current plan version
- current active item
- item states at the time of checkpoint
- refs to the evidence bundle supporting resumption

## 21.3 Design rule
Tracked plans, continuation records, and checkpoints should reinforce each other.
They are not redundant blobs.

---

## 22. What is not plan state

Do **not** treat the following as the tracked plan itself:
- raw conversation text
- giant narrative summaries
- all artifacts ever created
- the whole task history
- every event log entry
- policy tables
- arbitrary scratch notes with no item linkage

The plan is the official execution object, not the whole universe.

---

## 23. Anti-drift rules

The tracked plan must not drift into:
- vague project diary text
- one giant status paragraph
- proofless "done" claims
- rigid fake waterfall sequencing
- uncontrolled item churn with no versioning
- Robin-owned parent-task authority
- Alfred semantically inventing the plan meaning
- one-off ad hoc fields added every time a weird case appears

---

## 24. Implementation-facing organization guidance

Recommended future object organization:

```text
schemas/objects/
  tracked-plan.schema.json
  plan-item.schema.json
```

Potential storage split:
- plan header table/object
- plan item table/object
- plan revision history
- evidence ref link table/object

Potential runtime fields:
- active plan version for task
- active item pointer
- per-item evidence refs
- per-item verification rule blob/object

---

## 25. Final position

The tracked plan is a first-class Garage execution object.

It exists to:
- preserve structure
- preserve dependencies
- preserve evidence gates
- preserve resumability
- preserve truthful progression

Jarvis authors the meaning.
Alfred records the official shell/version/linkage.
Ledger stores the durable object and history.

The tracked plan must remain:
- explicit
- versioned
- evidence-aware
- dependency-aware
- resumable
- small enough to use
- strict enough to stop bullshit
