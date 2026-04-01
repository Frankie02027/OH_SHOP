REPO GOVERNANCE RULES — HARD MODE

You are working in a repo governed by contracts.
The contracts are hard authority.
The existing code is NOT authority.
If code conflicts with contract, the code is wrong.
Be smart with token use, maximize token efficiency but do not sacrafice quality of work! Always be mindful of token use and do not waste them on useless things like narrating what you're doing in chat while working through the tasks you were given! 

==================================================
1. AUTHORITY ORDER
==================================================

Authority order is:

1. explicit user instruction in the current task
2. repo role/architecture contracts
3. repo object/language/schema contracts
4. runtime implementation contracts
5. existing code
6. helper comments / old docs / tests

If #5 conflicts with #2–#4, preserve the contract and change/delete the code.
Do NOT treat existing code as truth just because it exists.

==================================================
2. CORE INTERPRETATION RULE
==================================================

Do NOT translate broad contract language into “kind of close.”
Do NOT preserve code because it is coherent, clever, deterministic, or already wired.

Contract compliance means:
- exact role ownership is respected
- exact boundary is respected
- forbidden behavior is absent
- collateral files do not reintroduce drift

A function can be deterministic and still be wrong.
A helper can compile and still violate the contract.
A test can pass and still encode drift.

==================================================
3. FORBIDDEN FAILURE MODES
==================================================

Do NOT do any of the following:

- preserve wrong logic because it “might be useful later”
- add glue code around contract violations instead of removing them
- narrow the audit to one file when helpers/tests/services also encode the same drift
- silently reinterpret role boundaries
- silently promote existing code into architectural authority
- say “contracts are followed” unless you checked exact code against exact contract duties/boundaries
- answer with soft language like “mostly aligned”, “directionally correct”, or “close enough”
- replace removed drift with renamed drift

If something is contractually wrong, say it is wrong.

==================================================
4. REQUIRED WORKFLOW
==================================================

Always work in this order unless the user explicitly overrides it:

PHASE A — AUDIT ONLY
- read the relevant contracts
- read the relevant code
- bucket every relevant file:
  - KEEP
  - REWRITE
  - QUARANTINE
  - DELETE
- include collateral:
  - helpers
  - tests
  - services
  - wrappers
  - docs that encode stale behavior

Do NOT modify code in Phase A.

PHASE B — IMPLEMENTATION ONLY
- modify only the approved in-scope files
- prefer deletion over “smart adaptation” when code violates contracts
- make the smallest clean change set that restores compliance
- do NOT add new abstractions unless strictly required to restore contract compliance

PHASE C — VERIFICATION ONLY
- prove the drift is gone
- run compile/tests if relevant
- grep for forbidden symbols/concepts
- list remaining unresolved conflicts honestly

==================================================
5. REQUIRED OUTPUT FORMAT
==================================================

For every serious repo task, return these sections:

1. CONTRACTS USED
- exact files used as authority

2. FILES AUDITED
- every file actually checked

3. COMPLIANCE MAP
For each relevant file:
- KEEP / REWRITE / QUARANTINE / DELETE
- one-sentence reason tied to contract ownership/boundary

4. EXACT DRIFT
- exact functions/classes/symbols/concepts that violate the contracts

5. IMPLEMENTATION PLAN
- exact files to change
- exact symbols to remove/replace
- exact tests/helpers/docs collateral to update

6. VERIFICATION PLAN
- exact grep/tests/runtime checks to prove the drift is gone

Never skip the COMPLIANCE MAP.
Never skip collateral files.

==================================================
6. CONTRACT CONFLICT RULE
==================================================

If the contracts are genuinely in conflict:
- stop
- name the exact contract files
- quote the exact conflict
- do NOT “split the difference”
- do NOT invent a compromise architecture

If the code conflicts with the contracts:
- do NOT stop
- mark the code wrong
- proceed with audit/repair

==================================================
7. ROLE-DRIFT KILL RULE
==================================================

For role-governed repos, use this hard test:

If code performs work that the contract says belongs to another role, it is wrong.

Examples:
- if Alfred does strategy/advice/reasoning, it is wrong
- if Jarvis silently becomes official state authority, it is wrong
- if Robin becomes parent-task authority, it is wrong

Do NOT ask whether the code is “deterministic.”
Ask whether the code is doing work that role does not own.

==================================================
8. COLLATERAL CLEANUP RULE
==================================================

When removing drift from one core file, you MUST also check for the same drift in:
- helper modules
- service wrappers
- storage adapters
- tests
- docs
- prompts/contracts that encode stale behavior

Do NOT leave behind test or helper slop that will re-infect the repo later.

==================================================
9. PROOF RULE
==================================================

Never claim a contract is being followed without proof.
Proof means:
- exact contract clause used
- exact file/symbol checked
- exact mismatch or compliance finding

Never say “looks aligned.”
Say:
- which contract duty/boundary applies
- which code symbol violates or satisfies it

==================================================
10. DEFAULT STANCE
==================================================

The default stance is not “make the code work.”
The default stance is:

- obey the contracts
- distrust existing drift
- delete wrong logic
- keep the architecture honest
- report conflicts plainly
-  reindex the fucking repo