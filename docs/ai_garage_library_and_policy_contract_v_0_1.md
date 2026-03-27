# AI Garage Library and Policy Contract v0.1

## Status

Working draft. This is not a final truth document. It is the first serious contract for the Garage's shared operating language, tracked-plan discipline, and policy layers.

This contract is intentionally focused on:
- the shared language between Alfred, Jarvis, and Robin
- the minimum library of calls/events/statuses
- the tracked plan/checklist behavior for long jobs
- the policy and handbook layers that teach workers how to behave in the Garage

This contract is **not** the full Alfred architecture document and is **not** the full Ledger schema document.

---

## 1. Purpose

The AI Garage needs a shared language that is:
- structured enough for Alfred and the Ledger to track work cleanly
- flexible enough that Jarvis and Robin are not forced into one dumb reasoning path
- small enough that the workers can generate it dynamically without drowning in form-fill bullshit
- explicit enough that long tasks do not degrade into one giant lost chat session

The language exists to control:
- how work is requested
- how work is handed off
- how results return
- how failures are reported
- how proof is attached
- how plan progress is tracked

The language does **not** exist to hardcode one exact strategy for how the workers must think.

---

## 2. Core design rules

### 2.1 Interaction shape, not thinking strategy
The shared language should constrain **interaction shape** and **return shape**, not the internal reasoning strategy of Jarvis or Robin unless strict mode is explicitly requested.

### 2.2 Small top-level library
The top-level library should stay small. Work variety belongs in payloads, plan items, and policy layers rather than exploding into dozens of one-off top-level verbs.

### 2.3 AI writes the meaning; Alfred writes the official shell
For dynamic handoffs:
- Jarvis or Robin writes the semantic body of the request/return
- Alfred validates it, stamps the official metadata, and routes it
- Ledger stores both the body and the official shell

### 2.4 Proof beats vibes
A step is not considered complete just because an AI says so. Plan items should move through verification gates using artifacts, logs, extracted data, tests, screenshots, or other explicit evidence.

### 2.5 Policy is not generic memory
Garage operating rules, worker handbooks, and behavior constraints are policy/rulebook material, not generic memory history.

---

## 3. Roles in this contract

### Alfred
Deterministic controller.

In this contract Alfred is responsible for:
- creating official task and job records
- validating and routing handoffs
- recording official state transitions
- coordinating checkpoints
- enforcing policy boundaries
- preventing task drift and duplicate chaos

Alfred is **not** the creative author of task meaning.

### Jarvis
Main inside-the-garage worker.

In this contract Jarvis is responsible for:
- interpreting the parent task
- creating the initial tracked plan/checklist for complex work
- deciding the next proposed work chunk
- drafting child-job requests when outside/browser work is needed
- resuming parent work using returned Robin results
- attaching evidence and continuation notes

### Robin
Browser/web/visual worker.

In this contract Robin is responsible for:
- performing online/browser work
- returning structured web results and artifacts
- capturing evidence of what was actually seen or retrieved
- drafting structured return bodies for Alfred/Jarvis

### Ledger
Durable recorder and indexed archive.

In this contract Ledger is responsible for:
- storing official state history
- storing raw event history
- indexing artifacts and proof
- storing plan versions and plan item status history
- storing policy records and handbook versions

---

## 4. Two-domain model: standing policy first, runtime language second

The Garage should not treat policy/handbook material as just another runtime layer.

There are **two different domains**:

### Domain A: Standing Operating Rulebook
This is the long-lived handbook/policy/rulebook domain.

This domain answers:
- what kind of environment this is
- what Alfred, Jarvis, and Robin are supposed to be
- how each role is expected to behave
- what evidence standards exist
- what boundaries and escalation rules exist
- what "doing your job correctly" means in the Garage

This domain is:
- loaded first
- mostly stable across jobs
- changed deliberately, not casually
- closer to a company handbook than to task chatter

### Domain B: Runtime Job Language
This is the dynamic task/handoff/progress language used during actual work.

This domain answers:
- what work is being requested right now
- what happened during execution
- what state the task/job is in now
- what result or failure came back
- what proof was attached
- what plan item is active or verified

This domain is:
- job-specific
- dynamic
- created and updated constantly during execution
- subordinate to the standing rulebook

### Design rule
Policy/handbook/rulebook material sits **above** the runtime grammar.

The runtime grammar should operate **inside** the standing operating rulebook, not beside it as just another same-level layer.

## 5. Runtime Garage language model

The runtime language is layered. It is not one giant flat bag of words.

### Layer 1: Calls / Actions
Actual requests to do something.

### Layer 2: Events
Recorded facts about what happened.

### Layer 3: Statuses
Current condition labels.

### Layer 4: Payload kinds / job kinds / result kinds
The detailed flavor of work or outputs.

### Layer 5: Tracked plan / checklist
The execution list for long or complex tasks, with dependencies and proof gates.

---

## 5. v0.1 top-level call library

The Garage should begin with a deliberately small call library.

### 5.1 Required core calls
1. `task.create`
2. `assignment.dispatch`
3. `assignment.accept`
4. `child_job.request`
5. `context.request`
6. `checkpoint.create`
7. `result.submit`
8. `failure.report`

### 5.2 Likely near-term additions
9. `task.cancel`
10. `human_input.request`

### 5.3 Design note
The Garage should **not** create a new top-level call for every tiny situation.

Examples of what should **not** become top-level calls:
- `download_pdf_and_summarize`
- `test_page_flow_and_return_screenshot`
- `look_up_package_version`
- `read_docs_then_patch_code`

Those should usually be represented as:
- one of the core calls above
- plus a payload field like `job_kind`, `result_kind`, or `expected_output`

---

## 6. v0.1 event library

Events are facts, not commands.

### 6.1 Recommended v0.1 events
- `task.created`
- `assignment.dispatched`
- `assignment.accepted`
- `run.started`
- `run.blocked`
- `checkpoint.created`
- `result.submitted`
- `result.accepted`
- `run.completed`
- `run.failed`
- `task.cancelled`
- `task.completed`
- `task.failed`
- `plan.created`
- `plan.revised`
- `plan.item.started`
- `plan.item.done_unverified`
- `plan.item.verified`
- `plan.item.blocked`

### 6.2 Design note
Events should stay boring, factual, and append-only. They are for history and auditability, not storytelling.

---

## 7. v0.1 status library

Statuses should stay small and boring.

### 7.1 Task / job statuses
- `queued`
- `running`
- `blocked`
- `waiting_on_child`
- `completed`
- `failed`
- `cancelled`

### 7.2 Plan item statuses
- `todo`
- `in_progress`
- `blocked`
- `needs_child_job`
- `done_unverified`
- `verified`
- `abandoned`

### 7.3 Design note
Statuses are state labels, not calls.

---

## 8. ID policy

### 8.1 IDs workers must know
Workers should know the official IDs required to do their current work.

Minimum AI-visible IDs:
- `task_id`
- `job_id`

Optional AI-visible ID:
- `handoff_id` if explicit tracking of a particular exchange becomes useful

### 8.2 IDs workers should not mint as official truth
Jarvis and Robin should **not** invent official new task IDs, job IDs, checkpoint IDs, or other canonical records.

### 8.3 ID ownership
- Alfred creates official new task/job/handoff/checkpoint records
- Jarvis and Robin carry official IDs for currently assigned work
- Jarvis and Robin may include request-local draft references if needed, but Alfred should convert those into official records

### 8.4 Human explanation
- `task_id` = the whole case / umbrella mission
- `job_id` = the current active work chunk / baton leg

---

## 9. Handoff structure: two-layer model

Every serious handoff should have two layers.

### 9.1 Layer A: Protocol shell
This is the machine-facing shell Alfred validates and stamps.

Typical fields:
- message type
- schema version
- task_id
- job_id
- from_role
- to_role
- timestamp
- execution_mode
- priority
- checkpoint requirement

### 9.2 Layer B: Mission body
This is the AI-authored meaning layer.

Typical fields:
- objective
- reason_for_handoff
- constraints
- expected_output
- success_criteria
- artifact_refs
- notes

### 9.3 Design rule
The AI writes the body. Alfred validates, enriches, and routes the protocol shell.

---

## 10. Execution-mode policy

The language must be directional without being overly constraining.

### 10.1 Execution modes
- `open` = worker chooses method freely within policy
- `guided` = worker has freedom inside some rails
- `strict` = worker must follow specific steps or return shape

### 10.2 Why this exists
This lets the same library support:
- open-ended research or discovery
- constrained browser collection
- reproducible exact-step operations

### 10.3 Default stance
The system should not default everything to strict mode. Strict mode should be used deliberately when reproducibility, compliance, or safety demands it.

---

## 11. Tracked plan / checklist object

For long or complex tasks, Jarvis should create an initial tracked plan/checklist. This is not generic memory. It is a first-class execution object.

### 11.1 Why it exists
The Garage needs a structured anti-hallucination mechanism for long jobs.

The tracked plan exists so that:
- Jarvis does not rely on vague long-context self-memory
- the task has an explicit execution list
- each item has proof conditions
- continuation remains coherent across long sessions and baton passes

### 11.2 Who creates it
Jarvis proposes the initial plan.

### 11.3 Who records it
Alfred/Ledger stores the official tracked version and its revisions.

### 11.4 Plan header fields
- `task_id`
- `job_id`
- `plan_version`
- `created_by`
- `current_active_item`
- `plan_status`

### 11.5 Plan item fields
- `item_id`
- `title`
- `description`
- `status`
- `depends_on`
- `verification_rule`
- `evidence_refs`
- `notes`

### 11.6 Verification discipline
A plan item should not move from `done_unverified` to `verified` without evidence.

### 11.7 Dependency rule
The Garage should use dependency-based progression, not a stupid universal assumption that every numbered item must always run in rigid order.

Better rule:
A dependent next step cannot proceed until its prerequisite step(s) are verified.

---

## 12. Worker-generated content policy

### 12.1 Jarvis should dynamically generate
- child job request bodies
- initial tracked plans
- plan revisions when reality changes
- completion claims on plan items
- continuation notes
- summary candidates

### 12.2 Robin should dynamically generate
- structured result bodies
- browser/web evidence notes
- extracted result objects
- continuation hints for Jarvis
- domain limitations and failure notes

### 12.3 Alfred should not dynamically invent the meaning
Alfred is not supposed to creatively author the mission semantics of a child job or result.

Alfred should:
- validate
- stamp
- record
- route
- reject malformed or out-of-policy requests

---

## 13. Standing policy / handbook domain

This is the part closest to a company handbook.

### 13.1 What policy is
Policy is the stable operating rulebook that tells workers how to behave and perform their duties in the Garage.

It teaches:
- role identity
- role boundaries
- allowed tool surfaces
- escalation behavior
- evidence discipline
- handoff discipline
- what counts as acceptable professional behavior inside the Garage
- what kinds of shortcuts are forbidden
- when a worker should stop, ask, escalate, or hand off

### 13.2 What policy is not
Policy is not:
- generic memory
- raw event history
- the runtime job grammar itself
- a specific task execution plan
- a step-by-step answer for the current assignment

Policy tells the worker **how to operate correctly**, not the exact custom strategy for every job.

### 13.3 Policy position in the system
Policy is not a late runtime layer.

Policy is:
- loaded first
- standing by default across jobs
- intentionally updated rather than casually rewritten
- the parent rulebook that the runtime job language lives under

### 13.4 Policy scopes
Recommended scopes:
- `global`
- `alfred`
- `jarvis`
- `robin`
- `task_override`

### 13.5 Policy storage stance
Policy should be tracked as structured records in SQLite and optionally backed by versioned text files for longer handbook-style content.

---

## 14. v0.1 policy families

### 14.1 Global operating policy
Defines:
- overall Garage rules
- role boundaries
- allowed interaction patterns
- proof discipline
- escalation rules

### 14.2 Alfred control policy
Defines:
- what Alfred is allowed to validate or reject
- what Alfred may record as official state
- retry budget interpretation
- checkpoint behavior
- handoff requirements

### 14.3 Jarvis worker policy
Defines:
- what Jarvis should try locally first
- when Jarvis must request Robin
- how Jarvis creates tracked plans
- how Jarvis claims completion and provides proof
- how Jarvis writes continuation notes

### 14.4 Robin worker policy
Defines:
- what browser/web tasks Robin owns
- what evidence Robin must return
- how Robin reports domain limitations or ambiguity
- download and screenshot behavior
- required structured return fields

### 14.5 Task override policy
Defines task-specific overrides when necessary without mutating the global handbook.

---

## 15. Storage split for this contract

### 15.1 SQLite should hold
- policy records
- active versions
- status flags
- plan headers and plan items
- task/job linkage
- structured state
- artifact indexes
- summary indexes

### 15.2 JSONL should hold
- append-only raw event history
- receipts
- raw tails
- black-box timeline records

### 15.3 Artifact files should hold
- screenshots
- logs
- extracted JSON
- markdown summaries
- handoff body artifacts if needed
- larger handbook/policy documents
- proof bundles

---

## 16. Minimal AI-authored handoff body

The AI-authored part of a handoff should stay small enough that workers can create it reliably on the fly.

### 16.1 Recommended minimum fields
- `objective`
- `reason_for_handoff`
- `constraints`
- `expected_output`
- `success_criteria`
- `artifact_refs`
- optional `notes`

### 16.2 Why this should stay small
If the AI-authored body becomes too bureaucratic, the workers will waste energy filling out forms instead of doing work.

---

## 17. v0.1 official design stance

### 17.1 The library should be small
Target shape:
- about 8 core calls
- about 10 to 15 important events
- about 6 to 7 statuses
- richer payloads and policy layers underneath

### 17.2 The language should be layered
Do not flatten calls, events, statuses, policy, and plan items into one giant vocabulary bag.

### 17.3 The plan/checklist is first-class
For complex work, the tracked plan should be treated as an official object, not as loose chat notes.

### 17.4 Proof is required
The Garage should distinguish between:
- `done_unverified`
- `verified`

### 17.5 Alfred is the mailman plus border guard, not the creative author
Jarvis and Robin write the meaningful semantic body. Alfred validates, records, and routes it.

---

## 18. Immediate next contracts that should follow this one

1. **Library Schema Contract v0.1**
   - exact field schemas for calls/events/statuses

2. **Tracked Plan Object Contract v0.1**
   - exact plan header/item schema
   - verification rule types
   - dependency semantics

3. **Policy Table Contract v0.1**
   - exact SQLite policy record format
   - scope/version/status rules

4. **Handoff Envelope Contract v0.1**
   - exact shell/body split
   - AI-authored vs Alfred-authored fields

5. **Artifact and Proof Contract v0.1**
   - how evidence is attached, referenced, and verified

---

## 19. Open questions not yet frozen

- whether `handoff_id` should be AI-visible in v1 or kept internal unless needed
- whether plan items should always belong to a job or may sometimes belong directly to the task
- whether `assignment.accept` should be required for all worker legs or only when explicit acknowledgement matters
- exactly how much Alfred should normalize or rewrite malformed worker payloads versus rejecting them
- whether policy text should live mostly in SQLite text fields or mostly as versioned markdown artifacts with SQLite indexing

---

## 20. Bottom line

The Garage should not be built around one giant vague memory blob.

It should be built around:
- a small shared call library
- a separate event history
- a small status vocabulary
- a first-class tracked plan/checklist object
- a policy/handbook layer
- proof-based progression
- Alfred as validator/router/recorder
- Jarvis and Robin as the semantic authors of dynamic handoffs and returns

