# Jarvis Master Contract Merge Notes v0.1

## 1. Source documents used

Primary authority inputs:
- `docs/architecture/AI_GARAGE_BLUEPRINT.MD.md`
- `docs/architecture/ai_garage_library_and_policy_contract_v_0_1.md`
- `docs/runtime/stabilization/master_intent_brief.md`
- `docs/architecture/JARVIS_WORKBENCH_AND_PROGRESSION_CONTRACT_v_0_1.md`
- `docs/architecture/JARVIS_WORKBENCH_EXAMPLES_v_0_1.md`
- `docs/architecture/JARVIS_ROLE_AND_WORK_STYLE_POLICY_v_0_1.md`
- `docs/architecture/JARVIS_ROLE_AND_WORK_STYLE_EXAMPLES_v_0_1.md`

Supporting file check:
- `deep-research-open-hands.md` was not present locally during this pass and was therefore not used.

## 2. What each source contributed

### `AI_GARAGE_BLUEPRINT.MD.md`

Contributed:
- Jarvis's high-level role identity as the main reasoning and local work role
- OpenHands as Jarvis's workbench
- Alfred as deterministic controller rather than AI
- Robin as the browser/web specialist
- the one-model baton-pass reality
- the durable-state-over-chat-memory principle

### `ai_garage_library_and_policy_contract_v_0_1.md`

Contributed:
- standing policy versus runtime language layering
- the shell/body split between Alfred-authored protocol and worker-authored meaning
- proof discipline and verification-gate logic
- tracked plan/checklist as a first-class object
- the rule that Alfred records official state while Jarvis authors semantic work

### `master_intent_brief.md`

Contributed:
- stronger wording on role boundaries
- the layered plane separation
- the anti-"hidden orchestrator" stance for Jarvis
- the requirement that handoffs and state transitions be explicit and durable

### `JARVIS_WORKBENCH_AND_PROGRESSION_CONTRACT_v_0_1.md`

Contributed:
- the strongest workbench boundary language
- Jarvis-local versus Alfred-official distinction
- progression and promotion discipline
- checkpoint, child-job, and pivot boundary expectations
- the overall workbench-to-official progression frame

### `JARVIS_WORKBENCH_EXAMPLES_v_0_1.md`

Contributed:
- concrete examples of local work, Robin delegation, pivots, failure, and checkpoint/resume
- useful scenario framing for practical behavioral rules

### `JARVIS_ROLE_AND_WORK_STYLE_POLICY_v_0_1.md`

Contributed:
- the clearest operational behavioral policy language
- local scratch discipline
- proof discipline
- Robin delegation discipline
- uncertainty, pivot, failure, and continuation-note discipline
- strong dos and don'ts

### `JARVIS_ROLE_AND_WORK_STYLE_EXAMPLES_v_0_1.md`

Contributed:
- cleaner example set for behavior-first policy interpretation
- stronger threshold examples for when Robin is mandatory
- clearer weak-evidence and blocked-state examples

## 3. Overlaps removed

The source documents had substantial overlap in these areas:
- Jarvis role identity
- OpenHands as workbench
- local-versus-official discipline
- proof-before-claim behavior
- Robin delegation thresholds
- pivot boundaries
- continuation-note expectations

The master contract removed duplication by:
- stating Jarvis role identity once
- stating the OpenHands workbench position once
- combining progression and work-style material into one working loop
- folding proof expectations into one policy section
- collapsing repeated Robin-boundary language into one delegation section
- keeping only one hard dos-and-don'ts list

## 4. Contradictions resolved

No major hard contradiction existed across the Jarvis source documents. The main issue was not contradiction but layering blur and duplicated emphasis.

The following potential tensions were resolved explicitly:

- **Workbench convenience vs official truth**
  Resolved by making local OpenHands state clearly subordinate to Alfred-official state.

- **Jarvis as main brain vs Alfred as controller**
  Resolved by stating that Jarvis owns planning and semantic work, while Alfred owns official progression and verification gates.

- **Strong local power vs policy discipline**
  Resolved by affirming that Jarvis has broad workbench power but cannot silently convert local actions into official truth.

- **Local CLI/network reach vs Robin delegation**
  Resolved by defining a clear threshold: direct CLI/text retrieval can remain local; rendered, interactive, visual, or browser-only work requires Robin.

## 5. Weak language tightened

The master contract tightened several areas that were softer in the source set:

- "Proof beats vibes" was turned into explicit no-self-certification policy.
- "Jarvis may use local task tracking" was tightened into a hard subordinate-state rule.
- "Jarvis should request Robin when needed" was tightened into a concrete threshold statement.
- "Jarvis should write continuation notes" was tightened into exact required content.
- "Jarvis should not bluff certainty" was tightened into explicit ambiguity-handling rules.
- "Jarvis should not become Alfred" was tightened into a hard non-bypass boundary.

The master contract deliberately replaced softer framing such as "should probably" or "may often" with clearer operational language where the policy boundary needed to be hard.

## 6. What remains deferred

The master contract intentionally does not settle:
- Alfred internals
- Ledger schema
- Robin internal behavior policy
- final tool/API implementations
- UI behavior
- verification engine implementation details
- artifact indexing schemas
- policy storage mechanics

Those remain separate contract layers.

## 7. Recommendation on older Jarvis docs

Recommended treatment after creation of the master contract:

- `JARVIS_MASTER_CONTRACT_v_0_1.md`
  - treat as the main starting authority

- `JARVIS_WORKBENCH_AND_PROGRESSION_CONTRACT_v_0_1.md`
  - treat as a supporting reference
  - still useful for the progression boundary and object-shape layer

- `JARVIS_ROLE_AND_WORK_STYLE_POLICY_v_0_1.md`
  - treat as a superseded draft that fed into the master contract

- `JARVIS_WORKBENCH_EXAMPLES_v_0_1.md`
  - treat as supporting examples until a later pass decides whether to merge example sets

- `JARVIS_ROLE_AND_WORK_STYLE_EXAMPLES_v_0_1.md`
  - treat as supporting examples until a later pass decides whether to consolidate or replace them

Short recommendation:
- the master contract should now be the primary Jarvis authority
- the older Jarvis contracts should be treated as supporting references or superseded drafts
- the older examples should remain examples, not parallel authority
