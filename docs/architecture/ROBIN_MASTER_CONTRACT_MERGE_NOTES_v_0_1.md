# ROBIN Master Contract Merge Notes v0.1

> These merge notes now accompany [ROBIN_MASTER_CONTRACT_v_0_1.md](/home/dev/OH_SHOP/docs/architecture/ROBIN_MASTER_CONTRACT_v_0_1.md).
> The older path `docs/architecture/robin_initial_contract_v_0.md` is historical only and no longer serves as live authority.

## 1. Source documents used

Primary authority inputs used for this consolidation:

- `docs/architecture/AI_GARAGE_BLUEPRINT.MD.md`
- `docs/architecture/ai_garage_library_and_policy_contract_v_0_1.md`
- `docs/runtime/stabilization/master_intent_brief.md`
- `docs/architecture/JARVIS_MASTER_CONTRACT_v_0_1.md`
- `docs/architecture/JARVIS_MASTER_CONTRACT_MERGE_NOTES_v_0_1.md`

Primary implementation/research inputs used to ground the Robin execution lane:

- `vendor/stagehand_mcp/src/server.ts`
- `vendor/stagehand_mcp/package.json`
- `vendor/stagehand_mcp/Dockerfile`
- `docs/research/deep-research-report_#2.md`

Supporting project references used where helpful:

- `docs/architecture/JARVIS_WORKBENCH_AND_PROGRESSION_CONTRACT_v_0_1.md`
- `docs/architecture/JARVIS_WORKBENCH_EXAMPLES_v_0_1.md`
- `docs/architecture/JARVIS_ROLE_AND_WORK_STYLE_POLICY_v_0_1.md`
- `docs/architecture/JARVIS_ROLE_AND_WORK_STYLE_EXAMPLES_v_0_1.md`
- `docs/architecture/jarvis_final_contract_v_0.md`

## 2. What each source contributed

### `AI_GARAGE_BLUEPRINT.MD.md`

Contributed:
- Robin's top-level identity as the browser / visual / online specialist
- the baton-pass architecture
- the structured handoff and return envelope expectation
- the principle that Robin is not the full mission owner
- the expectation that Robin returns artifacts, visited URLs, screenshots, downloads, and grounded findings

### `ai_garage_library_and_policy_contract_v_0_1.md`

Contributed:
- shell/body handoff model
- ID ownership boundaries
- execution-mode language
- the principle that Jarvis and Robin author semantic meaning while Alfred validates and routes
- explicit future need for Robin worker policy
- return/evidence expectations

### `master_intent_brief.md`

Contributed:
- the cleanest concise description of Robin as the specialist web / browser / visual role
- the non-ownership boundary
- the architectural insistence that Robin remains a specialist lane, not a second main brain
- the baton-pass sequence and Ledger/Alfred separation

### `JARVIS_MASTER_CONTRACT_v_0_1.md`

Contributed:
- the parent-task perspective Robin must fit under
- the threshold where Jarvis must hand work off
- the expectation that Robin returns structured evidence for Jarvis to absorb
- the need to align Robin policy with the already finalized Jarvis authority

### `JARVIS_MASTER_CONTRACT_MERGE_NOTES_v_0_1.md`

Contributed:
- the consolidation pattern and authority-position logic used for the Robin master contract
- the expectation that older drafts become supporting references instead of parallel authority

### `vendor/stagehand_mcp/src/server.ts`

Contributed:
- the actual live Robin execution surface
- the real Stagehand MCP tool inventory
- the local distinction between direct tools and `browserbase_stagehand_agent`
- the repo's actual `dom`/`hybrid` agent-mode exposure
- session, tab, cookie, header, init-script, and low-level tool realities

### `docs/research/deep-research-report_#2.md`

Contributed:
- the strongest explicit articulation of Robin as the browser/web/visual lane
- the return-envelope framing
- the importance of keeping Robin from collapsing into a role-confused blended system

## 3. Overlaps removed

The master contract removes repeated Robin language that was previously spread across:
- Blueprint role descriptions
- Library/Policy role notes
- master intent summary language
- Jarvis-side delegation sections
- research summaries

The following repetitive themes were collapsed into one Robin authority:
- Robin is a specialist, not a second Jarvis
- Robin handles browser/web/visual work
- Robin returns structured results and artifacts
- Robin must not own official state or the full mission
- Alfred must remain the gatekeeper and recorder

## 4. Contradictions resolved

### Role breadth vs bounded scope

The Blueprint sometimes describes Robin in broad, ambitious terms as a deep web investigator, while the baton-pass and policy docs insist on bounded child-job scope.

Resolved position:
- Robin may be powerful and investigative inside the child job
- Robin may not silently expand beyond the delegated leg

### Stagehand implementation vs Robin role identity

The repo's live Robin lane is Stagehand MCP, but the architectural intent describes Robin as a worker role rather than just a tool server.

Resolved position:
- Robin is the role
- Stagehand is the current browser execution layer
- the contract is written around role behavior, with Stagehand-grounded operational policy

### Agent power vs determinism

The research and Stagehand docs show agent mode as powerful, but the contract stack values proof, boundedness, and explicit handoffs.

Resolved position:
- direct tools are the default discipline
- agent mode is allowed but bounded
- agent mode is an escalation path, not Robin's entire identity

## 5. Weak language tightened

The consolidation tightened soft language in several places.

Examples:
- "Robin is a specialist lane" was sharpened into explicit non-ownership and non-orchestrator rules.
- "Robin returns structured results" was tightened into a required return-envelope discipline.
- "Robin may use browser tools" was tightened into direct-tool-first and agent-mode governance.
- "Robin should handle ambiguity" was tightened into explicit no-bluffing and partial/blocked/failed return behavior.

## 6. What remains deferred

The master contract intentionally leaves these areas for later contracts:
- Alfred enforcement mechanics for Robin jobs
- exact Ledger schema and artifact indexing
- Robin JSON schema details for all request/return fields
- retry and checkpoint implementation details
- Robin memory-bank implementation
- UI representation of Robin jobs and evidence
- future alternative browser runtimes beyond Stagehand

## 7. Recommendation on older Robin-related material

Current recommendation:

- `docs/architecture/AI_GARAGE_BLUEPRINT.MD.md`
  - Treat as **architectural intent authority**
  - Not superseded; remains upstream design authority

- `docs/architecture/ai_garage_library_and_policy_contract_v_0_1.md`
  - Treat as **companion structural authority**
  - Not superseded; remains the shared protocol-language contract

- `docs/runtime/stabilization/master_intent_brief.md`
  - Treat as **supporting architectural summary**
  - Not the main Robin behavioral authority anymore

- `docs/research/deep-research-report_#2.md`
  - Treat as **supporting research**
  - Not authority

- Jarvis-side docs mentioning Robin
  - Treat as **adjacent authority from Jarvis's perspective**
  - They remain valid for Jarvis behavior, but they do not replace Robin's own master contract

## 8. Recommended next contract layer

Now that Jarvis and Robin each have a primary behavioral authority, the next contract layer should be one of:

1. **Alfred Control / Enforcement Contract v0.1**
   - defines official gating, checkpoints, retries, and state transitions

2. **Ledger / Artifact / Proof Contract v0.1**
   - defines what official evidence, artifact refs, and durable records must look like

3. **Robin Result Schema Contract v0.1**
   - if the next need is machine-checkable Robin return envelopes rather than broader Alfred policy
