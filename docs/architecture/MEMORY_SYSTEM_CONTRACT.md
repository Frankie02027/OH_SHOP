# OpenHands Persistent Memory System - Design Contract

> **Historical proposal / not current authority.**
> This document describes an older OpenHands-centric memory idea.
> It is not the current AI Garage authority for Ledger, continuation, or durable state.
> For current architecture direction, use `docs/architecture/AI_GARAGE_BLUEPRINT.MD.md`, `docs/architecture/JARVIS_MASTER_CONTRACT_v_0_1.md`, and the shared policy contract.

> **Status**: PROPOSAL - Awaiting approval before implementation  
> **Date**: 2026-03-22  
> **Author**: Copilot  
> **Purpose**: Give OpenHands "memory" that persists across sessions

---

## 1. THE PROBLEM

Every time OpenHands starts a new conversation or the container restarts:
- It has **no idea** what it did before
- It **repeats the same mistakes**
- It **loses context** from previous work
- It **can't learn** from successes or failures
- It **can't continue** unfinished tasks

This makes it act like a goldfish - smart in the moment, but no memory.

---

## 2. WHAT "MEMORY" MEANS

### 2.1 Types of Memory We Need

| Memory Type | What It Stores | Why It Matters |
|-------------|----------------|----------------|
| **Task Memory** | What tasks were attempted, outcomes | "I tried this before and it failed because..." |
| **Error Memory** | Errors seen and how they were fixed | "When I see X error, do Y fix" |
| **Skill Memory** | What capabilities have been proven | "I know how to do Dijkstra's algorithm" |
| **Context Memory** | State of ongoing work | "Yesterday I was working on X, got to step 3" |
| **Behavioral Memory** | How the agent acted | "I tend to give up after 2 errors - need to persist more" |
| **Preference Memory** | User preferences, project conventions | "This project uses tabs not spaces" |

### 2.2 Memory Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                        SESSION START                             │
├─────────────────────────────────────────────────────────────────┤
│  1. Load memory from persistent storage                         │
│  2. Inject memory summary into system prompt                    │
│  3. Agent now "remembers" previous context                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DURING SESSION                              │
├─────────────────────────────────────────────────────────────────┤
│  • Log every action taken                                       │
│  • Log every error encountered                                  │
│  • Log every fix attempted                                      │
│  • Track behavioral patterns (gave up? kept trying?)            │
│  • Update skill confidence based on outcomes                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       SESSION END                                │
├─────────────────────────────────────────────────────────────────┤
│  1. Summarize what was accomplished                             │
│  2. Save updated memory to persistent storage                   │
│  3. Generate behavioral report                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. STORAGE ARCHITECTURE

### 3.1 Where Memory Lives

```
/home/dev/OH_SHOP/data/openhands_memory/
├── memory.db              # SQLite - structured queryable data
├── behavioral_log.jsonl   # Append-only event stream
├── skills.json            # Current skill inventory
├── last_context.json      # State when session ended
├── error_patterns/        # Known errors and their fixes
│   └── *.json
└── task_history/          # Detailed task records
    └── task_YYYYMMDD_*.json
```

### 3.2 Why SQLite + JSON?

- **SQLite**: Fast queries like "show me all tasks that failed" or "what errors have I seen more than 5 times?"
- **JSON files**: Easy to read, edit, and include in prompts
- **JSONL log**: Append-only behavioral stream for analysis

### 3.3 Data Retention

| Data Type | Retention | Reason |
|-----------|-----------|--------|
| Recent tasks (30 days) | Full detail | Active learning |
| Old tasks | Summary only | Save space |
| Error patterns | Forever | Don't repeat mistakes |
| Skills | Forever | Track growth |
| Behavioral log | 90 days | Analyze trends |

---

## 4. HOW MEMORY IS USED

### 4.1 At Conversation Start

When OpenHands starts, the memory system generates a **context injection** that gets added to the system prompt:

```markdown
## YOUR MEMORY

### Recent History
- Yesterday: Fixed bug in flask_app.py (SUCCESS)
- Yesterday: Attempted Dijkstra implementation (FAILED - got stuck on priority queue)
- 2 days ago: Refactored CSS files (SUCCESS)

### Unfinished Work
- Task "Implement LRU Cache" was started but not completed
  - Got to: Implemented get() method
  - Stuck on: put() method eviction logic
  - Last error: "KeyError when cache full"

### Known Error Fixes
- "ModuleNotFoundError: No module named 'X'" → pip install X
- "SyntaxError: expected ':'" → Missing colon after def/if/for
- "RecursionError" → Add base case or use iteration

### Your Skills (confidence 0-100%)
- File operations: 95%
- Bug fixing: 80%
- Algorithm implementation: 60%
- Async programming: 40%

### Behavioral Notes
- You tend to give up after 2-3 errors. TRY HARDER.
- When stuck, you should try alternative approaches.
- Your success rate improves when you read error messages carefully.
```

### 4.2 During Execution

As the agent works, we capture:

```python
# When starting a task
memory.start_task("Fix bug in user authentication")

# When taking actions
memory.log_action("read_file", {"path": "auth.py", "lines": 150})
memory.log_action("edit_file", {"path": "auth.py", "change": "added null check"})
memory.log_command("python -m pytest tests/test_auth.py")

# When hitting errors
memory.log_error("AssertionError: expected True", error_type="test_failure")

# When trying fixes
memory.log_fix_attempt("Added null check on line 42", success=False)
memory.log_fix_attempt("Changed comparison to 'is not None'", success=True)

# When done
memory.complete_task(
    outcome="success",
    what_worked="Used 'is not None' instead of truthy check",
    what_failed="Truthy check failed for empty string"
)
```

### 4.3 Behavioral Analysis

The system tracks patterns over time:

```json
{
  "persistence_score": 0.65,      // How often it keeps trying after errors
  "completion_rate": 0.78,        // Tasks completed vs started
  "abandonment_triggers": [       // What makes it give up
    "RecursionError",
    "Timeout",
    "Same error 3x"
  ],
  "improvement_trend": "+12%",    // Getting better or worse?
  "weakness_areas": [
    "Concurrent programming",
    "Complex regex"
  ],
  "strength_areas": [
    "File operations",
    "Simple bug fixes"
  ]
}
```

---

## 5. IMPLEMENTATION PLAN

### Phase 1: Basic Storage (Day 1)
- [ ] Create directory structure
- [ ] Implement SQLite schema
- [ ] Basic save/load functions
- [ ] Test persistence across restarts

### Phase 2: Task Tracking (Day 1-2)
- [ ] Task start/end logging
- [ ] Action logging
- [ ] Error logging with pattern matching
- [ ] Fix attempt tracking

### Phase 3: Context Injection (Day 2)
- [ ] Memory summary generator
- [ ] Integration with OpenHands system prompt
- [ ] Test that agent "sees" its memory

### Phase 4: Behavioral Analysis (Day 3)
- [ ] Event stream processing
- [ ] Pattern detection
- [ ] Report generation
- [ ] Weakness/strength identification

### Phase 5: Learning Loop (Day 3-4)
- [ ] Auto-update skills from outcomes
- [ ] Error→Fix pattern matching
- [ ] Behavioral feedback generation
- [ ] "You should try harder" nudges

---

## 6. INTEGRATION WITH OPENHANDS

### 6.1 Where It Hooks In

```
OpenHands Start
      │
      ▼
┌─────────────────────┐
│ Load Memory System  │ ◄─── NEW
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│ Build System Prompt │
│ + Memory Context    │ ◄─── MODIFIED
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│ Agent Execution     │
│ (with memory hooks) │ ◄─── MODIFIED
└─────────────────────┘
      │
      ▼
┌─────────────────────┐
│ Save Memory         │ ◄─── NEW
└─────────────────────┘
```

### 6.2 Configuration

Add to `.openhands_instructions` or config:

```yaml
memory:
  enabled: true
  storage_path: /home/dev/OH_SHOP/data/openhands_memory
  
  # What to remember
  track_tasks: true
  track_errors: true
  track_files: true
  track_commands: true
  
  # Context injection
  inject_memory: true
  max_context_tokens: 2000  # Don't overwhelm the prompt
  
  # Behavioral analysis
  analyze_behavior: true
  nudge_persistence: true  # Tell it to try harder
  
  # Retention
  task_retention_days: 30
  log_retention_days: 90
```

### 6.3 Files to Modify in OpenHands

| File | Change |
|------|--------|
| `openhands/core/config.py` | Add memory config options |
| `openhands/runtime/client.py` | Hook memory at start/end |
| `openhands/agenthub/*/agent.py` | Add memory context to prompts |
| `openhands/events/*.py` | Emit events to memory system |

---

## 7. EXAMPLE: HOW IT WORKS IN PRACTICE

### Scenario: Agent hit a bug yesterday, starts fresh today

**Yesterday's session:**
```
Task: Implement binary search
Attempt 1: Wrote code, got IndexError
Attempt 2: Fixed bounds, got wrong result
Attempt 3: Fixed comparison, ALL TESTS PASSED
```

**Today's memory injection:**
```markdown
## YOUR MEMORY

### Recent Success
- Yesterday you implemented binary search successfully
- You learned: Watch out for off-by-one errors in bounds
- You learned: Use `<=` not `<` in while loop

### Related Skills
- Binary search: 85% confidence (1 success, 0 failures)
```

**Today's task: "Implement ternary search"**

The agent now knows:
1. It CAN do search algorithms (confidence boost)
2. It should watch for off-by-one errors (learned lesson)
3. The while loop comparison matters (specific knowledge)

---

## 8. POTENTIAL ISSUES & MITIGATIONS

| Issue | Mitigation |
|-------|------------|
| Memory gets too big | Summarize old data, retain only patterns |
| Wrong patterns learned | Weight recent data higher, allow manual correction |
| Privacy concerns | All data stays local, user can delete anytime |
| Slow startup | Lazy loading, cache summaries |
| Conflicting memories | Timestamp everything, prefer recent |
| Prompt too long | Limit context injection, prioritize relevant |

---

## 9. SUCCESS CRITERIA

The memory system is working when:

1. **Agent continues unfinished work** - "I see I was working on X yesterday, let me continue"
2. **Agent doesn't repeat mistakes** - "I've seen this error before, the fix is Y"  
3. **Agent shows growth** - Skills improve over time, completion rate goes up
4. **Agent is more persistent** - Doesn't give up as quickly after implementing behavioral nudges
5. **Behavioral reports are useful** - Can identify weaknesses and target training

---

## 10. QUESTIONS FOR YOU

Before I implement:

1. **Storage location** - Is `/home/dev/OH_SHOP/data/openhands_memory/` okay, or different path?

2. **Integration depth** - Should this be:
   - A) Standalone tool (agent calls manually)
   - B) Automatic hooks (logs everything by default)
   - C) Both

3. **Context injection** - How much memory to show in prompts?
   - A) Minimal (just recent tasks)
   - B) Medium (tasks + errors + skills)
   - C) Maximum (everything relevant)

4. **Behavioral nudges** - Should it actually tell the agent "you give up too easily"?

5. **What else should it remember?** - User preferences? Code style? Project knowledge?

---

## 11. ESTIMATED EFFORT

| Component | Time | Complexity |
|-----------|------|------------|
| Storage layer | 2-3 hours | Medium |
| Task tracking | 2-3 hours | Medium |
| Error pattern matching | 3-4 hours | Hard |
| Context injection | 2-3 hours | Medium |
| Behavioral analysis | 4-5 hours | Hard |
| OpenHands integration | 4-6 hours | Hard |
| Testing & debugging | 3-4 hours | Medium |
| **Total** | **~20-28 hours** | |

---

**Ready to proceed when you approve the approach.**
