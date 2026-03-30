# ARTIFACT AND PROOF CONTRACT v0.1
## AI Garage Artifact / Evidence / Proof Contract

## Status

Working draft.

This is not final.
It is the first serious contract for Garage artifact and proof handling.

This contract exists because the repo already has:
- a higher-level library/policy contract
- a universal language dictionary
- a library schema contract
- a tracked-plan object contract
- a handoff-envelope contract

Those authorities already rely on:
- `artifact_id`
- `artifact_ref`
- `workspace_ref`
- `payload_ref`
- `evidence_refs`
- `verification_rule`
- `done_unverified` vs `verified`

Without one explicit contract for artifact and proof handling, those fields stay half-defined and too easy to misuse.

This document does **not** replace:
- `ai_garage_library_and_policy_contract_v_0_1.md`
- `garage_universal_language_dictionary_v0_1.md`
- `LIBRARY_SCHEMA_CONTRACT_v_0_1.md`
- `TRACKED_PLAN_OBJECT_CONTRACT_v_0_1.md`
- `HANDOFF_ENVELOPE_CONTRACT_v_0_1.md`

It narrows and operationalizes the artifact/proof layer they already depend on.

---

## 1. Purpose

This contract defines the Garage artifact and proof layer.

It governs:
- what an artifact is
- what counts as evidence
- what counts as proof
- how artifacts are referenced officially
- how `artifact_ref`, `workspace_ref`, and `payload_ref` relate to each other
- how `evidence_refs` should be used
- how proof-bearing returns support tracked-plan verification
- who owns artifact creation vs official registration vs durable indexing
- how proof interacts with `done_unverified` vs `verified`
- what Alfred may record mechanically
- what Alfred must not semantically pretend to prove

It does **not** govern:
- final storage engine internals
- final filesystem layout
- final JSON Schema syntax
- final checksum implementation details
- final UI rendering of artifacts
- semantic truth of a screenshot, log, or summary by itself
- final retention policy for every artifact kind

---

## 2. Primary authority relationship

## 2.1 Library/policy contract authority
`ai_garage_library_and_policy_contract_v_0_1.md` is the higher-level authority for:
- why proof beats vibes
- why tracked work needs evidence gates
- why policy and runtime language must stay separate

## 2.2 Dictionary authority
`garage_universal_language_dictionary_v0_1.md` is the primary authority for:
- `artifact_id`
- `artifact_ref`
- `workspace_ref`
- `payload_ref`
- official call/event/state tokens
- shell field names

This contract must not silently rename those objects or tokens.

## 2.3 Library schema contract authority
`LIBRARY_SCHEMA_CONTRACT_v_0_1.md` is the schema-layer authority for:
- shared object schema organization
- `artifact-ref.schema.json`
- `workspace-ref.schema.json`
- `payload-ref.schema.json`
- later proof-related schema objects

## 2.4 Tracked-plan contract authority
`TRACKED_PLAN_OBJECT_CONTRACT_v_0_1.md` is the authority for:
- `verification_rule`
- `evidence_refs`
- `done_unverified` vs `verified`
- plan-item progression discipline

## 2.5 Handoff-envelope contract authority
`HANDOFF_ENVELOPE_CONTRACT_v_0_1.md` is the authority for:
- shell/body split
- how refs travel in official envelopes
- why refs stay in the shell while body meaning stays worker-authored

This contract must align with all of them.

---

## 3. Core distinction: artifact vs evidence vs proof

These are related but not interchangeable.

## 3.1 Artifact
An artifact is a created, found, or captured output object.

Examples:
- screenshot
- downloaded file
- extracted JSON
- test log
- diff patch
- command output file
- markdown summary
- transcript excerpt stored as a file

An artifact is an object.
It is not automatically proof.

## 3.2 Evidence
Evidence is an artifact or pointer that is being used to support a claim.

Examples:
- a screenshot attached to support a browser result
- a test log attached to support a completion claim
- a diff attached to support a code-change claim
- an extracted JSON file attached to support a structured result

Evidence is artifact-in-context.

## 3.3 Proof
Proof is evidence that satisfies the declared verification gate for the relevant claim.

Examples:
- the required test output exists and matches the item's verification rule
- the required screenshot exists and shows the claimed page state per the defined rule
- the required extracted result object exists and is attached where the rule demands it

Proof is not a vibe and not merely “some artifact exists somewhere.”

## 3.4 Design rule
The Garage must not collapse these three layers into one mush.

- artifact = object
- evidence = supporting object used for a claim
- proof = evidence that satisfies the declared gate

---

## 4. Why this layer must be explicit

The repo already uses proof language in multiple places.
Without an explicit artifact/proof contract, drift happens fast.

Failure modes this contract exists to stop:
- every file becoming “proof” by assertion
- refs being attached with no idea what they mean
- workers claiming completion with no gate discipline
- Alfred treating raw artifact existence as semantic truth
- tracked-plan `evidence_refs` becoming an unstructured junk drawer
- envelope refs and plan evidence refs drifting apart

This layer exists so the system can say, explicitly:
- what object was created
- how it is referenced
- who reported it
- whether it is merely attached evidence or actual proof for a declared rule

---

## 5. Ownership model

## 5.1 Jarvis owns artifact meaning in Jarvis work
Jarvis may create or identify:
- diffs
- test logs
- command logs
- generated code outputs
- summaries
- continuation-supporting notes
- extracted local analysis outputs

Jarvis owns the semantic claim about why those objects matter.

## 5.2 Robin owns artifact meaning in Robin work
Robin may create or identify:
- screenshots
- rendered-page extracts
- downloaded files
- browser-session outputs
- structured web result objects
- ambiguity notes tied to observed material

Robin owns the semantic claim about why those objects matter.

## 5.3 Alfred owns official registration and linkage
Alfred owns:
- minting optional `artifact_id`
- recording `artifact_ref`
- recording `workspace_ref`
- recording `payload_ref`
- linking artifacts to task/job/event/checkpoint context
- recording what kind of object was reported

Alfred does **not** own the semantic truth of what the artifact means.

## 5.4 Ledger owns durable indexing
Ledger owns:
- durable ref storage
- artifact metadata storage
- linkage indexes
- proof/evidence linkage history
- later retention and archival mechanics

---

## 6. Artifact object model

## 6.1 `workspace_ref`
This is the lowest-level pointer.
It answers:
- where the worker says the object currently lives
- which worker/runtime area it came from

Minimum expected meaning:
- `role`
- `path`

A `workspace_ref` points to location.
It does not by itself tell you whether the object is official, proof-bearing, or semantically useful.

## 6.2 `artifact_ref`
This is the official identified artifact pointer.
It answers:
- which artifact object is being referred to
- what kind of object it is
- where it lives
- who reported it

Minimum expected meaning from current authority:
- `artifact_id`
- `kind`
- `workspace_ref`
- `reported_by`

An `artifact_ref` is the main official artifact pointer.

## 6.3 `payload_ref`
This is a pointer to a worker-owned body/payload file.

It is used when:
- the meaningful body is externalized from the envelope
- the body is too large or cleaner as a file
- the envelope should stay small

A `payload_ref` is not automatically an artifact intended as proof, though it may later be used as evidence if the verification rule allows it.

---

## 7. Required vs optional artifact metadata

## 7.1 Required artifact-ref fields
At minimum, an official `artifact_ref` should carry:
- `artifact_id`
- `kind`
- `workspace_ref`
- `reported_by`

## 7.2 Optional artifact-ref fields
Recommended later fields when the implementation needs them:
- `created_at`
- `mime_type`
- `size_bytes`
- `hash`
- `description`
- `source_job_id`
- `source_event_id`

## 7.3 Anti-drift rule
Do not make every optional field mandatory too early.
The point is consistent evidence discipline, not paperwork bloat.

---

## 8. Artifact kinds

The contract needs a stable minimum artifact-kind posture without turning into a giant taxonomy war.

## 8.1 Recommended minimum kinds
- `screenshot`
- `download`
- `extract_json`
- `log`
- `diff`
- `summary`
- `report`
- `payload_file`
- `other`

## 8.2 Design rule
Keep artifact kinds broad enough to be usable.
Do not create a new official kind for every tiny edge case.

## 8.3 Anti-drift rule
Artifact kind is classification help.
It is not semantic proof by itself.

---

## 9. Evidence refs

## 9.1 Meaning
`evidence_refs` are the refs attached to a tracked-plan item or other official claim to show what evidence is being relied on.

## 9.2 Allowed evidence ref targets
Evidence refs may target:
- `artifact_ref`
- `workspace_ref`
- `payload_ref`
- later, other official ref objects if a later contract explicitly adds them

## 9.3 Preferred posture
Prefer `artifact_ref` when the object is important enough to be tracked officially.
Use raw `workspace_ref` only when the object has not yet been promoted to a formal artifact but still needs pointing.
Use `payload_ref` when the body file itself is the evidence-bearing object.

## 9.4 Anti-drift rule
Do not stuff giant raw evidence bodies into the tracked-plan object.
Use refs.

---

## 10. Proof-bearing claims

The Garage has multiple proof-bearing claim surfaces.

## 10.1 Plan-item completion claims
A plan item moving toward `verified` is a proof-bearing claim.

## 10.2 Result returns
A `result.submit` return may contain evidence-bearing refs supporting the worker's claim.

## 10.3 Failure returns
A `failure.report` return may also carry evidence:
- logs
- screenshots
- extracts
- failure traces

Failure evidence still matters.
It is not only success that needs proof.

## 10.4 Continuation and checkpoint records
A continuation note or checkpoint may carry refs that explain:
- what is already proven
- what remains unverified
- what exact objects support clean resumption

---

## 11. Verification discipline

## 11.1 Verification rules control proof, not artifact existence alone
A claim becomes verified when the declared `verification_rule` is satisfied, not just because an artifact exists.

## 11.2 `done_unverified`
Use when:
- the worker claims the step is complete enough to submit
- evidence refs exist or are being attached
- the declared proof gate is not yet satisfied or accepted

## 11.3 `verified`
Use when:
- the evidence refs satisfy the declared verification rule
- or later approved policy says another explicit gate was satisfied

## 11.4 Anti-drift rule
Do not turn “artifact attached” into “verified” automatically.
That would destroy the point of tracked proof discipline.

---

## 12. Proof bundles

A single artifact is sometimes enough.
Often it is not.

## 12.1 Meaning
A proof bundle is the set of refs and minimal metadata needed to support a claim cleanly.

## 12.2 Typical proof bundle contents
Examples:
- screenshot + extracted JSON + short summary
- diff + test log + command output
- download + hash + extract summary
- failure screenshot + log + failure summary

## 12.3 Contract stance
The Garage should be able to treat a claim as supported by:
- one evidence ref
- or a small proof bundle

Do not force all proof into one artifact.
Do not force every claim to drag a huge bundle either.

---

## 13. Artifact creation vs official promotion

## 13.1 Worker creation
A worker may create or identify an object before Alfred registers it.

## 13.2 Official promotion
An object becomes an official Garage artifact when Alfred records it as an `artifact_ref` with task/job linkage.

## 13.3 Why this distinction matters
Not every scratch file deserves official promotion.
Some do.
This contract preserves that distinction.

---

## 14. Alfred's validation boundary

## 14.1 What Alfred may validate mechanically
Alfred may validate:
- ref shape
- required artifact-ref fields
- linkage to task/job context
- whether referenced objects were declared
- whether the envelope carries refs where policy requires them
- whether a verification rule demanded evidence refs and none were attached

## 14.2 What Alfred must not semantically judge
Alfred must not pretend to determine:
- whether the screenshot truly proves the browser claim in the human sense
- whether the diff is a good diff
- whether the log proves the right thing semantically
- whether the summary interpretation is intellectually sound

That is not Alfred's role.

---

## 15. Artifact and proof interaction with the handoff envelope

## 15.1 Envelope shell posture
`artifact_refs`, `workspace_refs`, and `payload_ref` belong in the shell as official pointers.

## 15.2 Envelope body posture
The worker-authored body explains:
- what those refs mean
- why they matter
- how they support the return, failure, or continuation

## 15.3 Anti-drift rule
Do not collapse shell refs and body semantics into one field.
The envelope contract already drew that boundary. Keep it.

---

## 16. Artifact and proof interaction with the tracked plan

## 16.1 Evidence refs support plan items
A tracked-plan item uses `evidence_refs` to point at the objects supporting its completion claim.

## 16.2 Verification rules decide sufficiency
The plan's `verification_rule` determines what kind of evidence is enough.

## 16.3 Item state discipline remains intact
Artifact/proof handling must reinforce, not weaken:
- `todo`
- `in_progress`
- `needs_child_job`
- `done_unverified`
- `verified`
- `blocked`
- `abandoned`

This contract must not blur those plan-item states.

---

## 17. Artifact and proof interaction with checkpoints and continuation

## 17.1 Checkpoints
A checkpoint may capture or reference:
- proof-bearing outputs already created
- the latest relevant proof bundle
- what remains unverified
- what objects are required to resume cleanly

## 17.2 Continuation records
A continuation record may point to:
- current proof-bearing artifacts
- failure artifacts
- the last known evidence bundle
- the objects the next worker should inspect first

This is how proof survives session boundaries without relying on chat memory.

---

## 18. Storage and retention stance

## 18.1 Default posture
Alfred records refs first.
Ledger indexes durable artifact metadata and linkage.
Worker workspaces remain the default object home unless later storage policy promotes copies elsewhere.

## 18.2 Anti-drift rule
Do not turn Alfred into the warehouse for every raw file.
That was already rejected in Alfred authority.

## 18.3 Later storage policy
Later policy/storage contracts may decide:
- which artifact kinds get copied into durable storage
- which kinds remain pointer-only
- which kinds require hashes
- which kinds require retention windows

That is deferred on purpose.

---

## 19. What is not proof

The contract needs a blunt line here.

The following are **not automatically proof**:
- an artifact merely existing
- a summary merely sounding confident
- a screenshot with no declared relevance
- a log with no linkage to the claim
- a diff with no verification rule saying why it matters
- a downloaded file with no indication what it proves

Proof requires declared relation to the claim and a satisfied gate.

---

## 20. Anti-drift rules

This layer must not drift into:
- artifact sprawl with no ref discipline
- workers declaring every scratch file “proof”
- Alfred acting like a semantic reviewer
- giant raw blobs embedded into plan objects or shell headers
- checksum fetish before the base ref model is even stable
- one new artifact kind every time a weird object appears
- implicit proof rules hidden in prose with no declared verification relation

---

## 21. Implementation-facing organization guidance

Recommended future schema/object organization:

```text
schemas/objects/
  artifact-ref.schema.json
  workspace-ref.schema.json
  payload-ref.schema.json
  proof-bundle.schema.json
```

Potential supporting storage/index objects later:
- artifact metadata record
- artifact-to-job linkage record
- artifact-to-event linkage record
- proof-bundle record
- verification-result record

Potential implementation sequence:
1. stabilize ref objects already named in current authority
2. define proof-bundle object only after ref objects are clean
3. add later retention/hash/promotion rules only after the base artifact model is proven usable

---

## 22. Good vs bad usage

## 22.1 Good usage
Good usage means:
- the worker returns explicit refs
- the refs point to real objects with clear kind and origin
- the body explains what those objects support
- the tracked-plan item links those refs through `evidence_refs`
- `verified` is only used after the declared gate is actually satisfied

Example good posture:
- Robin returns a screenshot artifact, an extract JSON artifact, and a concise body summary
- the corresponding plan item carries those refs as `evidence_refs`
- the item remains `done_unverified` until the required verification rule is satisfied

## 22.2 Bad usage
Bad usage includes:
- “I attached proof” with no refs
- one giant narrative note claiming multiple things with no attached objects
- embedding raw file bodies into the shell instead of using refs
- calling an item `verified` because a screenshot exists somewhere
- promoting every temporary scratch output into an official artifact for no reason
- pretending Alfred has semantically validated what the artifact means

---

## 23. Final position

The Garage artifact/proof layer exists so the system can distinguish clearly between:
- objects
- supporting evidence
- satisfied proof gates

Jarvis and Robin create or identify the meaningful objects.
Alfred records official refs and linkage.
Ledger stores durable indexes and history.

Artifact existence is not proof.
Evidence attachment is not proof.
Proof is evidence that satisfies the declared gate.

That line has to stay hard or the rest of the contract stack turns back into bullshit.