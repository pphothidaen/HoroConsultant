---
name: terminal-session-management
description: Manage persistent terminal sessions with herdr (primary) and tmux fallback on Mac.
owner: hermes
responsibility: terminal-infrastructure
responsible_agents:
  - hermes
  - devops
---

# Terminal Session Management Skill

Manage persistent, agent-aware terminal sessions using **herdr** (primary) with **tmux** fallback for long-running commands, multi-agent orchestration, and CI/deploy monitoring on macOS.

## Purpose

Provide Hermes and DevOps agents with structured terminal session management that:
1. Keeps long-running processes alive across terminal disconnects
2. Detects agent states (working / blocked / idle / done) automatically via herdr
3. Captures bounded output to prevent context pollution
4. Supports the 6-lane concurrency architecture with isolated workspaces

## Tool Chain & Fallback Priority

```
herdr (agent-native, Rust binary)
  └── tmux (traditional multiplexer)
       └── background process + log file (universal fallback)
```

Detection at runtime:
```bash
command -v herdr &>/dev/null  # Priority 1
command -v tmux  &>/dev/null  # Priority 2
# else: bg process fallback    # Priority 3
```

## Session Lifecycle Operations

### 1. Create Session

```bash
# herdr (preferred)
herdr workspace create <name> --path <project-path>
herdr pane create --workspace <name> --name <pane-label> -- <command>

# tmux (fallback)
tmux new-session -d -s <name> "<command>"
```

### 2. List / Status

```bash
# herdr — agent-aware status with working/blocked/idle detection
herdr status
herdr status --workspace <name>

# tmux — manual check
tmux list-sessions
tmux list-panes -t <session>
```

### 3. Capture Bounded Output

Extract only the last N lines to prevent context window pollution:

```bash
# herdr
herdr pane read --workspace <name> --name <pane> --lines <N>

# tmux
tmux capture-pane -pt <session> -S -<N> 2>/dev/null | tail -n <N>
```

**Default max lines**: `30` (adjustable per task complexity).

### 4. Send Input / Commands

```bash
# herdr
herdr pane send --workspace <name> --name <pane> "<input>"

# tmux
tmux send-keys -t <session> "<input>" Enter
```

### 5. Terminate Session

```bash
# herdr
herdr pane kill --workspace <name> --name <pane>
herdr workspace delete <name>

# tmux
tmux kill-session -t <session>
```

## Multi-Workspace Patterns (6-Lane Architecture)

Map the 6-lane concurrency model to terminal workspaces:

```
herdr workspace: horoconsultant
├── pane: mgmt-lead-ba     (Management Tier)
├── pane: mgmt-intake      (Management Tier)
├── pane: mgmt-auditor     (Management Tier)
├── pane: exec-dev-api     (Execution Tier)
├── pane: exec-dev-core    (Execution Tier)
└── pane: exec-qa          (Execution Tier)
```

### Lane Isolation Rule

Each pane maps to exactly one lane. Never assign two concurrent agents to the same pane. Pane names MUST include the lane identifier for traceability.

## Agent State Detection (herdr only)

herdr automatically detects 20+ coding agents including Antigravity CLI (`agy`):

| State | Meaning | Action |
|:------|:--------|:-------|
| `working` | Agent is actively processing | No intervention needed |
| `blocked` | Agent waiting for human input | Escalate to HITL or send input |
| `idle` | Agent finished or awaiting task | Ready for new dispatch |
| `done` | Task completed | Collect evidence, teardown pane |

Use `herdr status` sidebar to monitor all lanes without polling.

## Script Wrappers

Two helper scripts are provided in `scripts/` subdirectory:

### `scripts/herdr-ops.sh`
Primary wrapper for herdr operations with structured ASCII output.

### `scripts/tmux-ops.sh`
Improved tmux wrapper (replacing legacy `.agy/scripts/tmux-runner.sh`) with:
- Unique session naming with timestamp suffixes
- Persistent log capture to `/tmp/agy-sessions/`
- Exit code and done-metadata tracking
- Graceful cleanup on SIGTERM/SIGINT

## Usage by Agents

### Hermes (Orchestrator)
- Create workspace at task start
- Spawn panes for delegated specialist lanes
- Monitor agent states via `herdr status`
- Collect bounded output as evidence
- Teardown workspace after all lanes complete

### DevOps
- Run CI/deploy commands in persistent sessions
- Watch build/deploy events with exponential backoff
- Capture deployment logs as release evidence

## Safeguards

1. **Bounded Output**: Always use `--lines <N>` or `tail -n <N>`. Default `N=30`. Never dump unbounded terminal output into agent context.
2. **Session Naming**: Use pattern `<project>-<lane>-<timestamp>` to prevent name collisions.
3. **Cleanup Mandate**: Terminate all sessions after task completion. Orphaned sessions waste resources.
4. **ASCII Logging**: All wrapper output uses `[OK]`, `[ERROR]`, `[WARNING]`, `[INFO]` tags only.
5. **No Secret Leakage**: Never capture terminal output containing secrets or credentials. Sanitize before evidence collection.

## Reporting

```
[OK] Session created: horoconsultant/exec-dev-api (herdr)
[OK] Output captured: 30 lines from exec-qa
[WARNING] Agent blocked: exec-dev-core awaiting input
[ERROR] Session creation failed: tmux server not running, falling back to bg process
[INFO] Workspace teardown complete: horoconsultant (6 panes cleaned)
```
