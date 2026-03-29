# Jarvis Workbench and Progression Contract v0.1

This document defines the first‑generation contract for how the Jarvis worker role operates inside an **AI Garage**.  It specifies how Jarvis plans locally in the OpenHands workbench, how that plan becomes official state under Alfred’s control, and how Jarvis interacts with the Robin browser worker.  It fills gaps left by the OpenHands deep research pass by providing explicit object shapes, lifecycle states and policies.  It does **not** implement Alfred itself, design the Ledger schema or cover UI concerns.

## 1. Purpose

The purpose of this contract is to turn high‑level architectural intent into implementable specifications for the Jarvis role.  It defines:

* How Jarvis uses OpenHands as a **local workbench**, distinct from the Garage’s official record.
* The exact shape of the **initial plan**, **step claims**, **checkpoints**, **pivots**, **child‑job requests**, and **return envelopes**.
* The **step lifecycle**, including permissible transitions and evidence requirements.
* The minimal **Alfred call/event surface** needed to record state without becoming an AI.
* The **policy boundaries** for when Alfred automatically accepts changes versus pausing for human review.

It does **not** define the final Alfred implementation, Ledger storage details, the complete Robin contract or UI behaviour.  Those remain separate efforts.

## 2. Role of OpenHands in AI Garage

OpenHands is Jarvis’s workbench.  It provides a local sandbox with a filesystem, editor, terminal and Python execution where Jarvis can prepare, experiment and stage work.  Within the garage boundary, Jarvis has full control of this environment.  **OpenHands is not the system of record**: its local checklist, scratch notes and conversation state are **ephemeral** and exist only to support Jarvis’s reasoning.  The authoritative state of a task lives in Alfred’s Ledger plane.

OpenHands **is for**:

* Developing and testing code, editing files and running scripts in a safe sandbox.
* Drafting and maintaining a **local plan/checklist** and personal notes as Jarvis thinks through the work.
* Pre‑qualifying evidence and artifacts before submitting them for official verification.

OpenHands **is not for**:

* Storing official task state, job history or verified artifacts.
* Assigning or tracking official step statuses beyond Jarvis’s local notes.
* Making authoritative decisions about plan acceptance, pivot approval or external access.

Jarvis must never silently treat any local note or action in OpenHands as official truth.  Only when Jarvis calls Alfred with a structured payload does it become part of the Garage’s official record.

## 3. Jarvis Operating Model

Jarvis is the main reasoning and coding role.  The model below describes how Jarvis should operate within this contract:

1. **Interpret the user’s request.**  Read the task description supplied by the operator through Open WebUI and form a clear objective.
2. **Draft a local plan.**  Use OpenHands to break the mission into a sequence of **plan items** (steps), record them in a local checklist, and annotate with dependencies, verification rules and notes.  Jarvis may iterate on this plan privately.
3. **Submit the initial plan to Alfred.**  When ready, Jarvis calls `plan.submit` with a structured initial plan object (see §5).  Alfred stamps IDs and a version number and records it as the official plan for the task.
4. **Execute step‑by‑step.**  For each plan item, Jarvis:
   * Starts the step via `step.start`, works in OpenHands and uses local tools.
   * Keeps local scratch notes and interim results private.
   * If external web work is needed, submits a **child‑job request** (§10) through Alfred, waits for the result from Robin, then resumes.
   * When the step is completed locally, submits a **step‑complete claim** (§7).  Alfred records the claim, attaches evidence, applies policy and either auto‑verifies or awaits operator review.
5. **Checkpoints.**  For long tasks or before any baton pass, Jarvis proposes a **checkpoint** (§8).  Checkpoints capture a resumable anchor: the current plan version, completed steps, blocked steps and key artifacts.
6. **Pivots.**  If Jarvis discovers a fundamentally better approach, he submits a **pivot / plan revision** (§9) describing the changes.  Alfred applies risk policies to decide whether to auto‑accept, continue under policy or pause for operator approval.
7. **Finalization.**  When all plan items are verified, Jarvis submits final evidence and a completion note; Alfred records the task as completed.

Jarvis may have full power inside the sandbox (editing files, executing code, reading local documentation), but must never bypass Alfred for actions that change the official plan or interact with the outside world.

## 4. Jarvis‑Local vs Alfred‑Official Boundary

The following table summarises what data lives only in Jarvis’s local workspace versus what becomes official in Alfred/Ledger.  Jarvis is free to maintain rich local context, but Alfred only sees what is explicitly promoted.

| Category | Jarvis local only | Official (Alfred) |
| --- | --- | --- |
| **Scratch notes** | Personal reasoning notes, partial thoughts, internal hypotheses, raw chat history. | *Never recorded.* Jarvis may summarise relevant points in continuation notes or evidence. |
| **Local checklist** | A mutable list of steps with statuses maintained by Jarvis for convenience. | Not authoritative. Jarvis must promote a structured **initial plan** via `plan.submit` to create the official plan. |
| **Draft step decomposition** | Iterative breakdown of tasks; may change frequently. | Only the version submitted to Alfred becomes official; subsequent changes require a **pivot** request. |
| **Evidence preparation** | Local files, scripts, test results, screenshots pending verification. | Once attached to a claim or return envelope and referenced by ID in the Ledger, they become official artifacts. |
| **Official plan** | *None.* Jarvis must treat the Ledger’s plan as truth after creation. | `plan.submit` creates the authoritative plan.  Alfred assigns `plan_version` and `plan_id`. |
| **Official step state** | *None.* Jarvis’s local statuses have no official effect. | Alfred tracks each plan item’s state (`todo`, `in_progress`, `done_unverified`, `verified`, `blocked`, `needs_robin`, `failed`) based on calls from Jarvis and verification events. |
| **Official checkpoint** | Jarvis may keep local snapshots for convenience. | Alfred records checkpoints only when Jarvis calls `checkpoint.propose`; each checkpoint receives a unique ID. |
| **Official child‑job creation** | Jarvis may annotate local steps that will require web work. | Only `child_job.request` creates a child job; Alfred stamps a job ID and routes to Robin. |
| **Official verification state** | Jarvis may self‑assess progress. | Only Alfred (or the operator) may set `verified` status after applying policy and evidence rules. |

Jarvis must treat any local plan or status as tentative until Alfred has acknowledged and recorded a corresponding structured object.  Local to official promotion always flows through a call into Alfred.

## 5. Initial Plan Object

When Jarvis is ready to commit the first plan for a task, he calls `plan.submit` with a JSON‑serialisable object having the following structure.  Fields are required unless marked “optional”.

### Top‑Level Fields

* **`task_id`** (string) – The identifier for the parent task, assigned by Alfred when the task was created.
* **`author_role`** (string) – Must be `"jarvis"`.  Used by Alfred to verify who is submitting.
* **`title`** (string) – Human‑readable title of the overall mission.
* **`objective`** (string) – Short sentence describing what the mission aims to achieve (for example, “Prepare and commit a feature to add CSV export”).
* **`plan_description`** (string) – Optional prose description of the approach and key considerations.  Jarvis should summarise the rationale here, but long reasoning stays local.
* **`items`** (array of plan items) – Ordered list of steps, each defined as below.
* **`execution_mode`** (string) – One of `"open"`, `"guided"`, or `"strict"` following the Library/Policy contract.  Defines how Alfred will enforce policy.  Jarvis selects this according to the mission’s risk profile.

### Plan Item Fields

Each element of `items` is an object with:

* **`item_id`** (string) – A temporary identifier created by Jarvis.  Alfred will normalise these into globally unique IDs when recording the plan.
* **`title`** (string) – Brief name of the step.
* **`description`** (string) – Clear description of what Jarvis intends to do in this step.
* **`status`** (string) – Initial status must be `"todo"`; Alfred will not accept other initial states.
* **`depends_on`** (array of strings, optional) – List of other `item_id`s that must be verified before this step can start.  Use this to express ordering and prerequisites.
* **`verification_rule`** (string) – A succinct rule describing how completion will be verified (for example, “Unit tests pass on script X,” “Screenshot of correct webpage title,” “Diff shows file updated with specified text”).  Jarvis must keep it high‑level; detailed test logic stays in the sandbox.
* **`evidence_hint`** (string, optional) – Advice about what kinds of artifacts or evidence will be produced (for example, file names, screenshot types).  This helps Alfred prepare for indexing.
* **`notes`** (string, optional) – Any other clarifications Jarvis wishes to attach to this step.  These become part of the official plan.

### Fields Added by Alfred

When Alfred accepts the plan, he will:

* Assign a **`plan_id`** and **`plan_version`**.
* Normalise `item_id`s into globally unique stable IDs, preserving the order.
* Stamp `created_at` and `submitted_at` timestamps.
* Record the `author_role` and enforce that it came from Jarvis.
* Persist the plan as the official baseline.  Any subsequent changes require a pivot (§9).

### Draft vs Official

Jarvis may iterate on the plan privately, but only the version submitted to Alfred becomes official.  After submission, Jarvis must not modify local plan items without submitting a pivot request.  Jarvis may keep a personal copy of the plan with extra notes, but Alfred’s version is canonical.

## 6. Step Lifecycle Model

The following state machine governs each plan item.  Alfred enforces valid transitions; Jarvis can only request certain transitions and must supply evidence where required.

### States

* **`todo`** – Initial state.  The step exists but work has not started.  Only Jarvis may move a step from `todo` to `in_progress` via `step.start`.
* **`in_progress`** – Jarvis is actively working on this step in OpenHands.  Jarvis may keep local progress notes.  Jarvis may move the step into `done_unverified` via `step.complete_claim` or into `blocked`/`needs_robin`/`failed` via `failure.report`.
* **`needs_robin`** – Jarvis has determined the step requires web/visual work.  Jarvis must call `child_job.request`; Alfred will mark the step as `needs_robin` until a return envelope arrives.  Only Alfred may transition out of this state when dispatching/receiving.
* **`done_unverified`** – Jarvis has completed the work locally and has submitted a `step.complete_claim`.  Alfred stores the evidence and moves the step to this state.  The step is considered pending verification; Jarvis may not proceed to dependent steps until the step is verified or blocked.
* **`verified`** – Alfred (or the operator following policy) has accepted the claim and evidence.  This state unlocks dependent steps.
* **`blocked`** – The step cannot proceed due to missing input, failure, policy violation or unresolved external dependency.  A blocked step requires either additional evidence, a revised plan, or operator intervention.
* **`failed`** – Jarvis reports that the step cannot be completed under the current plan.  Jarvis should include a failure bucket and evidence in the `failure.report`.  Alfred may allow retries under policy or mark the task as failed.

### Transitions and Permissions

| From → To | Who may request | Evidence required | Notes |
| --- | --- | --- | --- |
| `todo` → `in_progress` | Jarvis via `step.start` | None | Signals that work is starting. |
| `in_progress` → `needs_robin` | Jarvis via `child_job.request` | Structured child job request (§10) | Alfred creates a child job and pauses Jarvis’s job. |
| `in_progress` → `done_unverified` | Jarvis via `step.complete_claim` | Claim summary + evidence refs | Jarvis asserts completion; Alfred verifies later. |
| `needs_robin` → `done_unverified` | Alfred automatically upon Robin return | Return envelope evidence (§11) | Jarvis resumes upon dispatch. |
| `done_unverified` → `verified` | Alfred / operator via `verification.record` | Must satisfy `verification_rule` and evidence | Only Alfred/authorised operator may set. |
| `in_progress` → `blocked` | Jarvis via `failure.report` | Failure bucket and notes | e.g. missing dependency, ambiguous spec. |
| `needs_robin` → `blocked` | Alfred via policy | N/A | If Robin fails repeatedly or policy triggers. |
| `blocked` → `in_progress` | Jarvis via `resume.note_submit` | Continuation note explaining how to unblock | Resuming after a pause or after operator approval. |
| Any → `failed` | Jarvis via `failure.report` or Alfred via policy | Failure reason and evidence | Terminal for the step and possibly the task. |

Jarvis must provide evidence and a clear claim before Alfred can verify a step.  Evidence may include file hashes, test outputs, screenshots, logs or extraction results.  Alfred uses the `verification_rule` to decide whether the claim meets the bar; Jarvis should keep this rule concise and specific.

## 7. Step‑Complete Claim Object

When Jarvis believes a step is finished, he calls `step.complete_claim` with a structured payload.  The payload must have the following fields:

* **`task_id`** (string) – Parent task ID.
* **`plan_version`** (string) – The current plan version.  Claims must reference the active plan; Alfred rejects mismatched versions.
* **`step_id`** (string) – The globally unique identifier for the plan item (assigned by Alfred when the plan was recorded).
* **`claim_summary`** (string) – A concise description of what was done and why Jarvis believes the step is complete.
* **`evidence_refs`** (array of strings) – References to artifacts stored in the sandbox (file hashes, screenshot IDs, JSON extraction manifests).  These must exist in the PO‑box broker path so Alfred can index them.
* **`verification_rule_applied`** (string) – Copy of the `verification_rule` from the plan item, indicating what check Alfred should run.
* **`continuation_note`** (string) – A structured note summarising state for the next step.  Should include decisions made, constraints learned and any partial results needed for later steps.
* **`ready_for_verification`** (boolean) – `true` if Jarvis asserts the step is ready for verification; `false` if Jarvis submits a partial claim (for example, intermediate artifact ready but more work is needed).  Partial claims remain in `in_progress` state until a final claim is submitted.

Alfred appends this claim to the Ledger, sets the step to `done_unverified`, and awaits verification.  Jarvis must not treat the step as verified until Alfred/ operator confirmation.

## 8. Checkpoint Proposal Model

A checkpoint provides a resumable anchor capturing the job’s state.  Jarvis proposes a checkpoint via `checkpoint.propose` with these fields:

* **`task_id`** (string) – The task to checkpoint.
* **`plan_version`** (string) – Current official plan version.
* **`current_step_id`** (string) – The step being worked when the checkpoint is proposed (may be `null` if between steps).
* **`completed_steps`** (array of step IDs) – Steps verified so far in this plan version.
* **`blocked_steps`** (array of step IDs, optional) – Steps currently in `blocked` state and waiting for unblocking or revision.
* **`key_artifact_refs`** (array of strings, optional) – References to critical artifacts that must be preserved (for example, compiled binaries, downloaded datasets, large files).
* **`resume_point`** (string) – Short note describing where to resume after restore (for example, “resume after step 2, before starting step 3”).
* **`reason`** (string) – Explanation of why a checkpoint is needed (for example, “preparing to hand off to Robin,” “saving progress before long external wait”).

Alfred records the checkpoint, assigns a unique `checkpoint_id`, and requires that a checkpoint exist before any baton pass (child job dispatch or model switch) to ensure restart safety.  Checkpoints are not verification events; they are state snapshots.

## 9. PIVOT / PLAN REVISION MODEL

If Jarvis determines that the original plan should change (due to new information, discovered blockers, or a better approach), he must submit a **pivot request** via `plan.revise`.  The pivot is a structured description of the proposed new plan and the differences from the current plan.  This section defines the pivot object and risk classes.

### Pivot Object Fields

* **`task_id`** (string) – Parent task ID.
* **`current_plan_version`** (string) – The version of the plan currently in effect.
* **`proposed_plan_version`** (string) – A new unique version identifier Jarvis proposes.  Alfred will verify uniqueness and stamp if accepted.
* **`pivot_type`** (string) – High‑level classification of the change.  Allowed values:
  * `reorder_steps` – Changing the sequence without altering content or dependencies.
  * `add_steps` – Adding new plan items (with full definitions).
  * `remove_steps` – Removing existing items.
  * `modify_step` – Changing descriptions or verification rules of existing items.
  * `goal_change` – Changing the mission’s objective.
  * `scope_expansion` – Broadening the scope of work (for example, adding external domains or deliverables).
  * `scope_reduction` – Narrowing the scope.
  * `external_access_change` – Adding new web domains, download allowances or export destinations.
  * `destructive_action` – Introducing actions that may delete or overwrite files or external resources.
* **`changes`** (array) – A list describing each change.  Each element should identify the affected `step_id` (if applicable) and specify the new fields (for example, new description, new verification rule, new dependencies).  For `add_steps` this includes full plan item definitions.
* **`goal_changed`** (boolean) – `true` if the overall mission objective has changed.  Changing the goal almost always requires human review.
* **`scope_changed`** (boolean) – `true` if the scope of the mission is expanded or reduced.  Alfred uses this to trigger review.
* **`destructive`** (boolean) – `true` if the new plan involves destructive operations (file deletion, irreversible external side effects).  Destructive pivots always require human approval.
* **`external_access_changed`** (boolean) – `true` if the pivot introduces new external domains, APIs, downloads or exports.  External access changes may be high‑risk.
* **`evidence_refs`** (array of strings, optional) – References to artifacts or information that justify the pivot (for example, a URL showing the new requirement, a failed build log demonstrating the need for a new library).
* **`human_review_requested`** (boolean, optional) – Jarvis can set this to `true` to explicitly ask for operator review even if policy might allow automatic acceptance.
* **`justification`** (string) – A concise rationale for why the pivot is needed.  Jarvis must provide enough context for Alfred and the operator to decide whether to accept.
* **`proposed_plan`** (object) – The full new plan object in the same shape as the initial plan (§5), reflecting the proposed changes.  Jarvis must supply a complete replacement rather than diffs alone.

### Risk Classes and Alfred Policy

Alfred does not semantically understand the pivot; it applies deterministic policy based on declared fields.  Policies classify pivots into three risk tiers:

* **Low‑risk revisions** – Reordering steps, adding clarifying notes, or splitting a step into multiple sub‑steps *without* altering the goal, scope or external access, and without destructive actions.  Alfred may auto‑accept and record these changes as the new plan version.
* **Medium‑risk revisions** – Adding non‑destructive steps, modifying verification rules or descriptions, or reducing scope.  Alfred can record and continue automatically but must log the change for later operator inspection.  Evidence references strengthen the case.
* **High‑risk revisions** – Any pivot where `goal_changed`, `scope_changed`, `destructive`, or `external_access_changed` is `true`, or if Jarvis explicitly requests human review.  Alfred must pause progression and await operator approval.  The operator may approve, reject or request adjustments.

Alfred never infers semantics; it only inspects boolean flags and pivot types.  Jarvis must accurately label the pivot to ensure proper handling.  If Jarvis mislabels a high‑risk pivot as low‑risk, this is considered a policy violation.

## 10. Robin Child‑Job Request Model

Jarvis delegates web and visual tasks to Robin via `child_job.request`.  The request body must be structured to allow Alfred to route work and enforce policy.  The following fields are required unless marked optional:

* **`task_id`** (string) – Parent task ID.
* **`parent_job_id`** (string) – The current Jarvis job ID (assigned by Alfred when Jarvis started this leg).
* **`objective`** (string) – Clear description of what Robin must accomplish (for example, “Search for the official release date of product X on the vendor’s website”).
* **`reason`** (string) – Why web/visual work is needed (for example, “Local code cannot determine the release date; requires visiting the site”).
* **`constraints`** (object, optional) – Map of constraints such as time limits (`seconds`), maximum pages to visit (`max_pages`), or specific instructions (`no_logins: true`).
* **`allowed_domains`** (array of strings) – Fully qualified domain names or patterns (for example, `["example.com", "*.github.com"]`) that Robin may visit.  Robin must not access other domains unless a new pivot is approved.
* **`downloads_allowed`** (boolean) – If `true`, Robin may download files; otherwise downloads are disallowed.
* **`expected_output`** (object) – Definition of what structured data Robin should return.  For example, fields like `{ "release_date": "string" }` or a schema describing a list of results.  Jarvis should keep this as a machine‑readable specification.
* **`success_criteria`** (string or array) – Conditions that define success (for example, “release_date field is a valid date”, “at least one screenshot captured”, “JSON length > 0”).
* **`artifact_expectations`** (array of strings, optional) – Types of artifacts to capture (for example, “screenshot_homepage”, “downloaded_manual.pdf”).
* **`retry_budget`** (integer) – Number of retries Alfred may grant to Robin before marking the step as failed.
* **`continuation_hints`** (string, optional) – Information Robin should include in the return envelope to help Jarvis resume (for example, “Please return the URL of the final page visited.”).

Alfred will stamp a **`child_job_id`**, set policy scopes and create a checkpoint if none exists.  Alfred then routes the request to Robin and pauses the Jarvis job until the return is received.

## 11. Robin Return Envelope Model

When Robin finishes its job, it calls `result.submit` with a structured return envelope that Alfred records and forwards to Jarvis.  The envelope has these fields:

* **`task_id`** (string) – Parent task ID.
* **`parent_job_id`** (string) – The Jarvis job ID that spawned this child job.
* **`child_job_id`** (string) – The job ID assigned to Robin.
* **`result_status`** (string) – One of `succeeded`, `partial`, `blocked`, or `failed`.  `partial` means some but not all expected outputs were produced; `blocked` means Robin could not complete due to constraints; `failed` means the job cannot progress under current parameters.
* **`summary`** (string) – Plain‑English summary of what was done and what was found.
* **`structured_result`** (object) – JSON object matching the `expected_output` specification.  If `partial`, some fields may be missing; if `failed`, this may be empty.
* **`visited_urls`** (array of strings, optional) – Ordered list of URLs visited during execution.
* **`artifacts`** (array of strings) – References to screenshots, downloaded files or other evidence captured in the PO‑box broker.
* **`ambiguity_notes`** (string, optional) – Notes about uncertainties, ambiguities or conflicts encountered (for example, “Multiple release dates found, chose earliest”).
* **`failure_bucket`** (string, optional) – If `result_status` is `failed`, a categorisation of why (for example, `no_results_found`, `domain_blocked`, `policy_violation`).
* **`continuation_hints`** (string, optional) – Guidance for Jarvis on how to interpret or use the result (for example, “Use the `release_date` field in step 2 of your plan”).

Alfred stores this envelope, attaches artifacts and either dispatches the Jarvis job for resumption or, if `failed`, applies failure policy (retry or block).  Jarvis consumes the envelope and updates his local plan or pivot accordingly.

## 12. MINIMUM ALFRED CALL / EVENT SURFACE

To support this contract without turning Alfred into an AI, the control plane needs only a small set of calls and event types.  Each call corresponds to a deterministic state transition; Alfred validates fields, stamps metadata, writes to the Ledger and routes jobs.

### Calls (invoked by workers or UI)

* **`task.create(request_body)`** – Create a new parent task.  `request_body` contains user objective and high‑level parameters (not detailed here).  Returns `task_id`.
* **`plan.submit(initial_plan)`** – Jarvis submits the initial plan (§5).  Alfred stamps IDs and records a new `plan_version`.
* **`plan.revise(pivot_body)`** – Jarvis proposes a pivot (§9).  Alfred applies risk policy, creates a new plan version if approved and returns status.
* **`step.start(step_id)`** – Jarvis signals that he is beginning work on a plan item.  Alfred marks the step `in_progress` and leases the job to Jarvis.
* **`step.complete_claim(claim_body)`** – Jarvis submits a completion claim (§7).  Alfred records the evidence and sets the step `done_unverified`.
* **`checkpoint.propose(checkpoint_body)`** – Jarvis proposes a checkpoint (§8).  Alfred records it and returns a `checkpoint_id`.
* **`child_job.request(child_job_request)`** – Jarvis requests Robin to perform a web/visual task (§10).  Alfred stamps IDs, ensures a checkpoint exists, pauses the parent job and dispatches the child job.
* **`result.submit(return_envelope)`** – Robin submits results (§11).  Alfred records the result, attaches artifacts and dispatches the parent job for resumption.
* **`failure.report(failure_body)`** – Jarvis or Robin reports a failure on the current job, including a failure bucket, evidence and notes.  Alfred marks the step/job `blocked` or `failed` according to policy.
* **`verification.record(record_body)`** – Operator or automated verifier records a verification decision.  Alfred transitions the step from `done_unverified` to `verified` or back to `in_progress` if verification fails.
* **`resume.note_submit(note_body)`** – Jarvis submits continuation notes after resuming from a pause or checkpoint, explaining state and next actions.

### Events / State Notifications (emitted by Alfred)

The Ledger should record events such as: `task.created`, `plan.submitted`, `plan.revised`, `step.started`, `step.claimed`, `step.done_unverified`, `step.verified`, `checkpoint.created`, `child_job.requested`, `job.dispatched`, `result.submitted`, `failure.reported`, `job.blocked`, `job.failed`, `job.resumed`, `job.completed`.  Each event includes timestamps, actor, job IDs and references to artifacts or pivot bodies.  UI and audit tooling can subscribe to these events to render job timelines.

## 13. Human Review Triggers

Alfred enforces deterministic policy but cannot make value judgements.  The following conditions always require operator approval before progression can continue:

* **Goal change** – The mission objective is different from what the user originally requested.
* **Scope expansion** – The plan widens to include additional deliverables, domains or complexity beyond the initial brief.
* **Destructive actions** – Steps or pivots that delete or overwrite files, modify external systems, or perform irreversible actions.
* **External access changes** – New websites, APIs or file exports that were not included in the initial plan or policy scope.
* **Import/export policy changes** – Shifts in what data can be imported into or exported out of the garage (for example, enabling downloads when previously disallowed).
* **Reduced verification requirements** – Any attempt to lower evidence requirements or skip tests must be approved.
* **Repeated failed pivots or retries** – Multiple consecutive failures may indicate a deeper issue and require human intervention.
* **Policy overrides** – If Jarvis requests an override of standing policy via `human_review_requested`, Alfred pauses.
* **High‑risk pivot flags** – Any pivot with `goal_changed`, `scope_changed`, `destructive`, or `external_access_changed` flagged `true`.

The operator interface should surface these events as “review required” prompts with the structured payloads, evidence and justifications so that the operator can accept, reject or request changes.

## 14. What Stays Out of This Contract

To maintain focus, this contract deliberately leaves several areas unspecified:

* **Alfred implementation details** – The data structures, transaction handling and concurrency model for Alfred are out of scope.  Only the external contract matters here.
* **Ledger schema design** – The underlying tables, indexes and storage layout are not defined; only the conceptual domains are referenced.
* **UI and console behaviour** – Presentation, navigation and operator UX flows are not covered.  The contract ensures the UI has the data it needs.
* **Robin’s internal contract** – While this document defines the request and return envelopes, the full Robin tool suite and browser automation schema remain separate.
* **Tool plane specifications** – Detailed JSON‑RPC schemas for each tool (for example, `browser.click`, `python.execute`) are not included.
* **Advanced orchestration features** – Concurrency, multi‑agent extensions, auto‑splitting tasks, or dynamic scaling are intentionally deferred until the core baton‑passing model is proven.

## 15. Final Contract Position

This contract codifies the intended working relationship inside the AI Garage:

* **Jarvis makes the plan**: he decomposes the mission, drafts steps, produces code, performs analysis and writes evidence inside OpenHands.
* **Alfred records and gates**: it stamps IDs, persists plans, enforces the step lifecycle, stores checkpoints, applies policy and determines whether operator intervention is needed.  Alfred is deterministic and never does AI reasoning or tool‑calling.
* **Robin assists on specialist web work**: through formal child jobs, Robin navigates the web, captures data and returns structured results and artifacts.
* **OpenHands is Jarvis’s workbench**: a local sandbox for doing the work.  Its checklists and notes are not official truth.  Only when Jarvis promotes data via Alfred does it become canonical.
* **The official truth lives in the Ledger**: job state, plan versions, checkpoints, handoffs, return envelopes and verification records are stored durably outside any single worker runtime.

With these roles and boundaries clarified, subsequent passes can focus on implementing Jarvis’s local work style and Alfred’s deterministic controller while preserving the integrity of the AI Garage.