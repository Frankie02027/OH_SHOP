# POLICY TABLE CONTRACT v0.1
## AI Garage Standing Policy Record Contract

## Status

Working draft.

This is not final.
It is the first serious contract for Garage policy records and policy-table structure.

This contract exists because the repo already has:
- a higher-level library/policy contract
- a universal language dictionary
- a library schema contract
- role contracts
- tracked-plan and handoff contracts
- an artifact/proof contract

Those authorities already assume that policy exists as a standing rulebook layer above runtime job language.
What the repo still needed was one explicit contract for how policy records themselves should be shaped, scoped, versioned, activated, and linked.

This document does **not** replace:
- `ai_garage_library_and_policy_contract_v_0_1.md`
- `garage_universal_language_dictionary_v0_1.md`
- `LIBRARY_SCHEMA_CONTRACT_v_0_1.md`
- the role master contracts

It narrows and operationalizes the policy-record layer they already depend on.

---

## 1. Purpose

This contract defines the Garage policy-table layer.

It governs:
- what a policy record is
- what scope fields it needs
- how policy versions should work
- how active vs inactive policy records should be represented
- how policy text/rule content relates to policy metadata
- how role-specific and task-specific policies relate to global policy
- how policy overrides should be layered
- how policy records should be indexed and referenced
- what Alfred may enforce mechanically from policy records
- what policy records must not drift into

It does **not** govern:
- final SQLite DDL
- final JSON Schema syntax
- final UI policy editor behavior
- final hot-reload mechanics
- whether policy text lives inline or in attached markdown artifacts in every case
- semantic truth of worker behavior after a policy exists

---

## 2. Primary authority relationship

## 2.1 Library/policy contract authority
`ai_garage_library_and_policy_contract_v_0_1.md` is the higher-level authority for:
- the two-domain model
- policy as standing rulebook above runtime language
- the recommended policy scopes
- the idea that policy should be tracked as structured records and optionally backed by longer handbook-style files

## 2.2 Dictionary authority
`garage_universal_language_dictionary_v0_1.md` remains the primary authority for:
- core runtime tokens
- call types
- event types
- official state/status tokens
- official IDs and shell field names

This contract must not silently invent alternate runtime-language tokens.

## 2.3 Library schema contract authority
`LIBRARY_SCHEMA_CONTRACT_v_0_1.md` remains the schema-layer authority for how policy-related schemas should later be organized.

## 2.4 Role master contract authority
The role master contracts remain the behavioral authorities for the meaning of role policy content.
This contract governs the record/table layer for policy, not the full prose of every role handbook.

---

## 3. Why the policy-table layer must exist

The repo already distinguishes:
- standing operating rulebook
- runtime job language

Without a policy-table contract, policy drifts into one of two bad extremes:
- giant loose markdown files with no activation/version/indexing discipline
- ad hoc runtime flags pretending to be policy with no durable authority trail

The policy-table layer exists so the Garage can say, explicitly:
- which policy record is active
- which scope it applies to
- which version is current
- whether it is global, role-specific, or task-specific
- where the full policy body lives
- what superseded what

That is the difference between a real rulebook layer and a pile of vibes.

---

## 4. Policy domain vs runtime domain

## 4.1 Policy domain
Policy is standing rulebook material.
It tells workers:
- who they are
- what lane they own
- what boundaries they must respect
- what proof discipline applies
- when to stop, escalate, checkpoint, or hand off

## 4.2 Runtime domain
Runtime language is job-specific execution material.
It tells the system:
- what work is being requested now
- what happened during a specific job
- what result or failure came back
- what refs and state transitions exist

## 4.3 Design rule
Policy records sit above runtime records.
They are loaded first and persist across many jobs until deliberately changed.

---

## 5. Policy record object

A policy record is the official structured record for one policy body/version.

## 5.1 Required policy-record fields
- `policy_key`
- `scope`
- `version`
- `status`
- `content_ref`

## 5.2 Recommended additional fields
- `title`
- `description`
- `created_at`
- `updated_at`
- `effective_from`
- `effective_to`
- `supersedes_policy_key`
- `task_id`
- `approved_by`
- `notes`

## 5.3 Meaning
- `policy_key` = stable identity for the policy family
- `scope` = where it applies
- `version` = revision number for that policy family
- `status` = whether the record is active, draft, superseded, etc.
- `content_ref` = pointer to the actual body content

---

## 6. Policy scopes

The higher-level library/policy contract already defines the recommended scopes.
This contract keeps them explicit.

## 6.1 Required core scopes
- `global`
- `alfred`
- `jarvis`
- `robin`
- `task_override`

## 6.2 Meaning
- `global` = applies Garage-wide unless a narrower allowed override exists
- `alfred` = applies to Alfred behavior/enforcement posture
- `jarvis` = applies to Jarvis role behavior
- `robin` = applies to Robin role behavior
- `task_override` = task-scoped override policy that does not rewrite the standing global handbook itself

## 6.3 Anti-drift rule
Do not invent new scopes casually.
If a new scope is truly needed later, it should be added explicitly by later authority, not by random implementation convenience.

---

## 7. Policy status values

The policy table needs its own record status layer.

## 7.1 Recommended policy record statuses
- `draft`
- `active`
- `inactive`
- `superseded`
- `archived`

## 7.2 Meaning
- `draft` = proposed but not yet active authority
- `active` = currently authoritative for its scope/key
- `inactive` = stored but not currently authoritative
- `superseded` = replaced by a later version
- `archived` = retained for history/reference only

## 7.3 Anti-drift rule
Do not reuse runtime task/job states as policy-record states.
This is a separate domain.

---

## 8. Policy versioning

## 8.1 `version`
Each policy family should version monotonically.

## 8.2 Version rule
When a policy changes materially:
- create a new version record
- preserve the older version
- mark the older active version `superseded` when the new one becomes active

## 8.3 What counts as material
Examples:
- changed worker boundary rule
- changed retry/timeout/allowed-domain policy
- changed proof standard
- changed escalation requirement

## 8.4 What does not require a new active version by itself
Examples:
- fixing formatting only
- correcting a typo in explanatory notes while leaving the substantive policy unchanged

If you want a strict immutable-record posture later, create a new version anyway.
This contract allows that stricter stance.

---

## 9. Policy identity rules

## 9.1 `policy_key`
`policy_key` identifies the stable policy family.

Examples:
- `global.operating`
- `alfred.control`
- `jarvis.behavior`
- `robin.behavior`
- `task_override.T000001`

## 9.2 Design rule
Keep policy keys readable and boring.
Do not turn them into narrative strings.

## 9.3 Anti-drift rule
Do not confuse `policy_key` with `title`.
The key is the stable identity. The title is human-readable labeling.

---

## 10. Content body vs metadata record

## 10.1 Metadata record
The policy table stores the structured record:
- scope
- status
- version
- activation status
- linkage
- content pointer

## 10.2 Policy body content
The actual policy body may live:
- inline in a text field
- in a markdown artifact pointed to by `content_ref`
- in another structured content record if later storage wants that

## 10.3 Design rule
Do not force the table record itself to carry the full giant handbook text if a clean `content_ref` is better.
But also do not force every short policy into an external file if inline storage is cleaner.

This contract allows either.

---

## 11. `content_ref`

## 11.1 Purpose
`content_ref` points to the actual policy content body.

## 11.2 Minimum meaning
A `content_ref` should identify:
- where the content lives
- what kind of content it is

Recommended minimal posture:
- `kind`
- `path` or equivalent location pointer

## 11.3 Anti-drift rule
Do not let policy records exist with no way to retrieve the actual rule content.
A policy table row with missing body linkage is bullshit.

---

## 12. Policy layering and override rules

## 12.1 Default posture
The Garage should apply policy from broad to narrow:
1. `global`
2. role-specific (`alfred`, `jarvis`, `robin`)
3. `task_override`

## 12.2 Override rule
A narrower policy may refine a broader one only where the broader one allows that refinement or where later authority explicitly says the override class is allowed.

## 12.3 Anti-drift rule
A task override is not permission to silently rewrite the entire Garage rulebook.
It is task-scoped refinement, not uncontrolled mutation.

---

## 13. Task override records

## 13.1 Purpose
A task override policy exists so a specific task can carry narrower rules without rewriting the standing global or role-level handbooks.

## 13.2 Required linkage
A `task_override` policy record should normally carry:
- `task_id`
- `policy_key`
- `scope = task_override`
- `version`
- `status`
- `content_ref`

## 13.3 Anti-drift rule
Do not create task overrides with no linked `task_id`.
That would make them fake pseudo-global policy.

---

## 14. Alfred's relationship to policy records

## 14.1 What Alfred may do mechanically
Alfred may:
- load active policy records
- determine which record is active for each required scope
- enforce mechanical rule surfaces derived from policy
- reject malformed or out-of-policy runtime envelopes based on declared policy metadata

## 14.2 What Alfred must not do
Alfred must not:
- invent policy content on the fly and call it canonical
- semantically rewrite role policy bodies because it "knows better"
- silently activate a draft policy as if it were approved

---

## 15. Recommended policy families

The higher-level contract already implies these families.
This contract makes the record families concrete.

## 15.1 Global operating policy
Typical key:
- `global.operating`

## 15.2 Alfred control policy
Typical key:
- `alfred.control`

## 15.3 Jarvis worker policy
Typical key:
- `jarvis.behavior`

## 15.4 Robin worker policy
Typical key:
- `robin.behavior`

## 15.5 Task override policy
Typical key pattern:
- `task_override.<task_id>`

---

## 16. Approval and activation posture

## 16.1 Approval metadata
The policy table may later need:
- `approved_by`
- `approved_at`
- `activation_reason`

## 16.2 Minimum stance now
Even if those fields are not mandatory yet, the system must still distinguish clearly between:
- proposed draft policy
- active policy
- historical policy

## 16.3 Anti-drift rule
Do not treat “file exists in repo” as automatically equivalent to “active policy.”
Activation must be explicit.

---

## 17. Policy record history

The storage layer should make it possible to answer:
- what policy was active at a given time
- what superseded it
- which task override applied to which task
- which version a worker should have been following when a job occurred

If you cannot answer those questions later, your policy table is half-broken.

---

## 18. Interaction with runtime records

## 18.1 Policy is not a runtime envelope
Policy records are not handoff envelopes.
Do not mix them.

## 18.2 Policy may govern runtime behavior
Policy may control:
- allowed domains
- retry posture
- proof standards
- escalation boundaries
- download behavior
- checkpoint requirements

## 18.3 Design rule
Policy records shape runtime behavior from above.
They are not runtime event substitutes.

---

## 19. Interaction with artifact/proof layer

Policy may define:
- what evidence kinds are required for a given class of work
- when manual review is required
- what proof discipline a role must follow

But policy records are not themselves proof artifacts.
They govern proof behavior.
They are not proof of task completion.

---

## 20. Interaction with tracked-plan and continuation

Policy may influence:
- whether a checkpoint is required before a baton pass
- whether a plan item needs manual review
- what evidence standard applies
- what continuation detail is required

But the tracked plan, checkpoint record, and continuation record remain separate objects.
Do not collapse them into policy state.

---

## 21. Storage split stance

## 21.1 Structured record layer
The table/record layer should store:
- `policy_key`
- `scope`
- `version`
- `status`
- linkage fields
- activation metadata
- `content_ref`

## 21.2 Content layer
The actual prose/rule content may live:
- inline
- in markdown artifacts
- in a dedicated content table later

## 21.3 Anti-drift rule
Do not make the table so thin that it cannot answer activation/scope/version questions.
Do not make it so bloated that every giant handbook body must live inline no matter what.

---

## 22. Anti-drift rules

The policy-table layer must not drift into:
- runtime event history
- vague markdown piles with no active/inactive distinction
- ad hoc config flags pretending to be policy authority
- silently activated drafts
- unscoped role rules
- task overrides with no linked task
- one giant blob row with no version/history discipline

---

## 23. Implementation-facing organization guidance

Recommended future schema/object organization:

```text
schemas/objects/
  policy-record.schema.json
  policy-content-ref.schema.json
```

Potential storage objects later:
- policy record table
- policy content table or artifact store
- policy activation history table
- policy-to-task linkage table

Recommended implementation order:
1. define policy record object
2. define content_ref object
3. define active-policy resolution rules by scope
4. add approval/activation metadata only after the base record model is stable

---

## 24. Good vs bad usage

## 24.1 Good usage
Good usage means:
- one stable `policy_key`
- explicit `scope`
- explicit `version`
- explicit `status`
- retrievable policy body through `content_ref`
- clear active vs superseded distinction
- task overrides linked to real tasks

## 24.2 Bad usage
Bad usage includes:
- a role policy file sitting somewhere in repo with no activation record
- multiple conflicting policy files all pretending to be current
- using runtime task states as policy statuses
- inventing new policy scopes casually
- treating a task override like permission to rewrite the whole Garage rulebook
- storing no body pointer and pretending the table row alone is enough

---

## 25. Final position

The Garage policy-table layer exists so policy stops being a pile of vibes and starts being a real standing rulebook record system.

A policy record must answer, explicitly:
- what policy family this is
- what scope it applies to
- what version it is
- whether it is active
- where the actual content lives
- what it superseded
- whether it is task-linked when it is a task override

That is the minimum serious policy-table discipline.
