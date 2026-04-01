# Project State — Human-Readable Summary

Date: 2026-04-01
Repo: `OH_SHOP`
Branch target: `master`

## What this repo is right now

This repo is **not one finished system**.
It is currently two overlapping tracks living in the same tree:

1. **The old live runtime / pre-Garage stack**
   - a patched OpenHands-style stack with Stagehand MCP, LM Studio, compose wrappers, persisted runtime state, and stabilization work
2. **The new AI Garage architecture / contract / implementation track**
   - the newer Alfred / Jarvis / Robin architecture, shared language contracts, and early deterministic controller code

That split matters.
A lot of confusion came from treating these as if they were already one clean finished machine.
They are not.

## The simplest honest description

If you want the blunt version:

- the repo has a **real stabilized runtime lane**, but that lane is still carrying some old patch/version baggage
- the repo has a **real Garage contract stack**, and Alfred has a meaningful early code surface now
- **Jarvis and Robin runtime breadth are still mostly unbuilt**
- the repo is therefore **past architecture-only talk**, but **not yet at full Garage implementation**

## Where the project sits now

The project sits at this stage:

### 1. The architecture stage is no longer vague

The repo already has the major architecture/contract layer for:
- the Garage blueprint
- Alfred role authority
- Jarvis role authority
- Robin role authority
- shared language/dictionary
- library/schema contract
- tracked-plan object contract
- handoff-envelope contract

That means the project is no longer stuck at the "what are we even building" stage.

### 2. Alfred is the only role with serious runtime/code progress so far

The Garage-side coding work has mostly gone into Alfred-related deterministic controller logic.
That includes things such as:
- schema/boundary validation
- runtime dispatch
- deterministic call handling
- storage-backed state/ID continuity
- tracked-plan linkage
- evidence/proof posture
- receipt/continuation/follow routing

Important:
that does **not** mean Alfred is becoming a hidden AI brain.
It means Alfred has been the first practical implementation target because Alfred is the deterministic controller layer.

### 3. Jarvis and Robin are still mostly contract-defined, not runtime-complete

Jarvis and Robin are much more defined at the contract/policy level than at the implementation/runtime level.
That is not a bug in tracking.
That is where the repo really sits.

So the current state is:
- Jarvis: strongly defined in docs/policy/contracts, lightly implemented in runtime terms
- Robin: strongly defined in docs/policy/contracts, lightly implemented in runtime terms
- Alfred: both contract-defined and meaningfully implemented in code

## What is real on the old runtime side

The old runtime lane did get serious stabilization work.
That work established a more honest current runtime story:

- canonical startup path
- canonical shutdown path
- canonical verification path
- canonical browser/tool lane
- canonical provider path
- canonical persisted runtime config root

At a human level, that means the repo is no longer completely lying about how the old stack starts or what browser lane/provider path it is actually using.

## What is still unresolved on the old runtime side

That runtime lane is **not perfectly clean**.
The stabilization summary still leaves real deferred issues such as:
- weak OpenHands app base-image authority
- mixed-family agent-server base/package skew
- fragmented patch authority
- misleading stale/reference trees still present in the repo
- tracked mutable runtime DB/state in the repo

So the old runtime side is **stabilized enough to understand**, but **not yet a perfectly clean final base**.

## What the Garage-side code work has really accomplished

The Garage-side code work should be described honestly.
It has accomplished this:

### Real wins
- the shared language/object stage is no longer hand-wavy
- Alfred has a real deterministic controller surface
- storage/state/proof/plan behavior has been exercised heavily
- the repo now has more structured behavior than a pile of architecture notes

### Real limits
- too much time was starting to go into receipt layers and test-surface growth
- Alfred had started accumulating wrappers on top of wrappers
- test coverage had become too monolithic
- the latest consolidation pass corrected some of that by reducing duplication and splitting tests by concern

So the project is not stalled.
But it **was** at risk of burning effort on control-surface geometry instead of pushing into new core implementation.

## The current practical interpretation

If a human asks, "Where are we actually at?", the correct answer is:

- We finished the first serious architecture/contract stack.
- We built the first serious deterministic Alfred slice.
- We cleaned up a lot of controller/test sprawl.
- We have **not** built the full Garage runtime yet.
- We have **not** built real Jarvis/Robin runtime breadth yet.
- We do now have enough structure to stop arguing about the shape every five minutes and start writing more real implementation.

## What should happen next

The repo should now bias toward:

1. **real implementation**, not more helper layers on Alfred
2. **meaningful Garage code**, not more wrapper receipts unless they remove real pain
3. **Jarvis/Robin-side implementation planning**, because Alfred is no longer the only thing with substance
4. **keeping the old runtime lane separate from the new Garage lane in people’s heads**, so the repo does not get mentally flattened into one fake finished system

## What should not happen next

The repo should not keep drifting into:
- checks for checks for checks
- wrapper helpers over wrapper helpers
- giant test matrices for tiny alias surfaces
- pretending Jarvis/Robin are already implemented when they are not
- pretending the old runtime lane and the new Garage lane are already one finished unified product

## Bottom line

The project is in a **serious but transitional** state.

That means:
- it is no longer just dream docs
- it is no longer just runtime chaos
- it is no longer blocked by major architecture ambiguity
- but it is also not yet the full AI Garage

The best plain-English summary is:

> The repo now has a real architecture, a real deterministic Alfred slice, and a partially stabilized old runtime base.
> It still needs substantial Jarvis/Robin/runtime build-out before it becomes the Garage it is designed to be.

## Recommended reading order for a human trying to understand the repo

1. `docs/current/project_state_human_readable_2026-04-01.md` ← this file
2. `docs/architecture/AI_GARAGE_BLUEPRINT.MD.md`
3. `docs/current/contract_stage_review_after_plan_and_handoff.md`
4. `docs/runtime_stabilization_summary.md`
5. Alfred / Jarvis / Robin role contracts

That reading order is better than dropping a human straight into the deepest contract/object files with no map.
