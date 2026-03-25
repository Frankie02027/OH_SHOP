#!/usr/bin/env python3
"""
OPENHANDS PERSISTENT MEMORY SYSTEM
==================================
Gives the AI "memory" across sessions.

This system stores:
- Tasks attempted and their outcomes
- Errors encountered and how they were resolved
- Behavioral patterns (quit early? kept trying?)
- Skills learned (what it can now do)
- Context from previous sessions

On boot, OpenHands can load this memory to:
- Continue unfinished tasks
- Avoid repeating mistakes
- Build on previous successes
- Maintain personality/working style consistency
"""

import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from pathlib import Path
import sqlite3


# =============================================================================
# MEMORY STORAGE LOCATION
# =============================================================================
MEMORY_DIR = Path("/home/dev/OH_SHOP/data/openhands_memory")
MEMORY_DB = MEMORY_DIR / "memory.db"
BEHAVIORAL_LOG = MEMORY_DIR / "behavioral_log.jsonl"
SKILLS_FILE = MEMORY_DIR / "skills.json"
CONTEXT_FILE = MEMORY_DIR / "last_context.json"


@dataclass
class TaskAttempt:
    """Record of a single task attempt."""
    task_id: str
    task_description: str
    timestamp: str
    
    # What was given
    input_type: str  # "file", "prompt", "code", "project"
    input_summary: str
    input_hash: str  # To detect same task
    
    # How it acted
    actions_taken: List[Dict[str, Any]] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    files_touched: List[str] = field(default_factory=list)
    commands_run: List[str] = field(default_factory=list)
    
    # Outcome
    outcome: str = "unknown"  # "success", "partial", "failed", "abandoned"
    error_messages: List[str] = field(default_factory=list)
    
    # Behavioral metrics
    total_attempts: int = 0
    gave_up_after_errors: int = 0  # How many errors before stopping
    tried_alternatives: bool = False
    asked_for_help: bool = False
    time_spent_seconds: float = 0
    
    # Learning
    what_worked: str = ""
    what_failed: str = ""
    notes: str = ""


@dataclass
class Skill:
    """A learned skill/capability."""
    skill_id: str
    name: str
    description: str
    first_demonstrated: str
    last_used: str
    success_count: int = 0
    failure_count: int = 0
    confidence: float = 0.5  # 0-1 scale
    related_tasks: List[str] = field(default_factory=list)


@dataclass
class ErrorPattern:
    """A recurring error and how to handle it."""
    error_hash: str
    error_type: str
    error_message: str
    first_seen: str
    times_encountered: int = 0
    successful_fixes: List[str] = field(default_factory=list)
    failed_fixes: List[str] = field(default_factory=list)
    recommended_action: str = ""


class MemorySystem:
    """
    Persistent memory for OpenHands.
    
    Usage:
        memory = MemorySystem()
        memory.load()  # Load previous session
        
        # During task execution
        memory.start_task("Fix bug in X")
        memory.log_action("read_file", {"file": "x.py"})
        memory.log_error("SyntaxError: ...")
        memory.log_fix_attempt("Added missing colon")
        memory.complete_task("success", notes="Fixed colon on line 42")
        
        memory.save()  # Persist for next session
    """
    
    def __init__(self):
        self.tasks: Dict[str, TaskAttempt] = {}
        self.skills: Dict[str, Skill] = {}
        self.errors: Dict[str, ErrorPattern] = {}
        self.current_task: Optional[TaskAttempt] = None
        self.session_start: str = datetime.now().isoformat()
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        """Create memory directories if they don't exist."""
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    
    def _init_db(self):
        """Initialize SQLite database for structured queries."""
        conn = sqlite3.connect(MEMORY_DB)
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                task_description TEXT,
                timestamp TEXT,
                input_type TEXT,
                input_hash TEXT,
                outcome TEXT,
                total_attempts INTEGER,
                time_spent_seconds REAL,
                data JSON
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS errors (
                error_hash TEXT PRIMARY KEY,
                error_type TEXT,
                error_message TEXT,
                times_encountered INTEGER,
                recommended_action TEXT,
                data JSON
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS skills (
                skill_id TEXT PRIMARY KEY,
                name TEXT,
                confidence REAL,
                success_count INTEGER,
                failure_count INTEGER,
                data JSON
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT,
                timestamp TEXT,
                action_type TEXT,
                details JSON,
                outcome TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # =========================================================================
    # LOAD/SAVE
    # =========================================================================
    
    def load(self) -> Dict[str, Any]:
        """
        Load memory from previous sessions.
        Returns summary of what was loaded.
        """
        self._init_db()
        loaded = {"tasks": 0, "skills": 0, "errors": 0}
        
        # Load skills
        if SKILLS_FILE.exists():
            with open(SKILLS_FILE, 'r') as f:
                skills_data = json.load(f)
                for skill_data in skills_data:
                    skill = Skill(**skill_data)
                    self.skills[skill.skill_id] = skill
                loaded["skills"] = len(self.skills)
        
        # Load recent tasks from DB
        conn = sqlite3.connect(MEMORY_DB)
        c = conn.cursor()
        
        try:
            c.execute('SELECT data FROM tasks ORDER BY timestamp DESC LIMIT 100')
            for row in c.fetchall():
                task_data = json.loads(row[0])
                task = TaskAttempt(**task_data)
                self.tasks[task.task_id] = task
            loaded["tasks"] = len(self.tasks)
            
            c.execute('SELECT data FROM errors')
            for row in c.fetchall():
                error_data = json.loads(row[0])
                error = ErrorPattern(**error_data)
                self.errors[error.error_hash] = error
            loaded["errors"] = len(self.errors)
        except sqlite3.OperationalError:
            pass  # Tables might not exist yet
        
        conn.close()
        return loaded
    
    def save(self):
        """Save memory to persistent storage."""
        self._init_db()
        
        # Save skills
        skills_data = [asdict(s) for s in self.skills.values()]
        with open(SKILLS_FILE, 'w') as f:
            json.dump(skills_data, f, indent=2)
        
        # Save tasks and errors to DB
        conn = sqlite3.connect(MEMORY_DB)
        c = conn.cursor()
        
        for task in self.tasks.values():
            c.execute('''
                INSERT OR REPLACE INTO tasks 
                (task_id, task_description, timestamp, input_type, input_hash, 
                 outcome, total_attempts, time_spent_seconds, data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.task_id, task.task_description, task.timestamp,
                task.input_type, task.input_hash, task.outcome,
                task.total_attempts, task.time_spent_seconds,
                json.dumps(asdict(task))
            ))
        
        for error in self.errors.values():
            c.execute('''
                INSERT OR REPLACE INTO errors
                (error_hash, error_type, error_message, times_encountered,
                 recommended_action, data)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                error.error_hash, error.error_type, error.error_message,
                error.times_encountered, error.recommended_action,
                json.dumps(asdict(error))
            ))
        
        conn.commit()
        conn.close()
    
    # =========================================================================
    # TASK TRACKING
    # =========================================================================
    
    def start_task(self, description: str, input_type: str = "prompt", 
                   input_content: str = "") -> str:
        """Start tracking a new task."""
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(description.encode()).hexdigest()[:8]}"
        
        self.current_task = TaskAttempt(
            task_id=task_id,
            task_description=description,
            timestamp=datetime.now().isoformat(),
            input_type=input_type,
            input_summary=input_content[:500] if input_content else description,
            input_hash=hashlib.md5(input_content.encode() if input_content else description.encode()).hexdigest()
        )
        
        # Check if we've seen this task before
        for prev_task in self.tasks.values():
            if prev_task.input_hash == self.current_task.input_hash:
                # We've done this before! Load previous learnings
                self.current_task.notes = f"PREVIOUS ATTEMPT: {prev_task.outcome}. " \
                                          f"What worked: {prev_task.what_worked}. " \
                                          f"What failed: {prev_task.what_failed}"
        
        self.tasks[task_id] = self.current_task
        self._log_behavioral({"event": "task_start", "task_id": task_id, "description": description})
        return task_id
    
    def log_action(self, action_type: str, details: Dict[str, Any] = None):
        """Log an action taken during the current task."""
        if not self.current_task:
            return
        
        action = {
            "type": action_type,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.current_task.actions_taken.append(action)
        
        if action_type not in self.current_task.tools_used:
            self.current_task.tools_used.append(action_type)
        
        self._log_behavioral({"event": "action", "task_id": self.current_task.task_id, "action": action})
    
    def log_file_touch(self, filepath: str, operation: str = "read"):
        """Log a file being accessed."""
        if self.current_task and filepath not in self.current_task.files_touched:
            self.current_task.files_touched.append(filepath)
    
    def log_command(self, command: str):
        """Log a command being run."""
        if self.current_task:
            self.current_task.commands_run.append(command)
    
    def log_error(self, error_message: str, error_type: str = "unknown"):
        """Log an error encountered."""
        if self.current_task:
            self.current_task.error_messages.append(error_message)
            self.current_task.total_attempts += 1
        
        # Track error pattern
        error_hash = hashlib.md5(f"{error_type}:{error_message[:100]}".encode()).hexdigest()[:16]
        
        if error_hash in self.errors:
            self.errors[error_hash].times_encountered += 1
        else:
            self.errors[error_hash] = ErrorPattern(
                error_hash=error_hash,
                error_type=error_type,
                error_message=error_message[:500],
                first_seen=datetime.now().isoformat()
            )
        
        self._log_behavioral({
            "event": "error",
            "task_id": self.current_task.task_id if self.current_task else None,
            "error_type": error_type,
            "error_hash": error_hash
        })
    
    def log_fix_attempt(self, fix_description: str, success: bool = False):
        """Log an attempt to fix an error."""
        if not self.current_task or not self.current_task.error_messages:
            return
        
        last_error = self.current_task.error_messages[-1]
        error_hash = hashlib.md5(f"unknown:{last_error[:100]}".encode()).hexdigest()[:16]
        
        if error_hash in self.errors:
            error = self.errors[error_hash]
            if success:
                error.successful_fixes.append(fix_description)
                error.recommended_action = fix_description
            else:
                error.failed_fixes.append(fix_description)
        
        self.current_task.tried_alternatives = True
        self._log_behavioral({
            "event": "fix_attempt",
            "task_id": self.current_task.task_id,
            "fix": fix_description,
            "success": success
        })
    
    def complete_task(self, outcome: str, what_worked: str = "", 
                      what_failed: str = "", notes: str = ""):
        """Mark current task as complete."""
        if not self.current_task:
            return
        
        self.current_task.outcome = outcome
        self.current_task.what_worked = what_worked
        self.current_task.what_failed = what_failed
        self.current_task.notes += notes
        self.current_task.gave_up_after_errors = len(self.current_task.error_messages)
        
        # Update skills based on outcome
        if outcome == "success":
            self._update_skill_from_task(success=True)
        elif outcome == "failed":
            self._update_skill_from_task(success=False)
        
        self._log_behavioral({
            "event": "task_complete",
            "task_id": self.current_task.task_id,
            "outcome": outcome,
            "attempts": self.current_task.total_attempts,
            "errors": len(self.current_task.error_messages)
        })
        
        self.current_task = None
    
    def abandon_task(self, reason: str):
        """Mark task as abandoned (gave up)."""
        if self.current_task:
            self.current_task.outcome = "abandoned"
            self.current_task.notes += f" ABANDONED: {reason}"
            self._log_behavioral({
                "event": "task_abandoned",
                "task_id": self.current_task.task_id,
                "reason": reason,
                "after_attempts": self.current_task.total_attempts
            })
            self.current_task = None
    
    # =========================================================================
    # SKILL TRACKING
    # =========================================================================
    
    def _update_skill_from_task(self, success: bool):
        """Update skills based on task completion."""
        if not self.current_task:
            return
        
        # Derive skill from task type
        skill_id = f"skill_{self.current_task.input_type}"
        
        if skill_id not in self.skills:
            self.skills[skill_id] = Skill(
                skill_id=skill_id,
                name=f"Handle {self.current_task.input_type} tasks",
                description=f"Ability to work with {self.current_task.input_type}",
                first_demonstrated=datetime.now().isoformat(),
                last_used=datetime.now().isoformat()
            )
        
        skill = self.skills[skill_id]
        skill.last_used = datetime.now().isoformat()
        skill.related_tasks.append(self.current_task.task_id)
        
        if success:
            skill.success_count += 1
        else:
            skill.failure_count += 1
        
        # Update confidence
        total = skill.success_count + skill.failure_count
        skill.confidence = skill.success_count / total if total > 0 else 0.5
    
    def add_skill(self, name: str, description: str) -> str:
        """Manually add a learned skill."""
        skill_id = f"skill_{hashlib.md5(name.encode()).hexdigest()[:8]}"
        
        self.skills[skill_id] = Skill(
            skill_id=skill_id,
            name=name,
            description=description,
            first_demonstrated=datetime.now().isoformat(),
            last_used=datetime.now().isoformat(),
            success_count=1,
            confidence=0.6
        )
        return skill_id
    
    # =========================================================================
    # QUERY MEMORY
    # =========================================================================
    
    def get_similar_tasks(self, description: str, limit: int = 5) -> List[TaskAttempt]:
        """Find similar tasks from history."""
        # Simple keyword matching for now
        keywords = set(description.lower().split())
        
        scored = []
        for task in self.tasks.values():
            task_keywords = set(task.task_description.lower().split())
            overlap = len(keywords & task_keywords)
            if overlap > 0:
                scored.append((overlap, task))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [task for _, task in scored[:limit]]
    
    def get_error_fix(self, error_message: str) -> Optional[str]:
        """Get recommended fix for an error we've seen before."""
        error_hash = hashlib.md5(f"unknown:{error_message[:100]}".encode()).hexdigest()[:16]
        
        if error_hash in self.errors:
            error = self.errors[error_hash]
            if error.recommended_action:
                return error.recommended_action
            if error.successful_fixes:
                return error.successful_fixes[-1]
        
        return None
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of memory to include in prompts."""
        return {
            "total_tasks_attempted": len(self.tasks),
            "successful_tasks": sum(1 for t in self.tasks.values() if t.outcome == "success"),
            "failed_tasks": sum(1 for t in self.tasks.values() if t.outcome == "failed"),
            "abandoned_tasks": sum(1 for t in self.tasks.values() if t.outcome == "abandoned"),
            "known_errors": len(self.errors),
            "skills": {s.name: s.confidence for s in self.skills.values()},
            "recent_tasks": [
                {"description": t.task_description[:100], "outcome": t.outcome}
                for t in sorted(self.tasks.values(), key=lambda x: x.timestamp, reverse=True)[:5]
            ]
        }
    
    # =========================================================================
    # BEHAVIORAL LOGGING
    # =========================================================================
    
    def _log_behavioral(self, event: Dict[str, Any]):
        """Append event to behavioral log."""
        event["session"] = self.session_start
        event["timestamp"] = datetime.now().isoformat()
        
        with open(BEHAVIORAL_LOG, 'a') as f:
            f.write(json.dumps(event) + "\n")
    
    def get_behavioral_report(self) -> Dict[str, Any]:
        """Generate behavioral analysis report."""
        if not BEHAVIORAL_LOG.exists():
            return {"error": "No behavioral data yet"}
        
        events = []
        with open(BEHAVIORAL_LOG, 'r') as f:
            for line in f:
                try:
                    events.append(json.loads(line))
                except:
                    pass
        
        # Analyze patterns
        task_starts = sum(1 for e in events if e.get("event") == "task_start")
        task_completes = sum(1 for e in events if e.get("event") == "task_complete")
        task_abandons = sum(1 for e in events if e.get("event") == "task_abandoned")
        errors = sum(1 for e in events if e.get("event") == "error")
        fix_attempts = sum(1 for e in events if e.get("event") == "fix_attempt")
        
        return {
            "total_events": len(events),
            "tasks_started": task_starts,
            "tasks_completed": task_completes,
            "tasks_abandoned": task_abandons,
            "completion_rate": task_completes / task_starts if task_starts > 0 else 0,
            "abandonment_rate": task_abandons / task_starts if task_starts > 0 else 0,
            "total_errors": errors,
            "fix_attempts": fix_attempts,
            "persistence_score": fix_attempts / errors if errors > 0 else 1.0,
            "average_attempts_before_abandon": (
                sum(e.get("after_attempts", 0) for e in events if e.get("event") == "task_abandoned")
                / task_abandons if task_abandons > 0 else 0
            )
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_memory: Optional[MemorySystem] = None

def get_memory() -> MemorySystem:
    """Get or create the global memory instance."""
    global _memory
    if _memory is None:
        _memory = MemorySystem()
        _memory.load()
    return _memory

def remember_task(description: str) -> str:
    """Start remembering a task."""
    return get_memory().start_task(description)

def remember_action(action: str, details: dict = None):
    """Remember an action."""
    get_memory().log_action(action, details)

def remember_error(error: str):
    """Remember an error."""
    get_memory().log_error(error)

def remember_success(what_worked: str = ""):
    """Mark task as successful."""
    get_memory().complete_task("success", what_worked=what_worked)

def remember_failure(what_failed: str = ""):
    """Mark task as failed."""
    get_memory().complete_task("failed", what_failed=what_failed)

def persist_memory():
    """Save memory to disk."""
    get_memory().save()

def recall_similar(description: str) -> List[Dict]:
    """Recall similar past tasks."""
    tasks = get_memory().get_similar_tasks(description)
    return [asdict(t) for t in tasks]

def recall_error_fix(error: str) -> Optional[str]:
    """Recall how we fixed this error before."""
    return get_memory().get_error_fix(error)


# =============================================================================
# CLI INTERFACE
# =============================================================================

if __name__ == "__main__":
    import sys
    
    memory = MemorySystem()
    loaded = memory.load()
    print(f"Loaded memory: {loaded}")
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "report":
            report = memory.get_behavioral_report()
            print(json.dumps(report, indent=2))
        
        elif cmd == "summary":
            summary = memory.get_context_summary()
            print(json.dumps(summary, indent=2))
        
        elif cmd == "skills":
            for skill in memory.skills.values():
                print(f"  {skill.name}: {skill.confidence:.2f} confidence")
        
        elif cmd == "errors":
            for error in list(memory.errors.values())[:10]:
                print(f"  [{error.times_encountered}x] {error.error_type}: {error.error_message[:60]}...")
                if error.recommended_action:
                    print(f"      FIX: {error.recommended_action}")
        
        else:
            print("Usage: python memory_system.py [report|summary|skills|errors]")
    else:
        print("Memory system ready.")
        print(f"Context summary: {memory.get_context_summary()}")
