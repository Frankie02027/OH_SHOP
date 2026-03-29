# AI Garage Master Architecture Intent Brief
## Research Context Document
### Status: Goal-definition document
### Purpose: Explain **what this project is supposed to become**
### Explicitly not: an implementation plan, migration plan, cleanup contract, or coding task list

---

## 1. What this document is for

This document exists to explain the **true intended end-state** of the AI Garage project to a deep research model.

It is meant to answer:

- what this system is ultimately supposed to be
- what problem it is trying to solve
- what roles and boundaries it is supposed to have
- what architectural properties matter most
- what constraints are non-negotiable
- what must be separated cleanly
- what the human operator expects from the finished environment

It is **not** meant to tell the model exactly how to implement the system.
It is **not** meant to force one predetermined stack.
It is **not** meant to preserve accidental choices from the current repo if better real-world patterns exist.

The research model should use this document to understand the **goal**, then compare that goal against proven existing architectures, systems, tools, and patterns.

---

## 2. Core mission

AI Garage is intended to become a **local-first, operator-controlled, multi-role AI workbench** for serious research, reasoning, execution, and long-running technical or mixed-domain work.

The system is supposed to support work that is:

- too large for a single short chat
- too tool-heavy for a plain LLM session
- too stateful for stateless prompt chains
- too brittle if progress is not recorded
- too expensive in attention if the operator must manually restate context constantly

The goal is to create an environment where multiple specialized AI roles can participate in one larger body of work **without losing continuity, lying about state, or collapsing into tool chaos**.

This is not meant to be a novelty chatbot shell.
This is not meant to be a random agent demo.
This is not meant to be a toy multi-agent experiment with vague autonomy theater.

The intended system should be:

- practical
- inspectable
- durable
- traceable
- local-first
- resilient to long tasks
- explicit about state
- explicit about role boundaries
- controllable by the operator

---

## 3. High-level vision

The intended end-state is a system where:

- the human operator gives a top-level task or mission
- one primary reasoning role interprets the work
- that role can request specific child work from a specialist role
- a deterministic controller handles routing, tracking, and resumption
- all meaningful progress, artifacts, handoffs, and decisions are recorded
- the system can survive long-running work, interruptions, retries, and resumptions
- the system can show what happened, why it happened, and what remains to be done

The project should behave more like a **serious local AI operations environment** than a single-chat assistant.

---

## 4. The intended role model

The project currently uses these working names, and the final architecture is expected to preserve the conceptual split even if the underlying implementation changes.

### 4.1 Jarvis
Jarvis is the **primary reasoning and task-owning role**.

Jarvis is intended to:
- receive the operator’s main task
- interpret the task
- define the working approach
- decide when specialist child work is needed
- consume specialist returns and continue the parent job
- maintain the main line of reasoning for the job
- decide whether work is complete, blocked, or needs further subdivision

Jarvis should be the role that most resembles a lead analyst, lead engineer, or lead researcher.

Jarvis is **not** supposed to roam every tool lane directly if that breaks clarity.
Jarvis is **not** supposed to be the persistence system.
Jarvis is **not** supposed to be the scheduler or workflow engine.
Jarvis is **not** supposed to become a hidden orchestrator.

### 4.2 Robin
Robin is the **specialist web / browser / visual / online interaction role**.

Robin is intended to:
- perform browser-heavy or visually grounded work
- inspect sites, UI states, documents, and web interactions
- gather evidence from web-facing environments
- return structured results, artifacts, and observations to the parent workflow

Robin is **not** supposed to own the full mission.
Robin is **not** supposed to become a general orchestrator.
Robin is **not** supposed to silently expand its job beyond the delegated child scope.

Robin is a specialist lane, not a second main brain.

### 4.3 Alfred
Alfred is the intended **deterministic controller / orchestrator**.

Alfred is not an AI personality.
Alfred is not supposed to “reason” like Jarvis or Robin.
Alfred is not supposed to improvise task meaning.

Alfred is intended to:
- create and track jobs
- assign IDs and maintain state transitions
- route child work
- persist handoff records
- record progress markers
- enforce workflow rules
- coordinate retries / resume points
- maintain authoritative job/task metadata
- provide the boring, deterministic backbone

Alfred should be:
- predictable
- auditable
- cheap to run
- easy to debug
- policy-enforcing
- state-aware
- explicit

Alfred should **not** become a fuzzy AI layer.
Alfred should **not** become a hidden pile of heuristics.
Alfred should **not** own the meaning of the work.
Alfred should own the **workflow mechanics**, not the reasoning content.

### 4.4 Ledger / record-keeper
The Garage Ledger is the intended **durable state, memory, record, and artifact layer**.

It is expected to hold:
- job records
- child job records
- handoffs
- summaries
- checkpoints
- continuation notes
- evidence trails
- artifact pointers
- structured state for resumption and review

The Ledger is not supposed to be a vague “memory” blob.
It should be a deliberate system for durable work tracking and retrieval.

The Ledger is **not** Alfred.
The Ledger is **not** Jarvis.
The Ledger is **not** OpenWebUI.
The Ledger is **not** just a chat log.

---

## 5. The intended interaction pattern

The intended system is built around a **baton-pass model**, not a “everyone talks to everyone however they want” model.

At a conceptual level:

1. The operator starts a parent task.
2. Alfred registers the task.
3. Jarvis receives the task context and begins parent reasoning.
4. If Jarvis needs web/visual/browser work, Jarvis creates a child request.
5. Alfred receives and records that child request.
6. Alfred routes the child request to Robin.
7. Robin performs the scoped specialist work.
8. Robin returns structured results and artifacts.
9. Alfred records the return.
10. Alfred routes the return back to Jarvis.
11. Jarvis continues the parent task with the new evidence.
12. All of this is persisted in a durable, inspectable way.

The important point is not the exact message syntax.
The important point is that:
- ownership is explicit
- handoffs are explicit
- state transitions are explicit
- the return path is explicit
- the record is durable

This is intended to prevent:
- silent context loss
- hidden branch work
- hallucinated continuity
- “I think I already did that” behavior
- confused multi-agent cross-talk

---

## 6. The intended architectural style

The target style is **layered and separable**.

The final system should clearly distinguish at least these planes.

### 6.1 Operator/UI plane
This is where the human interacts with the system.

It should:
- provide a usable interface to initiate, inspect, and continue work
- show enough status to understand what is happening
- not be the hidden source of truth
- not silently store the real architecture state in an opaque way

OpenWebUI or a similar interface may serve this role, but the UI is **not** the architecture itself.

### 6.2 Control/orchestration plane
This is where Alfred belongs.

It should:
- manage job lifecycle
- manage state transitions
- manage routing
- manage resume logic
- manage deterministic workflow metadata

This plane should be explicit and durable.

### 6.3 Reasoning plane
This is where Jarvis and Robin-like reasoning agents live.

It should:
- receive scoped context
- do reasoning work
- emit structured outputs
- not become the hidden persistence layer

### 6.4 Tool plane
This is where tool servers belong.

It should include things like:
- browser automation
- extraction tools
- possibly filesystem or document tools
- other structured tool interfaces

This plane should be cleanly separable from orchestration and persistence.

### 6.5 Execution/sandbox plane
This is where risky, isolated, or reproducible execution belongs.

It should:
- isolate code execution
- isolate tool-side actions when appropriate
- protect the host
- keep runs reproducible
- support inspection and cleanup

### 6.6 Durable state / memory / ledger plane
This should hold the structured record of work.

It should not be a pile of arbitrary chat text.
It should not rely on the operator’s memory.
It should not rely on model context window retention.

This plane is what lets the system continue, resume, audit, and reason over prior work safely.

---

## 7. What the system is **not** trying to be

This project is **not** intended to be:

- a generic chatbot wrapper
- a one-shot autonomous agent demo
- a “just let the AI browse the web forever” toy
- a single monolithic process that does UI, orchestration, memory, browsing, and execution all in one blob
- a thin skin over raw tool calls with no durable state
- a system that depends on invisible prompts and operator luck
- a SaaS-first cloud-dependent architecture
- a vibe-coded pile of containers with no durable workflow model
- a hand-wavy “multi-agent” system where every role is actually the same model doing the same thing

---

## 8. What the system is trying to optimize for

The desired architecture should optimize for the following properties.

### 8.1 Traceability
The operator should be able to answer:
- what happened
- in what order
- under which job
- by which role
- based on which handoff
- using which artifacts
- with which outcome

### 8.2 Durability
The system should not collapse if:
- a long task runs for a while
- a container restarts
- the operator closes the UI
- a subtask needs to be resumed later
- a specialist branch has to be retried

### 8.3 Clear role boundaries
The system should not blur:
- reasoning
- orchestration
- tool execution
- persistence
- UI

### 8.4 Operator control
The human should remain able to:
- initiate work
- inspect work
- interrupt work
- approve or deny specific transitions if needed
- review evidence
- resume from known state

### 8.5 Local-first operation
The system should prefer:
- local models where practical
- local runtime boundaries
- local storage where practical
- Docker-first deployment for internal components
- minimal dependence on paid cloud services

### 8.6 Evidence and artifact fidelity
When work involves:
- web browsing
- screenshots
- downloads
- extracted data
- summaries
- code changes
- reports

those outputs should be explicitly recorded and retrievable.

### 8.7 Long-horizon work support
The system is meant for tasks that may require:
- multiple stages
- multiple child jobs
- back-and-forth specialist work
- revisiting the same task later
- preserving rationale and progress

### 8.8 Honest state
The system should not lie about:
- what is active
- what is authoritative
- what is stale
- what is inferred versus proven
- what is complete versus merely “healthy”

---

## 9. Constraints that matter

The research model should treat these as important constraints unless it can justify a better alternative very strongly.

### 9.1 Local-first
The system should be designed under a local-first mindset.

### 9.2 Docker-first internal composition
Internal services are expected to run in containers unless there is a strong reason not to.

### 9.3 Likely later VM containment
The likely long-term containment boundary is a dedicated Garage VM that runs the internal container stack.

### 9.4 GPU reality matters
GPU limits, passthrough practicality, and model-slot reality are real constraints, not theoretical footnotes.

### 9.5 The operator wants clarity, not magic
The system should be inspectable and debuggable.
A pretty illusion of autonomy is not enough.

### 9.6 Durable records matter more than chat memory
The finished system should not rely on chat scrollback or vague LLM memory as its main continuity mechanism.

### 9.7 Tool use should use standards where possible
Custom glue should be minimized where established patterns already exist.

---

## 10. Memory, policy, and state are different things

A major source of confusion in projects like this is collapsing multiple concepts into the word “memory.”

The research model must treat these as distinct.

### 10.1 Policy / handbook / role rules
This is the stable operating doctrine.
Examples:
- how a role behaves
- what a role is allowed to do
- when a handoff is required
- what must be recorded
- what good task progression looks like

This is not task-specific memory.
This is more like a rulebook.

### 10.2 Job state
This is current work state.
Examples:
- task IDs
- status
- subtask list
- next step
- last successful checkpoint
- blocked reason
- resume target

### 10.3 Memory / summaries / continuation notes
This is durable contextual compression for future reuse.
Examples:
- what has been learned
- why a decision was made
- what matters going forward
- what should be remembered next time

### 10.4 Artifact state
This is the actual physical or digital output record.
Examples:
- screenshots
- downloaded files
- logs
- code diffs
- proofs
- reports
- receipts
- evidence attachments

The target architecture should keep these distinct instead of muddling them together.

---

## 11. Handoffs must be real, not theatrical

The system should not simulate handoffs in vague prose only.
It should support structured handoff objects or records that include things like:

- parent task/job reference
- child job reference
- sender role
- receiver role
- objective
- scope
- constraints
- expected output shape
- artifact expectations
- return summary
- completion status
- failure status
- timestamps or equivalent progression markers

This does **not** mean the research model must prescribe one exact schema here.
It means the final architecture should treat handoffs as explicit first-class records, not fuzzy chat behavior.

---

## 12. The current repo is **not** the goal

The research model must understand this clearly.

The current OH_SHOP repo is:
- a useful current runtime
- a proof that a local stack can work
- a staging area
- a stabilization effort
- a current baseline

It is **not** the final AI Garage architecture.

The current repo should be treated as:
- evidence of current capability
- evidence of current debt
- evidence of current runtime choices
- evidence of what has already been proven

But it should **not** be mistaken for the final desired architecture.

The research should not be constrained by accidental local minima in the current repo if better proven patterns exist.

---

## 13. What the research model should compare against

The research should examine real, proven patterns for systems that combine:

- tool protocols
- browser automation
- sandboxed execution
- long-running task orchestration
- human-in-the-loop workflow control
- durable state/checkpointing
- artifact and event recording
- local or hybrid containerized deployment

The research should compare patterns such as:

- tool-server standards
- browser MCP/server patterns
- durable workflow engines
- graph/state-machine orchestrators
- sandbox-execution patterns
- artifact/event-log patterns
- local multi-service deployment patterns

The point is to find **the strongest architecture for this project’s intent**, not to worship any one existing project.

---

## 14. Desired research output

The deep research model should return an answer that explains:

### 14.1 Target architecture
What the strongest practical architecture looks like for this project’s intent.

### 14.2 Service boundaries
What should be separate services or layers versus what should remain thin wrappers.

### 14.3 State model
How durable state, checkpoints, job records, summaries, and artifacts should be organized conceptually.

### 14.4 Control model
What kind of orchestration pattern best fits Alfred’s intended role.

### 14.5 Tool model
How tool access should be structured cleanly.

### 14.6 Execution model
How code execution and risky actions should be isolated.

### 14.7 UI/operator model
How the human should interact with the environment without the UI becoming the hidden source of truth.

### 14.8 Migration direction
At a high level, what parts of the current stack are useful scaffolding and what parts are local minima that should not define the final design.

The output should emphasize:
- proven patterns
- clear separation of concerns
- operational sanity
- traceability
- durability
- local practicality

---

## 15. What the research should avoid

The research should avoid giving a shallow answer like:
- “use microservices”
- “use Kubernetes”
- “use a database”
- “use events”
- “use agents”
- “use memory”

That kind of answer is too generic to be useful.

It should also avoid:
- treating the current repo’s patch structure as sacred
- assuming the final system must look like OpenHands internally
- assuming one monolithic Python script is the right long-term control plane
- confusing a tool server with an orchestrator
- confusing memory with chat history
- confusing a UI with durable state authority

---

## 16. Explicit non-goals for the research answer

The research answer does **not** need to:

- write code
- write migration scripts
- fix the current repo directly
- produce a patch list
- produce a Dockerfile rewrite
- produce an Alfred implementation
- choose exact database schemas unless conceptually necessary
- choose exact libraries unless strongly justified

The goal is to identify the best architecture **shape** and **boundary model**.

---

## 17. Final intent statement

AI Garage is intended to become a **serious local AI workbench for long-running, tool-using, multi-role work**.

It should have:
- a primary reasoning role
- one or more specialist roles
- a deterministic orchestration backbone
- a durable work ledger / state system
- explicit handoffs
- explicit artifacts
- explicit resumability
- clear operator control
- clear runtime boundaries
- supportable local deployment

It should not depend on:
- hidden prompt magic
- fragile chat continuity
- one giant overloaded house script
- vague “agent memory”
- accidental repo drift
- theatrical multi-agent branding with no real workflow discipline

The research model should therefore focus on:

**what architecture best supports this mission using proven existing patterns, while keeping the system local-first, Docker-first, auditable, durable, and sane.**

---

## 18. Instruction to the research model

Treat this document as the **architectural intent brief**.

Use it to understand:
- the mission
- the role model
- the required separations
- the constraints
- the desired properties

Do not mistake the current repo for the final design.
Do not assume historical docs are current runtime truth.
Do not optimize for preserving the current mess.
Optimize for identifying the strongest real-world architecture for the intended end-state.