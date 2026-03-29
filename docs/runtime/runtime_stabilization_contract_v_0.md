# Runtime Stabilization Contract v0.1

## Status
Working contract for the next engineering phase.

## Date Context
Current reference date: March 27, 2026.

## Purpose
This contract defines the **first serious cleanup phase** for the current OH_SHOP / pre-Garage stack.

The purpose of this phase is **not** to complete AI Garage.
The purpose is **not** to redesign the full long-term system.
The purpose is **not** to add Alfred, the Ledger, baton-passing, memory, or policy execution layers.

The purpose of this phase is to do one thing correctly:

**stabilize the current runtime so it stops lying about what it is, how it starts, what it uses, and which files actually matter.**

This contract exists because the project currently has:
- conflicting runtime truths
- stale docs outranking live behavior in practice
- multiple patch layers with weak authority boundaries
- local runtime state mixed with repo truth
- version skew between OpenHands-related components
- dead or semi-dead architecture branches still sitting in the active tree
- a browser/tooling lane that changed in practice faster than the docs changed

Until this runtime stabilization work is done, any further AI Garage work will be built on a dirty and misleading base.

---

## Non-Goals
This phase does **not** include the following work:

- implementing Alfred
- implementing the Garage Ledger
- implementing memory/continuation storage for Jarvis/Robin/Alfred
- implementing baton-passing contracts between AIs
- designing VM orchestration for the final Garage
- rebuilding the full repo into a new multi-service Garage architecture
- finishing Phase C bridge ideas
- preserving every historical path out of sentiment
- cleaning docs for cosmetic reasons alone
- chasing every theoretical improvement before runtime truth is stabilized

If a change does not directly improve runtime truth, configuration truth, patch truth, or reproducibility, it is outside this contract.

---

## Core Problem Statement
The current system is not failing because the overall mission is stupid.
The current system is failing because multiple partially-true stories are competing at the same time.

Those competing stories include:

1. **Compose/runtime truth**
   - what actually starts
   - what containers actually run
   - which images and overrides are actually used

2. **Persisted runtime settings truth**
   - what OpenHands runtime settings are currently saved
   - what model IDs and MCP URLs actually persist across restarts
   - what DB/state files still influence behavior

3. **Historical doc truth**
   - what earlier docs say the system is
   - what earlier plans say should be canonical
   - what later replacement docs only partially corrected

4. **Patch-layer truth**
   - what files are actually being patched
   - what runtime behavior is being altered by Dockerfiles, patch scripts, or vendored overrides
   - which workaround layers are real versus stale

5. **Local-folder truth**
   - what exists locally but is not actually runtime authority
   - what looks authoritative but is broken, stale, or unused

This phase exists to collapse those competing truths into one controlled runtime story.

---

## Phase Name
**Phase 1: Runtime Stabilization**

---

## Operating Principle
During this phase:

**runtime truth beats remembered intent**

Additional rules:
- actual active code paths beat docs
- persisted live settings beat assumptions
- one active startup path beats multiple “maybe canonical” paths
- deterministic build-time behavior beats runtime mutation hacks
- one browser lane beats two half-alive browser stories
- pinned version lines beat mixed-family dependency drift
- quarantining evidence beats deleting first and regretting it later

---

## Canonical Runtime Truths for This Phase
The following items are treated as the current active runtime baseline for this stabilization phase unless direct runtime evidence proves otherwise.

### 1. Canonical startup wrapper
- `scripts/up.sh`

### 2. Canonical shutdown wrapper
- `scripts/down.sh`

### 3. Canonical verification wrapper
- `scripts/verify.sh`

### 4. Canonical control script
- `scripts/agent_house.py`

### 5. Canonical compose definition
- `compose/docker-compose.yml`

### 6. Canonical OpenHands app override path
- `compose/openhands_override/`

### 7. Canonical agent-server override path
- `compose/agent_server_override/`

### 8. Canonical browser/tooling lane for this phase
- `stagehand-mcp`
- source rooted in `repos/stagehand(working)/packages/mcp/`

### 9. Canonical local model/provider posture for this phase
- LM Studio on host
- Dockerized callers reach host LM Studio through `host.docker.internal`

### 10. Canonical OpenHands runtime state root for this phase
- `data/openhands/`

Important: this does **not** mean every file under `data/openhands/` is good, correct, or safe to treat as versioned truth.
It means this directory is part of actual runtime behavior and must be treated as first-class state during stabilization.

---

## Current Phase Assumptions
These assumptions are accepted as working assumptions for this contract until disproven by direct inspection.

### Assumption A: The repo is not yet AI Garage
The current repo is a patched OpenHands stack and a pre-Garage staging area, not the Garage itself.

### Assumption B: The vendored `repos/OpenHands/` copy is not the current runtime authority
Even if useful as reference or patch source, it is not assumed to be the active OpenHands runtime unless explicitly proven.

### Assumption C: `stagehand-mcp` is the current browser lane winner in practice
Historical references to `oh-browser-mcp` and `SearxNG` are treated as stale unless current runtime proves otherwise.

### Assumption D: OpenHands runtime state can override repo intent
Persisted settings, DB rows, secrets, and local state may continue influencing runtime after code changes.
Therefore code truth alone is insufficient.

### Assumption E: The patch/override story is currently too fragmented to trust casually
No patch script, Dockerfile mutation, or vendored override should be assumed necessary, sufficient, or current without ledgering it.

---

## Primary Objectives
This phase has seven objectives.

### Objective 1: Freeze the exact current runtime baseline
Before cleanup, capture the exact live baseline so future rework does not destroy the ability to explain what was actually working or failing.

### Objective 2: Reconcile configuration truth
Determine the single authoritative answers for:
- OpenHands model ID
- OpenHands base URL
- MCP endpoint URL
- Stagehand model selection
- browser-lane runtime path
- persistence behavior across restarts

### Objective 3: Build a patch ledger
Document every meaningful patch, override, shim, and workaround so the stack can be stabilized intentionally rather than by tribal memory.

### Objective 4: Eliminate version-family drift
Collapse mixed OpenHands version lines into one coherent pinned family.

### Objective 5: Convert runtime mutation into deterministic build-time authority
Where patching is still required, it must become deterministic, minimal, and explicit.

### Objective 6: Establish one proof path
Define and pass one canonical end-to-end proof task through the actual OpenHands runtime path.

### Objective 7: Quarantine stale or competing architecture paths
Do not leave dead or misleading branches sitting next to the live path pretending to be equally relevant.

---

## Deliverables
This phase must produce the following deliverables.

### Deliverable 1: Baseline Snapshot Record
A written artifact capturing:
- current compose file identity
- current override file identities
- key persisted settings values
- current startup path
- current expected services
- current known failing proof tasks
- current known host dependencies
- current container/image references

### Deliverable 2: Runtime Configuration Authority Record
A written artifact stating the definitive current values for:
- OpenHands provider/base URL
- OpenHands model string
- MCP URL
- Stagehand model string
- Stagehand base URL behavior
- any env/file/runtime precedence rules

### Deliverable 3: Patch Ledger
A written artifact listing each patch/hack/override with:
- file path
- target component
- exact purpose
- exact bug or symptom addressed
- whether currently required
- whether duplicated elsewhere
- whether superseded
- what test proves necessity

### Deliverable 4: Version Authority Decision
A written artifact stating:
- which OpenHands runtime family is authoritative
- which agent-server family is authoritative
- whether vendored source is authoritative or reference-only
- which tags/versions/digests are pinned

### Deliverable 5: Quarantine List
A list of files/directories that are not current authority and must not guide further runtime work.

### Deliverable 6: Canonical Proof Specification
A short spec defining:
- one exact proof task
- one exact success condition
- required supporting evidence
- required cleanup/rollback behavior after the run

### Deliverable 7: Runtime Stabilization Summary
A final concise artifact stating:
- what changed
- what is now canonical
- what remains deferred
- what must be tested next

---

## Mandatory Sequence
This work must happen in this order unless a hard blocker forces a documented exception.

### Step 1: Freeze the baseline
Before making changes:
- snapshot relevant runtime state
- snapshot active configs
- snapshot override directories
- snapshot key persisted settings
- capture any current proof/failure artifacts

No destructive cleanup before this snapshot exists.

### Step 2: Reconcile configuration truth
Determine the current effective values and precedence for:
- model provider
- model ID
- OpenHands base URL
- MCP URL
- Stagehand model selection
- settings persistence

If multiple values conflict, document the conflict and identify which one actually wins.

### Step 3: Build the patch ledger
No patch should survive this phase as “mystery glue.”
Every meaningful patch layer must be recorded before large rewrites begin.

### Step 4: Decide version authority
Choose one authoritative runtime family.
No further stabilization work should continue on top of version soup.

### Step 5: Rebuild the override story cleanly
Reduce the active mutation surface into one deterministic build-time override path per relevant component.

### Step 6: Run the canonical proof task
After runtime/config/version truth is stabilized, prove the stack through one end-to-end task.

### Step 7: Quarantine stale branches
Only after truth is stabilized should stale paths be removed or archived out of the active tree.

### Step 8: Rewrite runtime docs
Docs should be updated last in this phase, after runtime truth is stabilized enough to document honestly.

---

## Freeze Requirements
Before cleanup starts, the following must be captured.

### Required baseline captures
- current `compose/docker-compose.yml`
- current `scripts/agent_house.py`
- current `compose/openhands_override/`
- current `compose/agent_server_override/`
- current `repos/stagehand(working)/packages/mcp/`
- current `data/openhands/settings.json`
- current `data/openhands/openhands.db`
- current auth-related runtime state under `data/openhands/`
- current `.env`-like values affecting compose/runtime
- current known proof prompts/tasks and their observed failures

### Required environment facts
Capture or record:
- whether Docker stack is up or down at time of baseline
- container list if running
- image references if available
- ports expected
- any required host networking hack status

### Freeze rule
No file/directory should be deleted from the active tree until either:
1. it is represented in the baseline snapshot, or
2. it has been explicitly classified as irrelevant noise.

---

## Configuration Truth Reconciliation Rules
This is the first real engineering pass.

### Questions that must have one answer after this phase
1. What is the one canonical OpenHands model string?
2. What is the one canonical OpenHands base URL?
3. What is the one canonical browser/MCP endpoint URL?
4. What is the one canonical Stagehand model setting?
5. What runtime source wins when config values disagree?
   - compose env
   - persisted OpenHands settings
   - local `.env`
   - hardcoded verifier expectations
   - code defaults
6. Which state is ephemeral and which is intended to persist?

### Precedence rule to determine
This phase must explicitly determine config precedence instead of assuming it.
If the answer differs by subsystem, document that.

### Required outcome
After this phase, there must be one written authoritative config table for runtime-critical values.

---

## Patch Ledger Requirements
For each patch/hack/override/shim, record the following.

### Required fields
- path
- component touched
- upstream or base target
- category
  - Dockerfile inline patch
  - vendored file override
  - patch script
  - runtime janitor tool
  - host networking helper
  - local service compatibility shim
- exact purpose
- known symptom or bug addressed
- whether still active
- whether duplicated elsewhere
- risk level
- proposed fate
  - keep
  - merge
  - rewrite
  - quarantine
  - delete
- proof/test that validates necessity

### Mandatory candidates
At minimum the ledger must include:
- `compose/openhands_override/Dockerfile`
- `compose/agent_server_override/Dockerfile`
- `scripts/patch_openhands_external_resource_routing.py`
- `scripts/patch_openhands_tool_call_mode.py`
- `scripts/chat_guard.py`
- `scripts/lmstudio-docker-dnat.sh`
- all files under active `vendor_sdk` override paths
- the live Stagehand MCP compatibility code in `server.ts`

---

## Version Authority Decision Rules
The current runtime must stop mixing incompatible or ambiguous OpenHands component families.

### This phase must answer
- Which OpenHands app source line is authoritative?
- Which agent-server source line is authoritative?
- Which SDK/tools versions are authoritative?
- Is the vendored `repos/OpenHands/` tree runtime authority, reference-only, or garbage?

### Prohibited post-phase state
After stabilization, the project must **not** remain in a state where:
- one runtime image is effectively pinned to one family
- one Dockerfile installs packages from another family
- a vendored tree declares a third family
- and all three coexist without explicit rationale

### Acceptable state
One clear family, one clear patch overlay, one clear build path.

---

## Canonical Proof Path Requirements
The phase must define one exact proof path.

### Purpose of the proof
The proof task exists to test real runtime truth, not docs or wishful thinking.

### Proof must go through
- canonical startup path
- canonical OpenHands runtime
- canonical browser/tool lane
- canonical provider path
- canonical persisted/runtime config behavior

### Proof spec must define
- exact prompt/task
- exact expected execution behavior
- exact evidence to record
- exact success criteria
- exact failure criteria
- exact cleanup behavior after run

### Proof rule
A green health/readiness status is **not** enough.
One real task must pass.

---

## Quarantine Rules
Some files/paths may be stale, misleading, broken, or purely historical.
They must be quarantined before deletion.

### Quarantine means
- not considered runtime authority
- not used to guide stabilization decisions
- not deleted until their role has been logged
- explicitly labeled as stale, historical, placeholder, broken, or reference-only

### Likely quarantine candidates
These are expected candidates, subject to verification:
- stale compose files
- old bridge directories
- vendored OpenHands copy if not runtime authority
- dead helper repos or toy repos under `repos/`
- stale docs describing abandoned runtime paths
- duplicate vendored SDK trees
- `.bak` or shadow implementation files

### Rule
Do not let quarantined paths continue presenting themselves as equally canonical alongside the real runtime path.

---

## Do-Not-Touch-Yet List
The following work is forbidden during this phase unless a documented blocker proves it is unavoidable.

### Forbidden during Phase 1
- Alfred implementation
- Ledger implementation
- memory-bank design implementation
- baton-pass protocol implementation
- Garage VM redesign work
- replacing the whole stack with a new architecture
- speculative multi-model orchestration work
- Phase C bridge implementation
- large UI redesigns
- deleting evidence before patch/config truth is documented
- introducing new services unrelated to stabilization

### Reason
This phase is not allowed to become a scope-creep swamp.

---

## Acceptance Criteria
Phase 1 is complete only when **all** of the following are true.

### Runtime truth
1. There is one documented canonical startup path.
2. There is one documented canonical shutdown path.
3. There is one documented canonical verification path.
4. There is one documented canonical browser/tool lane.
5. There is one documented canonical model/provider path.

### Config truth
6. OpenHands model ID has one authoritative value.
7. OpenHands base URL has one authoritative value.
8. MCP endpoint URL has one authoritative value.
9. Stagehand model selection has one authoritative rule.
10. Config precedence between env/files/persisted settings has been explicitly determined.

### Patch truth
11. Every active patch layer is listed in the patch ledger.
12. Duplicate or superseded patch layers have been identified.
13. The active OpenHands patch path is deterministic.
14. The active agent-server patch path is deterministic.

### Version truth
15. One authoritative OpenHands-related runtime family has been selected.
16. Mixed-family version drift has been reduced or explicitly pinned with rationale.

### Proof
17. One canonical end-to-end proof task has been run.
18. The result has been captured with evidence.
19. If the proof failed, the failure has been classified precisely rather than hand-waved.

### Hygiene
20. Stale competing runtime paths have been quarantined.
21. Runtime docs no longer claim a browser stack that is not actually current.
22. Runtime state handling is explicitly classified as versioned template, live mutable state, or off-repo secret material.

If any of those remain false, this phase is not done.

---

## Risk Management Rules
During this phase, the following risks must be treated explicitly.

### Risk 1: Floating upstream mutation
If a Dockerfile patches a floating upstream image, that is a breakage risk and must be reduced.

### Risk 2: Hidden state resurrection
Persisted settings/DB state can reintroduce bad config after code cleanup.

### Risk 3: Fake readiness
Any health endpoint that does not prove browser/provider/runtime readiness must be documented as weak readiness only.

### Risk 4: Silent policy overlays
Any hidden instruction file or mounted policy file that can alter behavior must be identified.

### Risk 5: Version-family mismatch
Different OpenHands-related families must not continue coexisting casually.

### Risk 6: Accidental evidence destruction
Deleting stale files before extracting the patch/config story can destroy the explanation for why the stack ended up here.

---

## Documentation Rules for This Phase
No further runtime doc should present itself as authoritative unless it matches current stabilized truth.

### Required doc posture
- one runtime truth doc
- one stabilization contract
- clearly labeled historical docs
- no docs claiming inactive services are current
- no docs implying Garage features are implemented if they are not

### Prohibited doc posture
- “current setup” docs that lie about actual runtime
- multiple equal-ranking setup stories
- historical docs without banners
- future architecture docs phrased as existing implementation truth

---

## Codex Execution Boundary for This Phase
Any coding agent or coding pass working under this contract is constrained as follows.

### Allowed
- baseline capture
- runtime/config inspection
- patch ledger generation
- version pinning work
- deterministic override cleanup
- canonical proof-path work
- stale-path quarantine
- runtime-doc rewrite after truth is stabilized

### Not allowed
- full architecture redesign
- adding Alfred/Ledger systems
- building Garage-layer orchestration
- large speculative refactors outside runtime stabilization scope

---

## Final Statement
This project is not ready for serious AI Garage implementation work until the current runtime stops lying.

The first job is not to dream bigger.
The first job is to make the existing stack honest, deterministic, and supportable.

This contract is therefore the gatekeeper for all further work.

Until the runtime has:
- one startup path
- one config truth
- one patch truth
- one browser lane
- one version family
- and one proof path

all higher-level Garage architecture remains downstream of unstable ground.

