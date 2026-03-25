# AI Garage Blueprint Contract v0.3

## 1. Project identity

This document defines the expanded first serious infrastructure blueprint for the **AI Garage** project.

The AI Garage is intended to be a **self-contained, local, AI-driven work environment** that lives primarily inside Docker, uses local LLMs, supports structured task progression, and separates responsibilities between specialized roles instead of forcing one model to do everything badly.

The purpose of the AI Garage is to create a controlled environment where AI can:

- reason about a task
- write and modify code
- inspect files and project artifacts
- browse and interact with the web when needed
- download and process resources
- hand work off between specialized roles
- persist the state of the work as it progresses
- recover from failures without losing the entire job
- stay inside a bounded environment that can be rebuilt when needed

The AI Garage is not meant to be just a chatbot in a container.
It is meant to be a **working garage** for local AI-assisted projects.

This contract is also meant to reflect a more realistic version of the project direction:

- the garage is expected to evolve over time
- the internal structure will not stay frozen forever
- role boundaries matter more than hype
- persistence, indexing, and recoverability matter more than one impressive demo
- the garage is being designed to become a repeatable machine for technical work, research work, and computational task progression in general

---

## 2. Plain-English summary

The easiest way to explain the AI Garage is this:

- **Open WebUI** is the front desk where the user talks to the system.
- **Jarvis** is the main inside-the-garage worker that reasons, plans, writes, and continues the job.
- **Robin** is the online worker that browses, clicks, reads pages, and brings back structured results.
- **Alfred** is the director and record keeper that keeps the whole system organized.
- **Docker** is the wall around the garage that keeps the environment contained and rebuildable.
- **The PO box** is the narrow mail slot for files coming in and going out.

So this project is not just “run one AI locally.”
It is closer to building a **small controlled operating environment for AI work** inside the main computer.

That is why the design matters.
The goal is not to make the AI feel impressive for five minutes.
The goal is to make it **useful, recoverable, inspectable, durable, and hard to accidentally destroy**.

The bigger idea is that the garage should eventually behave less like a random chat session and more like a managed machine:

- it should keep working when a session ends
- it should keep records when a model changes
- it should know what happened when something fails
- it should know what to resume next
- it should be able to keep grinding on long jobs when the structure has been set correctly

---

## 3. Main technology building blocks

Before defining the named roles, the main software pieces should be explained clearly.

### 3.1 Docker

**Docker** is the containment layer.

A simple way to explain Docker is this:
Docker lets us package software and its dependencies into controlled boxes called containers, so the system inside the box behaves the same way each time it starts.

For AI Garage, Docker is used because it gives:

- isolation
- reproducibility
- easier rebuilds
- cleaner dependency management
- a safer place to give the AI meaningful powers without handing it the whole host machine

So when people hear “the garage lives in Docker,” what that really means is:

- the AI work environment has walls
- the tools are easier to keep consistent
- broken environments are easier to reset
- damage inside the garage is less likely to become damage to the host system

Docker is not magic security.
But it is a very practical containment and packaging layer.

### 3.2 Open WebUI

**Open WebUI** is the user-facing front end.

This is where the user chats with the garage, reviews results, submits requests, and sees what the system is doing.
Open WebUI is the front counter, not the mechanic.

### 3.3 OpenHands

**OpenHands** is the main AI work environment for inside-the-garage task execution.

A simple explanation:
OpenHands is the system that gives a reasoning model a structured workspace where it can operate on files, inspect code, plan actions, and move through a task more like a worker than like a simple chat assistant.

That is why OpenHands matters to Jarvis.
It gives Jarvis a real workbench instead of just a chat box.

It should also be stated more explicitly that **OpenHands already includes the kind of built-in VS Code-style work surface that makes Jarvis feel like an operator inside the environment rather than just a text responder**.
That is not some distant future feature.
That is part of what makes OpenHands useful right now.

The more important operational point is that OpenHands gives Jarvis a controlled internal environment where Jarvis can behave like a high-privilege workshop operator inside the containerized garage.
That includes things such as:

- terminal-driven control of the internal environment
- command execution inside the garage workspace
- package and dependency operations when policy allows
- environment inspection
- process-oriented task progression
- workspace manipulation through command and editor actions
- pseudo-admin style control **inside the garage boundary**, without turning that into unrestricted host control

So the core value is not merely that Jarvis can read or patch an individual file.
The real value is that Jarvis can work like an operator with command-line reach, editor reach, and structured task reach inside the contained environment.

### 3.4 Stagehand

**Stagehand** is the browser/computer action layer used by Robin.

A simple explanation:
Stagehand is what lets Robin behave like the garage’s online hands and eyes.
It is the browser-driving layer that allows controlled web actions such as:

- opening pages
- navigating sites
- clicking
- scrolling
- filling forms
- reading what is on the page
- downloading files when policy allows it

### 3.5 Local model server

A local model server such as **LM Studio** provides the actual locally hosted models used by the garage.

That means the front end, the work environment, and the browser worker are not the model themselves.
They are the surrounding structure that lets the selected model do useful work.

### 3.6 Separate Docker stations working together

The major systems are expected to run in **separate Docker containers/services** while cooperating over a controlled internal network.

That means, conceptually:

- Open WebUI runs in its own container/service
- OpenHands runs in its own container/service
- Robin’s browser stack runs in its own container/service
- supporting services such as SQLite, artifact storage helpers, controllers, or watchdog helpers may run in their own containers/services too

This matters because it keeps responsibilities clean.
If one piece breaks, the whole garage does not have to become one giant tangled mess.

### 3.7 Host operating environment

The garage itself is meant to behave like an internal workshop layer, but the host-side operating foundation still matters.

The intended software environment should be described accurately as:

- a **Linux-based host environment**
- using a **Debian-style / Debian-based userland and package ecosystem** where appropriate
- with Docker acting as the main application containment boundary above that host OS

A cleaner way to say it is this:
The garage is not its own literal kernel.
It sits on top of a Linux host and is expected to inherit many practical assumptions from a Debian-style Linux operating environment.

That matters because the garage design will naturally depend on things such as:

- shell tooling
- package management behavior
- filesystem conventions
- service management expectations
- scripting assumptions
- permissions and path layout conventions

So when the contract refers to the garage as a controlled work environment, it is still grounded in a real Linux operating base, not in magic abstraction.

### 3.8 External higher-tier AI work surfaces

Over time, the garage may also make selective use of a **higher-tier external AI work surface** when needed.

The clean way to describe that is not to overhype it.
It is enough to say that such a worker may have **regular Suite-power-tier access** and therefore may expose capabilities such as:

- structured reasoning
- terminal-backed work
- controlled web access
- coding assistance
- the ability to help with broader computational task progression

The important point is that this is **not only about coding**.
It is also about:

- research
- information gathering
- detailed investigation
- structured comparison work
- computationally assisted problem solving
- multi-step reasoning across messy or complicated tasks

A clarification is important here:
**the built-in VS Code-style work surface already exists in OpenHands now**.
So the main reason to swap in a stronger worker is not to gain a code editor surface that did not exist before.
It is to gain stronger reasoning, bigger-context analysis, or better deep-problem-solving in the same Jarvis role when the task justifies it.

So if a higher-tier or larger worker is wired into the garage, the contract should describe it as a **capability upgrade to the Jarvis role** rather than as the first time the system gains a real workbench.
The value is in what the worker can do with those abilities, not in the mere fact that it can touch a browser or terminal.

---

## 4. Named roles

The project currently defines three primary named roles/components.

### 4.1 Jarvis

**Jarvis** is the main reasoning role.

Jarvis is responsible for:

- understanding user requests
- planning work
- operating on code and project files inside the garage
- using controlled terminal access inside the garage environment
- performing standard Linux / Debian-style terminal actions when policy allows
- using terminal-based internet access for normal command-line operations such as package retrieval, updates, and direct file fetching when appropriate
- deciding when outside-web work is required beyond terminal-only access
- consuming results returned by the web role
- continuing the overall job after a handoff completes
- integrating outputs into a usable result
- deciding when another subtask is needed

Jarvis is a **logical role**, not one permanently hardcoded model forever.
Jarvis may be backed by different reasoning-oriented models over time depending on:

- task size
- task complexity
- coding intensity
- context requirements
- local VRAM limits
- whether the current step needs stronger deep reasoning or broader analytical power

The contract should never assume Jarvis is one fixed model forever.
Jarvis is a role profile, not a permanent model lock.
That matters right now, not only later:
when a task is harder, a bigger or stronger model can be swapped into the Jarvis slot so the same role gains better reasoning without changing the surrounding garage architecture.

### 4.2 Robin

**Robin** is the dedicated web / visual / browser AI role.

Robin is responsible for:

- browser-based web research
- search behavior
- site navigation
- scrolling
- clicking
- forms
- downloads
- page interpretation
- interactive online tasks
- returning structured results back to the system

In the current design, Robin is built from:

- **Stagehand** as the browser/computer agent stack
- **a dedicated visual/browser-capable model profile** such as Qwen3-VL-8B or a future replacement

Robin is the AI role that should perform full interactive outside-web work.

### 4.3 Alfred

**Alfred** is the director / controller / housekeeper.

Alfred is **not an AI**.
Alfred is a **deterministic script or small service**.

Alfred exists to:

- start tasks
- create job records
- track progression state
- handle handoffs between Jarvis and Robin
- choose when a job is waiting, running, blocked, or complete
- coordinate model slot transitions
- call the file transfer broker when imports/exports are needed
- write logs, manifests, and artifact metadata
- enforce retry and failure policy
- act as the authoritative record keeper for the garage

Alfred is the project’s director and housekeeper, not its thinker.

### 4.4 Watchdog and librarian functions

Even if these functions start small, the contract should acknowledge that the garage will likely need a stricter supporting layer that behaves like a combination of:

- librarian
- timekeeper
- watchdog
- checkpoint registrar
- memory-index discipline layer

This does **not** automatically mean a separate giant service on day one.
These functions may initially live inside Alfred or next to Alfred.

But the purpose is clear:

- keep job records indexed properly
- enforce structured saves
- keep memory organized by date, job, worker, and checkpoint
- detect drift between expected state and actual state
- preserve progression evidence cleanly enough that the system can resume after interruption

This matters because basic folders alone are not enough.
The garage needs **structure within structure**.

---

## 5. What the AI Garage is supposed to become

The AI Garage is meant to become a local, controlled AI work environment that behaves like a real workshop.

The garage should be able to:

- start with a user request
- break the request into actionable work
- do local work inside a contained environment
- hand web/browser work to Robin when required
- receive and store results from Robin
- resume the larger task through Jarvis
- move files in and out only through a narrow brokered lane
- keep a persistent record of what happened, what failed, what succeeded, and what still needs to be done

The long-term goal is not simply “AI that can do a thing.”
The long-term goal is:

- **AI that can work through multi-step jobs**
- **AI that can recover from failure loops**
- **AI that can persist context through role changes**
- **AI that can stay inside safe boundaries while still being useful**
- **AI that can run continuously as a managed work system instead of a one-shot chat toy**

This means the garage is being designed around:

- role separation
- persistence
- auditable state changes
- limited external access
- deterministic control around nondeterministic AI work
- indexing discipline
- restart-safe recovery
- continuity across long-running work

The garage should eventually feel like a machine that can be pointed at a goal and keep grinding toward that goal, instead of a fragile conversation that dies the second context gets messy.

---

## 6. Design principles

### 6.1 Docker is the garage boundary

The AI Garage exists inside Docker because Docker provides the main containment boundary.

The reasons this matters are practical:

- the AI can be given meaningful capabilities inside the container without giving it uncontrolled host access
- the environment can be reset and rebuilt if it gets damaged
- the dependencies are easier to reproduce
- the browser stack and other tools can be contained
- failures inside the garage do not automatically become host-level problems

The entire architecture depends on treating Docker as the main containment layer.

### 6.2 The project is built around one active model slot

The system is being designed for hardware that should assume **one active local model at a time** for the core worker role.

This means:

- Jarvis and Robin are logical roles, not always concurrently resident models
- the system must preserve enough task state to pause one role and resume another
- the controller must treat model usage as a baton-pass, not as parallel multi-agent abundance

This is one of the most important truths of the project and must be respected at every level of the design.

### 6.3 Specialization is mandatory

One giant AI role that tries to do everything will be worse than specialized roles with clean handoffs.

So the initial specialization is:

- Jarvis = main reasoning / code / local task continuation
- Robin = browser / web / visual / online action worker
- Alfred = deterministic director and keeper of order

### 6.4 External access must be brokered

The garage should never be given broad host access by default.

Any interaction with the outside world should happen through narrow, explicit channels.

That is why:

- web work goes through Robin
- file import/export goes through a dedicated transfer broker
- state transitions go through Alfred

### 6.5 Persistence matters more than concurrency

The real challenge is not how to run many things at once.
The real challenge is how to keep track of the task as it moves between roles and still continue coherently.

So the design prioritizes:

- persistent task records
- append-only event logs
- structured handoffs
- resumable job state
- artifact retention

### 6.6 Durability matters more than pretty demos

The garage should be judged more by:

- whether it can resume after failure
- whether it can prove what happened
- whether it can preserve the last known good state
- whether it can reconstruct itself sanely
- whether it can keep working without corrupting its own memory

than by whether it looked flashy in a single one-off run.

---

## 7. Why one active local model at a time is still the right design

This needs to be explained directly because the hardware sounds strong on paper.

Even with a modern GPU such as a **5070-class card with 16 GB of VRAM**, it is still smart to design v0 around **one active local worker model at a time**.

That is because running multiple serious models at once creates pressure from:

- VRAM limits
- context window memory use
- browser stack overhead
- inference instability under load
- slower switching and worse responsiveness
- debugging complexity
- harder state coordination

In other words, the question is not just “can two models fit somehow.”
The real question is “can they run cleanly, predictably, and with sane orchestration while the rest of the garage is also alive.”

For v0, the answer is that the safer design is:

- one active worker model slot
- persistent task state
- controlled baton passing
- deterministic resumption

That gives a more stable system than pretending the garage has cloud-scale abundance locally.

### 7.1 Future expansion beyond one slot

Later versions can add:

- cloud API workers
- remote browser workers
- parallel child-job execution
- external reasoning workers
- model pools with checksums and result validation
- higher-tier external workers with Suite-power-tier capability surfaces

That future is valid.
But it should be built **after** the garage proves it can track state, verify outputs, and recover from failures in a sane way.

---

## 8. The garage as an OS inside an OS

A useful high-level explanation is that the AI Garage behaves like an **OS inside an OS**.

That does not mean it is literally booting a second kernel.
It means it has its own:

- users and worker roles
- workspace
- file flow rules
- task queue
- memory system
- logs
- artifacts
- policies
- lifecycle

So from the outside, the host machine is the building.
Inside that building, the garage is a **controlled workshop floor** where the AIs do their jobs.

This matters because it changes the mindset.
The project is not “talk to an AI and hope.”
It is “run a managed work environment where AI is one of the moving parts.”

### 8.1 Ground truth on the operating base

To keep this technically honest, the garage should be described as:

- a managed AI work environment
- running on top of a Linux host
- likely relying heavily on Debian-style conventions and tooling where that matches the host setup
- using Docker as the primary containment boundary inside that broader operating base

So the garage is “OS-like” in workflow discipline, not in the literal sense of replacing the host operating system.

---

## 9. 24/7 operation and continuous work progression

One of the long-term goals is for the garage to support **24/7 continuous reasoning and work progression**.

That does not mean one model thinks forever in one giant fragile chat session.
It means the system is built so work can continue across time through structured state, checkpoints, and resumable tasks.

If the garage is stable and fully wired, it should be able to support ongoing work on things such as:

- code projects
- documentation
- research tasks
- school assignments
- long-form writing
- data cleanup
- repeated technical workflows

The important idea is this:
The garage should not forget the whole damn job just because one model session ended.

### 9.1 What makes 24/7 operation possible

Continuous operation depends on:

- task ledgers
- checkpoints
- resumable child jobs
- per-worker memory banks
- deterministic controller state
- artifact retention
- restart-safe boot logic

### 9.2 What 24/7 operation does not mean

It does **not** mean:

- unlimited autonomous freedom
- uncontrolled host access
- blind endless loops
- no human oversight
- no failure controls

The point is managed continuity, not chaos.

### 9.3 What 24/7 operation should mean in practice

When the garage has been set up correctly, when the structures match the intended architecture, and when the prompts, behavior policies, tasks, and handoff rules have been built correctly, the system should be able to:

- keep progressing on the assigned job without needing sleep
- keep resuming from checkpoints instead of starting over
- keep pushing through multi-step work until the goal is reached or policy says stop
- keep operating like a machine rather than like a distracted assistant

The intent is blunt:

- no breaks needed
- no smoke breaks needed
- no sleep needed
- no forgetting the job because one chat window died

It should keep grinding until it reaches the required outcome, or until a defined policy, failure state, or human review condition stops it.

### 9.4 The real requirement behind nonstop operation

True nonstop operation is not mainly about raw model uptime.
It is about:

- stable task structure
- clean continuation notes
- durable memory registration
- deterministic restart logic
- proof of what step just completed
- proof of what step comes next

Without those things, “24/7” is just empty wording.
With those things, the garage can actually behave like a continuous work system.

---

## 10. The PO-box file transfer model

### 10.1 Purpose of the PO box

The host-side outside folder is not the live project workspace.
It is a **PO box**.

Its purpose is:

- getting files into the garage
- getting files out of the garage
- nothing else

It is not intended to be:

- a mounted live project root
- a working directory for the AI
- a general host filesystem bridge

### 10.2 Why the PO box is guarded so heavily

The PO box is guarded because the AI roles will have **pseudo-user powers** inside the garage.

That means the system may be able to:

- read and write files in its own workspace
- modify code
- run commands
- download packages
- generate artifacts
- export outputs

If a system with those powers is given broad, casual, always-open access to the host filesystem, one wrong action could:

- overwrite files
- damage projects
- delete the wrong thing
- spread bad outputs into trusted folders
- turn a contained mistake into a host-level mess

So the PO box exists to enforce one narrow, inspectable outside-facing file exchange lane.

That means:

- the user can drop in a script, archive, image, zip file, or other asset
- the garage can import it when explicitly instructed
- the garage can export results back out when explicitly instructed
- the AI does not need general access to host storage to do useful work

### 10.3 Transfer broker

The PO-box lane should be controlled by a dedicated transfer script/service.

The transfer broker is the only component allowed to touch the outside transfer folder.

Its job is:

- import requested files into the internal job inbox
- export requested outputs back to the outside folder
- write transfer manifests
- enforce path restrictions
- reject invalid or dangerous transfer requests

### 10.4 Transfer commands

The garage needs only two core transfer actions:

- `import_from_pobox`
- `export_to_pobox`

These are intentionally narrow.
They should not allow arbitrary path freedom.
They should not be generalized into broad filesystem access.

### 10.5 Why the transfer lane should stay narrow

If the AI can only move files through one brokered lane, then:

- file movement is auditable
- external access is easier to inspect
- host exposure is reduced
- path restrictions are enforceable
- the garage remains more self-contained

### 10.6 PO-box security intent

The import/export broker should be described even more clearly than before.
Its function should be **extremely narrow and heavily guarded**.

The broker should have literally one outside-facing purpose:

- write into the Docker-side environment when an import is allowed
- write out of the Docker-side environment when an export is allowed

That is it.

The broker should not become a casual side door for:

- arbitrary host browsing
- free path traversal
- unbounded mount behavior
- random shell execution against the host

This matters because the PO-box path is one of the few places where the inside garage meets the outside world.
If that lane is sloppy, the whole containment story gets weaker.

### 10.7 Breakout resistance philosophy

The PO-box layer is also part of the anti-breakout design.

Its job is not just convenience.
Its job is to reduce the chance that a tool or worker with strong inside-the-garage abilities can abuse import/export behavior to gain broader reach than intended.

So the transfer layer should be treated like a guarded mail slot, not like a shared hallway.

---

## 11. High-level system structure

The AI Garage v0 consists of these main layers.

### 11.1 User front door

The user interacts with the garage through Open WebUI and any future local control surfaces.

The front door is where:

- tasks begin
- prompts enter the system
- outputs are reviewed
- files are intentionally introduced through the PO-box lane

### 11.2 Jarvis lane

Jarvis handles:

- task interpretation
- planning
- reasoning
- coding
- file-local analysis
- taking returned web results and continuing the broader job

Jarvis should work only inside the controlled garage environment and on the files placed inside the internal workspace.

### 11.3 Robin lane

Robin handles:

- everything interactive or web-related
- anything requiring browsing, web navigation, downloads, or visual interpretation
- page-level extraction and online resource discovery

Robin is the dedicated external-web action specialist.

### 11.4 Alfred lane

Alfred coordinates:

- task creation
- task state
- child job creation
- handoff records
- retries
- completion rules
- import/export requests
- model slot sequencing

Alfred is the middle management of the garage.

### 11.5 Transfer lane

A separate broker handles file movement between the outside transfer folder and the internal garage.

This lane exists so neither Jarvis nor Robin has raw direct host-folder access.

### 11.6 Watchdog / indexing lane

The contract should also acknowledge an emerging support lane responsible for:

- save discipline
- checkpoint registration
- memory indexing
- crash detection
- timestamped continuity records
- durable artifact cataloging

That function may begin inside Alfred and later split into its own helper service.
But architecturally, it is important enough to name.

---

## 12. Why Alfred should be a script and not another AI

This point should be locked in early.

Alfred should be a deterministic script or lightweight service because:

- the controller should be cheap
- the controller should be predictable
- the controller should enforce policy, not improvise
- the controller should be easy to inspect and debug
- the controller should not burn model time deciding whether a state transition is valid

If Alfred were another AI, the system would become:

- more expensive
- less predictable
- harder to debug
- more likely to loop or improvise dumb behavior during failure handling

Alfred should be boring.
That is a good thing.

### 12.1 Alfred may still absorb watchdog functions

Even while Alfred stays deterministic, Alfred may still absorb additional responsibilities over time, such as:

- heartbeat collection
- container status observation
- crash-trigger handling
- checkpoint registration
- memory summary registration
- cross-service awareness

That does not turn Alfred into an AI.
It just turns Alfred into a more complete operations brain for the garage.

---

## 13. Core runtime architecture

The initial runtime architecture should be thought of as:

`User -> Open WebUI -> Jarvis/OpenHands -> Alfred -> Robin/Stagehand -> Alfred -> Jarvis/OpenHands -> User`

But with the understanding that:

- Alfred owns the official record
- Robin never directly decides the whole task
- Jarvis never directly roams the web lane
- all important changes are persisted before role transitions

This is a serialized orchestration model.

It is not a parallel swarm.
It is not a freeform multi-agent chat.
It is a controlled baton-pass system.

### 13.1 Extended runtime reality

In practice, the runtime will also include:

- a task ledger
- checkpoint logic
- health monitoring
- artifact indexing
- crash recovery policy
- transfer broker calls
- possibly external backup writes
- possibly Git-based durability writes

So the runtime is better understood as a **managed workflow system**, not as a single conversation chain.

---

## 14. Internal workspace model

The actual live work should happen **inside the garage**, not in the PO box.

Recommended conceptual internal layout:

```text
/workspace/
  jobs/
    <job-id>/
      input/
      work/
      output/
      artifacts/
      logs/
      handoffs/
      memory/
      checkpoints/
      manifests/
      runtime/
```

### Folder purposes

- `input/` → imported assets for the job
- `work/` → temporary active work area
- `output/` → finalized outputs ready for export
- `artifacts/` → screenshots, hashes, extracted JSON, traces, downloads, diagnostics
- `logs/` → job-local logs
- `handoffs/` → structured records of role-to-role requests and results
- `memory/` → task-local memory summaries and worker-specific continuation notes
- `checkpoints/` → last known good state, restart anchors, resume bundles
- `manifests/` → structured indexes of what belongs to the job
- `runtime/` → temporary runtime support state for the current execution window

This internal workspace should be where AI actually works.
The outside PO box should not be the place where AI actively edits files.

### 14.1 Structure within structure

The current structure should be understood as a **starting frame**, not as a final ceiling.

The garage will likely need additional internal layers over time, such as:

- worker-specific subfolders
- environment-specific folders
- dependency staging directories
- virtual environment directories
- indexed daily snapshots
- per-step manifests
- retry-state bundles
- per-artifact verification files

The project should assume that there may be cases where:

- a job needs its own local virtual environment
- a dependency must be staged in a different directory
- extra root folders or supporting volumes are needed
- certain job types require their own sub-layout

So the internal workspace model must remain expandable.

### 14.2 Every job needs indexed placement

The garage should not rely on loose piles of files.
Every serious job should have its own indexed placement, including:

- job id
- parent id if applicable
- date or timestamp markers
- worker lane provenance
- checkpoint count
- artifact counts
- state summary pointers

The point is that every day, every update, every memory save, and every progression event should be structured well enough that the system can reconstruct what happened later.

---

## 15. Task progression and tracking

The most important system problem is not browsing or coding.
The most important system problem is **keeping track of the task as it evolves**.

That means the garage needs a real progression model.

### 15.1 Parent task and child jobs

Every user task should become a **parent task**.

That parent task may create multiple **child jobs**.

Examples of child jobs:

- local reasoning step
- code modification step
- browser research step
- download step
- extraction step
- validation step
- packaging step
- export step
- checkpoint consolidation step
- recovery analysis step

The parent task stays alive until the required child jobs are complete.

### 15.2 State ownership

Alfred owns the authoritative state.

Neither Jarvis nor Robin should be the authoritative keeper of the full task progression.
They contribute work.
Alfred records and coordinates the progression.

### 15.3 Minimum state machine

#### Parent task states

- `created`
- `planned`
- `running`
- `waiting_on_child`
- `resuming`
- `assembling`
- `review_ready`
- `done`
- `failed`
- `recovery_analysis`
- `rollback_pending`

#### Child job states

- `queued`
- `leased`
- `running`
- `retry_wait`
- `blocked`
- `completed`
- `failed`
- `checkpointed`
- `rebuild_pending`

This structure is enough to start with.
It can be extended later, but it should not start as a chaotic freeform status model.

---

## 16. Best way to store progression and memory

The simplest reliable first design is:

- **SQLite** for canonical task/job state
- **JSONL** for append-only event logs
- **artifact directories** for generated files and evidence
- **worker memory summaries** for continuity across restarts

This is the best initial tradeoff because it is:

- local
- simple
- inspectable
- easy to back up
- easy to query
- not overengineered

The system does not need a distributed queue stack or a giant message bus to get started.

### 16.1 SQLite use

SQLite should store:

- parent tasks
- child jobs
- worker role assignments
- model profile used
- retry counts
- timestamps
- current status
- failure buckets
- pointers to artifacts and output records
- memory summary pointers
- checkpoint references
- recovery attempt records
- last-known-good markers

### 16.2 JSONL use

JSONL should store append-only event history, such as:

- task created
- task updated
- child job emitted
- child job started
- handoff completed
- import performed
- export performed
- failure encountered
- retry scheduled
- task completed
- memory checkpoint written
- container health change observed
- rollback started
- rollback completed
- recovery attempt skipped

This becomes the garage’s memory of what actually happened, independent of what any one AI currently remembers.

### 16.3 Memory-bank model

Each major worker should have its own memory bank.

That does **not** mean vague magical long-term memory.
It means structured, inspectable continuity records.

Recommended memory layers:

#### Global garage memory

Stores durable system facts such as:

- environment facts
- known tool availability
- policy defaults
- recurring workflow recipes
- garage configuration notes

#### Jarvis memory bank

Stores things such as:

- project summaries
- codebase notes
- prior design decisions
- unfinished reasoning threads
- validated assumptions
- pending local tasks
- observed recurring failure patterns
- candidate behavioral improvements

#### Robin memory bank

Stores things such as:

- site workflow notes
- domain-specific navigation recipes
- stable extraction patterns
- prior download results
- known page quirks
- browsing constraints encountered earlier

#### Task memory

Stores per-job continuity such as:

- what the user asked for
- what has already been completed
- what remains blocked
- the last known good step
- what artifacts exist
- what handoff should occur next

#### Artifact memory

Stores durable evidence such as:

- screenshots
- downloaded files
- hashes
- extracted JSON
- logs
- traces

### 16.4 Why separate memory banks matter

If the garage shuts down and comes back later, the workers should not be forced to start from zero every time.

Instead:

- Alfred reconstructs the authoritative task state from SQLite and JSONL
- task memory tells the next worker where the job left off
- Jarvis resumes its local reasoning context from summaries
- Robin resumes its online context from browsing summaries and artifacts

That is how the system becomes restart-safe and continuity-friendly.

### 16.5 Dual-save durability model

The garage should eventually save important continuity data in at least **two different locations**.

That means the durability model may include:

- the primary internal garage storage
- a secondary external storage target for memory and critical saves

The purpose is simple:
If one place goes bad, the work history is not gone.

For important memory, progress records, and checkpoint material, the system should be able to copy or mirror critical data to:

- an external attached storage device
- a dedicated backup volume
- a secondary archive path

The exact storage device can change over time, but the principle stays the same:
important job memory and continuity data should not live in only one place.

### 16.6 External backup and Git durability

In addition to local dual-save durability, the project should also consider:

- offline repository snapshots
- online repository pushes when appropriate
- Git commits for code and structured config history
- exportable recovery bundles for severe failure cases

This does not mean every scratch file needs to be committed.
It means the garage should eventually support **durable project-state preservation** through both filesystem backups and repository-based history.

### 16.7 Cross-container awareness and checks and balances

The contract should explicitly acknowledge a checks-and-balances model across containers and services.

The idea is that each important container or service should not operate as if it is alone.
Instead, the garage should move toward a system where:

- services emit heartbeats
- services can observe the health state of peer services
- one service crashing becomes a recorded event for the others
- failures are registered into the shared ledger instead of dying silently

That way, if one part of the garage stops, the others do not remain blind.

### 16.8 Recovery requires analysis before blind restart

If a service crashes or something catastrophic goes wrong, the system should not just mindlessly slam restart forever.

A better design is:

1. stop or pause the affected workflow safely
2. record the crash and affected components
3. gather recent logs, state, and artifacts
4. identify the likely reason for the crash if possible
5. restore or reconstruct from the last known good checkpoint
6. only then attempt restart or rebuild
7. resume work using the latest valid known differences and saved continuity state

This matters because a dumb restart loop just recreates the same crash again.
A sane system should at least attempt to understand the failure before replaying it.

---

## 17. How Jarvis and Robin should communicate

Jarvis and Robin should not communicate through vague prose memory.
They should communicate through **structured handoff records** that Alfred owns.

### 17.1 Handoff request

When Jarvis needs Robin to do web work, Alfred should create a child job with a structured payload.

That payload should include:

- job id
- parent task id
- worker role (`robin_web_vl`)
- requested model profile
- goal
- constraints
- allowed domains
- max steps
- whether downloads are allowed
- expected outputs
- retry budget

### 17.2 Handoff result

When Robin completes the work, Robin should return a structured result envelope.

That result should include:

- job id
- status
- summary
- structured result object
- visited URLs if relevant
- downloaded file paths if relevant
- artifact list
- failure bucket if failed
- continuation hints for Jarvis

Then Alfred records that result and Jarvis resumes from it.

### 17.3 Why this matters

This allows:

- continuity
- resumability
- auditability
- lower ambiguity
- better debugging
- less token waste

---

## 18. The one-model-at-a-time baton-pass model

Because only one serious local worker model should be assumed active at a time, the AI Garage must behave like a baton relay.

### 18.1 Baton-pass sequence

Typical sequence:

1. user gives task
2. Jarvis begins reasoning about the task
3. Jarvis determines web/browser work is required
4. Alfred records a child job for Robin
5. Alfred checkpoints task state
6. the active worker slot is handed to Robin’s model profile
7. Robin performs browser/web work
8. Robin returns structured results
9. Alfred records results, artifacts, and status
10. Alfred hands the baton back to Jarvis
11. Jarvis resumes the parent task using Robin’s returned results

This may happen multiple times inside the same parent task.

### 18.2 Why the baton-pass has to be dynamic

The baton-pass should not be rigid.
It should be **dynamic during task progression**.

That means Jarvis can hit new obstacles during a task and emit new child jobs as needed.
For example:

- Jarvis needs a package version check
- Jarvis needs a documentation page read
- Jarvis needs a browser-only download
- Jarvis needs a site flow tested
- Jarvis needs a release file fetched
- Jarvis needs a live example copied into structured notes

Each time, Alfred can decide:

- whether the task is allowed
- whether the job should go to Robin
- whether a retry is allowed
- whether the result should be merged back into the parent task

### 18.3 Simple baton example

A realistic simple flow:

- Jarvis is patching code
- Jarvis discovers a library name but does not trust the version
- Jarvis asks Alfred for a web child job
- Alfred emits a Robin task: find the official install docs and latest stable package name
- Robin goes online, visits the official docs, extracts the needed information, and returns it
- Alfred records the result
- Jarvis resumes, updates the code or install instructions, and keeps going

That is the baton-pass system in normal use.

---

## 19. What kind of tool abilities Jarvis should have

Jarvis should have **inside-the-garage worker tools**.

These are not claims about one official vendor API forever.
They are examples of the kinds of tool capabilities a Jarvis-class worker should be wired to use inside the garage.

### 19.1 Core Jarvis operator profile

Jarvis should be described as the garage’s senior system architect, senior coding and analysis programmer, systems engineer, and high-authority reasoning worker.

Jarvis is the god-tier inside-the-garage position doing the heavy intellectual and technical lifting. Jarvis is expected to:

- architect solutions
- analyze complex technical problems
- reason across code, systems, dependencies, workflows, and project goals
- operate the environment through terminal and editor control inside the garage boundary
- make high-level technical judgments
- break ambiguous work into sane next steps
- decide when terminal-based access is enough and when Robin needs to take over
- integrate returned findings into the larger job
- keep the whole task coherent from start to finish

The point is not that Jarvis can do tiny obvious file actions.
The point is that Jarvis acts like a senior operator with pseudo-admin style command authority inside the contained environment, combining system architecture, coding, analysis, planning, and deep reasoning in one top-tier role.

### 19.3 What Jarvis should do

With that position, Jarvis should:

- design and restructure projects
- solve hard coding and systems problems
- analyze failures, logs, dependencies, and architecture tradeoffs
- drive the parent task forward
- decide what is known, unknown, blocked, or worth delegating
- call Robin when the job needs deeper browser or web investigation beyond normal terminal access
- absorb Robin’s findings and turn them into decisions, code, plans, fixes, or deliverables
- return with follow-up questions or flagged uncertainty when ambiguity remains instead of blindly pushing bad assumptions

Jarvis is the worker that should carry the garage’s heaviest reasoning burden and keep the whole effort technically sane.

### 19.4 Jarvis as more than a coder

The contract should be explicit that Jarvis is not just a coding bot.
Jarvis is a broader computational worker.

Jarvis may be used for:

- coding
- technical writing
- research synthesis
- investigation
- planning
- structured comparison work
- computational reasoning
- messy task decomposition

That broader framing matches the actual purpose of the garage better than limiting Jarvis to “software only.”

---

## 20. What kind of tool abilities Robin should have

Robin should have **browser and visual action tools**.

Again, these are conceptual tool surfaces for the garage design.
They are not promises about a single vendor API.

### 20.1 Core Robin operator profile

Robin should be described as a deep web investigator and browser operator, not as a dumb clicker.

Robin is meant to crawl through the web, follow chains of pages, inspect multiple layers of results, dig into files, docs, release assets, nested links, and rendered content, and keep going until the real target information or file is found.

Robin should be able to:

- chase a task several layers deep across the web
- compare competing answers or conflicting evidence
- inspect browser-rendered content that terminal access alone will miss
- use Stagehand / Playwright-style actions, scrolling, navigation, and screenshots as part of grounded investigation
- return not only the result, but also ambiguity, conflicting A/B possibilities, missing pieces, or reasons the answer is not yet trustworthy
- escalate back with a structured “this may be A or B; confirm whether to continue or search deeper” style response when the evidence is unclear

The point is that Robin is also a thinking cog in the garage.
Robin is not just a fetcher.
Robin is the browser-minded investigative AI that goes out, digs, evaluates, and comes back with grounded findings or flagged uncertainty.

### 20.2 Example Robin-style tool calls

Conceptual examples:

- `open_url(url)`
- `search_web(query)`
- `click(selector_or_target)`
- `type_text(target, value)`
- `scroll_page(direction, amount)`
- `wait_for(condition)`
- `extract_page_data(schema)`
- `download_file(url_or_target)`
- `capture_screenshot(label)`
- `submit_result_envelope(payload)`

### 20.3 What Robin should do

With those capabilities, Robin can return:

- the requested result when it is clear
- the best-supported candidate answers when there are multiple plausible results
- screenshots, page evidence, downloads, and source trails showing how the result was reached
- ambiguity flags when the evidence conflicts or the page flow is unclear
- a recommendation on whether the garage should accept the result, compare more sources, or send Robin back out for deeper search

Robin is the garage’s online hands, eyes, and investigative reasoning worker.

### 20.4 Higher-tier external work surface alignment

If Robin or a future auxiliary worker is ever backed by a higher-tier external work environment, the contract should still describe the result in operational terms.

That means capabilities such as:

- terminal-backed research
- browser-backed retrieval
- built-in code workspace support
- broader multi-step computational help

should be treated as tools that extend the garage’s reach, not as a reason to blur the existing role boundaries.

---

## 21. Jarvis responsibilities in detail

Jarvis is the main inside-the-garage worker.

Jarvis should be able to:

- understand the user task
- break work into steps
- modify code
- operate the environment through terminal and editor actions
- use standard command-line networked operations when policy allows
- inspect local files and local runtime state
- process results returned from Robin
- decide whether another handoff is necessary
- continue iteratively until the parent task is complete
- build summaries for future continuation
- leave clean continuation notes for the next session
- identify predictable patterns in recurring work
- suggest policy or workflow improvements based on repeated observations

Jarvis should not:

- directly perform full interactive browser-deep web work when that work belongs in Robin’s lane
- directly move files into/out of the host PO box
- directly override Alfred’s state machine
- directly take over Robin’s browser responsibilities

Jarvis is the primary local worker and main reasoning engine, not the universal access role.
Jarvis can have **terminal-based internet reach** for ordinary Linux / Debian-style command operations inside policy, but the moment the task becomes truly browser-interactive, visually interpretive, or several pages deep, the handoff should go to Robin.

---

## 22. Robin responsibilities in detail

Robin is the dedicated web/visual/online worker.

Robin, implemented through Stagehand plus a visual/browser-capable model profile, should be responsible for:

- web navigation
- search behavior
- page interpretation
- following page chains and deeper navigation paths
- clicking
- scrolling
- form entry
- download actions
- extracting relevant information
- digging through multiple layers of web material to find the real target information or file
- using Stagehand / Playwright-style browser behavior and screenshot evidence to support findings
- returning structured online results
- recording browsing artifacts

Robin should not:

- own the full parent task
- do general codebase reasoning unless necessary for the browser job
- become the permanent canonical source of task truth
- manage import/export policy directly

Robin is the external-web specialist.
Robin is the worker that should take over when the garage needs a browser-minded operator that can behave like a smart person sitting in front of a computer and chasing information several layers deep across the web.

---

## 23. Alfred responsibilities in detail

Alfred should be deliberately small and deterministic.

Alfred should own:

- task creation
- task ids and child job ids
- state transitions
- job leasing
- retry policy enforcement
- timeout handling
- result recording
- artifact indexing
- transfer broker calls
- model baton-pass management
- continuation-note checkpoints
- memory summary registration

Alfred should not:

- think like an AI
- browse the web
- do coding work
- operate as a hidden third worker AI

Alfred is the director, clerk, and safety manager.

### 23.1 Alfred and watchdog cooperation

As the garage matures, Alfred should also coordinate or host a watchdog layer responsible for:

- crash detection
- restart gating
- log collection
- peer-service awareness
- recovery sequencing
- controlled rollback behavior

Alfred should be the authority that decides whether work:

- continues normally
- pauses for analysis
- resumes from a checkpoint
- rebuilds a failed container
- stops because the same failure is repeating

That prevents dumb infinite crash cycles.

---

## 24. Retry and failure behavior

The garage should not rely on AI improvisation for failure handling.
Instead, failures should be assigned to **failure buckets**, and the behavior for each bucket should be controlled by deterministic policy.

Examples of failure buckets:

- `timeout`
- `navigation_failed`
- `download_failed`
- `import_failed`
- `export_failed`
- `policy_denied`
- `output_missing`
- `model_unavailable`
- `browser_worker_failed`
- `validation_failed`
- `resume_context_missing`
- `checkpoint_missing`
- `container_crashed`
- `repeated_boot_failure`
- `storage_write_failed`

Each bucket should have a defined response, such as:

- retry once
- retry with reduced step budget
- escalate to parent task
- hard fail immediately
- request user intervention
- roll back to last good checkpoint
- rebuild service from a known-good image
- rehydrate memory summaries before resuming

This prevents uncontrolled looping and token waste.

### 24.1 Crash recovery watchdog behavior

The project should eventually implement a proper crash recovery watchdog system.

That watchdog should aim to do all of the following:

- detect when a critical container or service crashes
- notify the ledger and peer services
- gather logs and recent state
- determine whether restart is safe
- restore the failed component to the latest valid known state
- bring it up to date using the latest recorded differences when possible
- resume work only after the environment is sane again

The goal is not just to restart.
The goal is to recover **intelligently**.

### 24.2 Avoiding dumb crash loops

If a container crashes, the system should not simply hammer the same restart sequence forever.

A better rule is:

- inspect
- classify
- checkpoint
- reconstruct
- retry with evidence

If the likely cause has not been addressed, then a blind restart is not recovery.
It is just another crash with extra steps.

---

## 25. Behavioral policy files

The garage will likely need behavioral policy files later.
These should not start as giant AI-authored chaos documents.
They should start as small, layered, human-owned configuration files.

Recommended layers:

### 25.1 Global guardrails

Defines:

- max retries
- max downloads
- max file size
- allowed transfer extensions
- export rules
- timeout caps
- no-access zones
- resource caps

### 25.2 Worker policy

Defines per-worker behavior, such as:

- Robin retry policy for navigation failures
- Jarvis retry policy for local step failures
- Alfred escalation rules

### 25.3 Task policy overrides

Defines job-specific adjustments, such as:

- downloads allowed
- specific domains allowed
- stricter timeout
- export review required
- step budget changes

### 25.4 Policy evolution over time

The contract should also acknowledge that behavioral policy files may improve over time through observed patterns.

The clean way to frame that is:

- predictable recurring events should be logged
- repeated workflow successes and failures should be analyzed
- Jarvis may propose improvements to policy behavior files based on pattern matching and deep reasoning
- Alfred or a human review layer should decide what gets accepted into canonical policy

This allows the garage to become better over time without turning policy into uncontrolled self-edit chaos.

### 25.5 Policy self-improvement boundaries

The long-term vision can include a system where the garage gradually improves its own policy and behavior files.
But that should happen through structured channels such as:

- candidate policy diffs
- logged justification
- repeat-pattern evidence
- approval rules
- rollback ability

That gives the system a way to self-improve without losing control of the rule base.

---

## 26. Web browsing extensions and network hardening

Over time, Robin’s web lane will likely need more mature browsing support.
That should be described carefully.

Useful future capabilities include:

- proxy support
- session persistence when appropriate
- controlled header/profile configuration
- timeout and retry rules
- backoff strategies
- download verification
- domain allowlists
- stable browser fingerprints within policy
- artifact capture for failed page flows

The purpose of these features is not to act like malware or smash through site protections.
The purpose is to make the browser worker **more reliable, more consistent, and less fragile** when dealing with modern websites.

That means the design should favor:

- slower, sane request pacing
- reliable retries
- consistent session handling
- clear timeout behavior
- user review when a site blocks or challenges access

In other words, the goal is professional browsing stability, not reckless evasion.

---

## 27. Safety philosophy

The AI Garage is being built this way because control matters.

### 27.1 Good safety properties

This design provides:

- containment inside Docker
- narrow file transfer boundaries
- no wide-open host filesystem roaming
- role separation
- auditable task state
- recoverable workflows
- easier reset when the garage breaks
- less risk than handing one AI unrestricted system reach

### 27.2 Why this design is safer

It is safer because:

- the web worker is isolated from being the whole system
- the main reasoner is not automatically given host-wide web and file powers
- the transfer lane is narrow
- the controller is deterministic
- state is persisted instead of left to AI memory alone
- crash recovery is expected to be evidence-driven instead of purely improvised

---

## 28. Weaknesses and limitations

This design has real downsides too, and they should be acknowledged.

### 28.1 One-model-at-a-time slows things down

Because only one major local worker model is assumed active at once:

- handoffs cost time
- model changes cost time
- iterative workflows can feel slower than parallel systems

### 28.2 The controller and state model must be built carefully

Alfred may be small, but if Alfred is wrong, the whole system gets messy fast.

### 28.3 Policy design will be annoying

The behavioral guardrails and failure handling policies will take real work to get right.

### 28.4 The browser role will still need real testing

Robin’s capabilities sound broad, but they will need real-world validation against:

- bad sites
- wrong downloads
- weird versions
- failed installs
- broken workflows
- partial results

### 28.5 The garage can still fail in ugly ways

Docker containment helps, but it does not magically make bad orchestration or bad logic harmless.

The system still needs:

- sane defaults
- logs
- checkpoints
- recovery paths

### 28.6 Durability layers add complexity

The moment the garage starts doing:

- mirrored saves
- Git durability
- external storage sync
- checkpoint replay
- watchdog-driven reconstruction

it becomes more powerful, but also more operationally complex.

That complexity is worth it only if it is kept structured and inspectable.

---

## 29. Why this project structure is still good

Even with those downsides, this design is strong because it makes hard constraints explicit rather than pretending they do not exist.

It accepts that:

- hardware is limited
- web work is different from reasoning work
- file access should be narrow
- progress must be tracked explicitly
- AI needs deterministic supervision in the middle
- memory and durability need real engineering

That makes it a more realistic and more robust design than a vague “let one AI do everything” setup.

---

## 30. Long-term direction

If this structure works, the AI Garage can grow into a more powerful local work environment with:

- better model profile selection
- more deterministic replay/caching of repeated browser workflows
- richer policy files
- better artifacts and reports
- stronger task templates
- better handoff schemas
- additional specialized roles if hardware and stability allow later
- cloud API workers for parallel overflow work
- checksum-based result verification
- better resumption after shutdowns or crashes
- a smarter memory indexing layer
- mirrored memory durability
- external backup targets
- Git-based continuity protection
- better crash reconstruction and service healing

If the project progresses at a steady pace with correct management, it could eventually automate or absorb pieces of work that today are split across multiple coding, research, documentation, and technical support roles.

That does not mean magic replacement overnight.
It means the project could become a serious production-grade automation garage that handles large portions of technical workflow with trackable proof, artifacts, and results.

But those future expansions should be built on top of the same core principles defined here:

- role separation
- deterministic control
- persistent state
- narrow external access
- recoverable workflows
- indexed memory
- durability across failure

---

## 31. End-to-end example: collectible card indexing program

The best way to explain the AI Garage is to show what a real task flow looks like.

Assume the user wants this:

> Build a program that catalogs collectible cards, stores metadata, tracks prices, and helps find where cards can be bought online.

For a concrete example, use a **Pokemon card indexing program**.

### 31.1 The user request

The user gives the garage:

- a rough idea
- maybe a starter folder or old script through the PO box
- a goal such as:
  - create a local app or script
  - catalog cards
  - store name, set, rarity, condition, and market notes
  - fetch current store references or public listing references
  - export a usable report

### 31.2 Step 1: Jarvis starts the parent task

Jarvis receives the request through Open WebUI and begins the parent task.

Jarvis may do things such as:

- inspect imported files
- identify the app structure needed
- propose a storage format
- create the basic project scaffold
- draft the schema for cards and pricing records
- create the first code files

At this point Jarvis is doing local reasoning and build work.

### 31.3 Step 2: Jarvis hits an outside-web dependency

Jarvis realizes it needs live information such as:

- card metadata source ideas
- public product reference pages
- store page structure examples
- official set naming conventions
- current pricing page patterns

Jarvis should not directly wander the web lane.
So Jarvis asks Alfred to create a Robin child job.

### 31.4 Step 3: Alfred creates the Robin job

Alfred records:

- parent task id
- Robin child job id
- goal
- allowed domains
- whether downloads are allowed
- expected output format
- retry budget

Then Alfred checkpoints the current state.

### 31.5 Step 4: Robin takes the baton

Robin receives the child job and decides how to complete it using its browser tools.

Robin may:

- open official Pokemon card references
- inspect public listing pages
- compare how titles and set numbers are written
- gather examples of card metadata fields
- capture screenshots of relevant page structures
- extract example product fields into JSON
- note which sites are too messy or blocked to use reliably

Robin is not trying to own the whole project.
Robin is just doing the online leg of the job.

### 31.6 Step 5: Robin returns structured results

Robin returns a result envelope to Alfred containing things such as:

- summary of what was found
- usable field names
- example URLs
- structured extraction data
- screenshots
- notes about domain limitations
- downloaded public reference files if allowed

Alfred records everything.

### 31.7 Step 6: Jarvis resumes and continues building

Jarvis gets the baton back.
Now Jarvis can use Robin’s results to:

- refine the database schema
- build scraper adapters or importers for allowed sources
- normalize card naming
- create search and filter functions
- build price history tables
- generate export formats

### 31.8 Step 7: Jarvis hits another problem

Jarvis may then discover a second issue.
For example:

- a site uses heavy JavaScript
- product pages load dynamically
- a download link is hidden behind a browser flow
- current examples are inconsistent between stores

Jarvis again asks Alfred for another Robin job.

This second Robin job may say:

- test whether the target site is usable with browser extraction
- inspect the dynamic page flow
- capture the final rendered fields
- determine whether downloading is necessary or whether field extraction is enough

Robin does the browser work, returns the result, and Alfred hands the baton back again.

### 31.9 Step 8: Alfred keeps the job from turning into chaos

The entire time, Alfred is doing boring but critical work:

- tracking child jobs
- writing event logs
- storing artifacts
- checking retry budgets
- recording what was already done
- preserving continuation notes
- preventing the task from turning into one giant lost chat session

That is why Alfred matters so much.
Without Alfred, the garage becomes a memory leak with vibes.

### 31.10 Step 9: Final assembly

Once Jarvis has enough information, Jarvis can:

- finish the indexing program
- write setup instructions
- create output samples
- generate a report of supported sources
- export the finished project to the PO box

### 31.11 What the user sees

From the user’s point of view, the process looks clean:

- the user gave a goal
- the garage broke it into pieces
- online work happened when needed
- local build work continued after each handoff
- progress was preserved
- the final result came back as a usable deliverable

That is the point of the design.
The garage is not supposed to feel like random AI mood swings.
It is supposed to feel like a controlled workshop pipeline.

### 31.12 What happens if a crash hits mid-job

A stronger version of this example should also acknowledge failure handling.

If a container crashes in the middle of the card-indexing build, the intended system behavior should eventually be:

- the crash is detected and logged
- peer services become aware of it
- the parent task is paused or shifted into recovery analysis
- recent logs, artifacts, and memory summaries are gathered
- the last known good checkpoint is located
- the failed component is rebuilt or restarted only when policy allows
- the parent task resumes from the restored checkpoint using the latest valid saved differences

That is how the garage turns a crash from total derailment into a recoverable interruption.

---

## 32. v0.3 implementation summary

At v0.3, the project should be thought of as:

- **Open WebUI** = user front door
- **OpenHands** = Jarvis work environment with built-in VS Code-style operator surface
- **Jarvis** = main reasoning / local work role
- **Robin** = Stagehand-based web/visual role
- **Alfred** = deterministic controller / tracker / director
- **Watchdog / librarian layer** = save discipline, indexing, recovery support
- **Transfer broker** = narrow PO-box import/export lane
- **Task ledger** = SQLite + JSONL + artifacts + memory summaries
- **Durability model** = local state + secondary backups + optional Git continuity
- **Garage boundary** = Docker
- **Host base reality** = Linux host with Debian-style operating assumptions where applicable
- **Model reality** = one active major local worker slot at a time
- **Model swap reality** = stronger reasoning can be gained now by swapping a larger or better model into the Jarvis slot when the task gets harder

## 33. Updated contract position

This updated version reflects a more serious direction for the garage.

The project is no longer being described as only:

- a Docker stack
- a one-shot coding assistant
- a browser helper

It is being described as a controlled AI workshop environment that must eventually support:

- durable memory
- structured indexing
- container-aware health checks
- intelligent crash recovery
- narrow and hardened import/export boundaries
- continuous long-run work progression
- policy evolution through logged patterns and reviewable improvements

That is the better direction for the contract.
It keeps the original foundation, but it adds the missing durability, operational discipline, and long-run machine behavior that the garage will need if it is going to become a real system instead of just a cool demo.

