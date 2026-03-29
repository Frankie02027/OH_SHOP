# Jarvis Workbench Examples v0.1

The following examples illustrate how the contract defined in `JARVIS_WORKBENCH_AND_PROGRESSION_CONTRACT_v_0_1.md` works in practice.  They show representative data structures and flows for common situations.  These are not comprehensive but should be concrete enough to serve as reference models.  Prose explanations accompany the structured payloads; the real implementation will exchange JSON.

## 1. Simple Local Coding Task

**User request:** “Create a Python script that adds two numbers and prints the result.”

### Jarvis’s Local Plan

Jarvis drafts a plan in OpenHands:

1. Create a new file `adder.py`.
2. Write a function `add(a, b)` that returns `a + b`.
3. Write a `main` section that reads two numbers and prints the sum.
4. Test the script with sample inputs.
5. Notify the operator.

Jarvis records this in a local checklist.  Once satisfied, he submits the following initial plan to Alfred:

```json
{
  "task_id": "T1001",
  "author_role": "jarvis",
  "title": "Simple Adder Script",
  "objective": "Create and test a Python script that adds two numbers",
  "plan_description": "Break the task into file creation, implementation, testing, and reporting.",
  "execution_mode": "open",
  "items": [
    {"item_id": "step1", "title": "Create file", "description": "Create adder.py in the workspace", "status": "todo", "verification_rule": "File adder.py exists in workspace", "notes": "Use the file system tools"},
    {"item_id": "step2", "title": "Implement add function", "description": "Define add(a, b) that returns a+b", "status": "todo", "depends_on": ["step1"], "verification_rule": "Function definition exists and passes tests"},
    {"item_id": "step3", "title": "Implement main logic", "description": "Read two numbers and print sum", "status": "todo", "depends_on": ["step2"], "verification_rule": "Script prints correct sum for inputs"},
    {"item_id": "step4", "title": "Test script", "description": "Run adder.py with sample inputs", "status": "todo", "depends_on": ["step3"], "verification_rule": "Test output matches expected"},
    {"item_id": "step5", "title": "Notify operator", "description": "Summarise the work and final result", "status": "todo", "depends_on": ["step4"], "verification_rule": "Message summarises completion and test results"}
  ]
}
```

Alfred normalises `item_id`s and returns `plan_version: 1` and a `plan_id`.  Jarvis begins work by calling `step.start` on the first step.  After completing the file creation, he calls `step.complete_claim` with an evidence reference (hash of the file) and a continuation note describing the created file.  Alfred sets the step to `done_unverified`.  An automated verification script (or operator) checks that `adder.py` exists and marks the step `verified`.

Jarvis repeats this pattern for each step: starting it, working locally, submitting a completion claim with evidence (unit test results, program output), and waiting for verification.  Once all steps are verified, Jarvis submits a completion note in step 5, Alfred records the task as done and notifies the operator.

## 2. WEB-DEPENDENT TASK

**User request:** “Find the official release date of the fictitious product ‘Widget Z’ from the manufacturer’s website and update the README with this date.”

### Jarvis’s Initial Plan

Jarvis realises that he will need to consult the web.  He drafts the following plan and submits it via `plan.submit`:

```json
{
  "task_id": "T2001",
  "author_role": "jarvis",
  "title": "Update README with Widget Z release date",
  "objective": "Retrieve the official release date of Widget Z from Acme Corp’s website and record it in README.md",
  "execution_mode": "guided",
  "items": [
    {"item_id": "s1", "title": "Research release date", "description": "Use web search to find the official release date of Widget Z from acme.example.com", "status": "todo", "verification_rule": "Structured result contains release_date", "notes": "Requires Robin"},
    {"item_id": "s2", "title": "Update README", "description": "Edit README.md to include the release date", "status": "todo", "depends_on": ["s1"], "verification_rule": "README.md contains release date"},
    {"item_id": "s3", "title": "Commit changes", "description": "Commit README.md with updated date", "status": "todo", "depends_on": ["s2"], "verification_rule": "Git log shows commit with updated README"}
  ]
}
```

### Delegating to Robin

Jarvis starts step `s1` and quickly realises this step requires web browsing.  He pauses local work and submits a child‑job request:

```json
{
  "task_id": "T2001",
  "parent_job_id": "J2001-jarvis-leg-1",
  "objective": "Retrieve the official release date of Widget Z from acme.example.com",
  "reason": "The information is only available on the manufacturer’s website.",
  "constraints": {"seconds": 60, "max_pages": 5, "no_logins": true},
  "allowed_domains": ["acme.example.com"],
  "downloads_allowed": false,
  "expected_output": {"release_date": "string"},
  "success_criteria": ["release_date is in ISO format", "At least one supporting screenshot"],
  "artifact_expectations": ["screenshot_product_page"],
  "retry_budget": 2,
  "continuation_hints": "Return the release_date in the structured_result."
}
```

Alfred validates this, creates a checkpoint, assigns `child_job_id: J2001-robin-leg-1` and dispatches the job to Robin.  Jarvis’s job is paused.  Robin navigates to `acme.example.com`, finds the release date and returns:

```json
{
  "task_id": "T2001",
  "parent_job_id": "J2001-jarvis-leg-1",
  "child_job_id": "J2001-robin-leg-1",
  "result_status": "succeeded",
  "summary": "Found release date on the product page.",
  "structured_result": {"release_date": "2026-02-15"},
  "visited_urls": ["https://acme.example.com/products/widget-z"],
  "artifacts": ["artifact://J2001-robin-leg-1/screenshot_product_page.png"],
  "continuation_hints": "Use structured_result.release_date in your README update."
}
```

Alfred records the result and resumes Jarvis’s job.  Jarvis updates README.md locally, submits a completion claim for step `s2` with evidence (a diff showing the new date), waits for verification, then commits the change in step `s3`.  Once all steps are verified, the task completes.

## 3. Pivot Example

**Scenario:** Jarvis is tasked with adding a CSV export feature.  His initial plan involves writing a custom parser, but midway through he discovers a standard library function that meets the need more safely.  He decides to pivot.

### Original Plan (simplified)

Steps:

1. Analyse requirements.
2. Write a custom CSV parser.
3. Integrate parser into the application.
4. Write tests and verify.

### Pivot Trigger

During step 2, Jarvis finds that the language’s standard library already has a `csv` module that satisfies the requirements.  Using it reduces complexity and risk.  Jarvis decides to remove the custom parser step, replace it with “use standard library,” and adjust subsequent steps.

### Pivot Request

Jarvis submits the following pivot via `plan.revise`:

```json
{
  "task_id": "T3001",
  "current_plan_version": "1",
  "proposed_plan_version": "2",
  "pivot_type": "modify_step",
  "changes": [
    {
      "step_id": "step2", 
      "new_title": "Use standard csv module", 
      "new_description": "Leverage the built‑in csv module instead of writing a custom parser.",
      "new_verification_rule": "Parser uses built‑in csv module; tests pass"
    }
  ],
  "goal_changed": false,
  "scope_changed": false,
  "destructive": false,
  "external_access_changed": false,
  "evidence_refs": ["artifact://T3001/logs/discovery_note.md"],
  "justification": "Built‑in csv module reduces complexity and risk.",
  "proposed_plan": {
    "task_id": "T3001",
    "author_role": "jarvis",
    "title": "Add CSV export",
    "objective": "Provide CSV export functionality using standard library",
    "execution_mode": "guided",
    "items": [
      {"item_id": "step1", "title": "Analyse requirements", "description": "Confirm fields for export", "status": "todo", "verification_rule": "Requirements doc exists"},
      {"item_id": "step2", "title": "Use standard csv module", "description": "Implement export using built‑in csv module", "status": "todo", "depends_on": ["step1"], "verification_rule": "Exported CSV matches specification"},
      {"item_id": "step3", "title": "Integrate into application", "description": "Call csv export function in app", "status": "todo", "depends_on": ["step2"], "verification_rule": "Application writes CSV correctly"},
      {"item_id": "step4", "title": "Write tests and verify", "description": "Implement tests for CSV export", "status": "todo", "depends_on": ["step3"], "verification_rule": "Tests pass"}
    ]
  }
}
```

Because the goal and scope did not change and no destructive actions or new external access are introduced, this is a **medium‑risk revision**.  Alfred accepts it automatically, records `plan_version: 2`, and Jarvis continues under the new plan.  If the pivot had involved adding a new external domain or deleting files, Alfred would have paused for operator review.

## 4. Failure / Blocked Example

**Scenario:** Jarvis is instructed to compile a C project.  He creates the initial plan with steps to configure, build and test.  During compilation, he encounters a missing dependency and cannot proceed.

### Failure Report

While working on step “Compile project,” Jarvis realises the environment lacks a required library.  He cannot fix this locally.  He submits a failure report:

```json
{
  "task_id": "T4001",
  "plan_version": "1",
  "step_id": "compile", 
  "failure_bucket": "missing_dependency", 
  "summary": "Compilation failed due to missing libfoo", 
  "evidence_refs": ["artifact://T4001/build_log.txt"],
  "details": "Makefile indicates libfoo is required but not present.  Cannot proceed without operator intervention or pivot."
}
```

Alfred records the failure, sets the step state to `blocked`, and pauses the job.  The operator is notified.  Possible resolutions include:

* **Operator installs the dependency** and uses the UI to resume the job.  Jarvis then calls `resume.note_submit` explaining how he will retry and restarts the step.
* **Jarvis pivots the plan** to download and build `libfoo` before compiling the project.  He submits a pivot request (likely high‑risk because it adds a download) that Alfred routes for human review.
* **Task cancellation** if the operator decides not to proceed.

This example shows how structured failure reporting keeps the official record clear and prevents Jarvis from silently skipping failed steps.

## 5. Checkpoint / Resume Example

**Scenario:** Jarvis is performing a long data processing task that involves multiple hours of computation.  Before handing control to Robin for a web lookup, he wants to ensure progress is saved.

### Creating a Checkpoint

Jarvis is at step 2 of a four‑step plan (data download, process data, analyse results, write report).  Steps 1 and 2 are verified.  He proposes a checkpoint before starting a Robin leg to fetch additional context:

```json
{
  "task_id": "T5001",
  "plan_version": "1",
  "current_step_id": null,
  "completed_steps": ["step1", "step2"],
  "blocked_steps": [],
  "key_artifact_refs": ["artifact://T5001/output/processed_data.csv"],
  "resume_point": "Start analysis with processed_data.csv",
  "reason": "Preparing to hand off web lookup to Robin; want a safe restore point."
}
```

Alfred records this checkpoint as `checkpoint_id: CP5001`.  A child job is then requested to fetch external data.  If the system crashes or the external lookup fails catastrophically, Alfred can restore the workspace to `CP5001` and reassign the job.

### Resuming After a Pause

Later, the operator pauses the job overnight.  When resuming, Jarvis calls `resume.note_submit`:

```json
{
  "task_id": "T5001",
  "job_id": "J5001-jarvis-leg-1",
  "checkpoint_id": "CP5001",
  "note": "Resuming analysis after pause.  Processed data is loaded; starting step3."
}
```

Alfred records the continuation note, reassigns the job, and Jarvis proceeds with the remaining steps.

This example demonstrates how checkpoints and resumption notes provide durable recovery without relying on the chat session or unstructured memory.