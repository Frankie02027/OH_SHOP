# OpenHands Capabilities Audit Report

**Date:** 2026-03-22  
**Workspace:** `/home/dev/OH_SHOP`  
**OpenHands Version:** v1.3.0 (with V0 legacy agent running)

---

## Executive Summary

OpenHands is already a **fully capable god-tier agent** out of the box. It has:
- Full bash terminal access
- Python/IPython execution 
- File read/write/edit capabilities
- Web browsing (BrowserGym-based)
- Package manager access (pip, apt, npm)
- MCP tool integration (connected to oh-browser-mcp)

**The only missing piece is AI-driven browser navigation** (blocked for local LLM due to `browser-use` requiring structured output). This is being addressed separately with Stagehand integration.

---

## 1. Available Agents

| Agent | Purpose | Status |
|-------|---------|--------|
| **CodeActAgent** | Main agent - code generation, bash, IPython, file editing, browsing | ✅ Active (default) |
| **BrowsingAgent** | Specialized web browsing with BrowserGym | ✅ Available |
| **VisualBrowsingAgent** | Visual/screenshot-based browsing | ✅ Available |
| **DummyAgent** | Testing agent | ✅ Available |
| **LOCAgent** | Lines-of-code focused agent | ✅ Available |
| **ReadonlyAgent** | Read-only operations | ✅ Available |

---

## 2. Built-in Tools (Already Available)

### 2.1 Bash Terminal (`execute_bash`)
```
Full Linux shell access with:
- Persistent session (env vars, cwd persist between commands)
- Command chaining (&&, ;, |)
- Process management (background tasks, Ctrl+C)
- Timeout controls
```
**Status:** ✅ FULLY WORKING

### 2.2 Python/IPython (`execute_ipython_cell`)
```
Interactive Python environment with:
- Magic commands (%pip, %cd, etc.)
- Variable persistence across cells
- Full library access
```
**Status:** ✅ FULLY WORKING

### 2.3 File Editor (`str_replace_editor`)
```
Commands:
- view: Display file contents or directory listing
- create: Create new files
- str_replace: Find and replace text
- insert: Insert text at line number
- undo_edit: Revert last edit
```
**Status:** ✅ FULLY WORKING

### 2.4 Browser Tool (`web_browse`)
BrowserGym-based with 15 actions:
```
Navigation:
- goto(url)           - Navigate to URL
- go_back()           - Browser back
- go_forward()        - Browser forward
- noop(wait_ms)       - Wait for page load

Interaction:
- click(bid)          - Click element by bid
- dblclick(bid)       - Double-click
- fill(bid, value)    - Fill form field
- select_option(bid, options) - Select dropdown
- clear(bid)          - Clear input
- press(bid, key)     - Press keyboard key
- hover(bid)          - Hover over element
- focus(bid)          - Focus element
- scroll(dx, dy)      - Scroll page
- drag_and_drop(from, to) - Drag and drop
- upload_file(bid, path) - Upload file
```
**Status:** ⚠️ PARTIALLY WORKING (basic navigation works, AI-driven clicking blocked for local LLM)

### 2.5 Think Tool
```
Agent logs reasoning/thought process
```
**Status:** ✅ FULLY WORKING

### 2.6 Finish Tool
```
Agent signals task completion
```
**Status:** ✅ FULLY WORKING

### 2.7 Task Tracker
```
Long-horizon planning and task management
```
**Status:** ✅ FULLY WORKING

### 2.8 MCP Tool Integration
```
Calls external MCP server tools
Currently connected to: http://host.docker.internal:3010/sse
Tool discovered: web_research
```
**Status:** ✅ CONNECTED (underlying browser-use blocked for now)

---

## 3. Runtime Actions (Event Types)

| Action | Description | Status |
|--------|-------------|--------|
| `CmdRunAction` | Execute bash commands | ✅ Working |
| `IPythonRunCellAction` | Execute Python code | ✅ Working |
| `FileReadAction` | Read file contents | ✅ Working |
| `FileWriteAction` | Write file contents | ✅ Working |
| `FileEditAction` | Edit files (str_replace/insert/view/create) | ✅ Working |
| `BrowseURLAction` | Navigate to URL | ✅ Working |
| `BrowseInteractiveAction` | Interact with browser | ⚠️ Partial |
| `MCPAction` | Call MCP tools | ✅ Working |
| `AgentDelegateAction` | Delegate to sub-agent | ✅ Working |
| `AgentFinishAction` | Complete task | ✅ Working |
| `AgentThinkAction` | Log thought | ✅ Working |
| `TaskTrackingAction` | Track subtasks | ✅ Working |
| `RecallAction` | Retrieve from memory | ✅ Working |
| `MessageAction` | Send message to user | ✅ Working |

---

## 4. Runtime Environment

### 4.1 Sandbox Container Image
```
Base: nikolaik/python-nodejs:python3.12-nodejs22
Runtime: ghcr.io/openhands/runtime:oh_v1.3.0_*
```

### 4.2 Pre-installed Tools
| Tool | Version | Status |
|------|---------|--------|
| Python | 3.12.13 | ✅ |
| Node.js | 22.22.1 | ✅ |
| npm | 10.9.4 | ✅ |
| pip | 26.0.1 | ✅ |
| apt | 3.0.3 | ✅ |
| gcc | installed | ✅ |

### 4.3 Package Manager Access
```bash
# All of these work inside the sandbox:
pip install <package>       # Python packages
apt install <package>       # System packages (may need sudo)
npm install <package>       # Node.js packages
```
**Status:** ✅ FULLY AVAILABLE

---

## 5. Runtime Plugins

| Plugin | Purpose | Status |
|--------|---------|--------|
| **AgentSkillsPlugin** | File operations (open_file, edit_file, search_dir, find_file) | ✅ Active |
| **JupyterPlugin** | IPython/Jupyter environment | ✅ Active |
| **VSCodePlugin** | VSCode integration | ✅ Available |

### AgentSkills Functions
```python
from agentskills import open_file, edit_file
from agentskills import help_me

# File navigation
open_file("/workspace/file.py", line_number=10)
goto_line(50)
scroll_down()
scroll_up()

# Search
search_dir("pattern", "./src")
search_file("pattern", "file.py")  
find_file("config.py", "./")

# Editing
edit_file("/workspace/file.py", start=1, end=3, content="new content")
```

---

## 6. Current Configuration

From `/home/dev/OH_SHOP/data/openhands/settings.json`:

| Setting | Value | Implication |
|---------|-------|-------------|
| `agent` | null | Uses CodeActAgent (default) |
| `max_iterations` | null | Uses default max iterations |
| `security_analyzer` | null | **No security restrictions** |
| `confirmation_mode` | null | **No confirmation required for actions** |
| `sandbox_base_container_image` | null | Uses default nikolaik/python-nodejs |
| `enable_default_condenser` | true | Memory condensation enabled |
| `mcp_config.sse_servers` | oh-browser-mcp:3010 | MCP web_research tool available |

---

## 7. What's Already God-Tier

### ✅ Code Generation & Editing
- Agent can write any code in any language
- Full str_replace_editor for precise edits
- Can create/modify/delete files
- Auto-linting available

### ✅ Shell Access
- Full bash terminal with persistence
- Can run any Linux command
- Process management (bg/fg/signals)
- Environment variable management

### ✅ Python Execution
- Interactive IPython environment
- Magic commands (%pip, %run, etc.)
- Full library ecosystem access
- Jupyter notebook integration

### ✅ Package Management
- pip install works
- apt install works (full system access)
- npm install works
- Can compile from source (gcc available)

### ✅ Multi-Agent Delegation
- Can delegate to specialized agents
- BrowsingAgent for web tasks
- Subtask tracking and management

### ✅ No Security Restrictions (Currently)
- security_analyzer: null
- confirmation_mode: null
- Agent has full autonomy

---

## 8. What's Missing/Needs Work

### ❌ AI-Driven Browser Navigation
**Problem:** `browser-use` library requires LLM with `structured_output` support. Local LLM (openhands-lm via LM Studio) doesn't support this.

**Current State:** Built-in BrowserGym tool can navigate via bid-based clicking, but the AI can't intelligently decide what to click without structured output.

**Solution in Progress:** Stagehand integration (supports base_url for local LLM)

### ❌ File Downloads from Web
**Problem:** Related to browser-use blocking. The agent can navigate to pages but can't execute the AI-driven download workflow.

**Solution:** Stagehand will handle this

### ⚠️ No Built-in Web Search
**Problem:** OpenHands doesn't have native web search

**Current Solution:** MCP `web_research` tool via oh-browser-mcp (uses SearxNG backend)

---

## 9. Configuration Changes Needed

### 9.1 No Changes Needed for God-Tier Mode
OpenHands is **already in god-tier mode**:
- No security_analyzer blocking actions
- No confirmation_mode requiring approval
- Full sandbox access
- All tools enabled by default

### 9.2 Default AgentConfig Already Enables Everything
From `agent_config.py`:
```python
enable_browsing: bool = True      # ✅ Already on
enable_editor: bool = True        # ✅ Already on  
enable_jupyter: bool = True       # ✅ Already on
enable_cmd: bool = True           # ✅ Already on
enable_think: bool = True         # ✅ Already on
enable_finish: bool = True        # ✅ Already on
enable_mcp: bool = True           # ✅ Already on
enable_plan_mode: bool = True     # ✅ Already on
```

---

## 10. What OpenHands Can Already Do (Examples)

### Install Any Software
```
User: "Install Docker inside the sandbox"
Agent: Uses apt to install Docker, configures it
```

### Write Complete Applications
```
User: "Create a FastAPI server with SQLite database"
Agent: Creates files, installs dependencies, writes code
```

### Edit Existing Code
```
User: "Refactor this function to use async/await"
Agent: Uses str_replace_editor to modify code
```

### Run & Test Code
```
User: "Run the tests and fix any failures"
Agent: Executes pytest, reads output, fixes code
```

### Multi-Step Tasks
```
User: "Clone this repo, analyze it, and create documentation"
Agent: Uses git, reads files, creates markdown docs
```

### Navigate Web Pages
```
User: "Go to example.com and click the login button"
Agent: Uses BrowserGym goto() and click(bid) (if bid is known)
```

---

## 11. Conclusion

**OpenHands is already a fully capable AI software engineer.** It can:

1. ✅ Generate and edit code in any language
2. ✅ Execute bash commands with full system access
3. ✅ Run Python code interactively
4. ✅ Install any package (pip/apt/npm)
5. ✅ Read/write/edit files
6. ✅ Navigate web pages (basic)
7. ✅ Use MCP tools
8. ✅ Plan and track multi-step tasks

**The only gap is intelligent AI-driven web browsing**, which is being addressed with Stagehand integration to replace browser-use.

---

## 12. Recommended Actions

| Priority | Action | Status |
|----------|--------|--------|
| HIGH | Replace browser-use with Stagehand for AI browsing | In Progress (ChatGPT documenting) |
| LOW | No other configuration needed | N/A |

The agent is ready for use. Test it with any code generation or file manipulation task while we finalize browser automation.
