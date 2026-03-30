# Phase 2 — Review Pack Artifacts

> **Future-work / non-authoritative runtime document.**
> This file is a specification for later work.
> It does not describe a currently implemented subsystem.
> Do not treat it as proof that review-pack tooling already exists.

(Starts with item #9 from the prior Phase 1 todo list.)

## 9) Review Pack (human audit bundle)

### Objective
Every autonomous run that changes files must leave behind a **reviewable bundle** so a human can audit the work quickly in VS Code (Source Control + diff view) without digging through logs.

This is **not** about committing or opening PRs. The agent does not touch git history. The bundle is just files.

### Hard rules
- Never run `git commit`, `git push`, `gh pr`, etc.
- Never write outside the mounted workspace except the approved OH_SHOP download path.
- Keep bundle paths deterministic.

### Output location (deterministic)
Inside the repo/workspace:
- `/workspace/artifacts/review_pack/<run_id>/`

Where `<run_id>` is:
- `YYYYMMDD_HHMMSS_<short_hash>`

### Required files in every bundle
1) `summary.md`
   - task goal (one sentence)
   - what changed (bullets)
   - what was verified (exact commands run)
   - current status (PASS/FAIL and why)
   - next actions if FAIL

2) `patch.diff`
   - unified diff of all changes
   - produced by `git diff` if repo is git, otherwise by filesystem diff tool

3) `touched_files.txt`
   - newline-separated list of paths modified/created/deleted

4) `verify.log`
   - stdout/stderr captured from the verifier command(s)

5) `tool_trace.jsonl`
   - append-only JSONL of key tool calls for this run
   - include at least: time, tool_name, inputs summary, outputs summary, exit_code

### Minimum implementation (Phase 2)
Implement a small helper that can be called from:
- OpenHands agent flow (preferred)
- `oh-browser-mcp` (only when it writes files)
- any future tasks

Implementation must support:
- `begin_run(task_name: str) -> run_id`
- `record_change(file_path: str, action: create|modify|delete)`
- `record_command(cmd: str, cwd: str, exit_code: int, stdout_tail: str, stderr_tail: str)`
- `finalize_run(status: PASS|FAIL, notes: str)`

### Verifier integration
If the repo has `scripts/verify_phase*.sh`, run it and capture output.
Otherwise run the Phase-specific default verifier command stored in `AGENTS.md`.

### Verification (Phase 2 acceptance)
A) Trigger a run that edits at least 2 files.
B) Confirm a new bundle folder exists under `artifacts/review_pack/<run_id>/`.
C) Confirm all required files exist and are non-empty.
D) Confirm `patch.diff` applies cleanly (`git apply --check patch.diff`) when repo is git.

### Out of scope
- No git commits.
- No PR creation.
- No UI work.
